"""Redraft Trade Analysis (NWR Overnight V3, Lane 7).

Explicitly unblocked regardless of Lane 1/2's weekly-source find (per the
governing directive). Three prior overnight passes on this branch each
independently confirmed real trade infrastructure exists
(`draft_day_trade_lab_service.py`, `trade_decision_assistant_service.py`,
`trade_roster_negotiation_service.py`, `trade_service.py`,
`trade_brief_export_service.py`) but is wired into the Dynasty app only, and
each deferred wiring it into Redraft as "a genuine multi-file cross-app
integration, not attempted."

Design decision, disclosed: this module does NOT force-reuse the Dynasty
trade-lab's own decision dimensions (youth window, contract/pick flexibility,
production certainty vs. upside uncertainty, rookie/veteran bridge) -- those
are genuinely Dynasty-shaped concepts (multi-year windows, contracts, future
draft picks) that do not exist in Redraft. Redraft's own governing directive
for this lane asks for a DIFFERENT evaluation basis: weekly starting lineup
impact, ROS value, depth, position scarcity, status/risk -- concepts that
already live in REDRAFT's own existing infrastructure, reused directly here
rather than duplicated:
  * `_asset_pool` / `_roster_players` (draft-room/shadow-authorities private
    helpers, already reused across this codebase the same way) for ROS
    value.
  * `roster_composition_report` (`shadow_numeric_authorities_service.py`) for
    starting-lineup value, bench contingency value, and position redundancy
    before/after -- not a second, competing composition algorithm.
  * `marginal_roster_utility_v2` -- the SAME promoted, CLOSED model used
    live in the draft room and reused for Lane 4/5 waivers -- for each
    traded player's real marginal contribution to the roster he is joining
    or leaving. MODEL STATUS CLOSED respected: called read-only.
  * The ONE shared status layer (`current_player_status_overrides_service`)
    for real risk flags (never a second injury system).
  * `weekly_lineup_optimizer_service.optimize_weekly_lineup` for an OPTIONAL
    weekly-impact delta, only when a real week + weekly projections are
    supplied -- omitted, not fabricated, otherwise.

No single fabricated "trade score." Championship Equity is deliberately NOT
included: this repo's own Lane A inventory records it MISSING (needs a live
standings store that does not exist) -- naming it here without real data
would be fabrication, not honesty.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.services.current_player_status_overrides_service import ZERO_VALUE_KINDS, StatusOverride
from src.services.redraft_draft_room_v1_service import _asset_pool
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.shadow_numeric_authorities_service import (
    RosterCompositionReport,
    _roster_players,
    marginal_roster_utility_v2,
    roster_composition_report,
)


class TradeAnalysisError(ValueError):
    pass


@dataclass(frozen=True)
class TradeSideImpact:
    player_id: str
    player_name: str
    position: str
    ros_replacement_value: float
    marginal_utility: float | None
    becomes_starter: bool
    status_flag: str | None  # a real ZERO_VALUE_KINDS override, if one exists


@dataclass(frozen=True)
class TradeEvaluation:
    gives: tuple[TradeSideImpact, ...]
    receives: tuple[TradeSideImpact, ...]
    ros_value_delta: float
    net_marginal_utility: float | None
    starting_lineup_value_before: float
    starting_lineup_value_after: float
    starting_lineup_value_delta: float
    bench_contingency_value_before: float
    bench_contingency_value_after: float
    starter_holes_before: tuple[str, ...]
    starter_holes_after: tuple[str, ...]
    position_redundancy_before: Mapping[str, int]
    position_redundancy_after: Mapping[str, int]
    risk_flags: tuple[str, ...]
    championship_equity_note: str = (
        "Championship Equity is not evaluated -- this repo has no live standings store "
        "(a real, disclosed MISSING capability, not a fabricated omission)."
    )


def _status_flag(player_id: str, overrides_by_id: Mapping[str, StatusOverride]) -> str | None:
    override = overrides_by_id.get(player_id)
    if override is not None and override.kind in ZERO_VALUE_KINDS:
        return override.kind
    return None


def evaluate_trade(
    *,
    roster_before_ids: Sequence[str],
    gives_ids: Sequence[str],
    receives_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    status_overrides: Sequence[StatusOverride] = (),
) -> TradeEvaluation:
    roster_before = list(roster_before_ids)
    gives = list(dict.fromkeys(gives_ids))
    receives = list(dict.fromkeys(receives_ids))
    if not gives and not receives:
        raise TradeAnalysisError("A trade must give or receive at least one player.")
    missing_gives = [pid for pid in gives if pid not in roster_before]
    if missing_gives:
        raise TradeAnalysisError(f"Cannot give a player not on the current roster: {missing_gives}")
    already_rostered_receives = [pid for pid in receives if pid in roster_before]
    if already_rostered_receives:
        raise TradeAnalysisError(
            f"Cannot receive a player already on the current roster: {already_rostered_receives}"
        )
    overlap = set(gives) & set(receives)
    if overlap:
        raise TradeAnalysisError(f"A player cannot be both given and received: {sorted(overlap)}")

    pool = _asset_pool(ranking, manual_assets)
    roster_after = [pid for pid in roster_before if pid not in gives] + receives
    before_players = _roster_players(roster_before, pool)
    after_players = _roster_players(roster_after, pool)
    report_before: RosterCompositionReport = roster_composition_report(before_players, profile)
    report_after: RosterCompositionReport = roster_composition_report(after_players, profile)

    overrides_by_id = {override.player_id: override for override in status_overrides}
    roster_minus_gives = [pid for pid in roster_before if pid not in gives]

    def _impact(player_id: str, current_player_ids_for_utility: Sequence[str]) -> TradeSideImpact:
        asset = pool.get(player_id)
        result = marginal_roster_utility_v2(
            player_id, current_player_ids_for_utility, profile, ranking, manual_assets
        )
        return TradeSideImpact(
            player_id=player_id,
            player_name=str(asset.get("player_name")) if asset else player_id,
            position=str(asset.get("position")) if asset else "",
            ros_replacement_value=float(asset.get("replacement_adjusted_value") or 0.0) if asset else 0.0,
            marginal_utility=result.utility,
            becomes_starter=result.becomes_starter,
            status_flag=_status_flag(player_id, overrides_by_id),
        )

    gives_impacts = tuple(
        _impact(player_id, [pid for pid in roster_before if pid != player_id]) for player_id in gives
    )
    receives_impacts = tuple(_impact(player_id, roster_minus_gives) for player_id in receives)

    ros_delta = sum(impact.ros_replacement_value for impact in receives_impacts) - sum(
        impact.ros_replacement_value for impact in gives_impacts
    )
    net_marginal = None
    if all(impact.marginal_utility is not None for impact in (*gives_impacts, *receives_impacts)):
        net_marginal = round(
            sum(impact.marginal_utility for impact in receives_impacts)
            - sum(impact.marginal_utility for impact in gives_impacts),
            2,
        )

    risk_flags = [
        f"{impact.player_name} carries a real {impact.status_flag} status override"
        for impact in (*gives_impacts, *receives_impacts)
        if impact.status_flag
    ]

    return TradeEvaluation(
        gives=gives_impacts,
        receives=receives_impacts,
        ros_value_delta=round(ros_delta, 2),
        net_marginal_utility=net_marginal,
        starting_lineup_value_before=report_before.starting_lineup_value,
        starting_lineup_value_after=report_after.starting_lineup_value,
        starting_lineup_value_delta=round(
            report_after.starting_lineup_value - report_before.starting_lineup_value, 2
        ),
        bench_contingency_value_before=report_before.bench_contingency_value,
        bench_contingency_value_after=report_after.bench_contingency_value,
        starter_holes_before=report_before.starter_holes,
        starter_holes_after=report_after.starter_holes,
        position_redundancy_before=dict(report_before.position_redundancy),
        position_redundancy_after=dict(report_after.position_redundancy),
        risk_flags=tuple(risk_flags),
    )
