import runs from "@/data/runs.json";

export type Decision = "HEALTHY" | "WATCH" | "INVESTIGATE" | "BLOCK";

export interface Run {
  run_id: string;
  pipeline_name: string;
  domain: string;
  run_timestamp: string;
  status: string;
  failure_rate: number;
  freshness_delay_minutes: number;
  freshness_severity: string;
  jev_decision: Decision;
  jev_confidence: number | null;
}

export const RUNS = runs as Run[];

export const DECISIONS: Decision[] = ["HEALTHY", "WATCH", "INVESTIGATE", "BLOCK"];

export const DECISION_COLORS: Record<Decision, string> = {
  HEALTHY: "#2f9e6e",
  WATCH: "#d9a521",
  INVESTIGATE: "#e0722a",
  BLOCK: "#cf4444",
};

const ATTENTION: Decision[] = ["WATCH", "INVESTIGATE"];

export interface Kpis {
  total: number;
  healthyPct: number;
  attention: number;
  blocked: number;
  byDecision: Record<Decision, number>;
}

export function kpis(runs: Run[] = RUNS): Kpis {
  const byDecision = Object.fromEntries(
    DECISIONS.map((d) => [d, runs.filter((r) => r.jev_decision === d).length]),
  ) as Record<Decision, number>;
  const total = runs.length;
  return {
    total,
    healthyPct: total === 0 ? 0 : (byDecision.HEALTHY / total) * 100,
    attention: runs.filter((r) => ATTENTION.includes(r.jev_decision)).length,
    blocked: byDecision.BLOCK,
    byDecision,
  };
}

export interface DomainRow {
  domain: string;
  HEALTHY: number;
  WATCH: number;
  INVESTIGATE: number;
  BLOCK: number;
}

export function decisionByDomain(runs: Run[] = RUNS): DomainRow[] {
  const domains = [...new Set(runs.map((r) => r.domain))].sort();
  return domains.map((domain) => {
    const inDomain = runs.filter((r) => r.domain === domain);
    return {
      domain,
      HEALTHY: inDomain.filter((r) => r.jev_decision === "HEALTHY").length,
      WATCH: inDomain.filter((r) => r.jev_decision === "WATCH").length,
      INVESTIGATE: inDomain.filter((r) => r.jev_decision === "INVESTIGATE").length,
      BLOCK: inDomain.filter((r) => r.jev_decision === "BLOCK").length,
    };
  });
}

export interface FreshnessRow {
  pipeline_name: string;
  avg_freshness_delay: number;
}

export function avgFreshnessByPipeline(runs: Run[] = RUNS): FreshnessRow[] {
  const names = [...new Set(runs.map((r) => r.pipeline_name))].sort();
  return names.map((pipeline_name) => {
    const group = runs.filter((r) => r.pipeline_name === pipeline_name);
    const avg = group.reduce((s, r) => s + r.freshness_delay_minutes, 0) / group.length;
    return { pipeline_name, avg_freshness_delay: Math.round(avg * 100) / 100 };
  });
}

export interface HealthRow {
  pipeline_name: string;
  domain: string;
  total_runs: number;
  healthy_pct: number;
  attention_runs: number;
  blocked_runs: number;
  avg_freshness_delay: number;
  avg_failure_rate: number;
}

export function healthTable(runs: Run[] = RUNS): HealthRow[] {
  const names = [...new Set(runs.map((r) => r.pipeline_name))].sort();
  return names.map((pipeline_name) => {
    const group = runs.filter((r) => r.pipeline_name === pipeline_name);
    const n = group.length;
    const healthy = group.filter((r) => r.jev_decision === "HEALTHY").length;
    return {
      pipeline_name,
      domain: group[0].domain,
      total_runs: n,
      healthy_pct: Math.round((healthy / n) * 1000) / 10,
      attention_runs: group.filter((r) => ATTENTION.includes(r.jev_decision)).length,
      blocked_runs: group.filter((r) => r.jev_decision === "BLOCK").length,
      avg_freshness_delay:
        Math.round((group.reduce((s, r) => s + r.freshness_delay_minutes, 0) / n) * 100) / 100,
      avg_failure_rate:
        Math.round((group.reduce((s, r) => s + r.failure_rate, 0) / n) * 100) / 100,
    };
  });
}

export interface QueueRow {
  pipeline_name: string;
  domain: string;
  jev_decision: "INVESTIGATE" | "BLOCK";
  jev_confidence: number | null;
  status: string;
  freshness_severity: string;
}

export function investigationQueue(runs: Run[] = RUNS): QueueRow[] {
  return runs
    .filter((r) => r.jev_decision === "INVESTIGATE" || r.jev_decision === "BLOCK")
    .map((r) => ({
      pipeline_name: r.pipeline_name,
      domain: r.domain,
      jev_decision: r.jev_decision as "INVESTIGATE" | "BLOCK",
      jev_confidence: r.jev_confidence,
      status: r.status,
      freshness_severity: r.freshness_severity,
    }))
    .sort((a, b) => (a.jev_confidence ?? 0) - (b.jev_confidence ?? 0));
}
