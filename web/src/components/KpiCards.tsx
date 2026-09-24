import { kpis } from "@/lib/stats";

const CARDS = [
  { key: "total", label: "Total Pipeline Runs" },
  { key: "healthyPct", label: "Healthy Percentage", suffix: "%" },
  { key: "attention", label: "Pipelines Requiring Attention" },
  { key: "blocked", label: "Blocked Pipelines" },
] as const;

function format(key: (typeof CARDS)[number]["key"], value: number): string {
  if (key === "healthyPct") return `${value.toFixed(1)}%`;
  return `${value}`;
}

export default function KpiCards() {
  const k = kpis();
  const values: Record<(typeof CARDS)[number]["key"], number> = {
    total: k.total,
    healthyPct: k.healthyPct,
    attention: k.attention,
    blocked: k.blocked,
  };
  return (
    <div className="kpis">
      {CARDS.map((card) => (
        <div className="kpi" key={card.key}>
          <div className="label">{card.label}</div>
          <div className="value">{format(card.key, values[card.key])}</div>
        </div>
      ))}
    </div>
  );
}
