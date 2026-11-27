import { createFileRoute } from "@tanstack/react-router";

import {
  useAlerts,
  useAnalysis,
  useHoldings,
  useKeyDates,
  useOverview,
  useRetryAnalysis,
} from "../api/hooks";
import { AnalysisOverview } from "../components/AnalysisOverview";
import { ApiStatus, SectionState } from "../components/ApiStatus";
import { Badge } from "../components/Badge";
import { Header } from "../components/Header";
import { HoldingsTable } from "../components/HoldingsTable";
import { KeyDates } from "../components/KeyDates";
import { Panel } from "../components/Panel";
import { ProcessingStages } from "../components/ProcessingStages";
import { ReviewPanel } from "../components/ReviewPanel";
import { RiskAlerts } from "../components/RiskAlerts";
import { analysisTone, formatDate, humanize, reviewTone } from "../lib/format";

export const Route = createFileRoute("/analyses/$analysisId")({
  component: AnalysisPage,
});

function AnalysisPage() {
  const { analysisId } = Route.useParams();
  const analysis = useAnalysis(analysisId);
  const completed = analysis.data?.status === "completed";

  // Las secciones se piden solo cuando el análisis terminó.
  const overview = useOverview(analysisId, completed);
  const alerts = useAlerts(analysisId, completed);
  const holdings = useHoldings(analysisId, completed);
  const dates = useKeyDates(analysisId, completed);
  const retry = useRetryAnalysis(analysisId);

  if (analysis.isPending)
    return <ApiStatus state="loading" title="Loading analysis…" />;
  if (analysis.error) {
    return (
      <ApiStatus state="error" title="Could not load the analysis">
        {analysis.error.message}
      </ApiStatus>
    );
  }

  const data = analysis.data;

  return (
    <>
      <Header
        title={data.event?.company_name ?? "Analysis"}
        subtitle={`Created ${formatDate(data.created_at)} · ID ${data.analysis_id}`}
        actions={
          <>
            <Badge tone={analysisTone(data.status)}>
              {humanize(data.status)}
            </Badge>
            <Badge tone={reviewTone(data.review_status)}>
              {humanize(data.review_status)}
            </Badge>
            {data.status === "failed" && (
              <button
                onClick={() => retry.mutate()}
                disabled={retry.isPending}
                className="rounded-lg bg-brand px-4 py-3 text-sm font-bold text-white hover:bg-brand-dark disabled:opacity-60"
              >
                {retry.isPending ? "Retrying…" : "Retry analysis"}
              </button>
            )}
          </>
        }
      />

      {data.status === "processing" && (
        <ApiStatus state="loading" title="Analysis in progress">
          This page updates automatically.
        </ApiStatus>
      )}
      {data.error && (
        <ApiStatus state="error" title="The analysis failed">
          {data.error}
        </ApiStatus>
      )}
      {retry.error && (
        <ApiStatus state="error" title="Could not retry the analysis">
          {retry.error.message}
        </ApiStatus>
      )}

      {!completed ? (
        <div className="mt-5 max-w-3xl">
          <ProcessingStages
            stages={data.stages}
            totalRuntimeMs={data.total_runtime_ms}
          />
        </div>
      ) : (
        <>
          <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              {overview.data ? (
                <AnalysisOverview overview={overview.data} />
              ) : (
                <Panel title="Analysis Overview">
                  <SectionState error={overview.error} />
                </Panel>
              )}
              {dates.data ? (
                <KeyDates data={dates.data} />
              ) : (
                <Panel title="Key Dates">
                  <SectionState error={dates.error} />
                </Panel>
              )}
              <ReviewPanel
                analysisId={analysisId}
                reviewStatus={data.review_status}
                history={data.review_history}
              />
            </div>
            <div>
              {alerts.data ? (
                <RiskAlerts data={alerts.data} />
              ) : (
                <Panel title="Risk & Information Alerts">
                  <SectionState error={alerts.error} />
                </Panel>
              )}
              <ProcessingStages
                stages={data.stages}
                totalRuntimeMs={data.total_runtime_ms}
              />
            </div>
          </div>

          {holdings.data ? (
            <HoldingsTable analysisId={analysisId} data={holdings.data} />
          ) : (
            <Panel title="Affected Portfolio Holdings">
              <SectionState error={holdings.error} />
            </Panel>
          )}
        </>
      )}
    </>
  );
}
