from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.mock_draft_input_contract import (
    MARKET_CONTEXT_COLUMNS,
    NWR_PRIVATE_VALUE_COLUMNS,
    READINESS_GREEN,
    READINESS_RED,
)


@dataclass(frozen=True)
class SeparationReport:
    readiness: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    no_rankings_created: bool = True
    no_simulations_run: bool = True


def validate_market_separation(
    market_rows: Sequence[Mapping[str, object]],
    private_value_rows: Sequence[Mapping[str, object]],
) -> SeparationReport:
    errors: list[str] = []
    market_columns = _columns(market_rows)
    private_columns = _columns(private_value_rows)
    private_in_market = sorted(market_columns & NWR_PRIVATE_VALUE_COLUMNS)
    market_in_private = sorted(private_columns & MARKET_CONTEXT_COLUMNS)
    if private_in_market:
        errors.append("Market context contains NWR private value columns.")
    if market_in_private:
        errors.append("NWR private value source contains market behavior columns.")
    if market_columns & private_columns & NWR_PRIVATE_VALUE_COLUMNS & MARKET_CONTEXT_COLUMNS:
        errors.append("Merged market/private source shape is invalid.")
    return SeparationReport(
        readiness=READINESS_RED if errors else READINESS_GREEN,
        errors=tuple(errors),
    )


def _columns(rows: Sequence[Mapping[str, object]]) -> set[str]:
    columns: set[str] = set()
    for row in rows:
        columns.update(str(key).strip().lower() for key in row)
    return columns
