from typing import Any, Literal

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, Field

EventType = Literal[
  "CASH_DIVIDEND", "STOCK_DIVIDEND", "STOCK_SPLIT", "REVERSE_STOCK_SPLIT", "MERGER",
  "ACQUISITION", "TENDER_OFFER", "RIGHTS_OFFERING", "SPIN_OFF", "BOND_REDEMPTION",
  "OTHER", "UNKNOWN",
]
AnalysisStatus = Literal["processing", "completed", "failed"]
ReviewStatus = Literal["pending", "approved", "rejected", "needs_info"]
Severity = Literal["high", "medium", "low"]
AlertCategory = Literal["risk", "missing_information", "conflict", "deadline", "data_quality"]
StageStatus = Literal["running", "completed", "failed", "skipped"]

EVENT_LABELS: dict[str, str] = {
  "CASH_DIVIDEND": "Cash Dividend",
  "STOCK_DIVIDEND": "Stock Dividend",
  "STOCK_SPLIT": "Stock Split",
  "REVERSE_STOCK_SPLIT": "Reverse Stock Split",
  "MERGER": "Merger",
  "ACQUISITION": "Acquisition",
  "TENDER_OFFER": "Tender Offer",
  "RIGHTS_OFFERING": "Rights Offering",
  "SPIN_OFF": "Spin-off",
  "BOND_REDEMPTION": "Bond Redemption",
  "OTHER": "Other",
  "UNKNOWN": "Unknown",
}

class BaseModel(_BaseModel):
    # Marca como "requeridos" en el esquema OpenAPI los campos que siempre se devuelven
    # (aunque tengan valor por defecto), para que los tipos de TypeScript sean exactos.
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

# ---------- Archivos ----------
class UploadedFileInfo(BaseModel):
  role: Literal["announcement", "holdings", "pasted_text"]
  filename: str
  size_bytes: int
  sha256: str


class StoredFile(UploadedFileInfo):
  stored_key: str  # interno: no se expone en la API


class AnalysisCreated(BaseModel):
  analysis_id: str
  status: AnalysisStatus
  files: list[UploadedFileInfo]


class KbSearchRequest(BaseModel):
  query: str = Field(min_length=3, max_length=500)
  top_k: int = Field(default=5, ge=1, le=20)


# ---------- Evento extraído ----------
class ExtractedEvent(BaseModel):
  company_name: str | None = None
  security_name: str | None = None
  isin: str | None = None
  cusip: str | None = None
  ticker: str | None = None
  event_type: EventType = "UNKNOWN"
  event_description: str | None = None

  announcement_date: str | None = None
  ex_date: str | None = None
  record_date: str | None = None
  payment_date: str | None = None
  effective_date: str | None = None
  election_deadline: str | None = None
  expiration_date: str | None = None
  election_required: bool | None = None

  dividend_amount: float | None = None
  currency: str | None = None
  exchange_ratio: str | None = None
  offer_price: float | None = None
  subscription_price: float | None = None
  distribution_ratio: str | None = None
  other_terms: list[str] = Field(default_factory=list)

  options: list[str] = Field(default_factory=list)
  extraction_notes: list[str] = Field(default_factory=list)


# ---------- Resultados del análisis ----------
class Alert(BaseModel):
  id: str = ""
  category: AlertCategory
  severity: Severity
  title: str
  detail: str
  origin: Literal["rule", "ai"]
  source_ids: list[str] = Field(default_factory=list)


class Source(BaseModel):
  id: str
  document: str
  document_id: str | None = None
  score: float | None = None
  excerpt: str


class StageRecord(BaseModel):
  name: str
  label: str
  status: StageStatus
  started_at: str | None = None
  duration_ms: int | None = None
  details: dict[str, Any] = Field(default_factory=dict)
  error: str | None = None


class HoldingMatch(BaseModel):
  match_id: str
  source_row: int
  account_id: str
  account_name: str
  security_id: str
  security_name: str
  quantity: float | None
  currency: str
  match_type: Literal["isin", "cusip", "ticker", "name"]
  confidence: Literal["high", "uncertain"]
  reason: str
  event_type: EventType
  review_status: Literal["pending", "reviewed", "flagged"] = "pending"


class HoldingsIssue(BaseModel):
  source_row: int | None
  level: Literal["error", "warning"]
  message: str


class HoldingsSummary(BaseModel):
  filename: str | None = None
  rows_read: int = 0
  matched: int = 0
  uncertain: int = 0
  not_matched: int = 0
  issues: list[HoldingsIssue] = Field(default_factory=list)
  matches_truncated: bool = False


class ReviewEntry(BaseModel):
  decision: Literal["approved", "rejected", "needs_info"]
  comment: str
  reviewer: str
  at: str


class AnalysisRecord(BaseModel):
  analysis_id: str
  created_at: str
  updated_at: str
  status: AnalysisStatus = "processing"
  review_status: ReviewStatus = "pending"
  error: str | None = None
  files: list[StoredFile] = Field(default_factory=list)
  stages: list[StageRecord] = Field(default_factory=list)
  total_runtime_ms: int | None = None
  event: ExtractedEvent | None = None
  summary: str | None = None
  required_actions: list[str] = Field(default_factory=list)
  next_steps: list[str] = Field(default_factory=list)
  alerts: list[Alert] = Field(default_factory=list)
  sources: list[Source] = Field(default_factory=list)
  holdings_summary: HoldingsSummary | None = None
  holdings_matches: list[HoldingMatch] = Field(default_factory=list)
  review_history: list[ReviewEntry] = Field(default_factory=list)


class AnalysisDetail(AnalysisRecord):
  files: list[UploadedFileInfo] = Field(default_factory=list)  # sin stored_key


class AnalysisSummary(BaseModel):
  analysis_id: str
  created_at: str
  status: AnalysisStatus
  review_status: ReviewStatus
  company_name: str | None = None
  security_id: str | None = None
  event_type: EventType | None = None
  record_date: str | None = None
  affected_accounts: int = 0
  high_alerts: int = 0
  total_runtime_ms: int | None = None
  files_count: int = 0


class AnalysisList(BaseModel):
  items: list[AnalysisSummary]
  total: int


class DashboardStats(BaseModel):
  total_events: int
  pending_review: int
  action_required: int
  completed: int
  processing: int
  recent: list[AnalysisSummary]
  generated_at: str


# ---------- Respuestas por sección ----------
class OverviewResponse(BaseModel):
  analysis_id: str
  status: AnalysisStatus
  event: ExtractedEvent | None
  event_label: str | None
  election_display: str | None
  summary: str | None
  required_actions: list[str]
  next_steps: list[str]


class KeyDate(BaseModel):
  key: str
  label: str
  date: str | None
  state: Literal["not_specified", "upcoming", "today", "passed"]
  days_remaining: int | None
  note: str | None = None


class KeyDatesResponse(BaseModel):
  analysis_id: str
  as_of: str
  dates: list[KeyDate]


class HoldingsResponse(BaseModel):
  analysis_id: str
  summary: HoldingsSummary | None
  matches: list[HoldingMatch]


class AlertsResponse(BaseModel):
  analysis_id: str
  counts: dict[str, int]
  alerts: list[Alert]
  sources: list[Source]

class ProcessingResponse(BaseModel):
  analysis_id: str
  status: AnalysisStatus
  error: str | None
  created_at: str
  stages: list[StageRecord]
  total_runtime_ms: int | None
  total_input_tokens: int
  total_output_tokens: int


class ReviewRequest(BaseModel):
  decision: Literal["approved", "rejected", "needs_info"]
  comment: str = Field(default="", max_length=2000)
  reviewer: str = Field(min_length=1, max_length=100)


class ReviewResponse(BaseModel):
  analysis_id: str
  review_status: ReviewStatus
  history: list[ReviewEntry]

class HoldingReviewRequest(BaseModel):
  review_status: Literal["pending", "reviewed", "flagged"]
  reviewer: str = Field(min_length=1, max_length=100)

class DocumentsResponse(BaseModel):
  analysis_id: str
  files: list[UploadedFileInfo]

class EventTypeOption(BaseModel):
  value: str
  label: str
