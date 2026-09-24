import { healthTable } from "@/lib/stats";

export default function HealthTable() {
  const rows = healthTable();
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Pipeline</th>
            <th>Domain</th>
            <th>Total runs</th>
            <th>Healthy %</th>
            <th>Attention</th>
            <th>Blocked</th>
            <th>Avg freshness delay</th>
            <th>Avg failure rate</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.pipeline_name}>
              <td>{r.pipeline_name}</td>
              <td>{r.domain}</td>
              <td>{r.total_runs}</td>
              <td>{r.healthy_pct.toFixed(1)}%</td>
              <td>{r.attention_runs}</td>
              <td>{r.blocked_runs}</td>
              <td>{r.avg_freshness_delay.toFixed(2)}</td>
              <td>{r.avg_failure_rate.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
