from __future__ import annotations

import csv

import pytest

from src.services.nwr_outcome_historical_row_factory import (
    build_historical_source_inventory,
    emit_candidate_training_row,
    write_dry_run_exports,
)
from src.services.nwr_outcome_training_row_service import FeatureSnapshot, PredictionSnapshot


def _snapshot(row_type: str = "rookie_post_draft") -> PredictionSnapshot:
    return PredictionSnapshot(
        cutoff_id="2026_post_draft_final",
        row_type=row_type,
        prediction_date="2026-05-01",
        input_snapshot_date="2026-05-01",
        label_available_date="2027-01-15",
        target_season=2026,
        target_horizon="year_1",
        parser_version="historical_row_factory_test_v1",
        source_manifest="test_manifest.json",
    )


def _player(**overrides):
    payload = {
        "player_id": "player_1",
        "player_name": "Legal Player",
        "position": "WR",
        "team_at_snapshot": "SF",
        "age_at_snapshot": 22.4,
        "experience_at_snapshot": 0,
    }
    payload.update(overrides)
    return payload


def _feature(
    *,
    feature_name: str = "draft_pick",
    value=12,
    source_family: str = "official_draft_capital",
    source_field: str = "overall_pick",
    source_available_at: str = "2026-04-28",
    source_max_timestamp: str = "2026-04-28",
    lineage: tuple[str, ...] = ("draft_capital.csv",),
    target_window_start: str = "",
    target_window_end: str = "",
) -> FeatureSnapshot:
    return FeatureSnapshot(
        feature_name=feature_name,
        value=value,
        source_family=source_family,
        source_field=source_field,
        source_available_at=source_available_at,
        source_max_timestamp=source_max_timestamp,
        lineage=lineage,
        target_window_start=target_window_start,
        target_window_end=target_window_end,
    )


def _csv(path, header, rows=None):
    rows = rows or []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_source_inventory_marks_forbidden_sources_as_blocked(tmp_path) -> None:
    blocked = tmp_path / "fantasypros_adp.csv"
    _csv(blocked, ["player_id", "player_name", "position", "adp"])

    inventory = build_historical_source_inventory([blocked])

    entry = inventory.entries[0]
    assert entry.classification == "blocked"
    assert entry.manual_review_required is False
    assert "Blocked" in entry.notes


def test_source_inventory_marks_unknown_sources_for_manual_review(tmp_path) -> None:
    unknown = tmp_path / "mystery_source.csv"
    _csv(unknown, ["player_id", "player_name", "position", "mystery_metric"])

    inventory = build_historical_source_inventory([unknown])

    entry = inventory.entries[0]
    assert entry.classification == "unknown"
    assert entry.manual_review_required is True


def test_source_inventory_detects_missing_required_identity_fields(tmp_path) -> None:
    missing_identity = tmp_path / "historical_week_scores.csv"
    _csv(missing_identity, ["player_id", "position", "week_score_total"])

    inventory = build_historical_source_inventory([missing_identity])

    entry = inventory.entries[0]
    assert entry.classification == "allowed"
    assert entry.required_fields_missing == ("player_name",)
    assert entry.manual_review_required is True


def test_row_factory_only_supports_approved_row_families() -> None:
    for row_type in ("rookie_post_draft", "all_player_pre_week1", "offseason_carryover"):
        emitted = emit_candidate_training_row(
            row_type=row_type,
            player_record=_player(),
            snapshot=_snapshot(row_type),
            feature_snapshots=[_feature()],
            as_of_date="2027-01-15",
        )
        assert emitted.row_type == row_type
        assert emitted.training_row is not None

    with pytest.raises(ValueError, match="Unsupported row_type"):
        emit_candidate_training_row(
            row_type="rookie_pre_draft",
            player_record=_player(),
            snapshot=_snapshot(),
            feature_snapshots=[_feature()],
            as_of_date="2027-01-15",
        )


def test_missing_identity_fields_block_row_emission() -> None:
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record={"player_id": "player_1", "position": "WR"},
        snapshot=_snapshot(),
        feature_snapshots=[_feature()],
        as_of_date="2027-01-15",
    )

    assert emitted.training_row is None
    assert emitted.blocked_reason == "missing_identity_fields"
    assert not emitted.legality_audit.valid


def test_missing_optional_features_are_masked_not_zero_filled() -> None:
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record=_player(),
        snapshot=_snapshot(),
        feature_snapshots=[_feature(feature_name="draft_pick", value=12)],
        optional_feature_names=("draft_pick", "route_participation"),
        as_of_date="2027-01-15",
    )

    assert emitted.feature_vector["route_participation"] is None
    assert emitted.missingness_mask["route_participation"] is True
    assert emitted.feature_vector["draft_pick"] == 12


def test_post_cutoff_timestamp_fails_legality_and_blocks_training_row() -> None:
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record=_player(),
        snapshot=_snapshot(),
        feature_snapshots=[_feature(source_available_at="2026-05-02")],
        as_of_date="2027-01-15",
    )

    assert emitted.training_row is None
    assert emitted.blocked_reason == "feature_legality_failed"
    assert "post_cutoff_source_timestamp" in {
        issue.issue_type for issue in emitted.legality_audit.issues
    }


def test_target_window_overlap_fails_legality() -> None:
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record=_player(),
        snapshot=_snapshot(),
        feature_snapshots=[
            _feature(
                feature_name="same_season_points",
                target_window_start="2026-09-01",
                target_window_end="2026-12-31",
            )
        ],
        as_of_date="2027-01-15",
    )

    assert emitted.training_row is None
    assert "target_window_overlap" in {issue.issue_type for issue in emitted.legality_audit.issues}


def test_forbidden_feature_and_source_names_fail_legality() -> None:
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record=_player(),
        snapshot=_snapshot(),
        feature_snapshots=[
            _feature(feature_name="market rank", source_field="market_rank"),
            _feature(
                feature_name="public_projection_points",
                source_family="public_projections",
                source_field="projection",
            ),
        ],
        as_of_date="2027-01-15",
    )

    issue_types = {issue.issue_type for issue in emitted.legality_audit.issues}
    assert emitted.training_row is None
    assert "forbidden_feature_family" in issue_types
    assert "source_blocked" in issue_types


def test_incomplete_lineage_fails_legality() -> None:
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record=_player(),
        snapshot=_snapshot(),
        feature_snapshots=[_feature(lineage=())],
        as_of_date="2027-01-15",
    )

    assert emitted.training_row is None
    assert "incomplete_lineage" in {issue.issue_type for issue in emitted.legality_audit.issues}


def test_stale_prior_row_reuse_is_rejected() -> None:
    with pytest.raises(ValueError, match="Stale prior-row reuse"):
        emit_candidate_training_row(
            row_type="offseason_carryover",
            player_record=_player(prior_row_cutoff_id="old_cutoff"),
            snapshot=_snapshot("offseason_carryover"),
            feature_snapshots=[_feature()],
            as_of_date="2027-01-15",
        )


def test_candidate_rows_have_deterministic_row_id_and_snapshot_hash() -> None:
    kwargs = {
        "row_type": "rookie_post_draft",
        "player_record": _player(),
        "snapshot": _snapshot(),
        "feature_snapshots": [_feature(feature_name="draft_pick", value=12)],
        "as_of_date": "2027-01-15",
    }
    first = emit_candidate_training_row(**kwargs)
    second = emit_candidate_training_row(**kwargs)
    changed = emit_candidate_training_row(
        **{
            **kwargs,
            "feature_snapshots": [_feature(feature_name="draft_pick", value=13)],
        }
    )

    assert first.row_id == second.row_id
    assert first.snapshot_hash == second.snapshot_hash
    assert first.snapshot_hash != changed.snapshot_hash


def test_training_rows_are_not_materialized_before_label_available_date() -> None:
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record=_player(),
        snapshot=_snapshot(),
        feature_snapshots=[_feature()],
        as_of_date="2026-12-31",
    )

    assert emitted.row_id
    assert emitted.training_row is None
    assert emitted.blocked_reason == "label_not_available"


def test_dry_run_exports_are_written_to_requested_folder(tmp_path) -> None:
    source = tmp_path / "historical_week_scores.csv"
    _csv(source, ["player_id", "player_name", "position", "week_score_total"])
    inventory = build_historical_source_inventory([source])
    emitted = emit_candidate_training_row(
        row_type="rookie_post_draft",
        player_record=_player(),
        snapshot=_snapshot(),
        feature_snapshots=[
            _feature(feature_name="rush_first_downs_previous_season", value=None),
            _feature(feature_name="injury_context_status", value="clean"),
        ],
        as_of_date="2027-01-15",
    )

    write_dry_run_exports(
        output_dir=tmp_path / "exports",
        inventory=inventory,
        candidates=[emitted],
    )

    assert (tmp_path / "exports" / "historical_source_inventory.csv").exists()
    assert (tmp_path / "exports" / "candidate_training_rows_dry_run.csv").exists()
    assert (tmp_path / "exports" / "source_coverage_report.csv").exists()
    assert (tmp_path / "exports" / "missingness_summary.csv").exists()
    assert (tmp_path / "exports" / "blocked_forbidden_source_summary.csv").exists()
