from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.mock_draft_input_contract import (
    MARKET_CONTEXT_COLUMNS,
    READINESS_GREEN,
    READINESS_RED,
)


@dataclass(frozen=True)
class AvailablePoolReport:
    readiness: str
    rookie_count: int
    veteran_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    no_ranked_output: bool = True
    no_simulations_run: bool = True


def validate_available_pool_contract(
    rookie_rows: Sequence[Mapping[str, object]],
    veteran_rows: Sequence[Mapping[str, object]],
) -> AvailablePoolReport:
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for label, rows in (("rookie", rookie_rows), ("veteran", veteran_rows)):
        for index, row in enumerate(rows, start=1):
            if _is_blank_row(row):
                warnings.append(f"{label} row {index} is blank and was ignored.")
                continue
            missing = [
                column
                for column in ("asset_id", "player", "position")
                if not _text(row.get(column))
            ]
            if missing:
                errors.append(
                    f"{label} row {index} missing identity columns: "
                    f"{', '.join(missing)}."
                )
            asset_id = _text(row.get("asset_id"))
            if asset_id and asset_id in seen:
                errors.append(f"Duplicate asset_id in available pool: {asset_id}.")
            seen.add(asset_id)
            if label == "rookie" and str(row.get("source_label") or "rookie") != "rookie":
                errors.append(f"Rookie row {index} has unclear source label.")
            if label == "veteran" and str(row.get("source_label") or "veteran") != "veteran":
                errors.append(f"Veteran row {index} has unclear source label.")
            market_value_columns = sorted(set(row) & MARKET_CONTEXT_COLUMNS)
            if market_value_columns and "nwr_private_value" in row:
                errors.append("Market-only columns cannot define NWR private value.")
    return AvailablePoolReport(
        readiness=READINESS_RED if errors else READINESS_GREEN,
        rookie_count=len(rookie_rows),
        veteran_count=len(veteran_rows),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _is_blank_row(row: Mapping[str, object]) -> bool:
    return not any(_text(value) for value in row.values())
