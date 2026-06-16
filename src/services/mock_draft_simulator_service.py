from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.draft_state_service import (
    AvailablePlayer,
    DraftBoardState,
    available_players_after_picks,
    current_draft_pick,
    mark_player_drafted,
    next_my_pick,
)

MARKET_CONTEXT_ALLOWED_USE = "opponent_behavior_player_availability_pick_timing_only"
MARKET_CONTEXT_BLOCKED_USE = "nwr_private_quality_score_or_value"
BLOCKED_MARKET_SCORE_FIELDS = frozenset(
    {
        "stats_model_value",
        "model_value",
        "draft_value",
        "nwr_draft_value",
        "nwr_dynasty_score",
        "nwr_quality_score",
        "quality_score",
        "war_score",
    }
)


@dataclass(frozen=True)
class OpponentMarketContext:
    asset_id: str
    player: str
    market_adp: float | None
    source: str
    ignored_score_fields: tuple[str, ...]
    allowed_use: str = MARKET_CONTEXT_ALLOWED_USE
    blocked_use: str = MARKET_CONTEXT_BLOCKED_USE


@dataclass(frozen=True)
class SimulatedOpponentPick:
    overall_pick: int
    pick_label: str
    owner: str
    asset_id: str
    player: str
    position: str
    asset_type: str
    asset_lifecycle: str
    stats_model_value: float
    market_value: float
    market_adp: float | None
    opponent_timing_score: float
    selected_by: str
    selection_reason: str


@dataclass(frozen=True)
class MockDraftReviewScenario:
    review_only: bool
    market_context_policy: str
    starting_current_pick: int | None
    ending_current_pick: int | None
    simulated_picks: tuple[SimulatedOpponentPick, ...]
    availability_at_my_next_pick: tuple[dict[str, object], ...]
    state_after_simulation: DraftBoardState
    warnings: tuple[str, ...]
    quality_score_firewall_passed: bool


def build_review_mock_draft_scenario(
    state: DraftBoardState,
    *,
    market_context_rows: Sequence[Mapping[str, object]] | None = None,
    max_picks: int | None = None,
    opponent_lookahead: int = 10,
    availability_limit: int = 15,
) -> MockDraftReviewScenario:
    """Simulate opponent picks without changing NWR player quality/value fields."""

    context_by_asset, warnings = _market_context_by_asset(market_context_rows or ())
    original_scores = _scores_by_asset(state)
    start_pick = state.current_pick
    scenario_state = state
    simulated: list[SimulatedOpponentPick] = []

    while scenario_state.current_pick is not None:
        if max_picks is not None and len(simulated) >= max_picks:
            break
        current = current_draft_pick(scenario_state)
        if current is None or current.is_my_pick:
            break
        selection = _select_opponent_player(
            scenario_state,
            overall_pick=current.overall_pick,
            market_context_by_asset=context_by_asset,
            opponent_lookahead=opponent_lookahead,
        )
        if selection is None:
            warnings.append("Simulation stopped because no available player remained.")
            break
        player, market_context, timing_score, reason = selection
        scenario_state = mark_player_drafted(
            scenario_state,
            player.asset_id,
            overall_pick=current.overall_pick,
        )
        simulated.append(
            SimulatedOpponentPick(
                overall_pick=current.overall_pick,
                pick_label=current.pick_label,
                owner=current.current_owner,
                asset_id=player.asset_id,
                player=player.player,
                position=player.position,
                asset_type=player.asset_type,
                asset_lifecycle=player.asset_lifecycle,
                stats_model_value=player.stats_model_value,
                market_value=player.market_value,
                market_adp=market_context.market_adp if market_context else None,
                opponent_timing_score=timing_score,
                selected_by="opponent_market_timing" if market_context else "fallback_board_order",
                selection_reason=reason,
            )
        )

    score_firewall_passed = _scores_by_asset(scenario_state) == original_scores
    if not score_firewall_passed:
        warnings.append("Blocked: simulated picks changed an NWR quality/value field.")

    return MockDraftReviewScenario(
        review_only=True,
        market_context_policy=(
            "ADP/market context is used only for opponent timing and availability. "
            "NWR quality/value fields are copied unchanged from the input state."
        ),
        starting_current_pick=start_pick,
        ending_current_pick=scenario_state.current_pick,
        simulated_picks=tuple(simulated),
        availability_at_my_next_pick=_availability_rows(
            scenario_state,
            market_context_by_asset=context_by_asset,
            limit=availability_limit,
        ),
        state_after_simulation=scenario_state,
        warnings=tuple(warnings),
        quality_score_firewall_passed=score_firewall_passed,
    )


def _market_context_by_asset(
    rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, OpponentMarketContext], list[str]]:
    contexts: dict[str, OpponentMarketContext] = {}
    warnings: list[str] = []
    for row in rows:
        asset_id = str(row.get("asset_id") or "").strip()
        if not asset_id:
            continue
        ignored = tuple(
            sorted(
                key
                for key, value in row.items()
                if key in BLOCKED_MARKET_SCORE_FIELDS and value not in (None, "")
            )
        )
        if ignored:
            warnings.append(
                "Ignored market context score/value fields for "
                f"{asset_id}: {', '.join(ignored)}."
            )
        contexts[asset_id] = OpponentMarketContext(
            asset_id=asset_id,
            player=str(row.get("player") or ""),
            market_adp=_optional_float(
                row.get("market_adp"),
                row.get("adp"),
                row.get("overall_adp"),
                row.get("expected_pick"),
            ),
            source=str(row.get("source") or "market_context"),
            ignored_score_fields=ignored,
        )
    return contexts, warnings


def _select_opponent_player(
    state: DraftBoardState,
    *,
    overall_pick: int,
    market_context_by_asset: Mapping[str, OpponentMarketContext],
    opponent_lookahead: int,
) -> tuple[AvailablePlayer, OpponentMarketContext | None, float, str] | None:
    remaining = available_players_after_picks(state)
    if not remaining:
        return None

    market_candidates = [
        (
            player,
            market_context_by_asset[player.asset_id],
        )
        for player in remaining
        if player.asset_id in market_context_by_asset
        and market_context_by_asset[player.asset_id].market_adp is not None
    ]
    near_market = [
        (player, context)
        for player, context in market_candidates
        if float(context.market_adp or 999) <= overall_pick + opponent_lookahead
    ]
    if near_market:
        player, context = min(
            near_market,
            key=lambda item: (
                max(float(item[1].market_adp or 999) - overall_pick, 0.0),
                float(item[1].market_adp or 999),
                item[0].player,
            ),
        )
        timing_score = _opponent_timing_score(
            overall_pick=overall_pick,
            market_adp=context.market_adp,
        )
        return (
            player,
            context,
            timing_score,
            "Selected from ADP/market timing window; NWR score ignored for selection.",
        )

    fallback = min(remaining, key=lambda player: (player.draft_rank, player.player))
    return (
        fallback,
        None,
        0.0,
        "No ADP/market timing row in range; used fallback board order for review only.",
    )


def _availability_rows(
    state: DraftBoardState,
    *,
    market_context_by_asset: Mapping[str, OpponentMarketContext],
    limit: int,
) -> tuple[dict[str, object], ...]:
    my_pick = next_my_pick(state)
    rows: list[dict[str, object]] = []
    for player in available_players_after_picks(state)[:limit]:
        context = market_context_by_asset.get(player.asset_id)
        rows.append(
            {
                "next_my_pick": my_pick.pick_label if my_pick else "",
                "asset_id": player.asset_id,
                "player": player.player,
                "position": player.position,
                "asset_type": player.asset_type,
                "asset_lifecycle": player.asset_lifecycle,
                "stats_model_value": player.stats_model_value,
                "market_value": player.market_value,
                "market_adp": context.market_adp if context else "",
                "market_context_used": bool(context and context.market_adp is not None),
                "nwr_score_status": "unchanged_from_input",
                "allowed_use": "review_next_pick_availability",
                "blocked_use": MARKET_CONTEXT_BLOCKED_USE,
            }
        )
    return tuple(rows)


def _scores_by_asset(state: DraftBoardState) -> dict[str, float]:
    scores = {player.asset_id: player.stats_model_value for player in state.available_players}
    scores.update(
        {player.asset_id: player.stats_model_value for player in state.drafted_players}
    )
    return scores


def _opponent_timing_score(*, overall_pick: int, market_adp: float | None) -> float:
    if market_adp is None:
        return 0.0
    if market_adp >= overall_pick:
        return round(max(0.0, 100.0 - ((market_adp - overall_pick) * 5.0)), 2)
    return round(100.0 + min(20.0, (overall_pick - market_adp) * 2.0), 2)


def _optional_float(*values: object) -> float | None:
    for value in values:
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None
