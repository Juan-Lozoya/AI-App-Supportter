"""Reglas deterministas: lo que se puede verificar en código no se le deja al modelo."""
from datetime import date

from app.schemas import Alert, AnalysisSummary, ExtractedEvent, KeyDate

DATE_FIELDS = [
  ("announcement_date", "Announcement date"),
  ("ex_date", "Ex-date"),
  ("record_date", "Record date"),
  ("payment_date", "Payment date"),
  ("effective_date", "Effective date"),
  ("election_deadline", "Election deadline"),
  ("expiration_date", "Expiration date"),
]

# (campos alternativos, etiqueta). Basta con que uno de los campos esté presente.
COMMON_REQUIRED = [
  (("company_name",), "company name"),
  (("isin", "cusip"), "security identifier (ISIN or CUSIP)"),
]
REQUIRED_BY_EVENT: dict[str, list[tuple[tuple[str, ...], str]]] = {
  "CASH_DIVIDEND": [(("record_date",), "record date"), (("payment_date",), "payment date"),
                    (("dividend_amount",), "dividend amount"), (("currency",), "currency")],
  "STOCK_DIVIDEND": [(("record_date",), "record date"), (("payment_date",), "payment date"),
                      (("distribution_ratio", "exchange_ratio"), "distribution ratio")],
  "STOCK_SPLIT": [(("exchange_ratio",), "split ratio"), (("record_date",), "record date"),
                  (("effective_date",), "effective date")],
  "REVERSE_STOCK_SPLIT": [(("exchange_ratio",), "split ratio"), (("record_date",), "record date"),
                          (("effective_date",), "effective date")],
  "MERGER": [(("effective_date",), "effective date"), (("offer_price", "exchange_ratio"), "offer price or exchange ratio")],
  "ACQUISITION": [(("effective_date",), "effective date"), (("offer_price", "exchange_ratio"), "offer price or exchange ratio")],
  "TENDER_OFFER": [(("offer_price",), "offer price"), (("expiration_date",), "expiration date"),
                    (("election_deadline", "expiration_date"), "election deadline")],
  "RIGHTS_OFFERING": [(("subscription_price",), "subscription price"), (("exchange_ratio",), "rights ratio"),
                      (("record_date",), "record date"), (("expiration_date",), "expiration date")],
  "SPIN_OFF": [(("distribution_ratio",), "distribution ratio"), (("record_date",), "record date"),
                (("effective_date",), "effective date")],
  "BOND_REDEMPTION": [(("offer_price",), "redemption price"), (("effective_date", "payment_date"), "redemption date")],
}
HIGH_IMPACT_FIELDS = {"election_deadline", "expiration_date", "record_date"}
ELECTION_LIKELY = {"MERGER", "ACQUISITION", "TENDER_OFFER", "RIGHTS_OFFERING"}

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_iso(value: str | None) -> date | None:
  if not value:
    return None
  try:
    return date.fromisoformat(value)
  except ValueError:
    return None


def _present(event: ExtractedEvent, key: str) -> bool:
  return getattr(event, key, None) not in (None, "", [])


def missing_alerts(event: ExtractedEvent) -> list[Alert]:
  alerts: list[Alert] = []
  reported: set[str] = set()

  for keys, label in COMMON_REQUIRED + REQUIRED_BY_EVENT.get(event.event_type, []):
    if any(_present(event, k) for k in keys):
      continue
    reported.update(keys)
    severity = "high" if any(k in HIGH_IMPACT_FIELDS for k in keys) else "medium"
    alerts.append(Alert(
      category="missing_information", severity=severity, origin="rule",
      title=f"Missing {label}",
      detail=f"The {label} is not specified in the uploaded documents. Confirm it with the issuer or agent before processing.",
    ))

    if not event.election_deadline and "election_deadline" not in reported:
      if event.election_required:
        alerts.append(Alert(
          category="missing_information", severity="high", origin="rule",
          title="Election deadline missing",
          detail="The documents indicate that holders may need to make an election, but no election deadline is specified.",
        ))
      elif event.election_required is None:
        alerts.append(Alert(
          category="missing_information",
          severity="medium" if event.event_type in ELECTION_LIKELY else "low",
          origin="rule",
          title="Confirm whether an election deadline applies",
          detail="The documents do not say whether an election is required or give an election deadline.",
        ))

    if event.event_type == "UNKNOWN":
        alerts.append(Alert(
          category="missing_information", severity="medium", origin="rule",
          title="Event type could not be determined",
          detail="The documents do not clearly identify the type of corporate action. Classify it manually.",
        ))
  return alerts


def deadline_alerts(event: ExtractedEvent, today: date) -> list[Alert]:
  alerts: list[Alert] = []

  for key, label in (("election_deadline", "Election deadline"), ("expiration_date", "Expiration date")):
    d = parse_iso(getattr(event, key))
    if not d:
      continue
    days = (d - today).days
    if days < 0:
      alerts.append(Alert(
        category="deadline", severity="high", origin="rule", title=f"{label} has passed",
        detail=f"{label} was {d.isoformat()} ({-days} day(s) ago). Confirm whether instructions can still be accepted.",
      ))
    elif days <= 7:
      alerts.append(Alert(
        category="deadline", severity="high", origin="rule", title=f"{label} in {days} day(s)",
        detail=f"{label} is {d.isoformat()}. Confirm that client instructions are being collected in time.",
      ))
    elif days <= 14:
      alerts.append(Alert(
        category="deadline", severity="medium", origin="rule", title=f"{label} in {days} days",
        detail=f"{label} is {d.isoformat()}.",
      ))

  record, payment, ex = parse_iso(event.record_date), parse_iso(event.payment_date), parse_iso(event.ex_date)
  if record and record < today:
    alerts.append(Alert(
      category="deadline", severity="medium", origin="rule", title="Record date has passed",
      detail=f"The record date was {record.isoformat()}. Entitlement depends on positions at the record date, not on current holdings.",
    ))
  if payment and payment < today:
    alerts.append(Alert(
      category="deadline", severity="low", origin="rule", title="Payment date has passed",
      detail=f"The payment date was {payment.isoformat()}. Verify that payment has been received and reconciled.",
    ))
  if ex and record and ex > record:
    alerts.append(Alert(
      category="conflict", severity="medium", origin="rule", title="Ex-date is after the record date",
      detail=f"Ex-date {ex.isoformat()} falls after record date {record.isoformat()}. Verify both dates with the issuer.",
    ))
  if record and payment and payment < record:
    alerts.append(Alert(
      category="conflict", severity="high", origin="rule", title="Payment date is before the record date",
      detail=f"Payment date {payment.isoformat()} is earlier than record date {record.isoformat()}. At least one date is likely wrong.",
    ))
  return alerts


def key_dates(event: ExtractedEvent, today: date) -> list[KeyDate]:
  result = []
  for key, label in DATE_FIELDS:
    value = getattr(event, key)
    d = parse_iso(value)
    if d is None:
      note = "Not applicable" if key == "election_deadline" and event.election_required is False else None
      result.append(KeyDate(key=key, label=label, date=None, state="not_specified",
                            days_remaining=None, note=note or "Not specified in the documents"))
      continue
    days = (d - today).days
    state = "today" if days == 0 else "upcoming" if days > 0 else "passed"
    result.append(KeyDate(key=key, label=label, date=d.isoformat(), state=state, days_remaining=days))
  return result


def election_display(event: ExtractedEvent) -> str:
  if event.election_deadline:
    return event.election_deadline
  return "Not applicable" if event.election_required is False else "Not specified"


def dashboard_bucket(summary: AnalysisSummary) -> str:
  if summary.status == "processing":
    return "processing"
  if summary.status == "failed":
    return "action_required"
  if summary.review_status in ("approved", "rejected"):
    return "completed"
  return "action_required" if summary.high_alerts > 0 else "pending_review"


def finalize_alerts(alerts: list[Alert]) -> list[Alert]:
  ordered = sorted(alerts, key=lambda a: SEVERITY_RANK[a.severity])
  for index, alert in enumerate(ordered, start=1):
    alert.id = f"A{index}"
  return ordered