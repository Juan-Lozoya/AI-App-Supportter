const SAMPLE_ROWS = [
  {
    account: "10001",
    securityId: "US1234567890",
    company: "ABC Corporation",
    quantity: 150,
    event: "Stock Split",
    reviewed: false,
  },
  {
    account: "10002",
    securityId: "US1234567890",
    company: "ABC Corporation",
    quantity: 500,
    event: "Stock Split",
    reviewed: false,
  },
  {
    account: "10003",
    securityId: "US1234567890",
    company: "ABC Corporation",
    quantity: 200,
    event: "Stock Split",
    reviewed: true,
  },
];

export default function HoldingsTable() {
  return (
    <div className="panel table-panel">
      <h2>Affected Portfolio Holdings</h2>
      <p className="panel-description">
        Sample data – actual holdings will be populated by the backend.
      </p>
      <table>
        <thead>
          <tr>
            <th>Account</th>
            <th>Security ID</th>
            <th>Company</th>
            <th>Quantity</th>
            <th>Event</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {SAMPLE_ROWS.map((row) => (
            <tr key={row.account}>
              <td>{row.account}</td>
              <td>{row.securityId}</td>
              <td>{row.company}</td>
              <td>{row.quantity}</td>
              <td>{row.event}</td>
              <td>
                <span
                  className={`status ${row.reviewed ? "status-complete" : "status-review"}`}
                >
                  {row.reviewed ? "Reviewed" : "Pending Review"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
