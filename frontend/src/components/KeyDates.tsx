import type { KeyDatesResponse } from "../api/types";
import { formatDate } from "../lib/format";
import { Badge } from "./Badge";
import { Panel } from "./Panel";

type KeyDate = KeyDatesResponse["dates"][number];

function dateBadge(item: KeyDate) {
  switch (item.state) {
    case "upcoming":
      return (
        <Badge tone="amber">
          {item.days_remaining != null
            ? `In ${item.days_remaining} day(s)`
            : "Upcoming"}
        </Badge>
      );
    case "today":
      return <Badge tone="red">Today</Badge>;
    case "passed":
      return <Badge tone="slate">Passed</Badge>;
    default:
      return <Badge tone="slate">Not specified</Badge>;
  }
}

export function KeyDates({ data }: { data: KeyDatesResponse }) {
  return (
    <Panel title="Key Dates" description={`As of ${formatDate(data.as_of)}`}>
      <ul>
        {data.dates.map((item) => (
          <li
            key={item.key}
            className="flex items-start justify-between gap-3 border-b border-[#edf0f4] py-3 last:border-b-0"
          >
            <div>
              <div className="text-sm font-bold">{item.label}</div>
              <div className="text-[13px] text-muted">
                {formatDate(item.date)}
                {item.note && ` — ${item.note}`}
              </div>
            </div>
            {dateBadge(item)}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
