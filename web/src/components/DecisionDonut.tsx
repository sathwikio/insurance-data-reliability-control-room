"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { DECISIONS, DECISION_COLORS, kpis } from "@/lib/stats";

export default function DecisionDonut() {
  const k = kpis();
  const data = DECISIONS.map((d) => ({ name: d, value: k.byDecision[d] }));
  return (
    <div className="panel">
      <h3>Decision Distribution</h3>
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={52} outerRadius={88}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={DECISION_COLORS[entry.name]} />
            ))}
          </Pie>
          <Tooltip formatter={(value, name) => `${name}: ${value} runs`} />
          <Legend layout="vertical" align="right" verticalAlign="middle" wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
