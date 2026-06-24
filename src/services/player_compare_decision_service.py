from __future__ import annotations

from dataclasses import dataclass
from typing import Any

NOT_ENOUGH_INFORMATION = "Not enough information"
MARKET_DISPLAY_ONLY_NOTE = (
    "Market/ADP context is display-only sanity context and does not decide the lean."
)


@dataclass(frozen=True)
class PlayerDecisionSummary:
    lean: str
    confidence: str
    reason_bullets: tuple[str, ...]
    red_flags: tuple[str, ...]
    best_use_case: str
    data_quality: str
    display_only_market_note: str


def build_player_compare_decision_summary(
    player_a: dict[str, Any],
    player_b: dict[str, Any],
    extra_players: list[dict[str, Any]] | None = None,
) -> PlayerDecisionSummary:
    """Build a review-only player comparison summary without changing source ranks."""

    candidates = [player_a, player_b, *(extra_players or [])]
    usable = [row for row in candidates if _player_name(row) != NOT_ENOUGH_INFORMATION]
    if len(usable) < 2:
        return PlayerDecisionSummary(
            lean=NOT_ENOUGH_INFORMATION,
            confidence="Low",
            reason_bullets=("Select at least two players with NWR context.",),
            red_flags=(NOT_ENOUGH_INFORMATION,),
            best_use_case=NOT_ENOUGH_INFORMATION,
            data_quality="Low",
            display_only_market_note=MARKET_DISPLAY_ONLY_NOTE,
        )

    ranked = sorted(usable, key=_decision_sort_key)
    leader = ranked[0]
    runner_up = ranked[1]
    leader_rank = _best_rank_value(leader)
    runner_rank = _best_rank_value(runner_up)
    missing_rank_count = sum(1 for row in usable if _best_rank_value(row) is None)

    if leader_rank is None and runner_rank is None:
        lean = NOT_ENOUGH_INFORMATION
        confidence = "Low"
    elif _players_are_close(leader, runner_up):
        lean = "Close / depends on roster"
        confidence = _confidence_for_close(leader, runner_up)
    else:
        lean = f"Prefer {_player_name(leader)}"
        confidence = _confidence_for_leader(leader, runner_up)

    red_flags = _red_flags(usable)
    if missing_rank_count:
        red_flags.append(f"{missing_rank_count} player(s) missing NWR rank context.")
    if not red_flags:
        red_flags.append("No major display warning in current context.")

    return PlayerDecisionSummary(
        lean=lean,
        confidence=confidence,
        reason_bullets=tuple(_reason_bullets(leader, runner_up, lean)),
        red_flags=tuple(red_flags[:6]),
        best_use_case=_best_use_case(leader, lean),
        data_quality=_data_quality(usable, red_flags),
        display_only_market_note=MARKET_DISPLAY_ONLY_NOTE,
    )


def decision_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in sorted(rows, key=_decision_sort_key):
        output.append(
            {
                "Player": _player_name(row),
                "Primary Rank Signal": _rank_signal(row),
                "Age": _field(row, "age"),
                "Tier / Band": _tier_signal(row),
                "Outcome Support": _outcome_signal(row),
                "Best Use Case": _best_use_case(row, ""),
                "Primary Risk": _risk_signal(row),
                "Market / ADP Sanity": _market_signal(row),
                "Confidence": _confidence_text(row),
            }
        )
    return output


def _decision_sort_key(row: dict[str, Any]) -> tuple[int, float, str]:
    rank = _best_rank_value(row)
    return (1 if rank is None else 0, rank if rank is not None else 9999.0, _player_name(row))


def _best_rank_value(row: dict[str, Any]) -> float | None:
    for key in ("dynasty_asset_rank", "cross_asset_candidate_rank", "final_board_rank"):
        value = _float_or_none(row.get(key))
        if value is not None:
            return value
    return None


def _rank_source(row: dict[str, Any]) -> str:
    for label, key in (
        ("NWR/Dynasty Candidate", "dynasty_asset_rank"),
        ("Tuned Candidate", "cross_asset_candidate_rank"),
        ("Frozen Baseline", "final_board_rank"),
    ):
        if _float_or_none(row.get(key)) is not None:
            return label
    return NOT_ENOUGH_INFORMATION


def _players_are_close(leader: dict[str, Any], runner_up: dict[str, Any]) -> bool:
    leader_rank = _best_rank_value(leader)
    runner_rank = _best_rank_value(runner_up)
    if leader_rank is None or runner_rank is None:
        return True
    gap = abs(runner_rank - leader_rank)
    if gap <= 4:
        return True
    return _confidence_text(leader).lower() == "low" and gap <= 10


def _confidence_for_close(leader: dict[str, Any], runner_up: dict[str, Any]) -> str:
    if _has_low_confidence(leader) or _has_low_confidence(runner_up):
        return "Low"
    return "Medium"


def _confidence_for_leader(leader: dict[str, Any], runner_up: dict[str, Any]) -> str:
    leader_rank = _best_rank_value(leader)
    runner_rank = _best_rank_value(runner_up)
    if leader_rank is None or runner_rank is None:
        return "Low"
    gap = runner_rank - leader_rank
    if _has_low_confidence(leader):
        return "Low"
    if gap >= 20 and not _has_loud_warning(leader):
        return "High"
    if gap >= 6:
        return "Medium"
    return "Low"


def _reason_bullets(
    leader: dict[str, Any],
    runner_up: dict[str, Any],
    lean: str,
) -> list[str]:
    if lean == NOT_ENOUGH_INFORMATION:
        return ["NWR rank context is missing for the selected comparison."]

    leader_name = _player_name(leader)
    runner_name = _player_name(runner_up)
    bullets: list[str] = []
    leader_rank = _best_rank_value(leader)
    runner_rank = _best_rank_value(runner_up)
    if leader_rank is not None and runner_rank is not None:
        bullets.append(
            f"{leader_name} has the better {_rank_source(leader)} rank "
            f"({leader_rank:g} vs {runner_rank:g})."
        )
    tier = _tier_signal(leader)
    if tier != NOT_ENOUGH_INFORMATION:
        bullets.append(f"{leader_name} carries the stronger tier/band signal: {tier}.")
    age_note = _age_edge(leader, runner_up)
    if age_note:
        bullets.append(age_note)
    outcome = _outcome_signal(leader)
    if outcome != NOT_ENOUGH_INFORMATION:
        bullets.append(f"Outcome support for {leader_name}: {outcome}.")
    risk = _risk_signal(leader)
    if risk != NOT_ENOUGH_INFORMATION:
        bullets.append(f"Main caveat on {leader_name}: {risk}.")
    if lean == "Close / depends on roster":
        bullets.append(f"{leader_name} and {runner_name} are close enough to use roster fit.")
    return bullets[:6] or [NOT_ENOUGH_INFORMATION]


def _red_flags(rows: list[dict[str, Any]]) -> list[str]:
    flags: list[str] = []
    for row in rows:
        player = _player_name(row)
        for label, key in (
            ("age missing", "age"),
            ("unsupported outcome", "outcome_applicable_summary"),
            ("no market match", "available_pool_adp_range"),
        ):
            value = _field(row, key)
            if value == NOT_ENOUGH_INFORMATION:
                flags.append(f"{player}: {label}.")
        warning = _field(row, "on_clock_warning")
        if warning != NOT_ENOUGH_INFORMATION:
            flags.append(f"{player}: {warning}")
        caveat = _field(row, "candidate_key_caveat")
        if caveat != NOT_ENOUGH_INFORMATION and "warning" in caveat.lower():
            flags.append(f"{player}: {caveat}")
    return _dedupe(flags)


def _best_use_case(row: dict[str, Any], lean: str) -> str:
    risk_text = " ".join(
        _field(row, key)
        for key in ("main_risk", "candidate_key_caveat", "on_clock_warning")
    ).lower()
    age = _float_or_none(row.get("age"))
    band = _field(row, "candidate_value_band").lower()
    position = _field(row, "position")
    if lean == NOT_ENOUGH_INFORMATION:
        return NOT_ENOUGH_INFORMATION
    if "age" in risk_text or (age is not None and age >= 30):
        return "win-now / discount only"
    if "rookie" in band or "upside" in band:
        return "upside / long-term"
    if position == "QB":
        return "long-term stability; format-dependent in 1QB"
    if "floor" in risk_text:
        return "floor"
    return "long-term / best-player-at-value"


def _data_quality(rows: list[dict[str, Any]], red_flags: list[str]) -> str:
    if any(_best_rank_value(row) is None for row in rows):
        return "Low"
    if len(red_flags) >= 4:
        return "Low"
    if red_flags:
        return "Medium"
    return "High"


def _rank_signal(row: dict[str, Any]) -> str:
    for label, key in (
        ("NWR/Dynasty Candidate Rank", "dynasty_asset_rank"),
        ("Tuned Candidate Rank", "cross_asset_candidate_rank"),
        ("Frozen Baseline Rank", "final_board_rank"),
    ):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            return f"{label}: {value}"
    return NOT_ENOUGH_INFORMATION


def _tier_signal(row: dict[str, Any]) -> str:
    for key in (
        "dynasty_asset_tier",
        "on_clock_decision_tier",
        "candidate_value_band",
        "final_tier",
    ):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


def _outcome_signal(row: dict[str, Any]) -> str:
    value = _field(row, "outcome_applicable_summary")
    if value.lower() in {"unsupported", "no", "none"}:
        return NOT_ENOUGH_INFORMATION
    return value


def _risk_signal(row: dict[str, Any]) -> str:
    for key in ("main_risk", "candidate_key_caveat", "on_clock_warning", "risk_notes"):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


def _market_signal(row: dict[str, Any]) -> str:
    pieces = []
    for key in ("available_pool_adp_range", "current_pick_value", "market_sanity_label"):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            pieces.append(value)
    return " / ".join(pieces) if pieces else NOT_ENOUGH_INFORMATION


def _confidence_text(row: dict[str, Any]) -> str:
    for key in ("dynasty_asset_confidence", "confidence_band", "on_clock_confidence"):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            if "high" in value.lower():
                return "High"
            if "medium" in value.lower():
                return "Medium"
            if "low" in value.lower():
                return "Low"
            return value
    return NOT_ENOUGH_INFORMATION


def _has_low_confidence(row: dict[str, Any]) -> bool:
    return _confidence_text(row).lower() == "low"


def _has_loud_warning(row: dict[str, Any]) -> bool:
    text = " ".join(str(value) for value in row.values()).lower()
    return "loud warning" in text or "major" in text or "review required" in text


def _age_edge(leader: dict[str, Any], runner_up: dict[str, Any]) -> str:
    leader_age = _float_or_none(leader.get("age"))
    runner_age = _float_or_none(runner_up.get("age"))
    if leader_age is None or runner_age is None:
        return ""
    gap = runner_age - leader_age
    if abs(gap) < 2:
        return ""
    if gap > 0:
        return f"{_player_name(leader)} has the age edge ({leader_age:.1f} vs {runner_age:.1f})."
    return f"{_player_name(runner_up)} has the age edge ({runner_age:.1f} vs {leader_age:.1f})."


def _player_name(row: dict[str, Any]) -> str:
    return _field(row, "player")


def _field(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return NOT_ENOUGH_INFORMATION
    return text


def _float_or_none(value: Any) -> float | None:
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output
