from __future__ import annotations

import csv
from pathlib import Path

RECEIPT_CONTRACT_PATH = Path("docs/model_v4/RECEIPT_REQUIREMENT_CONTRACT.csv")
RECEIPT_CONTRACT_DOC_PATH = Path("docs/model_v4/RECEIPT_REQUIREMENT_CONTRACT.md")

EXPECTED_HEADER = [
    "receipt_section",
    "required_raw_fields",
    "normalized_fields",
    "source_status",
    "contribution_display",
    "warning_display",
    "when_section_unavailable",
]

REQUIRED_SECTIONS = {
    "production",
    "first-down scoring fit",
    "usage/opportunity",
    "snap/proxy role",
    "projection",
    "age/dropoff",
    "injury/context",
    "young-player prior",
    "confidence",
    "market context",
    "league-rank rule context",
}


def test_model_v4_receipt_requirement_contract_exists() -> None:
    assert RECEIPT_CONTRACT_PATH.exists()
    assert RECEIPT_CONTRACT_DOC_PATH.exists()


def test_model_v4_receipt_requirement_contract_has_required_sections() -> None:
    rows = _read_receipt_contract()

    assert set(rows) == REQUIRED_SECTIONS


def test_model_v4_receipt_requirement_contract_schema_is_complete() -> None:
    with RECEIPT_CONTRACT_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == EXPECTED_HEADER
    assert rows
    for row in rows:
        assert all(row[field].strip() for field in EXPECTED_HEADER)


def test_context_sections_stay_separate_from_private_value() -> None:
    rows = _read_receipt_contract()

    assert rows["market context"]["source_status"] == "trade_context_only"
    assert rows["league-rank rule context"]["source_status"] == "rule_context_only"
    assert rows["injury/context"]["source_status"] == "context_only"
    assert "separately from private" in rows["market context"]["contribution_display"]
    assert "separately from Dynasty Asset Value" in rows[
        "league-rank rule context"
    ]["contribution_display"]


def _read_receipt_contract() -> dict[str, dict[str, str]]:
    with RECEIPT_CONTRACT_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {row["receipt_section"]: row for row in rows}
