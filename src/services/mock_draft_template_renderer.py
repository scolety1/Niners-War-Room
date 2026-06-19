from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from src.services.mock_draft_input_contract import (
    INPUT_SCHEMAS,
    MARKET_CONTEXT_COLUMNS,
    NWR_PRIVATE_VALUE_COLUMNS,
)

TEMPLATE_ROLE_TO_SCHEMA_KEY = {
    "rookie_input": "frozen_rookie_input",
    "veteran_pool": "veteran_pool",
    "pick_order": "pick_order",
    "my_picks": "my_picks",
    "rosters_keepers": "rosters",
    "team_needs": "team_needs",
    "nwr_private_values": "nwr_private_values",
    "market_context": "market_context",
}


@dataclass(frozen=True)
class CsvTemplate:
    role: str
    headers: tuple[str, ...]
    csv_text: str
    no_files_written: bool = True
    no_simulations_run: bool = True


def render_blank_template(role: str) -> CsvTemplate:
    schema_key = TEMPLATE_ROLE_TO_SCHEMA_KEY[role]
    headers = tuple(sorted(INPUT_SCHEMAS[schema_key].required_columns))
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    return CsvTemplate(role=role, headers=headers, csv_text=buffer.getvalue())


def render_all_blank_templates() -> dict[str, CsvTemplate]:
    return {role: render_blank_template(role) for role in TEMPLATE_ROLE_TO_SCHEMA_KEY}


def template_has_source_contamination(role: str) -> bool:
    headers = set(render_blank_template(role).headers)
    if role == "nwr_private_values":
        return bool(headers & MARKET_CONTEXT_COLUMNS)
    if role == "market_context":
        return bool(headers & NWR_PRIVATE_VALUE_COLUMNS)
    return False
