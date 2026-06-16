from __future__ import annotations

from src.services.nwr_outcome_feature_snapshot_service import (
    build_feature_snapshot_candidate,
    cutoff_date,
)
from src.services.nwr_outcome_training_row_service import FeatureSnapshot


def _feature(
    *,
    feature_name: str = "prior_games_played",
    value=16,
    source_family: str = "truth_set_scoring_season",
    source_field: str = "games",
    source_available_at: str = "2026-05-15",
    source_max_timestamp: str = "2026-05-15",
    lineage: tuple[str, ...] = ("fixture.csv",),
):
    return FeatureSnapshot(
        feature_name=feature_name,
        value=value,
        source_family=source_family,
        source_field=source_field,
        source_available_at=source_available_at,
        source_max_timestamp=source_max_timestamp,
        lineage=lineage,
    )


def _candidate(features):
    return build_feature_snapshot_candidate(
        player_id="00-TEST",
        player_name="Example Player",
        position="WR",
        row_type="all_player_pre_week1",
        target_season=2026,
        target_horizon="same_year",
        features=features,
        source_manifest="test_manifest",
    )


def _rookie_candidate(features, *, input_snapshot_date="2026-05-25T23:45:00+00:00"):
    return build_feature_snapshot_candidate(
        player_id="rookie:2026:testplayer",
        player_name="Test Player",
        position="UNK",
        row_type="rookie_post_draft",
        target_season=2026,
        target_horizon="year_1",
        features=features,
        source_manifest="rookie_post_draft_manifest_approved_v1",
        input_snapshot_date=input_snapshot_date,
        cutoff_id="rookie_post_draft_2026_rookie_post_draft_manifest_approved_v1",
    )


def test_cutoff_dates_are_deterministic() -> None:
    assert cutoff_date("all_player_pre_week1", 2026) == "2026-09-01"
    assert cutoff_date("offseason_carryover", 2026) == "2026-02-15"
    assert cutoff_date("rookie_post_draft", 2026) == "2026-05-01"


def test_forbidden_feature_names_are_rejected() -> None:
    candidate = _candidate([_feature(feature_name="adp_market_rank", source_field="adp")])

    assert candidate.legality_status == "blocked"
    assert "forbidden_feature_family" in {issue.issue_type for issue in candidate.legality_issues}


def test_same_season_features_are_rejected_for_preseason_rows() -> None:
    candidate = _candidate(
        [_feature(feature_name="same_season_final_points", source_field="same_season_final_stats")]
    )

    assert candidate.legality_status == "blocked"
    assert "same_season_feature_blocked" in {
        issue.issue_type for issue in candidate.legality_issues
    }


def test_supplement_label_sources_are_rejected_as_features() -> None:
    candidate = _candidate(
        [_feature(source_family="player_stats_rare_components", feature_name="passing_2pt")]
    )

    assert candidate.legality_status == "blocked"
    issue_types = {issue.issue_type for issue in candidate.legality_issues}
    assert "supplement_or_blocked_source_as_feature" in issue_types
    assert "source_blocked" in issue_types


def test_missing_optional_fields_are_preserved_not_zero_filled() -> None:
    candidate = _candidate([_feature(feature_name="age_at_snapshot", value=None)])

    assert candidate.legality_status == "valid"
    assert candidate.feature_vector["age_at_snapshot"] is None
    assert candidate.missingness_mask["age_at_snapshot"] is True


def test_snapshot_hash_is_deterministic_and_changes_with_payload() -> None:
    first = _candidate([_feature(feature_name="prior_games_played", value=16)])
    second = _candidate([_feature(feature_name="prior_games_played", value=16)])
    changed = _candidate([_feature(feature_name="prior_games_played", value=15)])

    assert first.snapshot_hash == second.snapshot_hash
    assert first.snapshot_hash != changed.snapshot_hash


def test_ambiguous_prior_feature_names_are_not_emitted() -> None:
    candidate = _candidate(
        [
            _feature(feature_name="prior_nwr_ppg", value=12.4),
            _feature(feature_name="prior_nwr_finish_rank", value=18),
            _feature(feature_name="prior_games_played", value=16),
            _feature(feature_name="prior_rushing_first_downs", value=22),
        ]
    )

    assert "prior_nwr_ppg" not in candidate.feature_vector
    assert "prior_nwr_finish_rank" not in candidate.feature_vector
    assert "prior_games_played" not in candidate.feature_vector
    assert "prior_rushing_first_downs" not in candidate.feature_vector
    assert candidate.feature_vector["prior_season_nwr_ppg"] == 12.4
    assert candidate.feature_vector["prior_season_nwr_finish_rank"] == 18
    assert candidate.feature_vector["prior_completed_season_games_played"] == 16
    assert candidate.feature_vector["prior_completed_season_rushing_first_downs"] == 22


def test_renamed_prior_features_carry_lineage_metadata() -> None:
    candidate = _candidate(
        [
            _feature(
                feature_name="prior_nwr_ppg",
                value=12.4,
                lineage=(
                    "truth_set_v3_production_player_season.csv",
                    "source_season=2025",
                    "target_season=2026",
                    "derived_availability_date=2026-02-15",
                    "source_policy_id=completed_prior_season_stats_available_feb15_v1",
                ),
            )
        ]
    )

    lineage = candidate.feature_lineage["prior_season_nwr_ppg"]
    assert lineage["source_season"] == "2025"
    assert lineage["target_season"] == "2026"
    assert lineage["derived_availability_date"] == "2026-02-15"
    assert lineage["prediction_cutoff"] == "2026-09-01"
    assert lineage["feature_family"] == "prior_nwr_scoring"
    assert lineage["legality_status"] == "allowed_prior_completed_season_fact"
    assert lineage["source_season_strictly_before_target"] == "yes"
    assert lineage["derived_availability_before_cutoff"] == "yes"
    assert lineage["target_window_overlap"] == "no"
    assert lineage["label_supplement_source_as_feature"] == "no"


def test_source_max_timestamp_after_cutoff_is_blocked() -> None:
    candidate = _candidate(
        [
            _feature(
                source_available_at="2026-09-02",
                source_max_timestamp="2026-09-02",
            )
        ]
    )

    assert candidate.legality_status == "blocked"
    issue_types = {issue.issue_type for issue in candidate.legality_issues}
    assert "post_cutoff_source_timestamp" in issue_types
    assert "post_cutoff_source_max_timestamp" in issue_types


def test_unknown_or_manual_review_sources_are_blocked() -> None:
    candidate = _candidate(
        [_feature(source_family="rotowire_factual_injury_status", feature_name="injury_note")]
    )

    assert candidate.legality_status == "blocked"
    issue_types = {issue.issue_type for issue in candidate.legality_issues}
    assert "unknown_or_manual_review_source" in issue_types
    assert "source_not_allowlisted" in issue_types


def test_identity_fields_are_not_model_features() -> None:
    candidate = _candidate([_feature(feature_name="player_id", source_field="player_id")])

    assert candidate.legality_status == "blocked"
    assert "identity_feature_blocked" in {issue.issue_type for issue in candidate.legality_issues}


def test_rookie_post_draft_uses_approved_manifest_timestamp() -> None:
    candidate = _rookie_candidate(
        [
            _feature(
                feature_name="draft_pick",
                value=12,
                source_family="official_draft_capital",
                source_field="overall_pick",
                source_available_at="2026-05-25T23:45:00+00:00",
                source_max_timestamp="2026-05-25T23:45:00+00:00",
            )
        ]
    )

    assert candidate.legality_status == "valid"
    assert candidate.input_snapshot_date == "2026-05-25T23:45:00+00:00"
    assert candidate.cutoff_id == "rookie_post_draft_2026_rookie_post_draft_manifest_approved_v1"


def test_rookie_post_draft_blocks_source_after_approved_cutoff() -> None:
    candidate = _rookie_candidate(
        [
            _feature(
                feature_name="draft_pick",
                value=12,
                source_family="official_draft_capital",
                source_field="overall_pick",
                source_available_at="2026-05-26T00:00:00+00:00",
                source_max_timestamp="2026-05-26T00:00:00+00:00",
            )
        ]
    )

    issue_types = {issue.issue_type for issue in candidate.legality_issues}
    assert candidate.legality_status == "blocked"
    assert "post_cutoff_source_timestamp" in issue_types
    assert "post_cutoff_source_max_timestamp" in issue_types


def test_rookie_forbidden_features_are_rejected() -> None:
    candidate = _rookie_candidate(
        [
            _feature(
                feature_name="rookie_adp_rank",
                source_family="official_draft_capital",
                source_field="adp",
            )
        ]
    )

    assert candidate.legality_status == "blocked"
    assert "forbidden_feature_family" in {issue.issue_type for issue in candidate.legality_issues}
