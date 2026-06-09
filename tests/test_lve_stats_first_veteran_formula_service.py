from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.services.lve_stats_first_veteran_formula_service import (
    STATS_FIRST_MODEL_VERSION,
    score_stats_first_veteran_csv,
    score_stats_first_veteran_row,
    score_stats_first_veteran_rows,
    stats_first_output_rows,
)


def test_stats_first_private_value_ignores_market_liquidity() -> None:
    low_market = score_stats_first_veteran_row(_wr_row(market_liquidity=0))
    high_market = score_stats_first_veteran_row(_wr_row(market_liquidity=100))

    assert low_market.private_lve_value == high_market.private_lve_value
    assert low_market.horizon_retention_score == high_market.horizon_retention_score
    assert low_market.market_edge_score > high_market.market_edge_score
    assert low_market.market_edge_label.endswith("model_higher")
    assert high_market.market_edge_label.endswith("market_higher")
    assert low_market.market_keeper_influence == pytest.approx(0.0)
    assert high_market.market_keeper_influence == pytest.approx(0.0)
    assert high_market.keeper_score == low_market.keeper_score
    assert high_market.trade_value > low_market.trade_value + 25.0


def test_missing_market_liquidity_does_not_create_fake_market_edge() -> None:
    row = _wr_row()
    row.pop("market_liquidity")

    score = score_stats_first_veteran_row(row)
    output = stats_first_output_rows((score,))[0]

    assert score.market_value_status == "missing_market"
    assert score.market_trade_value == 50.0
    assert score.market_edge_score == 0.0
    assert score.market_edge_label == "missing_market"
    assert score.market_edge_warning == "missing_market_trade_value"
    assert output["market_value_status"] == "missing_market"


def test_critical_missing_source_caps_confidence_below_action_certainty() -> None:
    score = score_stats_first_veteran_row(
        _wr_row()
        | {
            "confidence": "94",
            "warnings": "missing_lve_scoring_history|missing_role_usage_features",
        }
    )

    assert score.confidence_score <= 58
    assert score.warning_status == "review_needed"
    assert "low_confidence" in score.risk_flags


def test_proxy_role_source_caps_high_confidence_without_changing_player_value() -> None:
    clean = score_stats_first_veteran_row(_wr_row() | {"confidence": "94"})
    proxy = score_stats_first_veteran_row(
        _wr_row()
        | {
            "confidence": "94",
            "warnings": "missing_participation_proxy|stale_lve_scoring_source",
        }
    )

    assert proxy.private_lve_value == clean.private_lve_value
    assert proxy.confidence_score <= 74
    assert proxy.warning_status == "data_warning"


def test_local_baseline_projection_caps_only_decision_certainty() -> None:
    normal = score_stats_first_veteran_row(_wr_row() | {"confidence": "76"})
    high_claim = score_stats_first_veteran_row(
        _wr_row()
        | {
            "confidence": "94",
            "projection_source_status": "local_baseline_projection",
            "warnings": "local_baseline_projection_not_independent",
        }
    )

    assert normal.confidence_score == pytest.approx(76)
    assert high_claim.confidence_score == pytest.approx(78)
    assert high_claim.warning_status == "ready"


def test_missing_injury_source_caps_only_usable_certainty() -> None:
    score = score_stats_first_veteran_row(
        _wr_row()
        | {
            "confidence": "94",
            "warnings": "missing_injury_features",
        }
    )

    assert score.confidence_score == pytest.approx(82)
    assert score.warning_status == "ready"


def test_stats_first_drop_risk_ignores_market_and_forced_release_pressure() -> None:
    football_row = _wr_row(market_liquidity=0) | {"is_league_rank_top5": "false"}
    market_rule_row = _wr_row(market_liquidity=100) | {"is_league_rank_top5": "true"}

    football_only = score_stats_first_veteran_row(football_row)
    market_rule = score_stats_first_veteran_row(market_rule_row)

    assert football_only.private_lve_value == market_rule.private_lve_value
    assert football_only.keeper_score == market_rule.keeper_score
    assert football_only.drop_candidate_score == market_rule.drop_candidate_score
    assert football_only.trade_value < market_rule.trade_value


def test_stats_first_private_contributions_are_stats_only() -> None:
    score = score_stats_first_veteran_row(
        _wr_row(market_liquidity=99) | {"efficiency_score": "90"}
    )
    private_features = {
        contribution.feature_name
        for contribution in score.contributions
        if contribution.component in {"private_lve_value", "win_now_value", "dynasty_hold_value"}
    }

    assert "market_liquidity" not in private_features
    assert "efficiency_score" in private_features
    assert "win_now_value" in private_features
    assert "dynasty_hold_value" in private_features
    assert "trade_value" in {
        contribution.component
        for contribution in score.contributions
        if contribution.feature_name == "market_liquidity"
    }


def test_young_nfl_bridge_adds_visible_private_value_prior() -> None:
    young_wr = score_stats_first_veteran_row(
        _wr_row(
            player_id="12519",
            player_name="Luther Burden",
            weighted_recent_lve_ppg_score=50,
            expected_lve_points_score=50,
            lve_projection_value=50,
            role_security=23,
            target_earning_stability=0,
            route_role=0,
            first_down_td_fit=50,
            age_curve=90,
            injury_durability=100,
            market_liquidity=50,
        )
        | {
            "draft_year": "2025",
            "draft_round": "2",
            "draft_ovr": "39",
            "warnings": (
                "missing_lve_scoring_history|missing_projection_features|"
                "missing_participation_proxy"
            ),
        }
    )
    same_row_without_prior = _wr_row(
        player_id="veteran_missing_production",
        player_name="Missing Production Veteran",
        weighted_recent_lve_ppg_score=50,
        expected_lve_points_score=50,
        lve_projection_value=50,
        role_security=23,
        target_earning_stability=0,
        route_role=0,
        first_down_td_fit=50,
        age_curve=90,
        injury_durability=100,
        market_liquidity=50,
    )
    older = score_stats_first_veteran_row(
        same_row_without_prior
        | {
            "draft_year": "2021",
            "draft_round": "2",
            "draft_ovr": "39",
        }
    )
    receipts = _receipt_map(young_wr)

    assert young_wr.experience_bucket == "year_one_nfl_player"
    assert young_wr.young_nfl_bridge_weight > 0.34
    assert young_wr.private_lve_value > older.private_lve_value
    assert ("private_lve_value", "young_nfl_bridge_prior") in receipts
    assert ("private_lve_value", "draft_capital_prior_score") in receipts
    assert ("private_lve_value", "young_nfl_bridge_decay_weight") in receipts
    assert ("private_lve_value", "young_nfl_bridge_nfl_evidence_weight") in receipts
    assert receipts[("private_lve_value", "young_nfl_bridge_prior")].normalized_score == 82.0


def test_draft_capital_prior_decays_when_young_wr_has_clear_nfl_evidence() -> None:
    clear_evidence = score_stats_first_veteran_row(
        _wr_row(
            player_id="young_high_cap_wr",
            player_name="Young High Capital WR",
            weighted_recent_lve_ppg_score=84,
            expected_lve_points_score=85,
            lve_projection_value=84,
            role_security=86,
            target_earning_stability=84,
            route_role=85,
            first_down_td_fit=82,
            age_curve=91,
            injury_durability=82,
            market_liquidity=50,
        )
        | {
            "draft_year": "2025",
            "draft_round": "1",
            "draft_ovr": "18",
            "confidence": "88",
            "warnings": "",
        }
    )
    missing_evidence = score_stats_first_veteran_row(
        _wr_row(
            player_id="young_high_cap_missing_wr",
            player_name="Young High Capital Missing WR",
            weighted_recent_lve_ppg_score=50,
            expected_lve_points_score=50,
            lve_projection_value=50,
            role_security=50,
            target_earning_stability=50,
            route_role=50,
            first_down_td_fit=50,
            age_curve=91,
            injury_durability=82,
            market_liquidity=50,
        )
        | {
            "draft_year": "2025",
            "draft_round": "1",
            "draft_ovr": "18",
            "confidence": "88",
            "warnings": (
                "missing_lve_scoring_history|missing_projection_features|"
                "missing_participation_proxy"
            ),
        }
    )
    receipts = _receipt_map(clear_evidence)

    assert clear_evidence.young_nfl_bridge_weight < missing_evidence.young_nfl_bridge_weight
    assert clear_evidence.young_nfl_bridge_weight < 0.22
    assert receipts[("private_lve_value", "draft_capital_prior_score")].normalized_score == 90.0
    assert receipts[("private_lve_value", "young_nfl_bridge_prior")].feature_weight < 22
    assert (
        receipts[
            ("private_lve_value", "young_nfl_bridge_nfl_evidence_weight")
        ].normalized_score
        > 95
    )


def test_young_low_capital_rb_prior_stays_small_and_auditable() -> None:
    low_cap_rb = score_stats_first_veteran_row(
        _rb_row(
            player_id="young_low_cap_rb",
            player_name="Young Low Capital RB",
            weighted_recent_lve_ppg_score=52,
            expected_lve_points_score=54,
            lve_projection_value=53,
            role_security=46,
            workload_earning=45,
            first_down_td_fit=48,
            efficiency_score=50,
            age_curve=88,
            injury_durability=76,
        )
        | {
            "draft_year": "2025",
            "draft_round": "6",
            "draft_ovr": "185",
            "confidence": "82",
            "warnings": "missing_participation_proxy",
        }
    )
    receipts = _receipt_map(low_cap_rb)

    assert low_cap_rb.experience_bucket == "year_one_nfl_player"
    assert low_cap_rb.young_nfl_bridge_prior_score < 50
    assert receipts[("private_lve_value", "draft_capital_prior_score")].normalized_score < 50
    assert low_cap_rb.private_lve_value < 65


def test_established_veteran_draft_capital_does_not_move_private_value() -> None:
    with_old_draft_capital = score_stats_first_veteran_row(
        _wr_row(player_id="established_wr", player_name="Established WR")
        | {"draft_year": "2020", "draft_round": "1", "draft_ovr": "1"}
    )
    without_draft_capital = score_stats_first_veteran_row(
        _wr_row(player_id="established_wr", player_name="Established WR")
    )

    assert with_old_draft_capital.experience_bucket == "established_veteran"
    assert with_old_draft_capital.private_lve_value == without_draft_capital.private_lve_value
    assert ("private_lve_value", "young_nfl_bridge_prior") not in _receipt_map(
        with_old_draft_capital
    )


def test_stats_first_wr_beats_speculative_rb_without_market_help() -> None:
    solid_wr = score_stats_first_veteran_row(_wr_row(market_liquidity=50))
    speculative_rb = score_stats_first_veteran_row(
        {
            "season": "2026",
            "player_id": "rb_spec",
            "player_name": "Speculative RB",
            "position": "RB",
            "team": "SF",
            "weighted_recent_lve_ppg_score": "68",
            "expected_lve_points_score": "72",
            "lve_projection_value": "74",
            "role_security": "58",
            "workload_earning": "56",
            "target_earning_stability": "50",
            "route_role": "50",
            "first_down_td_fit": "55",
            "age_curve": "86",
            "injury_durability": "76",
            "confidence": "84",
            "missing_data_penalty": "0",
            "warnings": "",
            "market_liquidity": "80",
        }
    )

    assert solid_wr.keeper_score > speculative_rb.keeper_score
    assert speculative_rb.private_lve_value < 70
    assert "committee_risk" in speculative_rb.risk_flags


def test_wr_formula_separates_win_now_from_dynasty_hold() -> None:
    jsn = score_stats_first_veteran_row(
        _wr_row(
            player_id="jaxon_smith_njigba",
            player_name="Jaxon Smith-Njigba",
            weighted_recent_lve_ppg_score=96,
            expected_lve_points_score=94,
            lve_projection_value=93,
            role_security=94,
            target_earning_stability=96,
            route_role=93,
            first_down_td_fit=92,
            efficiency_score=94,
            age_curve=90,
            injury_durability=84,
        )
    )
    tee = score_stats_first_veteran_row(
        _wr_row(
            player_id="tee_higgins",
            player_name="Tee Higgins",
            weighted_recent_lve_ppg_score=84,
            expected_lve_points_score=82,
            lve_projection_value=85,
            role_security=82,
            target_earning_stability=76,
            route_role=82,
            first_down_td_fit=82,
            efficiency_score=84,
            age_curve=72,
            injury_durability=78,
            market_liquidity=95,
        )
    )

    assert jsn.win_now_value > tee.win_now_value
    assert jsn.dynasty_hold_value > tee.dynasty_hold_value
    assert jsn.private_lve_value > tee.private_lve_value
    assert jsn.keeper_score > tee.keeper_score
    assert "elite_wr_anchor" in jsn.upside_flags
    assert "wr_stable_target_role" in jsn.floor_flags


def test_wr_btj_beats_luther_when_recent_production_and_target_role_are_stronger() -> None:
    btj = score_stats_first_veteran_row(
        _wr_row(
            player_id="brian_thomas",
            player_name="Brian Thomas",
            weighted_recent_lve_ppg_score=91,
            expected_lve_points_score=90,
            lve_projection_value=90,
            role_security=91,
            target_earning_stability=87,
            route_role=90,
            first_down_td_fit=89,
            efficiency_score=90,
            age_curve=91,
            injury_durability=86,
        )
    )
    luther = score_stats_first_veteran_row(
        _wr_row(
            player_id="luther_burden",
            player_name="Luther Burden",
            weighted_recent_lve_ppg_score=62,
            expected_lve_points_score=70,
            lve_projection_value=77,
            role_security=76,
            target_earning_stability=74,
            route_role=76,
            first_down_td_fit=76,
            efficiency_score=78,
            age_curve=96,
            injury_durability=84,
            market_liquidity=96,
        )
    )

    assert btj.private_lve_value > luther.private_lve_value
    assert btj.keeper_score > luther.keeper_score
    assert btj.win_now_value > luther.win_now_value
    assert btj.dynasty_hold_value > luther.dynasty_hold_value


def test_elite_wr_anchor_fixtures_clear_top_tier() -> None:
    anchors = score_stats_first_veteran_rows(
        [
            _wr_row(
                player_id="jamarr_chase",
                player_name="Ja'Marr Chase",
                weighted_recent_lve_ppg_score=96,
                expected_lve_points_score=95,
                lve_projection_value=95,
                role_security=94,
                target_earning_stability=96,
                route_role=95,
                first_down_td_fit=94,
                efficiency_score=95,
                age_curve=88,
                injury_durability=85,
            ),
            _wr_row(
                player_id="justin_jefferson",
                player_name="Justin Jefferson",
                weighted_recent_lve_ppg_score=94,
                expected_lve_points_score=95,
                lve_projection_value=95,
                role_security=94,
                target_earning_stability=95,
                route_role=96,
                first_down_td_fit=91,
                efficiency_score=96,
                age_curve=86,
                injury_durability=82,
            ),
            _wr_row(
                player_id="puka_nacua",
                player_name="Puka Nacua",
                weighted_recent_lve_ppg_score=94,
                expected_lve_points_score=93,
                lve_projection_value=93,
                role_security=93,
                target_earning_stability=94,
                route_role=94,
                first_down_td_fit=92,
                efficiency_score=93,
                age_curve=91,
                injury_durability=80,
            ),
        ]
    )

    assert all(score.private_lve_value >= 90 for score in anchors)
    assert all("elite_wr_anchor" in score.upside_flags for score in anchors)
    assert all("stable_target_earner" in score.upside_flags for score in anchors)


def test_wr_score_receipts_show_recent_production_and_target_earning() -> None:
    score = score_stats_first_veteran_row(
        _wr_row(
            player_id="receipt_wr",
            player_name="Receipt WR",
            weighted_recent_lve_ppg_score=94,
            expected_lve_points_score=92,
            lve_projection_value=91,
            role_security=92,
            target_earning_stability=93,
            route_role=91,
            first_down_td_fit=89,
            efficiency_score=90,
            age_curve=88,
            injury_durability=82,
        )
    )
    receipts = {
        (contribution.component, contribution.feature_name): contribution
        for contribution in score.contributions
    }

    assert ("win_now_value", "weighted_recent_lve_ppg_score") in receipts
    assert ("win_now_value", "target_earning_stability") in receipts
    assert ("win_now_value", "route_role") in receipts
    assert ("dynasty_hold_value", "target_earning_stability") in receipts
    assert ("dynasty_hold_value", "production_stability") in receipts
    assert receipts[("win_now_value", "target_earning_stability")].component_contribution > 18
    assert receipts[("dynasty_hold_value", "target_earning_stability")].component_contribution > 20


def test_wr_missing_participation_uses_target_earning_route_proxy() -> None:
    score = score_stats_first_veteran_row(
        _wr_row(
            player_id="elite_wr_missing_route",
            player_name="Elite WR Missing Route Data",
            weighted_recent_lve_ppg_score=94,
            expected_lve_points_score=93,
            lve_projection_value=92,
            role_security=92,
            workload_earning=94,
            target_earning_stability=95,
            route_role=50,
            first_down_td_fit=90,
            efficiency_score=92,
            age_curve=88,
            injury_durability=82,
        )
        | {"warnings": "missing_participation_proxy"}
    )
    receipts = _receipt_map(score)

    route_receipt = receipts[("win_now_value", "route_role")]
    assert route_receipt.normalized_score > 90
    assert score.private_lve_value > 88
    assert "route_role_fragility" not in score.risk_flags
    assert "elite_wr_anchor" in score.upside_flags


def test_wr_real_low_route_role_still_penalizes_fragile_profile() -> None:
    score = score_stats_first_veteran_row(
        _wr_row(
            player_id="fragile_wr_real_route",
            player_name="Fragile WR Real Route Data",
            weighted_recent_lve_ppg_score=94,
            expected_lve_points_score=93,
            lve_projection_value=92,
            role_security=92,
            workload_earning=94,
            target_earning_stability=95,
            route_role=50,
            first_down_td_fit=90,
            efficiency_score=92,
            age_curve=88,
            injury_durability=82,
        )
    )
    receipts = _receipt_map(score)

    assert receipts[("win_now_value", "route_role")].normalized_score == 50
    assert "route_role_fragility" in score.risk_flags
    assert score.private_lve_value < 86


def test_rb_formula_separates_win_now_from_dynasty_hold() -> None:
    kyren = score_stats_first_veteran_row(
        _rb_row(
            player_id="kyren_williams",
            player_name="Kyren Williams",
            weighted_recent_lve_ppg_score=94,
            expected_lve_points_score=93,
            lve_projection_value=91,
            role_security=96,
            workload_earning=95,
            first_down_td_fit=92,
            efficiency_score=82,
            age_curve=56,
            injury_durability=58,
        )
    )
    bijan = score_stats_first_veteran_row(
        _rb_row(
            player_id="bijan_robinson",
            player_name="Bijan Robinson",
            weighted_recent_lve_ppg_score=91,
            expected_lve_points_score=94,
            lve_projection_value=94,
            role_security=92,
            workload_earning=92,
            first_down_td_fit=90,
            efficiency_score=90,
            age_curve=94,
            injury_durability=88,
        )
    )

    assert kyren.win_now_value >= 90
    assert kyren.dynasty_hold_value < bijan.dynasty_hold_value
    assert kyren.private_lve_value < bijan.private_lve_value
    assert kyren.keeper_score < bijan.keeper_score
    assert "rb_workload_injury_fragility" in kyren.risk_flags


def test_rb_sanity_fixture_ranking_is_not_role_only() -> None:
    scores = score_stats_first_veteran_rows(
        [
            _rb_row(
                player_id="kyren_williams",
                player_name="Kyren Williams",
                weighted_recent_lve_ppg_score=94,
                expected_lve_points_score=93,
                lve_projection_value=91,
                role_security=96,
                workload_earning=95,
                first_down_td_fit=92,
                efficiency_score=82,
                age_curve=56,
                injury_durability=58,
            ),
            _rb_row(
                player_id="bijan_robinson",
                player_name="Bijan Robinson",
                weighted_recent_lve_ppg_score=91,
                expected_lve_points_score=94,
                lve_projection_value=94,
                role_security=92,
                workload_earning=92,
                first_down_td_fit=90,
                efficiency_score=90,
                age_curve=94,
                injury_durability=88,
            ),
            _rb_row(
                player_id="jahmyr_gibbs",
                player_name="Jahmyr Gibbs",
                weighted_recent_lve_ppg_score=90,
                expected_lve_points_score=92,
                lve_projection_value=92,
                role_security=89,
                workload_earning=86,
                first_down_td_fit=84,
                efficiency_score=92,
                age_curve=93,
                injury_durability=86,
            ),
            _rb_row(
                player_id="ashton_jeanty",
                player_name="Ashton Jeanty",
                weighted_recent_lve_ppg_score=84,
                expected_lve_points_score=88,
                lve_projection_value=88,
                role_security=81,
                workload_earning=86,
                first_down_td_fit=88,
                efficiency_score=88,
                age_curve=97,
                injury_durability=85,
            ),
            _rb_row(
                player_id="devon_achane",
                player_name="De'Von Achane",
                weighted_recent_lve_ppg_score=88,
                expected_lve_points_score=88,
                lve_projection_value=89,
                role_security=77,
                workload_earning=72,
                first_down_td_fit=76,
                efficiency_score=95,
                age_curve=91,
                injury_durability=68,
            ),
            _rb_row(
                player_id="chase_brown",
                player_name="Chase Brown",
                weighted_recent_lve_ppg_score=80,
                expected_lve_points_score=82,
                lve_projection_value=82,
                role_security=83,
                workload_earning=82,
                first_down_td_fit=82,
                efficiency_score=80,
                age_curve=78,
                injury_durability=74,
            ),
        ]
    )
    rb_order = [score.player_name for score in scores]

    assert rb_order[0] in {"Bijan Robinson", "Jahmyr Gibbs"}
    assert rb_order.index("Kyren Williams") > rb_order.index("Bijan Robinson")
    assert rb_order.index("Kyren Williams") > rb_order.index("Jahmyr Gibbs")
    assert rb_order.index("Kyren Williams") > rb_order.index("Ashton Jeanty")


def test_role_score_alone_cannot_create_rb1_profile() -> None:
    role_only = score_stats_first_veteran_row(
        _rb_row(
            player_id="role_only",
            player_name="Role Only RB",
            weighted_recent_lve_ppg_score=70,
            expected_lve_points_score=72,
            lve_projection_value=72,
            role_security=100,
            workload_earning=100,
            first_down_td_fit=100,
            efficiency_score=70,
            age_curve=45,
            injury_durability=45,
        )
    )
    balanced_elite = score_stats_first_veteran_row(
        _rb_row(
            player_id="balanced_elite",
            player_name="Balanced Elite RB",
            weighted_recent_lve_ppg_score=88,
            expected_lve_points_score=90,
            lve_projection_value=90,
            role_security=88,
            workload_earning=88,
            first_down_td_fit=86,
            efficiency_score=88,
            age_curve=90,
            injury_durability=84,
        )
    )

    assert role_only.win_now_value < balanced_elite.win_now_value
    assert role_only.dynasty_hold_value < 65
    assert role_only.private_lve_value < balanced_elite.private_lve_value
    assert role_only.keeper_score < balanced_elite.keeper_score


def test_elite_rushing_qb_exception_beats_pocket_qb_suppression() -> None:
    lamar = score_stats_first_veteran_row(
        _qb_row(
            player_id="lamar_jackson",
            player_name="Lamar Jackson",
            weighted_recent_lve_ppg_score=94,
            expected_lve_points_score=95,
            lve_projection_value=94,
            role_security=96,
            qb_rushing_profile=98,
            first_down_td_fit=96,
            efficiency_score=88,
            age_curve=83,
            injury_durability=82,
        )
    )
    pocket_qb = score_stats_first_veteran_row(
        _qb_row(
            player_id="good_pocket_qb",
            player_name="Good Pocket QB",
            weighted_recent_lve_ppg_score=88,
            expected_lve_points_score=90,
            lve_projection_value=90,
            role_security=94,
            qb_rushing_profile=28,
            first_down_td_fit=30,
            efficiency_score=94,
            age_curve=80,
            injury_durability=88,
            market_liquidity=100,
        )
    )

    assert lamar.private_lve_value >= 90
    assert lamar.keeper_score > pocket_qb.keeper_score + 20
    assert lamar.structural_adjustment == pytest.approx(-2.0)
    assert "elite_1qb_exception" in lamar.upside_flags
    assert "secure_rushing_qb_edge" in lamar.upside_flags
    assert pocket_qb.private_lve_value < 80
    assert pocket_qb.structural_adjustment == pytest.approx(-10.0)
    assert "pocket_qb_1qb_suppression" in pocket_qb.risk_flags
    assert "replaceable_1qb_profile" in pocket_qb.risk_flags


def test_elite_rushing_qb_can_use_real_production_when_projection_is_neutral() -> None:
    rushing_anchor = score_stats_first_veteran_row(
        _qb_row(
            player_id="secure_rushing_anchor",
            player_name="Secure Rushing Anchor",
            weighted_recent_lve_ppg_score=96,
            expected_lve_points_score=50,
            lve_projection_value=50,
            role_security=96,
            qb_rushing_profile=98,
            first_down_td_fit=96,
            efficiency_score=88,
            age_curve=82,
            injury_durability=82,
        )
    )
    pocket_qb = score_stats_first_veteran_row(
        _qb_row(
            player_id="neutral_projection_pocket_qb",
            player_name="Neutral Projection Pocket QB",
            weighted_recent_lve_ppg_score=96,
            expected_lve_points_score=50,
            lve_projection_value=50,
            role_security=96,
            qb_rushing_profile=28,
            first_down_td_fit=30,
            efficiency_score=94,
            age_curve=82,
            injury_durability=82,
        )
    )
    receipts = _receipt_map(rushing_anchor)

    assert rushing_anchor.private_lve_value > pocket_qb.private_lve_value + 12
    assert rushing_anchor.structural_adjustment == pytest.approx(-2.0)
    assert "elite_1qb_exception" in rushing_anchor.upside_flags
    assert "secure_rushing_qb_edge" in rushing_anchor.upside_flags
    assert "pocket_qb_1qb_suppression" not in rushing_anchor.risk_flags
    assert "pocket_qb_1qb_suppression" in pocket_qb.risk_flags
    assert ("private_lve_value", "qb_elite_exception") in receipts


def test_qb_rushing_counts_only_when_start_security_is_real() -> None:
    rushing_backup = score_stats_first_veteran_row(
        _qb_row(
            player_id="rushing_backup",
            player_name="Rushing Backup",
            weighted_recent_lve_ppg_score=58,
            expected_lve_points_score=62,
            lve_projection_value=64,
            role_security=48,
            qb_rushing_profile=96,
            first_down_td_fit=94,
            efficiency_score=70,
            age_curve=82,
            injury_durability=84,
        )
    )
    receipts = {
        (contribution.component, contribution.feature_name): contribution
        for contribution in rushing_backup.contributions
    }

    assert rushing_backup.private_lve_value < 65
    assert "qb_start_security_risk" in rushing_backup.risk_flags
    assert "qb_rushing_not_start_gated" in rushing_backup.risk_flags
    assert "secure_rushing_qb_edge" not in rushing_backup.upside_flags
    assert receipts[("win_now_value", "start_gated_rushing_profile")].normalized_score <= 45


def test_non_elite_qb_does_not_crowd_out_similar_tier_rb_wr_values() -> None:
    qb = score_stats_first_veteran_row(
        _qb_row(
            player_id="mid_qb",
            player_name="Mid QB",
            weighted_recent_lve_ppg_score=84,
            expected_lve_points_score=85,
            lve_projection_value=84,
            role_security=86,
            qb_rushing_profile=45,
            first_down_td_fit=45,
            efficiency_score=86,
            age_curve=80,
            injury_durability=80,
        )
    )
    wr = score_stats_first_veteran_row(
        _wr_row(
            player_id="solid_wr_tier",
            player_name="Solid WR Tier",
            weighted_recent_lve_ppg_score=84,
            expected_lve_points_score=84,
            lve_projection_value=84,
            role_security=84,
            target_earning_stability=84,
            route_role=84,
            first_down_td_fit=82,
            efficiency_score=83,
            age_curve=82,
            injury_durability=80,
        )
    )
    rb = score_stats_first_veteran_row(
        _rb_row(
            player_id="solid_rb_tier",
            player_name="Solid RB Tier",
            weighted_recent_lve_ppg_score=84,
            expected_lve_points_score=84,
            lve_projection_value=84,
            role_security=84,
            workload_earning=82,
            first_down_td_fit=82,
            efficiency_score=82,
            age_curve=82,
            injury_durability=78,
        )
    )

    assert qb.keeper_score < wr.keeper_score
    assert qb.keeper_score < rb.keeper_score
    assert "replaceable_1qb_profile" in qb.risk_flags


def test_qb_replacement_baseline_is_visible_in_score_receipts() -> None:
    qb = score_stats_first_veteran_row(
        _qb_row(
            player_id="receipt_qb",
            player_name="Receipt QB",
            weighted_recent_lve_ppg_score=82,
            expected_lve_points_score=82,
            lve_projection_value=82,
            role_security=84,
            qb_rushing_profile=42,
            first_down_td_fit=42,
            efficiency_score=84,
            age_curve=80,
            injury_durability=80,
            qb_replacement_level_baseline=77,
        )
    )
    receipts = {
        (contribution.component, contribution.feature_name): contribution
        for contribution in qb.contributions
    }

    assert ("private_lve_value", "qb_replacement_level_baseline") in receipts
    assert ("private_lve_value", "qb_replacement_suppression") in receipts
    assert receipts[("private_lve_value", "qb_replacement_level_baseline")].normalized_score == 77


def test_stats_first_qb_and_te_suppression_rules() -> None:
    qb = score_stats_first_veteran_row(
        _base_row(
            position="QB",
            player_id="qb_good",
            weighted_recent_lve_ppg_score=82,
            expected_lve_points_score=84,
            lve_projection_value=84,
            role_security=86,
            first_down_td_fit=42,
            market_liquidity=92,
        )
    )
    te = score_stats_first_veteran_row(
        _base_row(
            position="TE",
            player_id="te_ok",
            weighted_recent_lve_ppg_score=76,
            expected_lve_points_score=78,
            lve_projection_value=77,
            role_security=74,
            route_role=64,
            target_earning_stability=66,
            first_down_td_fit=69,
            market_liquidity=90,
        )
    )

    assert qb.structural_adjustment == pytest.approx(-10.0)
    assert qb.keeper_score < 80
    assert "replaceable_1qb_profile" in qb.risk_flags
    assert te.structural_adjustment == pytest.approx(-8.0)
    assert te.private_lve_value < 75
    assert "replaceable_no_premium_te" in te.risk_flags


def test_elite_te_can_clear_no_premium_exception_gate() -> None:
    elite_te = score_stats_first_veteran_row(
        _base_row(
            position="TE",
            player_id="te_elite",
            weighted_recent_lve_ppg_score=93,
            expected_lve_points_score=92,
            lve_projection_value=92,
            role_security=90,
            route_role=90,
            target_earning_stability=88,
            first_down_td_fit=88,
            age_curve=78,
            injury_durability=84,
            market_liquidity=90,
        )
    )

    assert elite_te.private_lve_value >= 88
    assert elite_te.structural_adjustment == pytest.approx(-2.0)
    assert "difference_making_te_routes" in elite_te.upside_flags


def test_elite_te_can_use_real_production_when_projection_is_neutral() -> None:
    elite = score_stats_first_veteran_row(
        _te_row(
            player_id="elite_route_target_te",
            player_name="Elite Route Target TE",
            weighted_recent_lve_ppg_score=90,
            expected_lve_points_score=50,
            lve_projection_value=50,
            route_role=92,
            target_earning_stability=90,
            first_down_td_fit=86,
            efficiency_score=90,
            age_curve=78,
            injury_durability=82,
        )
    )
    low_route = score_stats_first_veteran_row(
        _te_row(
            player_id="low_route_te",
            player_name="Low Route TE",
            weighted_recent_lve_ppg_score=90,
            expected_lve_points_score=50,
            lve_projection_value=50,
            route_role=52,
            target_earning_stability=88,
            first_down_td_fit=86,
            efficiency_score=90,
            age_curve=78,
            injury_durability=82,
        )
    )
    receipts = _receipt_map(elite)

    assert elite.private_lve_value > low_route.private_lve_value + 18
    assert "elite_no_premium_te_exception" in elite.upside_flags
    assert "replaceable_no_premium_te" not in elite.risk_flags
    assert "replaceable_no_premium_te" in low_route.risk_flags
    assert ("private_lve_value", "te_elite_exception") in receipts


def test_te_scarcity_cannot_directly_inflate_private_value() -> None:
    normal = score_stats_first_veteran_row(
        _te_row(
            player_id="scarcity_te",
            player_name="Scarcity TE",
            weighted_recent_lve_ppg_score=76,
            expected_lve_points_score=78,
            lve_projection_value=78,
            route_role=74,
            target_earning_stability=70,
            first_down_td_fit=72,
            efficiency_score=76,
            age_curve=78,
            injury_durability=82,
            market_liquidity=20,
        )
    )
    inflated_scarcity = score_stats_first_veteran_row(
        _te_row(
            player_id="scarcity_te",
            player_name="Scarcity TE",
            weighted_recent_lve_ppg_score=76,
            expected_lve_points_score=78,
            lve_projection_value=78,
            route_role=74,
            target_earning_stability=70,
            first_down_td_fit=72,
            efficiency_score=76,
            age_curve=78,
            injury_durability=82,
            market_liquidity=100,
        )
        | {"te_scarcity_score": "100", "position_scarcity": "100"}
    )

    assert inflated_scarcity.private_lve_value == normal.private_lve_value
    assert inflated_scarcity.dynasty_hold_value == normal.dynasty_hold_value
    assert inflated_scarcity.trade_value > normal.trade_value
    assert "replaceable_no_premium_te" in normal.risk_flags


def test_low_route_blocker_te_is_heavily_suppressed() -> None:
    blocker = score_stats_first_veteran_row(
        _te_row(
            player_id="blocker_te",
            player_name="Blocker TE",
            weighted_recent_lve_ppg_score=58,
            expected_lve_points_score=62,
            lve_projection_value=62,
            route_role=44,
            target_earning_stability=50,
            first_down_td_fit=64,
            efficiency_score=68,
            age_curve=76,
            injury_durability=84,
        )
    )

    assert blocker.private_lve_value < 64
    assert blocker.keeper_score < 60
    assert blocker.structural_adjustment == pytest.approx(-12.0)
    assert "blocking_dependency_risk" in blocker.risk_flags
    assert "weak_te_target_earning" in blocker.risk_flags
    assert "low_route_te_profile" in blocker.risk_flags


def test_no_premium_te_fixtures_separate_elite_from_replaceable_starters() -> None:
    elite = score_stats_first_veteran_row(
        _te_row(
            player_id="elite_route_te",
            player_name="Elite Route TE",
            weighted_recent_lve_ppg_score=92,
            expected_lve_points_score=91,
            lve_projection_value=91,
            route_role=91,
            target_earning_stability=88,
            first_down_td_fit=88,
            efficiency_score=91,
            age_curve=82,
            injury_durability=84,
        )
    )
    useful_starter = score_stats_first_veteran_row(
        _te_row(
            player_id="useful_starter_te",
            player_name="Useful Starter TE",
            weighted_recent_lve_ppg_score=78,
            expected_lve_points_score=79,
            lve_projection_value=79,
            route_role=76,
            target_earning_stability=71,
            first_down_td_fit=74,
            efficiency_score=77,
            age_curve=80,
            injury_durability=84,
            market_liquidity=95,
        )
    )

    assert elite.private_lve_value >= 88
    assert elite.keeper_score > useful_starter.keeper_score + 15
    assert elite.structural_adjustment == pytest.approx(-2.0)
    assert useful_starter.private_lve_value < 80
    assert useful_starter.structural_adjustment == pytest.approx(-8.0)
    assert "elite_no_premium_te_exception" in elite.upside_flags
    assert "te_real_route_floor" in elite.floor_flags
    assert "replaceable_no_premium_te" in useful_starter.risk_flags


def test_te_score_receipts_show_route_target_and_no_premium_suppression() -> None:
    te = score_stats_first_veteran_row(
        _te_row(
            player_id="receipt_te",
            player_name="Receipt TE",
            weighted_recent_lve_ppg_score=76,
            expected_lve_points_score=78,
            lve_projection_value=78,
            route_role=66,
            target_earning_stability=64,
            first_down_td_fit=72,
            efficiency_score=76,
            age_curve=78,
            injury_durability=82,
            te_replacement_level_baseline=69,
        )
    )
    receipts = {
        (contribution.component, contribution.feature_name): contribution
        for contribution in te.contributions
    }

    assert ("win_now_value", "route_role") in receipts
    assert ("win_now_value", "target_earning_stability") in receipts
    assert ("dynasty_hold_value", "route_role") in receipts
    assert ("dynasty_hold_value", "target_earning_stability") in receipts
    assert ("private_lve_value", "te_replacement_level_baseline") in receipts
    assert ("private_lve_value", "te_no_premium_suppression") in receipts
    assert receipts[("dynasty_hold_value", "route_role")].component_contribution > 18
    assert receipts[("dynasty_hold_value", "target_earning_stability")].component_contribution > 14


def test_cross_position_elite_wr_and_rb_stay_top_of_lve_board() -> None:
    scores = score_stats_first_veteran_rows(
        [
            _wr_row(
                player_id="elite_wr_cross",
                player_name="Elite WR Cross",
                weighted_recent_lve_ppg_score=95,
                expected_lve_points_score=95,
                lve_projection_value=95,
                role_security=94,
                target_earning_stability=95,
                route_role=95,
                first_down_td_fit=92,
                efficiency_score=94,
                age_curve=90,
                injury_durability=84,
            ),
            _rb_row(
                player_id="elite_rb_cross",
                player_name="Elite RB Cross",
                weighted_recent_lve_ppg_score=92,
                expected_lve_points_score=94,
                lve_projection_value=94,
                role_security=92,
                workload_earning=92,
                first_down_td_fit=90,
                efficiency_score=90,
                age_curve=94,
                injury_durability=88,
            ),
            _qb_row(
                player_id="lamar_cross",
                player_name="Lamar Cross",
                weighted_recent_lve_ppg_score=94,
                expected_lve_points_score=95,
                lve_projection_value=94,
                role_security=96,
                qb_rushing_profile=98,
                first_down_td_fit=96,
                efficiency_score=88,
                age_curve=83,
                injury_durability=82,
            ),
            _te_row(
                player_id="elite_te_cross",
                player_name="Elite TE Cross",
                weighted_recent_lve_ppg_score=92,
                expected_lve_points_score=91,
                lve_projection_value=91,
                route_role=91,
                target_earning_stability=88,
                first_down_td_fit=88,
                efficiency_score=91,
                age_curve=82,
                injury_durability=84,
            ),
        ]
    )
    top_two = {score.position for score in scores[:2]}

    assert top_two == {"WR", "RB"}
    assert scores[0].lve_lineup_demand_adjustment > 0
    assert scores[1].lve_lineup_demand_adjustment > 0


def test_cross_position_mid_wr_beats_fragile_role_driven_rb() -> None:
    mid_wr = score_stats_first_veteran_row(
        _wr_row(
            player_id="mid_wr_cross",
            player_name="Mid WR Cross",
            weighted_recent_lve_ppg_score=82,
            expected_lve_points_score=83,
            lve_projection_value=83,
            role_security=84,
            target_earning_stability=84,
            route_role=84,
            first_down_td_fit=80,
            efficiency_score=82,
            age_curve=82,
            injury_durability=80,
        )
    )
    fragile_rb = score_stats_first_veteran_row(
        _rb_row(
            player_id="fragile_rb_cross",
            player_name="Fragile RB Cross",
            weighted_recent_lve_ppg_score=88,
            expected_lve_points_score=88,
            lve_projection_value=88,
            role_security=94,
            workload_earning=94,
            first_down_td_fit=90,
            efficiency_score=80,
            age_curve=50,
            injury_durability=52,
        )
    )

    assert fragile_rb.win_now_value > mid_wr.win_now_value
    assert fragile_rb.dynasty_hold_value < mid_wr.dynasty_hold_value
    assert fragile_rb.lve_lineup_demand_adjustment < 0
    assert mid_wr.keeper_score > fragile_rb.keeper_score


def test_cross_position_elite_wr_anchor_beats_good_but_fragile_rb() -> None:
    wr_anchor = score_stats_first_veteran_row(
        _wr_row(
            player_id="wr_anchor_cross_balance",
            player_name="WR Anchor Cross Balance",
            weighted_recent_lve_ppg_score=93,
            expected_lve_points_score=94,
            lve_projection_value=94,
            role_security=93,
            target_earning_stability=94,
            route_role=93,
            first_down_td_fit=90,
            efficiency_score=92,
            age_curve=88,
            injury_durability=82,
        )
    )
    fragile_rb = score_stats_first_veteran_row(
        _rb_row(
            player_id="fragile_good_rb_cross_balance",
            player_name="Fragile Good RB Cross Balance",
            weighted_recent_lve_ppg_score=90,
            expected_lve_points_score=90,
            lve_projection_value=90,
            role_security=91,
            workload_earning=91,
            first_down_td_fit=90,
            efficiency_score=78,
            age_curve=54,
            injury_durability=58,
        )
    )
    wr_receipts = _receipt_map(wr_anchor)
    rb_receipts = _receipt_map(fragile_rb)

    assert wr_anchor.private_lve_value > fragile_rb.private_lve_value
    assert wr_anchor.keeper_score > fragile_rb.keeper_score
    assert "elite_wr_anchor" in wr_anchor.upside_flags
    assert "rb_workload_injury_fragility" in fragile_rb.risk_flags
    assert ("dynasty_hold_value", "target_earning_stability") in wr_receipts
    assert ("dynasty_hold_value", "age_curve") in rb_receipts
    assert ("dynasty_hold_value", "injury_durability") in rb_receipts


def test_cross_position_first_down_fit_cannot_overload_rb_value_by_itself() -> None:
    rb_with_only_chain_fit = score_stats_first_veteran_row(
        _rb_row(
            player_id="chain_only_rb_cross_balance",
            player_name="Chain Only RB Cross Balance",
            weighted_recent_lve_ppg_score=72,
            expected_lve_points_score=73,
            lve_projection_value=73,
            role_security=58,
            workload_earning=56,
            first_down_td_fit=100,
            efficiency_score=72,
            age_curve=84,
            injury_durability=78,
        )
    )
    stable_wr = score_stats_first_veteran_row(
        _wr_row(
            player_id="stable_wr_cross_balance",
            player_name="Stable WR Cross Balance",
            weighted_recent_lve_ppg_score=82,
            expected_lve_points_score=82,
            lve_projection_value=82,
            role_security=82,
            target_earning_stability=82,
            route_role=82,
            first_down_td_fit=78,
            efficiency_score=80,
            age_curve=82,
            injury_durability=80,
        )
    )
    receipts = _receipt_map(rb_with_only_chain_fit)

    assert ("win_now_value", "first_down_td_fit_capped") in receipts
    assert receipts[("win_now_value", "first_down_td_fit_capped")].normalized_score < 75
    assert "committee_risk" in rb_with_only_chain_fit.risk_flags
    assert stable_wr.private_lve_value > rb_with_only_chain_fit.private_lve_value
    assert stable_wr.keeper_score > rb_with_only_chain_fit.keeper_score


def test_cross_position_qb_and_te_suppression_against_lve_flex_demand() -> None:
    solid_wr = score_stats_first_veteran_row(
        _wr_row(
            player_id="solid_wr_cross",
            player_name="Solid WR Cross",
            weighted_recent_lve_ppg_score=82,
            expected_lve_points_score=83,
            lve_projection_value=83,
            role_security=84,
            target_earning_stability=84,
            route_role=84,
            first_down_td_fit=80,
            efficiency_score=82,
            age_curve=82,
            injury_durability=80,
        )
    )
    pocket_qb = score_stats_first_veteran_row(
        _qb_row(
            player_id="pocket_qb_cross",
            player_name="Pocket QB Cross",
            weighted_recent_lve_ppg_score=86,
            expected_lve_points_score=88,
            lve_projection_value=88,
            role_security=92,
            qb_rushing_profile=30,
            first_down_td_fit=30,
            efficiency_score=90,
            age_curve=80,
            injury_durability=86,
        )
    )
    useful_te = score_stats_first_veteran_row(
        _te_row(
            player_id="useful_te_cross",
            player_name="Useful TE Cross",
            weighted_recent_lve_ppg_score=78,
            expected_lve_points_score=79,
            lve_projection_value=79,
            route_role=76,
            target_earning_stability=71,
            first_down_td_fit=74,
            efficiency_score=77,
            age_curve=80,
            injury_durability=84,
        )
    )

    assert pocket_qb.lve_lineup_demand_adjustment < 0
    assert useful_te.lve_lineup_demand_adjustment < 0
    assert solid_wr.keeper_score > pocket_qb.keeper_score
    assert solid_wr.keeper_score > useful_te.keeper_score


def test_stats_first_output_rows_include_overall_position_rank_audit() -> None:
    scores = score_stats_first_veteran_rows(
        [
            _wr_row(player_id="wr_audit_one", player_name="WR Audit One"),
            _wr_row(
                player_id="wr_audit_two",
                player_name="WR Audit Two",
                weighted_recent_lve_ppg_score=78,
                expected_lve_points_score=78,
                lve_projection_value=78,
                role_security=80,
                target_earning_stability=80,
                route_role=80,
            ),
            _rb_row(
                player_id="rb_audit_one",
                player_name="RB Audit One",
                weighted_recent_lve_ppg_score=80,
                expected_lve_points_score=80,
                lve_projection_value=80,
                role_security=80,
                workload_earning=80,
                first_down_td_fit=80,
                efficiency_score=80,
                age_curve=80,
                injury_durability=80,
            ),
        ]
    )
    output = stats_first_output_rows(scores, computed_at="2026-08-01T00:00:00Z")

    assert [row["overall_rank"] for row in output] == [1, 2, 3]
    assert [row["board_rank"] for row in output] == [1, 2, 3]
    assert {row["position_rank_label"] for row in output} == {"WR1", "WR2", "RB1"}
    assert all(
        "sort=keeper_score_desc|private_lve_value_desc" in row["rank_audit"]
        for row in output
    )
    assert all("replacement_baseline=" in row["rank_audit"] for row in output)
    assert all("lineup_adjustment=" in row["rank_audit"] for row in output)
    assert all("market_edge_score" in row for row in output)
    assert all("market_edge_label" in row for row in output)
    assert all("market_trade_value" in row for row in output)


def test_stats_first_output_rows_include_year_specific_lifecycle_labels() -> None:
    scores = score_stats_first_veteran_rows(
        [
            _wr_row(
                player_id="year_one_wr",
                player_name="Year One WR",
            )
            | {
                "draft_year": "2025",
                "draft_round": "1",
                "draft_ovr": "25",
            },
            _wr_row(
                player_id="year_two_wr",
                player_name="Year Two WR",
            )
            | {
                "draft_year": "2024",
                "draft_round": "1",
                "draft_ovr": "25",
            },
            _wr_row(
                player_id="year_three_wr",
                player_name="Year Three WR",
            )
            | {
                "draft_year": "2023",
                "draft_round": "1",
                "draft_ovr": "25",
            },
            _wr_row(
                player_id="established_wr",
                player_name="Established WR",
            )
            | {
                "draft_year": "2022",
                "draft_round": "1",
                "draft_ovr": "25",
            },
        ]
    )

    output = {
        row["player_id"]: row
        for row in stats_first_output_rows(scores, computed_at="2026-08-01T00:00:00Z")
    }

    assert output["year_one_wr"]["asset_lifecycle"] == "year_one_nfl_bridge"
    assert output["year_one_wr"]["asset_lifecycle_label"] == "Year-One NFL Bridge"
    assert output["year_two_wr"]["asset_lifecycle"] == "year_two_nfl_bridge"
    assert output["year_two_wr"]["asset_lifecycle_label"] == "Year-Two NFL Bridge"
    assert output["year_three_wr"]["asset_lifecycle"] == "year_three_nfl_bridge"
    assert output["year_three_wr"]["asset_lifecycle_label"] == "Year-Three NFL Bridge"
    assert output["established_wr"]["asset_lifecycle"] == "established_veteran"
    assert output["established_wr"]["asset_lifecycle_label"] == "Established Veteran"


def test_named_sanity_kyren_role_spike_does_not_rank_over_bijan_gibbs_or_jeanty() -> None:
    kyren = score_stats_first_veteran_row(
        _rb_row(
            player_id="kyren_williams",
            player_name="Kyren Williams",
            weighted_recent_lve_ppg_score=94,
            expected_lve_points_score=93,
            lve_projection_value=91,
            role_security=96,
            workload_earning=95,
            first_down_td_fit=92,
            efficiency_score=82,
            age_curve=56,
            injury_durability=58,
        )
    )
    anchor_backs = [
        score_stats_first_veteran_row(
            _rb_row(
                player_id="bijan_robinson",
                player_name="Bijan Robinson",
                weighted_recent_lve_ppg_score=91,
                expected_lve_points_score=94,
                lve_projection_value=94,
                role_security=92,
                workload_earning=92,
                first_down_td_fit=90,
                efficiency_score=90,
                age_curve=94,
                injury_durability=88,
            )
        ),
        score_stats_first_veteran_row(
            _rb_row(
                player_id="jahmyr_gibbs",
                player_name="Jahmyr Gibbs",
                weighted_recent_lve_ppg_score=90,
                expected_lve_points_score=92,
                lve_projection_value=92,
                role_security=89,
                workload_earning=86,
                first_down_td_fit=84,
                efficiency_score=92,
                age_curve=93,
                injury_durability=86,
            )
        ),
        score_stats_first_veteran_row(
            _rb_row(
                player_id="ashton_jeanty",
                player_name="Ashton Jeanty",
                weighted_recent_lve_ppg_score=84,
                expected_lve_points_score=88,
                lve_projection_value=88,
                role_security=81,
                workload_earning=86,
                first_down_td_fit=88,
                efficiency_score=88,
                age_curve=97,
                injury_durability=85,
            )
        ),
    ]
    receipts = _receipt_map(kyren)

    assert kyren.win_now_value >= 90
    assert all(kyren.dynasty_hold_value < back.dynasty_hold_value for back in anchor_backs)
    assert all(kyren.private_lve_value < back.private_lve_value for back in anchor_backs)
    assert all(kyren.keeper_score < back.keeper_score for back in anchor_backs)
    assert "rb_workload_injury_fragility" in kyren.risk_flags
    assert ("dynasty_hold_value", "age_curve") in receipts
    assert ("dynasty_hold_value", "injury_durability") in receipts
    assert ("dynasty_hold_value", "lve_structural_formula_adjustment") in receipts


def test_named_sanity_jsn_beats_tee_on_target_earning_production_and_age_receipts() -> None:
    jsn = score_stats_first_veteran_row(
        _wr_row(
            player_id="jaxon_smith_njigba",
            player_name="Jaxon Smith-Njigba",
            weighted_recent_lve_ppg_score=96,
            expected_lve_points_score=94,
            lve_projection_value=93,
            role_security=94,
            target_earning_stability=96,
            route_role=93,
            first_down_td_fit=92,
            efficiency_score=94,
            age_curve=90,
            injury_durability=84,
        )
    )
    tee = score_stats_first_veteran_row(
        _wr_row(
            player_id="tee_higgins",
            player_name="Tee Higgins",
            weighted_recent_lve_ppg_score=84,
            expected_lve_points_score=82,
            lve_projection_value=85,
            role_security=82,
            target_earning_stability=76,
            route_role=82,
            first_down_td_fit=82,
            efficiency_score=84,
            age_curve=72,
            injury_durability=78,
            market_liquidity=95,
        )
    )
    receipts = _receipt_map(jsn)

    assert jsn.win_now_value > tee.win_now_value
    assert jsn.dynasty_hold_value > tee.dynasty_hold_value
    assert jsn.keeper_score > tee.keeper_score
    assert ("win_now_value", "target_earning_stability") in receipts
    assert ("win_now_value", "weighted_recent_lve_ppg_score") in receipts
    assert ("dynasty_hold_value", "age_curve") in receipts


def test_named_sanity_chase_brown_beats_luther_unless_luther_is_marked_review_only() -> None:
    chase = score_stats_first_veteran_row(
        _rb_row(
            player_id="chase_brown",
            player_name="Chase Brown",
            weighted_recent_lve_ppg_score=80,
            expected_lve_points_score=82,
            lve_projection_value=82,
            role_security=83,
            workload_earning=82,
            first_down_td_fit=82,
            efficiency_score=80,
            age_curve=78,
            injury_durability=74,
        )
    )
    luther_row = _wr_row(
        player_id="luther_burden",
        player_name="Luther Burden",
        weighted_recent_lve_ppg_score=52,
        expected_lve_points_score=68,
        lve_projection_value=76,
        role_security=72,
        target_earning_stability=74,
        route_role=76,
        first_down_td_fit=76,
        efficiency_score=78,
        age_curve=96,
        injury_durability=84,
        market_liquidity=96,
    )
    luther_row["confidence"] = "62"
    luther_row["warnings"] = "missing_lve_scoring_history|rookie_transition_projection_only"
    luther = score_stats_first_veteran_row(luther_row)
    receipts = _receipt_map(luther)

    assert chase.keeper_score > luther.keeper_score
    assert luther.warning_status == "review_needed"
    assert "low_confidence" in luther.risk_flags
    assert "missing_lve_scoring_history" in luther.warning_reasons
    assert ("win_now_value", "weighted_recent_lve_ppg_score") in receipts
    assert ("dynasty_hold_value", "target_earning_stability") in receipts


def test_named_sanity_btj_beats_luther_when_proven_nfl_production_is_visible() -> None:
    btj = score_stats_first_veteran_row(
        _wr_row(
            player_id="brian_thomas",
            player_name="Brian Thomas",
            weighted_recent_lve_ppg_score=91,
            expected_lve_points_score=90,
            lve_projection_value=90,
            role_security=91,
            target_earning_stability=87,
            route_role=90,
            first_down_td_fit=89,
            efficiency_score=90,
            age_curve=91,
            injury_durability=86,
        )
    )
    luther = score_stats_first_veteran_row(
        _wr_row(
            player_id="luther_burden",
            player_name="Luther Burden",
            weighted_recent_lve_ppg_score=62,
            expected_lve_points_score=70,
            lve_projection_value=77,
            role_security=76,
            target_earning_stability=74,
            route_role=76,
            first_down_td_fit=76,
            efficiency_score=78,
            age_curve=96,
            injury_durability=84,
            market_liquidity=96,
        )
    )
    receipts = _receipt_map(btj)

    assert btj.win_now_value > luther.win_now_value
    assert btj.dynasty_hold_value > luther.dynasty_hold_value
    assert btj.keeper_score > luther.keeper_score
    assert ("win_now_value", "weighted_recent_lve_ppg_score") in receipts
    assert ("win_now_value", "target_earning_stability") in receipts
    assert ("dynasty_hold_value", "production_stability") in receipts


def test_named_sanity_elite_wr_group_requires_target_route_and_production_receipts() -> None:
    anchors = score_stats_first_veteran_rows(
        [
            _wr_row(
                player_id="jamarr_chase",
                player_name="Ja'Marr Chase",
                weighted_recent_lve_ppg_score=96,
                expected_lve_points_score=95,
                lve_projection_value=95,
                role_security=94,
                target_earning_stability=96,
                route_role=95,
                first_down_td_fit=94,
                efficiency_score=95,
                age_curve=88,
                injury_durability=85,
            ),
            _wr_row(
                player_id="justin_jefferson",
                player_name="Justin Jefferson",
                weighted_recent_lve_ppg_score=94,
                expected_lve_points_score=95,
                lve_projection_value=95,
                role_security=94,
                target_earning_stability=95,
                route_role=96,
                first_down_td_fit=91,
                efficiency_score=96,
                age_curve=86,
                injury_durability=82,
            ),
            _wr_row(
                player_id="puka_nacua",
                player_name="Puka Nacua",
                weighted_recent_lve_ppg_score=94,
                expected_lve_points_score=93,
                lve_projection_value=93,
                role_security=93,
                target_earning_stability=94,
                route_role=94,
                first_down_td_fit=92,
                efficiency_score=93,
                age_curve=91,
                injury_durability=80,
            ),
        ]
    )

    assert all(score.private_lve_value >= 90 for score in anchors)
    assert all("elite_wr_anchor" in score.upside_flags for score in anchors)
    for score in anchors:
        receipts = _receipt_map(score)
        assert ("win_now_value", "target_earning_stability") in receipts
        assert ("win_now_value", "route_role") in receipts
        assert ("win_now_value", "weighted_recent_lve_ppg_score") in receipts


def test_named_sanity_old_rb_cliff_gets_review_even_with_hot_recent_box_score() -> None:
    old_hot_rb = score_stats_first_veteran_row(
        _rb_row(
            player_id="old_hot_rb",
            player_name="Old Hot RB",
            weighted_recent_lve_ppg_score=92,
            expected_lve_points_score=91,
            lve_projection_value=89,
            role_security=92,
            workload_earning=91,
            first_down_td_fit=90,
            efficiency_score=79,
            age_curve=38,
            injury_durability=55,
        )
    )
    stable_prime_rb = score_stats_first_veteran_row(
        _rb_row(
            player_id="stable_prime_rb",
            player_name="Stable Prime RB",
            weighted_recent_lve_ppg_score=84,
            expected_lve_points_score=86,
            lve_projection_value=86,
            role_security=84,
            workload_earning=84,
            first_down_td_fit=84,
            efficiency_score=84,
            age_curve=86,
            injury_durability=82,
        )
    )
    receipts = _receipt_map(old_hot_rb)

    assert old_hot_rb.win_now_value > stable_prime_rb.win_now_value
    assert old_hot_rb.dynasty_hold_value < stable_prime_rb.dynasty_hold_value
    assert old_hot_rb.keeper_score < stable_prime_rb.keeper_score
    assert old_hot_rb.warning_status == "model_warning"
    assert "rb_weak_age_window" in old_hot_rb.risk_flags
    assert "injury_risk" in old_hot_rb.risk_flags
    assert "rb_weak_age_window" in old_hot_rb.warning_reasons
    assert "injury_risk" in old_hot_rb.warning_reasons
    assert ("dynasty_hold_value", "age_curve") in receipts
    assert ("dynasty_hold_value", "injury_durability") in receipts
    assert ("private_lve_value", "rb_dynasty_cap") in receipts


def test_named_sanity_low_confidence_stat_spike_is_review_needed_not_ready() -> None:
    spike_row = _wr_row(
        player_id="low_confidence_stat_spike",
        player_name="Low Confidence Stat Spike",
        weighted_recent_lve_ppg_score=93,
        expected_lve_points_score=74,
        lve_projection_value=76,
        role_security=66,
        target_earning_stability=64,
        route_role=65,
        first_down_td_fit=88,
        efficiency_score=92,
        age_curve=80,
        injury_durability=78,
        market_liquidity=88,
    )
    spike_row["confidence"] = "58"
    spike_row["warnings"] = "small_sample_stat_spike"
    score = score_stats_first_veteran_row(spike_row)
    receipts = _receipt_map(score)

    assert score.warning_status == "review_needed"
    assert "low_confidence" in score.risk_flags
    assert "small_sample_stat_spike" in score.warning_reasons
    assert ("win_now_value", "weighted_recent_lve_ppg_score") in receipts
    assert ("win_now_value", "expected_lve_points_score") in receipts
    assert ("dynasty_hold_value", "production_stability") in receipts


def test_stats_first_csv_scoring_and_output_rows(tmp_path: Path) -> None:
    path = tmp_path / "lve_normalized_veteran_features.csv"
    rows = [_wr_row(player_id="wr_one"), _base_row(position="RB", player_id="rb_one")]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    scores = score_stats_first_veteran_csv(path)
    output = stats_first_output_rows(scores, computed_at="2026-08-01T00:00:00Z")

    assert scores[0].keeper_score >= scores[1].keeper_score
    assert output[0]["model_version"] == STATS_FIRST_MODEL_VERSION
    assert output[0]["computed_at"] == "2026-08-01T00:00:00Z"
    assert "private_lve_value" in output[0]


def test_score_stats_first_rows_uses_stable_sort() -> None:
    rows = [
        _wr_row(player_id="b_player", player_name="B Player"),
        _wr_row(player_id="a_player", player_name="A Player"),
    ]

    scores = score_stats_first_veteran_rows(rows)

    assert [score.player_name for score in scores] == ["A Player", "B Player"]


def _receipt_map(score: object) -> dict[tuple[str, str], object]:
    return {
        (contribution.component, contribution.feature_name): contribution
        for contribution in score.contributions
    }


def _qb_row(
    *,
    player_id: str,
    player_name: str,
    weighted_recent_lve_ppg_score: float,
    expected_lve_points_score: float,
    lve_projection_value: float,
    role_security: float,
    qb_rushing_profile: float,
    first_down_td_fit: float,
    efficiency_score: float,
    age_curve: float,
    injury_durability: float,
    qb_replacement_level_baseline: float = 76,
    market_liquidity: float = 50,
) -> dict[str, object]:
    row = _base_row(
        position="QB",
        player_id=player_id,
        player_name=player_name,
        weighted_recent_lve_ppg_score=weighted_recent_lve_ppg_score,
        expected_lve_points_score=expected_lve_points_score,
        lve_projection_value=lve_projection_value,
        role_security=role_security,
        first_down_td_fit=first_down_td_fit,
        age_curve=age_curve,
        injury_durability=injury_durability,
        market_liquidity=market_liquidity,
    )
    row["qb_rushing_profile"] = str(qb_rushing_profile)
    row["efficiency_score"] = str(efficiency_score)
    row["qb_replacement_level_baseline"] = str(qb_replacement_level_baseline)
    return row


def _wr_row(
    *,
    player_id: str = "wr_solid",
    player_name: str = "Solid WR",
    weighted_recent_lve_ppg_score: float = 82,
    expected_lve_points_score: float = 83,
    lve_projection_value: float = 82,
    role_security: float = 84,
    workload_earning: float = 55,
    target_earning_stability: float = 82,
    route_role: float = 84,
    first_down_td_fit: float = 80,
    efficiency_score: float | None = None,
    age_curve: float = 80,
    injury_durability: float = 80,
    market_liquidity: float = 50,
) -> dict[str, object]:
    row = _base_row(
        position="WR",
        player_id=player_id,
        player_name=player_name,
        weighted_recent_lve_ppg_score=weighted_recent_lve_ppg_score,
        expected_lve_points_score=expected_lve_points_score,
        lve_projection_value=lve_projection_value,
        role_security=role_security,
        workload_earning=workload_earning,
        target_earning_stability=target_earning_stability,
        route_role=route_role,
        first_down_td_fit=first_down_td_fit,
        age_curve=age_curve,
        injury_durability=injury_durability,
        market_liquidity=market_liquidity,
    )
    if efficiency_score is not None:
        row["efficiency_score"] = str(efficiency_score)
    return row


def _rb_row(
    *,
    player_id: str,
    player_name: str,
    weighted_recent_lve_ppg_score: float,
    expected_lve_points_score: float,
    lve_projection_value: float,
    role_security: float,
    workload_earning: float,
    first_down_td_fit: float,
    efficiency_score: float,
    age_curve: float,
    injury_durability: float,
) -> dict[str, object]:
    row = _base_row(
        position="RB",
        player_id=player_id,
        player_name=player_name,
        weighted_recent_lve_ppg_score=weighted_recent_lve_ppg_score,
        expected_lve_points_score=expected_lve_points_score,
        lve_projection_value=lve_projection_value,
        role_security=role_security,
        workload_earning=workload_earning,
        first_down_td_fit=first_down_td_fit,
        age_curve=age_curve,
        injury_durability=injury_durability,
    )
    row["efficiency_score"] = str(efficiency_score)
    return row


def _te_row(
    *,
    player_id: str,
    player_name: str,
    weighted_recent_lve_ppg_score: float,
    expected_lve_points_score: float,
    lve_projection_value: float,
    route_role: float,
    target_earning_stability: float,
    first_down_td_fit: float,
    efficiency_score: float,
    age_curve: float,
    injury_durability: float,
    te_replacement_level_baseline: float = 69,
    market_liquidity: float = 50,
) -> dict[str, object]:
    row = _base_row(
        position="TE",
        player_id=player_id,
        player_name=player_name,
        weighted_recent_lve_ppg_score=weighted_recent_lve_ppg_score,
        expected_lve_points_score=expected_lve_points_score,
        lve_projection_value=lve_projection_value,
        role_security=route_role,
        target_earning_stability=target_earning_stability,
        route_role=route_role,
        first_down_td_fit=first_down_td_fit,
        age_curve=age_curve,
        injury_durability=injury_durability,
        market_liquidity=market_liquidity,
    )
    row["efficiency_score"] = str(efficiency_score)
    row["te_replacement_level_baseline"] = str(te_replacement_level_baseline)
    return row


def _base_row(
    *,
    position: str,
    player_id: str,
    player_name: str = "Fixture Player",
    weighted_recent_lve_ppg_score: float = 80,
    expected_lve_points_score: float = 80,
    lve_projection_value: float = 80,
    role_security: float = 80,
    workload_earning: float = 80,
    target_earning_stability: float = 80,
    route_role: float = 80,
    first_down_td_fit: float = 80,
    age_curve: float = 80,
    injury_durability: float = 80,
    market_liquidity: float = 50,
) -> dict[str, object]:
    return {
        "season": "2026",
        "as_of_week": "18",
        "player_id": player_id,
        "gsis_id": player_id,
        "sleeper_id": "",
        "player_name": player_name,
        "position": position,
        "team": "SF",
        "weighted_recent_lve_ppg_score": str(weighted_recent_lve_ppg_score),
        "expected_lve_points_score": str(expected_lve_points_score),
        "lve_projection_value": str(lve_projection_value),
        "role_security": str(role_security),
        "workload_earning": str(workload_earning),
        "target_earning_stability": str(target_earning_stability),
        "route_role": str(route_role),
        "first_down_td_fit": str(first_down_td_fit),
        "age_curve": str(age_curve),
        "injury_durability": str(injury_durability),
        "private_stat_value": "",
        "confidence": "84",
        "missing_data_penalty": "0",
        "warnings": "",
        "source_version": "fixture",
        "computed_at": "2026-08-01T00:00:00Z",
        "market_liquidity": str(market_liquidity),
    }
