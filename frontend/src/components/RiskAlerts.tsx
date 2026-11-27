const SAMPLE_ALERTS = [
  {
    label: "Review Required",
    className: "status-review",
    text: "Verify security eligibility and holdings before processing.",
  },
  {
    label: "Missing Information",
    className: "status-action",
    text: "Confirm whether an election deadline applies to the event.",
  },
];

export default function RiskAlerts() {
  return (
    <div className="panel">
      <h2>Risk & Information Alerts</h2>
      <p className="panel-description">Sample data</p>
      {SAMPLE_ALERTS.map((alert) => (
        <div className="result-item" key={alert.label}>
          <span className={`status ${alert.className}`}>{alert.label}</span>
          <p className="result-text" style={{ marginTop: 10 }}>
            {alert.text}
          </p>
        </div>
      ))}
    </div>
  );
}
