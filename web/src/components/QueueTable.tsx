import { investigationQueue } from "@/lib/stats";

export default function QueueTable() {
  const rows = investigationQueue();
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Pipeline</th>
            <th>Domain</th>
            <th>Decision</th>
            <th>Confidence</th>
            <th>Status</th>
            <th>Freshness severity</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={`${r.pipeline_name}-${i}`}>
              <td>{r.pipeline_name}</td>
              <td>{r.domain}</td>
              <td>
                <span className={`badge ${r.jev_decision}`}>{r.jev_decision}</span>
              </td>
              <td>{r.jev_confidence === null ? "n/a" : r.jev_confidence.toFixed(2)}</td>
              <td>{r.status}</td>
              <td>{r.freshness_severity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
