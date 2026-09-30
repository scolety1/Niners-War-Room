"""Deterministic Dynasty waiver-wire ranking over governed asset values.

This module deliberately does not call a provider and does not mutate any
governed value.  A caller supplies the current Sleeper ownership/FAAB context
(live when available, a dated local snapshot otherwise) and the already-built
Dynasty evidence rows.  The service then adds a small, testable decision layer
for waiver ordering, roster fit, stash framing, safe drop candidates, and FAAB
ranges.

It does *not* reuse Redraft's replacement-value or season-taper formulas.
Dynasty priority starts from the existing governed long-term NWR value and only
adds disclosed contextual bonuses/penalties.  Weekly role, usage, and injury-
opportunity signals are intentionally absent until a real Dynasty weekly data
lane exists.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

_FLEX_POSITIONS = frozenset({"RB", "WR", "TE"})
_SUPERFLEX_POSITIONS = frozenset({"QB", "RB", "WR", "TE"})


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _position_supported(position: str, roster_positions: Sequence[str]) -> bool:
    normalized = position.upper().strip()
    slots = {str(value).upper().strip() for value in roster_positions}
    if normalized in slots:
        return True
    if normalized in _FLEX_POSITIONS and slots.intersection({"FLEX", "WRT", "WRRB_FLEX"}):
        return True
    return normalized in _SUPERFLEX_POSITIONS and bool(
        slots.intersection({"SUPER_FLEX", "SUPERFLEX", "OP"})
    )


def age_upside_bonus(age: float | None) -> tuple[float, str]:
    """Small contextual modifier; the governed long-term score remains primary."""

    if age is None:
        return 0.0, "UNKNOWN"
    if age <= 22.5:
        return 3.0, "HIGH"
    if age <= 24.5:
        return 2.0, "HIGH"
    if age <= 26.5:
        return 1.0, "MEDIUM"
    if age >= 29.0:
        return -1.0, "LOW"
    return 0.0, "MEDIUM"


def stash_value_band(*, dynasty_score: float, age: float | None) -> str:
    if dynasty_score >= 15.0 and (age is None or age <= 25.5):
        return "HIGH"
    if dynasty_score >= 8.0 and (age is None or age <= 28.0):
        return "MEDIUM"
    return "LOW"


def dynasty_waiver_priority_score(
    *,
    dynasty_score: float,
    age_bonus: float,
    roster_fit_bonus: float,
    status_kind: str,
) -> float:
    """Transparent additive priority layer; never changes the source score."""

    status_penalty = 5.0 if status_kind.upper().strip() == "SEASON_OUT" else 0.0
    return round(dynasty_score + age_bonus + roster_fit_bonus - status_penalty, 4)


def suggest_dynasty_faab_range(
    *,
    remaining_budget: int | None,
    percentile: float,
    transaction_net_value: float | None,
    stash_value: str,
    roster_fit: str,
) -> tuple[int | None, int | None, str]:
    """Dynasty-specific relative FAAB range, not a market-clearing estimate.

    Positive ranges are deliberately capped at 35% of the remaining budget.
    A non-positive/unknown add-drop net never receives a paid recommendation.
    """

    if remaining_budget is None:
        return None, None, "LIVE_FAAB_BALANCE_UNAVAILABLE"
    if remaining_budget < 0 or not 0.0 <= percentile <= 1.0:
        raise ValueError("Invalid Dynasty FAAB context.")
    if transaction_net_value is None or transaction_net_value <= 0:
        return 0, 0, "NONPOSITIVE_OR_UNKNOWN_TRANSACTION_NET"
    low_pct = 0.01 + 0.09 * percentile
    high_pct = 0.03 + 0.17 * percentile
    multiplier = 1.0
    if stash_value == "HIGH":
        multiplier *= 1.15
    if roster_fit in {"STARTER_NEED", "DEPTH_NEED"}:
        multiplier *= 1.25
    low_pct = min(0.30, low_pct * multiplier)
    high_pct = min(0.35, high_pct * multiplier)
    return (
        round(remaining_budget * low_pct),
        round(remaining_budget * high_pct),
        "RELATIVE_DYNASTY_HEURISTIC",
    )


@dataclass(frozen=True)
class DynastyDropCandidate:
    asset_id: str
    player_name: str
    position: str
    dynasty_rank: int | None
    dynasty_score: float
    roster_status: str


@dataclass(frozen=True)
class DynastyWaiverCandidate:
    asset_id: str
    sleeper_player_id: str
    player_name: str
    position: str
    team: str
    age: float | None
    dynasty_rank: int | None
    dynasty_score: float
    priority_score: float
    age_upside: str
    roster_fit: str
    roster_fit_reason: str
    stash_value: str
    availability: str
    faab_bid_low: int | None
    faab_bid_high: int | None
    faab_rationale: str
    drop_candidate: DynastyDropCandidate | None
    drop_required: bool | None
    transaction_net_value: float | None
    current_status_override: Mapping[str, Any] | None
    short_term_usability: str = "NOT_SCORED"
    role_signal: str = "NOT_SCORED"
    injury_opportunity: str = "NOT_SCORED"
    taxi_eligibility: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _dedicated_starter_slot_count(position: str, roster_positions: Sequence[str]) -> int:
    """Count only dedicated slots; a flex slot is not a need for every eligible position."""

    slots = Counter(str(value).upper().strip() for value in roster_positions)
    return slots[position]


def rank_dynasty_waiver_candidates(
    *,
    asset_rows: Sequence[Mapping[str, Any]],
    all_rostered_player_ids: Sequence[str],
    owner_roster_status_by_player_id: Mapping[str, str],
    roster_positions: Sequence[str],
    remaining_faab_budget: int | None,
    open_active_roster_slot: bool | None,
    limit: int = 25,
) -> tuple[DynastyWaiverCandidate, ...]:
    if limit <= 0:
        return ()

    rows_by_player_id: dict[str, Mapping[str, Any]] = {}
    for row in asset_rows:
        asset_id = _text(row.get("asset_id"))
        if not asset_id.startswith("current:"):
            continue
        player_id = asset_id.removeprefix("current:")
        if player_id:
            rows_by_player_id[player_id] = row

    owner_rows: list[tuple[str, Mapping[str, Any], str]] = []
    owner_position_counts: Counter[str] = Counter()
    for player_id, status in owner_roster_status_by_player_id.items():
        row = rows_by_player_id.get(str(player_id))
        if row is None:
            continue
        position = _text(row.get("position")).upper()
        owner_position_counts[position] += 1
        owner_rows.append((str(player_id), row, str(status).upper()))

    droppable: list[DynastyDropCandidate] = []
    for player_id, row, status in owner_rows:
        if status != "BENCH":
            continue
        score = _number(row.get("nwr_dynasty_score"))
        if score is None:
            continue
        rank_value = _number(row.get("dynasty_rank"))
        droppable.append(
            DynastyDropCandidate(
                asset_id=f"current:{player_id}",
                player_name=_text(row.get("asset_name")) or "Unknown player",
                position=_text(row.get("position")).upper(),
                dynasty_rank=int(rank_value) if rank_value is not None else None,
                dynasty_score=score,
                roster_status=status,
            )
        )
    droppable.sort(key=lambda row: (row.dynasty_score, row.player_name.casefold(), row.asset_id))
    weakest_drop = droppable[0] if droppable else None

    rostered = {str(value) for value in all_rostered_player_ids}
    provisional: list[dict[str, Any]] = []
    for player_id, row in rows_by_player_id.items():
        if player_id in rostered:
            continue
        position = _text(row.get("position")).upper()
        if not _position_supported(position, roster_positions):
            continue
        dynasty_score = _number(row.get("nwr_dynasty_score"))
        if dynasty_score is None:
            continue
        age = _number(row.get("age"))
        age_bonus, age_band = age_upside_bonus(age)
        same_position_drops = [item for item in droppable if item.position == position]
        drop = same_position_drops[0] if same_position_drops else weakest_drop
        transaction_net = dynasty_score - drop.dynasty_score if drop is not None else None
        required = _dedicated_starter_slot_count(position, roster_positions)
        owned_count = owner_position_counts[position]
        if owned_count < required:
            roster_fit = "STARTER_NEED"
            roster_fit_bonus = 4.0
            roster_fit_reason = (
                f"Only {owned_count} rostered for {required} eligible starting slot(s)."
            )
        elif owned_count < required + (2 if position in {"RB", "WR"} else 1):
            roster_fit = "DEPTH_NEED"
            roster_fit_bonus = 2.0
            roster_fit_reason = f"Adds depth behind {required} eligible starting slot(s)."
        elif transaction_net is not None and transaction_net > 0:
            roster_fit = "ROSTER_UPGRADE"
            roster_fit_bonus = min(3.0, transaction_net / 5.0)
            roster_fit_reason = (
                f"Governed value is {transaction_net:.1f} above the safest "
                "same-position bench drop."
            )
        else:
            roster_fit = "STASH_ONLY"
            roster_fit_bonus = 0.0
            roster_fit_reason = "No governed-value roster upgrade is currently identified."
        override = row.get("current_status_override")
        status_kind = _text(override.get("kind")) if isinstance(override, Mapping) else ""
        priority = dynasty_waiver_priority_score(
            dynasty_score=dynasty_score,
            age_bonus=age_bonus,
            roster_fit_bonus=roster_fit_bonus,
            status_kind=status_kind,
        )
        rank_value = _number(row.get("dynasty_rank"))
        provisional.append(
            {
                "asset_id": f"current:{player_id}",
                "sleeper_player_id": player_id,
                "player_name": _text(row.get("asset_name")) or "Unknown player",
                "position": position,
                "team": _text(row.get("team")),
                "age": age,
                "dynasty_rank": int(rank_value) if rank_value is not None else None,
                "dynasty_score": dynasty_score,
                "priority_score": priority,
                "age_upside": age_band,
                "roster_fit": roster_fit,
                "roster_fit_reason": roster_fit_reason,
                "stash_value": stash_value_band(dynasty_score=dynasty_score, age=age),
                "drop_candidate": None if open_active_roster_slot is True else drop,
                "drop_required": (
                    None if open_active_roster_slot is None else not open_active_roster_slot
                ),
                "transaction_net_value": dynasty_score
                if open_active_roster_slot is True
                else transaction_net,
                "current_status_override": dict(override)
                if isinstance(override, Mapping)
                else None,
            }
        )

    provisional.sort(
        key=lambda row: (
            -float(row["priority_score"]),
            -float(row["dynasty_score"]),
            row["player_name"].casefold(),
            row["asset_id"],
        )
    )
    selected = provisional[:limit]
    positive = [row for row in selected if (row["transaction_net_value"] or 0.0) > 0]
    percentile_by_id = {
        row["asset_id"]: 1.0 - (index / max(1, len(positive) - 1))
        for index, row in enumerate(positive)
    }

    results: list[DynastyWaiverCandidate] = []
    for row in selected:
        percentile = percentile_by_id.get(row["asset_id"], 0.0)
        low, high, rationale = suggest_dynasty_faab_range(
            remaining_budget=remaining_faab_budget,
            percentile=percentile,
            transaction_net_value=row["transaction_net_value"],
            stash_value=row["stash_value"],
            roster_fit=row["roster_fit"],
        )
        results.append(
            DynastyWaiverCandidate(
                **row,
                availability="UNROSTERED",
                faab_bid_low=low,
                faab_bid_high=high,
                faab_rationale=rationale,
            )
        )
    return tuple(results)
