import type { StageRecord } from "../api/types";
import { formatDuration, humanize, stageTone } from "../lib/format";
import { Badge } from "./Badge";
import { Panel } from "./Panel";

interface ProcessingStagesProps {
  stages: StageRecord[];
  totalRuntimeMs: number | null;
}

export function ProcessingStages({
  stages,
  totalRuntimeMs,
}: ProcessingStagesProps) {
  return (
    <Panel
      title="Processing"
      description={`Total runtime: ${formatDuration(totalRuntimeMs)}`}
    >
      <ol>
        {stages.map((stage) => (
          <li
            key={stage.name}
            className="flex items-start justify-between gap-3 border-b border-[#edf0f4] py-3 last:border-b-0"
          >
            <div>
              <div className="text-sm font-bold">{stage.label}</div>
              <div className="text-xs text-muted">
                {formatDuration(stage.duration_ms)}
              </div>
              {stage.error && (
                <div className="mt-1 text-xs text-red-700">{stage.error}</div>
              )}
            </div>
            <Badge tone={stageTone(stage.status)}>
              {humanize(stage.status)}
            </Badge>
          </li>
        ))}
      </ol>
    </Panel>
  );
}
