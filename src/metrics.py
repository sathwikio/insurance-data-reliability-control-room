"""Deterministic data-quality metrics for pipeline runs.

Every measurable fact about a run is computed here, in plain Python, so the
same source data always produces the same metrics. The Jev decision layer
reads these values but never computes them.
"""

FRESHNESS_THRESHOLDS = [
    (15, "ON_TIME"),
    (60, "MINOR"),
    (240, "MAJOR"),
    (float("inf"), "SEVERE"),
]

METRIC_PRECISION = 6


def failure_rate(run: dict) -> float:
    """Share of expected rows that failed processing."""
    expected = run["expected_rows"]
    if not expected:
        return 0.0
    return round(run["failed_rows"] / expected, METRIC_PRECISION)


def row_count_variance(run: dict) -> float:
    """Relative difference between actual and expected rows."""
    expected = run["expected_rows"]
    if not expected:
        return 0.0
    return round((run["actual_rows"] - expected) / expected, METRIC_PRECISION)


def duration_variance(run: dict) -> float:
    """Relative difference between actual and expected duration."""
    expected = run["expected_duration_seconds"]
    if not expected:
        return 0.0
    return round((run["duration_seconds"] - expected) / expected, METRIC_PRECISION)


def freshness_severity(freshness_delay_minutes: int) -> str:
    """Classify freshness delay into an ordered severity band."""
    for threshold, label in FRESHNESS_THRESHOLDS:
        if freshness_delay_minutes <= threshold:
            return label
    return "SEVERE"


def has_schema_drift(run: dict) -> bool:
    """True when the run reported any schema drift."""
    return bool(run["schema_drift"]) and run["schema_drift"] != "none"


def error_present(run: dict) -> bool:
    """True when the run recorded an error message."""
    return bool(run["error_message"])


def metric_record(run: dict) -> dict:
    """All deterministic metrics for one run, ready for the Jev input."""
    return {
        "run_id": run["run_id"],
        "domain": run["domain"],
        "failure_rate": failure_rate(run),
        "row_count_variance": row_count_variance(run),
        "duration_variance": duration_variance(run),
        "freshness_delay_minutes": run["freshness_delay_minutes"],
        "freshness_severity": freshness_severity(run["freshness_delay_minutes"]),
        "schema_drift": run["schema_drift"],
        "schema_drift_present": has_schema_drift(run),
        "status": run["status"],
        "error_present": error_present(run),
    }
