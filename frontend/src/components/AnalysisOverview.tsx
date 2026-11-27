import type { OverviewResponse } from "../api/types";
import { formatDate, humanize } from "../lib/format";
import { Panel, ResultItem } from "./Panel";

export function AnalysisOverview({ overview }: { overview: OverviewResponse }) {
  const event = overview.event;

  const rows: [string, string][] = [
    [
      "Event classification",
      overview.event_label ?? humanize(event?.event_type),
    ],
    ["Company", event?.company_name ?? "—"],
    ["Security ID", event?.isin ?? event?.cusip ?? event?.ticker ?? "—"],
    ["Record date", formatDate(event?.record_date)],
    [
      "Election deadline",
      overview.election_display ?? formatDate(event?.election_deadline),
    ],
  ];

  return (
    <Panel
      title="Analysis Overview"
      description="Extracted from the announcement"
    >
      {rows.map(([title, value]) => (
        <ResultItem key={title} title={title}>
          {value}
        </ResultItem>
      ))}

      {overview.summary && (
        <ResultItem title="Summary">{overview.summary}</ResultItem>
      )}
      {overview.required_actions.length > 0 && (
        <ResultItem title="Required actions">
          <ul className="list-disc pl-5">
            {overview.required_actions.map((text) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
        </ResultItem>
      )}
      {overview.next_steps.length > 0 && (
        <ResultItem title="Next steps">
          <ul className="list-disc pl-5">
            {overview.next_steps.map((text) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
        </ResultItem>
      )}
    </Panel>
  );
}
