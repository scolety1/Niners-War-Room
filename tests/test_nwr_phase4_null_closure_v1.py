from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_nwr_phase4_null_closure_v1 import (
    FAMILIES,
    GOLDEN_RELATIVE,
    PACKET_RELATIVE,
    PHASE3_RELATIVE,
    read_csv,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]


def test_phase3_truthful_null_is_exact() -> None:
    summary = json.loads((ROOT / PHASE3_RELATIVE / "GAUNTLET_SUMMARY.json").read_text())
    assert summary["overall_verdict"] == "NULL_NO_FAMILY_PASSED"
    assert summary["families_passed"] == []


def test_all_five_families_remain_unpromoted() -> None:
    rows = read_csv(ROOT / PACKET_RELATIVE / "FEATURE_FAMILY_DISPOSITION.csv")
    assert {row["family_id"] for row in rows} == FAMILIES
    assert {row["formula_use"] for row in rows} == {"NOT_AUTHORIZED"}
    assert {row["ranking_use"] for row in rows} == {"NOT_AUTHORIZED"}


def test_optional_lanes_are_not_required_and_not_executed() -> None:
    rows = read_csv(ROOT / PACKET_RELATIVE / "OPTIONAL_LANE_DISPOSITION.csv")
    assert {row["phase"] for row in rows} == {"PHASE_5", "PHASE_6"}
    assert {row["work_executed"] for row in rows} == {"NO"}
    assert {row["owner_decision_required"] for row in rows} == {"NO"}


def test_phase7_is_the_only_active_next_gate() -> None:
    gates = read_csv(ROOT / GOLDEN_RELATIVE / "PHASE_GATE_MATRIX.csv")
    assert [row["gate"] for row in gates if row["status"] == "ACTIVE"] == ["PHASE_7"]


def test_phase4_packet_validates() -> None:
    result = validate(ROOT)
    assert result["valid"] is True
    assert result["production_changes"] == 0
    assert result["optional_lanes_not_required"] == 2
