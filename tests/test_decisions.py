"""Tests for the Jev decision layer and the final analytics dataset."""

import csv
import json
from pathlib import Path

import pytest

from src.metrics import metric_record

DATA = Path(__file__).resolve().parent.parent / "data"
ALLOWED = {"HEALTHY", "WATCH", "INVESTIGATE", "BLOCK"}


def load_json(name):
    return json.load(open(DATA / name))


def load_csv(name):
    with open(DATA / name, newline="") as fh:
        rows = []
        for raw in csv.DictReader(fh):
            row = dict(raw)
            for key in ("expected_rows", "actual_rows", "failed_rows",
                        "duration_seconds", "expected_duration_seconds",
                        "freshness_delay_minutes"):
                row[key] = int(row[key])
            for key in ("failure_rate", "row_count_variance", "duration_variance",
                        "jev_confidence"):
                if row.get(key):
                    row[key] = float(row[key])
            rows.append(row)
        return rows


@pytest.fixture(scope="module")
def runs():
    return load_csv("pipeline_runs.csv")


@pytest.fixture(scope="module")
def jev_input():
    return load_json("jev_input.json")


@pytest.fixture(scope="module")
def decisions():
    return load_json("jev_decisions.json")


@pytest.fixture(scope="module")
def final():
    return load_csv("final_analytics.csv")


def require_artifacts(*names):
    pytest.mark.skipif = None  # keep pytest import used
    missing = [n for n in names if not (DATA / n).exists()]
    if missing:
        pytest.skip(f"artifacts not generated yet: {missing}")


def test_jev_input_untouched(runs, jev_input):
    """Every source run has exactly one jev input record with matching fields."""
    by_id = {r["run_id"]: r for r in runs}
    assert len(jev_input) == len(runs) == 40
    assert {r["run_id"] for r in jev_input} == set(by_id)
    for record in jev_input:
        metric = metric_record(by_id[record["run_id"]])
        assert record["failure_rate"] == metric["failure_rate"]
        assert record["row_count_variance"] == metric["row_count_variance"]
        assert record["duration_variance"] == metric["duration_variance"]


def test_decisions_cover_every_run_once(jev_input, decisions):
    require_artifacts("jev_decisions.json")
    assert len(decisions) == len(jev_input) == 40
    assert [d["run_id"] for d in decisions].count(decisions[0]["run_id"]) == 1
    assert {d["run_id"] for d in decisions} == {r["run_id"] for r in jev_input}


def test_decisions_use_allowed_labels_only(decisions):
    require_artifacts("jev_decisions.json")
    assert {d["decision"] for d in decisions} <= ALLOWED


def test_confidence_is_native_number_or_absent(decisions):
    require_artifacts("jev_decisions.json")
    for d in decisions:
        assert set(d) == {"run_id", "decision", "confidence"}
        if d["confidence"] is not None:
            assert isinstance(d["confidence"], (int, float))
            assert 0.0 <= d["confidence"] <= 1.0


def test_final_dataset_contains_every_source_run(runs, final):
    require_artifacts("final_analytics.csv")
    assert len(final) == len(runs) == 40
    assert {r["run_id"] for r in final} == {r["run_id"] for r in runs}


def test_final_dataset_preserves_both_layers(final, decisions):
    require_artifacts("final_analytics.csv")
    decision_by_id = {d["run_id"]: d for d in decisions}
    for row in final:
        assert row["jev_decision"] in ALLOWED
        assert row["jev_decision"] == decision_by_id[row["run_id"]]["decision"]
        # deterministic metric columns still match recomputation from source
        metric = metric_record(row)
        assert float(row["failure_rate"]) == metric["failure_rate"]
        assert row["freshness_severity"] == metric["freshness_severity"]
        assert (row["error_present"] == "True") == metric["error_present"]


def test_final_dataset_jev_confidence_matches_decision_layer(final, decisions):
    require_artifacts("final_analytics.csv")
    confidence_by_id = {d["run_id"]: d["confidence"] for d in decisions}
    for row in final:
        expected = confidence_by_id[row["run_id"]]
        if expected is None:
            assert row["jev_confidence"] in ("", None)
        else:
            assert float(row["jev_confidence"]) == expected
