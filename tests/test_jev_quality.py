"""Decision-quality invariants for the Jev layer (offline, no API key).

Shape/coverage is tested elsewhere; here we assert semantic sanity:
synthetic `status` must correlate with the bounded Jev label.
"""

import csv
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def _load():
    runs = {r["run_id"]: r for r in csv.DictReader(open(DATA / "pipeline_runs.csv"))}
    decisions = {d["run_id"]: d for d in json.load(open(DATA / "jev_decisions.json"))}
    final = list(csv.DictReader(open(DATA / "final_analytics.csv")))
    return runs, decisions, final


def test_failed_runs_are_blocked():
    runs, decisions, _ = _load()
    failed = [r for r in runs.values() if r["status"] == "failed"]
    assert failed, "expected synthetic failed runs"
    for r in failed:
        assert decisions[r["run_id"]]["decision"] == "BLOCK"


def test_healthy_runs_are_healthy():
    runs, decisions, _ = _load()
    healthy = [r for r in runs.values() if r["status"] == "healthy"]
    assert healthy
    for r in healthy:
        assert decisions[r["run_id"]]["decision"] == "HEALTHY"


def test_degraded_runs_need_attention():
    runs, decisions, _ = _load()
    degraded = [r for r in runs.values() if r["status"] == "degraded"]
    assert degraded
    for r in degraded:
        assert decisions[r["run_id"]]["decision"] in ("WATCH", "INVESTIGATE")


def test_healthy_decisions_have_low_failure_rate():
    _, _, final = _load()
    for row in final:
        if row["jev_decision"] == "HEALTHY":
            assert float(row["failure_rate"]) < 0.01
