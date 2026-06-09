from __future__ import annotations

from src.services.model_v4_component_calculator_service import (
    MODEL_V4_COMPONENT_CALCULATOR_VERSION,
    calculate_age_dropoff_component,
    calculate_all_model_v4_components,
    calculate_confidence_component,
    calculate_first_down_scoring_fit_component,
    calculate_production_component,
    calculate_projection_component,
    calculate_qb_position_scarcity_suppression_component,
    calculate_snap_proxy_role_component,
    calculate_te_no_premium_suppression_component,
    calculate_usage_opportunity_component,
    calculate_young_player_prior_component,
)


def test_model_v4_production_component_calculates_lve_points_review_only() -> None:
    receipt = calculate_production_component(
        {
            "position": "RB",
            "rushing_yards": 1000,
            "rushing_tds": 10,
            "receiving_yards": 200,
            "receiving_tds": 2,
            "production_source_status": "imported_real_data",
        }
    )

    assert MODEL_V4_COMPONENT_CALCULATOR_VERSION
    assert receipt.component == "production"
    assert receipt.raw_values["lve_points_no_first_downs"] == 168.0
    assert receipt.normalized_score == 56.0
    assert receipt.weight == 24
    assert receipt.contribution == 13.44
    assert receipt.source_status == "imported_real_data"
    assert receipt.review_only is True


def test_model_v4_first_down_component_uses_point_four_rule() -> None:
    receipt = calculate_first_down_scoring_fit_component(
        {
            "position": "RB",
            "rushing_first_downs": 6,
            "receiving_first_downs": 4,
            "first_down_source_status": "imported_real_data",
        }
    )

    assert receipt.component == "first_down_scoring_fit"
    assert receipt.raw_values["first_downs"] == 10.0
    assert receipt.raw_values["first_down_points"] == 4.0
    assert receipt.raw_values["first_down_point_value"] == 0.4
    assert receipt.normalized_score == 10.0
    assert receipt.contribution == 1.4


def test_model_v4_usage_component_derives_opportunity_without_route_metrics() -> None:
    receipt = calculate_usage_opportunity_component(
        {
            "position": "RB",
            "targets": 55,
            "team_targets": 500,
            "target_share": 0.10,
            "rushing_attempts": 200,
            "team_rushing_attempts": 333,
            "rb_carry_share": 0.60,
            "rb_target_share": 0.20,
            "weighted_opportunities": 210,
            "red_zone_carries": 12,
            "red_zone_targets": 6,
            "goal_line_carries": 3,
            "goal_line_targets": 1,
            "route_participation": 0.90,
            "usage_source_status": "derived_real_data",
        }
    )

    assert receipt.component == "usage_opportunity"
    assert "route_participation" not in receipt.raw_fields_used
    assert receipt.raw_values["targets"] == 55
    assert receipt.raw_values["rushing_attempts"] == 200
    assert receipt.raw_values["route_metrics_used"] is False
    assert receipt.raw_values["sub_scores"]["rb_carry_share"] == 60.0
    assert receipt.raw_values["sub_scores"]["weighted_opportunities"] == 60.0
    assert receipt.normalized_score == 33.333
    assert receipt.contribution == 8.0
    assert "route_participation_unavailable" in receipt.warning
    assert "routes_run_unavailable" in receipt.warning
    assert "tprr_unavailable" in receipt.warning
    assert "yprr_unavailable" in receipt.warning
    assert "route_metrics_ignored_unavailable" in receipt.warning


def test_model_v4_usage_component_does_not_score_counts_without_subscores() -> None:
    receipt = calculate_usage_opportunity_component(
        {
            "position": "WR",
            "targets": 95,
            "rushing_attempts": 2,
        }
    )

    assert receipt.component == "usage_opportunity"
    assert receipt.normalized_score == 0.0
    assert receipt.contribution == 0.0
    assert receipt.warning == "missing_usage_opportunity_data"
    assert receipt.source_status == "missing"
    assert "targets" in receipt.raw_fields_used


def test_model_v4_snap_component_is_proxy_only_not_route_participation() -> None:
    receipt = calculate_snap_proxy_role_component(
        {
            "position": "WR",
            "snap_share": 0.82,
            "offense_snaps": 710,
            "games_with_offensive_snaps": 15,
            "snap_source_status": "imported_real_data",
        }
    )

    assert receipt.component == "snap_proxy_role"
    assert receipt.normalized_score == 82.0
    assert receipt.contribution == 4.1
    assert receipt.raw_values["offense_snaps"] == 710
    assert receipt.raw_values["games_with_offensive_snaps"] == 15
    assert receipt.raw_values["proxy_only"] is True
    assert receipt.raw_values["route_participation_used"] is False
    assert "snap_share_proxy_only_not_route_participation" in receipt.warning
    assert "route_participation_unavailable" in receipt.warning


def test_model_v4_projection_component_recomputes_points_and_status() -> None:
    receipt = calculate_projection_component(
        {
            "position": "WR",
            "projected_rushing_yards": 20,
            "projected_receiving_yards": 1000,
            "projected_receiving_tds": 6,
            "projected_receiving_first_downs": 50,
            "projected_lve_points_if_calculable": 999,
            "projection_source_status": "independent_projection",
        }
    )

    assert receipt.component == "projection"
    assert receipt.raw_values["recomputed_lve_points_no_first_downs"] == 126.0
    assert receipt.raw_values["first_down_points"] == 20.0
    assert receipt.raw_values["recomputed_lve_points"] == 146.0
    assert receipt.raw_values["first_down_projection_status"] == (
        "direct_first_down_projection"
    )
    assert receipt.normalized_score == 48.667
    assert "supplied_projection_points_ignored" in receipt.warning


def test_model_v4_projection_component_labels_estimated_first_downs() -> None:
    receipt = calculate_projection_component(
        {
            "position": "RB",
            "projected_rushing_attempts": 200,
            "projected_rushing_yards": 900,
            "projected_rushing_tds": 7,
            "projected_targets": 40,
            "projected_receptions": 30,
            "projected_receiving_yards": 240,
            "projected_receiving_tds": 2,
            "projected_rushing_first_downs": 44,
            "projected_receiving_first_downs": 12,
            "first_down_projection_status": "estimated_from_history",
            "first_down_projection_rate_source_status": (
                "historical_nflverse_player_stats"
            ),
            "first_down_projection_model_usage_status": (
                "preview_only_not_active_scoring"
            ),
            "rushing_first_down_rate": 0.22,
            "rushing_first_down_rate_scope": "player_recent",
            "receiving_first_down_rate_basis": "targets",
            "receiving_first_down_rate": 0.3,
            "receiving_first_down_rate_scope": "position_recent",
            "projection_source_status": "projection_stat_recompute_review_only",
        }
    )

    assert receipt.raw_values["first_down_projection_status"] == "estimated_from_history"
    assert receipt.raw_values["rushing_first_down_rate_scope"] == "player_recent"
    assert receipt.raw_values["receiving_first_down_rate_scope"] == "position_recent"
    assert receipt.raw_values["first_down_points"] == 22.4
    assert "estimated_from_history" in receipt.warning
    assert "projection_first_downs_estimated_from_history" in receipt.warning
    assert "first_down_projection_preview_only" in receipt.warning


def test_model_v4_age_component_is_visible_and_missing_age_is_not_scored() -> None:
    older_rb = calculate_age_dropoff_component({"position": "RB", "age": 29})
    missing_age = calculate_age_dropoff_component({"position": "WR"})

    assert older_rb.component == "age_dropoff"
    assert older_rb.raw_values["age_bucket"] == "cliff_risk_window"
    assert older_rb.normalized_score < 70
    assert older_rb.source_status == "derived_real_data"

    assert missing_age.source_status == "neutral_imputation"
    assert missing_age.normalized_score == 0.0
    assert missing_age.contribution == 0.0
    assert missing_age.raw_values["neutral_default_not_scored"] == 50.0
    assert missing_age.warning == "age_not_available"


def test_model_v4_young_player_prior_component_is_visible_and_lifecycle_limited() -> None:
    young = calculate_young_player_prior_component(
        {
            "position": "WR",
            "player_name": "Young Wideout",
            "draft_year": 2025,
            "draft_round": 1,
            "draft_overall": 23,
            "asset_lifecycle": "year_one_nfl_bridge",
        },
        season=2026,
    )
    veteran = calculate_young_player_prior_component(
        {
            "position": "WR",
            "player_name": "Veteran Wideout",
            "draft_year": 2020,
            "draft_round": 1,
            "draft_overall": 23,
            "asset_lifecycle": "established_veteran",
        },
        season=2026,
    )

    assert young.component == "young_player_prior"
    assert young.raw_values["experience_bucket"] == "year_one_nfl_player"
    assert young.raw_values["draft_capital_prior_score"] == 90.0
    assert young.raw_values["bridge_weight"] > 0
    assert young.contribution > 0
    assert young.warning == "young_player_prior_review_only"

    assert veteran.source_status == "not_applicable"
    assert veteran.normalized_score == 0.0
    assert veteran.contribution == 0.0
    assert veteran.warning == "young_player_prior_not_applicable"


def test_model_v4_qb_position_scarcity_component_suppresses_replaceable_qbs() -> None:
    elite_rusher = calculate_qb_position_scarcity_suppression_component(
        {
            "position": "QB",
            "passing_yards": 3800,
            "passing_tds": 28,
            "interceptions": 8,
            "rushing_yards": 650,
            "rushing_tds": 8,
            "rushing_first_downs": 45,
            "snap_share": 0.94,
        }
    )
    replaceable_passer = calculate_qb_position_scarcity_suppression_component(
        {
            "position": "QB",
            "passing_yards": 3900,
            "passing_tds": 26,
            "interceptions": 10,
            "rushing_yards": 80,
            "rushing_tds": 1,
            "rushing_first_downs": 6,
            "snap_share": 0.98,
        }
    )

    assert elite_rusher.component == "position_scarcity_suppression"
    assert elite_rusher.weight == 41
    assert elite_rusher.normalized_score > replaceable_passer.normalized_score
    assert elite_rusher.normalized_score == 8.0
    assert elite_rusher.contribution == 3.28
    assert replaceable_passer.normalized_score == 0.0
    assert "elite_rushing_qb_exception_review_only" in elite_rusher.warning
    assert "replaceable_qb_suppressed" in replaceable_passer.warning


def test_model_v4_te_no_premium_component_keeps_elite_exception_review_only() -> None:
    elite = calculate_te_no_premium_suppression_component(
        {
            "position": "TE",
            "receiving_yards": 1000,
            "receiving_tds": 7,
            "receiving_first_downs": 65,
            "target_share": 0.24,
            "weighted_opportunities": 170,
            "projected_receiving_yards": 950,
            "projected_receiving_tds": 6,
            "projected_receiving_first_downs": 55,
            "age": 24,
        }
    )
    replaceable = calculate_te_no_premium_suppression_component(
        {
            "position": "TE",
            "receiving_yards": 500,
            "receiving_tds": 3,
            "receiving_first_downs": 28,
            "target_share": 0.12,
            "weighted_opportunities": 80,
            "age": 32,
        }
    )

    assert elite.component == "no_premium_suppression"
    assert elite.weight == 10
    assert elite.normalized_score > replaceable.normalized_score
    assert "no_premium_te_suppression_review_only" in elite.warning
    assert "elite_te_exception_review_only" in elite.warning
    assert "replaceable_no_premium_te_review" in replaceable.warning


def test_model_v4_confidence_component_surfaces_missing_data_warnings() -> None:
    receipt = calculate_confidence_component(
        {
            "confidence": 88,
            "critical_missing_count": 1,
            "review_gap_count": 2,
            "warnings": "missing_projection_data|proxy_heavy_role",
        }
    )

    assert receipt.component == "confidence"
    assert receipt.source_status == "derived_audit_status"
    assert receipt.normalized_score == 50.0
    assert receipt.raw_values["confidence_label"] == "review"
    assert "missing_projection_data" in receipt.warning
    assert "proxy_heavy_role" in receipt.warning
    assert receipt.contribution == 0.0


def test_model_v4_incoming_rookie_with_no_evidence_cannot_show_strong_confidence() -> None:
    receipts = calculate_all_model_v4_components(
        {
            "player_name": "Incoming Rookie",
            "position": "RB",
            "asset_lifecycle": "incoming_rookie",
        }
    )
    confidence = next(receipt for receipt in receipts if receipt.component == "confidence")

    assert confidence.raw_values["confidence_label"] == "weak"
    assert confidence.raw_values["incoming_rookie_missing_all_evidence"] is True
    assert confidence.raw_values["confidence_cap"] == (
        "incoming_rookie_missing_all_evidence_weak_cap"
    )
    assert "incoming_rookie_missing_evidence_confidence_cap" in confidence.warning


def test_model_v4_all_components_do_not_create_final_ranks() -> None:
    receipts = calculate_all_model_v4_components({"position": "TE"})

    assert [receipt.component for receipt in receipts] == [
        "production",
        "first_down_scoring_fit",
        "usage_opportunity",
        "snap_proxy_role",
        "projection",
        "age_dropoff",
        "no_premium_suppression",
        "young_player_prior",
        "confidence",
    ]
    assert all(receipt.review_only for receipt in receipts)
    assert all("rank" not in receipt.as_row() for receipt in receipts)
    assert receipts[0].warning == "missing_production_data"
    assert receipts[1].warning == "missing_first_down_data"
    assert receipts[2].warning == "missing_usage_opportunity_data"
