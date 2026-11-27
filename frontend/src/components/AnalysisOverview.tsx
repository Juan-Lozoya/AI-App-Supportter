const SAMPLE_FIELDS = [
  { title: "Event Classification", value: "Stock Split" },
  { title: "Company", value: "ABC Corporation" },
  { title: "Security ID", value: "US1234567890" },
  { title: "Record Date", value: "December 10, 2026" },
  { title: "Election Deadline", value: "Not applicable" },
];

export default function AnalysisOverview() {
  return (
    <div className="panel">
      <h2>Analysis Overview</h2>
      <p className="panel-description">
        Sample data – not a real analysis result
      </p>
      {SAMPLE_FIELDS.map((field) => (
        <div className="result-item" key={field.title}>
          <div className="result-title">{field.title}</div>
          <div className="result-text">{field.value}</div>
        </div>
      ))}
    </div>
  );
}
