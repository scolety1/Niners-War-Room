from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from src.services.mock_draft_input_contract import (
    MARKET_CONTEXT_COLUMNS,
    NWR_PRIVATE_VALUE_COLUMNS,
    READINESS_GREEN,
    READINESS_RED,
)

COMMON_ALIASES = {
    "name": "player",
    "player_name": "player",
    "player_id": "asset_id",
    "pos": "position",
    "team": "nfl_team",
}

MARKET_ONLY_ALIASES = {
    "adp": "market_adp_pick",
    "market_adp": "market_adp_pick",
    "overall_adp": "market_adp_pick",
    "source_name": "market_source",
}

PRIVATE_ONLY_ALIASES = {
    "nwr_score": "nwr_private_value",
    "nwr_value": "nwr_private_value",
    "private_score": "nwr_private_value",
}

AMBIGUOUS_ALIASES = frozenset({"value", "score", "rank", "rating"})


@dataclass(frozen=True)
class HeaderAliasReport:
    schema_key: str
    readiness: str
    canonical_headers: tuple[str, ...]
    rejected_aliases: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    no_rankings_created: bool = True
    no_simulations_run: bool = True


def canonicalize_headers(headers: Iterable[str], *, schema_key: str) -> HeaderAliasReport:
    canonical: list[str] = []
    rejected: list[str] = []
    errors: list[str] = []

    for raw_header in headers:
        header = raw_header.strip().lower()
        if not header:
            continue
        mapped = _map_header(header, schema_key)
        if mapped is None:
            rejected.append(header)
            errors.append(f"Header alias requires manual mapping: {header}.")
        else:
            canonical.append(mapped)

    return HeaderAliasReport(
        schema_key=schema_key,
        readiness=READINESS_RED if errors else READINESS_GREEN,
        canonical_headers=tuple(canonical),
        rejected_aliases=tuple(rejected),
        warnings=(),
        errors=tuple(errors),
    )


def _map_header(header: str, schema_key: str) -> str | None:
    if header in AMBIGUOUS_ALIASES:
        return None
    if schema_key == "nwr_private_values" and (
        header in MARKET_ONLY_ALIASES or header in MARKET_CONTEXT_COLUMNS
    ):
        return None
    if schema_key == "market_context" and (
        header in PRIVATE_ONLY_ALIASES or header in NWR_PRIVATE_VALUE_COLUMNS
    ):
        return None
    if schema_key == "market_context" and header in MARKET_ONLY_ALIASES:
        return MARKET_ONLY_ALIASES[header]
    if schema_key == "nwr_private_values" and header in PRIVATE_ONLY_ALIASES:
        return PRIVATE_ONLY_ALIASES[header]
    return COMMON_ALIASES.get(header, header)
