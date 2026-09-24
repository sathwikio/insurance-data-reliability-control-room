"""Regenerate web/src/data/runs.json from data/final_analytics.csv.

Keeps the public Next.js dashboard in sync with the deterministic final table.
Run: python scripts/sync_web_data.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "final_analytics.csv"
DST = ROOT / "web" / "src" / "data" / "runs.json"

FIELDS = [
    "run_id",
    "pipeline_name",
    "domain",
    "run_timestamp",
    "status",
    "failure_rate",
    "freshness_delay_minutes",
    "freshness_severity",
    "jev_decision",
    "jev_confidence",
]


def main() -> None:
    with open(SRC, newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        out.append(
            {
                "run_id": r["run_id"],
                "pipeline_name": r["pipeline_name"],
                "domain": r["domain"],
                "run_timestamp": r["run_timestamp"],
                "status": r["status"],
                "failure_rate": float(r["failure_rate"]),
                "freshness_delay_minutes": int(r["freshness_delay_minutes"]),
                "freshness_severity": r["freshness_severity"],
                "jev_decision": r["jev_decision"],
                "jev_confidence": float(r["jev_confidence"]) if r.get("jev_confidence") else None,
            }
        )
    out.sort(key=lambda x: x["run_id"])
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {len(out)} runs to {DST}")


if __name__ == "__main__":
    main()
