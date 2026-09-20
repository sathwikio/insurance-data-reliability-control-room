"""Generate deterministic synthetic insurance pipeline-run data.

The dataset models daily data pipelines for five insurance domains with
healthy, degraded, and failed runs. A fixed random seed makes generation a
pure function: the same code always produces the same dataset.

Output: data/pipeline_runs.csv
"""

import csv
import random
from datetime import datetime
from pathlib import Path

SEED = 42
RUN_DAYS = (datetime(2026, 9, 18), datetime(2026, 9, 19))
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "pipeline_runs.csv"

COLUMNS = [
    "run_id",
    "pipeline_name",
    "domain",
    "run_timestamp",
    "expected_rows",
    "actual_rows",
    "failed_rows",
    "duration_seconds",
    "expected_duration_seconds",
    "freshness_delay_minutes",
    "schema_drift",
    "status",
    "error_message",
]

DOMAIN_PIPELINES = {
    "auto_claims": ["auto_claims_raw_ingest", "auto_claims_dedupe_transform"],
    "home_claims": ["home_claims_raw_ingest", "home_claims_enrich_transform"],
    "policies": ["policies_snapshot_load", "policies_scd2_transform"],
    "billing": ["billing_payments_ingest", "billing_reconciliation_transform"],
    "customers": ["customers_master_load", "customers_match_transform"],
}

RUN_SLOTS = {0: [(2, 15), (14, 30)], 1: [(4, 45), (16, 0)]}  # daily run times per pipeline slot

ERROR_MESSAGES = [
    "upstream source unavailable after 3 retries",
    "schema validation failed: unexpected column claim_reserve_usd",
    "checkpoint write timed out",
    "out of memory during shuffle partition",
    "source credential expired",
    "duplicate key violation in delta merge",
]

WARN_MESSAGES = [
    "row count variance above warn threshold",
    "freshness delay within degraded range",
]


def _health_profile(rng: random.Random) -> str:
    return rng.choices(["healthy", "degraded", "failed"], weights=[24, 10, 6])[0]


def _scale_rows(rng: random.Random) -> int:
    """Base expected row count for a pipeline (rows/day)."""
    return rng.choice([120_000, 250_000, 480_000, 900_000, 1_600_000])


def _expected_duration(rng: random.Random) -> int:
    return rng.randrange(120, 900)


def _run_fields(rng: random.Random, status: str, expected: int, expected_duration: int) -> dict:
    """Derive all measured fields from a run's health profile."""
    if status == "healthy":
        actual = expected * rng.uniform(0.995, 1.0)
        failed = expected * rng.uniform(0.0, 0.001)
        duration = expected_duration * rng.uniform(0.85, 1.1)
        freshness = rng.randrange(0, 16)
        drift = "none"
        error = None
    elif status == "degraded":
        actual = expected * rng.uniform(0.90, 0.985)
        failed = expected * rng.uniform(0.005, 0.03)
        duration = expected_duration * rng.uniform(1.15, 1.8)
        freshness = rng.randrange(30, 181)
        drift = rng.choice(["none", "none", "none", "column_added"])
        error = rng.choice(WARN_MESSAGES) if rng.random() < 0.15 else None
    else:  # failed
        actual = expected * rng.uniform(0.0, 0.4)
        failed = expected * rng.uniform(0.2, 0.8)
        duration = expected_duration * rng.uniform(0.4, 2.5)
        freshness = rng.randrange(240, 1441)
        drift = rng.choice(["none", "none", "column_added", "type_changed", "column_removed"])
        error = rng.choice(ERROR_MESSAGES)
    return {
        "actual_rows": int(actual),
        "failed_rows": int(failed),
        "duration_seconds": int(duration),
        "freshness_delay_minutes": freshness,
        "schema_drift": drift,
        "error_message": error,
    }


def generate_runs(seed: int = SEED) -> list[dict]:
    """Return the full list of synthetic pipeline runs (deterministic)."""
    rng = random.Random(seed)
    runs = []
    for domain, pipelines in DOMAIN_PIPELINES.items():
        for slot, pipeline_name in enumerate(pipelines):
            base_rows = _scale_rows(rng)
            base_duration = _expected_duration(rng)
            run_number = 0
            for day in RUN_DAYS:
                for hour, minute in RUN_SLOTS[slot]:
                    status = _health_profile(rng)
                    expected = base_rows
                    timestamp = datetime(day.year, day.month, day.day, hour, minute, 0)
                    run = {
                        "run_id": f"{pipeline_name}_{day:%Y%m%d}_{run_number}",
                        "pipeline_name": pipeline_name,
                        "domain": domain,
                        "run_timestamp": timestamp.isoformat(),
                        "expected_rows": expected,
                        "expected_duration_seconds": base_duration,
                        "status": status,
                    }
                    run.update(_run_fields(rng, status, expected, base_duration))
                    runs.append(run)
                    run_number += 1
    return runs


def write_csv(runs: list[dict], path: Path = DATA_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(runs)
    return path


def main() -> None:
    path = write_csv(generate_runs())
    print(f"wrote {path} ({len(list(path.open())) - 1} runs)")


if __name__ == "__main__":
    main()
