"""Guard against stale web mirror (scripts/sync_web_data.py is manual)."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "final_analytics.csv"
DST = ROOT / "web" / "src" / "data" / "runs.json"


def test_web_mirror_covers_every_final_run():
    final_ids = {r["run_id"] for r in csv.DictReader(open(SRC))}
    web = json.load(open(DST))
    web_ids = {r["run_id"] for r in web}
    assert len(final_ids) == 40
    assert web_ids == final_ids


def test_web_mirror_fields_in_sync():
    final = {r["run_id"]: r for r in csv.DictReader(open(SRC))}
    web = {r["run_id"]: r for r in json.load(open(DST))}
    for run_id, f in final.items():
        w = web[run_id]
        assert w["jev_decision"] == f["jev_decision"]
        assert w["status"] == f["status"]
        assert abs(w["failure_rate"] - float(f["failure_rate"])) < 1e-9
