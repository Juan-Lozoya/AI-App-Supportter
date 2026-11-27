import logging
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app import config
from app.schemas import AnalysisRecord, AnalysisSummary

logger = logging.getLogger("corpactions.repository")

MAX_ITEM_BYTES = 380_000  # DynamoDB limita cada ítem a 400 KB
SCAN_LIMIT = 2000

_SUMMARY_ATTRS = [
  "analysis_id", "created_at", "#s", "review_status", "company_name", "security_id",
  "event_type", "record_date", "affected_accounts", "high_alerts", "total_runtime_ms", "files_count",
]

_table = None


class RepositoryError(Exception):
  pass


def _get_table():
  global _table
  if _table is None:
    _table = boto3.resource("dynamodb", region_name=config.AWS_REGION).Table(config.ANALYSES_TABLE)
  return _table


def now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()


def summarize(record: AnalysisRecord) -> AnalysisSummary:
  event = record.event
  return AnalysisSummary(
    analysis_id=record.analysis_id,
    created_at=record.created_at,
    status=record.status,
    review_status=record.review_status,
    company_name=event.company_name if event else None,
    security_id=(event.isin or event.cusip or event.ticker) if event else None,
    event_type=event.event_type if event else None,
    record_date=event.record_date if event else None,
    affected_accounts=len({m.account_id for m in record.holdings_matches if m.account_id}),
    high_alerts=sum(1 for a in record.alerts if a.severity == "high"),
    total_runtime_ms=record.total_runtime_ms,
    files_count=len(record.files),
  )


def save(record: AnalysisRecord) -> None:
  record.updated_at = now_iso()
  payload = record.model_dump_json()
  if len(payload.encode("utf-8")) > MAX_ITEM_BYTES:
    raise RepositoryError("Analysis record is too large to store.")
  item = summarize(record).model_dump(mode="json")
  item["record"] = payload
  try:
    _get_table().put_item(Item=item)
  except (BotoCoreError, ClientError) as exc:
    logger.exception("DynamoDB put_item failed for %s", record.analysis_id)
    raise RepositoryError("Could not save the analysis.") from exc


def get(analysis_id: str) -> AnalysisRecord | None:
  try:
    response = _get_table().get_item(Key={"analysis_id": analysis_id})
  except (BotoCoreError, ClientError) as exc:
    logger.exception("DynamoDB get_item failed for %s", analysis_id)
    raise RepositoryError("Could not read the analysis.") from exc
  item = response.get("Item")
  return AnalysisRecord.model_validate_json(item["record"]) if item else None


def _plain(item: dict) -> dict:
    return {k: (int(v) if isinstance(v, Decimal) else v) for k, v in item.items()}


def list_summaries() -> list[AnalysisSummary]:
  """Lee solo los campos de resumen (sin el JSON completo) de todos los análisis."""
  items: list[dict] = []
  kwargs = {
    "ProjectionExpression": ", ".join(_SUMMARY_ATTRS),
    "ExpressionAttributeNames": {"#s": "status"},
  }
  try:
    while len(items) < SCAN_LIMIT:
      response = _get_table().scan(**kwargs)
      items.extend(response.get("Items", []))
      if "LastEvaluatedKey" not in response:
        break
      kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
  except (BotoCoreError, ClientError) as exc:
    logger.exception("DynamoDB scan failed")
    raise RepositoryError("Could not list analyses.") from exc

  summaries = [AnalysisSummary.model_validate(_plain(i)) for i in items]
  return sorted(summaries, key=lambda s: s.created_at, reverse=True)