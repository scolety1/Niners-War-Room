from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.mock_draft_input_contract import (
    NWR_PRIVATE_VALUE_COLUMNS,
    READINESS_GREEN,
    READINESS_RED,
)


@dataclass(frozen=True)
class TeamNeedsReport:
    readiness: str
    row_count: int
    errors: tuple[str, ...]
    opponent_behavior_only: bool = True
    no_simulations_run: bool = True


def validate_team_needs_contract(rows: Sequence[Mapping[str, object]]) -> TeamNeedsReport:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for column in ("team_id", "team_name", "position", "need_weight", "tendency_note"):
            if not row.get(column):
                errors.append(f"Team-need row {index} missing {column}.")
        try:
            weight = float(str(row.get("need_weight")))
        except (TypeError, ValueError):
            errors.append(f"Team-need row {index} has invalid need_weight.")
        else:
            if weight < 0 or weight > 1:
                errors.append(f"Team-need row {index} need_weight outside 0..1.")
        if set(row) & NWR_PRIVATE_VALUE_COLUMNS:
            errors.append("Opponent tendency rows cannot carry NWR private value.")
    return TeamNeedsReport(
        readiness=READINESS_RED if errors else READINESS_GREEN,
        row_count=len(rows),
        errors=tuple(errors),
    )
