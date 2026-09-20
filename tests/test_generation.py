"""Tests for deterministic synthetic data generation (src/generate_data.py)."""

import csv

from src.generate_data import COLUMNS, DOMAIN_PIPELINES, generate_runs, write_csv


def test_run_count_matches_plan():
    runs = generate_runs()
    expected = sum(len(pipelines) * 4 for pipelines in DOMAIN_PIPELINES.values())
    assert len(runs) == expected == 40


def test_generation_is_deterministic():
    assert generate_runs() == generate_runs()


def test_generation_responds_to_seed():
    assert generate_runs(seed=1) != generate_runs(seed=2)


def test_all_required_columns_present():
    runs = generate_runs()
    for run in runs:
        assert set(COLUMNS) == set(run.keys())


def test_all_domains_covered():
    runs = generate_runs()
    assert {run["domain"] for run in runs} == set(DOMAIN_PIPELINES)


def test_statuses_include_healthy_degraded_failed():
    statuses = {run["status"] for run in generate_runs()}
    assert statuses == {"healthy", "degraded", "failed"}


def test_failed_runs_carry_error_messages():
    runs = generate_runs()
    for run in runs:
        if run["status"] == "failed":
            assert run["error_message"]
        if run["status"] == "healthy":
            assert not run["error_message"]


def test_run_ids_unique():
    runs = generate_runs()
    ids = [run["run_id"] for run in runs]
    assert len(ids) == len(set(ids))


def test_metrics_are_consistent_with_fields():
    for run in generate_runs():
        assert 0 <= run["failed_rows"] <= run["expected_rows"]
        assert run["duration_seconds"] > 0
        assert run["freshness_delay_minutes"] >= 0
        if run["status"] == "failed":
            assert run["failed_rows"] / run["expected_rows"] >= 0.2


def test_write_csv_round_trip(tmp_path):
    path = tmp_path / "pipeline_runs.csv"
    write_csv(generate_runs(), path)
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 40
    assert list(rows[0].keys()) == COLUMNS
