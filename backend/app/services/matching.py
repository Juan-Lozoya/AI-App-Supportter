"""Cruce determinista entre el evento y los holdings. No usa el modelo."""
import re

from app.schemas import ExtractedEvent, HoldingMatch
from app.services.holdings import ISIN_RE, HoldingsResult

MAX_MATCHES = 500
_NAME_NOISE = {"inc", "corp", "corporation", "plc", "ag", "sa", "nv", "ltd", "llc", "co", "company", "group", "holdings", "holding"}


def _normalize_name(name: str | None) -> str:
  words = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower()).split()
  return " ".join(w for w in words if w not in _NAME_NOISE)


def _embedded_cusip(isin: str | None) -> str:
  return isin[2:11] if isin and ISIN_RE.match(isin) and isin[:2] in {"US", "CA"} else ""


def _classify(event: ExtractedEvent, h) -> tuple[str, str, str] | None:
  """Devuelve (match_type, confidence, reason) o None si no coincide."""
  ev_isin, ev_cusip = event.isin or "", event.cusip or ""
  ev_cusip_any = ev_cusip or _embedded_cusip(ev_isin)

  if ev_isin and h.isin == ev_isin:
    return "isin", "high", "ISIN matches the event exactly."
  if ev_cusip_any and (h.cusip == ev_cusip_any or _embedded_cusip(h.isin) == ev_cusip_any):
    return "cusip", "high", "CUSIP matches the event."

  if event.ticker and h.ticker == event.ticker:
    if h.isin and ev_isin and h.isin != ev_isin:
      return "ticker", "uncertain", (
        f"Ticker matches but the holding's ISIN ({h.isin}) differs from the event ISIN ({ev_isin}). "
        "Possible ISIN change or a different listing."
      )
    return "ticker", "uncertain", "Matched by ticker only; no ISIN or CUSIP in the holdings file to confirm."

  ev_name, h_name = _normalize_name(event.company_name), _normalize_name(h.security_name)
  if ev_name and ev_name == h_name:
    return "name", "uncertain", "Matched by company name only; no identifier matched."
  return None


def match_holdings(event: ExtractedEvent, holdings: HoldingsResult) -> tuple[list[HoldingMatch], int, bool]:
  """Devuelve (coincidencias, filas sin coincidencia, si se truncó la lista)."""
  matches: list[HoldingMatch] = []
  for h in holdings.holdings:
    found = _classify(event, h)
    if not found:
      continue
    match_type, confidence, reason = found
    if h.quantity is None:
      reason += " The quantity in the file is invalid."
    matches.append(HoldingMatch(
      match_id=f"m{h.source_row}", source_row=h.source_row, account_id=h.account_id,
      account_name=h.account_name, security_id=h.isin or h.cusip or h.ticker,
      security_name=h.security_name, quantity=h.quantity, currency=h.currency,
      match_type=match_type, confidence=confidence, reason=reason, event_type=event.event_type,
    ))

  not_matched = len(holdings.holdings) - len(matches)
  matches.sort(key=lambda m: (m.confidence != "high", m.account_id, m.source_row))
  truncated = len(matches) > MAX_MATCHES
  return matches[:MAX_MATCHES], not_matched, truncated