from __future__ import annotations

from pathlib import Path

from scripts.validate_nwr_phase7_product_completion_v1 import (
    EXPECTED_COUNTS,
    PACKET_RELATIVE,
    read_csv,
)

ROOT = Path(__file__).resolve().parents[1]


def test_phase7_authority_contract_is_source_separated() -> None:
    rows = read_csv(ROOT / PACKET_RELATIVE / "AUTHORITY_CONTRACT.csv")
    assert {row["asset_type"]: int(row["count"]) for row in rows} == EXPECTED_COUNTS
    assert {row["recommendation_behavior"] for row in rows} == {"NONE"}
    assert len({row["source_label"] for row in rows}) == 3


def test_product_matrix_truthfully_records_deferred_persistence_slices() -> None:
    rows = {
        row["surface"]: row
        for row in read_csv(ROOT / PACKET_RELATIVE / "PRODUCT_COMPLETION_MATRIX.csv")
    }
    assert rows["Personal Board overlay"]["disposition"] == "FORMALLY_DEFERRED"
    assert rows["Decision Journal"]["disposition"] == "FORMALLY_DEFERRED"


def test_phase7_changed_routes_are_exact() -> None:
    rows = read_csv(ROOT / PACKET_RELATIVE / "ROUTE_CHANGE_INVENTORY.csv")
    assert {row["route"] for row in rows} == {"/", "/asset-explorer", "/rookie-board"}
