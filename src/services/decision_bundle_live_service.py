"""Live DecisionBundle composition for the current draft state (Owner Test
Candidate V1, section 2).

Bridges the real, already-loaded live Draft Room state (the exact
`ranking`/`manual_assets`/`adp`/room `state` `redraft_bootstrap()` and
`build_draft_room_payload()` already produce) into a real
`decision_bundle_service.DecisionBundle` -- backend computes, frontend
renders. Reuses the real production candidate-legality rule
(`_roster_candidate_allowed`) and availability filter (`_available_ranked`)
from `redraft_draft_room_v1_service` directly, rather than re-deriving
"roster-legal available candidates" a second time -- the exact same
precedent `shadow_numeric_authorities_service.evaluate_pick_candidates`
already established for reusing internal draft-room mechanics from a
research/decision-support module.

Never fabricates a value: if the owner slot isn't configured, or no
roster-legal candidate exists, this returns an explicit
`LiveDecisionBundleUnavailable` with a real reason -- never a
DecisionBundle with placeholder numbers.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.services.decision_bundle_service import DecisionBundle, build_decision_bundle
from src.services.redraft_draft_room_v1_service import (
    AdpSnapshot,
    _available_ranked,
    _roster_candidate_allowed,
    _roster_need_adjustment,
    draft_order,
)
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.score_provenance_service import ScoreProvenance
from src.services.shadow_numeric_authorities_service import RosterPlayer

LIVE_DECISION_BUNDLE_VERSION = "decision-bundle-live-v1"
DEFAULT_MAX_CANDIDATES = 12

# Owner-test follow-up: the shortlist feeding Suggestions was a plain
# `legal_rows[:max_candidates]` rank slice with zero positional-diversity
# awareness -- confirmed the real cause of a real, reproduced complaint
# (7 of 8 Suggestions candidates were QBs after an RB pick, at a rank
# range where the ranked pool happened to cluster QB value). This is a
# SELECTION change only: it never computes a new score, never touches
# Team Score/Championship Equity/Pick Score/Raw Action Value/Cost of
# Waiting, and never excludes a position that is already legal-filtered
# out -- it only decides WHICH already-ranked legal rows are worth
# sending into that existing, unmodified pipeline. `DIVERSITY_POSITIONS`
# are the modeled skill positions Suggestions is meant to compare across;
# K/DST are excluded (NWR does not rank them -- see manual assets).
DIVERSITY_POSITIONS = ("QB", "RB", "WR", "TE")


def diversify_candidate_shortlist(
    legal_rows: Sequence[Any],
    max_candidates: int,
    needed_positions: frozenset[str] | None = None,
) -> list[Any]:
    """Selects up to `max_candidates` rows from `legal_rows` (already
    rank-ordered, already roster-legality-filtered) such that the
    shortlist is not dominated by one position when better-rounded
    options exist, while never inventing a score and never discarding a
    position that is genuinely and legitimately the strongest, deepest
    option right now.

    Owner-test follow-up (round 2): the first version of this function
    guaranteed one coverage slot per DIVERSITY_POSITION unconditionally,
    which itself became a real, reported problem -- it could force a
    legal-but-unneeded backup (e.g. a second TE when the starter and any
    open FLEX are already filled) into the slate purely to satisfy a
    quota, and it capped every position's representation at roughly
    max_candidates / 4 even when one position was both genuinely needed
    and genuinely deep (a real "superior third WR" could be pushed out).

    Two changes fix this without touching any score:
    1. `needed_positions` (typically computed via the same, already-real
       `_roster_need_adjustment` signal the CPU auto-pick/Cost-of-Waiting
       machinery already uses -- an unfilled starter slot or open FLEX
       capacity) gates the COVERAGE pass. A position with no real
       remaining need (its starter slot and any FLEX eligibility are
       already filled) gets no guaranteed slot -- it can still appear if
       it is independently one of the best-ranked remaining legal rows,
       just never as a forced quota filler.
    2. The FILL pass is rank order with a soft per-position cap (60% of
       max_candidates, rounded up, minimum 2) rather than a strict
       round-robin -- this is what stops one position's rank cluster
       from re-dominating the slate (the original real bug: 7 of 8
       candidates were QB) while still letting a genuinely deep, needed
       position take 3-4 of 8 slots when it legitimately earns them,
       rather than being capped at exactly one extra.
    """
    if not legal_rows or max_candidates <= 0:
        return []
    rank_of = {row.player_id: index for index, row in enumerate(legal_rows)}
    selected: list[Any] = [legal_rows[0]]
    selected_ids = {legal_rows[0].player_id}
    covered_positions = {legal_rows[0].position}
    coverage_targets = needed_positions if needed_positions is not None else set(DIVERSITY_POSITIONS)
    # Coverage pass: one best-ranked row per not-yet-covered NEEDED position only.
    for row in legal_rows:
        if len(selected) >= max_candidates:
            break
        if row.position not in coverage_targets or row.position in covered_positions:
            continue
        selected.append(row)
        selected_ids.add(row.player_id)
        covered_positions.add(row.position)
    # Fill pass: next-best-ranked legal rows regardless of position, capped
    # per position so no single position's rank cluster can re-dominate.
    position_cap = max(2, -(-int(max_candidates * 0.6) // 1))
    position_counts: dict[str, int] = {}
    for row in selected:
        position_counts[row.position] = position_counts.get(row.position, 0) + 1
    for row in legal_rows:
        if len(selected) >= max_candidates:
            break
        if row.player_id in selected_ids:
            continue
        if position_counts.get(row.position, 0) >= position_cap:
            continue
        selected.append(row)
        selected_ids.add(row.player_id)
        position_counts[row.position] = position_counts.get(row.position, 0) + 1
    # If the cap left slots unfilled (every remaining legal row belonged to
    # an already-capped position), relax the cap rather than under-filling
    # the slate -- a real, disclosed depth-exhaustion case, not a bug.
    if len(selected) < max_candidates:
        for row in legal_rows:
            if len(selected) >= max_candidates:
                break
            if row.player_id in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row.player_id)
    selected.sort(key=lambda row: rank_of[row.player_id])
    return selected


# NWR OVERNIGHT (K/DST completion): DIVERSITY_POSITIONS/legal_rows are built
# purely from `ranking.rows`, which never contains K/DST (NWR has no model
# for them -- they exist only in `manual_assets`, see _asset_pool). That
# meant K/DST could NEVER appear as a Suggestions candidate at any point in
# a real draft, no matter how late or how urgently required -- the precisely
# traced root cause of a real top-suggestion mock finishing K 0/1, DST 0/1.
# This is the honestly-labeled market-fallback candidate source the owner's
# directive asks for: manual K/DST assets, ordered by real market ADP where
# available (never a fabricated NWR score), surfaced ONLY when
# `_roster_need_adjustment` reports genuine remaining need for that
# position -- never unconditionally, never crowding out a skill-position
# pick that isn't actually needed yet.
MANUAL_FALLBACK_POSITIONS = ("K", "DST")


def _needed_manual_candidates(
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    profile: LeagueProfile,
    roster: Counter[str],
    round_number: int,
    drafted_ids: set[str],
    adp: AdpSnapshot,
    positions: Sequence[str] = MANUAL_FALLBACK_POSITIONS,
    per_position: int = 2,
) -> list[dict[str, Any]]:
    adp_by_id = adp.by_player_id if adp.available else {}
    out: list[dict[str, Any]] = []
    for position in positions:
        if _roster_need_adjustment(profile, roster, round_number, position) >= 0:
            continue  # not genuinely needed right now -- never force it into view
        candidates = [
            asset for asset in manual_assets
            if str(asset.get("position") or "").upper() == position
            and str(asset.get("player_id") or "") not in drafted_ids
        ]

        def _order_key(asset: Mapping[str, Any]) -> tuple[float, str]:
            entry = adp_by_id.get(str(asset.get("player_id") or ""))
            expected_pick = entry.expected_pick if entry is not None else float("inf")
            return (expected_pick, str(asset.get("player_name") or ""))

        candidates.sort(key=_order_key)
        out.extend(candidates[:per_position])
    return out


class LiveDecisionBundleError(ValueError):
    pass


@dataclass(frozen=True)
class LiveDecisionBundleUnavailable:
    reason: str


def build_live_decision_bundle(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    room_state: Mapping[str, Any],
    *,
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    provenance: ScoreProvenance,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
    include_cost_of_waiting: bool = True,
    trials: int = 200,
    seasons: int = 200,
    base_seed: int = 20260903,
    position_filter: str | None = None,
    continuation_seeds: int = 1,
) -> DecisionBundle | LiveDecisionBundleUnavailable:
    """`comparable_leagues` and `provenance` are caller-supplied (not
    built here) so the expensive Monte Carlo reference population can be
    cached at the facade layer, keyed by real provenance (profile,
    ranking/ADP hashes, trial count, seed) -- never reused across a
    changed universe/market/model version."""
    if not ranking.ready:
        return LiveDecisionBundleUnavailable(
            "The active Redraft ranking is not ready (blocked/errored) -- no "
            "DecisionBundle can be computed from it."
        )
    owner_slot = room_state.get("owner_slot")
    if not isinstance(owner_slot, int):
        return LiveDecisionBundleUnavailable("Owner slot is not configured for this profile.")

    # The look-ahead simulation this composes (evaluate_pick_candidates ->
    # simulate_pick_now) forces a candidate as the owner's VERY NEXT actual
    # turn, then completes the draft from there. That is only a meaningful
    # "if I pick X now" answer when it genuinely IS the owner's turn right
    # now -- otherwise the intervening CPU picks (deterministic, same
    # best-available logic driving this function's own candidate selection)
    # can legitimately draft one of these candidates before the owner's
    # real next turn arrives, which is a real state to report, not a crash
    # to hide.
    order = draft_order(profile)
    picks_so_far = len(room_state.get("picks", []))
    current_pick_number = picks_so_far + 1
    current_team_slot = order[picks_so_far] if picks_so_far < len(order) else None
    if current_team_slot != owner_slot:
        return LiveDecisionBundleUnavailable(
            f"It is not currently the owner's turn (pick {current_pick_number} belongs to "
            f"team {current_team_slot}) -- DecisionBundle recommendations are only computed "
            "for the immediate next owner pick, never a hypothetical future turn."
        )

    drafted_ids = {str(value) for value in room_state.get("drafted", [])}
    current_owner_player_ids = tuple(
        str(pick["player_id"])
        for pick in room_state.get("picks", [])
        if pick.get("team_slot") == owner_slot and pick.get("player_id")
    )
    roster = Counter(
        str(pick["position"])
        for pick in room_state.get("picks", [])
        if pick.get("team_slot") == owner_slot
    )
    available_rows = _available_ranked(ranking, room_state)
    legal_rows = [
        row for row in available_rows
        if _roster_candidate_allowed(profile, roster, {"position": row.position})
    ]
    if not legal_rows:
        return LiveDecisionBundleUnavailable(
            "No roster-legal available candidate exists at this pick (every open "
            "position may already be at its configured maximum, or the player "
            "universe is exhausted)."
        )
    # Owner-test follow-up, section 8: an explicit position filter draws
    # its shortlist from the REAL eligible pool of that position (still
    # rank-ordered, still roster-legality-filtered), never a client-side
    # re-filter of the default top-N slice -- which could falsely report
    # "no candidates" for a position that simply wasn't in that slice.
    # Bypasses diversify_candidate_shortlist entirely (there is nothing to
    # diversify across when the owner has already chosen the position).
    if position_filter is not None:
        normalized_filter = position_filter.strip().upper()
        if normalized_filter and normalized_filter != "ALL":
            # Owner feedback closure, section 9: FLEX means the league's
            # REAL configured FLEX-eligible positions (RB/WR/TE), never a
            # literal "FLEX" position value (no candidate row ever has
            # that as its position, so a naive exact match would falsely
            # report zero candidates). Superflex is a distinct, separate
            # filter (adds QB) -- never silently folded into ordinary
            # FLEX, and only offered at all when the league actually
            # configures a Superflex slot.
            if normalized_filter == "FLEX":
                eligible_positions = frozenset({"RB", "WR", "TE"})
                position_rows = [row for row in legal_rows if row.position in eligible_positions]
                candidate_ids = [row.player_id for row in position_rows[:max_candidates]]
            elif normalized_filter == "SFLX" and profile.roster.superflex > 0:
                eligible_positions = frozenset({"QB", "RB", "WR", "TE"})
                position_rows = [row for row in legal_rows if row.position in eligible_positions]
                candidate_ids = [row.player_id for row in position_rows[:max_candidates]]
            elif normalized_filter in MANUAL_FALLBACK_POSITIONS:
                # NWR OVERNIGHT: K/DST are never in `ranking.rows`/`legal_rows`
                # (unmodeled, manual-only) -- an explicit K or DST filter must
                # draw from the real manual pool, ordered by market ADP, not
                # from a ranked-row list that structurally can never contain
                # them (the prior code path always returned "no candidates").
                candidate_ids = [
                    str(asset.get("player_id"))
                    for asset in _needed_manual_candidates(
                        manual_assets, profile=profile, roster=roster,
                        round_number=(current_pick_number - 1) // max(1, profile.team_count) + 1,
                        drafted_ids=drafted_ids, adp=adp,
                        positions=(normalized_filter,), per_position=max_candidates,
                    )
                ] or [
                    str(asset.get("player_id"))
                    for asset in manual_assets
                    if str(asset.get("position") or "").upper() == normalized_filter
                    and str(asset.get("player_id") or "") not in drafted_ids
                ][:max_candidates]
            else:
                position_rows = [row for row in legal_rows if row.position == normalized_filter]
                candidate_ids = [row.player_id for row in position_rows[:max_candidates]]
            if not candidate_ids:
                return LiveDecisionBundleUnavailable(
                    f"No roster-legal available {normalized_filter} exists at this pick."
                )
            player_scores = {row.player_id: float(row.replacement_adjusted_value) for row in ranking.rows}
            bundle = build_decision_bundle(
                profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
                owner_slot=owner_slot, current_owner_player_ids=current_owner_player_ids,
                candidate_player_ids=candidate_ids, comparable_leagues=comparable_leagues,
                provenance=provenance, player_scores=player_scores, from_state=room_state,
                include_cost_of_waiting=include_cost_of_waiting,
                current_pick_number=current_pick_number, trials=trials, seasons=seasons,
                base_seed=base_seed, continuation_seeds=continuation_seeds,
            )
            unresolved_filtered = [pid for pid in candidate_ids if pid in drafted_ids]
            if unresolved_filtered:
                raise LiveDecisionBundleError(
                    f"Candidate player(s) {unresolved_filtered} are already drafted; refusing to score them."
                )
            return bundle
    # Real remaining need only (unfilled starter slot or open FLEX capacity),
    # via the same _roster_need_adjustment signal the CPU auto-pick and
    # Cost-of-Waiting machinery already use -- never a fresh position-demand
    # model. A position already at or above its requirement with no FLEX
    # slack (e.g. TE filled and FLEX also filled) gets no guaranteed
    # coverage slot in the shortlist (see diversify_candidate_shortlist).
    round_number = (current_pick_number - 1) // max(1, profile.team_count) + 1
    needed_positions = frozenset(
        position for position in DIVERSITY_POSITIONS
        if _roster_need_adjustment(profile, roster, round_number, position) < 0
    )
    candidate_rows = diversify_candidate_shortlist(legal_rows, max_candidates, needed_positions)
    candidate_player_ids = [row.player_id for row in candidate_rows]
    # NWR OVERNIGHT (K/DST completion): K/DST are structurally absent from
    # `legal_rows`/`diversify_candidate_shortlist` above (unmodeled, manual
    # pool only) -- append them here, honestly-labeled-market-ordered, ONLY
    # when `_roster_need_adjustment` reports genuine remaining need. This is
    # additive to the existing shortlist (never removes a skill-position
    # candidate to make room), so a required K/DST becomes a real,
    # selectable Suggestions row exactly when it is genuinely needed,
    # without ever crowding out an unrelated pick before that.
    needed_manual = _needed_manual_candidates(
        manual_assets, profile=profile, roster=roster, round_number=round_number,
        drafted_ids=drafted_ids, adp=adp,
    )
    for asset in needed_manual:
        player_id = str(asset.get("player_id"))
        if player_id not in candidate_player_ids:
            candidate_player_ids.append(player_id)
    player_scores = {
        row.player_id: float(row.replacement_adjusted_value) for row in ranking.rows
    }

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=owner_slot, current_owner_player_ids=current_owner_player_ids,
        candidate_player_ids=candidate_player_ids, comparable_leagues=comparable_leagues,
        provenance=provenance, player_scores=player_scores,
        # The CURRENT real draft-room state -- without this, the look-ahead
        # simulation (evaluate_pick_candidates -> simulate_pick_now) starts
        # from an EMPTY draft instead of continuing the real one, and can
        # collide with players the real room has already drafted.
        from_state=room_state,
        include_cost_of_waiting=include_cost_of_waiting,
        current_pick_number=current_pick_number, trials=trials, seasons=seasons,
        base_seed=base_seed, continuation_seeds=continuation_seeds,
    )
    unresolved = [pid for pid in candidate_player_ids if pid in drafted_ids]
    if unresolved:  # defensive -- should be impossible given _available_ranked's own filter
        raise LiveDecisionBundleError(
            f"Candidate player(s) {unresolved} are already drafted; refusing to score them."
        )
    return bundle
