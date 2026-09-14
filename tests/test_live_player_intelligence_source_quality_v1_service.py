"""Tests for the Gate 3/4/5 computation logic itself (Work Unit 5) -- known,
small, constructed examples, proving the LOGIC is correct, not merely
trusting the one real aggregate run reported in
`docs/codex/live_player_intelligence_v1/SOURCE_QUALITY_EVALUATION_V1.md`."""

from __future__ import annotations

from src.services.live_player_intelligence_source_quality_v1_service import (
    AgreementPair,
    compute_agreement,
    compute_coverage,
    diff_poll_rows,
    is_hard_active_like,
    is_hard_out_like,
    normalize_benchmark_report_status,
    normalize_sleeper_designation,
    summarize_seconds,
)

# --- Gate 4: coverage --------------------------------------------------


def test_coverage_full_match():
    result = compute_coverage(["a", "b", "c"], ["a", "b", "c", "z"])
    assert result.population_size == 3
    assert result.covered_size == 3
    assert result.coverage_ratio == 1.0
    assert result.meets_gate is True
    assert result.uncovered_ids == ()


def test_coverage_below_threshold():
    # 1 of 3 covered = 0.3333 < 0.95
    result = compute_coverage(["a", "b", "c"], ["a"])
    assert result.covered_size == 1
    assert result.coverage_ratio == 0.3333
    assert result.meets_gate is False
    assert result.uncovered_ids == ("b", "c")


def test_coverage_exactly_at_threshold_boundary():
    # 19/20 = 0.95 exactly -- must meet the gate (>=, not >).
    population = [str(i) for i in range(20)]
    covered = [str(i) for i in range(19)]
    result = compute_coverage(population, covered)
    assert result.coverage_ratio == 0.95
    assert result.meets_gate is True


def test_coverage_empty_population_is_not_computable_not_a_fabricated_number():
    result = compute_coverage([], ["a", "b"])
    assert result.population_size == 0
    assert result.coverage_ratio is None
    assert result.meets_gate is None


def test_coverage_deduplicates_population_ids():
    result = compute_coverage(["a", "a", "b"], ["a", "b"])
    assert result.population_size == 2
    assert result.coverage_ratio == 1.0


# --- Gate 3: normalization ----------------------------------------------


def test_normalize_benchmark_report_status_passthrough():
    assert normalize_benchmark_report_status("OUT") == "OUT"
    assert normalize_benchmark_report_status("QUESTIONABLE") == "QUESTIONABLE"


def test_normalize_benchmark_report_status_empty_means_cleared():
    assert normalize_benchmark_report_status(None) == "CLEARED_OR_NOT_LISTED"
    assert normalize_benchmark_report_status("") == "CLEARED_OR_NOT_LISTED"


def test_normalize_sleeper_designation_maps_real_values():
    assert normalize_sleeper_designation("Out") == "OUT"
    assert normalize_sleeper_designation("Doubtful") == "DOUBTFUL"
    assert normalize_sleeper_designation("Questionable") == "QUESTIONABLE"


def test_normalize_sleeper_designation_na_and_empty_mean_cleared():
    assert normalize_sleeper_designation("NA") == "CLEARED_OR_NOT_LISTED"
    assert normalize_sleeper_designation(None) == "CLEARED_OR_NOT_LISTED"
    assert normalize_sleeper_designation("") == "CLEARED_OR_NOT_LISTED"


def test_normalize_sleeper_designation_list_statuses_are_not_folded_into_designations():
    assert normalize_sleeper_designation("IR") == "ON_LIST_IR"
    assert normalize_sleeper_designation("PUP") == "ON_LIST_PUP"
    assert normalize_sleeper_designation("Sus") == "ON_LIST_SUSPENDED"
    assert normalize_sleeper_designation("COV") == "ON_LIST_COVID"


def test_normalize_sleeper_designation_dnr_and_unrecognized():
    assert normalize_sleeper_designation("DNR") == "DID_NOT_REPORT"
    assert normalize_sleeper_designation("SomethingNew") == "UNRECOGNIZED:SomethingNew"


def test_hard_out_and_hard_active_classification():
    assert is_hard_out_like("OUT") is True
    assert is_hard_out_like("ON_LIST_IR") is True
    assert is_hard_out_like("QUESTIONABLE") is False
    assert is_hard_active_like("CLEARED_OR_NOT_LISTED") is True
    assert is_hard_active_like("QUESTIONABLE") is False


# --- Gate 3: agreement computation ---------------------------------------


def test_agreement_perfect_agreement():
    pairs = [
        AgreementPair("p1", "OUT", "OUT"),
        AgreementPair("p2", "QUESTIONABLE", "QUESTIONABLE"),
        AgreementPair("p3", "CLEARED_OR_NOT_LISTED", "CLEARED_OR_NOT_LISTED"),
    ]
    result = compute_agreement(pairs)
    assert result.comparable_pairs == 3
    assert result.exact_agreements == 3
    assert result.agreement_ratio == 1.0
    assert result.meets_gate is True
    assert result.hard_contradictions == ()


def test_agreement_below_99_percent_threshold():
    # 98/100 exact = 0.98 < 0.99 -- must fail the gate.
    pairs = [AgreementPair(f"p{i}", "OUT", "OUT") for i in range(98)]
    pairs += [AgreementPair("p98", "OUT", "QUESTIONABLE"), AgreementPair("p99", "QUESTIONABLE", "OUT")]
    result = compute_agreement(pairs)
    assert result.comparable_pairs == 100
    assert result.exact_agreements == 98
    assert result.agreement_ratio == 0.98
    assert result.meets_gate is False
    assert len(result.disagreements) == 2


def test_agreement_detects_hard_contradiction_benchmark_out_candidate_active():
    pairs = [AgreementPair("p1", "OUT", "CLEARED_OR_NOT_LISTED")]
    result = compute_agreement(pairs)
    assert len(result.hard_contradictions) == 1
    assert result.hard_contradictions[0].player_id == "p1"
    assert result.to_dict()["zeroHardContradictions"] is False


def test_agreement_detects_hard_contradiction_candidate_out_benchmark_active():
    pairs = [AgreementPair("p1", "CLEARED_OR_NOT_LISTED", "ON_LIST_IR")]
    result = compute_agreement(pairs)
    assert len(result.hard_contradictions) == 1


def test_agreement_soft_disagreement_is_not_a_hard_contradiction():
    # Doubtful vs Questionable disagree exactly, but neither is a hard
    # OUT-vs-ACTIVE contradiction.
    pairs = [AgreementPair("p1", "DOUBTFUL", "QUESTIONABLE")]
    result = compute_agreement(pairs)
    assert result.hard_contradictions == ()
    assert len(result.disagreements) == 1
    assert result.agreement_ratio == 0.0


def test_agreement_excludes_non_designation_candidate_values_from_ratio_but_checks_hard_contradiction():
    # A candidate ON_LIST_IR value is a real, different concept from a
    # weekly designation -- excluded from the agreement ratio denominator
    # -- but if the benchmark says CLEARED (healthy) that is STILL a real
    # hard contradiction and must be caught.
    pairs = [
        AgreementPair("p1", "OUT", "OUT"),
        AgreementPair("p2", "CLEARED_OR_NOT_LISTED", "ON_LIST_IR"),
    ]
    result = compute_agreement(pairs)
    assert result.comparable_pairs == 1
    assert result.exact_agreements == 1
    assert result.agreement_ratio == 1.0
    assert len(result.hard_contradictions) == 1


def test_agreement_empty_pairs_is_not_computable():
    result = compute_agreement([])
    assert result.comparable_pairs == 0
    assert result.agreement_ratio is None
    assert result.meets_gate is None
    assert result.hard_contradictions == ()


# --- Gate 5: diff/freshness helpers --------------------------------------


def test_diff_poll_rows_detects_added_removed_changed():
    poll_a = {
        "1": {"report_status": "Out"},
        "2": {"report_status": "Questionable"},
        "3": {"report_status": ""},
    }
    poll_b = {
        "1": {"report_status": "Out"},  # unchanged
        "2": {"report_status": "Out"},  # changed
        "4": {"report_status": "Doubtful"},  # added
        # "3" removed
    }
    result = diff_poll_rows(poll_a, poll_b, compare_fields=("report_status",))
    assert result["added"] == ["4"]
    assert result["removed"] == ["3"]
    assert result["changedIds"] == ["2"]
    assert result["changedCount"] == 1
    assert result["sharedIds"] == 2


def test_diff_poll_rows_zero_changes_real_stability_evidence():
    poll_a = {"1": {"report_status": "Out", "practice_status": "DNP"}}
    poll_b = {"1": {"report_status": "Out", "practice_status": "DNP"}}
    result = diff_poll_rows(poll_a, poll_b, compare_fields=("report_status", "practice_status"))
    assert result["changedCount"] == 0
    assert result["added"] == []
    assert result["removed"] == []


def test_summarize_seconds_known_values():
    # 10 values, 0..9 minutes in seconds, evenly spaced.
    values = [float(i * 60) for i in range(10)]
    summary = summarize_seconds(values)
    assert summary["sampleSize"] == 10
    assert summary["minSeconds"] == 0.0
    assert summary["maxSeconds"] == 540.0
    assert summary["p50Seconds"] is not None
    assert summary["p95Seconds"] is not None
    # P95 must be >= P50 for a real, non-degenerate distribution.
    assert summary["p95Seconds"] >= summary["p50Seconds"]


def test_summarize_seconds_single_value():
    summary = summarize_seconds([42.0])
    assert summary["sampleSize"] == 1
    assert summary["p50Seconds"] == 42.0
    assert summary["p95Seconds"] == 42.0


def test_summarize_seconds_empty_is_honestly_not_computable():
    summary = summarize_seconds([])
    assert summary["sampleSize"] == 0
    assert summary["p50Seconds"] is None
    assert summary["p95Seconds"] is None
