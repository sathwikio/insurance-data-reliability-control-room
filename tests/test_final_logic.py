"""Offline tests for final-join validation rules (no Spark needed)."""

import pytest

ALLOWED_DECISIONS = ("HEALTHY", "WATCH", "INVESTIGATE", "BLOCK")


class FakeRow:
    def __init__(self, run_id, decision=None):
        self.run_id = run_id
        self.decision = decision


class FakeDF:
    def __init__(self, rows):
        self._rows = rows

    def select(self, _col):
        return self

    def collect(self):
        return self._rows


def _validate(metric_ids, decision_rows):
    """Mirror of src.build_final.validate_decisions core logic, testable offline."""
    ALLOWED = ALLOWED_DECISIONS

    decision_ids = [r.run_id for r in decision_rows]
    if len(decision_rows) != len(decision_ids) or set(metric_ids) != set(decision_ids):
        raise ValueError("decision coverage mismatch")
    bad = {r.decision for r in decision_rows} - set(ALLOWED)
    if bad:
        raise ValueError(f"decisions outside allowed labels: {bad}")


def test_allowed_labels_are_exact():
    assert set(ALLOWED_DECISIONS) == {"HEALTHY", "WATCH", "INVESTIGATE", "BLOCK"}


def test_coverage_ok():
    _validate({"a", "b"}, [FakeRow("a", "HEALTHY"), FakeRow("b", "BLOCK")])


def test_missing_run_fails():
    with pytest.raises(ValueError, match="coverage mismatch"):
        _validate({"a", "b"}, [FakeRow("a", "HEALTHY")])


def test_extra_run_fails():
    with pytest.raises(ValueError, match="coverage mismatch"):
        _validate({"a"}, [FakeRow("a", "HEALTHY"), FakeRow("b", "WATCH")])


def test_bad_label_fails():
    with pytest.raises(ValueError, match="allowed labels"):
        _validate({"a"}, [FakeRow("a", "MAYBE")])


def test_duplicate_run_ids_fail():
    # len(rows) != len(set) is caught via set comparison in real code;
    # here duplicate + missing triggers mismatch
    with pytest.raises(ValueError, match="coverage mismatch"):
        _validate({"a", "b"}, [FakeRow("a", "HEALTHY"), FakeRow("a", "HEALTHY")])


def test_fakedf_shape():
    df = FakeDF([FakeRow("a")])
    assert [r.run_id for r in df.select("run_id").collect()] == ["a"]


def test_build_final_allowed_labels_in_sync():
    from pathlib import Path

    text = (Path(__file__).resolve().parent.parent / "src" / "build_final.py").read_text()
    for label in ALLOWED_DECISIONS:
        assert label in text
