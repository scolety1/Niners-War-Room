from __future__ import annotations

import csv
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.public_source_import_service import (
    DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
    LVE_PROJECTION_SCORING,
    PUBLIC_SOURCE_TEMPLATE_HEADERS,
    build_public_source_feature_readiness_rows,
    build_public_source_match_rows,
    build_public_source_player_match_rows,
    build_unscored_player_rows,
    create_public_source_model_applied_pack,
    create_public_source_model_input_candidate,
    create_public_source_model_preview,
    create_public_source_model_promotion_candidate,
    create_public_source_normalization_worklist,
    create_public_source_snapshot,
    public_source_backfill_acceptance_rows,
    public_source_backfill_acceptance_summary_rows,
    public_source_domain_rows,
    public_source_feature_readiness_summary_rows,
    public_source_model_applied_pack_review_rows,
    public_source_model_applied_pack_review_summary_rows,
    public_source_model_applied_pack_snapshot_rows,
    public_source_model_input_candidate_coverage_rows,
    public_source_model_input_candidate_coverage_summary_rows,
    public_source_model_input_candidate_rows,
    public_source_model_input_candidate_snapshot_rows,
    public_source_model_input_candidate_validation_rows,
    public_source_model_input_candidate_validation_summary_rows,
    public_source_model_preview_comparison_rows,
    public_source_model_preview_comparison_summary_rows,
    public_source_model_preview_review_rows,
    public_source_model_preview_review_summary_rows,
    public_source_model_preview_snapshot_rows,
    public_source_model_promotion_candidate_review_rows,
    public_source_model_promotion_candidate_review_summary_rows,
    public_source_model_promotion_candidate_snapshot_rows,
    public_source_normalization_worklist_rows,
    public_source_normalization_worklist_snapshot_rows,
    public_source_player_match_summary_rows,
    public_source_policy_rows,
    public_source_projection_rescore_rows,
    public_source_projection_rescore_summary_rows,
    public_source_readiness_rows,
    public_source_snapshot_rows,
    validate_public_source_inputs,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/public_sources")
SAMPLE_PACK = Path("sample_data/2026_pre_declaration")


def test_public_source_templates_validate_cleanly() -> None:
    report = validate_public_source_inputs(TEMPLATE_ROOT)

    assert report.status == "ready"
    assert report.issues == ()
    assert set(report.row_counts) == set(PUBLIC_SOURCE_TEMPLATE_HEADERS)


def test_public_source_snapshot_copies_files_and_writes_manifest(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    result = create_public_source_snapshot(
        source_root,
        snapshot_root,
        snapshot_id="Night Before Draft",
        created_at_utc=datetime(2026, 8, 1, 12, 30, tzinfo=UTC),
    )

    assert result.created is True
    assert result.snapshot_id == "night_before_draft"
    assert result.manifest_path is not None
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["validation_status"] == "ready"
    assert manifest["scoring_effect"] == "none; raw source snapshot only"
    assert len(manifest["files"]) == len(PUBLIC_SOURCE_TEMPLATE_HEADERS)
    assert all((result.snapshot_path / name).exists() for name in PUBLIC_SOURCE_TEMPLATE_HEADERS)
    rows = public_source_snapshot_rows(snapshot_root)
    assert rows[0]["snapshot_id"] == "night_before_draft"


def test_public_source_snapshot_refuses_duplicates(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    snapshot_root = tmp_path / "snapshots"

    first = create_public_source_snapshot(source_root, snapshot_root, snapshot_id="same")
    second = create_public_source_snapshot(source_root, snapshot_root, snapshot_id="same")

    assert first.created is True
    assert second.created is False
    assert second.status == "blocked"
    assert "already exists" in second.message


def test_public_source_snapshot_blocks_invalid_source_root(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "public_source_catalog.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["public_source_catalog.csv"],
        [
            {
                "source_id": "ktc",
                "source_name": "KeepTradeCut",
                "source_role": "market",
                "requires_scrape": "true",
            }
        ],
    )

    result = create_public_source_snapshot(
        source_root,
        tmp_path / "snapshots",
        snapshot_id="bad_source",
    )

    assert result.created is False
    assert result.status == "blocked"
    assert not result.snapshot_path.exists()


def test_public_source_validation_rejects_bad_position_and_scores(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p1",
                "player_name": "Bad Kicker",
                "position": "K",
                "proj_fantasy_points_source": "many",
            }
        ],
    )

    report = validate_public_source_inputs(source_root)

    issue_text = {issue.issue for issue in report.issues}
    assert "Unsupported position." in issue_text
    assert "proj_fantasy_points_source must be numeric." in issue_text
    assert report.status == "blocked"


def test_public_source_policy_rows_include_accepted_and_rejected_sources() -> None:
    rows = {row["source_key"]: row for row in public_source_policy_rows()}

    assert rows["sleeper"]["status"] == "approved"
    assert rows["ffa"]["allowed_uses"] == "projection_stat_lines|lve_projection_rescoring"
    assert rows["ktc"]["status"] == "rejected"
    assert "scraping" in rows["keeptradecut"]["forbidden_uses"]


def test_public_source_validation_blocks_rejected_catalog_source(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "public_source_catalog.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["public_source_catalog.csv"],
        [
            {
                "source_id": "ktc",
                "source_name": "KeepTradeCut",
                "source_role": "market",
                "requires_scrape": "true",
            }
        ],
    )

    report = validate_public_source_inputs(source_root)

    assert report.status == "blocked"
    assert "Source is rejected by the v1 source policy." in {
        issue.issue for issue in report.issues
    }


def test_public_source_validation_warns_on_unknown_source_reference(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "public_source_catalog.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["public_source_catalog.csv"],
        [
            {
                "source_id": "ffa_2026",
                "source_name": "Fantasy Football Analytics",
                "source_role": "projection",
                "requires_scrape": "false",
            }
        ],
    )
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "unknown_projection",
                "season": "2026",
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "proj_fantasy_points_source": "180",
            }
        ],
    )

    report = validate_public_source_inputs(source_root)

    assert report.status == "review"
    assert "Source key is not listed in public_source_catalog.csv." in {
        issue.issue for issue in report.issues
    }


def test_projection_rescore_uses_lve_scoring_and_direct_first_downs(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p_wr",
                "player_name": "Receiver One",
                "position": "WR",
                "proj_targets": "100",
                "proj_receptions": "70",
                "proj_rec_yards": "1000",
                "proj_rec_tds": "8",
                "proj_rec_first_downs": "55",
                "proj_fumbles_lost": "1",
            }
        ],
    )

    rows = public_source_projection_rescore_rows(source_root)

    assert rows[0]["projected_lve_points"] == "153.00"
    assert rows[0]["first_down_source"] == "direct_partial"
    assert "first_downs_estimated" not in rows[0]["missing_projection_flags"]


def test_public_source_projection_scoring_uses_shared_lve_constants() -> None:
    assert LVE_PROJECTION_SCORING == {
        "pass_yard": LVE_SCORING["passing_yard"],
        "pass_td": LVE_SCORING["passing_td"],
        "interception": LVE_SCORING["interception"],
        "rush_yard": LVE_SCORING["rushing_yard"],
        "rush_td": LVE_SCORING["rushing_td"],
        "rec_yard": LVE_SCORING["receiving_yard"],
        "rec_td": LVE_SCORING["receiving_td"],
        "return_yard": LVE_SCORING["return_yard"],
        "return_td": LVE_SCORING["return_td"],
        "rush_rec_first_down": LVE_SCORING["rushing_receiving_first_down"],
        "fumble_lost": LVE_SCORING["fumble_lost"],
    }


def test_projection_rescore_estimates_missing_first_downs(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p_rb",
                "player_name": "Runner One",
                "position": "RB",
                "proj_rush_attempts": "200",
                "proj_rush_yards": "900",
                "proj_rush_tds": "7",
                "proj_targets": "50",
                "proj_rec_yards": "300",
                "proj_rec_tds": "2",
            }
        ],
    )

    rows = public_source_projection_rescore_rows(source_root)
    summary = {
        row["metric"]: row["value"]
        for row in public_source_projection_rescore_summary_rows(rows)
    }

    assert rows[0]["projected_lve_points"] == "180.40"
    assert rows[0]["projected_rush_first_downs"] == "46.00"
    assert rows[0]["projected_rec_first_downs"] == "15.00"
    assert rows[0]["first_down_source"] == "estimated"
    assert rows[0]["missing_projection_flags"] == "first_downs_estimated"
    assert summary["estimated_first_down_rows"] == 1


def test_public_source_matching_uses_player_id_and_name(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "proj_fantasy_points_source": "180",
            }
        ],
    )
    _write_rows(
        source_root / "player_market_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_market_inputs.csv"],
        [
            {
                "market_source_id": "market_test",
                "season": "2026",
                "player_key": "",
                "player_name": "Lamar Jackson",
                "position": "WR",
                "value_1qb": "9200",
            }
        ],
    )

    rows = build_public_source_match_rows(SAMPLE_PACK, source_root)
    by_name = {row["player_name"]: row for row in rows}

    assert by_name["De'Von Achane"]["projection_match"] is True
    assert by_name["Lamar Jackson"]["market_match"] is True
    assert "projection" in by_name["Lamar Jackson"]["missing_sources"]

    domain_rows = {
        row["domain"]: row for row in public_source_domain_rows(rows)
    }
    assert domain_rows["projection"]["matched_players"] == 1
    assert domain_rows["market"]["matched_players"] == 1
    assert domain_rows["injury"]["status"] == "empty"


def test_player_match_review_uses_id_then_name_fallback(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p_achane",
                "player_name": "Wrong Display Name",
                "position": "RB",
                "proj_fantasy_points_source": "180",
            },
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "proj_fantasy_points_source": "240",
            },
        ],
    )

    rows = build_public_source_player_match_rows(SAMPLE_PACK, source_root)
    by_name = {row["source_player_name"]: row for row in rows}

    assert by_name["Wrong Display Name"]["match_status"] == "matched"
    assert by_name["Wrong Display Name"]["match_method"] == "id"
    assert by_name["Wrong Display Name"]["matched_player_id"] == "p_achane"
    assert by_name["Lamar Jackson"]["match_status"] == "matched"
    assert by_name["Lamar Jackson"]["match_method"] == "name_position"
    summary = {
        row["match_status"]: row
        for row in public_source_player_match_summary_rows(rows)
    }
    assert summary["matched"]["rows"] == 2


def test_player_match_review_flags_ambiguous_names(tmp_path: Path) -> None:
    pack = _copy_sample_pack_with_extra_player(
        tmp_path,
        {
            "player_id": "p_lamar_other",
            "player_name": "Lamar Jackson",
            "merge_name": "lamar jackson",
            "position": "QB",
        },
    )
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "proj_fantasy_points_source": "240",
            },
        ],
    )

    rows = build_public_source_player_match_rows(pack, source_root)

    assert rows[0]["match_status"] == "ambiguous"
    assert rows[0]["candidate_player_ids"] == "p_lamar|p_lamar_other"
    assert "Add player_key" in rows[0]["suggested_fix"]


def test_player_match_review_flags_unmatched_rows(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "",
                "player_name": "Not A Real Player",
                "position": "WR",
                "proj_fantasy_points_source": "12",
            },
        ],
    )

    rows = build_public_source_player_match_rows(SAMPLE_PACK, source_root)

    assert rows[0]["match_status"] == "unmatched"
    assert "No roster/player record matches" in rows[0]["issue"]


def test_feature_readiness_maps_matched_sources_to_active_features(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "role_security",
                "requires_source_type": "depth_chart",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "proj_fantasy_points_source": "180",
            }
        ],
    )

    rows = build_public_source_feature_readiness_rows(
        SAMPLE_PACK,
        source_root,
        registry,
    )
    achane_rows = {
        row["feature_name"]: row
        for row in rows
        if row["player_id"] == "p_achane"
    }

    assert achane_rows["lve_projection_value"]["status"] == "source_available"
    assert achane_rows["role_security"]["status"] == "missing_source"
    assert achane_rows["age_curve"]["status"] == "manual_required"
    summary = {
        row["status"]: row
        for row in public_source_feature_readiness_summary_rows(rows)
    }
    assert summary["source_available"]["rows"] == 1
    assert summary["manual_required"]["rows"] >= 1


def test_feature_readiness_prefers_normalized_backfill_over_raw_source(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "role_security",
                "requires_source_type": "depth_chart",
                "scoring_status": "active_v1",
            },
        ],
    )
    _write_rows(
        source_root / "normalized_veteran_feature_backfill.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["normalized_veteran_feature_backfill.csv"],
        [
            {
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "lve_projection_value": "91",
                "role_security": "77",
                "overall_feature_confidence": "84",
                "manual_review_required": "false",
            }
        ],
    )

    rows = build_public_source_feature_readiness_rows(
        SAMPLE_PACK,
        source_root,
        registry,
    )
    achane_rows = {
        row["feature_name"]: row
        for row in rows
        if row["player_id"] == "p_achane"
    }

    assert achane_rows["lve_projection_value"]["status"] == "ready"
    assert achane_rows["lve_projection_value"]["normalized_score"] == "91"
    assert achane_rows["lve_projection_value"]["confidence"] == "84"
    assert achane_rows["role_security"]["status"] == "ready"


def test_feature_readiness_reviews_flagged_normalized_backfill(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
        ],
    )
    _write_rows(
        source_root / "normalized_veteran_feature_backfill.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["normalized_veteran_feature_backfill.csv"],
        [
            {
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "lve_projection_value": "91",
                "overall_feature_confidence": "84",
                "manual_review_required": "true",
            }
        ],
    )

    rows = build_public_source_feature_readiness_rows(
        SAMPLE_PACK,
        source_root,
        registry,
    )
    achane = next(
        row
        for row in rows
        if row["player_id"] == "p_achane"
        and row["feature_name"] == "lve_projection_value"
    )

    assert achane["status"] == "review"
    assert "Review backfill flags" in achane["next_action"]


def test_normalization_worklist_rows_exclude_ready_features() -> None:
    readiness_rows = [
        {
            "player_id": "p_ready",
            "player_name": "Ready Player",
            "position": "WR",
            "feature_name": "lve_projection_value",
            "required_source_type": "projection",
            "source_domain": "projection",
            "status": "ready",
        },
        {
            "player_id": "p_source",
            "player_name": "Source Player",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "required_source_type": "projection",
            "source_domain": "projection",
            "status": "source_available",
            "league_rank": "42",
            "source_evidence": "projection",
            "next_action": "Normalize matched source rows.",
        },
        {
            "player_id": "p_manual",
            "player_name": "Manual Player",
            "position": "QB",
            "feature_name": "age_curve",
            "required_source_type": "manual_note",
            "source_domain": "manual_review",
            "status": "manual_required",
        },
    ]

    rows = public_source_normalization_worklist_rows(readiness_rows)
    by_player = {row["player_id"]: row for row in rows}

    assert "p_ready" not in by_player
    assert by_player["p_source"]["normalization_task"] == "derive_normalized_0_100_score"
    assert by_player["p_source"]["priority"] == "high"
    assert "derive a reviewed 0-100 score" in by_player["p_source"]["task_reason"]
    assert by_player["p_source"]["scoring_effect"] == "none"
    assert by_player["p_manual"]["normalization_task"] == "enter_reviewed_local_baseline"


def test_create_normalization_worklist_writes_csv_and_manifest(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "proj_fantasy_points_source": "180",
            }
        ],
    )

    result = create_public_source_normalization_worklist(
        SAMPLE_PACK,
        source_root,
        registry,
        tmp_path / "worklists",
        worklist_id="Source Worklist",
        created_at_utc=datetime(2026, 8, 2, 9, 0, tzinfo=UTC),
    )

    assert result.created is True
    assert result.worklist_id == "source_worklist"
    assert result.csv_path is not None
    assert result.manifest_path is not None
    csv_rows = list(csv.DictReader(result.csv_path.open(newline="", encoding="utf-8")))
    assert any(row["player_id"] == "p_achane" for row in csv_rows)
    assert all(row["priority"] for row in csv_rows)
    assert all(row["scoring_effect"] == "none" for row in csv_rows)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["scoring_effect"] == "none; normalization worklist only"
    assert manifest["priority_counts"]
    snapshots = public_source_normalization_worklist_snapshot_rows(tmp_path / "worklists")
    assert snapshots[0]["worklist_id"] == "source_worklist"
    assert snapshots[0]["priority_counts"]


def test_create_normalization_worklist_refuses_duplicate_id(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )
    output_root = tmp_path / "worklists"

    first = create_public_source_normalization_worklist(
        SAMPLE_PACK,
        source_root,
        registry,
        output_root,
        worklist_id="same",
    )
    second = create_public_source_normalization_worklist(
        SAMPLE_PACK,
        source_root,
        registry,
        output_root,
        worklist_id="same",
    )

    assert first.created is True
    assert second.created is False
    assert second.status == "blocked"


def test_backfill_acceptance_accepts_ready_normalized_rows() -> None:
    rows = public_source_backfill_acceptance_rows(
        [
            {
                "player_id": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "feature_name": "lve_projection_value",
                "status": "ready",
                "normalized_score": "91",
                "confidence": "84",
            }
        ]
    )

    assert rows[0]["acceptance_status"] == "accepted"
    assert rows[0]["blocking"] is False
    assert rows[0]["decision_effect"] == "review only; no score impact"
    summary = {
        row["acceptance_status"]: row
        for row in public_source_backfill_acceptance_summary_rows(rows)
    }
    assert summary["accepted"]["rows"] == 1


def test_backfill_acceptance_reviews_low_or_missing_confidence() -> None:
    rows = public_source_backfill_acceptance_rows(
        [
            {
                "player_id": "p_low",
                "player_name": "Low Confidence",
                "position": "WR",
                "feature_name": "role_security",
                "status": "ready",
                "normalized_score": "70",
                "confidence": "64",
            },
            {
                "player_id": "p_blank",
                "player_name": "Blank Confidence",
                "position": "WR",
                "feature_name": "age_curve",
                "status": "ready",
                "normalized_score": "70",
                "confidence": "",
            },
            {
                "player_id": "p_bad_confidence",
                "player_name": "Bad Confidence",
                "position": "WR",
                "feature_name": "role_security",
                "status": "ready",
                "normalized_score": "70",
                "confidence": "not-a-number",
            },
            {
                "player_id": "p_flagged",
                "player_name": "Flagged",
                "position": "WR",
                "feature_name": "target_earning_stability",
                "status": "review",
                "normalized_score": "70",
                "confidence": "80",
            },
        ]
    )

    assert {row["acceptance_status"] for row in rows} == {"review"}
    assert all(row["blocking"] is False for row in rows)
    assert all(row["priority"] == "high" for row in rows)


def test_backfill_acceptance_blocks_unresolved_features() -> None:
    rows = public_source_backfill_acceptance_rows(
        [
            {
                "player_id": "p_source",
                "player_name": "Needs Normalize",
                "position": "RB",
                "feature_name": "lve_projection_value",
                "status": "source_available",
                "normalized_score": "",
                "confidence": "",
            },
            {
                "player_id": "p_manual",
                "player_name": "Needs Manual",
                "position": "QB",
                "feature_name": "age_curve",
                "status": "manual_required",
                "normalized_score": "",
                "confidence": "",
            },
            {
                "player_id": "p_missing",
                "player_name": "Missing Source",
                "position": "TE",
                "feature_name": "route_share_stability",
                "status": "missing_source",
                "normalized_score": "",
                "confidence": "",
            },
        ]
    )

    assert {row["acceptance_status"] for row in rows} == {"blocked"}
    assert all(row["blocking"] is True for row in rows)
    assert all("Complete normalization worklist" in row["next_action"] for row in rows)


def test_backfill_acceptance_blocks_unknown_readiness_status() -> None:
    rows = public_source_backfill_acceptance_rows(
        [
            {
                "player_id": "p_unknown",
                "player_name": "Unknown Status",
                "position": "RB",
                "feature_name": "lve_projection_value",
                "status": "",
                "normalized_score": "90",
                "confidence": "90",
            }
        ]
    )

    assert rows[0]["acceptance_status"] == "blocked"
    assert rows[0]["blocking"] is True
    assert "unknown" in rows[0]["reason"]


def test_model_input_candidate_rows_include_only_accepted_backfill() -> None:
    acceptance_rows = [
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "91",
            "acceptance_status": "accepted",
        },
        {
            "player_id": "p_lamar",
            "position": "QB",
            "feature_name": "age_curve",
            "normalized_score": "82",
            "acceptance_status": "review",
        },
    ]

    rows = public_source_model_input_candidate_rows(SAMPLE_PACK, acceptance_rows)

    assert len(rows) == 1
    assert rows[0]["season"] == "2026"
    assert rows[0]["snapshot_date"] == "2026-08-01"
    assert rows[0]["player_id"] == "p_achane"
    assert rows[0]["source_key"] == "public_source_backfill_candidate"
    assert rows[0]["source_confidence"] == "derived"
    assert rows[0]["is_missing"] == "false"
    assert rows[0]["is_user_override"] == "false"


def test_create_model_input_candidate_writes_accepted_feature_csv(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )
    _write_rows(
        source_root / "normalized_veteran_feature_backfill.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["normalized_veteran_feature_backfill.csv"],
        [
            {
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "lve_projection_value": "91",
                "age_curve": "88",
                "overall_feature_confidence": "84",
                "manual_review_required": "false",
            }
        ],
    )

    result = create_public_source_model_input_candidate(
        SAMPLE_PACK,
        source_root,
        registry,
        tmp_path / "candidates",
        candidate_id="Accepted Backfill",
        created_at_utc=datetime(2026, 8, 3, 10, 0, tzinfo=UTC),
    )

    assert result.created is True
    assert result.candidate_id == "accepted_backfill"
    assert result.csv_path is not None
    assert result.manifest_path is not None
    csv_rows = list(csv.DictReader(result.csv_path.open(newline="", encoding="utf-8")))
    assert {
        (row["player_id"], row["feature_name"])
        for row in csv_rows
    } == {
        ("p_achane", "lve_projection_value"),
        ("p_achane", "age_curve"),
    }
    assert all(row["source_key"] == "public_source_backfill_candidate" for row in csv_rows)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["scoring_effect"] == "none; model input candidate only"
    assert manifest["live_mutation"] is False
    assert manifest["candidate_schema"] == "veteran_feature_scores"
    assert manifest["row_count"] == 2
    assert manifest["player_count"] == 1
    assert manifest["feature_count"] == 2
    assert manifest["accepted_input_count"] == 2
    snapshots = public_source_model_input_candidate_snapshot_rows(
        tmp_path / "candidates"
    )
    assert snapshots[0]["candidate_id"] == "accepted_backfill"
    assert snapshots[0]["player_count"] == 1
    assert snapshots[0]["feature_count"] == 2


def test_create_model_input_candidate_refuses_empty_export(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )

    result = create_public_source_model_input_candidate(
        SAMPLE_PACK,
        source_root,
        registry,
        tmp_path / "candidates",
        candidate_id="empty",
    )

    assert result.created is False
    assert result.status == "blocked"
    assert result.csv_path is None


def test_create_model_input_candidate_refuses_duplicate_id(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
        ],
    )
    _write_rows(
        source_root / "normalized_veteran_feature_backfill.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["normalized_veteran_feature_backfill.csv"],
        [
            {
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "lve_projection_value": "91",
                "overall_feature_confidence": "84",
                "manual_review_required": "false",
            }
        ],
    )
    output_root = tmp_path / "candidates"

    first = create_public_source_model_input_candidate(
        SAMPLE_PACK,
        source_root,
        registry,
        output_root,
        candidate_id="same",
    )
    second = create_public_source_model_input_candidate(
        SAMPLE_PACK,
        source_root,
        registry,
        output_root,
        candidate_id="same",
    )

    assert first.created is True
    assert second.created is False
    assert second.status == "blocked"


def test_model_input_candidate_validation_accepts_safe_candidate_rows(
    tmp_path: Path,
) -> None:
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
        ],
    )
    candidate_rows = [
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "91",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        }
    ]

    rows = public_source_model_input_candidate_validation_rows(
        SAMPLE_PACK,
        candidate_rows,
        registry,
    )

    assert rows[0]["validation_status"] == "accepted"
    assert rows[0]["blocking"] is False
    summary = {
        row["validation_status"]: row
        for row in public_source_model_input_candidate_validation_summary_rows(rows)
    }
    assert summary["accepted"]["rows"] == 1


def test_model_input_candidate_validation_blocks_bad_candidate_rows(
    tmp_path: Path,
) -> None:
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
        ],
    )
    candidate_rows = [
        {
            "player_id": "p_achane",
            "position": "WR",
            "feature_name": "lve_projection_value",
            "normalized_score": "91",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_not_real",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "91",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "not_active",
            "normalized_score": "91",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_chase_brown",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "many",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
    ]

    rows = public_source_model_input_candidate_validation_rows(
        SAMPLE_PACK,
        candidate_rows,
        registry,
    )

    assert {row["validation_status"] for row in rows} == {"blocked"}
    assert all(row["blocking"] is True for row in rows)


def test_model_input_candidate_validation_flags_duplicates_and_provenance_review(
    tmp_path: Path,
) -> None:
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )
    candidate_rows = [
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "91",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "92",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "age_curve",
            "normalized_score": "88",
            "source_key": "",
            "source_confidence": "",
            "is_missing": "false",
            "is_user_override": "false",
        },
    ]

    rows = public_source_model_input_candidate_validation_rows(
        SAMPLE_PACK,
        candidate_rows,
        registry,
    )
    by_feature = {}
    for row in rows:
        by_feature.setdefault(row["feature_name"], set()).add(row["validation_status"])

    assert by_feature["lve_projection_value"] == {"blocked"}
    assert by_feature["age_curve"] == {"review"}


def test_model_input_candidate_coverage_marks_complete_partial_and_empty(
    tmp_path: Path,
) -> None:
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )
    candidate_rows = [
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "91",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "age_curve",
            "normalized_score": "88",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_chase_brown",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "80",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
    ]
    validation_rows = public_source_model_input_candidate_validation_rows(
        SAMPLE_PACK,
        candidate_rows,
        registry,
    )

    rows = public_source_model_input_candidate_coverage_rows(
        SAMPLE_PACK,
        candidate_rows,
        validation_rows,
        registry,
    )
    by_player = {row["player_id"]: row for row in rows}

    assert by_player["p_achane"]["coverage_status"] == "complete"
    assert by_player["p_achane"]["coverage_pct"] == 100.0
    assert by_player["p_chase_brown"]["coverage_status"] == "partial"
    assert by_player["p_david_montgomery"]["coverage_status"] == "empty"
    summary = {
        row["coverage_status"]: row
        for row in public_source_model_input_candidate_coverage_summary_rows(rows)
    }
    assert summary["complete"]["players"] == 1
    assert summary["partial"]["players"] >= 1
    assert summary["empty"]["players"] >= 1


def test_model_input_candidate_coverage_ignores_review_and_blocked_rows(
    tmp_path: Path,
) -> None:
    registry = _write_registry(
        tmp_path,
        [
            {
                "position": "RB",
                "feature_name": "lve_projection_value",
                "requires_source_type": "projection",
                "scoring_status": "active_v1",
            },
            {
                "position": "RB",
                "feature_name": "age_curve",
                "requires_source_type": "manual_note",
                "scoring_status": "active_v1",
            },
        ],
    )
    candidate_rows = [
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "lve_projection_value",
            "normalized_score": "91",
            "source_key": "public_source_backfill_candidate",
            "source_confidence": "derived",
            "is_missing": "false",
            "is_user_override": "false",
        },
        {
            "player_id": "p_achane",
            "position": "RB",
            "feature_name": "age_curve",
            "normalized_score": "88",
            "source_key": "",
            "source_confidence": "",
            "is_missing": "false",
            "is_user_override": "false",
        },
    ]
    validation_rows = public_source_model_input_candidate_validation_rows(
        SAMPLE_PACK,
        candidate_rows,
        registry,
    )

    rows = public_source_model_input_candidate_coverage_rows(
        SAMPLE_PACK,
        candidate_rows,
        validation_rows,
        registry,
    )
    achane = next(row for row in rows if row["player_id"] == "p_achane")

    assert achane["accepted_features"] == 1
    assert achane["required_features"] == 2
    assert achane["coverage_status"] == "partial"
    assert achane["missing_features"] == "age_curve"


def test_model_preview_creates_isolated_outputs_for_complete_players(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_complete_rb_backfill(source_root, "p_achane", "De'Von Achane")
    preview_root = tmp_path / "previews"

    result = create_public_source_model_preview(
        SAMPLE_PACK,
        source_root,
        DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
        preview_root,
        preview_id="Achane Preview",
        created_at_utc=datetime(2026, 8, 2, 9, 0, tzinfo=UTC),
    )

    assert result.created is True
    assert result.output_path is not None
    assert result.manifest_path is not None
    assert result.model_input_path is not None
    output_rows = list(csv.DictReader(result.output_path.open(encoding="utf-8")))
    assert [row["player_id"] for row in output_rows] == ["p_achane"]
    assert result.model_input_path.parent == result.preview_path
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["complete_player_count"] == 1
    assert "no live model inputs" in manifest["scoring_effect"]
    snapshot_rows = public_source_model_preview_snapshot_rows(preview_root)
    assert snapshot_rows[0]["preview_id"] == "achane_preview"


def test_model_preview_refuses_duplicate_preview_id(tmp_path: Path) -> None:
    source_root = _copy_templates(tmp_path)
    _write_complete_rb_backfill(source_root, "p_achane", "De'Von Achane")
    preview_root = tmp_path / "previews"

    first = create_public_source_model_preview(
        SAMPLE_PACK,
        source_root,
        DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
        preview_root,
        preview_id="same_preview",
    )
    second = create_public_source_model_preview(
        SAMPLE_PACK,
        source_root,
        DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
        preview_root,
        preview_id="same_preview",
    )

    assert first.created is True
    assert second.created is False
    assert second.status == "blocked"


def test_model_preview_blocks_when_no_player_has_complete_coverage(
    tmp_path: Path,
) -> None:
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "normalized_veteran_feature_backfill.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["normalized_veteran_feature_backfill.csv"],
        [
            {
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "team": "MIA",
                "season": "2026",
                "asof_date": "2026-08-01",
                "lve_projection_value": "91",
                "overall_feature_confidence": "85",
                "manual_review_required": "false",
            }
        ],
    )

    result = create_public_source_model_preview(
        SAMPLE_PACK,
        source_root,
        DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
        tmp_path / "previews",
        preview_id="partial_only",
    )

    assert result.created is False
    assert result.status == "blocked"
    assert not result.preview_path.exists()


def test_model_preview_review_gate_classifies_preview_outputs(
    tmp_path: Path,
) -> None:
    preview_root = tmp_path / "previews"
    ready_dir = preview_root / "ready_preview"
    ready_dir.mkdir(parents=True)
    _write_preview_manifest(ready_dir, "ready_preview", schema_warning_count=0)
    _write_preview_output(
        ready_dir,
        [
            {
                "player_id": "p_ready",
                "player_name": "Ready Player",
                "position": "WR",
                "keeper_score": "86",
                "drop_candidate_score": "14",
                "confidence_score": "88",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
            },
            {
                "player_id": "p_review",
                "player_name": "Review Player",
                "position": "RB",
                "keeper_score": "72",
                "drop_candidate_score": "38",
                "confidence_score": "74",
                "warning_status": "data_warning",
                "risk_level": "medium",
                "missing_data_penalty": "2",
            },
            {
                "player_id": "p_blocked",
                "player_name": "Blocked Player",
                "position": "TE",
                "keeper_score": "50",
                "drop_candidate_score": "70",
                "confidence_score": "58",
                "warning_status": "blocking",
                "risk_level": "high",
                "missing_data_penalty": "7",
            },
        ],
    )

    rows = public_source_model_preview_review_rows(preview_root)
    by_player = {row["player_id"]: row for row in rows}

    assert by_player["p_ready"]["preview_review_status"] == "ready"
    assert by_player["p_review"]["preview_review_status"] == "review"
    assert by_player["p_blocked"]["preview_review_status"] == "blocked"
    summary = {
        row["preview_review_status"]: row
        for row in public_source_model_preview_review_summary_rows(rows)
    }
    assert summary["ready"]["rows"] == 1
    assert summary["review"]["rows"] == 1
    assert summary["blocked"]["rows"] == 1


def test_model_preview_review_gate_blocks_missing_output(tmp_path: Path) -> None:
    preview_root = tmp_path / "previews"
    preview_dir = preview_root / "broken_preview"
    preview_dir.mkdir(parents=True)
    _write_preview_manifest(preview_dir, "broken_preview", schema_warning_count=0)

    rows = public_source_model_preview_review_rows(preview_root)

    assert rows[0]["preview_review_status"] == "blocked"
    assert rows[0]["blocking"] is True
    assert rows[0]["warning_status"] == "missing_output"


def test_model_preview_comparison_marks_ready_review_and_blocked(
    tmp_path: Path,
) -> None:
    preview_root = tmp_path / "previews"
    preview_dir = preview_root / "comparison_preview"
    preview_dir.mkdir(parents=True)
    _write_preview_manifest(preview_dir, "comparison_preview", schema_warning_count=0)
    _write_preview_output(
        preview_dir,
        [
            {
                "player_id": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "keeper_score": "95",
                "drop_candidate_score": "8",
                "confidence_score": "88",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
            },
            {
                "player_id": "p_lamar",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "keeper_score": "70",
                "drop_candidate_score": "28",
                "confidence_score": "86",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
            },
            {
                "player_id": "p_unknown",
                "player_name": "Unknown Player",
                "position": "WR",
                "keeper_score": "70",
                "drop_candidate_score": "30",
                "confidence_score": "88",
                "warning_status": "blocking",
                "risk_level": "high",
                "missing_data_penalty": "8",
            },
        ],
    )

    rows = public_source_model_preview_comparison_rows(SAMPLE_PACK, preview_root)
    by_player = {row["player_id"]: row for row in rows}

    assert by_player["p_achane"]["comparison_status"] == "ready"
    assert by_player["p_achane"]["keeper_delta"] == "1.0"
    assert by_player["p_lamar"]["comparison_status"] == "review"
    assert by_player["p_lamar"]["keeper_delta"] == "-22.0"
    assert by_player["p_unknown"]["comparison_status"] == "blocked"
    summary = {
        row["comparison_status"]: row
        for row in public_source_model_preview_comparison_summary_rows(rows)
    }
    assert summary["ready"]["rows"] == 1
    assert summary["review"]["rows"] == 1
    assert summary["blocked"]["rows"] == 1


def test_model_preview_comparison_reviews_missing_live_baseline(
    tmp_path: Path,
) -> None:
    preview_root = tmp_path / "previews"
    preview_dir = preview_root / "missing_live_preview"
    preview_dir.mkdir(parents=True)
    _write_preview_manifest(preview_dir, "missing_live_preview", schema_warning_count=0)
    _write_preview_output(
        preview_dir,
        [
            {
                "player_id": "p_not_live",
                "player_name": "Not Live",
                "position": "WR",
                "keeper_score": "78",
                "drop_candidate_score": "20",
                "confidence_score": "82",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
            }
        ],
    )

    rows = public_source_model_preview_comparison_rows(SAMPLE_PACK, preview_root)

    assert rows[0]["comparison_status"] == "review"
    assert "No current live model output" in rows[0]["reason"]


def test_model_promotion_candidate_exports_ready_rows_only(
    tmp_path: Path,
) -> None:
    preview_root = tmp_path / "previews"
    preview_dir = preview_root / "promotion_preview"
    preview_dir.mkdir(parents=True)
    _write_preview_manifest(preview_dir, "promotion_preview", schema_warning_count=0)
    _write_preview_output(
        preview_dir,
        [
            {
                "snapshot_date": "2026-08-01",
                "player_id": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "private_score": "95",
                "market_score": "88",
                "war_score": "93",
                "keeper_score": "95",
                "drop_candidate_score": "8",
                "confidence_score": "88",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
                "recommendation": "keep",
            },
            {
                "snapshot_date": "2026-08-01",
                "player_id": "p_lamar",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "private_score": "70",
                "market_score": "70",
                "war_score": "70",
                "keeper_score": "70",
                "drop_candidate_score": "28",
                "confidence_score": "86",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
                "recommendation": "keep",
            },
        ],
    )
    promotion_root = tmp_path / "promotions"

    result = create_public_source_model_promotion_candidate(
        SAMPLE_PACK,
        preview_root,
        promotion_root,
        promotion_id="Ready Only",
        created_at_utc=datetime(2026, 8, 3, 10, 0, tzinfo=UTC),
    )

    assert result.created is True
    assert result.csv_path is not None
    rows = list(csv.DictReader(result.csv_path.open(encoding="utf-8")))
    assert [row["player_id"] for row in rows] == ["p_achane"]
    assert rows[0]["promotion_source_preview_id"] == "promotion_preview"
    assert rows[0]["promotion_status"] == "candidate"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["row_count"] == 1
    assert "not changed" in manifest["scoring_effect"]
    snapshots = public_source_model_promotion_candidate_snapshot_rows(promotion_root)
    assert snapshots[0]["promotion_id"] == "ready_only"


def test_model_promotion_candidate_blocks_when_no_ready_rows(
    tmp_path: Path,
) -> None:
    preview_root = tmp_path / "previews"
    preview_dir = preview_root / "review_only_preview"
    preview_dir.mkdir(parents=True)
    _write_preview_manifest(preview_dir, "review_only_preview", schema_warning_count=0)
    _write_preview_output(
        preview_dir,
        [
            {
                "player_id": "p_lamar",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "keeper_score": "70",
                "drop_candidate_score": "28",
                "confidence_score": "86",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
            }
        ],
    )

    result = create_public_source_model_promotion_candidate(
        SAMPLE_PACK,
        preview_root,
        tmp_path / "promotions",
        promotion_id="blocked",
    )

    assert result.created is False
    assert result.status == "blocked"
    assert not result.promotion_path.exists()


def test_model_promotion_candidate_review_gate_classifies_rows(
    tmp_path: Path,
) -> None:
    promotion_root = tmp_path / "promotions"
    promotion_dir = promotion_root / "candidate_review"
    promotion_dir.mkdir(parents=True)
    _write_promotion_manifest(promotion_dir, "candidate_review")
    _write_promotion_output(
        promotion_dir,
        [
            {
                "player_id": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "keeper_score": "95",
                "drop_candidate_score": "8",
                "confidence_score": "88",
                "promotion_source_preview_id": "preview_a",
                "promotion_status": "candidate",
            },
            {
                "player_id": "p_lamar",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "keeper_score": "70",
                "drop_candidate_score": "28",
                "confidence_score": "86",
                "promotion_source_preview_id": "preview_a",
                "promotion_status": "candidate",
            },
            {
                "player_id": "p_broken",
                "player_name": "Broken",
                "position": "WR",
                "keeper_score": "70",
                "drop_candidate_score": "20",
                "confidence_score": "88",
                "promotion_source_preview_id": "",
                "promotion_status": "candidate",
            },
        ],
    )

    rows = public_source_model_promotion_candidate_review_rows(
        SAMPLE_PACK,
        promotion_root,
    )
    by_player = {row["player_id"]: row for row in rows}

    assert by_player["p_achane"]["promotion_review_status"] == "ready"
    assert by_player["p_lamar"]["promotion_review_status"] == "review"
    assert by_player["p_broken"]["promotion_review_status"] == "blocked"
    summary = {
        row["promotion_review_status"]: row
        for row in public_source_model_promotion_candidate_review_summary_rows(rows)
    }
    assert summary["ready"]["rows"] == 1
    assert summary["review"]["rows"] == 1
    assert summary["blocked"]["rows"] == 1


def test_model_promotion_candidate_review_gate_blocks_missing_csv(
    tmp_path: Path,
) -> None:
    promotion_root = tmp_path / "promotions"
    promotion_dir = promotion_root / "missing_csv"
    promotion_dir.mkdir(parents=True)
    _write_promotion_manifest(promotion_dir, "missing_csv")

    rows = public_source_model_promotion_candidate_review_rows(
        SAMPLE_PACK,
        promotion_root,
    )

    assert rows[0]["promotion_review_status"] == "blocked"
    assert rows[0]["blocking"] is True
    assert "CSV is missing" in rows[0]["reason"]


def test_model_applied_pack_writes_new_pack_copy_only(tmp_path: Path) -> None:
    promotion_root = tmp_path / "promotions"
    promotion_dir = promotion_root / "ready_candidate"
    promotion_dir.mkdir(parents=True)
    _write_promotion_manifest(promotion_dir, "ready_candidate")
    _write_promotion_output(
        promotion_dir,
        [
            {
                "player_id": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "keeper_score": "95",
                "drop_candidate_score": "8",
                "confidence_score": "88",
                "promotion_source_preview_id": "preview_a",
                "promotion_status": "candidate",
            }
        ],
    )
    output_root = tmp_path / "data_packs"

    result = create_public_source_model_applied_pack(
        SAMPLE_PACK,
        promotion_root,
        output_root,
        applied_pack_id="Applied Pack",
        created_at_utc=datetime(2026, 8, 4, 11, 0, tzinfo=UTC),
    )

    assert result.created is True
    applied_outputs = _read_model_output_rows(result.applied_pack_path)
    source_outputs = _read_model_output_rows(SAMPLE_PACK)
    assert applied_outputs["p_achane"]["keeper_score"] == "95"
    assert source_outputs["p_achane"]["keeper_score"] == "94"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["applied_row_count"] == 1
    assert "selected source pack was not changed" in manifest["scoring_effect"]
    snapshots = public_source_model_applied_pack_snapshot_rows(output_root)
    assert snapshots[0]["applied_pack_id"] == "applied_pack"


def test_model_applied_pack_blocks_duplicate_ready_candidates(
    tmp_path: Path,
) -> None:
    promotion_root = tmp_path / "promotions"
    first = promotion_root / "ready_one"
    second = promotion_root / "ready_two"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    _write_promotion_manifest(first, "ready_one")
    _write_promotion_manifest(second, "ready_two")
    for directory in (first, second):
        _write_promotion_output(
            directory,
            [
                {
                    "player_id": "p_achane",
                    "player_name": "De'Von Achane",
                    "position": "RB",
                    "keeper_score": "95",
                    "drop_candidate_score": "8",
                    "confidence_score": "88",
                    "promotion_source_preview_id": "preview_a",
                    "promotion_status": "candidate",
                }
            ],
        )

    result = create_public_source_model_applied_pack(
        SAMPLE_PACK,
        promotion_root,
        tmp_path / "data_packs",
        applied_pack_id="blocked_duplicates",
    )

    assert result.created is False
    assert result.status == "blocked"
    assert not result.applied_pack_path.exists()


def test_model_applied_pack_blocks_when_no_ready_candidates(tmp_path: Path) -> None:
    promotion_root = tmp_path / "promotions"

    result = create_public_source_model_applied_pack(
        SAMPLE_PACK,
        promotion_root,
        tmp_path / "data_packs",
        applied_pack_id="empty",
    )

    assert result.created is False
    assert result.status == "blocked"


def test_model_applied_pack_review_gate_marks_review_and_blocked(
    tmp_path: Path,
) -> None:
    promotion_root = tmp_path / "promotions"
    promotion_dir = promotion_root / "ready_candidate"
    promotion_dir.mkdir(parents=True)
    _write_promotion_manifest(promotion_dir, "ready_candidate")
    _write_promotion_output(
        promotion_dir,
        [
            {
                "player_id": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "keeper_score": "95",
                "drop_candidate_score": "8",
                "confidence_score": "88",
                "promotion_source_preview_id": "preview_one",
                "promotion_status": "candidate",
            }
        ],
    )
    output_root = tmp_path / "data_packs"

    applied_result = create_public_source_model_applied_pack(
        SAMPLE_PACK,
        promotion_root,
        output_root,
        applied_pack_id="review_pack",
    )
    blocked_pack = output_root / "blocked_pack"
    blocked_pack.mkdir(parents=True)
    _write_applied_pack_manifest(
        blocked_pack,
        "blocked_pack",
        applied_row_count=1,
    )

    assert applied_result.created is True
    _append_duplicate_roster_row(applied_result.applied_pack_path)

    rows = public_source_model_applied_pack_review_rows(output_root)
    statuses = {
        str(row["applied_pack_id"]): row["applied_pack_review_status"]
        for row in rows
    }
    summary = {
        str(row["applied_pack_review_status"]): row["rows"]
        for row in public_source_model_applied_pack_review_summary_rows(rows)
    }

    assert statuses["review_pack"] == "review"
    assert statuses["blocked_pack"] == "blocked"
    assert summary["review"] == 1
    assert summary["blocked"] == 1


def test_model_applied_pack_review_gate_blocks_zero_applied_rows(
    tmp_path: Path,
) -> None:
    pack = tmp_path / "zero_applied_pack"
    shutil.copytree(SAMPLE_PACK, pack)
    _write_applied_pack_manifest(
        pack,
        "zero_applied_pack",
        applied_row_count=0,
    )

    rows = public_source_model_applied_pack_review_rows(tmp_path)

    assert rows[0]["applied_pack_review_status"] == "blocked"
    assert "zero applied model rows" in str(rows[0]["reason"])


def test_unscored_report_marks_real_pack_placeholders_and_missing_features(
    tmp_path: Path,
) -> None:
    pack = _copy_sample_pack_with_placeholder(tmp_path)
    backfill = pack.parent / "backfill.csv"
    _write_rows(
        backfill,
        (
            "season",
            "snapshot_date",
            "player_id",
            "position",
            "feature_name",
            "is_missing",
        ),
        [
            {
                "season": "2026",
                "snapshot_date": "2026-08-01",
                "player_id": "p_achane",
                "position": "RB",
                "feature_name": "lve_projection_value",
                "is_missing": "true",
            }
        ],
    )
    rows = build_unscored_player_rows(pack, backfill)
    by_name = {row["player_name"]: row for row in rows}

    assert by_name["De'Von Achane"]["model_output_status"] == "placeholder"
    assert by_name["De'Von Achane"]["missing_feature_rows"] == 1
    assert "Collect sources" in by_name["De'Von Achane"]["next_action"]


def test_public_source_readiness_explains_source_to_score_steps(
    tmp_path: Path,
) -> None:
    pack = _copy_sample_pack_with_placeholder(tmp_path)
    source_root = _copy_templates(tmp_path)
    _write_rows(
        source_root / "player_projection_inputs.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["player_projection_inputs.csv"],
        [
            {
                "projection_source_id": "projection_test",
                "season": "2026",
                "player_key": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "proj_fantasy_points_source": "180",
            }
        ],
    )
    report = validate_public_source_inputs(source_root)
    matches = build_public_source_match_rows(pack, source_root)
    unscored = build_unscored_player_rows(pack)

    rows = public_source_readiness_rows(
        report,
        matches,
        unscored,
        tmp_path / "candidates",
        tmp_path / "previews",
        tmp_path / "promotions",
        tmp_path / "applied",
        data_pack_path=pack,
    )
    by_step = {row["step"]: row for row in rows}

    assert by_step["1. Collect raw source exports"]["status"] == "ready"
    assert by_step["2. Match sources to rostered players"]["status"] == "ready"
    assert by_step["4. Generate real model outputs"]["status"] == "blocked"
    assert "Do not use" in by_step["4. Generate real model outputs"]["next_action"]


def test_public_source_readiness_includes_review_pipeline_artifacts(
    tmp_path: Path,
) -> None:
    pack = _copy_sample_pack_with_placeholder(tmp_path)
    source_root = _copy_templates(tmp_path)
    report = validate_public_source_inputs(source_root)
    matches = build_public_source_match_rows(pack, source_root)
    unscored = build_unscored_player_rows(pack)
    candidate_root = tmp_path / "candidates"
    candidate_dir = candidate_root / "candidate_a"
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "model_input_candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidate_id": "candidate_a",
                "created_at_utc": "2026-08-01T12:00:00+00:00",
                "row_count": 3,
                "player_count": 1,
                "feature_count": 3,
                "live_mutation": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    preview_root = tmp_path / "previews"
    preview_dir = preview_root / "preview_a"
    preview_dir.mkdir(parents=True)
    _write_preview_manifest(
        preview_dir,
        "preview_a",
        schema_warning_count=0,
        output_row_count=1,
    )
    _write_preview_output(
        preview_dir,
        [
            {
                "player_id": "p_achane",
                "player_name": "De'Von Achane",
                "position": "RB",
                "keeper_score": "95",
                "drop_candidate_score": "8",
                "confidence_score": "88",
                "warning_status": "ready",
                "risk_level": "low",
                "missing_data_penalty": "0",
            }
        ],
    )

    rows = public_source_readiness_rows(
        report,
        matches,
        unscored,
        candidate_root,
        preview_root,
        tmp_path / "promotions",
        tmp_path / "applied",
        data_pack_path=pack,
    )
    by_step = {row["step"]: row for row in rows}

    assert by_step["5. Export accepted model-input candidates"]["status"] == "ready"
    assert "3 candidate rows" in by_step["5. Export accepted model-input candidates"]["detail"]
    assert by_step["6. Run isolated model preview"]["status"] == "ready"
    assert by_step["7. Review preview and compare to live"]["status"] == "ready"
    assert "live comparison" in by_step["7. Review preview and compare to live"]["detail"]
    assert by_step["8. Export promotion candidates"]["status"] == "needed"
    assert by_step["9. Apply to generated pack copy"]["status"] == "needed"


def _copy_templates(tmp_path: Path) -> Path:
    target = tmp_path / "public_sources"
    shutil.copytree(TEMPLATE_ROOT, target)
    return target


def _copy_sample_pack_with_placeholder(tmp_path: Path) -> Path:
    target = tmp_path / "placeholder_pack"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SAMPLE_PACK, target)
    model_path = target / "model_outputs.csv"
    with model_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        header = rows[0].keys()
    rows[0]["risk_level"] = "needs_model"
    rows[0]["notes"] = "Neutral placeholder generated from refreshed Sleeper data."
    _write_rows(model_path, tuple(header), rows)
    return target


def _copy_sample_pack_with_extra_player(
    tmp_path: Path,
    player_row: dict[str, str],
) -> Path:
    target = tmp_path / "extra_player_pack"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SAMPLE_PACK, target)
    players_path = target / "dim_players.csv"
    with players_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        header = tuple(rows[0].keys())
    rows.append({column: player_row.get(column, "") for column in header})
    _write_rows(players_path, header, rows)
    return target


def _write_complete_rb_backfill(
    source_root: Path,
    player_id: str,
    player_name: str,
) -> None:
    _write_rows(
        source_root / "normalized_veteran_feature_backfill.csv",
        PUBLIC_SOURCE_TEMPLATE_HEADERS["normalized_veteran_feature_backfill.csv"],
        [
            {
                "player_key": player_id,
                "player_name": player_name,
                "position": "RB",
                "team": "MIA",
                "season": "2026",
                "asof_date": "2026-08-01",
                "lve_projection_value": "91",
                "role_security": "88",
                "age_curve": "87",
                "first_down_td_fit": "84",
                "injury_durability": "80",
                "overall_feature_confidence": "85",
                "manual_review_required": "false",
            }
        ],
    )


def _write_preview_manifest(
    preview_dir: Path,
    preview_id: str,
    *,
    schema_warning_count: int,
    output_row_count: int = 0,
) -> None:
    (preview_dir / "model_preview_manifest.json").write_text(
        json.dumps(
            {
                "preview_id": preview_id,
                "output_file": "veteran_model_preview_outputs.csv",
                "output_row_count": output_row_count,
                "schema_warning_count": schema_warning_count,
                "scoring_effect": "isolated preview only",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_preview_output(
    preview_dir: Path,
    rows: list[dict[str, str]],
) -> None:
    header = (
        "player_id",
        "player_name",
        "position",
        "keeper_score",
        "drop_candidate_score",
        "confidence_score",
        "warning_status",
        "risk_level",
        "missing_data_penalty",
    )
    _write_rows(preview_dir / "veteran_model_preview_outputs.csv", header, rows)


def _write_promotion_manifest(promotion_dir: Path, promotion_id: str) -> None:
    (promotion_dir / "model_promotion_candidate_manifest.json").write_text(
        json.dumps(
            {
                "promotion_id": promotion_id,
                "csv_file": "model_outputs_promotion_candidate.csv",
                "scoring_effect": "promotion candidate only",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_promotion_output(
    promotion_dir: Path,
    rows: list[dict[str, str]],
) -> None:
    header = (
        "player_id",
        "player_name",
        "position",
        "keeper_score",
        "drop_candidate_score",
        "confidence_score",
        "promotion_source_preview_id",
        "promotion_status",
    )
    _write_rows(promotion_dir / "model_outputs_promotion_candidate.csv", header, rows)


def _write_applied_pack_manifest(
    pack_dir: Path,
    applied_pack_id: str,
    *,
    applied_row_count: int,
) -> None:
    (pack_dir / "model_applied_pack_manifest.json").write_text(
        json.dumps(
            {
                "applied_pack_id": applied_pack_id,
                "applied_row_count": applied_row_count,
                "promotion_candidate_count": applied_row_count,
                "validation_error_count": 0,
                "validation_warning_count": 0,
                "scoring_effect": (
                    "generated pack admission only; selected source pack "
                    "was not changed"
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _read_model_output_rows(data_pack_path: Path) -> dict[str, dict[str, str]]:
    with (data_pack_path / "model_outputs.csv").open(
        newline="",
        encoding="utf-8",
    ) as handle:
        return {row["player_id"]: row for row in csv.DictReader(handle)}


def _append_duplicate_roster_row(data_pack_path: Path) -> None:
    roster_path = data_pack_path / "fact_rosters.csv"
    with roster_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        header = tuple(rows[0].keys())
    rows.append(dict(rows[0]))
    _write_rows(roster_path, header, rows)


def _write_registry(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    path = tmp_path / "veteran_feature_registry.csv"
    _write_rows(
        path,
        (
            "position",
            "feature_name",
            "requires_source_type",
            "scoring_status",
        ),
        rows,
    )
    return path


def _write_rows(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
