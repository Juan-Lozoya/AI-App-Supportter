import { Link, createFileRoute } from "@tanstack/react-router";

import { useDashboardStats } from "../api/hooks";
import { ApiStatus } from "../components/ApiStatus";
import { Badge } from "../components/Badge";
import { Header } from "../components/Header";
import { Panel } from "../components/Panel";
import { StatCards } from "../components/StatCards";
import { analysisTone, formatDate, humanize, reviewTone } from "../lib/format";

export const Route = createFileRoute("/")({ component: Dashboard });

const columns = [
  "Company",
  "Security ID",
  "Event",
  "Record date",
  "Accounts",
  "High alerts",
  "Status",
  "Review",
];
const th = "bg-slate-50 px-3 py-3.5 text-left text-[13px] font-bold text-muted";
const td = "border-b border-line px-3 py-3.5 text-[13px] text-slate-700";

function Dashboard() {
  const { data, isPending, error } = useDashboardStats();

  return (
    <>
      <Header
        title="Corporate Actions Analyzer"
        subtitle="AI-powered corporate action analysis and operations workflow"
        actions={
          <Link
            to="/analyses/new"
            className="rounded-lg bg-brand px-4 py-3 text-sm font-bold text-white hover:bg-brand-dark"
          >
            New analysis
          </Link>
        }
      />

      {isPending && <ApiStatus state="loading" title="Loading dashboard…" />}
      {error && (
        <ApiStatus state="error" title="Could not load the dashboard">
          {error.message}
        </ApiStatus>
      )}

      {data && (
        <>
          <StatCards stats={data} />
          {data.processing > 0 && (
            <p className="mb-5 text-sm text-sky-800">
              {data.processing} analysis(es) running…
            </p>
          )}

          <Panel title="Recent analyses">
            {data.recent.length === 0 ? (
              <p className="text-[13px] text-muted">
                No analyses yet.{" "}
                <Link to="/analyses/new" className="font-bold text-brand">
                  Start the first one.
                </Link>
              </p>
            ) : (
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
                    {data.recent.map((item) => (
                      <tr key={item.analysis_id}>
                        <td className={td}>
                          <Link
                            to="/analyses/$analysisId"
                            params={{ analysisId: item.analysis_id }}
                            className="font-bold text-brand hover:underline"
                          >
                            {item.company_name ?? item.analysis_id}
                          </Link>
                        </td>
                        <td className={td}>{item.security_id ?? "—"}</td>
                        <td className={td}>{humanize(item.event_type)}</td>
                        <td className={td}>{formatDate(item.record_date)}</td>
                        <td className={td}>{item.affected_accounts}</td>
                        <td className={td}>{item.high_alerts}</td>
                        <td className={td}>
                          <Badge tone={analysisTone(item.status)}>
                            {humanize(item.status)}
                          </Badge>
                        </td>
                        <td className={td}>
                          <Badge tone={reviewTone(item.review_status)}>
                            {humanize(item.review_status)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </>
      )}
    </>
  );
}
