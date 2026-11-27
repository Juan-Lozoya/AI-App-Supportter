import { useUpdateHolding } from "../api/hooks";
import type { HoldingMatch, HoldingsResponse } from "../api/types";
import { REVIEWER, humanize, reviewTone } from "../lib/format";
import { Badge } from "./Badge";
import { Panel } from "./Panel";

interface HoldingsTableProps {
  analysisId: string;
  data: HoldingsResponse;
}

const columns = [
  "Account",
  "Security ID",
  "Company",
  "Quantity",
  "Event",
  "Match",
  "Status",
  "Actions",
];
const th = "bg-slate-50 px-3 py-3.5 text-left text-[13px] font-bold text-muted";
const td = "border-b border-line px-3 py-3.5 text-[13px] text-slate-700";
const action =
  "rounded-md bg-brand-soft px-2.5 py-1 text-xs font-bold text-brand disabled:opacity-50";

export function HoldingsTable({ analysisId, data }: HoldingsTableProps) {
  const update = useUpdateHolding(analysisId);

  function setStatus(
    match: HoldingMatch,
    review_status: HoldingMatch["review_status"],
  ) {
    update.mutate({
      matchId: match.match_id,
      body: { review_status, reviewer: REVIEWER },
    });
  }

  const summary = data.summary;

  return (
    <Panel
      title="Affected Portfolio Holdings"
      description={
        summary
          ? `${summary.filename ?? "Holdings file"}: ${summary.rows_read} rows read · ${summary.matched} matched · ${summary.uncertain} uncertain · ${summary.not_matched} not matched`
          : "No holdings file was uploaded for this analysis."
      }
    >
      {summary?.matches_truncated && (
        <p className="mb-3 text-[13px] text-amber-700">
          The list is truncated. Only part of the matches is shown.
        </p>
      )}
      {summary && summary.issues.length > 0 && (
        <ul className="mb-3 text-[13px] text-amber-700">
          {summary.issues.map((issue, index) => (
            <li key={index}>
              {issue.source_row != null && `Row ${issue.source_row}: `}
              {issue.message}
            </li>
          ))}
        </ul>
      )}
      {update.error && (
        <p role="alert" className="mb-3 text-[13px] text-red-700">
          {update.error.message}
        </p>
      )}

      {data.matches.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                {columns.map((label) => (
                  <th key={label} className={th}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.matches.map((match) => {
                const busy =
                  update.isPending &&
                  update.variables?.matchId === match.match_id;
                return (
                  <tr key={match.match_id}>
                    <td className={td}>
                      {match.account_id}
                      <div className="text-xs text-muted">
                        {match.account_name}
                      </div>
                    </td>
                    <td className={td}>{match.security_id}</td>
                    <td className={td}>{match.security_name}</td>
                    <td className={td}>
                      {match.quantity?.toLocaleString("en-US") ?? "—"}
                    </td>
                    <td className={td}>{humanize(match.event_type)}</td>
                    <td className={td} title={match.reason}>
                      {match.match_type.toUpperCase()}{" "}
                      <Badge
                        tone={match.confidence === "high" ? "green" : "amber"}
                      >
                        {humanize(match.confidence)}
                      </Badge>
                    </td>
                    <td className={td}>
                      <Badge tone={reviewTone(match.review_status)}>
                        {humanize(match.review_status)}
                      </Badge>
                    </td>
                    <td className={`${td} whitespace-nowrap`}>
                      <button
                        className={action}
                        disabled={busy || match.review_status === "reviewed"}
                        onClick={() => setStatus(match, "reviewed")}
                      >
                        Mark reviewed
                      </button>{" "}
                      <button
                        className={action}
                        disabled={busy || match.review_status === "flagged"}
                        onClick={() => setStatus(match, "flagged")}
                      >
                        Flag
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
