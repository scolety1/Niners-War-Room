"""Prospective Outcome V1 -- ingestion mechanism.

Pure functions that turn (a) a decision trace's own FROZEN, already-recorded
fields and (b) already-fetched, genuinely real, after-the-fact provider data
(Sleeper weekly matchups/rosters/transactions -- the same public,
already-wired, read-only Sleeper API this codebase uses everywhere else, via
`SleeperHttpClient`/`sleeper_redraft_owner_service.py`/
`sleeper_league_context_service.py`) into one of the decision-type-specific
outcome dataclasses in `prospective_outcome_schema_v1_service.py`.

THIS MODULE PERFORMS NO NETWORK I/O ITSELF. Every function below takes
already-fetched JSON (dicts/lists) as plain arguments -- the same division
of labor `sleeper_league_context_service.py` already established ("the
facade performs the actual HTTP reads ... every function here is a PURE
function over already-fetched Sleeper JSON"). The real orchestration (an
HTTP fetch, then a call into this module, then a `record_outcome(...,
detail=...)` append) belongs to a caller -- a future facade endpoint, or the
standalone real-data script this pass ships
(`scripts/build_prospective_outcome_ingestion_v1_startsit_demo.py`).

=== THE NO-FUTURE-LEAKAGE GUARANTEE, STRUCTURALLY ENFORCED ===

Every "what was known/eligible/recommended AT THE TIME" fact taken by these
functions comes ONLY from the decision trace's own already-recorded,
never-mutated fields (`recommendation`, `alternatives`,
`roster_state_player_ids`, `free_agent_state_player_ids`, `week`,
`owner_action`) -- literal keyword arguments below, never re-derived from a
"current" roster/free-agent read. No function in this module accepts a
"current roster" or "current free agents" parameter for that purpose. The
only data these functions accept that reflects information NOT known at
recommendation time is real, dated, AFTER-recommendation outcome data
(a matchup entry for the recommendation's own week or later, a transaction
log for the period after the recommendation, horizon matchup entries for
weeks after that) -- exactly the "outcomes attach AFTER the fact" contract
the governing directive asks for. See
`tests/test_prospective_outcome_ingestion_v1_service.py`'s
`test_no_future_leakage_*` tests for the proof: mutating what a "current"
data source would return never changes what these functions compute for the
recommendation-time fields, because they never look at a "current" source.

=== IDENTITY RESOLUTION IS EXPLICITLY OUT OF SCOPE HERE ===

Some decision types record player identity in the app's own canonical-id
space (WAIVER/ADD_DROP/FAAB/TRADE/TRADE_FINDER/TRADE_PACKAGE_SEARCH/
K_STREAMER/DST_STREAMER -- see `desktop_facade.py`'s real trace call sites),
while Sleeper's matchup/transaction/roster payloads are keyed by Sleeper's
own numeric player ids (team defenses use the team abbreviation, e.g.
"DEN"). START_SIT is the one exception: `weekly_lineup_optimizer_service`
already records `roster_state_player_ids`/`recommendation.starters` as raw
Sleeper ids directly, so it needs no resolution step -- the real reason this
pass's real-data demonstration targets START_SIT specifically, per the
governing directive's own suggestion. Every other decision type's ingestion
function below accepts ALREADY-RESOLVED Sleeper player ids as plain
arguments (or `None` when a resolution genuinely could not be made) --
this module does not invent a second identity matcher; a future
integration wires the app's existing identity/ranking-row crosswalk
(`resolve_roster_canonical_ids` et al.) before calling in.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.services.prospective_outcome_schema_v1_service import (
    AddDropOutcomeDetail,
    FaabBidRangeCalibration,
    FaabOutcomeDetail,
    FaabPlayerDecisionQuality,
    StartSitOutcomeDetail,
    StreamerOutcomeDetail,
    TradeFinderOutcomeDetail,
    TradeOutcomeDetail,
    TradeRealizedRosterOutcome,
    WaiverOutcomeDetail,
)

DEFAULT_HORIZON_WEEKS = 4


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------


def _actual_points_for_player(matchup_entry: Mapping[str, Any] | None, player_id: str | None) -> float | None:
    """Real per-player points for one roster's ONE week, from a raw Sleeper
    `GET /league/{id}/matchups/{week}` entry's own `players_points` map --
    populated once the games for that week have actually been played, never
    estimated."""

    if player_id is None or not isinstance(matchup_entry, Mapping):
        return None
    points_by_id = matchup_entry.get("players_points")
    if not isinstance(points_by_id, Mapping):
        return None
    value = points_by_id.get(str(player_id))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _string_ids(values: Any) -> tuple[str, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return ()
    return tuple(str(value) for value in values)


# ---------------------------------------------------------------------------
# START_SIT
# ---------------------------------------------------------------------------


def ingest_start_sit_outcome(
    *,
    week: int | None,
    recommendation: Mapping[str, Any],
    roster_state_player_ids: Sequence[str],
    actual_matchup_entry: Mapping[str, Any] | None,
) -> StartSitOutcomeDetail:
    """`recommendation`/`roster_state_player_ids` are the trace's OWN
    already-frozen fields (never re-read from a current roster).
    `actual_matchup_entry` is the real, after-the-fact Sleeper matchup entry
    for the owner's roster for this same week (`GET /league/{id}/
    matchups/{week}`, one entry, `roster_id == <owner's own>`)."""

    recommended = _string_ids(recommendation.get("starters"))
    actual = (
        _string_ids(actual_matchup_entry.get("starters"))
        if isinstance(actual_matchup_entry, Mapping)
        else ()
    )
    roster_at_lock = tuple(str(pid) for pid in roster_state_player_ids)
    eligible_alternatives = tuple(pid for pid in roster_at_lock if pid not in recommended)

    recommended_set = set(recommended)
    actual_set = set(actual)
    recommended_only = tuple(pid for pid in recommended if pid not in actual_set)
    actual_only = tuple(pid for pid in actual if pid not in recommended_set)

    relevant_ids = set(recommended) | set(actual)
    points_by_id: dict[str, float] = {}
    for player_id in relevant_ids:
        points = _actual_points_for_player(actual_matchup_entry, player_id)
        if points is not None:
            points_by_id[player_id] = points

    if not recommended_only and not actual_only:
        opportunity_cost: float | None = 0.0
    elif all(pid in points_by_id for pid in recommended_only) and all(
        pid in points_by_id for pid in actual_only
    ):
        opportunity_cost = sum(points_by_id[pid] for pid in recommended_only) - sum(
            points_by_id[pid] for pid in actual_only
        )
    else:
        opportunity_cost = None

    if isinstance(actual_matchup_entry, Mapping):
        raw_total = actual_matchup_entry.get("points")
        actual_points_total = (
            float(raw_total)
            if isinstance(raw_total, (int, float)) and not isinstance(raw_total, bool)
            else None
        )
    else:
        actual_points_total = None

    raw_projected = recommendation.get("projectedTotal")
    recommended_projected_total = (
        float(raw_projected)
        if isinstance(raw_projected, (int, float)) and not isinstance(raw_projected, bool)
        else None
    )

    return StartSitOutcomeDetail(
        week=week,
        recommended_starter_ids=recommended,
        actual_starter_ids=actual,
        eligible_alternative_ids_at_lock=eligible_alternatives,
        recommended_only_ids=recommended_only,
        actual_only_ids=actual_only,
        recommended_projected_total=recommended_projected_total,
        actual_points_total=actual_points_total,
        actual_points_by_player_id=points_by_id,
        lineup_opportunity_cost=opportunity_cost,
    )


# ---------------------------------------------------------------------------
# WAIVER
# ---------------------------------------------------------------------------


def _matching_add_transaction(
    transactions: Sequence[Mapping[str, Any]], *, player_id: str, owner_roster_id: Any
) -> Mapping[str, Any] | None:
    for transaction in transactions:
        if not isinstance(transaction, Mapping):
            continue
        adds = transaction.get("adds")
        if not isinstance(adds, Mapping):
            continue
        if str(adds.get(str(player_id))) != str(owner_roster_id):
            # Either this transaction doesn't touch this player at all, or
            # it added the player to a DIFFERENT roster (a real, observed
            # "someone else won it" fact, not a match for OUR claim).
            continue
        return transaction
    return None


def _horizon_usage_and_points(
    horizon_matchup_entries: Sequence[Mapping[str, Any]], player_id: str | None
) -> tuple[int | None, float | None]:
    if player_id is None:
        return None, None
    weeks_used = 0
    total_points = 0.0
    saw_any = False
    for entry in horizon_matchup_entries:
        if not isinstance(entry, Mapping):
            continue
        saw_any = True
        starters = _string_ids(entry.get("starters"))
        if str(player_id) in starters:
            weeks_used += 1
        points = _actual_points_for_player(entry, player_id)
        if points is not None:
            total_points += points
    if not saw_any:
        return None, None
    return weeks_used, round(total_points, 2)


def ingest_waiver_outcome(
    *,
    recommended_player_id: str | None,
    owner_roster_id: Any,
    transactions_for_period: Sequence[Mapping[str, Any]],
    horizon_matchup_entries: Sequence[Mapping[str, Any]] = (),
    horizon_weeks: int = DEFAULT_HORIZON_WEEKS,
) -> WaiverOutcomeDetail:
    """`recommended_player_id` must already be resolved to a Sleeper player
    id by the caller (see module docstring). `transactions_for_period` is
    the REAL, already-fetched Sleeper transaction log covering the waiver
    period(s) after this recommendation -- a claim is treated as
    submitted-and-won when a `type == "waiver"` (or `"free_agent"`, Sleeper's
    instant-add path) transaction adds this player to `owner_roster_id`;
    absence across the full supplied period is a real, observed "did not
    claim" (`False`), not an unknown."""

    if recommended_player_id is None:
        return WaiverOutcomeDetail(
            recommended_player_id=None,
            claim_submitted=None,
            claim_won=None,
            faab_paid=None,
            horizon_weeks=horizon_weeks,
            subsequent_roster_usage_weeks=None,
            subsequent_total_points=None,
        )

    matched = _matching_add_transaction(
        transactions_for_period, player_id=recommended_player_id, owner_roster_id=owner_roster_id
    )
    if matched is None:
        claim_submitted, claim_won, faab_paid = False, False, None
    else:
        status = str(matched.get("status") or "")
        claim_submitted = True
        claim_won = status == "complete"
        settings = matched.get("settings") if isinstance(matched.get("settings"), Mapping) else {}
        raw_bid = settings.get("waiver_bid") if isinstance(settings, Mapping) else None
        faab_paid = (
            float(raw_bid) if isinstance(raw_bid, (int, float)) and not isinstance(raw_bid, bool) else None
        )

    usage_weeks, subsequent_points = (
        _horizon_usage_and_points(horizon_matchup_entries, recommended_player_id)
        if claim_won
        else (None, None)
    )

    return WaiverOutcomeDetail(
        recommended_player_id=str(recommended_player_id),
        claim_submitted=claim_submitted,
        claim_won=claim_won,
        faab_paid=faab_paid,
        horizon_weeks=horizon_weeks,
        subsequent_roster_usage_weeks=usage_weeks,
        subsequent_total_points=subsequent_points,
    )


# ---------------------------------------------------------------------------
# ADD_DROP
# ---------------------------------------------------------------------------


def ingest_add_drop_outcome(
    *,
    added_player_id: str | None,
    dropped_player_id: str | None,
    owner_roster_id: Any,
    transactions_for_period: Sequence[Mapping[str, Any]],
    horizon_matchup_entries: Sequence[Mapping[str, Any]] = (),
    horizon_weeks: int = DEFAULT_HORIZON_WEEKS,
) -> AddDropOutcomeDetail:
    """Both player ids must already be resolved to Sleeper player ids by the
    caller. `dropped_player_reversed` looks for a LATER real transaction
    (within `transactions_for_period`) that re-adds `dropped_player_id` back
    to the SAME `owner_roster_id` -- a real, observed fact, not inferred."""

    added_usage, added_points = _horizon_usage_and_points(horizon_matchup_entries, added_player_id)

    dropped_points: float | None = None
    reversed_flag: bool | None = None
    if dropped_player_id is not None:
        readd = _matching_add_transaction(
            transactions_for_period, player_id=dropped_player_id, owner_roster_id=owner_roster_id
        )
        reversed_flag = bool(readd is not None and str(readd.get("status") or "") == "complete")
        # The dropped player's own subsequent value is read from whichever
        # roster picked them up next, if any -- not computable from this
        # roster's own matchup entries once they've left it. Left None here
        # (honestly not computable from this function's inputs alone); a
        # caller with that other roster's matchup entries can compute it the
        # same way `_horizon_usage_and_points` does.

    return AddDropOutcomeDetail(
        added_player_id=str(added_player_id) if added_player_id is not None else None,
        dropped_player_id=str(dropped_player_id) if dropped_player_id is not None else None,
        horizon_weeks=horizon_weeks,
        added_player_subsequent_points=added_points,
        added_player_subsequent_roster_usage_weeks=added_usage,
        dropped_player_subsequent_points=dropped_points,
        dropped_player_reversed=reversed_flag,
    )


# ---------------------------------------------------------------------------
# FAAB
# ---------------------------------------------------------------------------


def _actual_winning_bid_for_player(
    transactions_for_period: Sequence[Mapping[str, Any]], player_id: str
) -> float | None:
    for transaction in transactions_for_period:
        if not isinstance(transaction, Mapping):
            continue
        if str(transaction.get("status") or "") != "complete":
            continue
        adds = transaction.get("adds")
        if not isinstance(adds, Mapping) or str(player_id) not in adds:
            continue
        settings = transaction.get("settings") if isinstance(transaction.get("settings"), Mapping) else {}
        raw_bid = settings.get("waiver_bid") if isinstance(settings, Mapping) else None
        if isinstance(raw_bid, (int, float)) and not isinstance(raw_bid, bool):
            return float(raw_bid)
    return None


def ingest_faab_outcome(
    *,
    recommended_player_id: str | None,
    owner_roster_id: Any,
    suggested_bid_low: float | None,
    suggested_bid_high: float | None,
    transactions_for_period: Sequence[Mapping[str, Any]],
    horizon_matchup_entries: Sequence[Mapping[str, Any]] = (),
    horizon_weeks: int = DEFAULT_HORIZON_WEEKS,
) -> FaabOutcomeDetail:
    """Kept structurally SEPARATE per the directive: `player_decision_quality`
    (was the pickup itself good) never influences `bid_range_calibration`
    (was the suggested $ range accurate), and vice versa."""

    if recommended_player_id is None:
        return FaabOutcomeDetail(
            recommended_player_id=None,
            player_decision_quality=FaabPlayerDecisionQuality(
                subsequent_points=None, subsequent_roster_usage_weeks=None, horizon_weeks=horizon_weeks
            ),
            bid_range_calibration=FaabBidRangeCalibration(
                suggested_bid_low=suggested_bid_low,
                suggested_bid_high=suggested_bid_high,
                amount_bid=None,
                won=None,
                actual_winning_bid=None,
                bid_within_suggested_range=None,
                margin_vs_actual_winning_bid=None,
            ),
        )

    matched = _matching_add_transaction(
        transactions_for_period, player_id=recommended_player_id, owner_roster_id=owner_roster_id
    )
    won = bool(matched is not None and str(matched.get("status") or "") == "complete")
    amount_bid: float | None = None
    if matched is not None:
        settings = matched.get("settings") if isinstance(matched.get("settings"), Mapping) else {}
        raw_bid = settings.get("waiver_bid") if isinstance(settings, Mapping) else None
        amount_bid = (
            float(raw_bid) if isinstance(raw_bid, (int, float)) and not isinstance(raw_bid, bool) else None
        )

    actual_winning_bid = _actual_winning_bid_for_player(transactions_for_period, recommended_player_id)

    within_range: bool | None = None
    if actual_winning_bid is not None and suggested_bid_low is not None and suggested_bid_high is not None:
        within_range = suggested_bid_low <= actual_winning_bid <= suggested_bid_high

    margin: float | None = None
    if amount_bid is not None and actual_winning_bid is not None:
        margin = round(amount_bid - actual_winning_bid, 2)

    usage_weeks, subsequent_points = (
        _horizon_usage_and_points(horizon_matchup_entries, recommended_player_id) if won else (None, None)
    )

    return FaabOutcomeDetail(
        recommended_player_id=str(recommended_player_id),
        player_decision_quality=FaabPlayerDecisionQuality(
            subsequent_points=subsequent_points,
            subsequent_roster_usage_weeks=usage_weeks,
            horizon_weeks=horizon_weeks,
        ),
        bid_range_calibration=FaabBidRangeCalibration(
            suggested_bid_low=suggested_bid_low,
            suggested_bid_high=suggested_bid_high,
            amount_bid=amount_bid,
            won=won,
            actual_winning_bid=actual_winning_bid,
            bid_within_suggested_range=within_range,
            margin_vs_actual_winning_bid=margin,
        ),
    )


# ---------------------------------------------------------------------------
# TRADE
# ---------------------------------------------------------------------------


def _matching_trade_transaction(
    transactions_for_period: Sequence[Mapping[str, Any]],
    *,
    gives_ids: Sequence[str],
    receives_ids: Sequence[str],
    owner_roster_id: Any,
) -> Mapping[str, Any] | None:
    gives_set = {str(pid) for pid in gives_ids}
    receives_set = {str(pid) for pid in receives_ids}
    for transaction in transactions_for_period:
        if not isinstance(transaction, Mapping):
            continue
        if str(transaction.get("type") or "") != "trade":
            continue
        if str(transaction.get("status") or "") != "complete":
            continue
        adds = transaction.get("adds") if isinstance(transaction.get("adds"), Mapping) else {}
        drops = transaction.get("drops") if isinstance(transaction.get("drops"), Mapping) else {}
        owner_receives = {pid for pid, roster_id in adds.items() if str(roster_id) == str(owner_roster_id)}
        owner_gives = {pid for pid, roster_id in drops.items() if str(roster_id) == str(owner_roster_id)}
        if owner_receives == receives_set and owner_gives == gives_set:
            return transaction
    return None


def ingest_trade_outcome(
    *,
    gives_ids: Sequence[str],
    receives_ids: Sequence[str],
    owner_roster_id: Any,
    transactions_for_period: Sequence[Mapping[str, Any]],
    gives_horizon_matchup_entries: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    receives_horizon_matchup_entries: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    horizon_weeks: int = DEFAULT_HORIZON_WEEKS,
) -> TradeOutcomeDetail:
    """`gives_ids`/`receives_ids` must already be resolved to Sleeper player
    ids. A REJECTED (unmatched) trade returns `acceptance_status="REJECTED"`
    with `realized_roster_outcome=None` -- this function NEVER scores an
    unobserved counterfactual. `*_horizon_matchup_entries`, when supplied,
    map each traded player's Sleeper id to their own real post-trade
    matchup-entry sequence (from whichever roster now holds them) so a real
    realized value can be computed only for an actually accepted trade."""

    matched = _matching_trade_transaction(
        transactions_for_period, gives_ids=gives_ids, receives_ids=receives_ids, owner_roster_id=owner_roster_id
    )
    if matched is None:
        return TradeOutcomeDetail(
            acceptance_status="REJECTED", trade_accepted=False, realized_roster_outcome=None
        )

    realized_roster_outcome: TradeRealizedRosterOutcome | None = None
    if gives_horizon_matchup_entries is not None or receives_horizon_matchup_entries is not None:
        gives_points: dict[str, float | None] = {}
        for pid in gives_ids:
            _, points = _horizon_usage_and_points(
                (gives_horizon_matchup_entries or {}).get(str(pid), ()), pid
            )
            gives_points[str(pid)] = points
        receives_points: dict[str, float | None] = {}
        for pid in receives_ids:
            _, points = _horizon_usage_and_points(
                (receives_horizon_matchup_entries or {}).get(str(pid), ()), pid
            )
            receives_points[str(pid)] = points
        net_delta: float | None
        if all(value is not None for value in gives_points.values()) and all(
            value is not None for value in receives_points.values()
        ):
            net_delta = round(
                sum(receives_points.values()) - sum(gives_points.values()), 2  # type: ignore[arg-type]
            )
        else:
            net_delta = None
        realized_roster_outcome = TradeRealizedRosterOutcome(
            horizon_weeks=horizon_weeks,
            gives_subsequent_points=gives_points,
            receives_subsequent_points=receives_points,
            net_subsequent_points_delta=net_delta,
        )

    return TradeOutcomeDetail(
        acceptance_status="ACCEPTED", trade_accepted=True, realized_roster_outcome=realized_roster_outcome
    )


# ---------------------------------------------------------------------------
# TRADE_FINDER / TRADE_PACKAGE_SEARCH
# ---------------------------------------------------------------------------


def ingest_trade_finder_outcome(
    *,
    gives_ids: Sequence[str],
    receives_ids: Sequence[str],
    owner_roster_id: Any,
    owner_action: Mapping[str, Any] | None,
    transactions_for_period: Sequence[Mapping[str, Any]],
    gives_horizon_matchup_entries: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    receives_horizon_matchup_entries: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    horizon_weeks: int = DEFAULT_HORIZON_WEEKS,
) -> TradeFinderOutcomeDetail:
    """`owner_action` is the trace's OWN already-recorded
    `record_owner_action` fact (if any) -- e.g. `{"action": "SENT"}` -- read
    verbatim, never inferred. A real matching completed trade transaction
    always wins (an accepted package IS an accepted trade, regardless of
    what owner_action label was recorded), then reuses `ingest_trade_outcome`
    so acceptance is scored identically wherever it appears."""

    trade_outcome = ingest_trade_outcome(
        gives_ids=gives_ids,
        receives_ids=receives_ids,
        owner_roster_id=owner_roster_id,
        transactions_for_period=transactions_for_period,
        gives_horizon_matchup_entries=gives_horizon_matchup_entries,
        receives_horizon_matchup_entries=receives_horizon_matchup_entries,
        horizon_weeks=horizon_weeks,
    )
    if trade_outcome.trade_accepted:
        return TradeFinderOutcomeDetail(package_disposition="ACCEPTED", linked_trade_outcome=trade_outcome)

    action = str((owner_action or {}).get("action") or "").strip().upper()
    disposition = {
        "SENT": "SENT",
        "CONSIDERED": "CONSIDERED",
        "IGNORED": "IGNORED",
    }.get(action, "UNKNOWN")
    return TradeFinderOutcomeDetail(package_disposition=disposition, linked_trade_outcome=None)


# ---------------------------------------------------------------------------
# K_STREAMER / DST_STREAMER
# ---------------------------------------------------------------------------


def ingest_streamer_outcome(
    *,
    position: str,
    week: int | None,
    recommended_player_id: str | None,
    prior_roster_option_player_id: str | None,
    available_alternative_ids_at_recommendation: Sequence[str],
    actual_matchup_entry: Mapping[str, Any] | None,
) -> StreamerOutcomeDetail:
    """`recommended_player_id`/`prior_roster_option_player_id`/
    `available_alternative_ids_at_recommendation` must already be resolved
    to Sleeper ids by the caller (K/DST streamer traces only record
    `playerName`/`team`, see module docstring) and must come from the
    trace's own frozen `recommendation`/`roster_state_player_ids`/
    `alternatives` fields -- never a hindsight-best pick across the whole
    week's real results. `actual_matchup_entry` is the real, after-the-fact
    Sleeper matchup entry for the owner's roster for this week."""

    actual_starters = (
        _string_ids(actual_matchup_entry.get("starters")) if isinstance(actual_matchup_entry, Mapping) else ()
    )
    all_candidate_ids = {recommended_player_id, prior_roster_option_player_id} | set(
        available_alternative_ids_at_recommendation
    )
    position_starter_ids = [pid for pid in actual_starters if pid in all_candidate_ids]
    actual_starter_id = position_starter_ids[0] if position_starter_ids else None

    best_alternative_id: str | None = None
    best_alternative_points: float | None = None
    for candidate_id in available_alternative_ids_at_recommendation:
        points = _actual_points_for_player(actual_matchup_entry, candidate_id)
        if points is not None and (best_alternative_points is None or points > best_alternative_points):
            best_alternative_id, best_alternative_points = candidate_id, points

    return StreamerOutcomeDetail(
        position=position,
        week=week,
        recommended_player_id=recommended_player_id,
        recommended_player_actual_points=_actual_points_for_player(actual_matchup_entry, recommended_player_id),
        actual_starter_player_id=actual_starter_id,
        actual_starter_actual_points=_actual_points_for_player(actual_matchup_entry, actual_starter_id),
        prior_roster_option_player_id=prior_roster_option_player_id,
        prior_roster_option_actual_points=_actual_points_for_player(
            actual_matchup_entry, prior_roster_option_player_id
        ),
        available_alternative_ids_at_recommendation=tuple(
            str(pid) for pid in available_alternative_ids_at_recommendation
        ),
        best_available_alternative_id=best_alternative_id,
        best_available_alternative_actual_points=best_alternative_points,
    )
