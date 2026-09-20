"""Tests for the deterministic metric functions (src/metrics.py)."""

import pytest

from src.metrics import (
    error_present,
    failure_rate,
    freshness_severity,
    has_schema_drift,
    metric_record,
    row_count_variance,
    duration_variance,
)

HEALTHY_RUN = {
    "run_id": "r1", "domain": "auto_claims", "status": "healthy",
    "expected_rows": 1000, "actual_rows": 1000, "failed_rows": 0,
    "duration_seconds": 90, "expected_duration_seconds": 100,
    "freshness_delay_minutes": 10, "schema_drift": "none",
    "error_message": None,
}


class TestFailureRate:
    def test_zero_when_no_failed_rows(self):
        assert failure_rate(HEALTHY_RUN) == 0.0

    def test_computes_share_of_expected_rows(self):
        run = {**HEALTHY_RUN, "failed_rows": 250}
        assert failure_rate(run) == 0.25

    def test_full_failure(self):
        run = {**HEALTHY_RUN, "failed_rows": 1000}
        assert failure_rate(run) == 1.0

    def test_safe_when_expected_zero(self):
        run = {**HEALTHY_RUN, "expected_rows": 0, "failed_rows": 5}
        assert failure_rate(run) == 0.0

    def test_is_deterministic(self):
        assert failure_rate(HEALTHY_RUN) == failure_rate(HEALTHY_RUN)


class TestRowCountVariance:
    def test_zero_when_counts_match(self):
        assert row_count_variance(HEALTHY_RUN) == 0.0

    def test_negative_when_under_delivered(self):
        run = {**HEALTHY_RUN, "actual_rows": 900}
        assert row_count_variance(run) == -0.1

    def test_positive_when_over_delivered(self):
        run = {**HEALTHY_RUN, "actual_rows": 1100}
        assert row_count_variance(run) == 0.1

    def test_safe_when_expected_zero(self):
        run = {**HEALTHY_RUN, "expected_rows": 0, "actual_rows": 10}
        assert row_count_variance(run) == 0.0


class TestDurationVariance:
    def test_zero_when_on_plan(self):
        run = {**HEALTHY_RUN, "duration_seconds": 100}
        assert duration_variance(run) == 0.0

    def test_slow_run_is_positive(self):
        run = {**HEALTHY_RUN, "duration_seconds": 150}
        assert duration_variance(run) == 0.5

    def test_fast_run_is_negative(self):
        run = {**HEALTHY_RUN, "duration_seconds": 50}
        assert duration_variance(run) == -0.5

    def test_safe_when_expected_zero(self):
        run = {**HEALTHY_RUN, "expected_duration_seconds": 0, "duration_seconds": 60}
        assert duration_variance(run) == 0.0


class TestFreshnessSeverity:
    @pytest.mark.parametrize("minutes,expected", [
        (0, "ON_TIME"), (15, "ON_TIME"),
        (16, "MINOR"), (60, "MINOR"),
        (61, "MAJOR"), (240, "MAJOR"),
        (241, "SEVERE"), (1440, "SEVERE"),
    ])
    def test_thresholds(self, minutes, expected):
        assert freshness_severity(minutes) == expected


class TestSchemaDrift:
    def test_absent(self):
        assert has_schema_drift(HEALTHY_RUN) is False

    def test_present(self):
        run = {**HEALTHY_RUN, "schema_drift": "column_added"}
        assert has_schema_drift(run) is True

    def test_type_changed_counts(self):
        run = {**HEALTHY_RUN, "schema_drift": "type_changed"}
        assert has_schema_drift(run) is True


class TestErrorPresent:
    def test_absent(self):
        assert error_present(HEALTHY_RUN) is False

    def test_present(self):
        run = {**HEALTHY_RUN, "error_message": "source unavailable"}
        assert error_present(run) is True

    def test_empty_string_is_absent(self):
        run = {**HEALTHY_RUN, "error_message": ""}
        assert error_present(run) is False


def test_metric_record_contains_all_jev_fields():
    record = metric_record(HEALTHY_RUN)
    for field in ("run_id", "domain", "failure_rate", "row_count_variance",
                  "duration_variance", "freshness_delay_minutes", "freshness_severity",
                  "schema_drift", "schema_drift_present", "status", "error_present"):
        assert field in record
