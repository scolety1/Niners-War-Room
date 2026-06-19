from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.mock_draft_input_contract import READINESS_GREEN, READINESS_RED, READINESS_YELLOW


@dataclass(frozen=True)
class PickOrderReport:
    readiness: str
    pick_count: int
    my_pick_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    no_simulations_run: bool = True


def validate_pick_order_contract(
    pick_rows: Sequence[Mapping[str, object]],
    my_pick_rows: Sequence[Mapping[str, object]] | None,
) -> PickOrderReport:
    errors: list[str] = []
    warnings: list[str] = []
    pick_numbers: list[int] = []
    for index, row in enumerate(pick_rows, start=1):
        if _is_blank_row(row):
            warnings.append(f"Pick row {index} is blank and was ignored.")
            continue
        pick = _int_value(row.get("overall_pick"))
        if pick is None or pick <= 0:
            errors.append(f"Pick row {index} has invalid overall_pick.")
            continue
        pick_numbers.append(pick)
    duplicates = sorted({pick for pick in pick_numbers if pick_numbers.count(pick) > 1})
    if duplicates:
        errors.append(f"Duplicate pick numbers: {', '.join(str(pick) for pick in duplicates)}.")
    pick_set = set(pick_numbers)
    my_pick_count = 0
    if my_pick_rows is None:
        warnings.append("My-picks input is missing.")
    else:
        my_pick_count = len(my_pick_rows)
        for index, row in enumerate(my_pick_rows, start=1):
            if _is_blank_row(row):
                warnings.append(f"My-pick row {index} is blank and was ignored.")
                continue
            pick = _int_value(row.get("overall_pick"))
            if pick is None or pick not in pick_set:
                errors.append(f"My pick is not in pick order: {row.get('overall_pick')}.")
    readiness = READINESS_RED if errors else READINESS_YELLOW if warnings else READINESS_GREEN
    return PickOrderReport(
        readiness=readiness,
        pick_count=len(pick_rows),
        my_pick_count=my_pick_count,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _int_value(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _is_blank_row(row: Mapping[str, object]) -> bool:
    return not any("" if value is None else str(value).strip() for value in row.values())
