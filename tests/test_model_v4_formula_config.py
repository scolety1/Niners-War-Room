from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("docs/model_v4/MODEL_V4_FORMULA_CONFIG.json")

EXPECTED_LANES = {
    "dynasty_asset_value",
    "roster_decision_value",
    "required_top_five_release_pain",
    "trade_market_context",
    "draft_value",
    "confidence",
}

ROUTE_METRICS = {"route_participation", "routes_run", "tprr", "yprr"}


def test_model_v4_formula_config_exists_and_stays_review_only() -> None:
    config = _config()

    assert config["formula_version"] == "model_v4_review_only_0.2.1"
    assert config["status"] == "review_only"
    assert config["decision_ready_unlocked"] is False
    assert config["active_rankings_affected"] is False
    assert config["generated_rankings"] is False
    assert config["review_only_guardrails"]["no_decision_ready_unlock"] is True


def test_model_v4_formula_config_defines_required_lanes() -> None:
    config = _config()

    assert set(config["lanes"]) == EXPECTED_LANES
    assert set(config["lane_output_fields"]) == EXPECTED_LANES


def test_each_position_component_weights_sum_to_100() -> None:
    config = _config()

    assert set(config["position_component_weights"]) == {"RB", "WR", "QB", "TE"}
    for position, weights in config["position_component_weights"].items():
        total = sum(_weight for _weight in weights.values())
        assert total == 100, f"{position} weights sum to {total}"


def test_private_value_forbidden_inputs_are_not_scoring_components() -> None:
    config = _config()
    forbidden = set(
        config["forbidden_input_rules"]["private_value_forbidden_inputs"]
    )

    for weights in config["position_component_weights"].values():
        assert forbidden.isdisjoint(weights)


def test_market_weight_is_zero_for_private_and_dynasty_value() -> None:
    config = _config()
    market_policy = config["market_policy"]

    assert market_policy["private_value_weight"] == 0
    assert market_policy["dynasty_asset_value_weight"] == 0
    assert market_policy["allowed_lanes"] == ["trade_market_context"]
    assert market_policy["missing_or_neutral_market_cannot_create_edge"] is True

    for weights in config["position_component_weights"].values():
        assert "market_liquidity" not in weights
        assert "trade_market_value" not in weights
        assert "model_vs_market_edge" not in weights


def test_league_rank_weight_is_zero_for_dynasty_asset_value() -> None:
    config = _config()
    league_rank_policy = config["league_rank_policy"]
    dynasty_forbidden = set(
        config["forbidden_input_rules"]["dynasty_asset_value_forbidden_inputs"]
    )

    assert league_rank_policy["dynasty_asset_value_weight"] == 0
    assert league_rank_policy["league_rank_is_rule_signal_not_player_quality"] is True
    assert "league_rank" in dynasty_forbidden

    for weights in config["position_component_weights"].values():
        assert "league_rank" not in weights
        assert "required_top_five_release_status" not in weights


def test_unavailable_route_metrics_cannot_be_used_as_scoring_inputs() -> None:
    config = _config()
    route_policy = config["route_metric_policy"]

    assert route_policy["snap_share_proxy_allowed"] is True
    assert route_policy["snap_share_cannot_masquerade_as_route"] is True
    assert set(route_policy["metrics"]) == ROUTE_METRICS

    for metric, policy in route_policy["metrics"].items():
        assert policy["source_status"] == "unavailable_free_public"
        assert policy["allowed_in_scoring"] is False
        assert metric in config["forbidden_input_rules"]["private_value_forbidden_inputs"]

    for weights in config["position_component_weights"].values():
        assert ROUTE_METRICS.isdisjoint(weights)


def test_lifecycle_rules_block_established_veteran_draft_capital_scoring() -> None:
    lifecycle_rules = _config()["lifecycle_rules"]

    assert lifecycle_rules["incoming_rookie"]["rookie_prior_weight"] == 1.0
    assert lifecycle_rules["year_one_nfl_bridge"]["rookie_prior_weight_cap"] > 0
    assert lifecycle_rules["year_two_nfl_bridge"]["rookie_prior_weight_cap"] > 0
    assert lifecycle_rules["year_three_nfl_bridge"]["rookie_prior_weight_cap"] > 0
    assert lifecycle_rules["established_veteran"]["draft_capital_weight"] == 0
    assert lifecycle_rules["established_veteran"]["prospect_profile_weight"] == 0


def test_confidence_rules_do_not_convert_context_into_player_value() -> None:
    confidence_rules = _config()["confidence_rules"]

    assert confidence_rules["confidence_is_score_trust_not_player_value"] is True
    assert confidence_rules["local_baseline_projection_is_not_independent_forecast"]
    assert confidence_rules["unsourced_healthy_injury_context_cannot_boost_confidence"]
    assert confidence_rules["neutral_defaults_must_display_in_receipts"] is True
    assert confidence_rules["incoming_rookie_missing_all_evidence_cannot_be_strong"]
    assert (
        confidence_rules["incoming_rookie_missing_all_evidence_confidence_cap"]
        == "weak"
    )


def test_missing_evidence_policy_adds_uncertainty_without_zeroing_value() -> None:
    policy = _config()["missing_evidence_policy"]

    assert policy["established_veteran_missing_value_components_are_not_zero_production"]
    assert policy["missing_component_uncertainty_penalty_rate"] == 0.2
    assert policy["max_missing_component_uncertainty_penalty"] == 8.0
    assert policy["applies_only_to_evidence_adjusted_missing_not_zero"] is True


def _config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
