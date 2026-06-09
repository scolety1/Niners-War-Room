from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.keeper_scores import KeeperDecision, KeeperScoreInputs
from src.models.trade_scores import (
    TradeAsset,
    TradeScoreInputs,
    score_trade,
    trade_asset_value,
    trade_value_gap,
)
from src.services.market_influence_policy_service import (
    first_market_value,
    market_edge_classification,
    market_status_warning,
    market_value_status,
    safe_market_edge_score,
)
from src.services.review_score_envelope_service import active_pack_private_score_context
from src.services.table_sort_service import SortSpec
from src.services.team_service import build_team_keeper_board
from src.services.warning_language_service import warning_summary

# Compatibility-only quarantine: legacy Trade Central API names are preserved for
# old callers, but legacy active-pack scores cannot become primary review scores.
LEGACY_TRADE_SERVICE_COMPATIBILITY_QUARANTINE_NOTE = (
    "compatibility_only_legacy_active_pack_score_not_primary"
)

TRADE_PLAYER_SORT = SortSpec(
    table_key="trade_players",
    label="Roster review group, then context value",
    sort_columns=("signal", "trade_value", "player"),
    directions=("custom", "desc", "asc"),
    meaning=(
        "Manual review groups appear before holds; higher context value appears "
        "first within a group."
    ),
)
TRADE_PICK_PATH_SORT = SortSpec(
    table_key="trade_pick_paths",
    label="Closest value gap, then pick",
    sort_columns=("value_gap_absolute", "pick"),
    directions=("asc", "asc"),
    meaning="Potential pick paths closest to even value appear first.",
)
TRADE_BUY_TARGET_SORT = SortSpec(
    table_key="trade_external_asset_reviews",
    label="Model desirability descending, then acceptance likelihood",
    sort_columns=("model_desirability", "acceptance_likelihood", "player"),
    directions=("desc", "desc", "asc"),
    meaning=(
        "Opponent assets with stronger model context appear first; acceptance "
        "likelihood is displayed as context only."
    ),
)
TRADE_MARKET_EDGE_SORT = SortSpec(
    table_key="trade_market_edge",
    label="Absolute market edge descending, then player",
    sort_columns=("absolute_market_edge", "player"),
    directions=("desc", "asc"),
    meaning="Largest model-versus-market disagreements appear first.",
)
TRADE_PACKAGE_SORT = SortSpec(
    table_key="trade_package_builder",
    label="Model edge descending, then acceptance likelihood",
    sort_columns=("model_edge", "acceptance_likelihood", "package"),
    directions=("desc", "desc", "asc"),
    meaning=(
        "Packages with better model edge appear first; acceptance likelihood is "
        "not treated as desirability."
    ),
)


@dataclass(frozen=True)
class TradeCentralBoard:
    snapshot_date: str | None
    player_rows: list[dict[str, object]]
    # Compatibility-only API names retained until a future adapter quarantine.
    sell_rows: list[dict[str, object]]
    buy_rows: list[dict[str, object]]
    market_edge_rows: list[dict[str, object]]
    package_rows: list[dict[str, object]]
    path_rows: list[dict[str, object]]
    signals: list[str]
    buy_signals: list[str]
    edge_types: list[str]
    pick_signals: list[str]
    sort_metadata: dict[str, SortSpec]


def build_trade_central(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> TradeCentralBoard:
    validated = validate_data_pack(data_pack_path)
    joined_rows = _joined_player_rows(validated.rows_by_table, data_pack_path=data_pack_path)
    resolved_team_id = _resolve_team_id(joined_rows, team_id)
    team_rows = [
        row for row in joined_rows if str(row.get("team_id") or "") == resolved_team_id
    ]
    opponent_rows = [
        row for row in joined_rows if str(row.get("team_id") or "") != resolved_team_id
    ]
    keeper_board = build_team_keeper_board(
        [_keeper_input(row) for row in team_rows],
        team_id=resolved_team_id,
        team_name=_team_name(team_rows, resolved_team_id),
        protect_limit=protect_limit,
        official_top_five_keep_limit=official_top_five_keep_limit,
    )
    decisions = {decision.player_id: decision for decision in keeper_board.decisions}
    if _has_scored_model_outputs(team_rows):
        forced_release_ids = {
            str(row.get("player_id") or "")
            for row in _visible_forced_release_rows(_visible_top_five_rows(team_rows))
        }
    else:
        forced_release_ids = {
            player.player_id for player in keeper_board.forced_release_candidates
        }
    sell_rows = [
        _player_row(row, decisions.get(str(row["player_id"])), forced_release_ids)
        for row in team_rows
    ]
    buy_rows = [_buy_target_row(row) for row in opponent_rows]
    player_rows = sorted(
        sell_rows,
        key=lambda row: (
            _signal_order(str(row["signal"])),
            -float(row["trade_value"] or 0.0),
            str(row["player"]),
        ),
    )
    own_pick_rows = _pick_rows(validated.rows_by_table, resolved_team_id)
    opponent_pick_rows = _opponent_pick_rows(validated.rows_by_table, resolved_team_id)
    path_rows = _path_rows(player_rows, own_pick_rows)
    market_edge_rows = _market_edge_rows(player_rows, buy_rows)
    package_rows = _package_rows(
        sell_rows=player_rows,
        buy_rows=buy_rows,
        own_pick_rows=own_pick_rows,
        opponent_pick_rows=opponent_pick_rows,
    )
    return TradeCentralBoard(
        snapshot_date=validated.snapshot_date,
        player_rows=player_rows,
        sell_rows=player_rows,
        buy_rows=sorted(
            buy_rows,
            key=lambda row: (
                -float(row["model_desirability"] or 0.0),
                -float(row["acceptance_likelihood"] or 0.0),
                str(row["player"]),
            ),
        ),
        market_edge_rows=market_edge_rows,
        package_rows=package_rows,
        path_rows=path_rows,
        signals=_ordered_signals({str(row["signal"]) for row in player_rows}),
        buy_signals=_ordered_buy_signals({str(row["buy_signal"]) for row in buy_rows}),
        edge_types=_ordered_edge_types(
            {str(row["edge_type"]) for row in market_edge_rows}
        ),
        pick_signals=_ordered_pick_signals(
            {str(row["path_signal"]) for row in path_rows}
        ),
        sort_metadata={
            "player_rows": TRADE_PLAYER_SORT,
            "sell_rows": TRADE_PLAYER_SORT,
            "buy_rows": TRADE_BUY_TARGET_SORT,
            "market_edge_rows": TRADE_MARKET_EDGE_SORT,
            "package_rows": TRADE_PACKAGE_SORT,
            "path_rows": TRADE_PICK_PATH_SORT,
        },
    )


def _joined_player_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
    *,
    data_pack_path: str | Path,
) -> list[dict[str, object]]:
    rankings = _by_player_id(rows_by_table.get("official_rankings", []))
    outputs = _by_player_id(rows_by_table.get("model_outputs", []))
    rows: list[dict[str, object]] = []
    for roster_row in rows_by_table.get("rosters", []):
        player_id = str(roster_row.get("player_id") or "")
        ranking_row = rankings.get(player_id, {})
        output_row = outputs.get(player_id, {})
        row = dict(roster_row)
        row["league_rank"] = _first_present(
            roster_row.get("league_rank"),
            ranking_row.get("league_rank"),
            roster_row.get("official_rank"),
            ranking_row.get("official_rank"),
        )
        row["official_rank"] = row["league_rank"]
        for column in (
            "private_score",
            "market_score",
            "market_trade_value",
            "market_edge_score",
            "market_edge_label",
            "war_score",
            "keeper_score",
            "drop_candidate_score",
            "pick_adjusted_value",
            "confidence_score",
            "risk_level",
            "recommendation",
            "warning_status",
            "warning_reasons",
            "model_version",
            "notes",
        ):
            row[column] = output_row.get(column)
        row.update(
            active_pack_private_score_context(
                output_row,
                source_path=str(Path(data_pack_path) / "model_outputs.csv"),
                score_as_of_date=str(output_row.get("snapshot_date") or ""),
                asset_id=player_id,
                display_name=str(row.get("player_name") or player_id),
            )
        )
        rows.append(row)
    return rows


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _resolve_team_id(rows: list[dict[str, object]], requested_team_id: str) -> str:
    if any(str(row.get("team_id") or "") == requested_team_id for row in rows):
        return requested_team_id
    normalized_request = _normalize_name(requested_team_id)
    for row in rows:
        team_id = str(row.get("team_id") or "")
        team_name = str(row.get("team_name") or "")
        if _normalize_name(team_name) == normalized_request:
            return team_id
    if normalized_request == "niners":
        for row in rows:
            team_id = str(row.get("team_id") or "")
            team_name = str(row.get("team_name") or "")
            if _normalize_name(team_name) == "niners":
                return team_id
    return requested_team_id


def _normalize_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


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
    private_value = _score(row.get("private_score"))
    market_context = _market_context(row, private_value)
    market_value = market_context["market_value"]
    market_value_for_math = _score(market_value, private_value)
    market_edge = _score(market_context["market_edge"], 0.0)
    keeper_score = _decision_value(decision, "keeper_score")
    drop_score = _decision_value(decision, "drop_candidate_score")
    if _is_scored_model_row(row):
        keeper_score = _optional_float(row.get("keeper_score"))
        drop_score = _optional_float(row.get("drop_candidate_score"))
    return {
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "league_rank": row.get("league_rank"),
        "official_rank": row.get("official_rank"),
        "my_score": row.get("private_score"),
        "private_lve_value": row.get("private_score"),
        # Active-pack private_score disclosure only; primary_review_score remains blank.
        "primary_review_score": row.get("primary_review_score", ""),
        "legacy_active_pack_score": row.get("legacy_active_pack_score", ""),
        "score_lineage_class": row.get("score_lineage_class", ""),
        "score_source_column": row.get("score_source_column", ""),
        "score_model_version": row.get("score_model_version", ""),
        "score_manual_decision_required": row.get("score_manual_decision_required", False),
        "legacy_formula_warning": row.get("legacy_formula_warning", False),
        "stale_or_legacy_formula_warning": row.get("stale_or_legacy_formula_warning", False),
        "model_value": round(private_value, 2),
        "market_value": round(market_value, 2) if market_value is not None else "",
        "market_value_status": market_context["market_value_status"],
        "market_edge": round(market_edge, 2) if market_context["market_edge"] is not None else "",
        "edge_type": market_context["edge_type"],
        "market_edge_warning": market_context["market_edge_warning"],
        "acceptance_likelihood": _sell_acceptance_likelihood(
            market_value=market_value_for_math,
            private_value=private_value,
            signal=str(row.get("recommendation") or ""),
            forced_release=forced_release,
        ),
        "model_desirability": _sell_desirability(
            private_value=private_value,
            drop_score=drop_score,
            forced_release=forced_release,
        ),
        "market_score": row.get("market_score"),
        "trade_liquidity": row.get("market_score"),
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
        "team": row.get("team_name"),
        "team_id": row.get("team_id"),
    }


def _trade_signal(
    *,
    forced_release: bool,
    model_signal: str,
    keeper_score: float | None,
    drop_score: float | None,
) -> str:
    if forced_release or model_signal in {"shop", "shop/release"}:
        return "Roster Context Review"
    if drop_score is not None and drop_score >= 35:
        return "Manual Roster Review"
    if keeper_score is not None and keeper_score >= 90:
        return "Hold Value Context"
    return "Watch"


def _buy_target_row(row: dict[str, object]) -> dict[str, object]:
    private_value = _score(row.get("private_score"))
    market_context = _market_context(row, private_value)
    market_value = market_context["market_value"]
    market_value_for_math = _score(market_value, private_value)
    market_edge = _score(market_context["market_edge"], 0.0)
    confidence = _confidence(row.get("confidence_score"))
    desirability = _buy_desirability(
        private_value=private_value,
        market_edge=market_edge,
        confidence=confidence,
    )
    acceptance = _buy_acceptance_likelihood(
        market_value=market_value_for_math,
        market_edge=market_edge,
        recommendation=str(row.get("recommendation") or ""),
    )
    buy_signal = _buy_signal(desirability, acceptance, market_edge)
    return {
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "team": row.get("team_name"),
        "team_id": row.get("team_id"),
        "league_rank": row.get("league_rank"),
        "model_value": round(private_value, 2),
        # Active-pack private_score disclosure only; primary_review_score remains blank.
        "primary_review_score": row.get("primary_review_score", ""),
        "legacy_active_pack_score": row.get("legacy_active_pack_score", ""),
        "score_lineage_class": row.get("score_lineage_class", ""),
        "score_source_column": row.get("score_source_column", ""),
        "score_model_version": row.get("score_model_version", ""),
        "score_manual_decision_required": row.get("score_manual_decision_required", False),
        "legacy_formula_warning": row.get("legacy_formula_warning", False),
        "stale_or_legacy_formula_warning": row.get("stale_or_legacy_formula_warning", False),
        "market_value": round(market_value, 2) if market_value is not None else "",
        "market_value_status": market_context["market_value_status"],
        "market_edge": round(market_edge, 2) if market_context["market_edge"] is not None else "",
        "edge_type": market_context["edge_type"],
        "market_edge_warning": market_context["market_edge_warning"],
        "model_desirability": round(desirability, 2),
        "acceptance_likelihood": round(acceptance, 2),
        "buy_signal": buy_signal,
        "acquisition_path": _acquisition_path(buy_signal),
        "confidence": round(confidence, 2),
        "risk": row.get("risk_level"),
        "warning_status": row.get("warning_status") or "",
        "warning_reason": _clean_warning(row.get("warning_reasons")),
        "trade_value": trade_asset_value(
            _optional_float(row.get("pick_adjusted_value")),
            _optional_float(row.get("confidence_score")),
        ),
        "private_trade_value": trade_asset_value(
            _optional_float(row.get("pick_adjusted_value")),
            _optional_float(row.get("confidence_score")),
        ),
        "market_trade_value": _market_trade_value(row, 0.0),
        "keeper_trade_value": _optional_float(row.get("keeper_score"), 0.0) or 0.0,
    }


def _buy_signal(desirability: float, acceptance: float, market_edge: float) -> str:
    if desirability >= 72 and acceptance >= 35:
        return "External Asset Context"
    if market_edge >= 8 and acceptance >= 20:
        return "Value Gap Context"
    if desirability >= 65:
        return "Cost Review Context"
    return "Manual Review Context"


def _acquisition_path(buy_signal: str) -> str:
    if buy_signal == "External Asset Context":
        return "Review only if roster question remains open."
    if buy_signal == "Value Gap Context":
        return "Market/model disagreement context only."
    if buy_signal == "Cost Review Context":
        return "Market cost context; no automatic action."
    return "Manual review only unless new information changes."


def _buy_desirability(
    *,
    private_value: float,
    market_edge: float,
    confidence: float,
) -> float:
    return _clamp((0.72 * private_value) + (0.18 * confidence) + (0.55 * max(0.0, market_edge)))


def _sell_desirability(
    *,
    private_value: float,
    drop_score: float | None,
    forced_release: bool,
) -> float:
    forced_bonus = 14.0 if forced_release else 0.0
    return _clamp((0.65 * (100.0 - private_value)) + (0.35 * (drop_score or 0.0)) + forced_bonus)


def _buy_acceptance_likelihood(
    *,
    market_value: float,
    market_edge: float,
    recommendation: str,
) -> float:
    recommendation_bonus = 8.0 if recommendation.lower() in {"shop", "drop"} else 0.0
    discount_penalty = max(0.0, market_edge) * 0.65
    return _clamp(76.0 - (0.35 * market_value) - discount_penalty + recommendation_bonus)


def _sell_acceptance_likelihood(
    *,
    market_value: float,
    private_value: float,
    signal: str,
    forced_release: bool,
) -> float:
    signal_bonus = 12.0 if signal.lower() in {"shop", "shop/release", "drop"} else 0.0
    forced_bonus = 10.0 if forced_release else 0.0
    market_premium = max(0.0, market_value - private_value) * 0.45
    return _clamp(42.0 + (0.30 * market_value) + market_premium + signal_bonus + forced_bonus)


def _visible_top_five_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked_rows = [row for row in rows if _optional_int(row.get("league_rank")) is not None]
    return sorted(
        ranked_rows,
        key=lambda row: (
            _optional_int(row.get("league_rank")) or 999,
            str(row.get("player_name")),
        ),
    )[:5]


def _visible_forced_release_rows(
    top_five_rows: list[dict[str, object]],
    official_top_five_keep_limit: int = 4,
) -> list[dict[str, object]]:
    release_count = max(0, len(top_five_rows) - official_top_five_keep_limit)
    if release_count == 0:
        return []
    return sorted(
        top_five_rows,
        key=lambda row: (
            -(_optional_float(row.get("drop_candidate_score"), 0.0) or 0.0),
            _optional_float(row.get("keeper_score"), 0.0) or 0.0,
            _optional_int(row.get("league_rank")) or 999,
            str(row.get("player_name")),
        ),
    )[:release_count]


def _has_scored_model_outputs(rows: list[dict[str, object]]) -> bool:
    return bool(rows) and all(_is_scored_model_row(row) for row in rows)


def _is_scored_model_row(row: dict[str, object]) -> bool:
    return bool(row.get("model_version")) and "Neutral placeholder" not in str(
        row.get("notes") or ""
    )


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


def _opponent_pick_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
    team_id: str,
) -> list[dict[str, object]]:
    picks = {
        (int(row["pick_year"]), str(row["pick_label"])): row
        for row in rows_by_table.get("future_picks", [])
        if row.get("current_team_id") != team_id
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
                "owner_team": pick_row.get("current_team_name"),
                "owner_team_id": pick_row.get("current_team_id"),
                "certainty": pick_row.get("certainty") or "unknown",
                "snapshot_value": _optional_float(value_row.get("final_pick_value"), 0.0),
            }
        )
    return rows


def _path_rows(
    player_rows: list[dict[str, object]],
    pick_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidates = [
        row
        for row in player_rows
        if row["signal"] in {"Roster Context Review", "Manual Roster Review"}
    ]
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
                    "path_signal": _review_only_trade_label(trade_score.label),
                }
            )
    return sorted(
        rows,
        key=lambda row: (abs(float(row["value_gap"])), str(row["pick"])),
    )


def _market_edge_rows(
    sell_rows: list[dict[str, object]],
    buy_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in sell_rows:
        edge = _optional_float(row.get("market_edge"))
        edge_for_sort = edge if edge is not None else 0.0
        rows.append(
            {
                "player": row.get("player"),
                "pos": row.get("pos"),
                "team": row.get("team"),
                "side": "Roster",
                "signal": row.get("signal"),
                "model_value": row.get("model_value"),
                "market_value": row.get("market_value"),
                "market_value_status": row.get("market_value_status", ""),
                "market_edge": edge if edge is not None else "",
                "absolute_market_edge": abs(edge_for_sort),
                "edge_type": row.get("edge_type") or _edge_type(edge_for_sort),
                "market_edge_warning": row.get("market_edge_warning", ""),
                "model_desirability": row.get("model_desirability"),
                "acceptance_likelihood": row.get("acceptance_likelihood"),
            }
        )
    for row in buy_rows:
        edge = _optional_float(row.get("market_edge"))
        edge_for_sort = edge if edge is not None else 0.0
        rows.append(
            {
                "player": row.get("player"),
                "pos": row.get("pos"),
                "team": row.get("team"),
                "side": "External",
                "signal": row.get("buy_signal"),
                "model_value": row.get("model_value"),
                "market_value": row.get("market_value"),
                "market_value_status": row.get("market_value_status", ""),
                "market_edge": edge if edge is not None else "",
                "absolute_market_edge": abs(edge_for_sort),
                "edge_type": row.get("edge_type") or _edge_type(edge_for_sort),
                "market_edge_warning": row.get("market_edge_warning", ""),
                "model_desirability": row.get("model_desirability"),
                "acceptance_likelihood": row.get("acceptance_likelihood"),
            }
        )
    return sorted(
        rows,
        key=lambda row: (-float(row["absolute_market_edge"] or 0.0), str(row["player"])),
    )


def _package_rows(
    *,
    sell_rows: list[dict[str, object]],
    buy_rows: list[dict[str, object]],
    own_pick_rows: list[dict[str, object]],
    opponent_pick_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    sell_candidates = [
        row
        for row in sell_rows
        if row["signal"] in {"Roster Context Review", "Manual Roster Review"}
    ][:8]
    buy_candidates = [
        row
        for row in buy_rows
        if row["buy_signal"] in {"External Asset Context", "Value Gap Context"}
    ][:8]
    for buy in buy_candidates:
        for pick in own_pick_rows[:5]:
            score = score_trade(
                TradeScoreInputs(
                    incoming_assets=(_buy_asset(buy),),
                    outgoing_assets=(_pick_asset(pick),),
                    political_risk=_buy_political_risk(buy),
                )
            )
            rows.append(
                _package_row(
                    package=f"{pick['pick']} for {buy['player']}",
                    incoming=str(buy["player"]),
                    outgoing=str(pick["pick"]),
                    counterparty=str(buy.get("team") or ""),
                    score=score,
                    model_value=float(buy.get("model_value") or 0.0),
                    market_value=float(buy.get("market_value") or 0.0),
                    roster_spot_cost=1,
                )
            )
    for sell in sell_candidates:
        for pick in opponent_pick_rows[:5]:
            score = score_trade(
                TradeScoreInputs(
                    incoming_assets=(_pick_asset(pick),),
                    outgoing_assets=(_player_asset(sell),),
                    political_risk=_political_risk(sell),
                )
            )
            rows.append(
                _package_row(
                    package=f"{sell['player']} for {pick['pick']}",
                    incoming=str(pick["pick"]),
                    outgoing=str(sell["player"]),
                    counterparty=str(pick.get("owner_team") or ""),
                    score=score,
                    model_value=float(sell.get("model_value") or 0.0),
                    market_value=float(sell.get("market_value") or 0.0),
                    roster_spot_cost=-1,
                )
            )
    return sorted(
        rows,
        key=lambda row: (
            -float(row["model_edge"] or 0.0),
            -float(row["acceptance_likelihood"] or 0.0),
            str(row["package"]),
        ),
    )


def _package_row(
    *,
    package: str,
    incoming: str,
    outgoing: str,
    counterparty: str,
    score,
    model_value: float,
    market_value: float,
    roster_spot_cost: int,
) -> dict[str, object]:
    return {
        "package": package,
        "incoming": incoming,
        "outgoing": outgoing,
        "counterparty": counterparty,
        "model_value": round(model_value, 2),
        "market_value": round(market_value, 2),
        "model_edge": score.niners_edge_score,
        "acceptance_likelihood": score.acceptance_chance,
        "model_desirability": score.private_trade_score,
        "opponent_benefit": score.opponent_benefit_score,
        "roster_spot_cost": roster_spot_cost,
        "trade_label": _review_only_trade_label(score.label),
    }


def _signal_order(signal: str) -> int:
    return {
        "Roster Context Review": 0,
        "Manual Roster Review": 1,
        "Hold Value Context": 2,
        "Watch": 3,
    }.get(signal, 99)


def _ordered_signals(signals: set[str]) -> list[str]:
    return sorted(signals, key=lambda signal: (_signal_order(signal), signal))


def _ordered_buy_signals(signals: set[str]) -> list[str]:
    order = {
        "External Asset Context": 0,
        "Value Gap Context": 1,
        "Cost Review Context": 2,
        "Manual Review Context": 3,
    }
    return sorted(signals, key=lambda signal: (order.get(signal, 99), signal))


def _ordered_edge_types(edge_types: set[str]) -> list[str]:
    order = {
        "Model Higher Market Context": 0,
        "Market Higher Model Context": 1,
        "Market Close": 2,
    }
    return sorted(edge_types, key=lambda edge_type: (order.get(edge_type, 99), edge_type))


def _ordered_pick_signals(signals: set[str]) -> list[str]:
    order = {
        "REVIEW_ONLY_POSITIVE_CONTEXT": 0,
        "REVIEW_ONLY_CONTEXT": 1,
        "HOLD_VALUE_CONTEXT": 2,
        "MANUAL_REVIEW_CONTEXT": 3,
        "POLITICAL_RISK_CONTEXT": 4,
    }
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


def _buy_asset(player: dict[str, object]) -> TradeAsset:
    return TradeAsset(
        name=str(player["player"]),
        private_value=float(player.get("private_trade_value") or player.get("trade_value") or 0.0),
        market_value=float(player.get("market_trade_value") or player.get("trade_value") or 0.0),
        keeper_value=float(player.get("keeper_trade_value") or 0.0),
    )


def _market_context(row: dict[str, object], private_value: float) -> dict[str, object]:
    status = market_value_status(row)
    market_value = first_market_value(row)
    edge = safe_market_edge_score(
        private_value,
        market_value,
        status,
        explicit_edge=row.get("market_edge_score"),
    )
    warning = str(row.get("market_edge_warning") or "")
    status_warning = market_status_warning(status)
    if status_warning != "none":
        warning = status_warning
    return {
        "market_value_status": status,
        "market_value": market_value,
        "market_edge": edge,
        "edge_type": _edge_type_from_status(status, edge),
        "market_edge_warning": warning,
    }


def _edge_type_from_status(status: str, edge: float | None) -> str:
    classification = market_edge_classification(status, edge)
    if status != "real_imported_market" or edge is None:
        return classification.replace("_", " ").title()
    return _edge_type(edge)


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


def _buy_political_risk(player: dict[str, object]) -> float:
    if str(player.get("buy_signal") or "") == "Cost Review Context":
        return 15.0
    risk = str(player.get("risk") or "").lower()
    if risk == "high":
        return 20.0
    if risk == "medium":
        return 8.0
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


def _score(value: object, default: float = 50.0) -> float:
    if value is None or value == "":
        return default
    return max(-100.0, min(100.0, float(value)))


def _confidence(value: object) -> float:
    score = _score(value, 50.0)
    if 0.0 < score <= 1.0:
        return round(score * 100.0, 2)
    return score


def _market_edge(row: dict[str, object], private_value: float, market_value: float) -> float:
    explicit = row.get("market_edge_score")
    if explicit is not None and explicit != "":
        return _score(explicit, 0.0)
    return _score(private_value - market_value, 0.0)


def _edge_type(edge: float) -> str:
    if edge >= 5:
        return "Model Higher Market Context"
    if edge <= -5:
        return "Market Higher Model Context"
    return "Market Close"


def _review_only_trade_label(label: object) -> str:
    mapping = {
        "OFFER": "REVIEW_ONLY_POSITIVE_CONTEXT",
        "CONSIDER": "REVIEW_ONLY_CONTEXT",
        "HOLD": "HOLD_VALUE_CONTEXT",
        "DECLINE": "MANUAL_REVIEW_CONTEXT",
        "AVOID": "MANUAL_REVIEW_CONTEXT",
        "POLITICAL RISK": "POLITICAL_RISK_CONTEXT",
    }
    return mapping.get(str(label or "").upper(), "MANUAL_REVIEW_CONTEXT")


def _clean_warning(value: object) -> str:
    return warning_summary(value, default="")


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))
