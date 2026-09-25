"""Parity check: notebooks/databricks_pipeline.py must mirror src/metrics.py.

No Databricks import — text-level guard against silent drift.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "metrics.py"
NOTEBOOK = ROOT / "notebooks" / "databricks_pipeline.py"

REQUIRED_TOKENS = [
    "def failure_rate",
    "def row_count_variance",
    "def duration_variance",
    "def freshness_severity",
    "def has_schema_drift",
    "def error_present",
    "METRIC_PRECISION",
    "FRESHNESS_THRESHOLDS",
]


def test_notebook_mirrors_metrics_functions():
    src = SRC.read_text()
    nb = NOTEBOOK.read_text()
    for token in REQUIRED_TOKENS:
        assert token in src, f"missing in src/metrics.py: {token}"
        assert token in nb, f"drift: missing in notebook: {token}"


def test_notebook_does_not_reimplement_silently():
    # If the notebook ever imports src.metrics directly, this test still passes
    # but documents the preferred direction (import > copy).
    nb = NOTEBOOK.read_text()
    assert "verbatim mirror of src/metrics.py" in nb or "src.metrics" in nb
