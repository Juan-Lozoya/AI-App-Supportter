import type { DashboardStats } from "../api/types";

export function StatCards({ stats }: { stats: DashboardStats }) {
  const cards = [
    { label: "Total Events", value: stats.total_events, note: "All analyses" },
    {
      label: "Pending Review",
      value: stats.pending_review,
      note: "Awaiting validation",
    },
    {
      label: "Action Required",
      value: stats.action_required,
      note: "Needs attention",
    },
    { label: "Completed", value: stats.completed, note: "Reviewed and closed" },
  ];

  return (
    <ul className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <li
          key={card.label}
          className="rounded-xl border border-line bg-white p-[22px]"
        >
          <div className="text-[13px] text-muted">{card.label}</div>
          <div className="mt-3 text-[28px] font-bold">{card.value}</div>
          <div className="mt-2 text-xs text-muted">{card.note}</div>
        </li>
      ))}
    </ul>
  );
}
