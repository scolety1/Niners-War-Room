from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.model_v4_app_review_service import (
    MODEL_V4_OLD_VS_V4_BANNER,
    MODEL_V4_OLD_VS_V4_COLUMNS,
    MODEL_V4_OLD_VS_V4_LABELS,
    MODEL_V4_PREVIEW_RANKING_COLUMNS,
    MODEL_V4_PREVIEW_RANKING_LABELS,
    MODEL_V4_PREVIEW_REVIEW_ONLY_LABEL,
    MODEL_V4_PROMOTION_BLOCKER_COLUMNS,
    MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS,
    MODEL_V4_PROMOTION_BLOCKERS_BANNER,
    MODEL_V4_RECEIPT_DRILLDOWN_COLUMNS,
    MODEL_V4_RECEIPT_SECTION_LABELS,
    MODEL_V4_SHADOW_MY_TEAM_BANNER,
    MODEL_V4_SHADOW_MY_TEAM_COLUMNS,
    MODEL_V4_SHADOW_MY_TEAM_LABELS,
    MODEL_V4_SHADOW_WAR_BOARD_BANNER,
    MODEL_V4_SHADOW_WAR_BOARD_COLUMNS,
    MODEL_V4_SHADOW_WAR_BOARD_LABELS,
    MODEL_V4_SOURCE_GAP_CATEGORY_LABELS,
    build_model_v4_app_review,
    build_model_v4_audit_summary_rows,
    build_model_v4_named_player_audit_rows,
    build_model_v4_old_vs_v4_comparison_rows,
    build_model_v4_promotion_blocker_rows,
    build_model_v4_promotion_blocker_summary_rows,
    build_model_v4_receipt_drilldown_rows,
    build_model_v4_receipt_reconciliation_row,
    build_model_v4_sanity_fixture_audit_rows,
    build_model_v4_shadow_my_team_rows,
    build_model_v4_shadow_war_board_rows,
    build_model_v4_source_gap_rows,
    build_model_v4_source_gap_summary_rows,
)
from src.services.model_v4_roster_rank_contract_service import OfficialRosterRankRow


def test_model_v4_app_review_loads_review_only_preview(tmp_path: Path) -> None:
    root = tmp_path / "review_only_latest"
    root.mkdir()
    _write_summary(root, active_rankings_overwritten=False)
    _write_csv(
        root / "v4_preview_outputs.csv",
        ["player", "position", "dynasty_asset_value", "confidence_label"],
        [
            {
                "player": "Player B",
                "position": "RB",
                "dynasty_asset_value": "70",
                "confidence_label": "usable",
            },
            {
                "player": "Player A",
                "position": "WR",
                "dynasty_asset_value": "80",
                "confidence_label": "usable",
            },
        ],
    )
    _write_csv(
        root / "v4_normalized_component_rows.csv",
        ["player", "component", "source_status"],
        [
            {
                "player": "Player A",
                "component": "production",
                "source_status": "imported_real_data",
            }
        ],
    )
    _write_csv(
        root / "v4_receipt_rows.csv",
        ["player", "component", "contribution"],
        [{"player": "Player A", "component": "production", "contribution": "12"}],
    )
    _write_csv(
        root / "v4_source_coverage_rows.csv",
        ["player", "section", "coverage_status"],
        [{"player": "Player A", "section": "production", "coverage_status": "covered"}],
    )
    _write_csv(
        root / "v4_warning_rows.csv",
        ["player", "warning"],
        [{"player": "Player A", "warning": "review_only"}],
    )
    sanity_path = tmp_path / "sanity.csv"
    _write_csv(
        sanity_path,
        ["fixture_id", "status", "fixture_name"],
        [
            {"fixture_id": "ok", "status": "ready", "fixture_name": "Ready"},
            {"fixture_id": "review", "status": "review", "fixture_name": "Review"},
        ],
    )
    named_path = tmp_path / "named.csv"
    _write_csv(
        named_path,
        ["requested_player", "match_status"],
        [{"requested_player": "Player A", "match_status": "matched"}],
    )

    report = build_model_v4_app_review(root, sanity_path, named_path)

    assert report.issues == []
    assert report.summary_rows[0]["preview_status"] == "review_only"
    assert {row["status"] for row in report.gate_rows} == {"ready"}
    assert report.preview_rows[0]["player"] == "Player A"
    assert report.preview_rows[0]["overall_preview_rank"] == 1
    assert report.preview_rows[0]["position_preview_rank"] == "WR1"
    assert report.preview_rows[1]["position_preview_rank"] == "RB1"
    assert report.sanity_fixture_rows[0]["fixture_id"] == "review"
    assert report.sanity_fixture_rows[0]["audit_status"] == "review"
    assert report.sanity_fixture_summary_rows[0]["review_count"] == 1
    assert report.sanity_fixture_summary_rows[0]["ready_count"] == 1
    assert report.sanity_fixture_summary_rows[0]["decision_ready_unlocked"] is False
    assert report.named_player_summary_rows[0]["ready_count"] == 1
    assert report.named_player_summary_rows[0]["decision_ready_unlocked"] is False
    assert report.source_gap_detail_rows[0]["gap_labels"] == "Covered Evidence"


def test_model_v4_app_review_blocks_if_preview_claims_active_overwrite(
    tmp_path: Path,
) -> None:
    root = tmp_path / "review_only_latest"
    root.mkdir()
    _write_summary(root, active_rankings_overwritten=True)
    for name in (
        "v4_preview_outputs.csv",
        "v4_normalized_component_rows.csv",
        "v4_receipt_rows.csv",
        "v4_source_coverage_rows.csv",
        "v4_warning_rows.csv",
    ):
        _write_csv(root / name, ["player"], [])
    sanity_path = tmp_path / "sanity.csv"
    named_path = tmp_path / "named.csv"
    _write_csv(sanity_path, ["fixture_id", "status"], [])
    _write_csv(named_path, ["requested_player", "match_status"], [])

    report = build_model_v4_app_review(root, sanity_path, named_path)

    gate_status_by_field = {
        row["summary_field"]: row["status"] for row in report.gate_rows
    }
    assert gate_status_by_field["active_rankings_overwritten"] == "blocked"
    assert gate_status_by_field["decision_ready_unlocked"] == "ready"


def test_model_v4_preview_ranking_labels_are_plain_review_labels() -> None:
    assert MODEL_V4_PREVIEW_REVIEW_ONLY_LABEL == (
        "Review-only v4 preview. Not active rankings."
    )
    assert MODEL_V4_PREVIEW_RANKING_COLUMNS == (
        "overall_preview_rank",
        "position_preview_rank",
        "player",
        "position",
        "nfl_team",
        "lifecycle",
        "dynasty_asset_value",
        "confidence_label",
        "review_warnings",
        "unavailable_sections",
    )
    assert MODEL_V4_PREVIEW_RANKING_LABELS["overall_preview_rank"] == (
        "Overall Preview Rank"
    )
    assert MODEL_V4_PREVIEW_RANKING_LABELS["dynasty_asset_value"] == (
        "Dynasty Asset Value"
    )
    assert MODEL_V4_PREVIEW_RANKING_LABELS["review_warnings"] == "Review Warnings"


def test_model_v4_shadow_war_board_rows_do_not_overwrite_active_war_board() -> None:
    active_war_board_rows = [
        {
            "overall_rank": 1,
            "position_rank_label": "RB1",
            "player": "Active Player",
            "action": "keep",
            "stats_value": 99.0,
        }
    ]
    original_active_rows = [dict(row) for row in active_war_board_rows]
    preview_rows = [
        {
            "overall_preview_rank": 2,
            "position_preview_rank": "WR1",
            "player": "Player B",
            "position": "WR",
            "nfl_team": "SEA",
            "lifecycle": "established_veteran",
            "dynasty_asset_value": "71",
            "confidence_label": "review",
            "review_warnings": "route_data_unavailable",
            "unavailable_sections": "route_participation",
            "overall_rank": 1,
            "action": "drop",
            "stats_value": "999",
        },
        {
            "overall_preview_rank": 1,
            "position_preview_rank": "RB1",
            "player": "Player A",
            "position": "RB",
            "nfl_team": "ATL",
            "lifecycle": "year_three_nfl_bridge",
            "dynasty_asset_value": "76",
            "confidence_label": "review",
            "review_warnings": "",
            "unavailable_sections": "",
        },
    ]

    shadow_rows = build_model_v4_shadow_war_board_rows(preview_rows)

    assert active_war_board_rows == original_active_rows
    assert shadow_rows[0]["player"] == "Player A"
    assert set(shadow_rows[0]) == set(MODEL_V4_SHADOW_WAR_BOARD_COLUMNS)
    assert "overall_rank" not in shadow_rows[0]
    assert "action" not in shadow_rows[0]
    assert "stats_value" not in shadow_rows[0]
    assert MODEL_V4_SHADOW_WAR_BOARD_BANNER == (
        "V4 shadow board. Review-only. Active rankings are unchanged."
    )
    assert MODEL_V4_SHADOW_WAR_BOARD_LABELS["overall_preview_rank"] == (
        "V4 Overall Rank"
    )
    assert MODEL_V4_SHADOW_WAR_BOARD_LABELS["position_preview_rank"] == (
        "V4 Position Rank"
    )


def test_model_v4_shadow_my_team_rows_join_roster_context_without_active_labels() -> None:
    active_my_team_rows = [
        {
            "player": "Brian Thomas",
            "model_recommendation": "core",
            "stats_value": 99,
        }
    ]
    original_active_rows = [dict(row) for row in active_my_team_rows]
    roster_rows = [
        OfficialRosterRankRow(
            roster_team="Niners",
            roster_rank=1,
            player_name="Brian Thomas",
            position="WR",
            nfl_team="JAC",
            league_rank=66,
            source_title="Locked roster ranks",
            source_date="2026-03-31",
            ranking_source="FantasyPros",
        ),
        OfficialRosterRankRow(
            roster_team="Niners",
            roster_rank=2,
            player_name="Luther Burden",
            position="WR",
            nfl_team="CHI",
            league_rank=56,
            source_title="Locked roster ranks",
            source_date="2026-03-31",
            ranking_source="FantasyPros",
        ),
    ]
    preview_rows = [
        {
            "player": "Brian Thomas Jr.",
            "position": "WR",
            "nfl_team": "JAX",
            "dynasty_asset_value": "50.94",
            "confidence_label": "review",
            "review_warnings": "route_participation_unavailable",
            "unavailable_sections": "",
            "action": "keep",
            "stats_value": "100",
        }
    ]

    rows = build_model_v4_shadow_my_team_rows(
        roster_rows,
        preview_rows,
        top_five_names=("Brian Thomas",),
    )

    assert active_my_team_rows == original_active_rows
    assert rows[0]["player"] == "Brian Thomas"
    assert rows[0]["matched_v4_player"] == "Brian Thomas Jr."
    assert rows[0]["v4_match_status"] == "matched_v4_preview"
    assert rows[0]["top_five_rule_status"] == "Roster's League-Rank Top Five"
    assert rows[0]["v4_dynasty_asset_value"] == "50.94"
    assert rows[0]["v4_roster_decision_value"] == ""
    assert rows[1]["v4_match_status"] == "missing_v4_preview"
    assert set(MODEL_V4_SHADOW_MY_TEAM_COLUMNS).issubset(rows[0])
    assert "model_recommendation" not in rows[0]
    assert "action" not in rows[0]
    assert "stats_value" not in rows[0]
    assert MODEL_V4_SHADOW_MY_TEAM_BANNER == (
        "V4 shadow My Team. Review-only. Active My Team is unchanged."
    )
    assert MODEL_V4_SHADOW_MY_TEAM_LABELS["v4_dynasty_asset_value"] == (
        "V4 Dynasty Asset Value"
    )


def test_model_v4_old_vs_v4_comparison_rows_classify_movement() -> None:
    active_rows = [
        {
            "overall_rank": 20,
            "player": "Player A",
            "pos": "WR",
            "team": "Niners",
            "stats_value": "70.0",
            "confidence_label": "review",
            "warning_reason": "stale production source",
        },
        {
            "overall_rank": 8,
            "player": "Player B",
            "pos": "RB",
            "team": "Other",
            "stats_value": "80.0",
            "confidence_label": "usable",
            "warning_reason": "",
        },
    ]
    preview_rows = [
        {
            "overall_preview_rank": 8,
            "player": "Player A",
            "position": "WR",
            "nfl_team": "SEA",
            "dynasty_asset_value": "74.5",
            "confidence_label": "review",
            "review_warnings": "route_participation_unavailable",
            "unavailable_sections": "routes_run",
        },
        {
            "overall_preview_rank": 45,
            "player": "Player C",
            "position": "QB",
            "nfl_team": "BUF",
            "dynasty_asset_value": "41.0",
            "confidence_label": "review",
            "review_warnings": "one_qb_suppression_review_only",
            "unavailable_sections": "",
        },
    ]
    movement_rows = [
        {
            "player": "Player A",
            "movement_cause": "WR production/projection weighting patch",
        }
    ]

    rows = build_model_v4_old_vs_v4_comparison_rows(
        active_rows,
        preview_rows,
        movement_rows,
    )
    by_player = {row["player"]: row for row in rows}

    assert set(MODEL_V4_OLD_VS_V4_COLUMNS).issubset(by_player["Player A"])
    assert MODEL_V4_OLD_VS_V4_BANNER == (
        "Old vs V4 comparison. Review-only. Active rankings are unchanged."
    )
    assert MODEL_V4_OLD_VS_V4_LABELS["v4_shadow_rank"] == "V4 Shadow Rank"
    assert by_player["Player A"]["movement_direction"] == "up in v4"
    assert by_player["Player A"]["movement_size"] == "medium"
    assert by_player["Player A"]["movement_reason"] == "formula patch"
    assert by_player["Player A"]["in_niners_roster"] is True
    assert by_player["Player A"]["in_top_50"] is True
    assert by_player["Player A"]["large_unexplained_movement"] is False
    assert by_player["Player B"]["movement_direction"] == "missing from v4"
    assert by_player["Player C"]["movement_direction"] == "missing from active"
    assert by_player["Player C"]["movement_reason"] == "QB suppression"


def test_model_v4_old_vs_v4_flags_large_unknown_movement() -> None:
    rows = build_model_v4_old_vs_v4_comparison_rows(
        [
            {
                "overall_rank": 80,
                "player": "Quiet Player",
                "pos": "RB",
                "stats_value": "20",
                "confidence_label": "usable",
            }
        ],
        [
            {
                "overall_preview_rank": 20,
                "player": "Quiet Player",
                "position": "RB",
                "dynasty_asset_value": "70",
                "confidence_label": "usable",
                "review_warnings": "",
                "unavailable_sections": "",
            }
        ],
        [],
    )

    assert rows[0]["movement_size"] == "large"
    assert rows[0]["movement_reason"] == "unknown"
    assert rows[0]["large_unexplained_movement"] is True
    assert "review receipts" in rows[0]["movement_review_note"]


def test_model_v4_promotion_blockers_include_known_current_blockers() -> None:
    preview_rows = [
        {
            "player": "Luther Burden",
            "position": "WR",
            "nfl_team": "CHI",
            "lifecycle": "year_one_nfl_bridge",
            "confidence_label": "blocked",
            "review_warnings": (
                "missing_production_data|missing_usage_opportunity_data|"
                "route_participation_unavailable|projection_first_downs_estimated_from_history"
            ),
            "unavailable_sections": "production|usage_opportunity",
        },
        {
            "player": "Player Route",
            "position": "TE",
            "nfl_team": "LV",
            "lifecycle": "established_veteran",
            "confidence_label": "review",
            "review_warnings": "routes_run_unavailable|tprr_unavailable",
            "unavailable_sections": "routes_run",
        },
    ]
    source_gap_rows = [
        {
            "player": "Player Route",
            "component": "usage_opportunity",
            "gap_labels": "Route Data Unavailable",
            "warning": "route_data_unavailable_free_public",
        }
    ]
    sanity_rows = [
        {
            "fixture_id": "qb-control",
            "audit_status": "review",
            "classification": "formula issue",
        }
    ]
    named_rows = [
        {
            "requested_player": "Player Route",
            "audit_status": "ready",
            "classification": "receipt-backed ready row",
        }
    ]

    rows = build_model_v4_promotion_blocker_rows(
        preview_rows,
        source_gap_rows,
        sanity_rows,
        named_rows,
    )
    by_id = {str(row["blocker_id"]): row for row in rows}

    assert MODEL_V4_PROMOTION_BLOCKERS_BANNER == (
        "V4 promotion blockers. Review-only. No readiness gates are unlocked."
    )
    assert set(MODEL_V4_PROMOTION_BLOCKER_COLUMNS).issubset(rows[0])
    assert MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS["data_blocker"] == "Data Blocker"
    assert "caleb_williams_missing_qb_control" in by_id
    assert "source_limited_incoming_young_players" in by_id
    assert "unavailable_route_metrics" in by_id
    assert "open_formula_review_findings" in by_id
    assert "shadow_app_review_not_accepted" in by_id
    assert "roster_decision_gate_not_unlocked" in by_id
    assert "estimated_first_down_projection_limitation" in by_id
    assert by_id["caleb_williams_missing_qb_control"]["blocker_group"] == (
        "data_blocker"
    )
    assert by_id["unavailable_route_metrics"]["blocks_app_promotion"] is False
    assert by_id["unavailable_route_metrics"]["promotion_blocking_scope"] == (
        "Final decision-ready only"
    )
    assert by_id["shadow_app_review_not_accepted"]["blocks_app_promotion"] is True
    assert "Luther Burden" in str(
        by_id["source_limited_incoming_young_players"][
            "affected_players_surfaces"
        ]
    )


def test_model_v4_promotion_blocker_summary_includes_all_groups() -> None:
    rows = build_model_v4_promotion_blocker_rows(
        [
            {
                "player": "Veteran",
                "position": "WR",
                "lifecycle": "established_veteran",
                "review_warnings": "route_participation_unavailable",
                "unavailable_sections": "",
            }
        ],
        [],
        [],
        [],
    )

    summary = build_model_v4_promotion_blocker_summary_rows(rows)
    labels = {row["blocker_group_label"] for row in summary}

    assert labels == set(MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS.values())
    assert any(row["blocker_group"] == "formula_blocker" for row in summary)
    assert any(row["blocker_count"] == 0 for row in summary)
    assert any(row["app_promotion_blockers"] > 0 for row in summary)


def test_model_v4_receipt_drilldown_reconciles_component_contributions() -> None:
    preview_row = {
        "player": "Player A",
        "position": "WR",
        "dynasty_asset_value": "22.0",
        "component_contributions": json.dumps(
            {
                "production": 12.0,
                "first_down_scoring_fit": 4.0,
                "snap_proxy_role": 2.5,
                "projection": 3.0,
                "young_player_prior": 0.5,
            }
        ),
    }
    receipt_rows = [
        {
            "player": "Player A",
            "component": "projection",
            "normalized_score": "30",
            "weight": "10",
            "contribution": "3.0",
            "source_status": "projection_stat_recompute_review_only",
            "raw_fields_used": "projected_receiving_yards",
            "raw_values": '{"projected_receiving_yards": 500}',
            "warning": "missing_first_down_projection|supplied_projection_points_ignored",
            "unavailable_reason": "",
        },
        {
            "player": "Player A",
            "component": "production",
            "normalized_score": "50",
            "weight": "24",
            "contribution": "12.0",
            "source_status": "imported_real_data",
            "raw_fields_used": "receiving_yards",
            "raw_values": '{"receiving_yards": 1000}',
            "warning": "",
            "unavailable_reason": "",
        },
        {
            "player": "Player A",
            "component": "snap_proxy_role",
            "normalized_score": "31.25",
            "weight": "8",
            "contribution": "2.5",
            "source_status": "imported_real_data",
            "raw_fields_used": "snap_share",
            "raw_values": '{"snap_share": 0.3125}',
            "warning": "snap_share_proxy_only_not_route_participation",
            "unavailable_reason": "",
        },
        {
            "player": "Player B",
            "component": "production",
            "contribution": "99",
            "source_status": "imported_real_data",
            "raw_fields_used": "receiving_yards",
            "raw_values": "{}",
            "warning": "",
            "unavailable_reason": "",
        },
        {
            "player": "Player A",
            "component": "young_player_prior",
            "normalized_score": "50",
            "weight": "1",
            "contribution": "0.5",
            "source_status": "review_only",
            "raw_fields_used": "draft_pick",
            "raw_values": '{"draft_pick": 12}',
            "warning": "young_player_prior_review_only",
            "unavailable_reason": "",
        },
        {
            "player": "Player A",
            "component": "first_down_scoring_fit",
            "normalized_score": "40",
            "weight": "10",
            "contribution": "4.0",
            "source_status": "missing",
            "raw_fields_used": "",
            "raw_values": "{}",
            "warning": "",
            "unavailable_reason": "missing first-down fields",
        },
    ]

    rows = build_model_v4_receipt_drilldown_rows(preview_row, receipt_rows)

    assert [row["component"] for row in rows[:4]] == [
        "production",
        "first_down_scoring_fit",
        "usage_opportunity",
        "snap_proxy_role",
    ]
    assert all(row["reconciles_preview_contribution"] for row in rows)
    assert rows[0]["receipt_group"] == MODEL_V4_RECEIPT_SECTION_LABELS["production"]
    assert set(MODEL_V4_RECEIPT_DRILLDOWN_COLUMNS).issubset(rows[0])
    highlights = {
        row["component"]: row["audit_highlight"]
        for row in rows
        if row["audit_highlight"]
    }
    assert "missing source section" in highlights["first_down_scoring_fit"]
    assert "proxy-only snap role" in highlights["snap_proxy_role"]
    assert "missing first-down projection" in highlights["projection"]
    assert "young prior review-only" in highlights["young_player_prior"]
    assert "missing source section" in highlights["usage_opportunity"]
    assert rows[-2]["component"] == "market_context"
    assert rows[-2]["source_status"] == "context_only"
    assert rows[-1]["component"] == "league_rank_rule_context"
    assert rows[-1]["source_status"] == "rule_context_only"

    reconciliation = build_model_v4_receipt_reconciliation_row(preview_row, rows)
    assert reconciliation == {
        "player": "Player A",
        "dynasty_asset_value": 22.0,
        "receipt_contribution_total": 22.0,
        "score_delta": 0.0,
        "reconciles_preview_score": True,
    }


def test_model_v4_source_gap_classification_and_labels() -> None:
    rows = build_model_v4_source_gap_rows(
        [
            {
                "player": "Established WR",
                "position": "WR",
                "section": "young_player_prior",
                "source_status": "not_applicable",
                "coverage_status": "missing",
                "warning": "young_player_prior_not_applicable",
                "unavailable_reason": "",
            },
            {
                "player": "Route WR",
                "position": "WR",
                "section": "snap_proxy_role",
                "source_status": "imported_real_data",
                "coverage_status": "covered",
                "warning": "snap_share_proxy_only_not_route_participation",
                "unavailable_reason": "",
            },
            {
                "player": "Projection RB",
                "position": "RB",
                "section": "projection",
                "source_status": "projection_stat_recompute_review_only",
                "coverage_status": "covered",
                "warning": "missing_first_down_projection",
                "unavailable_reason": "",
            },
            {
                "player": "Missing TE",
                "position": "TE",
                "section": "production",
                "source_status": "missing",
                "coverage_status": "missing",
                "warning": "",
                "unavailable_reason": "missing production rows",
            },
        ]
    )

    by_player = {row["player"]: row for row in rows}
    assert by_player["Established WR"]["gap_labels"] == "Not Applicable"
    assert by_player["Established WR"]["is_data_failure"] is False
    assert "Proxy-Only Evidence" in by_player["Route WR"]["gap_labels"]
    assert "Route Data Unavailable" in by_player["Route WR"]["gap_labels"]
    assert by_player["Projection RB"]["gap_labels"] == "First-Down Projection Gap"
    assert by_player["Missing TE"]["gap_labels"] == "Critical Missing Evidence"
    assert by_player["Missing TE"]["is_data_failure"] is True

    summary_rows = build_model_v4_source_gap_summary_rows(rows)
    summary_keys = {
        (row["gap_label"], row["component"], row["position"]): row["row_count"]
        for row in summary_rows
    }
    assert summary_keys[("Not Applicable", "young_player_prior", "WR")] == 1
    assert summary_keys[("Proxy-Only Evidence", "snap_proxy_role", "WR")] == 1
    assert summary_keys[("Route Data Unavailable", "snap_proxy_role", "WR")] == 1
    assert summary_keys[("First-Down Projection Gap", "projection", "RB")] == 1
    assert summary_keys[("Critical Missing Evidence", "production", "TE")] == 1
    assert MODEL_V4_SOURCE_GAP_CATEGORY_LABELS["not_applicable"] == "Not Applicable"


def test_model_v4_audit_rows_show_review_findings_first_and_never_unlock() -> None:
    sanity_rows = build_model_v4_sanity_fixture_audit_rows(
        [
            {
                "fixture_id": "ready_fixture",
                "fixture_name": "Ready Fixture",
                "status": "ready",
                "review_severity": "low",
                "players": "Player A",
                "expected_behavior": "Expected ready behavior",
                "actual_behavior": "Actual ready behavior",
                "disagreement_classification": "acceptable model disagreement",
                "likely_cause": "Expectation met.",
                "next_action": "No automatic tuning.",
            },
            {
                "fixture_id": "review_fixture",
                "fixture_name": "Review Fixture",
                "status": "review",
                "review_severity": "high",
                "players": "Player B|Player C",
                "expected_behavior": "Expected review behavior",
                "actual_behavior": "Actual surprising behavior",
                "disagreement_classification": "formula issue",
                "likely_cause": "Needs receipt review.",
                "next_action": "Inspect receipts.",
            },
        ]
    )
    named_rows = build_model_v4_named_player_audit_rows(
        [
            {
                "requested_player": "Strong Player",
                "matched_player": "Strong Player",
                "match_status": "matched",
                "overall_rank": "1",
                "position_rank": "1",
                "dynasty_asset_value": "75.0",
                "confidence_label": "usable",
                "review_notes": "",
                "warnings": "",
                "unavailable_sections": "",
            },
            {
                "requested_player": "Weak Player",
                "matched_player": "Weak Player",
                "match_status": "matched",
                "overall_rank": "40",
                "position_rank": "20",
                "dynasty_asset_value": "18.0",
                "confidence_label": "weak",
                "review_notes": "Weak confidence; treat as review finding.",
                "warnings": "missing_production_data",
                "unavailable_sections": "production",
            },
        ]
    )

    assert sanity_rows[0]["fixture_id"] == "review_fixture"
    assert sanity_rows[0]["audit_status"] == "review"
    assert sanity_rows[0]["classification"] == "formula issue"
    assert "Player B" in str(sanity_rows[0]["receipt_drilldown_hint"])
    assert sanity_rows[0]["decision_ready_unlocked"] is False
    sanity_summary = build_model_v4_audit_summary_rows(
        "Sanity Fixture Dry Run",
        sanity_rows,
    )[0]
    assert sanity_summary["ready_count"] == 1
    assert sanity_summary["review_count"] == 1
    assert sanity_summary["blocked_count"] == 0
    assert sanity_summary["decision_ready_unlocked"] is False

    assert named_rows[0]["requested_player"] == "Weak Player"
    assert named_rows[0]["audit_status"] == "review"
    assert named_rows[0]["expected_behavior"].startswith("Named player should")
    assert "Dynasty Asset Value 18.0" in str(named_rows[0]["actual_behavior"])
    assert named_rows[0]["classification"] == "confidence or source review"
    assert "receipt drilldown" in str(named_rows[0]["next_action"])
    named_summary = build_model_v4_audit_summary_rows(
        "Named Player Review",
        named_rows,
    )[0]
    assert named_summary["ready_count"] == 1
    assert named_summary["review_count"] == 1
    assert named_summary["blocked_count"] == 0
    assert named_summary["decision_ready_unlocked"] is False


def _write_summary(root: Path, *, active_rankings_overwritten: bool) -> None:
    summary = {
        "review_status": "review_only",
        "formula_version": "model_v4_review_only_test",
        "preview_engine_version": "model_v4_preview_test",
        "computed_at": "2026-05-16T00:00:00Z",
        "preview_output_rows": 2,
        "component_rows": 1,
        "receipt_rows": 1,
        "source_coverage_rows": 1,
        "warning_rows": 1,
        "active_rankings_overwritten": active_rankings_overwritten,
        "app_promotion": False,
        "decision_ready_unlocked": False,
        "draft_ready_unlocked": False,
        "final_money_ready_unlocked": False,
    }
    (root / "v4_preview_summary.json").write_text(
        json.dumps(summary),
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
