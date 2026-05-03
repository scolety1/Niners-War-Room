from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.keeper_scores import KeeperDecision, KeeperScoreInputs
from src.models.trade_scores import (
    TRADE_LABELS,
    TradeAsset,
    TradeScoreInputs,
    score_trade,
    trade_asset_value,
    trade_value_gap,
)
from src.services.team_service import build_team_keeper_board


@dataclass(frozen=True)
class TradeCentralBoard:
    snapshot_date: str | None
    player_rows: list[dict[str, object]]
    path_rows: list[dict[str, object]]
    signals: list[str]
    pick_signals: list[str]


def build_trade_central(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> TradeCentralBoard:
    validated = validate_data_pack(data_pack_path)
    joined_rows = _joined_player_rows(validated.rows_by_table)
    team_rows = [row for row in joined_rows if row.get("team_id") == team_id]
    keeper_board = build_team_keeper_board(
        [_keeper_input(row) for row in team_rows],
        team_id=team_id,
        team_name=_team_name(team_rows, team_id),
        protect_limit=protect_limit,
        official_top_five_keep_limit=official_top_five_keep_limit,
    )
    decisions = {decision.player_id: decision for decision in keeper_board.decisions}
    forced_release_ids = {
        player.player_id for player in keeper_board.forced_release_candidates
    }
    player_rows = [
        _player_row(row, decisions.get(str(row["player_id"])), forced_release_ids)
        for row in team_rows
    ]
    pick_rows = _pick_rows(validated.rows_by_table, team_id)
    path_rows = _path_rows(player_rows, pick_rows)
    return TradeCentralBoard(
        snapshot_date=validated.snapshot_date,
        player_rows=sorted(
            player_rows,
            key=lambda row: (
                _signal_order(str(row["signal"])),
                -float(row["trade_value"] or 0.0),
                str(row["player"]),
            ),
        ),
        path_rows=path_rows,
        signals=_ordered_signals({str(row["signal"]) for row in player_rows}),
        pick_signals=_ordered_pick_signals(
            {str(row["path_signal"]) for row in path_rows}
        ),
    )


def _joined_player_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    rankings = _by_player_id(rows_by_table.get("official_rankings", []))
    outputs = _by_player_id(rows_by_table.get("model_outputs", []))
    rows: list[dict[str, object]] = []
    for roster_row in rows_by_table.get("rosters", []):
        player_id = str(roster_row.get("player_id") or "")
        ranking_row = rankings.get(player_id, {})
        output_row = outputs.get(player_id, {})
        row = dict(roster_row)
        row["official_rank"] = _first_present(
            roster_row.get("official_rank"),
            ranking_row.get("official_rank"),
        )
        for column in (
            "private_score",
            "market_score",
            "war_score",
            "keeper_score",
            "drop_candidate_score",
            "pick_adjusted_value",
            "confidence_score",
            "risk_level",
            "recommendation",
        ):
            row[column] = output_row.get(column)
        rows.append(row)
    return rows


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _keeper_input(row: dict[str, object]) -> KeeperScoreInputs:
    formula_value = _optional_float(row.get("keeper_score"))
    if formula_value is None:
        formula_value = _optional_float(row.get("private_score"), 50.0)
    confidence_value = _optional_float(row.get("confidence_score"), 0.0)
    return KeeperScoreInputs(
        player_id=str(row.get("player_id") or ""),
        player_name=str(row.get("player_name") or row.get("player_id") or ""),
        position=str(row.get("position") or ""),
        official_rank=_optional_int(row.get("official_rank")),
        private_score=_optional_float(row.get("private_score"), 50.0),
        market_score=_optional_float(row.get("market_score")),
        confidence_score=_optional_float(row.get("confidence_score"), 0.6),
        roster_status=str(row.get("roster_status") or "rostered"),
        long_term_private_value=_optional_float(
            row.get("long_term_private_value"), formula_value
        ),
        next_2_year_starter_value=_optional_float(
            row.get("next_2_year_starter_value"), formula_value
        ),
        scarcity_bonus=_optional_float(row.get("scarcity_bonus"), formula_value),
        trade_liquidity=_optional_float(row.get("trade_liquidity"), formula_value),
        age_curve=_optional_float(row.get("age_curve"), formula_value),
        risk_adj=_optional_float(row.get("risk_adj"), formula_value),
        build_fit=_optional_float(row.get("build_fit"), formula_value),
        roster_redundancy=_optional_float(row.get("roster_redundancy"), 0.0) or 0.0,
        decline_risk=_optional_float(row.get("decline_risk"), 0.0) or 0.0,
        data_completeness=_optional_float(
            row.get("data_completeness"), confidence_value
        ),
        historical_cohort_size=_optional_float(
            row.get("historical_cohort_size"), confidence_value
        ),
        market_agreement=_optional_float(row.get("market_agreement"), confidence_value),
        model_separation=_optional_float(row.get("model_separation"), confidence_value),
    )


def _team_name(rows: list[dict[str, object]], fallback: str) -> str:
    if not rows:
        return fallback
    return str(rows[0].get("team_name") or fallback)


def _player_row(
    row: dict[str, object],
    decision: KeeperDecision | None,
    forced_release_ids: set[str],
) -> dict[str, object]:
    player_id = str(row.get("player_id") or "")
    forced_release = player_id in forced_release_ids
    model_signal = str(row.get("recommendation") or "").lower()
    trade_value = trade_asset_value(
        _optional_float(row.get("pick_adjusted_value")),
        _optional_float(row.get("confidence_score")),
    )
    market_trade_value = _market_trade_value(row, trade_value)
    keeper_score = _decision_value(decision, "keeper_score")
    drop_score = _decision_value(decision, "drop_candidate_score")
    return {
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "official_rank": row.get("official_rank"),
        "my_score": row.get("private_score"),
        "market_score": row.get("market_score"),
        "war_score": row.get("war_score"),
        "keeper_score": keeper_score,
        "drop_score": drop_score,
        "trade_value": trade_value,
        "private_trade_value": trade_value,
        "market_trade_value": market_trade_value,
        "keeper_trade_value": keeper_score or 0.0,
        "confidence": row.get("confidence_score"),
        "risk": row.get("risk_level"),
        "signal": _trade_signal(
            forced_release=forced_release,
            model_signal=model_signal,
            keeper_score=keeper_score,
            drop_score=drop_score,
        ),
    }


def _trade_signal(
    *,
    forced_release: bool,
    model_signal: str,
    keeper_score: float | None,
    drop_score: float | None,
) -> str:
    if forced_release or model_signal in {"shop", "shop/release"}:
        return "Shop"
    if drop_score is not None and drop_score >= 35:
        return "Drop"
    if keeper_score is not None and keeper_score >= 90:
        return "Shield"
    return "Watch"


def _pick_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
    team_id: str,
) -> list[dict[str, object]]:
    picks = {
        (int(row["pick_year"]), str(row["pick_label"])): row
        for row in rows_by_table.get("future_picks", [])
        if row.get("current_team_id") == team_id
        and row.get("pick_year") is not None
        and row.get("pick_label")
    }
    rows: list[dict[str, object]] = []
    for value_row in rows_by_table.get("pick_values", []):
        key = (int(value_row["pick_year"]), str(value_row["pick_label"]))
        pick_row = picks.get(key)
        if pick_row is None:
            continue
        rows.append(
            {
                "pick": value_row.get("pick_label"),
                "pick_year": value_row.get("pick_year"),
                "overall_pick": value_row.get("overall_pick"),
                "certainty": pick_row.get("certainty") or "unknown",
                "snapshot_value": _optional_float(value_row.get("final_pick_value"), 0.0),
            }
        )
    return rows


def _path_rows(
    player_rows: list[dict[str, object]],
    pick_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidates = [row for row in player_rows if row["signal"] in {"Shop", "Drop"}]
    rows: list[dict[str, object]] = []
    for player in candidates:
        for pick in pick_rows:
            gap = trade_value_gap(pick["snapshot_value"], player["trade_value"])
            trade_score = score_trade(
                TradeScoreInputs(
                    incoming_assets=(_pick_asset(pick),),
                    outgoing_assets=(_player_asset(player),),
                    political_risk=_political_risk(player),
                )
            )
            rows.append(
                {
                    "player": player["player"],
                    "signal": player["signal"],
                    "trade_value": player["trade_value"],
                    "pick": pick["pick"],
                    "certainty": pick["certainty"],
                    "pick_value": pick["snapshot_value"],
                    "value_gap": gap,
                    "private_trade_score": trade_score.private_trade_score,
                    "market_trade_score": trade_score.market_trade_score,
                    "keeper_impact_score": trade_score.keeper_impact_score,
                    "niners_edge_score": trade_score.niners_edge_score,
                    "opponent_benefit_score": trade_score.opponent_benefit_score,
                    "acceptance_chance": trade_score.acceptance_chance,
                    "path_signal": trade_score.label,
                }
            )
    return sorted(
        rows,
        key=lambda row: (abs(float(row["value_gap"])), str(row["pick"])),
    )


def _signal_order(signal: str) -> int:
    return {"Shop": 0, "Drop": 1, "Shield": 2, "Watch": 3}.get(signal, 99)


def _ordered_signals(signals: set[str]) -> list[str]:
    return sorted(signals, key=lambda signal: (_signal_order(signal), signal))


def _ordered_pick_signals(signals: set[str]) -> list[str]:
    order = {label: index for index, label in enumerate(TRADE_LABELS)}
    return sorted(signals, key=lambda signal: (order.get(signal, 99), signal))


def _player_asset(player: dict[str, object]) -> TradeAsset:
    return TradeAsset(
        name=str(player["player"]),
        private_value=float(player["private_trade_value"] or 0.0),
        market_value=float(player["market_trade_value"] or 0.0),
        keeper_value=float(player["keeper_trade_value"] or 0.0),
    )


def _pick_asset(pick: dict[str, object]) -> TradeAsset:
    value = float(pick["snapshot_value"] or 0.0)
    return TradeAsset(
        name=str(pick["pick"]),
        private_value=value,
        market_value=value,
        keeper_value=0.0,
    )


def _market_trade_value(row: dict[str, object], fallback_value: float) -> float:
    private_score = _optional_float(row.get("private_score"))
    market_score = _optional_float(row.get("market_score"))
    pick_adjusted_value = _optional_float(row.get("pick_adjusted_value"))
    confidence_score = _optional_float(row.get("confidence_score"))
    if private_score is None or private_score <= 0 or market_score is None:
        return fallback_value
    market_adjusted_value = (pick_adjusted_value or 0.0) * min(
        max(market_score / private_score, 0.5),
        1.5,
    )
    return trade_asset_value(market_adjusted_value, confidence_score)


def _political_risk(player: dict[str, object]) -> float:
    risk = str(player.get("risk") or "").lower()
    if risk == "high":
        return 25.0
    if risk == "medium":
        return 10.0
    return 0.0


def _decision_value(decision: KeeperDecision | None, attribute: str) -> float | None:
    if decision is None:
        return None
    return getattr(decision, attribute)


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_float(value: object, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)
