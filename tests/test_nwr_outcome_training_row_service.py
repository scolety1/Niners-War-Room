from __future__ import annotations

import pytest

from src.services.nwr_outcome_training_row_service import (
    APP_PROBABILITY_STATUSES,
    FeatureSnapshot,
    PredictionSnapshot,
    build_training_row,
    contract_field_names,
    generate_row_id,
    materialize_training_row_if_label_available,
    missingness_mask,
    model_split_registry_skeleton,
    snapshot_hash,
    validate_feature_legality,
    validate_training_row_schema,
)


def _snapshot(row_type: str = "rookie_post_draft") -> PredictionSnapshot:
    return PredictionSnapshot(
        cutoff_id="2026_post_draft_final",
        row_type=row_type,
        prediction_date="2026-05-01",
        input_snapshot_date="2026-05-01",
        label_available_date="2027-01-15",
        target_season=2026,
        target_horizon="year_1",
        parser_version="training_row_contract_v1",
        source_manifest="manifest_2026_post_draft.json",
    )


def _feature(
    *,
    feature_name: str = "draft_capital_pick",
    source_family: str = "official_draft_capital",
    source_field: str = "overall_pick",
    source_available_at: str = "2026-04-27",
    source_max_timestamp: str = "2026-04-27",
    future_data_flag: bool = False,
    target_window_start: str = "",
    target_window_end: str = "",
    lineage: tuple[str, ...] = ("raw/official_draft.csv",),
) -> FeatureSnapshot:
    return FeatureSnapshot(
        feature_name=feature_name,
        value=12,
        source_family=source_family,
        source_field=source_field,
        source_available_at=source_available_at,
        source_max_timestamp=source_max_timestamp,
        lineage=lineage,
        future_data_flag=future_data_flag,
        target_window_start=target_window_start,
        target_window_end=target_window_end,
    )


def _training_row():
    return build_training_row(
        player_id="puka_2023",
        player_name="Example Receiver",
        position="WR",
        snapshot=_snapshot(),
        team_at_snapshot="LAR",
        age_at_snapshot=22.1,
        experience_at_snapshot=0,
        feature_vector={"draft_capital_pick": 177, "college_yprr": None},
        outcome_window="2026_regular_season",
        label_schema_version="nwr_outcome_labels_v1",
        source_max_timestamp="2026-04-27",
    )


def test_same_business_key_produces_same_row_id() -> None:
    kwargs = {
        "row_type": "rookie_post_draft",
        "player_id": "wr_123",
        "position": "wr",
        "cutoff_id": "2026_post_draft_final",
        "input_snapshot_date": "2026-05-01",
        "target_season": 2026,
        "target_horizon": "year_1",
    }

    assert generate_row_id(**kwargs) == generate_row_id(**kwargs)


def test_changing_feature_payload_changes_snapshot_hash() -> None:
    base = {
        "row_id": "nwr_tr_example",
        "feature_vector": {"draft_capital_pick": 12},
        "missingness_mask": {"draft_capital_pick": False},
    }
    changed = {
        "row_id": "nwr_tr_example",
        "feature_vector": {"draft_capital_pick": 13},
        "missingness_mask": {"draft_capital_pick": False},
    }

    assert snapshot_hash(base) != snapshot_hash(changed)


def test_post_cutoff_source_timestamp_fails_legality() -> None:
    audit = validate_feature_legality(
        [_feature(source_available_at="2026-05-02")],
        input_snapshot_date="2026-05-01",
        label_available_date="2027-01-15",
    )

    assert not audit.valid
    assert {issue.issue_type for issue in audit.issues} == {"post_cutoff_source_timestamp"}


def test_forbidden_feature_name_fails_legality() -> None:
    audit = validate_feature_legality(
        [
            _feature(feature_name="adp_overall_rank"),
            _feature(feature_name="same-season final stats"),
            _feature(source_field="RotoWire projections/outlooks/values"),
        ],
        input_snapshot_date="2026-05-01",
        label_available_date="2027-01-15",
    )

    assert not audit.valid
    assert "forbidden_feature_family" in {issue.issue_type for issue in audit.issues}


def test_future_data_and_incomplete_lineage_fail_legality() -> None:
    audit = validate_feature_legality(
        [
            _feature(feature_name="future_depth_role", future_data_flag=True),
            _feature(feature_name="unreceipted_usage", lineage=()),
        ],
        input_snapshot_date="2026-05-01",
        label_available_date="2027-01-15",
    )

    issue_types = {issue.issue_type for issue in audit.issues}
    assert not audit.valid
    assert "future_data_flag" in issue_types
    assert "incomplete_lineage" in issue_types


def test_forbidden_upstream_source_fails_legality() -> None:
    audit = validate_feature_legality(
        [_feature(source_family="fantasypros", source_field="rank")],
        input_snapshot_date="2026-05-01",
        label_available_date="2027-01-15",
    )

    issue_types = {issue.issue_type for issue in audit.issues}
    assert not audit.valid
    assert "source_blocked" in issue_types


def test_target_window_overlap_fails_legality() -> None:
    audit = validate_feature_legality(
        [
            _feature(
                feature_name="same_season_week_4_score",
                source_field="week_4_score",
                target_window_start="2026-09-01",
                target_window_end="2026-12-30",
            )
        ],
        input_snapshot_date="2026-05-01",
        label_available_date="2027-01-15",
    )

    issue_types = {issue.issue_type for issue in audit.issues}
    assert not audit.valid
    assert "target_window_overlap" in issue_types


def test_missingness_mask_preserves_nulls_instead_of_zero_filling() -> None:
    features = {"college_yprr": None, "target_share": "", "draft_capital_pick": 12}

    assert missingness_mask(features) == {
        "college_yprr": True,
        "target_share": True,
        "draft_capital_pick": False,
    }
    assert features["college_yprr"] is None
    assert features["target_share"] == ""


def test_training_row_blocked_before_label_available_date() -> None:
    row = _training_row()

    assert materialize_training_row_if_label_available(row, as_of_date="2026-12-31") is None
    assert materialize_training_row_if_label_available(row, as_of_date="2027-01-15") == row


def test_unsupported_row_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported row_type"):
        _snapshot(row_type="rookie_pre_draft")
        generate_row_id(
            row_type="rookie_pre_draft",
            player_id="wr_123",
            position="WR",
            cutoff_id="2026_pre_draft",
            input_snapshot_date="2026-04-01",
            target_season=2026,
            target_horizon="year_1",
        )


def test_supported_row_types_pass_basic_schema_validation() -> None:
    for row_type in ("rookie_post_draft", "all_player_pre_week1", "offseason_carryover"):
        row = build_training_row(
            player_id="player_1",
            player_name="Schema Player",
            position="RB",
            snapshot=_snapshot(row_type=row_type),
            team_at_snapshot="SF",
            age_at_snapshot=24.5,
            experience_at_snapshot=2,
            feature_vector={"qualified_ppg_prev_year": 11.2},
            outcome_window="2026_regular_season",
            label_schema_version="nwr_outcome_labels_v1",
            source_max_timestamp="2026-05-01",
            probability_status="in_development",
        )

        assert validate_training_row_schema(row).valid


def test_player_identity_fields_are_not_model_features() -> None:
    with pytest.raises(ValueError, match="identity fields"):
        build_training_row(
            player_id="player_1",
            player_name="Identity Player",
            position="WR",
            snapshot=_snapshot(),
            team_at_snapshot="SF",
            age_at_snapshot=23.0,
            experience_at_snapshot=1,
            feature_vector={"player_name": "Identity Player"},
            outcome_window="2026_regular_season",
            label_schema_version="nwr_outcome_labels_v1",
            source_max_timestamp="2026-05-01",
        )


def test_contracts_include_required_sprint_2_concepts_and_statuses() -> None:
    contracts = contract_field_names()
    split_specs = model_split_registry_skeleton()

    assert "row_id" in contracts.training_rows
    assert "source_manifest" in contracts.training_rows
    assert "source_available_at" in contracts.feature_snapshots
    assert "split_id" in contracts.model_split_registry
    assert APP_PROBABILITY_STATUSES == (
        "ready",
        "in_development",
        "needs_data",
        "model_unavailable",
        "insufficient_evidence",
        "not_applicable",
        "leakage_audit_failed",
        "source_stale",
        "manual_review_pending",
    )
    assert split_specs[0].split_type == "walk_forward"
