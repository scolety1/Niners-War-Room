"""Bounded, ownership-safe Dynasty counter-offer generation.

The service mutates one already-analyzed package against one verified
counterparty and reuses ``evaluate_trade_decision`` for every alternative.
It never changes the governed board, invents pick ownership, sums assets
onto a new package-value scale, or estimates acceptance probability.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.draft_day_trade_lab_service import replace_trade_state
from src.services.trade_decision_assistant_service import TradeDecision, evaluate_trade_decision


@dataclass(frozen=True)
class DynastyCounterCandidate:
    give: tuple[str, ...]
    receive: tuple[str, ...]
    owner_decision: TradeDecision
    opponent_decision: TradeDecision
    changes: tuple[str, ...]
    why_it_helps_you: str
    why_it_may_make_sense_for_them: str
    nwr_vs_market: str
    main_risk: str


@dataclass(frozen=True)
class DynastyCounterSearchResult:
    candidates: tuple[DynastyCounterCandidate, ...]
    packages_evaluated: int
    preserved_anchor_id: str
    opponent_window_basis: str
    truncated: bool


def _number(value: object) -> float | None:
    try:
        text = str(value if value is not None else "").strip().replace(",", "")
        return float(text) if text and text.casefold() not in {"nan", "none"} else None
    except (TypeError, ValueError):
        return None


def _asset_id(row: Mapping[str, object]) -> str:
    return str(row.get("asset_id") or "")


def _name(row: Mapping[str, object]) -> str:
    return str(row.get("player") or row.get("asset_name") or _asset_id(row))


def _rank(row: Mapping[str, object]) -> float:
    return _number(row.get("dynasty_rank")) or 9_999.0


def _position(row: Mapping[str, object]) -> str:
    return str(row.get("position") or "UNKNOWN")


def _recommendation_score(decision: TradeDecision) -> int:
    score = {
        "ACCEPT": 5,
        "LEAN_ACCEPT": 4,
        "TOO_CLOSE": 3,
        "COUNTER": 3,
        "LEAN_REJECT": 1,
        "REJECT": 0,
        "INSUFFICIENT_EVIDENCE": -1,
    }.get(decision.recommendation, -1)
    if decision.recommendation == "COUNTER":
        score += 1 if decision.preferred_side == "The incoming side" else -1
    return score


def _market_context(rows: Sequence[Mapping[str, object]]) -> str:
    contexts: list[str] = []
    for row in rows:
        nwr_rank = _number(row.get("dynasty_rank"))
        market_rank = _number(row.get("market_dp_rank"))
        if nwr_rank is None or market_rank is None:
            continue
        edge = market_rank - nwr_rank
        direction = "NWR higher" if edge > 0 else "market higher" if edge < 0 else "aligned"
        contexts.append(
            f"{_name(row)}: NWR #{int(nwr_rank)} vs market #{int(market_rank)} "
            f"({direction} by {abs(int(edge))})."
        )
    return (
        " ".join(contexts[:3])
        or "No exact current market match is admitted for the changed assets."
    )


def _risk(rows: Sequence[Mapping[str, object]], decision: TradeDecision) -> str:
    for row in rows:
        override = row.get("current_status_override")
        if isinstance(override, Mapping) and override.get("kind"):
            status = str(override["kind"]).replace("_", " ")
            return f"{_name(row)} carries verified status {status}."
    return decision.main_uncertainty or "The opponent's team window is not verified."


def _changes(
    *,
    original_give: Sequence[str],
    original_receive: Sequence[str],
    give: Sequence[str],
    receive: Sequence[str],
    rows_by_id: Mapping[str, Mapping[str, object]],
) -> tuple[str, ...]:
    notes: list[str] = []
    removed_give = set(original_give) - set(give)
    added_give = set(give) - set(original_give)
    removed_receive = set(original_receive) - set(receive)
    added_receive = set(receive) - set(original_receive)
    if removed_give:
        names = ", ".join(_name(rows_by_id[value]) for value in sorted(removed_give))
        notes.append(f"Keep {names}.")
    if added_give:
        names = ", ".join(_name(rows_by_id[value]) for value in sorted(added_give))
        notes.append(f"Add {names} to your outgoing side.")
    if removed_receive:
        names = ", ".join(_name(rows_by_id[value]) for value in sorted(removed_receive))
        notes.append(f"Remove {names} from the return.")
    if added_receive:
        names = ", ".join(_name(rows_by_id[value]) for value in sorted(added_receive))
        notes.append(f"Ask for {names} as an add-on.")
    return tuple(notes) or ("Same assets in a different constructible shape.",)


def generate_dynasty_trade_counters(
    *,
    original_give_ids: Sequence[str],
    original_receive_ids: Sequence[str],
    owner_asset_ids: Sequence[str],
    opponent_asset_ids: Sequence[str],
    lookup: Mapping[str, Mapping[str, object]],
    key_for_id: Mapping[str, str],
    team_window: str,
    owner_need_positions: Sequence[str] = (),
    opponent_need_positions: Sequence[str] = (),
    limit: int = 5,
    max_evaluated: int = 120,
) -> DynastyCounterSearchResult:
    give = tuple(dict.fromkeys(original_give_ids))
    receive = tuple(dict.fromkeys(original_receive_ids))
    owner_ids = tuple(value for value in dict.fromkeys(owner_asset_ids) if value in key_for_id)
    opponent_ids = tuple(
        value for value in dict.fromkeys(opponent_asset_ids) if value in key_for_id
    )
    if not give or not receive:
        raise ValueError("Counter generation requires both trade sides.")
    if any(value not in owner_ids for value in give):
        raise ValueError("Outgoing assets must be on the owner's verified roster.")
    if any(value not in opponent_ids for value in receive):
        raise ValueError("Incoming assets must be on the selected opponent roster.")

    rows_by_id = {
        asset_id: lookup[key_for_id[asset_id]]
        for asset_id in (*owner_ids, *opponent_ids)
    }
    anchor = min(receive, key=lambda value: (_rank(rows_by_id[value]), value))
    target_rank = min(
        (_rank(rows_by_id[value]) for value in give),
        default=_rank(rows_by_id[anchor]),
    )
    nearby_owner = sorted(
        (value for value in owner_ids if value not in give),
        key=lambda value: (
            abs(_rank(rows_by_id[value]) - target_rank),
            _rank(rows_by_id[value]),
            value,
        ),
    )[:6]
    give_pool = tuple(dict.fromkeys((*give, *nearby_owner)))
    give_sizes = sorted({max(1, len(give) - 1), min(2, len(give))})
    give_combos = [give]
    give_combos.extend(
        combo
        for size in give_sizes
        for combo in itertools.combinations(give_pool, size)
        if tuple(combo) != give
    )
    give_combos.sort(key=lambda combo: (len(set(combo).symmetric_difference(give)), combo))

    opponent_addons = sorted(
        (value for value in opponent_ids if value not in receive),
        key=lambda value: (-_rank(rows_by_id[value]), value),
    )[:6]
    receive_combos: list[tuple[str, ...]] = [receive]
    if (anchor,) not in receive_combos:
        receive_combos.append((anchor,))
    receive_combos.extend((anchor, value) for value in opponent_addons)
    receive_combos = list(dict.fromkeys(receive_combos))

    owner_needs = set(owner_need_positions)
    opponent_needs = set(opponent_need_positions)
    candidates: list[DynastyCounterCandidate] = []
    evaluated = 0
    truncated = False
    original_signature = (frozenset(give), frozenset(receive))
    for give_ids in give_combos:
        for receive_ids in receive_combos:
            if evaluated >= max_evaluated:
                truncated = True
                break
            signature = (frozenset(give_ids), frozenset(receive_ids))
            if anchor not in receive_ids or signature == original_signature:
                continue
            if set(give_ids) & set(receive_ids):
                continue
            if abs((len(give_ids) + len(receive_ids)) - (len(give) + len(receive))) > 1:
                continue
            evaluated += 1
            owner_state = replace_trade_state(
                [key_for_id[value] for value in give_ids],
                [key_for_id[value] for value in receive_ids],
            )
            opponent_state = replace_trade_state(
                [key_for_id[value] for value in receive_ids],
                [key_for_id[value] for value in give_ids],
            )
            owner_decision = evaluate_trade_decision(owner_state, lookup, team_window=team_window)
            # The opponent's window is not known from Sleeper. Balanced is
            # an explicit comparison basis, never a claim about their plan.
            opponent_decision = evaluate_trade_decision(
                opponent_state,
                lookup,
                team_window="Balanced",
            )
            owner_fit = sorted(
                {_position(rows_by_id[value]) for value in receive_ids} & owner_needs
            )
            opponent_fit = sorted(
                {_position(rows_by_id[value]) for value in give_ids} & opponent_needs
            )
            why_owner = owner_decision.summary
            if owner_fit:
                positions = ", ".join(owner_fit)
                why_owner += f" It also addresses your verified roster depth at {positions}."
            why_opponent = opponent_decision.summary
            if opponent_fit:
                positions = ", ".join(opponent_fit)
                why_opponent += (
                    f" The incoming side adds {positions} depth their current roster lacks."
                )
            changed_ids = tuple(dict.fromkeys((*give_ids, *receive_ids)))
            changed_rows = [rows_by_id[value] for value in changed_ids]
            candidates.append(
                DynastyCounterCandidate(
                    give=tuple(give_ids),
                    receive=tuple(receive_ids),
                    owner_decision=owner_decision,
                    opponent_decision=opponent_decision,
                    changes=_changes(
                        original_give=give,
                        original_receive=receive,
                        give=give_ids,
                        receive=receive_ids,
                        rows_by_id=rows_by_id,
                    ),
                    why_it_helps_you=why_owner,
                    why_it_may_make_sense_for_them=why_opponent,
                    nwr_vs_market=_market_context(changed_rows),
                    main_risk=_risk(changed_rows, owner_decision),
                )
            )
        if truncated:
            break

    def order_key(candidate: DynastyCounterCandidate) -> tuple[int, int, int, tuple[str, ...]]:
        owner_score = _recommendation_score(candidate.owner_decision)
        opponent_score = _recommendation_score(candidate.opponent_decision)
        mutations = len(set(candidate.give).symmetric_difference(give)) + len(
            set(candidate.receive).symmetric_difference(receive)
        )
        return (
            min(owner_score, opponent_score),
            owner_score + opponent_score,
            -mutations,
            candidate.give,
        )

    candidates.sort(key=order_key, reverse=True)
    return DynastyCounterSearchResult(
        candidates=tuple(candidates[: max(1, min(limit, 5))]),
        packages_evaluated=evaluated,
        preserved_anchor_id=anchor,
        opponent_window_basis=(
            "Balanced comparison only; the opponent's real team window is not verified."
        ),
        truncated=truncated,
    )
