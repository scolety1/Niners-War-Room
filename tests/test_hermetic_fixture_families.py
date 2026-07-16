from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKED_FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "hermetic" / "local_export_pack_v1"
EXPECTED_FAMILIES = (
    "F01_CURRENT_VALUE_BOARD",
    "F02_EVIDENCE_AND_FORMULA",
    "F03_DECISION_REVIEW_STACK",
    "F04_ROOKIE_PROSPECT_REVIEW",
    "F05_HISTORICAL_REPLAY",
    "F06_LICENSED_ROTOWIRE_RAW",
    "F07_PRIVATE_LEAGUE_PACK",
    "F08_EXTERNAL_PROSPECT_SOURCES",
    "F09_ABSOLUTE_LOCAL_WORKOUT",
    "F10_DRAFT_HISTORY_AND_TEMPLATE",
    "F11_CROSS_OUTPUT_AGGREGATES",
)


def _pack_root() -> Path:
    configured = os.environ.get("NWR_HERMETIC_PACK_ROOT")
    return Path(configured).resolve() if configured else TRACKED_FIXTURE_ROOT.resolve()


def _load_rows() -> dict[str, dict[str, str]]:
    root = _pack_root()
    if root != TRACKED_FIXTURE_ROOT.resolve():
        manifest = json.loads((root / "PACK_MANIFEST.json").read_text(encoding="utf-8"))
        assert manifest["packId"] == "nwr-hermetic-local-export-behavior-fixtures"
        assert manifest["version"] == "1.0.0"
        assert manifest["rights"] == "FICTIONAL_RIGHTS_CLEAR_TEST_DATA_ONLY"
    with (root / "payload" / "families.csv").open(newline="", encoding="utf-8") as handle:
        rows = {row["family_id"]: row for row in csv.DictReader(handle)}
    assert tuple(rows) == EXPECTED_FAMILIES
    return rows


def _evaluate(row: dict[str, str]) -> float:
    left = float(row["input_a"])
    right = float(row["input_b"])
    operations = {
        "sum": lambda: left + right,
        "difference": lambda: left - right,
        "product": lambda: left * right,
        "ratio": lambda: left / right,
        "equality": lambda: float(left == right),
        "maximum": lambda: max(left, right),
        "minimum": lambda: min(left, right),
        "absolute_gap": lambda: abs(left - right),
    }
    return operations[row["behavior"]]()


@pytest.mark.parametrize("family_id", EXPECTED_FAMILIES)
def test_fictional_fixture_closes_safe_behavior_family(family_id: str) -> None:
    row = _load_rows()[family_id]
    assert row["fixture_label"] == "FICTIONAL_TEST_FIXTURE_NOT_REAL"
    assert row["entity_id"].startswith("fictional_")
    assert _evaluate(row) == pytest.approx(float(row["expected"]))
