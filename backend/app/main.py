import logging
import uuid
from datetime import datetime, timezone

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.schemas import (
  EVENT_LABELS, AlertsResponse, AnalysisCreated, AnalysisDetail, AnalysisList, AnalysisRecord,
  AnalysisStatus, DashboardStats, DocumentsResponse, EventTypeOption, HoldingMatch,
  HoldingReviewRequest, HoldingsResponse, KbSearchRequest, KeyDatesResponse, OverviewResponse,
  ProcessingResponse, ReviewEntry, ReviewRequest, ReviewResponse, ReviewStatus, StoredFile,
)
from app.services import pipeline, rag, repository, rules, storage
from app.services.repository import RepositoryError
from app.services.storage import StorageError
from app.services.validation import ValidationError, read_upload, validate_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("corpactions")

app = FastAPI(title="Corporate Actions Analyzer")

app.add_middleware(
  CORSMiddleware,
  allow_origins=config.CORS_ORIGINS,
  allow_methods=["*"],
  allow_headers=["*"],
)


# ---------- Utilidades ----------
def _today():
  return datetime.now(timezone.utc).date()


def _load(analysis_id: uuid.UUID) -> AnalysisRecord:
  try:
    record = repository.get(str(analysis_id))
  except RepositoryError:
    raise HTTPException(502, "Could not read the analysis. Check backend logs.")
  if record is None:
    raise HTTPException(404, "Analysis not found.")
  return record


def _save(record: AnalysisRecord) -> None:
  try:
    repository.save(record)
  except RepositoryError:
    raise HTTPException(502, "Could not save the analysis. Check backend logs.")


def _unique_name(name: str, used: set[str]) -> str:
  """Evita que dos archivos con el mismo nombre se sobrescriban en S3."""
  candidate, counter = name, 2
  stem, dot, ext = name.rpartition(".")
  while candidate in used:
    candidate = f"{stem}_{counter}{dot}{ext}" if dot else f"{name}_{counter}"
    counter += 1
  used.add(candidate)
  return candidate


@app.get("/health")
def health():
  return {"status": "ok"}

# ---------- Crear y reintentar ----------
@app.post("/api/analyses", response_model=AnalysisCreated)
def create_analysis(
  background_tasks: BackgroundTasks,
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
  prepared: list[storage.PreparedFile] = []
  try:
    for role, uploads in (("announcement", announcement_uploads), ("holdings", [holdings] if holdings else [])):
      used_names: set[str] = set()
      for upload in uploads:
        data = read_upload(upload)
        safe_name = validate_file(upload.filename, data)
        if role == "holdings" and not safe_name.lower().endswith((".csv", ".xlsx")):
          raise ValidationError("The holdings file must be a .csv or .xlsx file.")
        prepared.append(storage.PreparedFile(
          role=role, original_filename=upload.filename,
          filename=_unique_name(safe_name, used_names), data=data,
          client_content_type=upload.content_type,
        ))
  except ValidationError as exc:
    raise HTTPException(exc.status_code, exc.message)

  if text:
    prepared.append(storage.PreparedFile(
      role="pasted_text", original_filename="pasted_text.txt", filename="pasted_text.txt",
      data=text.encode("utf-8"), client_content_type="text/plain",
    ))

  # 2) Guardar en S3, crear el registro y lanzar el análisis en segundo plano
  analysis_id = str(uuid.uuid4())
  try:
    stored = storage.save_analysis(analysis_id, prepared)
  except StorageError:
    raise HTTPException(502, "Could not store the files. Check backend logs.")

  now = repository.now_iso()
  record = AnalysisRecord(
    analysis_id=analysis_id, created_at=now, updated_at=now, status="processing",
    files=[StoredFile.model_validate(s) for s in stored],
  )
  _save(record)
  background_tasks.add_task(pipeline.run_pipeline, analysis_id)
  return AnalysisCreated(analysis_id=analysis_id, status="processing", files=record.files)


@app.post("/api/analyses/{analysis_id}/retry", response_model=AnalysisCreated)
def retry_analysis(analysis_id: uuid.UUID, background_tasks: BackgroundTasks):
  record = _load(analysis_id)
  if record.status != "failed":
    raise HTTPException(409, "Only failed analyses can be retried.")
  record.status, record.error = "processing", None
  record.stages, record.alerts, record.sources = [], [], []
  record.event = record.summary = record.holdings_summary = None
  record.required_actions, record.next_steps, record.holdings_matches = [], [], []
  record.total_runtime_ms = None
  _save(record)
  background_tasks.add_task(pipeline.run_pipeline, record.analysis_id)
  return AnalysisCreated(analysis_id=record.analysis_id, status="processing", files=record.files)


# ---------- Lista, detalle y dashboard ----------
@app.get("/api/analyses", response_model=AnalysisList)
def list_analyses(
  status: AnalysisStatus | None = None,
  review_status: ReviewStatus | None = None,
  event_type: str | None = None,
  q: str | None = None,
  limit: int = 50,
  offset: int = 0,
):
  limit, offset = max(1, min(limit, 200)), max(0, offset)
  try:
    items = repository.list_summaries()
  except RepositoryError:
    raise HTTPException(502, "Could not list analyses. Check backend logs.")

  if status:
    items = [i for i in items if i.status == status]
  if review_status:
    items = [i for i in items if i.review_status == review_status]
  if event_type:
    items = [i for i in items if i.event_type == event_type]
  if q:
    needle = q.strip().lower()
    items = [i for i in items if needle in " ".join(
      [i.analysis_id, i.company_name or "", i.security_id or ""]).lower()]
  return AnalysisList(items=items[offset:offset + limit], total=len(items))


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def dashboard_stats():
  try:
    items = repository.list_summaries()
  except RepositoryError:
    raise HTTPException(502, "Could not read dashboard data. Check backend logs.")
  counts = {"processing": 0, "action_required": 0, "pending_review": 0, "completed": 0}
  for item in items:
    counts[rules.dashboard_bucket(item)] += 1
  return DashboardStats(
    total_events=len(items), recent=items[:5],
    generated_at=datetime.now(timezone.utc).isoformat(), **counts,
  )


@app.get("/api/meta/event-types", response_model=list[EventTypeOption])
def event_types():
  return [EventTypeOption(value=k, label=v) for k, v in EVENT_LABELS.items()]


@app.get("/api/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: uuid.UUID):
  return _load(analysis_id)


# ---------- Una ruta por sección de la interfaz ----------
@app.get("/api/analyses/{analysis_id}/overview", response_model=OverviewResponse)
def overview(analysis_id: uuid.UUID):
  r = _load(analysis_id)
  return OverviewResponse(
    analysis_id=r.analysis_id, status=r.status, event=r.event,
    event_label=EVENT_LABELS.get(r.event.event_type) if r.event else None,
    election_display=rules.election_display(r.event) if r.event else None,
    summary=r.summary, required_actions=r.required_actions, next_steps=r.next_steps,
  )


@app.get("/api/analyses/{analysis_id}/dates", response_model=KeyDatesResponse)
def key_dates(analysis_id: uuid.UUID):
  r = _load(analysis_id)
  today = _today()
  return KeyDatesResponse(analysis_id=r.analysis_id, as_of=today.isoformat(),
                          dates=rules.key_dates(r.event, today) if r.event else [])


@app.get("/api/analyses/{analysis_id}/holdings", response_model=HoldingsResponse)
def affected_holdings(analysis_id: uuid.UUID, confidence: str | None = None, review_status: str | None = None):
  r = _load(analysis_id)
  matches = r.holdings_matches
  if confidence:
    matches = [m for m in matches if m.confidence == confidence]
  if review_status:
    matches = [m for m in matches if m.review_status == review_status]
  return HoldingsResponse(analysis_id=r.analysis_id, summary=r.holdings_summary, matches=matches)


@app.get("/api/analyses/{analysis_id}/alerts", response_model=AlertsResponse)
def alerts(analysis_id: uuid.UUID, category: str | None = None, severity: str | None = None):
  r = _load(analysis_id)
  items = r.alerts
  counts = {"high": 0, "medium": 0, "low": 0}
  for a in items:
    counts[a.severity] += 1
  if category:
    items = [a for a in items if a.category == category]
  if severity:
    items = [a for a in items if a.severity == severity]
  return AlertsResponse(analysis_id=r.analysis_id, counts=counts, alerts=items, sources=r.sources)


@app.get("/api/analyses/{analysis_id}/processing", response_model=ProcessingResponse)
def processing(analysis_id: uuid.UUID):
  r = _load(analysis_id)
  return ProcessingResponse(
    analysis_id=r.analysis_id, status=r.status, error=r.error, created_at=r.created_at,
    stages=r.stages, total_runtime_ms=r.total_runtime_ms,
    total_input_tokens=sum(int(s.details.get("input_tokens", 0)) for s in r.stages),
    total_output_tokens=sum(int(s.details.get("output_tokens", 0)) for s in r.stages),
  )


@app.get("/api/analyses/{analysis_id}/documents", response_model=DocumentsResponse)
def documents(analysis_id: uuid.UUID):
  r = _load(analysis_id)
  return DocumentsResponse(analysis_id=r.analysis_id, files=r.files)


# ---------- Revisión humana ----------
@app.get("/api/analyses/{analysis_id}/review", response_model=ReviewResponse)
def get_review(analysis_id: uuid.UUID):
  r = _load(analysis_id)
  return ReviewResponse(analysis_id=r.analysis_id, review_status=r.review_status, history=r.review_history)


@app.post("/api/analyses/{analysis_id}/review", response_model=ReviewResponse)
def submit_review(analysis_id: uuid.UUID, body: ReviewRequest):
  r = _load(analysis_id)
  if r.status != "completed":
    raise HTTPException(409, "Only completed analyses can be reviewed.")
  if body.decision in ("rejected", "needs_info") and not body.comment.strip():
    raise HTTPException(422, "A comment is required when rejecting or requesting more information.")

  r.review_history.append(ReviewEntry(
    decision=body.decision, comment=body.comment.strip(), reviewer=body.reviewer.strip(), at=repository.now_iso()))
  r.review_status = body.decision
  _save(r)
  logger.info("Analysis %s reviewed: %s", r.analysis_id, body.decision)
  return ReviewResponse(analysis_id=r.analysis_id, review_status=r.review_status, history=r.review_history)


@app.patch("/api/analyses/{analysis_id}/holdings/{match_id}", response_model=HoldingMatch)
def update_holding_status(analysis_id: uuid.UUID, match_id: str, body: HoldingReviewRequest):
  r = _load(analysis_id)
  match = next((m for m in r.holdings_matches if m.match_id == match_id), None)
  if match is None:
    raise HTTPException(404, "Holding match not found.")
  match.review_status = body.review_status
  _save(r)
  logger.info("Analysis %s holding %s set to %s", r.analysis_id, match_id, body.review_status)
  return match


# ---------- Herramienta de desarrollo ----------
@app.post("/api/kb/search")
def kb_search(req: KbSearchRequest):
  try:
    results = rag.retrieve(req.query, req.top_k)
  except (BotoCoreError, ClientError, RuntimeError):
    logger.exception("Knowledge base retrieval failed")
    raise HTTPException(502, "Knowledge base query failed. Check backend logs.")
  return {"query": req.query, "results": results}