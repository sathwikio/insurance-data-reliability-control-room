"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { avgFreshnessByPipeline } from "@/lib/stats";

export default function FreshnessBars() {
  const data = avgFreshnessByPipeline();
  return (
    <div className="panel">
      <h3>Average Freshness Delay by Pipeline (minutes)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 4, right: 12, bottom: 0, left: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e3e6ea" />
          <XAxis type="number" fontSize={11} />
          <YAxis type="category" dataKey="pipeline_name" fontSize={11} width={208} />
          <Tooltip formatter={(value) => `${value} min avg delay`} />
          <Bar dataKey="avg_freshness_delay" fill="#3a6ea5" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
