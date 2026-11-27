import logging
import time
from datetime import datetime, timezone

from botocore.exceptions import BotoCoreError, ClientError

from app.schemas import Alert, AnalysisRecord, HoldingsIssue, HoldingsSummary, StageRecord
from app.services import analysis, extraction, repository, rules, storage
from app.services.holdings import parse_holdings
from app.services.llm import LLMError
from app.services.matching import match_holdings
from app.services.parsers import ParseError, parse_document
from app.services.storage import StorageError

logger = logging.getLogger("corpactions.pipeline")

EXPECTED_ERRORS = (LLMError, ParseError, StorageError)


class PipelineError(Exception):
  """Error esperado con un mensaje seguro para mostrar al usuario."""


def _now() -> str:
  return datetime.now(timezone.utc).isoformat()


def _llm_details(result) -> dict:
  return {"model": result.model_id, "input_tokens": result.input_tokens,
          "output_tokens": result.output_tokens, "latency_ms": result.latency_ms}


def _run_stage(record: AnalysisRecord, name: str, label: str, fn, *, fatal: bool) -> bool:
  """Ejecuta una etapa midiendo su duración y guardando el progreso. Devuelve True si terminó bien."""
  stage = StageRecord(name=name, label=label, status="running", started_at=_now())
  record.stages = [s for s in record.stages if s.name != name] + [stage]
  repository.save(record)

  started = time.perf_counter()
  ok = False
  try:
    fn(stage)
    if stage.status == "running":
      stage.status = "completed"
    ok = True
  except (PipelineError, *EXPECTED_ERRORS) as exc:
    stage.status, stage.error = "failed", str(exc)
    if fatal:
      raise PipelineError(str(exc)) from exc
  except Exception as exc:  # noqa: BLE001
    logger.exception("Stage %s crashed for analysis %s", name, record.analysis_id)
    stage.status, stage.error = "failed", "Unexpected internal error."
    if fatal:
      raise PipelineError(stage.error) from exc
  finally:
    stage.duration_ms = int((time.perf_counter() - started) * 1000)
    repository.save(record)
  return ok


# ---------- Etapas ----------
def _parse(record, stage, ctx):
  documents: list[tuple[str, str]] = []
  warnings: list[str] = []

  for f in record.files:
    data = storage.read_object(f.stored_key)
    if f.role == "holdings":
      try:
        ctx["holdings"] = parse_holdings(f.filename, data)
      except ParseError as exc:
        warnings.append(f"Holdings file could not be read: {exc}")
        record.alerts.append(Alert(
          category="data_quality", severity="medium", origin="rule",
          title="Holdings file could not be read", detail=str(exc)))
    elif f.role == "pasted_text":
      documents.append(("pasted_text", data.decode("utf-8", errors="replace")))
    else:
      try:
        parsed = parse_document(f.filename, data)
      except ParseError as exc:
        warnings.append(f"{f.filename}: {exc}")
        continue
      warnings.extend(f"{f.filename}: {w}" for w in parsed.warnings)
      documents.append((f.filename, parsed.text))

  documents = [(name, text) for name, text in documents if text.strip()]
  if not documents:
    raise PipelineError(
      "No readable text was found in the uploaded documents. "
      "If the PDF is a scan, OCR is not available yet."
    )
  ctx["documents"] = documents
  stage.details = {
    "documents_read": len(documents),
    "characters": sum(len(text) for _, text in documents),
    "warnings": warnings,
    "holdings_file_read": ctx["holdings"] is not None,
  }


def _extract(record, stage, ctx):
  event, result = extraction.extract_event(ctx["documents"])
  record.event = event
  stage.details = _llm_details(result)


def _validate(record, stage, ctx):
  today = ctx["today"]
  alerts = rules.missing_alerts(record.event) + rules.deadline_alerts(record.event, today)
  for note in record.event.extraction_notes:
    alerts.append(Alert(category="conflict", severity="medium", origin="ai",
                        title="Ambiguous or conflicting information", detail=note))
  record.alerts.extend(alerts)
  ctx["rule_alerts"] = alerts
  stage.details = {"alerts_added": len(alerts), "as_of": today.isoformat()}


def _retrieve(record, stage, ctx):
  try:
    chunks = analysis.retrieve_context(record.event)
  except (BotoCoreError, ClientError, RuntimeError) as exc:
    logger.exception("Knowledge base retrieval failed")
    raise PipelineError("Knowledge base query failed.") from exc
  ctx["chunks"] = chunks
  record.sources = [c.source for c in chunks]
  stage.details = {"chunks": len(chunks), "min_score": float(analysis.config.RAG_MIN_SCORE)}


def _analyze(record, stage, ctx):
  output, result = analysis.generate_analysis(
      record.event, ctx["documents"], ctx.get("chunks", []), ctx.get("rule_alerts", []), ctx["today"])
  record.summary = output.summary
  record.required_actions = output.required_actions
  record.next_steps = output.next_steps
  record.alerts.extend(output.alerts)
  stage.details = {**_llm_details(result), "alerts_added": len(output.alerts)}


def _match(record, stage, ctx):
  holdings = ctx["holdings"]
  if holdings is None:
    stage.status = "skipped"
    stage.details = {"reason": "No holdings file was provided or it could not be read."}
    return

  matches, not_matched, truncated = match_holdings(record.event, holdings)
  uncertain = sum(1 for m in matches if m.confidence == "uncertain")
  errors = sum(1 for i in holdings.issues if i.level == "error")

  record.holdings_matches = matches
  record.holdings_summary = HoldingsSummary(
    filename=holdings.filename, rows_read=holdings.rows_read,
    matched=len(matches) - uncertain, uncertain=uncertain, not_matched=not_matched,
    issues=[HoldingsIssue(source_row=i.source_row, level=i.level, message=i.message)
            for i in holdings.issues[:100]],
    matches_truncated=truncated,
  )

  if uncertain:
    record.alerts.append(Alert(
      category="risk", severity="medium", origin="rule",
      title=f"{uncertain} holding(s) matched with low confidence",
      detail="Matched by ticker or company name only. Confirm the security identifier before treating these accounts as affected."))
  if not matches:
    record.alerts.append(Alert(
      category="risk", severity="medium", origin="rule", title="No holdings matched the event security",
      detail="None of the uploaded positions matched the event by ISIN, CUSIP, ticker or name. Confirm the identifiers."))
  else:
    record.alerts.append(Alert(
      category="risk", severity="low", origin="rule", title="Eligibility has not been verified",
      detail="Positions come from the uploaded file. Eligibility depends on holdings at the record date and on account-level restrictions."))
  if errors:
    record.alerts.append(Alert(
      category="data_quality", severity="medium", origin="rule",
      title=f"Holdings file has {errors} row(s) with errors",
      detail="See the holdings summary for the affected rows. Fix the file or review those positions manually."))

  stage.details = {"holdings_rows": holdings.rows_read, "matched": len(matches) - uncertain,
                    "uncertain": uncertain, "not_matched": not_matched}


# ---------- Orquestador ----------
def run_pipeline(analysis_id: str) -> None:
  """Se ejecuta en segundo plano. Nunca lanza: deja el resultado o el error en el registro."""
  record = repository.get(analysis_id)
  if record is None:
    logger.error("Pipeline started for unknown analysis %s", analysis_id)
    return

  started = time.perf_counter()
  ctx: dict = {"documents": [], "holdings": None, "chunks": [], "rule_alerts": [],
                "today": datetime.now(timezone.utc).date()}
  try:
    _run_stage(record, "parse", "Reading documents", lambda st: _parse(record, st, ctx), fatal=True)
    _run_stage(record, "extract", "Extracting event data", lambda st: _extract(record, st, ctx), fatal=True)
    _run_stage(record, "validate", "Checking dates and required fields", lambda st: _validate(record, st, ctx), fatal=False)

    if not _run_stage(record, "retrieve", "Retrieving policy context", lambda st: _retrieve(record, st, ctx), fatal=False):
      record.alerts.append(Alert(
        category="risk", severity="medium", origin="rule", title="Policy context unavailable",
        detail="The knowledge base could not be queried, so the analysis is not grounded in internal policies."))
    if not _run_stage(record, "analyze", "Generating operational analysis", lambda st: _analyze(record, st, ctx), fatal=False):
      record.alerts.append(Alert(
        category="risk", severity="high", origin="rule", title="AI operational analysis unavailable",
        detail="The summary and AI-generated findings could not be produced. Review the source documents manually."))
    if not _run_stage(record, "match", "Matching holdings", lambda st: _match(record, st, ctx), fatal=False):
      record.alerts.append(Alert(
        category="risk", severity="high", origin="rule", title="Holdings matching failed",
        detail="Affected accounts could not be identified. Check the holdings file and retry."))

    record.status, record.error = "completed", None
  except PipelineError as exc:
    record.status, record.error = "failed", str(exc)
  except Exception:  # noqa: BLE001
    logger.exception("Pipeline crashed for analysis %s", analysis_id)
    record.status, record.error = "failed", "Unexpected internal error."

  record.alerts = rules.finalize_alerts(record.alerts)
  record.total_runtime_ms = int((time.perf_counter() - started) * 1000)
  try:
    repository.save(record)
  except repository.RepositoryError:
    logger.exception("Could not save the final state of analysis %s", analysis_id)