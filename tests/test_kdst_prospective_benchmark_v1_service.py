from __future__ import annotations

from src.services.kdst_prospective_benchmark_v1_service import (
    ARM_NWR_RECOMMENDATION,
    ARM_PROVIDER_CONSENSUS,
    ARM_RAW_PROJECTION,
    ARM_REPLACEMENT_LEVEL,
    DATA_STATUS_NOT_AVAILABLE,
    DATA_STATUS_OK,
    DATA_STATUS_PENDING,
    PRELIMINARY_SAMPLE_SIZE_WEEKS_FLOOR,
    build_kdst_benchmark_week_record,
    compare_arms,
    sleeper_team_code,
    summarize_kdst_benchmark,
)


def _week1_k_record():
    return build_kdst_benchmark_week_record(
        season=2026, week=1, position="K", league_id="lg1", owner_roster_id="9",
        nwr_recommendation={"playerId": "11786", "playerName": "Cam Little", "team": "JAX", "ecr": 3},
        provider_consensus_rank1={"playerId": "9999", "playerName": "Brandon Aubrey", "team": "DAL", "ecr": 1},
        raw_projection_best={"playerId": "11786", "playerName": "Cam Little", "team": "JAX", "projectedPoints": 8.5},
        replacement_level_current={"playerId": "3451", "playerName": "Ka'imi Fairbairn", "team": "HOU", "ecr": 4},
        actual_points_by_sleeper_id={"11786": 12.0, "3451": 9.0, "9999": 6.0},
    )


def test_build_week_record_joins_real_actual_points_by_sleeper_id() -> None:
    record = _week1_k_record()
    nwr = record.arm(ARM_NWR_RECOMMENDATION)
    assert nwr.player_id == "11786"
    assert nwr.actual_points == 12.0
    assert nwr.data_status == DATA_STATUS_OK

    replacement = record.arm(ARM_REPLACEMENT_LEVEL)
    assert replacement.actual_points == 9.0
    assert replacement.data_status == DATA_STATUS_OK


def test_build_week_record_handles_missing_arm_as_not_available() -> None:
    record = build_kdst_benchmark_week_record(
        season=2026, week=1, position="K", league_id="lg1", owner_roster_id="9",
        nwr_recommendation={"playerId": "11786", "playerName": "Cam Little", "team": "JAX", "ecr": 3},
        provider_consensus_rank1=None,
        raw_projection_best=None,
        replacement_level_current=None,
        actual_points_by_sleeper_id={"11786": 12.0},
    )
    assert record.arm(ARM_PROVIDER_CONSENSUS).data_status == DATA_STATUS_NOT_AVAILABLE
    assert record.arm(ARM_RAW_PROJECTION).data_status == DATA_STATUS_NOT_AVAILABLE
    assert record.arm(ARM_REPLACEMENT_LEVEL).data_status == DATA_STATUS_NOT_AVAILABLE


def test_build_week_record_pending_when_actual_points_not_yet_observable() -> None:
    record = build_kdst_benchmark_week_record(
        season=2026, week=2, position="K", league_id="lg1", owner_roster_id="9",
        nwr_recommendation={"playerId": "11786", "playerName": "Cam Little", "team": "JAX", "ecr": 3},
        provider_consensus_rank1=None, raw_projection_best=None, replacement_level_current=None,
        actual_points_by_sleeper_id={},  # week not yet complete -- no real stats yet
    )
    nwr = record.arm(ARM_NWR_RECOMMENDATION)
    assert nwr.actual_points is None
    assert nwr.data_status == DATA_STATUS_PENDING


def test_build_week_record_rejects_an_invalid_position() -> None:
    import pytest

    with pytest.raises(ValueError):
        build_kdst_benchmark_week_record(
            season=2026, week=1, position="WR", league_id="lg1", owner_roster_id="9",
            nwr_recommendation=None, provider_consensus_rank1=None, raw_projection_best=None,
            replacement_level_current=None, actual_points_by_sleeper_id={},
        )


def test_compare_arms_computes_real_deltas_vs_nwr_recommendation() -> None:
    record = _week1_k_record()
    comparison = compare_arms(record)
    assert comparison["nwrRecommendationActualPoints"] == 12.0
    # provider consensus (Aubrey, 6.0) - nwr (Cam Little, 12.0) = -6.0
    assert comparison["deltaVsProviderConsensus"] == -6.0
    # raw projection arm picked the SAME real player here (12.0 - 12.0 = 0.0)
    assert comparison["deltaVsRawProjection"] == 0.0
    # replacement level (Fairbairn, 9.0) - nwr (12.0) = -3.0
    assert comparison["deltaVsReplacementLevel"] == -3.0


def test_compare_arms_never_substitutes_a_missing_actual_result() -> None:
    record = build_kdst_benchmark_week_record(
        season=2026, week=2, position="K", league_id="lg1", owner_roster_id="9",
        nwr_recommendation={"playerId": "11786", "playerName": "Cam Little", "team": "JAX", "ecr": 3},
        provider_consensus_rank1={"playerId": "9999", "playerName": "Someone", "team": "DAL", "ecr": 1},
        raw_projection_best=None, replacement_level_current=None,
        actual_points_by_sleeper_id={},  # week not complete -- nothing real to compare yet
    )
    comparison = compare_arms(record)
    assert comparison["nwrRecommendationActualPoints"] is None
    assert comparison["deltaVsProviderConsensus"] is None
    assert comparison["deltaVsRawProjection"] is None
    assert comparison["deltaVsReplacementLevel"] is None


def test_summarize_labels_small_samples_preliminary_and_reports_real_n() -> None:
    records = [_week1_k_record()]
    summary = summarize_kdst_benchmark(records)
    assert summary["generatedFromRealWeeks"] == 1
    assert summary["K"]["sampleSizeWeeks"] == 1
    assert summary["K"]["sampleSizeLabel"] == "PRELIMINARY"
    assert summary["K"]["meanDeltaVsProviderConsensus"] == -6.0
    assert len(summary["K"]["perWeekComparisons"]) == 1


def test_summarize_labels_standard_once_the_floor_is_reached() -> None:
    records = []
    for week in range(1, PRELIMINARY_SAMPLE_SIZE_WEEKS_FLOOR + 1):
        records.append(
            build_kdst_benchmark_week_record(
                season=2026, week=week, position="K", league_id="lg1", owner_roster_id="9",
                nwr_recommendation={"playerId": "11786", "playerName": "Cam Little", "team": "JAX", "ecr": 3},
                provider_consensus_rank1=None, raw_projection_best=None, replacement_level_current=None,
                actual_points_by_sleeper_id={"11786": 10.0},
            )
        )
    summary = summarize_kdst_benchmark(records)
    assert summary["K"]["sampleSizeWeeks"] == PRELIMINARY_SAMPLE_SIZE_WEEKS_FLOOR
    assert summary["K"]["sampleSizeLabel"] == "STANDARD"


def test_summarize_never_fabricates_a_verdict_it_only_reports_raw_comparisons() -> None:
    summary = summarize_kdst_benchmark([_week1_k_record()])
    assert "verdict" not in summary["K"]
    assert "recommendation" not in summary["K"]


def test_summarize_keeps_k_and_dst_separate() -> None:
    k_record = _week1_k_record()
    dst_record = build_kdst_benchmark_week_record(
        season=2026, week=1, position="DST", league_id="lg1", owner_roster_id="9",
        nwr_recommendation={"playerId": "JAX", "playerName": "Jacksonville Jaguars", "team": "JAX", "ecr": 1},
        provider_consensus_rank1={"playerId": "JAX", "playerName": "Jacksonville Jaguars", "team": "JAX", "ecr": 1},
        raw_projection_best=None,
        replacement_level_current={"playerId": "NE", "playerName": "New England Patriots", "team": "NE", "ecr": 9},
        actual_points_by_sleeper_id={"JAX": 15.0, "NE": 6.0},
    )
    summary = summarize_kdst_benchmark([k_record, dst_record])
    assert summary["K"]["sampleSizeWeeks"] == 1
    assert summary["DST"]["sampleSizeWeeks"] == 1
    # NWR and provider consensus picked the SAME real team for DST (the
    # disclosed identity-bug consequence) -- delta must be exactly 0.0.
    assert summary["DST"]["perWeekComparisons"][0]["deltaVsProviderConsensus"] == 0.0
    assert summary["DST"]["perWeekComparisons"][0]["deltaVsReplacementLevel"] == 6.0 - 15.0


# ---------------------------------------------------------------------------
# Team-code translation (the real, disclosed JAC/JAX nuance).
# ---------------------------------------------------------------------------


def test_sleeper_team_code_translates_the_one_known_divergence() -> None:
    assert sleeper_team_code("JAC") == "JAX"


def test_sleeper_team_code_passes_through_every_other_code_unchanged() -> None:
    for code in ("LAC", "PIT", "LAR", "PHI", "SEA", "DEN", "HOU", "BAL", "DET", "NE"):
        assert sleeper_team_code(code) == code
