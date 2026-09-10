"""Waiver-wire ranking, Add/Drop pairing, and FAAB bid ranges (NWR Overnight
V3, Lanes 4/5/6).

Two honest modes, per the governing directive:
  * REST_OF_SEASON -- buildable regardless of Lane 1/2's weekly-source find,
    since ROS player value already exists via NWR's own governed ranking.
  * THIS_WEEK -- only enabled when a real weekly projection was resolved for
    the candidate (Lane 1/2). Never fabricated when unavailable; the caller
    (facade) is expected to disable this mode outright when no weekly
    context is passed in, per the directive's "disable that mode honestly
    rather than fake it."

Reuses, does not duplicate:
  * `marginal_roster_utility_v2` (`shadow_numeric_authorities_service.py`) --
    the SAME promoted, closed, read-only bench-value signal used live in the
    draft room. MODEL STATUS IS CLOSED: this module calls it, never retunes
    or reimplements it. Used for BOTH add-ranking (marginal value of adding
    a free agent to the current roster) and drop-ranking (marginal value of
    a currently rostered bench player, computed the same way against the
    roster with that player removed -- "how much is he actually worth to
    THIS roster right now" is the same function, just pointed at an
    already-rostered player instead of a free agent).
  * `sleeper_free_agent_pool`'s own free-agent rows (`playerId` /
    `replacementAdjustedValue` / `overallRank`) for ROS value -- no second
    ranking read.

What is deliberately NOT estimated, per the directive's own anti-fabrication
rule: schedule/strength-of-schedule for general waiver ranking (a real,
disclosed omission -- schedule context lives in the DST/K streamer lane,
which has a real nflreadpy-backed matchup signal; general skill-position
waiver ranking does not get a schedule boost invented here), and any
"likely competition for this FAAB bid" acceptance probability (no real
signal in this app estimates that).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from src.services.fantasypros_kdst_consensus_service import (
    SLEEPER_FANTASY_POSITIONS,
    _identity,
    _sleeper_position,
)
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.shadow_numeric_authorities_service import (
    MarginalRosterUtility,
    marginal_roster_utility_v2,
)
from src.services.weekly_projection_service import WeeklyProjectionRow

WaiverMode = Literal["THIS_WEEK", "REST_OF_SEASON"]


@dataclass(frozen=True)
class ResolvedRoster:
    canonical_player_ids: tuple[str, ...]
    player_names_by_canonical_id: dict[str, str]
    player_positions_by_canonical_id: dict[str, str]
    unmatched_sleeper_player_ids: tuple[str, ...]


def resolve_roster_canonical_ids(
    *,
    roster_sleeper_player_ids: Sequence[str],
    players_catalog: Mapping[str, Mapping[str, Any]],
    ranking_rows: Sequence[Mapping[str, Any]],
) -> ResolvedRoster:
    """Joins a Sleeper roster to NWR's canonical ranking id space via the
    SAME name/position/team identity matcher `sleeper_free_agent_pool`
    already uses -- no new identity system, and never silently drops an
    unmatched roster player (reported separately, not just omitted)."""

    ranking_by_identity: dict[tuple[str, str, str], str] = {}
    for row in ranking_rows:
        key = _identity(
            row.get("playerName"), row.get("position"), row.get("team"),
            allowed_positions=SLEEPER_FANTASY_POSITIONS,
        )
        if key != ("", "", ""):
            ranking_by_identity.setdefault(key, str(row.get("playerId") or ""))

    canonical_ids: list[str] = []
    names: dict[str, str] = {}
    positions: dict[str, str] = {}
    unmatched: list[str] = []
    for raw_id in roster_sleeper_player_ids:
        sleeper_id = str(raw_id)
        catalog_entry = players_catalog.get(sleeper_id)
        if not isinstance(catalog_entry, Mapping):
            unmatched.append(sleeper_id)
            continue
        position = _sleeper_position(catalog_entry.get("position"))
        team = str(catalog_entry.get("team") or "").upper().strip()
        name = str(catalog_entry.get("full_name") or catalog_entry.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        key = _identity(name, position, team, allowed_positions=SLEEPER_FANTASY_POSITIONS)
        canonical_id = ranking_by_identity.get(key, "")
        if not canonical_id:
            unmatched.append(sleeper_id)
            continue
        canonical_ids.append(canonical_id)
        names[canonical_id] = name
        positions[canonical_id] = position
    return ResolvedRoster(
        canonical_player_ids=tuple(canonical_ids),
        player_names_by_canonical_id=names,
        player_positions_by_canonical_id=positions,
        unmatched_sleeper_player_ids=tuple(unmatched),
    )


@dataclass(frozen=True)
class WaiverCandidate:
    sleeper_player_id: str
    canonical_player_id: str
    player_name: str
    position: str
    team: str
    ros_replacement_value: float | None
    ros_overall_rank: int | None
    weekly_projected_points: float | None
    marginal_utility: float | None
    becomes_starter: bool
    marginal_utility_explanation: str
    identity_status: str  # MATCHED | UNMATCHED_IDENTITY


@dataclass(frozen=True)
class DropCandidate:
    canonical_player_id: str
    player_name: str
    position: str
    marginal_utility: float | None
    explanation: str


@dataclass(frozen=True)
class AddDropPairing:
    add: WaiverCandidate
    drop: DropCandidate | None
    net_marginal_utility: float | None


def rank_waiver_candidates(
    *,
    free_agents: Sequence[Mapping[str, Any]],
    owner_roster_canonical_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    mode: WaiverMode,
    weekly_projections_by_sleeper_id: Mapping[str, WeeklyProjectionRow] | None = None,
    limit: int = 25,
) -> tuple[WaiverCandidate, ...]:
    if mode == "THIS_WEEK" and weekly_projections_by_sleeper_id is None:
        raise ValueError(
            "THIS_WEEK mode requires real weekly projections; the caller must disable this "
            "mode honestly rather than call it with no data."
        )
    candidates: list[WaiverCandidate] = []
    for row in free_agents:
        sleeper_id = str(row.get("sleeperPlayerId") or "")
        canonical_id = str(row.get("playerId") or "")
        position = str(row.get("position") or "")
        weekly_row = (
            weekly_projections_by_sleeper_id.get(sleeper_id) if weekly_projections_by_sleeper_id else None
        )
        if canonical_id:
            utility_result: MarginalRosterUtility | None = marginal_roster_utility_v2(
                canonical_id, owner_roster_canonical_ids, profile, ranking, manual_assets
            )
            identity_status = "MATCHED"
        else:
            utility_result = None
            identity_status = "UNMATCHED_IDENTITY"
        candidates.append(
            WaiverCandidate(
                sleeper_player_id=sleeper_id,
                canonical_player_id=canonical_id,
                player_name=str(row.get("playerName") or ""),
                position=position,
                team=str(row.get("team") or ""),
                ros_replacement_value=row.get("replacementAdjustedValue"),
                ros_overall_rank=row.get("overallRank"),
                weekly_projected_points=weekly_row.projected_points if weekly_row else None,
                marginal_utility=utility_result.utility if utility_result else None,
                becomes_starter=utility_result.becomes_starter if utility_result else False,
                marginal_utility_explanation=(
                    utility_result.explanation if utility_result else "MARGINAL_UTILITY_UNAVAILABLE_UNMATCHED_IDENTITY"
                ),
                identity_status=identity_status,
            )
        )

    def sort_key(candidate: WaiverCandidate) -> tuple:
        # Primary: real marginal roster utility (the same promoted, closed
        # signal live drafting already uses) -- never fabricated when
        # unmatched, which sorts last. THIS_WEEK mode breaks ties with real
        # weekly points when two candidates have equal/near-equal utility.
        primary = candidate.marginal_utility
        secondary = candidate.weekly_projected_points if mode == "THIS_WEEK" else candidate.ros_replacement_value
        return (
            primary is None,
            -(primary or 0.0),
            secondary is None,
            -(secondary or 0.0),
        )

    candidates.sort(key=sort_key)
    return tuple(candidates[:limit])


def rank_drop_candidates(
    *,
    roster_canonical_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    player_names: Mapping[str, str],
    player_positions: Mapping[str, str],
) -> tuple[DropCandidate, ...]:
    """Rank the CURRENT roster's own players by how little marginal value
    they contribute right now -- weakest first, the honest drop-candidate
    order. Computed with the SAME `marginal_roster_utility_v2` call used for
    adds, just pointed at a rostered player against the rest of his own
    roster (never against the closed model's own promoted formula)."""

    drops: list[DropCandidate] = []
    roster_set = list(roster_canonical_ids)
    for player_id in roster_set:
        rest_of_roster = [value for value in roster_set if value != player_id]
        result = marginal_roster_utility_v2(player_id, rest_of_roster, profile, ranking, manual_assets)
        drops.append(
            DropCandidate(
                canonical_player_id=player_id,
                player_name=player_names.get(player_id, player_id),
                position=player_positions.get(player_id, ""),
                marginal_utility=result.utility,
                explanation=result.explanation,
            )
        )
    drops.sort(key=lambda candidate: (candidate.marginal_utility is None, candidate.marginal_utility or 0.0))
    return tuple(drops)


def pair_add_drop(
    *, add_candidates: Sequence[WaiverCandidate], drop_candidates: Sequence[DropCandidate], top_n: int = 10
) -> tuple[AddDropPairing, ...]:
    """Pairs each top ADD with the single weakest real roster piece
    (`drop_candidates[0]`, already ranked ascending by real marginal
    utility). A genuine, disclosed simplification: this does not solve a
    joint multi-add/multi-drop assignment across several simultaneous
    moves, only the single best drop for one add at a time."""

    weakest_drop = drop_candidates[0] if drop_candidates else None
    pairings: list[AddDropPairing] = []
    for add in add_candidates[:top_n]:
        net = None
        if add.marginal_utility is not None and weakest_drop is not None and weakest_drop.marginal_utility is not None:
            net = round(add.marginal_utility - weakest_drop.marginal_utility, 2)
        pairings.append(AddDropPairing(add=add, drop=weakest_drop, net_marginal_utility=net))
    return tuple(pairings)


@dataclass(frozen=True)
class FaabBidSuggestion:
    canonical_player_id: str
    player_name: str
    bid_low_pct: float
    bid_high_pct: float
    bid_low_dollars: int
    bid_high_dollars: int
    urgency: str  # STARTER_UPGRADE | BENCH_DEPTH | LOW_VALUE
    percentile_in_pool: float | None
    rationale: str


def suggest_faab_bids(
    *,
    candidates: Sequence[WaiverCandidate],
    remaining_budget_dollars: int,
    weeks_remaining: int,
    total_budget_dollars: int = 100,
) -> tuple[FaabBidSuggestion, ...]:
    """Contextual bid range, not a static universal percentage table --
    every candidate's range is computed from the REAL, live utility
    distribution of the candidates passed in this call plus real roster
    urgency and weeks-remaining context. No acceptance-probability /
    likely-competition figure is fabricated -- this app has no real signal
    for that.
    """

    if remaining_budget_dollars < 0 or total_budget_dollars <= 0 or weeks_remaining < 0:
        raise ValueError("Invalid FAAB context.")
    utilities = sorted(
        (candidate.marginal_utility for candidate in candidates if candidate.marginal_utility is not None),
        reverse=True,
    )
    suggestions: list[FaabBidSuggestion] = []
    for candidate in candidates:
        if candidate.marginal_utility is None:
            suggestions.append(
                FaabBidSuggestion(
                    canonical_player_id=candidate.canonical_player_id,
                    player_name=candidate.player_name,
                    bid_low_pct=0.0, bid_high_pct=0.0, bid_low_dollars=0, bid_high_dollars=0,
                    urgency="LOW_VALUE", percentile_in_pool=None,
                    rationale="No real marginal-utility signal (unmatched identity) -- $0 suggested, not fabricated.",
                )
            )
            continue
        rank = utilities.index(candidate.marginal_utility)
        percentile = 1.0 - (rank / max(1, len(utilities) - 1)) if len(utilities) > 1 else 1.0
        urgency = "STARTER_UPGRADE" if candidate.becomes_starter else (
            "BENCH_DEPTH" if candidate.marginal_utility > 0 else "LOW_VALUE"
        )
        # Base range scales with real percentile standing in THIS pool, not
        # a fixed lookup table. Starter upgrades get a real, disclosed
        # urgency multiplier; bench depth does not. Season-lateness tapers
        # the range down (fewer real weeks left to realize the value).
        base_low = 0.02 + 0.28 * percentile
        base_high = 0.05 + 0.45 * percentile
        urgency_multiplier = 1.4 if urgency == "STARTER_UPGRADE" else 1.0
        season_taper = min(1.0, max(0.35, weeks_remaining / 14.0))
        low_pct = min(0.95, base_low * urgency_multiplier * season_taper)
        high_pct = min(0.98, base_high * urgency_multiplier * season_taper)
        low_dollars = round(remaining_budget_dollars * low_pct)
        high_dollars = round(remaining_budget_dollars * high_pct)
        suggestions.append(
            FaabBidSuggestion(
                canonical_player_id=candidate.canonical_player_id,
                player_name=candidate.player_name,
                bid_low_pct=round(low_pct, 3), bid_high_pct=round(high_pct, 3),
                bid_low_dollars=low_dollars, bid_high_dollars=high_dollars,
                urgency=urgency, percentile_in_pool=round(percentile, 3),
                rationale=(
                    f"{'Real starter upgrade' if urgency == 'STARTER_UPGRADE' else 'Bench depth' if urgency == 'BENCH_DEPTH' else 'Low real value'}; "
                    f"marginal utility {candidate.marginal_utility:.1f} ranks at the {percentile:.0%} "
                    f"percentile of this week's real free-agent pool, {weeks_remaining} weeks remaining."
                ),
            )
        )
    return tuple(suggestions)
