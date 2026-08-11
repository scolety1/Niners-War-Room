"""Concise owner decision summary for source-separated Player Compare evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


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


def build_owner_compare_summary(rows: list[dict[str, Any]]) -> OwnerCompareSummary:
    if len(rows) < 2:
        return OwnerCompareSummary((), ())
    leans = (
        _short_term_lean(rows),
        _research_lean(rows, "Medium term", "research_outlook_3y"),
        _research_lean(rows, "Long term", "research_outlook_5y"),
    )
    ranges = tuple(
        {
            "Player": _text(row.get("player")) or "Unknown player",
            "Floor": _text(row.get("research_downside_signal")) or "Not admitted",
            "NWR Expected": (
                _text(row.get("research_tier"))
                or _text(row.get("source_tier"))
                or "Not admitted"
            ),
            "Ceiling": _text(row.get("research_ceiling_signal")) or "Not admitted",
            "Age / window": _age_window(row),
            "Risk / uncertainty": _risk(row),
            "Range authority": "Unified Research Preview — research only",
        }
        for row in rows
    )
    return OwnerCompareSummary(leans=leans, ranges=ranges)


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
            rank = int(_text(row.get("research_rank")))
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
    return CompareLean(
        horizon,
        best[1],
        "Unified Research Preview — research only",
        "Higher frozen research neighborhood "
        f"(rank {best[0]}); outlook: {best[2] or 'unavailable'}.",
    )


def _age_window(row: dict[str, Any]) -> str:
    age = _text(row.get("age"))
    position = _text(row.get("position"))
    return f"Age {age} · {position} lifecycle context" if age else "Age/window unavailable"


def _risk(row: dict[str, Any]) -> str:
    warning = _text(row.get("warning_flags")) or _text(row.get("risk_notes"))
    confidence = _text(row.get("research_confidence")) or _text(
        row.get("source_confidence")
    )
    if warning:
        return warning
    return f"Research confidence: {confidence}" if confidence else "Not enough information"


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.casefold() in {"", "nan", "none", "null", "<na>"} else text
