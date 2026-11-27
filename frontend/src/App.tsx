import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import StatCards from "./components/StatCards";
import AnalysisForm from "./components/AnalysisForm";
import AnalysisOverview from "./components/AnalysisOverview";
import RiskAlerts from "./components/RiskAlerts";
import HoldingsTable from "./components/HoldingsTable";

export default function App() {
  return (
    <>
      <Sidebar />
      <div className="main">
        <Header />
        <StatCards />

        <div className="content-grid">
          <AnalysisForm />
          <div>
            <AnalysisOverview />
            <RiskAlerts />
          </div>
        </div>

        <HoldingsTable />

        <div className="footer">
          Corporate Actions Analyzer | AI-assisted operations | Human validation
          required
        </div>
      </div>
    </>
  );
}
