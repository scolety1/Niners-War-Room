import pytest

from src.services.failure_analysis_service import (
    EvaluationRecord,
    FailureAnalysisError,
    slice_by_dimension,
    slice_by_every_dimension,
)


def _records():
    return [
        EvaluationRecord("r1", {"position": "QB", "rookie": True}, outcome_value=-5.0),
        EvaluationRecord("r2", {"position": "QB", "rookie": False}, outcome_value=2.0),
        EvaluationRecord("r3", {"position": "RB", "rookie": True}, outcome_value=8.0),
        EvaluationRecord("r4", {"position": "RB", "rookie": True}, outcome_value=10.0),
        EvaluationRecord("r5", {"position": "RB", "rookie": False}, outcome_value=1.0),
    ]


def test_slice_by_dimension_groups_and_computes_real_means() -> None:
    report = slice_by_dimension(_records(), dimension_name="position")
    by_value = {s.dimension_value: s for s in report.slices}
    assert by_value["QB"].sample_size == 2
    assert by_value["QB"].mean_outcome == pytest.approx(-1.5)
    assert by_value["RB"].sample_size == 3
    # mean_outcome is rounded to 4 decimals by slice_by_dimension() itself.
    assert by_value["RB"].mean_outcome == pytest.approx(19.0 / 3, abs=1e-4)


def test_slice_by_dimension_identifies_worst_and_best_slice() -> None:
    report = slice_by_dimension(_records(), dimension_name="position")
    assert report.worst_slice.dimension_value == "QB"
    assert report.best_slice.dimension_value == "RB"


def test_slice_flags_low_confidence_below_the_minimum_sample_size() -> None:
    report = slice_by_dimension(_records(), dimension_name="position")
    by_value = {s.dimension_value: s for s in report.slices}
    assert by_value["QB"].low_confidence is True  # only 2 records
    assert by_value["RB"].low_confidence is False  # 3 records, meets the floor


def test_slice_by_dimension_raises_when_no_record_carries_the_dimension() -> None:
    with pytest.raises(FailureAnalysisError):
        slice_by_dimension(_records(), dimension_name="league_size")


def test_slice_by_every_dimension_skips_absent_dimensions_without_erroring() -> None:
    reports = slice_by_every_dimension(
        _records(), dimension_names=["position", "rookie", "league_size"],
    )
    assert set(reports.keys()) == {"position", "rookie"}


def test_a_record_missing_the_dimension_is_excluded_not_defaulted() -> None:
    records = [
        EvaluationRecord("r1", {"position": "QB"}, outcome_value=1.0),
        EvaluationRecord("r2", {}, outcome_value=99.0),  # no "position" key at all
    ]
    report = slice_by_dimension(records, dimension_name="position")
    all_ids = {rid for s in report.slices for rid in s.record_ids}
    assert "r2" not in all_ids
