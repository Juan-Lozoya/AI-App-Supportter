const SAMPLE_STATS = [
  { label: "Total Events", value: 128, description: "Sample dashboard data" },
  { label: "Pending Review", value: 14, description: "Sample dashboard data" },
  { label: "Action Required", value: 8, description: "Sample dashboard data" },
  { label: "Completed", value: 106, description: "Sample dashboard data" },
];

export default function StatCards() {
  return (
    <div className="cards">
      {SAMPLE_STATS.map((stat) => (
        <div className="card" key={stat.label}>
          <div className="card-label">{stat.label}</div>
          <div className="card-value">{stat.value}</div>
          <div className="card-description">{stat.description}</div>
        </div>
      ))}
    </div>
  );
}
