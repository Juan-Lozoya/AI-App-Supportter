import csv
import io
import itertools
import logging
from dataclasses import dataclass, field

import pandas as pd
import pdfplumber

logger = logging.getLogger("corpactions.parsers")

MAX_PDF_PAGES = 100
MAX_TABLE_ROWS = 5000
MAX_SHEETS = 20
MAX_PARSED_CHARS = 300_000
MIN_PDF_CHARS = 50  # menos que esto: casi seguro es un PDF escaneado


class ParseError(Exception):
  """El archivo pasó la validación pero no se pudo leer."""


@dataclass
class ParsedDocument:
  filename: str
  file_type: str
  text: str
  pages: int | None = None
  warnings: list[str] = field(default_factory=list)


def _extension(filename: str) -> str:
  return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _decode(data: bytes, warnings: list[str]) -> str:
  try:
    return data.decode("utf-8-sig")
  except UnicodeDecodeError:
    warnings.append(
      "File is not UTF-8; decoded as Latin-1. Accented characters may be wrong."
    )
    return data.decode("latin-1")


# ---------- TXT ----------
def _parse_txt(filename: str, data: bytes) -> ParsedDocument:
  warnings: list[str] = []
  text = _decode(data, warnings).strip()
  return ParsedDocument(filename, ".txt", text, warnings=warnings)


# ---------- PDF ----------
def _parse_pdf(filename: str, data: bytes) -> ParsedDocument:
  warnings: list[str] = []
  parts: list[str] = []
  empty_pages: list[int] = []

  try:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
      total_pages = len(pdf.pages)
      if total_pages > MAX_PDF_PAGES:
        warnings.append(
          f"PDF has {total_pages} pages; only the first {MAX_PDF_PAGES} were read."
        )
      for number, page in enumerate(pdf.pages[:MAX_PDF_PAGES], start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
          parts.append(f"[Page {number}]\n{page_text}")
        else:
          empty_pages.append(number)
  except Exception as exc:  # pdfplumber/pdfminer lanzan muchos tipos de error
    logger.warning("PDF parse failed for %s: %s", filename, exc)
    raise ParseError(
      "Could not read the PDF. It may be corrupted or password-protected."
    ) from exc

  text = "\n\n".join(parts)

  if len(text) < MIN_PDF_CHARS:
    warnings.append(
      "Little or no extractable text. The PDF is probably scanned; OCR is not implemented yet."
    )
  elif empty_pages:
    warnings.append(f"No extractable text on pages: {empty_pages}.")

  return ParsedDocument(filename, ".pdf", text, pages=total_pages, warnings=warnings)


# ---------- Tablas (CSV / Excel) ----------
def read_tabular(data: bytes, extension: str) -> tuple[dict[str, pd.DataFrame], list[str]]:
  """Devuelve ({nombre_hoja: DataFrame}, advertencias). Sin asumir encabezados.

  Se reutilizará en el parser de holdings.
  """
  warnings: list[str] = []
  tables: dict[str, pd.DataFrame] = {}

  try:
    if extension == ".csv":
      text = _decode(data, warnings)
      try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
      except csv.Error:
        dialect = csv.excel
      rows = list(
        itertools.islice(csv.reader(io.StringIO(text), dialect), MAX_TABLE_ROWS + 1)
      )
      tables["csv"] = pd.DataFrame(rows)
    else:  # .xlsx
      excel = pd.ExcelFile(io.BytesIO(data), engine="openpyxl")
      sheet_names = excel.sheet_names
      if len(sheet_names) > MAX_SHEETS:
        warnings.append(
          f"Workbook has {len(sheet_names)} sheets; only the first {MAX_SHEETS} were read."
        )
      for name in sheet_names[:MAX_SHEETS]:
        tables[name] = excel.parse(
          name, header=None, dtype=str, nrows=MAX_TABLE_ROWS + 1
        )
  except Exception as exc:
    logger.warning("Table parse failed: %s", exc)
    raise ParseError(
      f"Could not read the {extension} file. It may be corrupted or malformed."
    ) from exc

  cleaned: dict[str, pd.DataFrame] = {}
  for name, df in tables.items():
    df = df.fillna("").astype(str)
    df = df.replace(r" 00:00:00$", "", regex=True)  # fechas de Excel sin hora
    if len(df) > MAX_TABLE_ROWS:
      df = df.iloc[:MAX_TABLE_ROWS]
      warnings.append(f"'{name}' was truncated to {MAX_TABLE_ROWS} rows.")
    df = df[(df.apply(lambda col: col.str.strip()) != "").any(axis=1)]  # quita filas vacías
    df = df.loc[:, (df.apply(lambda col: col.str.strip()) != "").any(axis=0)]  # y columnas vacías
    cleaned[name] = df

  return cleaned, warnings


def _parse_tabular(filename: str, data: bytes, extension: str) -> ParsedDocument:
  tables, warnings = read_tabular(data, extension)

  blocks = []
  for name, df in tables.items():
    lines = [
      " | ".join(str(cell).strip() for cell in row)
      for row in df.itertuples(index=False, name=None)
    ]
    blocks.append(f"[Sheet: {name}]\n" + "\n".join(lines))

  return ParsedDocument(filename, extension, "\n\n".join(blocks), warnings=warnings)


# ---------- Punto de entrada ----------
def parse_document(filename: str, data: bytes) -> ParsedDocument:
  extension = _extension(filename)

  if extension == ".txt":
    doc = _parse_txt(filename, data)
  elif extension == ".pdf":
    doc = _parse_pdf(filename, data)
  elif extension in {".csv", ".xlsx"}:
    doc = _parse_tabular(filename, data, extension)
  else:
    raise ParseError(f"Unsupported file type: {extension}")

  if len(doc.text) > MAX_PARSED_CHARS:
    doc.text = doc.text[:MAX_PARSED_CHARS]
    doc.warnings.append(f"Text was truncated to {MAX_PARSED_CHARS} characters.")

  if not doc.text.strip() and not doc.warnings:
    doc.warnings.append("No text content was extracted.")

  return doc