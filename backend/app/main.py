import logging
import uuid

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.schemas import AnalysisCreated, KbSearchRequest
from app.services import rag
from app.services.storage import PreparedFile, StorageError, save_analysis
from app.services.validation import ValidationError, read_upload, validate_file
from app.services.parsers import ParseError, parse_document
from dataclasses import asdict
from app.services.holdings import parse_holdings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("corpactions")

app = FastAPI(title="Corporate Actions Analyzer")

app.add_middleware(
  CORSMiddleware,
  allow_origins=config.CORS_ORIGINS,
  allow_methods=["*"],
  allow_headers=["*"],
)


@app.get("/health")
def health():
  return {"status": "ok"}


def _unique_name(name: str, used: set[str]) -> str:
  """Evita que dos archivos con el mismo nombre se sobrescriban en S3."""
  candidate, counter = name, 2
  stem, dot, ext = name.rpartition(".")
  while candidate in used:
    candidate = f"{stem}_{counter}{dot}{ext}" if dot else f"{name}_{counter}"
    counter += 1
  used.add(candidate)
  return candidate


@app.post("/api/analyses", response_model=AnalysisCreated)
def create_analysis(
  files: list[UploadFile] = File(default=[]),
  pasted_text: str | None = Form(default=None),
  holdings_file: UploadFile | None = File(default=None),
):
  announcement_uploads = [f for f in files if f.filename]
  holdings = holdings_file if holdings_file and holdings_file.filename else None
  text = (pasted_text or "").strip()

  if not announcement_uploads and not text:
    raise HTTPException(400, "Upload at least one document or paste announcement text.")
  if len(announcement_uploads) > config.MAX_FILES:
    raise HTTPException(400, f"Too many files. Maximum is {config.MAX_FILES}.")
  if len(text) > config.MAX_PASTED_CHARS:
    raise HTTPException(413, f"Pasted text exceeds {config.MAX_PASTED_CHARS} characters.")

  # 1) Validar TODO antes de escribir algo en S3
  prepared: list[PreparedFile] = []
  try:
    for role, uploads in (
      ("announcement", announcement_uploads),
      ("holdings", [holdings] if holdings else []),
    ):
      used_names: set[str] = set()
      for upload in uploads:
        data = read_upload(upload)
        safe_name = validate_file(upload.filename, data)
        prepared.append(
          PreparedFile(
            role=role,
            original_filename=upload.filename,
            filename=_unique_name(safe_name, used_names),
            data=data,
            client_content_type=upload.content_type,
          )
        )
  except ValidationError as exc:
    raise HTTPException(exc.status_code, exc.message)

  if text:
    prepared.append(
      PreparedFile(
        role="pasted_text",
        original_filename="pasted_text.txt",
        filename="pasted_text.txt",
        data=text.encode("utf-8"),
        client_content_type="text/plain",
      )
    )

  # 2) Guardar en S3 y escribir el log
  analysis_id = str(uuid.uuid4())
  try:
    stored = save_analysis(analysis_id, prepared)
  except StorageError:
    raise HTTPException(502, "Could not store the files. Check backend logs.")

  # TODO (Fase 2): extraer texto con parsers. Por ahora solo se guardan los archivos.
  return {"analysis_id": analysis_id, "status": "uploaded", "files": stored}


@app.post("/api/kb/search")
def kb_search(req: KbSearchRequest):
  try:
    results = rag.retrieve(req.query, req.top_k)
  except (BotoCoreError, ClientError, RuntimeError):
    logger.exception("Knowledge base retrieval failed")
    raise HTTPException(502, "Knowledge base query failed. Check backend logs.")
  return {"query": req.query, "results": results}

@app.post("/api/dev/parse")
def dev_parse(file: UploadFile = File(...)):
  """TEMPORAL: solo para probar los parsers. Se elimina al integrarlos."""
  try:
    data = read_upload(file)
    safe_name = validate_file(file.filename or "", data)
    parsed = parse_document(safe_name, data)
  except ValidationError as exc:
    raise HTTPException(exc.status_code, exc.message)
  except ParseError as exc:
    raise HTTPException(422, str(exc))

  return {
    "filename": parsed.filename,
    "file_type": parsed.file_type,
    "pages": parsed.pages,
    "chars": len(parsed.text),
    "warnings": parsed.warnings,
    "text_preview": parsed.text[:2000],
  }

@app.post("/api/dev/parse-holdings")
def dev_parse_holdings(file: UploadFile = File(...)):
  """TEMPORAL: solo para probar el parser de holdings. Usar únicamente datos sintéticos."""
  try:
    data = read_upload(file)
    safe_name = validate_file(file.filename or "", data)
    result = parse_holdings(safe_name, data)
  except ValidationError as exc:
    raise HTTPException(exc.status_code, exc.message)
  except ParseError as exc:
    raise HTTPException(422, str(exc))

  payload = asdict(result)
  return {
    "filename": payload["filename"],
    "sheet": payload["sheet"],
    "header_row": payload["header_row"],
    "detected_columns": payload["detected_columns"],
    "holdings_count": len(payload["holdings"]),
    "warnings": payload["warnings"],
    "issues": payload["issues"][:100],
    "holdings_preview": payload["holdings"][:20],
  }