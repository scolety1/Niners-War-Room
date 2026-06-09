from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.market_influence_policy_service import (
    market_edge_classification,
    market_status_warning,
    market_value_status,
    safe_market_edge_score,
)
from src.services.player_lifecycle_service import add_lifecycle_fields
from src.services.young_nfl_bridge_service import (
    blend_with_bridge_prior,
    young_nfl_bridge_prior_from_row,
)
from src.utils.scoring import clamp_score

STATS_FIRST_MODEL_VERSION = "veteran_lve_stats_first_v1_0_0"

LVE_CROSS_POSITION_REPLACEMENT_BASELINES = {
    "QB": 76.0,
    "RB": 72.0,
    "WR": 72.0,
    "TE": 69.0,
}


@dataclass(frozen=True)
class StatsFirstContribution:
    player_id: str
    component: str
    feature_name: str
    normalized_score: float
    feature_weight: float
    component_contribution: float


@dataclass(frozen=True)
class StatsFirstVeteranScore:
    season: str
    player_id: str
    player_name: str
    position: str
    team: str
    model_version: str
    private_lve_value: float
    win_now_value: float
    dynasty_hold_value: float
    keeper_score: float
    drop_candidate_score: float
    trade_value: float
    confidence_score: float
    horizon_retention_score: float
    market_liquidity: float
    market_value_status: str
    market_trade_value: float
    market_edge_score: float
    market_edge_label: str
    market_edge_warning: str
    market_keeper_influence: float
    structural_adjustment: float
    cross_position_replacement_baseline: float
    lve_lineup_demand_adjustment: float
    warning_status: str
    warning_reasons: tuple[str, ...]
    risk_flags: tuple[str, ...]
    upside_flags: tuple[str, ...]
    floor_flags: tuple[str, ...]
    contributions: tuple[StatsFirstContribution, ...]
    experience_bucket: str
    young_nfl_bridge_prior_score: float
    young_nfl_bridge_weight: float
    young_nfl_bridge_source: str


def score_stats_first_veteran_row(row: dict[str, object]) -> StatsFirstVeteranScore:
    position = str(row.get("position") or "")
    player_id = str(row.get("player_id") or row.get("gsis_id") or "")
    if position == "QB":
        win_now, win_now_contributions = _qb_win_now_value(player_id, row)
        dynasty_hold, dynasty_hold_contributions = _qb_dynasty_hold_value(player_id, row)
        private, private_contributions = _qb_private_lve_value(
            player_id,
            win_now,
            dynasty_hold,
            row,
        )
        horizon = dynasty_hold
        horizon_contributions = dynasty_hold_contributions
    elif position == "RB":
        win_now, win_now_contributions = _rb_win_now_value(player_id, row)
        dynasty_hold, dynasty_hold_contributions = _rb_dynasty_hold_value(player_id, row)
        private, private_contributions = _rb_private_lve_value(
            player_id,
            win_now,
            dynasty_hold,
            row,
        )
        horizon = dynasty_hold
        horizon_contributions = dynasty_hold_contributions
    elif position == "WR":
        win_now, win_now_contributions = _wr_win_now_value(player_id, row)
        dynasty_hold, dynasty_hold_contributions = _wr_dynasty_hold_value(player_id, row)
        private, private_contributions = _wr_private_lve_value(
            player_id,
            win_now,
            dynasty_hold,
            row,
        )
        horizon = dynasty_hold
        horizon_contributions = dynasty_hold_contributions
    elif position == "TE":
        win_now, win_now_contributions = _te_win_now_value(player_id, row)
        dynasty_hold, dynasty_hold_contributions = _te_dynasty_hold_value(player_id, row)
        private, private_contributions = _te_private_lve_value(
            player_id,
            win_now,
            dynasty_hold,
            row,
        )
        horizon = dynasty_hold
        horizon_contributions = dynasty_hold_contributions
    else:
        private, private_contributions = _private_lve_value(player_id, position, row)
        horizon, horizon_contributions = _horizon_retention_score(player_id, position, row)
        win_now = private
        dynasty_hold = horizon
        win_now_contributions = ()
    private, private_contributions, bridge_prior = _apply_young_nfl_bridge_prior(
        player_id,
        private,
        private_contributions,
        row,
    )
    confidence = _confidence_score(row)
    market_status = market_value_status(row, value_keys=("market_liquidity",))
    market_liquidity = _score(_float(row.get("market_liquidity"), 50.0))
    market_trade_value = market_liquidity
    safe_edge = safe_market_edge_score(
        private,
        market_trade_value,
        market_status,
    )
    edge = safe_edge if safe_edge is not None else 0.0
    market_keeper_influence = _market_keeper_influence(market_liquidity)
    structural_adjustment = _structural_adjustment(position, private, row)
    replacement_baseline = _cross_position_replacement_baseline(position, row)
    lineup_adjustment = _lve_lineup_demand_adjustment(position, private, row)
    keeper = _keeper_score(
        private,
        horizon,
        confidence,
        market_keeper_influence,
        structural_adjustment,
        lineup_adjustment,
    )
    trade, trade_contributions = _trade_value(
        player_id,
        position,
        private,
        keeper,
        confidence,
        market_liquidity,
    )
    drop = _drop_candidate_score(position, private, keeper, trade, row)
    risk = _risk_flags(position, private, keeper, drop, row)
    warnings = _warning_reasons(row, confidence, risk)
    return StatsFirstVeteranScore(
        season=str(row.get("season") or ""),
        player_id=player_id,
        player_name=str(row.get("player_name") or ""),
        position=position,
        team=str(row.get("team") or ""),
        model_version=STATS_FIRST_MODEL_VERSION,
        private_lve_value=round(private, 2),
        win_now_value=round(win_now, 2),
        dynasty_hold_value=round(dynasty_hold, 2),
        keeper_score=round(keeper, 2),
        drop_candidate_score=round(drop, 2),
        trade_value=round(trade, 2),
        confidence_score=round(confidence, 2),
        horizon_retention_score=round(horizon, 2),
        market_liquidity=round(market_liquidity, 2),
        market_value_status=market_status,
        market_trade_value=round(market_trade_value, 2),
        market_edge_score=edge,
        market_edge_label=market_edge_classification(market_status, safe_edge),
        market_edge_warning=_market_edge_warning(row, confidence, market_status),
        market_keeper_influence=round(market_keeper_influence, 2),
        structural_adjustment=round(structural_adjustment, 2),
        cross_position_replacement_baseline=round(replacement_baseline, 2),
        lve_lineup_demand_adjustment=round(lineup_adjustment, 2),
        warning_status=_warning_status(confidence, warnings, risk),
        warning_reasons=warnings,
        risk_flags=risk,
        upside_flags=_upside_flags(position, private, trade, row),
        floor_flags=_floor_flags(position, keeper, row),
        contributions=(
            *win_now_contributions,
            *private_contributions,
            *horizon_contributions,
            *trade_contributions,
        ),
        experience_bucket=bridge_prior.experience_bucket,
        young_nfl_bridge_prior_score=bridge_prior.rookie_prior_score,
        young_nfl_bridge_weight=bridge_prior.bridge_weight,
        young_nfl_bridge_source=bridge_prior.source,
    )


def score_stats_first_veteran_rows(
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> tuple[StatsFirstVeteranScore, ...]:
    return tuple(
        sorted(
            (score_stats_first_veteran_row(row) for row in rows),
            key=lambda score: (
                -score.keeper_score,
                -score.private_lve_value,
                score.position,
                score.player_name,
            ),
        )
    )


def score_stats_first_veteran_csv(path: str | Path) -> tuple[StatsFirstVeteranScore, ...]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return score_stats_first_veteran_rows(tuple(csv.DictReader(handle)))


def stats_first_output_rows(
    scores: tuple[StatsFirstVeteranScore, ...],
    *,
    computed_at: str = "",
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    position_ranks: dict[str, int] = {}
    for rank, score in enumerate(scores, start=1):
        position_ranks[score.position] = position_ranks.get(score.position, 0) + 1
        position_rank = position_ranks[score.position]
        row = add_lifecycle_fields(
            {
                "board_rank": rank,
                "overall_rank": rank,
                "position_rank": position_rank,
                "position_rank_label": f"{score.position}{position_rank}",
                "season": score.season,
                "player_id": score.player_id,
                "player_name": score.player_name,
                "position": score.position,
                "team": score.team,
                "private_lve_value": score.private_lve_value,
                "win_now_value": score.win_now_value,
                "dynasty_hold_value": score.dynasty_hold_value,
                "keeper_score": score.keeper_score,
                "drop_candidate_score": score.drop_candidate_score,
                "trade_value": score.trade_value,
                "confidence_score": score.confidence_score,
                "horizon_retention_score": score.horizon_retention_score,
                "market_keeper_influence": score.market_keeper_influence,
                "market_value_status": score.market_value_status,
                "market_trade_value": score.market_trade_value,
                "market_edge_score": score.market_edge_score,
                "market_edge_label": score.market_edge_label,
                "market_edge_warning": score.market_edge_warning,
                "structural_adjustment": score.structural_adjustment,
                "cross_position_replacement_baseline": (
                    score.cross_position_replacement_baseline
                ),
                "lve_lineup_demand_adjustment": score.lve_lineup_demand_adjustment,
                "warning_status": score.warning_status,
                "warning_reasons": "|".join(score.warning_reasons),
                "risk_flags": "|".join(score.risk_flags),
                "upside_flags": "|".join(score.upside_flags),
                "floor_flags": "|".join(score.floor_flags),
                "experience_bucket": score.experience_bucket,
                "young_nfl_bridge_prior_score": score.young_nfl_bridge_prior_score,
                "young_nfl_bridge_weight": score.young_nfl_bridge_weight,
                "young_nfl_bridge_source": score.young_nfl_bridge_source,
                "model_version": score.model_version,
                "computed_at": computed_at,
                "rank_audit": (
                    f"sort=keeper_score_desc|private_lve_value_desc;"
                    f"overall_rank={rank};position_rank={score.position}{position_rank};"
                    f"rank_value=keeper_score:{score.keeper_score};"
                    f"replacement_baseline={score.cross_position_replacement_baseline};"
                    f"lineup_adjustment={score.lve_lineup_demand_adjustment}"
                ),
            }
        )
        rows.append(row)
    return rows


def _private_lve_value(
    player_id: str,
    position: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    if position == "QB":
        items = (
            ("win_now_value", _qb_win_now_value(player_id, row)[0], 45),
            ("dynasty_hold_value", _qb_dynasty_hold_value(player_id, row)[0], 55),
        )
        return _weighted_items(player_id, "private_lve_value", items)
    if position == "RB":
        items = (
            ("win_now_value", _rb_win_now_value(player_id, row)[0], 40),
            ("dynasty_hold_value", _rb_dynasty_hold_value(player_id, row)[0], 60),
        )
        return _weighted_items(player_id, "private_lve_value", items)
    if position == "WR":
        items = (
            ("win_now_value", _wr_win_now_value(player_id, row)[0], 45),
            ("dynasty_hold_value", _wr_dynasty_hold_value(player_id, row)[0], 55),
        )
        return _weighted_items(player_id, "private_lve_value", items)
    if position == "TE":
        items = (
            ("win_now_value", _te_win_now_value(player_id, row)[0], 40),
            ("dynasty_hold_value", _te_dynasty_hold_value(player_id, row)[0], 60),
        )
        return _weighted_items(player_id, "private_lve_value", items)
    items = (
        ("weighted_recent_lve_ppg_score", _feature(row, "weighted_recent_lve_ppg_score"), 16),
        ("expected_lve_points_score", _feature(row, "expected_lve_points_score"), 17),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 13),
        ("route_role", _feature(row, "route_role"), 20),
        ("target_earning_stability", _feature(row, "target_earning_stability"), 13),
        ("efficiency_score", _efficiency_feature(row), 8),
        ("first_down_td_fit", _feature(row, "first_down_td_fit"), 3),
        ("age_curve", _feature(row, "age_curve"), 4),
        ("injury_durability", _feature(row, "injury_durability", default=76), 6),
    )
    route = _feature(row, "route_role")
    target = _feature(row, "target_earning_stability")
    penalty = 0.0 if route >= 82 and target >= 78 else -8.0 if route >= 60 else -14.0
    return _weighted_items(player_id, "private_lve_value", items, adjustment=penalty)


def _qb_win_now_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    gated_rushing = _qb_start_gated_rushing_profile(row)
    items = (
        ("role_security", _feature(row, "role_security"), 28),
        ("expected_lve_points_score", _feature(row, "expected_lve_points_score"), 22),
        ("weighted_recent_lve_ppg_score", _feature(row, "weighted_recent_lve_ppg_score"), 16),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 14),
        ("start_gated_rushing_profile", gated_rushing, 12),
        ("efficiency_score", _efficiency_feature(row), 6),
        ("injury_durability", _feature(row, "injury_durability", default=78), 2),
    )
    return _weighted_items(player_id, "win_now_value", items)


def _qb_dynasty_hold_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    gated_rushing = _qb_start_gated_rushing_profile(row)
    penalty = _qb_replaceability_penalty(row)
    items = (
        ("role_security", _feature(row, "role_security"), 24),
        ("start_gated_rushing_profile", gated_rushing, 22),
        ("expected_lve_points_score", _feature(row, "expected_lve_points_score"), 16),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 12),
        ("efficiency_score", _efficiency_feature(row), 10),
        ("age_curve", _feature(row, "age_curve"), 10),
        ("injury_durability", _feature(row, "injury_durability", default=78), 6),
    )
    return _weighted_items(
        player_id,
        "dynasty_hold_value",
        items,
        adjustment=-penalty,
    )


def _qb_private_lve_value(
    player_id: str,
    win_now: float,
    dynasty_hold: float,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    raw_private = (0.44 * win_now) + (0.56 * dynasty_hold)
    replacement = _qb_replacement_level_baseline(row)
    elite = _qb_elite_exception(row, raw_private)
    if elite:
        private = clamp_score(raw_private + 3.0)
    elif _feature(row, "role_security") < 70:
        private = min(raw_private - 16.0, replacement - 6.0)
    elif raw_private <= replacement + 6.0:
        private = min(raw_private - 10.0, replacement + 1.0)
    elif _qb_rushing_profile(row) < 55:
        private = min(raw_private - 12.0, replacement + 3.0)
    else:
        private = min(raw_private - 8.0, replacement + 7.0)
    private = clamp_score(private)
    adjustment = private - raw_private
    contributions = [
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "win_now_value",
            round(win_now, 2),
            44,
            round(win_now * 0.44, 4),
        ),
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "dynasty_hold_value",
            round(dynasty_hold, 2),
            56,
            round(dynasty_hold * 0.56, 4),
        ),
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "qb_replacement_level_baseline",
            round(replacement, 2),
            0,
            0.0,
        ),
    ]
    if adjustment:
        feature_name = "qb_elite_exception" if elite else "qb_replacement_suppression"
        contributions.append(
            StatsFirstContribution(
                player_id,
                "private_lve_value",
                feature_name,
                round(adjustment, 2),
                0,
                round(adjustment, 4),
            )
        )
    return round(private, 2), tuple(contributions)


def _rb_win_now_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    capped_first_down_fit = _rb_capped_first_down_td_fit(row)
    items = (
        ("expected_lve_points_score", _feature(row, "expected_lve_points_score"), 22),
        ("weighted_recent_lve_ppg_score", _feature(row, "weighted_recent_lve_ppg_score"), 18),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 18),
        ("role_security", _feature(row, "role_security"), 14),
        ("workload_earning", _feature(row, "workload_earning"), 12),
        ("first_down_td_fit_capped", capped_first_down_fit, 10),
        ("efficiency_score", _efficiency_feature(row), 6),
    )
    return _weighted_items(player_id, "win_now_value", items)


def _rb_dynasty_hold_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    capped_first_down_fit = _rb_capped_first_down_td_fit(row)
    penalty = _rb_fragility_penalty(row)
    items = (
        ("age_curve", _feature(row, "age_curve"), 24),
        ("injury_durability", _feature(row, "injury_durability", default=76), 18),
        ("workload_earning", _feature(row, "workload_earning"), 16),
        ("expected_lve_points_score", _feature(row, "expected_lve_points_score"), 12),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 10),
        ("role_security", _feature(row, "role_security"), 8),
        ("efficiency_score", _efficiency_feature(row), 8),
        ("first_down_td_fit_capped", capped_first_down_fit, 4),
    )
    return _weighted_items(
        player_id,
        "dynasty_hold_value",
        items,
        adjustment=-penalty,
    )


def _rb_private_lve_value(
    player_id: str,
    win_now: float,
    dynasty_hold: float,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    _ = row
    raw_private = (0.40 * win_now) + (0.60 * dynasty_hold)
    cap = 100.0
    if dynasty_hold < 70:
        cap = dynasty_hold + 12.0
    elif dynasty_hold < 76:
        cap = dynasty_hold + 14.0
    private = clamp_score(min(raw_private, cap))
    adjustment = private - raw_private
    contributions = [
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "win_now_value",
            round(win_now, 2),
            40,
            round(win_now * 0.40, 4),
        ),
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "dynasty_hold_value",
            round(dynasty_hold, 2),
            60,
            round(dynasty_hold * 0.60, 4),
        ),
    ]
    if adjustment < -0.01:
        contributions.append(
            StatsFirstContribution(
                player_id,
                "private_lve_value",
                "rb_dynasty_cap",
                round(adjustment, 2),
                0,
                round(adjustment, 4),
            )
        )
    return round(private, 2), tuple(contributions)


def _wr_win_now_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    items = (
        ("target_earning_stability", _feature(row, "target_earning_stability"), 20),
        ("role_security", _feature(row, "role_security"), 18),
        ("route_role", _wr_route_role(row), 14),
        ("weighted_recent_lve_ppg_score", _feature(row, "weighted_recent_lve_ppg_score"), 14),
        ("expected_lve_points_score", _feature(row, "expected_lve_points_score"), 12),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 10),
        ("efficiency_score", _efficiency_feature(row), 7),
        ("first_down_td_fit", _feature(row, "first_down_td_fit"), 5),
    )
    return _weighted_items(player_id, "win_now_value", items)


def _wr_dynasty_hold_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    penalty = _wr_role_target_penalty(row)
    production_stability = (
        (0.45 * _feature(row, "weighted_recent_lve_ppg_score"))
        + (0.35 * _feature(row, "expected_lve_points_score"))
        + (0.20 * _feature(row, "lve_projection_value"))
    )
    items = (
        ("target_earning_stability", _feature(row, "target_earning_stability"), 24),
        ("route_role", _wr_route_role(row), 18),
        ("age_curve", _feature(row, "age_curve"), 18),
        ("production_stability", production_stability, 14),
        ("efficiency_score", _efficiency_feature(row), 10),
        ("first_down_td_fit", _feature(row, "first_down_td_fit"), 7),
        ("role_security", _feature(row, "role_security"), 5),
        ("injury_durability", _feature(row, "injury_durability", default=78), 4),
    )
    return _weighted_items(
        player_id,
        "dynasty_hold_value",
        items,
        adjustment=-penalty,
    )


def _wr_private_lve_value(
    player_id: str,
    win_now: float,
    dynasty_hold: float,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    _ = row
    raw_private = (0.42 * win_now) + (0.58 * dynasty_hold)
    cap = 100.0
    if dynasty_hold < 66:
        cap = dynasty_hold + 10.0
    elif dynasty_hold < 74:
        cap = dynasty_hold + 13.0
    private = clamp_score(min(raw_private, cap))
    adjustment = private - raw_private
    contributions = [
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "win_now_value",
            round(win_now, 2),
            42,
            round(win_now * 0.42, 4),
        ),
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "dynasty_hold_value",
            round(dynasty_hold, 2),
            58,
            round(dynasty_hold * 0.58, 4),
        ),
    ]
    if adjustment < -0.01:
        contributions.append(
            StatsFirstContribution(
                player_id,
                "private_lve_value",
                "wr_dynasty_cap",
                round(adjustment, 2),
                0,
                round(adjustment, 4),
            )
        )
    return round(private, 2), tuple(contributions)


def _apply_young_nfl_bridge_prior(
    player_id: str,
    private_value: float,
    contributions: tuple[StatsFirstContribution, ...],
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...], object]:
    prior = young_nfl_bridge_prior_from_row(row)
    if prior.bridge_weight <= 0:
        return private_value, contributions, prior
    bridged = blend_with_bridge_prior(
        nfl_value=private_value,
        bridge_prior=prior,
    )
    adjustment = round(bridged - private_value, 4)
    bridge_contributions = (
        StatsFirstContribution(
            player_id=player_id,
            component="private_lve_value",
            feature_name="draft_capital_prior_score",
            normalized_score=prior.draft_capital_prior_score,
            feature_weight=0,
            component_contribution=0.0,
        ),
        StatsFirstContribution(
            player_id=player_id,
            component="private_lve_value",
            feature_name="young_nfl_bridge_decay_weight",
            normalized_score=round(prior.bridge_weight * 100.0, 2),
            feature_weight=0,
            component_contribution=0.0,
        ),
        StatsFirstContribution(
            player_id=player_id,
            component="private_lve_value",
            feature_name="young_nfl_bridge_nfl_evidence_weight",
            normalized_score=round(prior.nfl_evidence_weight * 100.0, 2),
            feature_weight=0,
            component_contribution=0.0,
        ),
        StatsFirstContribution(
            player_id=player_id,
            component="private_lve_value",
            feature_name="young_nfl_bridge_prior",
            normalized_score=prior.rookie_prior_score,
            feature_weight=round(prior.bridge_weight * 100.0, 2),
            component_contribution=adjustment,
        ),
    )
    return round(bridged, 2), (*contributions, *bridge_contributions), prior


def _te_win_now_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    items = (
        ("route_role", _te_route_role(row), 28),
        ("target_earning_stability", _te_target_earning(row), 22),
        ("expected_lve_points_score", _feature(row, "expected_lve_points_score"), 16),
        ("weighted_recent_lve_ppg_score", _feature(row, "weighted_recent_lve_ppg_score"), 12),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 10),
        ("efficiency_score", _efficiency_feature(row), 6),
        ("first_down_td_fit", _feature(row, "first_down_td_fit"), 4),
        ("injury_durability", _feature(row, "injury_durability", default=78), 2),
    )
    return _weighted_items(player_id, "win_now_value", items)


def _te_dynasty_hold_value(
    player_id: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    penalty = _te_route_target_penalty(row)
    production_stability = (
        (0.45 * _feature(row, "weighted_recent_lve_ppg_score"))
        + (0.35 * _feature(row, "expected_lve_points_score"))
        + (0.20 * _feature(row, "lve_projection_value"))
    )
    items = (
        ("route_role", _te_route_role(row), 30),
        ("target_earning_stability", _te_target_earning(row), 24),
        ("age_curve", _feature(row, "age_curve"), 12),
        ("efficiency_score", _efficiency_feature(row), 10),
        ("production_stability", production_stability, 8),
        ("injury_durability", _feature(row, "injury_durability", default=78), 8),
        ("first_down_td_fit", _feature(row, "first_down_td_fit"), 5),
        ("lve_projection_value", _feature(row, "lve_projection_value"), 3),
    )
    return _weighted_items(
        player_id,
        "dynasty_hold_value",
        items,
        adjustment=-penalty,
    )


def _te_private_lve_value(
    player_id: str,
    win_now: float,
    dynasty_hold: float,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    raw_private = (0.40 * win_now) + (0.60 * dynasty_hold)
    replacement = _te_replacement_level_baseline(row)
    elite = _te_elite_exception(row, raw_private)
    if elite:
        private = clamp_score(raw_private + 1.0)
    elif _te_route_role(row) < 58 or _te_target_earning(row) < 58:
        private = min(raw_private - 18.0, replacement - 6.0)
    elif _te_route_role(row) < 72 or _te_target_earning(row) < 68:
        private = min(raw_private - 10.0, replacement + 2.0)
    else:
        private = min(raw_private - 6.0, replacement + 8.0)
    private = clamp_score(private)
    adjustment = private - raw_private
    contributions = [
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "win_now_value",
            round(win_now, 2),
            40,
            round(win_now * 0.40, 4),
        ),
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "dynasty_hold_value",
            round(dynasty_hold, 2),
            60,
            round(dynasty_hold * 0.60, 4),
        ),
        StatsFirstContribution(
            player_id,
            "private_lve_value",
            "te_replacement_level_baseline",
            round(replacement, 2),
            0,
            0.0,
        ),
    ]
    if adjustment:
        feature_name = "te_elite_exception" if elite else "te_no_premium_suppression"
        contributions.append(
            StatsFirstContribution(
                player_id,
                "private_lve_value",
                feature_name,
                round(adjustment, 2),
                0,
                round(adjustment, 4),
            )
        )
    return round(private, 2), tuple(contributions)


def _horizon_retention_score(
    player_id: str,
    position: str,
    row: dict[str, object],
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    if position == "QB":
        skill = _feature(row, "role_security")
    elif position == "RB":
        skill = (0.55 * _feature(row, "workload_earning")) + (
            0.45 * _feature(row, "first_down_td_fit")
        )
    elif position == "WR":
        skill = _feature(row, "target_earning_stability")
    else:
        skill = (0.65 * _feature(row, "route_role")) + (
            0.35 * _feature(row, "target_earning_stability")
        )
    items = (
        ("age_curve", _feature(row, "age_curve"), 35),
        ("role_security", _feature(row, "role_security"), 25),
        ("injury_durability", _feature(row, "injury_durability", default=76), 20),
        ("skill_portability", skill, 20),
    )
    return _weighted_items(player_id, "horizon_retention_score", items)


def _keeper_score(
    private_value: float,
    horizon: float,
    confidence: float,
    market_keeper_influence: float,
    structural_adjustment: float,
    lineup_adjustment: float,
) -> float:
    # Market is trade/liquidity evidence only. It must not change private
    # football value, keeper value, or cut-risk scores.
    _ = market_keeper_influence
    return clamp_score(
        (0.72 * private_value)
        + (0.18 * horizon)
        + (0.05 * confidence)
        + structural_adjustment
        + lineup_adjustment
    )


def _trade_value(
    player_id: str,
    position: str,
    private_value: float,
    keeper: float,
    confidence: float,
    market_liquidity: float,
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    liquidity_adjustment = {
        "QB": -6.0 if private_value < 90 else -1.0,
        "RB": 0.0,
        "WR": 2.0,
        "TE": -6.0 if private_value < 88 else -1.0,
    }.get(position, 0.0)
    trade = clamp_score(
        (0.42 * market_liquidity)
        + (0.30 * private_value)
        + (0.18 * keeper)
        + (0.10 * confidence)
        + liquidity_adjustment
    )
    return trade, (
        StatsFirstContribution(
            player_id,
            "trade_value",
            "market_liquidity",
            round(market_liquidity, 2),
            42,
            round(market_liquidity * 0.42, 4),
        ),
        StatsFirstContribution(
            player_id,
            "trade_value",
            "private_lve_value",
            round(private_value, 2),
            30,
            round(private_value * 0.30, 4),
        ),
        StatsFirstContribution(
            player_id,
            "trade_value",
            "keeper_score",
            round(keeper, 2),
            18,
            round(keeper * 0.18, 4),
        ),
        StatsFirstContribution(
            player_id,
            "trade_value",
            "confidence_score",
            round(confidence, 2),
            10,
            round(confidence * 0.10, 4),
        ),
    )


def _drop_candidate_score(
    position: str,
    private_value: float,
    keeper: float,
    trade: float,
    row: dict[str, object],
) -> float:
    # This is football cut risk only. Trade liquidity and forced-release rule
    # pressure are separate action layers, not player-quality penalties.
    _ = trade
    role_risk = 100.0 - _role_value(position, row)
    health_risk = 100.0 - _feature(row, "injury_durability", default=76)
    return clamp_score(
        (0.48 * (100.0 - keeper))
        + (0.17 * (100.0 - private_value))
        + (0.15 * role_risk)
        + (0.10 * health_risk)
    )


def _confidence_score(row: dict[str, object]) -> float:
    base = _score(_float(row.get("confidence"), 50.0))
    missing_penalty = _float(row.get("missing_data_penalty"), 0.0)
    warning_penalty = min(8.0, len(_warnings_from_row(row)) * 2.0)
    confidence = clamp_score(base - (0.50 * missing_penalty) - warning_penalty)
    return min(confidence, _source_quality_confidence_cap(row))


def _source_quality_confidence_cap(row: dict[str, object]) -> float:
    warnings = _warnings_from_row(row)
    projection_status = str(row.get("projection_source_status") or "")
    cap = 100.0
    if "missing_lve_scoring_history" in warnings:
        cap = min(cap, 58.0)
    if "missing_role_usage_features" in warnings:
        cap = min(cap, 60.0)
    if "missing_projection_features" in warnings or projection_status == "missing_projection":
        cap = min(cap, 72.0)
    if (
        "local_baseline_projection_not_independent" in warnings
        or projection_status == "local_baseline_projection"
    ):
        cap = min(cap, 78.0)
    if "missing_participation_proxy" in warnings or "missing_snap_counts" in warnings:
        cap = min(cap, 74.0)
    if "stale_lve_scoring_source" in warnings:
        cap = min(cap, 74.0)
    if "missing_injury_features" in warnings:
        cap = min(cap, 82.0)
    return cap


def _market_keeper_influence(market_liquidity: float) -> float:
    _ = market_liquidity
    return 0.0


def _market_edge_warning(
    row: dict[str, object],
    confidence: float,
    market_status: str,
) -> str:
    warnings = _warnings_from_row(row)
    if confidence < 65:
        return "review_low_model_confidence"
    status_warning = market_status_warning(market_status)
    if status_warning != "none":
        return status_warning
    if "market_liquidity" not in row or str(row.get("market_liquidity") or "") == "":
        return "missing_market_trade_value"
    if warnings:
        return "source_warning:" + "|".join(sorted(warnings))
    return "none"


def _cross_position_replacement_baseline(position: str, row: dict[str, object]) -> float:
    field_name = {
        "QB": "qb_replacement_level_baseline",
        "RB": "rb_replacement_level_baseline",
        "WR": "wr_replacement_level_baseline",
        "TE": "te_replacement_level_baseline",
    }.get(position, "")
    default = LVE_CROSS_POSITION_REPLACEMENT_BASELINES.get(position, 70.0)
    return _feature(row, field_name, default=default) if field_name else default


def _lve_lineup_demand_adjustment(
    position: str,
    private_value: float,
    row: dict[str, object],
) -> float:
    baseline = _cross_position_replacement_baseline(position, row)
    edge = private_value - baseline
    if position == "QB":
        return 0.0 if _qb_elite_exception(row, private_value) else -3.0
    if position == "TE":
        return 0.0 if _te_elite_exception(row, private_value) else -3.0
    if position == "WR":
        target = _feature(row, "target_earning_stability")
        route = _wr_route_role(row)
        if target >= 88 and route >= 84 and edge >= 15:
            return 2.0
        if target >= 78 and route >= 76 and edge >= 8:
            return 1.5
        if target >= 70 and route >= 70 and edge >= 3:
            return 0.75
        return -1.0 if target < 60 or route < 62 else 0.0
    if position == "RB":
        age = _feature(row, "age_curve")
        injury = _feature(row, "injury_durability", default=76)
        workload = _feature(row, "workload_earning")
        first_down_fit = _rb_capped_first_down_td_fit(row)
        fragile = workload >= 86 and (age < 62 or injury < 65)
        if fragile:
            return -1.5
        if workload >= 86 and first_down_fit >= 82 and age >= 74 and edge >= 14:
            return 1.5
        if workload >= 76 and first_down_fit >= 75 and edge >= 6:
            return 1.0
        return 0.0
    return 0.0


def _structural_adjustment(position: str, private_value: float, row: dict[str, object]) -> float:
    if position == "QB":
        if _qb_elite_exception(row, private_value):
            return -2.0
        if _feature(row, "role_security") < 70:
            return -16.0
        return -10.0
    if position == "TE":
        if _te_elite_exception(row, private_value):
            return -2.0
        if _te_route_role(row) < 58 or _te_target_earning(row) < 58:
            return -12.0
        return -8.0
    if position == "WR":
        target = _feature(row, "target_earning_stability")
        route = _wr_route_role(row)
        if target >= 85 and route >= 82 and private_value >= 88:
            return 2.0
        if target >= 76 and route >= 74 and private_value >= 78:
            return 1.0
        if target < 58 or route < 60:
            return -4.0
        if target < 68 and route < 68:
            return -2.0
        return 0.0
    if position == "RB":
        age = _feature(row, "age_curve")
        injury = _feature(row, "injury_durability", default=76)
        workload = _feature(row, "workload_earning")
        first_down_fit = _rb_capped_first_down_td_fit(row)
        elite_lve_role = (
            private_value >= 88
            and workload >= 84
            and first_down_fit >= 82
            and age >= 74
            and injury >= 72
        )
        fragile_role_spike = workload >= 88 and (age < 62 or injury < 65)
        if elite_lve_role:
            return 1.5
        if fragile_role_spike:
            return -3.0
        return 0.0
    return 0.0


def _risk_flags(
    position: str,
    private_value: float,
    keeper: float,
    drop: float,
    row: dict[str, object],
) -> tuple[str, ...]:
    flags: set[str] = set()
    if _confidence_score(row) < 65:
        flags.add("low_confidence")
    if keeper < 62 or private_value < 62:
        flags.add("keeper_bubble")
    if drop >= 55:
        flags.add("drop_candidate")
    if _feature(row, "injury_durability", default=76) < 60:
        flags.add("injury_risk")
    if position == "QB":
        replacement = _qb_replacement_level_baseline(row)
        if private_value < 82:
            flags.add("replaceable_1qb_profile")
        if private_value <= replacement + 2:
            flags.add("qb_below_replacement_edge")
        if _feature(row, "role_security") < 70:
            flags.add("qb_start_security_risk")
        if _qb_rushing_profile(row) >= 80 and _feature(row, "role_security") < 78:
            flags.add("qb_rushing_not_start_gated")
        if _qb_rushing_profile(row) < 55 and not _qb_elite_exception(row, private_value):
            flags.add("pocket_qb_1qb_suppression")
    if position == "RB":
        if _feature(row, "workload_earning") < 58 or _feature(row, "role_security") < 60:
            flags.add("committee_risk")
        if _feature(row, "age_curve") < 62:
            flags.add("rb_weak_age_window")
        if _feature(row, "workload_earning") >= 88 and _feature(
            row,
            "injury_durability",
            default=76,
        ) < 70:
            flags.add("rb_workload_injury_fragility")
        if _feature(row, "first_down_td_fit") < 50:
            flags.add("weak_chain_or_td_role")
    if position == "WR":
        target = _feature(row, "target_earning_stability")
        route = _wr_route_role(row)
        role = _feature(row, "role_security")
        if target < 60:
            flags.add("weak_target_earning")
        if route < 62 or role < 60:
            flags.add("route_role_fragility")
        if target < 68 and route < 68:
            flags.add("wr_unstable_role")
    if position == "TE":
        route = _te_route_role(row)
        target = _te_target_earning(row)
        if route < 65:
            flags.add("blocking_dependency_risk")
        if target < 65:
            flags.add("weak_te_target_earning")
        if route < 58 or target < 58:
            flags.add("low_route_te_profile")
        if private_value < 84 or not _te_elite_exception(row, private_value):
            flags.add("replaceable_no_premium_te")
    return tuple(sorted(flags))


def _upside_flags(
    position: str,
    private_value: float,
    trade: float,
    row: dict[str, object],
) -> tuple[str, ...]:
    flags: set[str] = set()
    if private_value >= 88:
        flags.add("elite_stats_first_value")
    if trade >= 85:
        flags.add("strong_trade_liquidity")
    if (
        position == "RB"
        and _rb_capped_first_down_td_fit(row) >= 84
        and _feature(row, "age_curve") >= 72
        and _feature(row, "injury_durability", default=76) >= 70
    ):
        flags.add("first_down_td_engine")
    if (
        position == "WR"
        and _feature(row, "target_earning_stability") >= 82
        and _wr_route_role(row) >= 75
    ):
        flags.add("stable_target_earner")
    if (
        position == "WR"
        and private_value >= 90
        and _feature(row, "target_earning_stability") >= 88
        and _wr_route_role(row) >= 84
    ):
        flags.add("elite_wr_anchor")
    if (
        position == "TE"
        and _te_route_role(row) >= 84
        and _te_target_earning(row) >= 78
    ):
        flags.add("difference_making_te_routes")
    if position == "TE" and _te_elite_exception(row, private_value):
        flags.add("elite_no_premium_te_exception")
    if position == "QB" and _qb_elite_exception(row, private_value):
        flags.add("elite_1qb_exception")
    if (
        position == "QB"
        and _feature(row, "role_security") >= 85
        and _qb_start_gated_rushing_profile(row) >= 85
    ):
        flags.add("secure_rushing_qb_edge")
    return tuple(sorted(flags))


def _floor_flags(position: str, keeper: float, row: dict[str, object]) -> tuple[str, ...]:
    flags: set[str] = set()
    if keeper >= 80:
        flags.add("strong_keeper")
    if _role_value(position, row) >= 78:
        flags.add("secure_role")
    if _feature(row, "injury_durability", default=76) >= 75:
        flags.add("clean_durability")
    if position in {"RB", "WR"} and _feature(row, "lve_projection_value") >= 84:
        flags.add("flex_demand_edge")
    if (
        position == "RB"
        and _feature(row, "age_curve") >= 74
        and _feature(row, "injury_durability", default=76) >= 72
    ):
        flags.add("rb_dynasty_window")
    if (
        position == "WR"
        and _feature(row, "target_earning_stability") >= 75
        and _wr_route_role(row) >= 75
    ):
        flags.add("wr_stable_target_role")
    if position == "QB" and _feature(row, "role_security") >= 82:
        flags.add("qb_start_security")
    if position == "QB" and _qb_elite_exception(row, keeper):
        flags.add("elite_1qb_floor")
    if (
        position == "TE"
        and _te_route_role(row) >= 80
        and _te_target_earning(row) >= 75
    ):
        flags.add("te_real_route_floor")
    return tuple(sorted(flags))


def _warning_reasons(
    row: dict[str, object],
    confidence: float,
    risk: tuple[str, ...],
) -> tuple[str, ...]:
    warnings = _warnings_from_row(row)
    if confidence < 40:
        warnings.add("blocking_low_confidence")
    elif confidence < 65:
        warnings.add("review_needed_low_confidence")
    elif confidence < 75:
        warnings.add("data_warning_confidence_below_target")
    for flag in risk:
        warnings.add(flag)
    if "keeper_bubble" in risk or "drop_candidate" in risk:
        warnings.add("model_warning_keeper_fragility")
    return tuple(sorted(warnings))


def _warning_status(
    confidence: float,
    warnings: tuple[str, ...],
    risk: tuple[str, ...],
) -> str:
    if confidence < 40:
        return "blocking"
    if confidence < 65 or any(warning.startswith("review_needed") for warning in warnings):
        return "review_needed"
    if any(warning.startswith("model_") for warning in warnings) or risk:
        return "model_warning"
    if any(warning.startswith("data_") for warning in warnings):
        return "data_warning"
    return "ready"


def _role_value(position: str, row: dict[str, object]) -> float:
    if position == "QB":
        return (0.80 * _feature(row, "role_security")) + (
            0.20 * _qb_start_gated_rushing_profile(row)
        )
    if position == "RB":
        return (0.60 * _feature(row, "role_security")) + (0.40 * _feature(row, "workload_earning"))
    if position == "WR":
        return (
            (0.45 * _feature(row, "role_security"))
            + (0.35 * _feature(row, "target_earning_stability"))
            + (0.20 * _wr_route_role(row))
        )
    if position == "TE":
        return (0.70 * _te_route_role(row)) + (0.30 * _te_target_earning(row))
    return _feature(row, "role_security")


def _qb_rushing_profile(row: dict[str, object]) -> float:
    return _feature(
        row,
        "qb_rushing_profile",
        default=_feature(row, "first_down_td_fit"),
    )


def _qb_start_gated_rushing_profile(row: dict[str, object]) -> float:
    rushing = _qb_rushing_profile(row)
    start_security = _feature(row, "role_security")
    if start_security < 65:
        return min(rushing, 45.0)
    if start_security < 78:
        return min(rushing, start_security)
    return rushing


def _qb_replacement_level_baseline(row: dict[str, object]) -> float:
    return _feature(row, "qb_replacement_level_baseline", default=76.0)


def _qb_replaceability_penalty(row: dict[str, object]) -> float:
    role = _feature(row, "role_security")
    rushing = _qb_rushing_profile(row)
    projection = _feature(row, "lve_projection_value")
    penalty = 0.0
    if role < 70:
        penalty += min(10.0, (70.0 - role) * 0.35)
    if rushing < 55 and projection < 92:
        penalty += min(8.0, (55.0 - rushing) * 0.18)
    if role >= 80 and rushing < 45 and projection < 88:
        penalty += 3.0
    return round(clamp_score(penalty, 0.0, 16.0), 2)


def _qb_elite_exception(row: dict[str, object], value: float) -> bool:
    role = _feature(row, "role_security")
    rushing = _qb_start_gated_rushing_profile(row)
    expected = _feature(row, "expected_lve_points_score")
    projection = _feature(row, "lve_projection_value")
    recent = _feature(row, "weighted_recent_lve_ppg_score")
    efficiency = _efficiency_feature(row)
    production_signal = max(expected, recent)
    projection_or_production_signal = max(projection, recent)
    return role >= 85 and value >= 78 and (
        (rushing >= 88 and production_signal >= 84)
        or (
            production_signal >= 94
            and projection_or_production_signal >= 92
            and efficiency >= 90
        )
    )


def _rb_capped_first_down_td_fit(row: dict[str, object]) -> float:
    fit = _feature(row, "first_down_td_fit")
    age = _feature(row, "age_curve")
    injury = _feature(row, "injury_durability", default=76)
    role = _feature(row, "role_security")
    workload = _feature(row, "workload_earning")
    dynasty_window = min(age, injury)
    if dynasty_window < 55:
        dynasty_cap = 70.0
    elif dynasty_window < 65:
        dynasty_cap = 78.0
    elif dynasty_window < 72:
        dynasty_cap = 88.0
    else:
        dynasty_cap = 100.0
    role_access = min(role, workload)
    if role_access < 60:
        role_cap = 70.0
    elif role_access < 70:
        role_cap = 82.0
    elif role_access < 78:
        role_cap = 92.0
    else:
        role_cap = 100.0
    return min(fit, dynasty_cap, role_cap)


def _rb_fragility_penalty(row: dict[str, object]) -> float:
    age = _feature(row, "age_curve")
    injury = _feature(row, "injury_durability", default=76)
    role = _feature(row, "role_security")
    workload = _feature(row, "workload_earning")
    penalty = 0.0
    if age < 62:
        penalty += min(8.0, (62.0 - age) * 0.28)
    if injury < 68:
        penalty += min(8.0, (68.0 - injury) * 0.25)
    if workload >= 86 and role >= 84 and injury < 75:
        penalty += min(4.0, (75.0 - injury) * 0.12)
    if workload >= 88 and age < 68:
        penalty += min(3.0, (68.0 - age) * 0.10)
    return round(clamp_score(penalty, 0.0, 15.0), 2)


def _wr_route_role(row: dict[str, object]) -> float:
    route = _feature(
        row,
        "route_role",
        default=_feature(row, "role_security"),
    )
    warnings = _warnings_from_row(row)
    if "missing_participation_proxy" not in warnings or abs(route - 50.0) > 0.01:
        return route

    target = _feature(row, "target_earning_stability")
    workload = _feature(row, "workload_earning", default=target)
    role = _feature(row, "role_security", default=target)
    production = _feature(row, "weighted_recent_lve_ppg_score", default=target)
    expected = _feature(row, "expected_lve_points_score", default=production)
    proxy = (
        target * 0.38
        + workload * 0.22
        + role * 0.18
        + production * 0.12
        + expected * 0.10
    )
    return round(clamp_score(proxy, 50.0, 92.0), 2)


def _wr_role_target_penalty(row: dict[str, object]) -> float:
    target = _feature(row, "target_earning_stability")
    route = _wr_route_role(row)
    role = _feature(row, "role_security")
    penalty = 0.0
    if target < 60:
        penalty += min(8.0, (60.0 - target) * 0.25)
    elif target < 70:
        penalty += min(2.0, (70.0 - target) * 0.08)
    if route < 62:
        penalty += min(7.0, (62.0 - route) * 0.22)
    elif route < 70:
        penalty += min(2.0, (70.0 - route) * 0.08)
    if role < 60:
        penalty += min(4.0, (60.0 - role) * 0.16)
    if target < 65 and route < 65:
        penalty += 2.0
    return round(clamp_score(penalty, 0.0, 14.0), 2)


def _te_route_role(row: dict[str, object]) -> float:
    return _feature(row, "route_role")


def _te_target_earning(row: dict[str, object]) -> float:
    return _feature(row, "target_earning_stability")


def _te_replacement_level_baseline(row: dict[str, object]) -> float:
    return _feature(row, "te_replacement_level_baseline", default=69.0)


def _te_route_target_penalty(row: dict[str, object]) -> float:
    route = _te_route_role(row)
    target = _te_target_earning(row)
    penalty = 0.0
    if route < 58:
        penalty += min(10.0, (58.0 - route) * 0.35)
    elif route < 72:
        penalty += min(5.0, (72.0 - route) * 0.22)
    if target < 58:
        penalty += min(8.0, (58.0 - target) * 0.30)
    elif target < 68:
        penalty += min(4.0, (68.0 - target) * 0.18)
    if route < 65 and target < 65:
        penalty += 3.0
    return round(clamp_score(penalty, 0.0, 18.0), 2)


def _te_elite_exception(row: dict[str, object], value: float) -> bool:
    route = _te_route_role(row)
    target = _te_target_earning(row)
    expected = _feature(row, "expected_lve_points_score")
    recent = _feature(row, "weighted_recent_lve_ppg_score")
    efficiency = _efficiency_feature(row)
    production_signal = max(expected, recent)
    return (
        route >= 86
        and target >= 82
        and value >= 74
        and (production_signal >= 86 or efficiency >= 86)
    )


def _weighted_items(
    player_id: str,
    component: str,
    items: tuple[tuple[str, float, float], ...],
    *,
    adjustment: float = 0.0,
) -> tuple[float, tuple[StatsFirstContribution, ...]]:
    denominator = sum(weight for _, _, weight in items)
    if denominator <= 0:
        return 50.0, ()
    total = 0.0
    contributions: list[StatsFirstContribution] = []
    for feature_name, score, weight in items:
        contribution = score * weight / denominator
        total += contribution
        contributions.append(
            StatsFirstContribution(
                player_id=player_id,
                component=component,
                feature_name=feature_name,
                normalized_score=round(score, 2),
                feature_weight=weight,
                component_contribution=round(contribution, 4),
            )
        )
    if adjustment:
        contributions.append(
            StatsFirstContribution(
                player_id=player_id,
                component=component,
                feature_name="lve_structural_formula_adjustment",
                normalized_score=round(adjustment, 2),
                feature_weight=0,
                component_contribution=round(adjustment, 4),
            )
        )
    return round(clamp_score(total + adjustment), 2), tuple(contributions)


def _feature(row: dict[str, object], feature_name: str, *, default: float = 50.0) -> float:
    return _score(_float(row.get(feature_name), default))


def _efficiency_feature(row: dict[str, object]) -> float:
    return _feature(
        row,
        "efficiency_score",
        default=_feature(row, "lve_projection_value"),
    )


def _warnings_from_row(row: dict[str, object]) -> set[str]:
    return {part for part in str(row.get("warnings") or "").split("|") if part}


def _boolish(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _score(value: float) -> float:
    return clamp_score(value)
