import logging
import re
from dataclasses import dataclass, field

import pandas as pd

from app.services.parsers import ParseError, read_tabular

logger = logging.getLogger("corpactions.holdings")

HEADER_SCAN_ROWS = 25
HOLDINGS_EXTENSIONS = {".csv", ".xlsx"}

# Nombres de columna aceptados (ya normalizados: minúsculas, sin símbolos)
COLUMN_ALIASES: dict[str, set[str]] = {
    "account_id": {"account", "account id", "account number", "account no", "acct", "acct no",
                   "acct number", "account code", "portfolio", "portfolio id"},
    "account_name": {"account name", "client", "client name", "portfolio name", "account holder"},
    "isin": {"isin", "isin code"},
    "cusip": {"cusip", "cusip code"},
    "ticker": {"ticker", "symbol", "ticker symbol", "stock symbol"},
    "security_name": {"security", "security name", "description", "security description",
                      "instrument", "instrument name", "asset name", "name", "issuer"},
    "quantity": {"quantity", "qty", "shares", "position", "units", "holding", "holdings",
                 "nominal", "shares held", "quantity held"},
    "currency": {"currency", "ccy", "curr"},
}
ALIAS_TO_FIELD = {alias: f for f, aliases in COLUMN_ALIASES.items() for alias in aliases}

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CUSIP_RE = re.compile(r"^[A-Z0-9]{9}$")


@dataclass
class Holding:
    source_row: int
    account_id: str
    account_name: str
    isin: str
    cusip: str
    ticker: str
    security_name: str
    quantity: float | None
    currency: str


@dataclass
class HoldingIssue:
    source_row: int | None
    level: str  # "error" | "warning"
    message: str


@dataclass
class HoldingsResult:
    filename: str
    sheet: str
    header_row: int
    detected_columns: dict[str, str]
    rows_read: int
    holdings: list[Holding] = field(default_factory=list)
    issues: list[HoldingIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _normalize_header(cell: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", cell.lower()).strip()


def _find_header(df: pd.DataFrame) -> tuple[int | None, dict[str, int]]:
    best_pos, best_map = None, {}
    for pos in range(min(HEADER_SCAN_ROWS, len(df))):
        mapping: dict[str, int] = {}
        for col_pos, cell in enumerate(df.iloc[pos]):
            field_name = ALIAS_TO_FIELD.get(_normalize_header(str(cell)))
            if field_name and field_name not in mapping:
                mapping[field_name] = col_pos
        if len(mapping) > len(best_map):
            best_pos, best_map = pos, mapping
    return best_pos, best_map


def _missing_required(mapping: dict[str, int]) -> list[str]:
    missing = []
    if not any(k in mapping for k in ("isin", "cusip", "ticker")):
        missing.append("an ISIN, CUSIP or ticker column")
    if "quantity" not in mapping:
        missing.append("a quantity column")
    return missing


def _isin_checksum_ok(isin: str) -> bool:
    digits = "".join(str(int(c, 36)) for c in isin)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _parse_quantity(raw: str) -> tuple[float | None, str | None]:
    """Devuelve (valor, advertencia). valor None si no se pudo interpretar."""
    s = raw.replace(" ", "").replace("\u00a0", "")
    if not s:
        return None, None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative, s = True, s[1:-1]
    if s.startswith("-"):
        negative, s = True, s[1:]
    s = s.lstrip("+")

    note = None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):          # 1.234,56
            s = s.replace(".", "").replace(",", ".")
        else:                                    # 1,234.56
            s = s.replace(",", "")
    elif "," in s:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
            note = f"'{raw}' read as a decimal comma"
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        if s.count(".") > 1:
            s = s.replace(".", "")
        else:
            note = f"'{raw}' is ambiguous (1.500 = 1500 or 1.5?); read as {float(s)}"

    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None, None
    value = float(s)
    return (-value if negative else value), note


def parse_holdings(filename: str, data: bytes) -> HoldingsResult:
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in HOLDINGS_EXTENSIONS:
        raise ParseError("Holdings must be a .csv or .xlsx file.")

    tables, warnings = read_tabular(data, extension)

    chosen = None
    problems: list[str] = []
    for sheet_name, df in tables.items():
        header_pos, mapping = _find_header(df)
        missing = _missing_required(mapping)
        if header_pos is not None and not missing:
            chosen = (sheet_name, df, header_pos, mapping)
            break
        problems.append(f"'{sheet_name}': missing {' and '.join(missing)}")

    if not chosen:
        raise ParseError(
            "Could not find a holdings table. " + "; ".join(problems) +
            ". Expected headers like Account, ISIN, CUSIP, Ticker, Quantity."
        )

    sheet_name, df, header_pos, mapping = chosen
    ignored = [n for n in tables if n != sheet_name]
    if ignored:
        warnings.append(f"Only sheet '{sheet_name}' was used; ignored: {ignored}.")
    if "account_id" not in mapping:
        warnings.append("No account column found; affected accounts cannot be identified.")
    if "isin" not in mapping and "cusip" not in mapping:
        warnings.append("No ISIN or CUSIP column; matching will rely on ticker only and will be uncertain.")

    header_cells = df.iloc[header_pos]
    result = HoldingsResult(
        filename=filename,
        sheet=sheet_name,
        header_row=int(df.index[header_pos]) + 1,
        detected_columns={f: str(header_cells.iloc[p]).strip() for f, p in mapping.items()},
        rows_read=0,
        warnings=warnings,
    )

    seen_keys: dict[tuple, int] = {}

    for idx, row in df.iloc[header_pos + 1:].iterrows():
        source_row = int(idx) + 1

        def cell(name: str) -> str:
            pos = mapping.get(name)
            return str(row.iloc[pos]).strip() if pos is not None else ""

        isin = re.sub(r"\s+", "", cell("isin")).upper()
        cusip = re.sub(r"\s+", "", cell("cusip")).upper()
        ticker = cell("ticker").upper()

        if not (isin or cusip or ticker):
            if "total" not in " ".join(str(c) for c in row).lower():
                result.issues.append(HoldingIssue(source_row, "error", "Row skipped: no ISIN, CUSIP or ticker."))
            continue

        result.rows_read += 1

        def flag(level: str, message: str) -> None:
            result.issues.append(HoldingIssue(source_row, level, message))

        if isin:
            if not ISIN_RE.match(isin):
                flag("error", f"Invalid ISIN format: '{isin}'.")
            elif not _isin_checksum_ok(isin):
                flag("warning", f"ISIN '{isin}' fails the check-digit test.")
        if cusip and not CUSIP_RE.match(cusip):
            flag("error", f"Invalid CUSIP format: '{cusip}'.")
        if ISIN_RE.match(isin) and CUSIP_RE.match(cusip) and isin[:2] in {"US", "CA"} and isin[2:11] != cusip:
            flag("warning", f"CUSIP '{cusip}' does not match the one embedded in ISIN '{isin}'.")

        raw_quantity = cell("quantity")
        quantity, note = _parse_quantity(raw_quantity)
        if not raw_quantity:
            flag("error", "Quantity is missing.")
        elif quantity is None:
            flag("error", f"Quantity '{raw_quantity}' is not a valid number.")
        else:
            if note:
                flag("warning", note)
            if quantity < 0:
                flag("warning", "Negative quantity (short position?).")
            elif quantity == 0:
                flag("warning", "Quantity is zero.")

        account_id = cell("account_id")
        if "account_id" in mapping and not account_id:
            flag("warning", "Account is missing for this position.")

        key = (account_id, isin or cusip or ticker)
        if key in seen_keys:
            flag("warning", f"Duplicate position for the same account and security (also on row {seen_keys[key]}).")
        else:
            seen_keys[key] = source_row

        result.holdings.append(
            Holding(
                source_row=source_row,
                account_id=account_id,
                account_name=cell("account_name"),
                isin=isin,
                cusip=cusip,
                ticker=ticker,
                security_name=cell("security_name"),
                quantity=quantity,
                currency=cell("currency").upper(),
            )
        )

    if not result.holdings:
        raise ParseError("The holdings table has headers but no usable rows.")

    logger.info("Holdings parsed: %d rows, %d issues", len(result.holdings), len(result.issues))
    return result