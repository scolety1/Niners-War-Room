"""Concise owner decision summary for source-separated Player Compare evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.services.owner_mode_view_service import (
    market_decision_label,
    owner_range_contract,
    owner_risk,
)


@dataclass(frozen=True)
class CompareLean:
    horizon: str
    preferred: str
    authority: str
    reason: str


@dataclass(frozen=True)
class OwnerCompareSummary:
    leans: tuple[CompareLean, ...]
    ranges: tuple[dict[str, str], ...]
    notes: tuple[dict[str, object], ...]


def build_owner_compare_summary(rows: list[dict[str, Any]]) -> OwnerCompareSummary:
    if len(rows) < 2:
        return OwnerCompareSummary((), (), ())
    leans = (
        _short_term_lean(rows),
        _research_lean(rows, "Medium term", "research_outlook_3y"),
        _research_lean(rows, "Long term", "research_outlook_5y"),
    )
    ranges = tuple(
        {
            "Player": _text(row.get("player")) or "Unknown player",
            "Floor": owner_range_contract(row)["Floor"],
            "NWR Expected": owner_range_contract(row)["NWR Expected"],
            "Ceiling": owner_range_contract(row)["Ceiling"],
            "Age / window": _age_window(row),
            "Risk / uncertainty": owner_risk(row),
            "Range authority": owner_range_contract(row)["Authority"],
            "Range method": owner_range_contract(row)["Method"],
        }
        for row in rows
    )
    notes = tuple(_player_notes(row) for row in rows)
    return OwnerCompareSummary(leans=leans, ranges=ranges, notes=notes)


def _short_term_lean(rows: list[dict[str, Any]]) -> CompareLean:
    positions = {_text(row.get("position")).upper() for row in rows}
    if len(positions) != 1:
        return CompareLean(
            "Short term",
            "No cross-position lean",
            "Outcome V3",
            "NWR does not compare different position thresholds as if they were one scale.",
        )
    scored: list[tuple[float, str, str]] = []
    for row in rows:
        signals = row.get("outcome_signals", ())
        if isinstance(signals, str):
            signals = (signals,)
        current = next((str(value) for value in signals if "2026" in str(value)), "")
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)%", current)
        if match:
            scored.append((float(match.group(1)), _text(row.get("player")), current))
    if len(scored) != len(rows):
        return CompareLean(
            "Short term",
            "No admitted lean",
            "Outcome V3",
            "At least one player lacks a comparable governed 2026 Outcome probability.",
        )
    scored.sort(reverse=True)
    best = scored[0]
    if len(scored) > 1 and best[0] == scored[1][0]:
        return CompareLean(
            "Short term",
            "Too close",
            "Outcome V3",
            f"The applicable 2026 probabilities are tied at {best[0]:.1f}%.",
        )
    return CompareLean(
        "Short term",
        best[1],
        "Outcome V3",
        f"Higher applicable governed 2026 probability: {best[2]}.",
    )


def _research_lean(
    rows: list[dict[str, Any]], horizon: str, outlook_field: str
) -> CompareLean:
    ranked: list[tuple[int, str, str]] = []
    for row in rows:
        try:
            rank = int(float(_text(row.get("research_rank"))))
        except ValueError:
            continue
        ranked.append(
            (rank, _text(row.get("player")), _text(row.get(outlook_field)))
        )
    if len(ranked) != len(rows):
        return CompareLean(
            horizon,
            "No admitted production lean",
            "Unified Research Preview — research only",
            "The frozen research order does not cover every selected asset.",
        )
    ranked.sort()
    best = ranked[0]
    outlook = _research_score(best[2])
    return CompareLean(
        horizon,
        best[1],
        "Unified Research Preview — research only",
        "Higher frozen research neighborhood "
        f"(rank {best[0]}); research outlook score: {outlook}.",
    )


def _age_window(row: dict[str, Any]) -> str:
    age = _text(row.get("age"))
    position = _text(row.get("position"))
    return f"Age {age} · {position} lifecycle context" if age else "Age/window unavailable"


def _player_notes(row: dict[str, Any]) -> dict[str, object]:
    player = _text(row.get("player")) or "Unknown player"
    advantages: list[str] = []
    risks: list[str] = []
    if rank := _text(row.get("nwr_rank")):
        advantages.append(f"Finished V1 rank: #{rank}.")
    if position_rank := _text(row.get("position_rank")):
        advantages.append(f"Position rank: {position_rank}.")
    ceiling = owner_range_contract(row)["Ceiling"]
    if ceiling != "Not enough information":
        advantages.append(f"Research ceiling context: {ceiling}.")
    signals = row.get("outcome_signals", ())
    if isinstance(signals, str):
        signals = (signals,)
    if signals:
        advantages.append(f"Governed outcome context: {signals[0]}.")
    else:
        risks.append("No comparable governed Outcome V3 signal is available.")
    market, _gap = market_decision_label(row.get("nwr_rank"), row.get("market_dp_rank"))
    if market in {"Potential Buy", "NWR Higher"}:
        advantages.append(f"Market opportunity context: {market}.")
    elif market in {"Market Higher", "Potential Sell / Caution"}:
        risks.append(f"Market disagreement: {market}.")
    risk = owner_risk(row)
    if risk != "No major risk flag":
        risks.append(risk)
    if not risks:
        risks.append("No major admitted risk flag; review confidence and range method.")
    return {
        "Player": player,
        "Advantages": tuple(dict.fromkeys(advantages))[:4],
        "Risks": tuple(dict.fromkeys(risks))[:4],
    }


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.casefold() in {"", "nan", "none", "null", "<na>"} else text


def _research_score(value: object) -> str:
    try:
        return f"{float(_text(value)):.1f} research-index points"
    except ValueError:
        return "unavailable"
