"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DECISIONS, DECISION_COLORS, decisionByDomain } from "@/lib/stats";

export default function DomainBars() {
  const data = decisionByDomain();
  return (
    <div className="panel">
      <h3>Decision by Domain</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e3e6ea" />
          <XAxis dataKey="domain" fontSize={11} interval={0} angle={-18} dy={8} height={52} />
          <YAxis fontSize={11} allowDecimals={false} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {DECISIONS.map((d) => (
            <Bar key={d} dataKey={d} stackId="decisions" fill={DECISION_COLORS[d]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
