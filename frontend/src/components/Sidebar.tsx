const NAV_ITEMS = [
  "Dashboard",
  "New Analysis",
  "All Events",
  "Pending Review",
  "Reports",
  "Settings",
];

export default function Sidebar() {
  return (
    <nav className="sidebar" aria-label="Main navigation">
      <div className="logo">
        Corporate <span>Actions</span>
      </div>
      {NAV_ITEMS.map((item, index) => (
        <div key={item} className={`nav-item ${index === 0 ? "active" : ""}`}>
          {item}
        </div>
      ))}
    </nav>
  );
}
