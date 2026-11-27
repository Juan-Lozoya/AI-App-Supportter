import type { AlertsResponse } from "../api/types";
import { humanize, severityTone } from "../lib/format";
import { Badge } from "./Badge";
import { Panel } from "./Panel";

export function RiskAlerts({ data }: { data: AlertsResponse }) {
  const sources = new Map(data.sources.map((source) => [source.id, source]));

  return (
    <Panel title="Risk & Information Alerts">
      {data.alerts.length === 0 ? (
        <p className="text-[13px] text-muted">No alerts for this analysis.</p>
      ) : (
        data.alerts.map((alert) => {
          const cited = alert.source_ids.flatMap((id) => sources.get(id) ?? []);
          return (
            <div
              key={alert.id || alert.title}
              className="border-b border-[#edf0f4] py-4 last:border-b-0"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={severityTone(alert.severity)}>
                  {humanize(alert.severity)}
                </Badge>
                <span className="text-xs text-muted">
                  {humanize(alert.category)} ·{" "}
                  {alert.origin === "ai" ? "AI" : "Rule"}
                </span>
              </div>
              <p className="mt-2.5 text-sm font-bold">{alert.title}</p>
              <p className="mt-1 text-[13px] leading-relaxed text-muted">
                {alert.detail}
              </p>
              {cited.length > 0 && (
                <details className="mt-2 text-xs text-muted">
                  <summary className="cursor-pointer">
                    Sources ({cited.length})
                  </summary>
                  <ul className="mt-1 space-y-1">
                    {cited.map((source) => (
                      <li key={source.id}>
                        <span className="font-bold">{source.document}:</span>{" "}
                        {source.excerpt}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          );
        })
      )}
    </Panel>
  );
}
