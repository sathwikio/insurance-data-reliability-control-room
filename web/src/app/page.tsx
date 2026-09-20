import DecisionDonut from "@/components/DecisionDonut";
import DomainBars from "@/components/DomainBars";
import FreshnessBars from "@/components/FreshnessBars";
import HealthTable from "@/components/HealthTable";
import KpiCards from "@/components/KpiCards";
import QueueTable from "@/components/QueueTable";

const GITHUB_URL = "https://github.com/sathwikio/insurance-data-reliability-control-room";

export default function Page() {
  return (
    <div className="container">
      <header className="top">
        <h1>Insurance Data Reliability Control Room</h1>
        <a href={GITHUB_URL}>GitHub repository</a>
      </header>
      <p className="note">
        Public demo using synthetic data. The data pipeline was tested in Databricks Free
        Edition.
      </p>

      <section aria-label="Key metrics">
        <KpiCards />
      </section>

      <section aria-label="Distributions">
        <h2>Distributions</h2>
        <div className="grid-2">
          <DecisionDonut />
          <DomainBars />
        </div>
      </section>

      <section aria-label="Freshness">
        <h2>Freshness</h2>
        <FreshnessBars />
      </section>

      <section aria-label="Pipeline health and investigation queue">
        <div className="grid-tables">
          <div>
            <h2>Pipeline Health Table</h2>
            <HealthTable />
          </div>
          <div>
            <h2>Investigation Queue</h2>
            <QueueTable />
          </div>
        </div>
      </section>

      <footer>
        <span>Synthetic demo data. Deterministic metrics with a Jev decision layer.</span>
        <a href={GITHUB_URL}>GitHub repository</a>
      </footer>
    </div>
  );
}
