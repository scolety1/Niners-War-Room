from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rotowire_stats_first_value_service import (
    VALUE_HEADER,
    build_rotowire_stats_first_value_layer,
    write_rotowire_stats_first_value_outputs,
)


def test_rotowire_stats_first_value_covers_truth_set_without_external_value_leaks() -> None:
    result = build_rotowire_stats_first_value_layer()

    assert len(result.value_rows) == 80
    assert result.summary["projection_rows_used_for_core_value"] == 0
    assert result.summary["market_value_used_for_private_value"] is False
    assert result.summary["league_rank_used_for_private_value"] is False
    assert result.summary["active_rankings_overwritten"] is False


def test_rotowire_stats_first_value_keeps_incoming_rookies_weak_review() -> None:
    result = build_rotowire_stats_first_value_layer()
    rows = {row["player_name"]: row for row in result.value_rows}

    assert rows["Jeremiyah Love"]["confidence_label"] == "weak_review"
    assert "missing_historical_production" in str(rows["Jeremiyah Love"]["warnings"])
    assert rows["Fernando Mendoza"]["confidence_label"] == "weak_review"


def test_rotowire_stats_first_value_applies_1qb_no_te_premium_format_multiplier() -> None:
    result = build_rotowire_stats_first_value_layer()
    rows = {row["player_name"]: row for row in result.value_rows}

    assert float(rows["Trey McBride"]["format_position_multiplier"]) < 1.0
    assert float(rows["Josh Allen"]["format_position_multiplier"]) < 1.0
    assert float(rows["Bijan Robinson"]["format_position_multiplier"]) == 1.0
    assert int(rows["Trey McBride"]["overall_rank"]) > int(rows["Bijan Robinson"]["overall_rank"])


def test_rotowire_stats_first_value_uses_qb_role_usage_as_not_applicable() -> None:
    result = build_rotowire_stats_first_value_layer()
    components = {
        (row["player_name"], row["component"]): row
        for row in result.component_rows
    }
    value_rows = {row["player_name"]: row for row in result.value_rows}

    assert ("Josh Allen", "snap_role") not in components
    assert ("Josh Allen", "route_receiving_role") not in components
    assert "missing_role_usage" not in str(value_rows["Josh Allen"]["warnings"])


def test_rotowire_stats_first_value_uses_licensed_route_export_as_component() -> None:
    result = build_rotowire_stats_first_value_layer()
    components = {
        (row["player_name"], row["component"]): row
        for row in result.component_rows
    }

    route = components[("Jaxon Smith-Njigba", "route_receiving_role")]
    assert route["source_status"] == "licensed_user_export_route_data"
    assert float(route["contribution"]) > 0


def test_rotowire_stats_first_value_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_stats_first_value_layer()
    paths = write_rotowire_stats_first_value_outputs(tmp_path, result)

    assert paths["value"].exists()
    assert paths["components"].exists()
    assert paths["warnings"].exists()
    with paths["value"].open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == VALUE_HEADER
