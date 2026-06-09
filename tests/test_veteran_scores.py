from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from src.models.veteran_scores import (
    VeteranInput,
    VeteranPosition,
    confidence_score,
    league_rank_release_adjustment,
    league_rank_signal_score,
    missing_data_penalty,
    score_veteran,
    top_five_release_pressure,
)
from src.services.veteran_model_service import (
    generated_model_output_rows,
    run_veteran_model_from_dir,
    write_generated_model_outputs,
)

SAMPLE_DIR = Path("sample_data/veteran_model_v1")


def test_sample_veteran_model_run_has_expected_golden_outputs() -> None:
    run = run_veteran_model_from_dir(SAMPLE_DIR)
    scores = {score.player_id: score for score in run.scores}

    assert run.model_version == "veteran_lve_v1_3_0"
    assert len(scores) == 12

    assert scores["puka_nacua"].veteran_base_value == pytest.approx(91.97)
    assert scores["puka_nacua"].horizon_retention_score == pytest.approx(87.15)
    assert scores["puka_nacua"].keeper_score == pytest.approx(93.18)
    assert scores["puka_nacua"].drop_candidate_score == pytest.approx(9.63)
    assert scores["puka_nacua"].trade_value == pytest.approx(95.75)
    assert scores["puka_nacua"].warning_status == "ready"
    assert scores["puka_nacua"].structural_adjustment == pytest.approx(2.0)
    assert "elite_lve_value" in scores["puka_nacua"].upside_flags

    assert scores["lamar_jackson"].veteran_base_value == pytest.approx(88.56)
    assert scores["lamar_jackson"].keeper_score == pytest.approx(85.59)
    assert scores["lamar_jackson"].structural_adjustment == pytest.approx(-3.0)
    assert "elite_qb_edge" in scores["lamar_jackson"].upside_flags

    assert scores["patrick_mahomes"].structural_adjustment == pytest.approx(-10.0)

    assert scores["derrick_henry"].trade_value == pytest.approx(78.29)
    assert "aging_rb" in scores["derrick_henry"].risk_flags
    assert "first_down_td_engine" in scores["derrick_henry"].upside_flags

    assert scores["trey_mcbride"].structural_adjustment == pytest.approx(-2.0)
    assert "difference_making_te_routes" in scores["trey_mcbride"].upside_flags

    assert scores["travis_kelce"].veteran_base_value == pytest.approx(60.38)
    assert scores["travis_kelce"].drop_candidate_score == pytest.approx(47.5)
    assert scores["travis_kelce"].trade_value == pytest.approx(57.21)
    assert scores["travis_kelce"].warning_status == "model_warning"
    assert scores["travis_kelce"].structural_adjustment == pytest.approx(-8.0)
    assert "blocking_dependency_risk" in scores["travis_kelce"].risk_flags
    assert "replaceable_no_premium_te" in scores["travis_kelce"].risk_flags


def test_league_rank_is_signal_and_top_five_release_pressure_not_private_value() -> None:
    assert league_rank_signal_score(1) == pytest.approx(100.0)
    assert league_rank_signal_score(400) == pytest.approx(25.0)
    assert league_rank_signal_score(None) == pytest.approx(50.0)

    assert top_five_release_pressure(True, 60) == pytest.approx(10.0)
    assert top_five_release_pressure(True, 96) == pytest.approx(1.0)
    assert top_five_release_pressure(False, 60) == pytest.approx(0.0)
    assert league_rank_release_adjustment(True, 60) == pytest.approx(0.0)
    assert league_rank_release_adjustment(False, 60) == pytest.approx(0.0)


def test_league_rank_does_not_change_private_keeper_value() -> None:
    high_rank = score_veteran(
        _veteran(VeteranPosition.WR, _wr_feature_set(), league_rank=1, is_top_five=True)
    )
    low_rank = score_veteran(
        _veteran(VeteranPosition.WR, _wr_feature_set(), league_rank=250, is_top_five=True)
    )

    assert high_rank.league_rank_signal > low_rank.league_rank_signal
    assert high_rank.veteran_base_value == low_rank.veteran_base_value
    assert high_rank.horizon_retention_score == low_rank.horizon_retention_score
    assert high_rank.keeper_score == low_rank.keeper_score


def test_forced_release_pressure_does_not_change_drop_candidate_score() -> None:
    top_five = score_veteran(
        _veteran(VeteranPosition.WR, _wr_feature_set(), league_rank=1, is_top_five=True)
    )
    non_top_five = score_veteran(
        _veteran(VeteranPosition.WR, _wr_feature_set(), league_rank=250, is_top_five=False)
    )

    assert top_five.top_five_release_pressure > non_top_five.top_five_release_pressure
    assert top_five.league_rank_adjustment == pytest.approx(0.0)
    assert top_five.veteran_base_value == non_top_five.veteran_base_value
    assert top_five.keeper_score == non_top_five.keeper_score
    assert top_five.drop_candidate_score == non_top_five.drop_candidate_score


def test_market_liquidity_only_changes_trade_layer_not_private_value() -> None:
    low_market_features = _wr_feature_set() | {"market_liquidity": 20}
    high_market_features = _wr_feature_set() | {"market_liquidity": 95}

    low_market = score_veteran(_veteran(VeteranPosition.WR, low_market_features))
    high_market = score_veteran(_veteran(VeteranPosition.WR, high_market_features))

    assert low_market.veteran_base_value == high_market.veteran_base_value
    assert low_market.horizon_retention_score == high_market.horizon_retention_score
    assert low_market.keeper_score == high_market.keeper_score
    assert low_market.drop_candidate_score == high_market.drop_candidate_score
    assert high_market.trade_value > low_market.trade_value


def test_generated_war_score_caps_trade_liquidity_drift() -> None:
    low_market = score_veteran(
        _veteran(VeteranPosition.WR, _wr_feature_set() | {"market_liquidity": 0})
    )
    high_market = score_veteran(
        _veteran(VeteranPosition.WR, _wr_feature_set() | {"market_liquidity": 100})
    )

    rows = generated_model_output_rows(
        (low_market, high_market),
        snapshot_date="2026-05-05",
        computed_at="2026-05-05T12:00:00+00:00",
    )
    low_war = float(rows[0]["war_score"])
    high_war = float(rows[1]["war_score"])

    assert low_market.keeper_score == high_market.keeper_score
    assert high_market.trade_value > low_market.trade_value
    assert high_war - low_war <= 8.0
    assert float(rows[0]["market_score"]) == pytest.approx(0.0)
    assert float(rows[1]["market_score"]) == pytest.approx(100.0)
    assert float(rows[0]["market_edge_score"]) > float(rows[1]["market_edge_score"])


def test_explainable_base_contributions_reconcile_with_adjustments() -> None:
    score = next(
        score
        for score in run_veteran_model_from_dir(SAMPLE_DIR).scores
        if score.player_id == "puka_nacua"
    )
    base_contribution_total = sum(
        row.component_contribution
        for row in score.contributions
        if row.component == "veteran_base_value"
    )

    assert base_contribution_total == pytest.approx(score.veteran_base_value, abs=0.01)


def test_missing_core_input_neutralizes_score_and_reduces_confidence() -> None:
    veteran = _veteran(
        VeteranPosition.WR,
        {
            "lve_projection_value": None,
            "role_security": 80,
            "target_earning_stability": 82,
            "age_curve": 75,
            "market_liquidity": 70,
        },
    )
    score = score_veteran(veteran)

    assert score.veteran_base_value < 80
    assert score.missing_data_penalty == pytest.approx(2.8)
    assert score.confidence_score < 83
    assert score.warning_status == "data_warning"
    assert "data_warning_missing_inputs" in score.warning_reasons


def test_user_override_penalizes_confidence_but_keeps_score_auditable() -> None:
    base = _veteran(
        VeteranPosition.RB,
        {
            "lve_projection_value": 82,
            "role_security": 80,
            "first_down_td_fit": 86,
            "age_curve": 78,
            "injury_durability": 76,
        },
    )
    overridden = _veteran(
        VeteranPosition.RB,
        base.features,
        user_overrides={"first_down_td_fit": True},
    )

    assert score_veteran(overridden).veteran_base_value == score_veteran(
        base
    ).veteran_base_value
    assert score_veteran(overridden).confidence_score == pytest.approx(
        score_veteran(base).confidence_score - 3.0
    )


def test_qb_and_te_replacement_rules_suppress_non_elite_profiles() -> None:
    qb = score_veteran(
        _veteran(
            VeteranPosition.QB,
            {
                "lve_projection_value": 82,
                "role_security": 84,
                "market_liquidity": 80,
                "age_curve": 76,
                "position_replaceability": 62,
            },
        )
    )
    te = score_veteran(
        _veteran(
            VeteranPosition.TE,
            {
                "lve_projection_value": 78,
                "route_share_stability": 76,
                "role_security": 74,
                "position_replaceability": 62,
                "age_curve": 70,
            },
        )
    )

    assert qb.veteran_base_value < 80
    assert qb.trade_value < 76
    assert "replaceable_1qb_profile" in qb.risk_flags
    assert te.veteran_base_value < 75
    assert te.trade_value < 70
    assert "replaceable_no_premium_te" in te.risk_flags


def test_no_ppr_satellite_rb_gets_risk_flags_and_lower_fit() -> None:
    satellite = score_veteran(
        _veteran(
            VeteranPosition.RB,
            {
                "lve_projection_value": 72,
                "touch_share": 52,
                "role_security": 52,
                "high_value_touches": 42,
                "goal_line_short_yardage_role": 34,
                "receiving_role_no_ppr_adjusted": 88,
                "rush_efficiency_creation": 68,
                "first_down_conversion_profile": 45,
                "offense_environment_line": 70,
                "age_curve": 78,
                "injury_durability": 74,
            },
        )
    )

    assert satellite.lve_format_fit < 55
    assert "committee_risk" in satellite.risk_flags
    assert "goal_line_fragility" in satellite.risk_flags
    assert "no_ppr_satellite" in satellite.risk_flags


def test_elite_lve_rb_interleaves_with_elite_wr_after_calibration() -> None:
    elite_rb = score_veteran(
        _veteran(
            VeteranPosition.RB,
            {
                "lve_projection_value": 91,
                "touch_share": 92,
                "role_security": 91,
                "high_value_touches": 91,
                "goal_line_short_yardage_role": 90,
                "receiving_role_no_ppr_adjusted": 82,
                "rush_efficiency_creation": 89,
                "first_down_conversion_profile": 91,
                "offense_environment_line": 84,
                "age_curve": 88,
                "injury_durability": 82,
            },
        )
    )
    elite_wr = score_veteran(
        _veteran(
            VeteranPosition.WR,
            {
                "lve_projection_value": 92,
                "route_participation": 92,
                "target_share": 91,
                "targets_per_route_run": 90,
                "yards_per_route_run": 91,
                "first_downs_per_route": 89,
                "get_open_role_robustness": 90,
                "td_area_air_yards_role": 86,
                "offense_environment": 84,
                "role_security": 92,
                "age_curve": 88,
                "injury_durability": 82,
                "market_liquidity": 90,
            },
        )
    )

    assert elite_rb.structural_adjustment == pytest.approx(2.5)
    assert elite_wr.structural_adjustment == pytest.approx(2.0)
    assert abs(elite_wr.keeper_score - elite_rb.keeper_score) <= 3.0


def test_solid_wr_still_beats_speculative_rb_in_lve() -> None:
    solid_wr = score_veteran(
        _veteran(
            VeteranPosition.WR,
            {
                "lve_projection_value": 82,
                "route_participation": 84,
                "target_share": 82,
                "targets_per_route_run": 81,
                "yards_per_route_run": 82,
                "first_downs_per_route": 80,
                "get_open_role_robustness": 82,
                "td_area_air_yards_role": 76,
                "offense_environment": 75,
                "role_security": 84,
                "age_curve": 80,
                "injury_durability": 80,
                "market_liquidity": 78,
            },
        )
    )
    speculative_rb = score_veteran(
        _veteran(
            VeteranPosition.RB,
            {
                "lve_projection_value": 76,
                "touch_share": 61,
                "role_security": 62,
                "high_value_touches": 58,
                "goal_line_short_yardage_role": 52,
                "receiving_role_no_ppr_adjusted": 74,
                "rush_efficiency_creation": 78,
                "first_down_conversion_profile": 57,
                "offense_environment_line": 78,
                "age_curve": 86,
                "injury_durability": 76,
            },
        )
    )

    assert solid_wr.keeper_score > speculative_rb.keeper_score
    assert speculative_rb.structural_adjustment == pytest.approx(0.0)
    assert "committee_risk" not in solid_wr.risk_flags


def test_route_earning_te_clears_no_premium_exception_gate() -> None:
    elite_te = score_veteran(
        _veteran(
            VeteranPosition.TE,
            {
                "lve_projection_value": 91,
                "route_participation": 92,
                "target_earning": 94,
                "yards_per_route_run": 90,
                "blocking_suppression_inverse": 86,
                "td_area_adot_role": 86,
                "first_down_profile": 91,
                "route_share_stability": 92,
                "position_replaceability": 88,
                "role_security": 89,
                "age_curve": 78,
                "injury_durability": 84,
                "offense_environment": 80,
            },
        )
    )

    assert elite_te.veteran_base_value >= 88
    assert elite_te.structural_adjustment == pytest.approx(-2.0)
    assert "difference_making_te_routes" in elite_te.upside_flags


def test_supplied_future_candidate_features_override_compatibility_fallbacks(
    tmp_path: Path,
) -> None:
    pack = tmp_path / "veteran_model_v1"
    shutil.copytree(SAMPLE_DIR, pack)
    score_path = pack / "veteran_feature_scores.csv"
    rows = _read_csv(score_path)
    for row in rows:
        if row["player_id"] == "puka_nacua" and row["feature_name"] == "route_participation":
            row["normalized_score"] = "40"
            break
    _write_csv(score_path, rows)

    baseline = next(
        score
        for score in run_veteran_model_from_dir(SAMPLE_DIR).scores
        if score.player_id == "puka_nacua"
    )
    changed = next(
        score
        for score in run_veteran_model_from_dir(pack).scores
        if score.player_id == "puka_nacua"
    )

    assert changed.veteran_base_value < baseline.veteran_base_value
    assert any(
        contribution.feature_name == "route_participation"
        and contribution.normalized_score == 40
        for contribution in changed.contributions
    )


def test_write_generated_veteran_outputs_includes_b2_fields(tmp_path: Path) -> None:
    run = run_veteran_model_from_dir(SAMPLE_DIR)
    output = tmp_path / "veteran_model_outputs.csv"

    write_generated_model_outputs(
        output,
        run.scores,
        snapshot_date="2026-05-05",
        computed_at="2026-05-05T12:00:00+00:00",
    )
    rows = _read_csv(output)
    puka = next(row for row in rows if row["player_id"] == "puka_nacua")

    assert puka["model_version"] == "veteran_lve_v1_3_0"
    assert puka["veteran_base_value"] == "91.97"
    assert puka["horizon_retention_score"] == "87.15"
    assert puka["lve_format_fit"] == "93.7"
    assert puka["structural_adjustment"] == "2.0"
    assert puka["warning_status"] == "ready"
    assert puka["warning_reasons"] == ""
    assert puka["risk_flags"] == ""
    assert "strong_keeper" in puka["floor_flags"]
    assert "Neutral placeholder" not in puka["notes"]


def test_missing_data_penalty_and_confidence_are_bounded() -> None:
    veteran = _veteran(
        VeteranPosition.RB,
        {
            "lve_projection_value": None,
            "role_security": None,
            "first_down_td_fit": None,
            "age_curve": None,
            "injury_durability": None,
        },
    )

    assert missing_data_penalty(veteran) == pytest.approx(8.0)
    assert confidence_score(veteran, missing_data_penalty(veteran)) == pytest.approx(29.5)
    score = score_veteran(veteran)
    assert score.warning_status == "blocking"
    assert "blocking_low_confidence" in score.warning_reasons
    assert "review_needed_missing_core_inputs" in score.warning_reasons


def test_estimated_private_features_trigger_review_without_changing_value() -> None:
    features = _wr_feature_set()
    derived = score_veteran(_veteran(VeteranPosition.WR, features))
    estimated = score_veteran(
        VeteranInput(
            player_id="fixture_estimated",
            player_name="Fixture Estimated",
            position=VeteranPosition.WR,
            age=22.0,
            league_rank=50,
            is_league_rank_top5=False,
            features=features,
            missing_penalties={feature_name: 8.0 for feature_name in features},
            source_reliability={feature_name: 80.0 for feature_name in features},
            source_freshness={feature_name: 90.0 for feature_name in features},
            source_confidence={feature_name: "estimated" for feature_name in features},
            user_overrides={feature_name: False for feature_name in features},
        )
    )

    assert estimated.veteran_base_value == derived.veteran_base_value
    assert estimated.horizon_retention_score == derived.horizon_retention_score
    assert estimated.lve_format_fit == derived.lve_format_fit
    assert estimated.keeper_score < derived.keeper_score
    assert derived.keeper_score - estimated.keeper_score < 2.0
    assert estimated.trade_value < derived.trade_value
    assert estimated.confidence_score < derived.confidence_score
    assert estimated.warning_status == "review_needed"
    assert "review_needed_estimated_private_features" in estimated.warning_reasons


def _veteran(
    position: VeteranPosition,
    features: dict[str, float | None],
    *,
    user_overrides: dict[str, bool] | None = None,
    league_rank: int | None = 50,
    is_top_five: bool = True,
) -> VeteranInput:
    return VeteranInput(
        player_id="fixture",
        player_name="Fixture",
        position=position,
        age=27.0,
        league_rank=league_rank,
        is_league_rank_top5=is_top_five,
        features=features,
        missing_penalties={feature_name: 8.0 for feature_name in features},
        source_reliability={feature_name: 80.0 for feature_name in features},
        source_freshness={feature_name: 90.0 for feature_name in features},
        source_confidence={feature_name: "derived" for feature_name in features},
        user_overrides=user_overrides or {feature_name: False for feature_name in features},
    )


def _wr_feature_set() -> dict[str, float | None]:
    return {
        "lve_projection_value": 82,
        "route_participation": 84,
        "target_share": 82,
        "targets_per_route_run": 80,
        "yards_per_route_run": 83,
        "first_downs_per_route": 80,
        "get_open_role_robustness": 82,
        "td_area_air_yards_role": 78,
        "offense_environment": 76,
        "role_security": 84,
        "age_curve": 78,
        "injury_durability": 82,
        "market_liquidity": 78,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
