from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from src.services.mock_draft_input_contract import (
    GLOBAL_BLOCKED_COLUMNS,
    INPUT_SCHEMAS,
    MARKET_CONTEXT_COLUMNS,
    NWR_PRIVATE_VALUE_COLUMNS,
    READINESS_GREEN,
    READINESS_RED,
    READINESS_YELLOW,
)


@dataclass(frozen=True)
class SchemaDiagnosticReport:
    schema_key: str
    readiness: str
    missing_columns: tuple[str, ...]
    unexpected_columns: tuple[str, ...]
    forbidden_columns: tuple[str, ...]
    suggested_schema_key: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    no_files_written: bool = True
    no_simulations_run: bool = True
    no_draft_output: bool = True


def diagnose_schema(
    schema_key: str,
    actual_columns: Iterable[str],
    *,
    allow_extra_columns: bool = True,
) -> SchemaDiagnosticReport:
    if schema_key not in INPUT_SCHEMAS:
        return SchemaDiagnosticReport(
            schema_key=schema_key,
            readiness=READINESS_RED,
            missing_columns=(),
            unexpected_columns=(),
            forbidden_columns=(),
            suggested_schema_key="",
            warnings=(),
            errors=(f"Unknown schema role: {schema_key}.",),
        )

    headers = frozenset(_normalize(column) for column in actual_columns if column)
    schema = INPUT_SCHEMAS[schema_key]
    missing = tuple(sorted(schema.required_columns - headers))
    unexpected = tuple(sorted(headers - schema.required_columns))
    forbidden = _forbidden_columns(schema_key, headers)
    warnings: list[str] = []
    errors: list[str] = []

    if missing:
        errors.append("Required columns are missing.")
    if forbidden:
        errors.append("Forbidden columns violate source separation.")
    if unexpected and allow_extra_columns:
        warnings.append("Unexpected columns require manual review.")
    if unexpected and not allow_extra_columns:
        errors.append("Unexpected columns are not allowed for this schema.")

    if errors:
        readiness = READINESS_RED
    elif warnings:
        readiness = READINESS_YELLOW
    else:
        readiness = READINESS_GREEN

    return SchemaDiagnosticReport(
        schema_key=schema_key,
        readiness=readiness,
        missing_columns=missing,
        unexpected_columns=unexpected,
        forbidden_columns=forbidden,
        suggested_schema_key=suggest_schema_role(headers),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def suggest_schema_role(actual_columns: Iterable[str]) -> str:
    headers = frozenset(_normalize(column) for column in actual_columns if column)
    best_key = ""
    best_overlap = 0
    for key, schema in INPUT_SCHEMAS.items():
        overlap = len(headers & schema.required_columns)
        if overlap > best_overlap:
            best_key = key
            best_overlap = overlap
    return best_key


def _forbidden_columns(schema_key: str, headers: frozenset[str]) -> tuple[str, ...]:
    forbidden = set(headers & GLOBAL_BLOCKED_COLUMNS)
    if schema_key == "nwr_private_values":
        forbidden.update(headers & MARKET_CONTEXT_COLUMNS)
    if schema_key == "market_context":
        forbidden.update(headers & NWR_PRIVATE_VALUE_COLUMNS)
    return tuple(sorted(forbidden))


def _normalize(column: str) -> str:
    return column.strip().lower()
