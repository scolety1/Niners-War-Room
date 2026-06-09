import json
from pathlib import Path

from src.services.model_v4_rotowire_role_usage_intake_service import (
    build_rotowire_role_usage_intake,
    write_rotowire_role_usage_intake_outputs,
)


def test_rotowire_role_usage_intake_covers_role_sources() -> None:
    result = build_rotowire_role_usage_intake()

    assert len(result.validation_rows) == 20
    assert result.summary["seasons"] == "2021|2022|2023|2024|2025"
    assert result.summary["source_families"] == "alignment|snaps|targets|te_routes"
    assert result.summary["model_scores_changed"] is False


def test_rotowire_role_usage_intake_preserves_route_snap_and_target_evidence() -> None:
    result = build_rotowire_role_usage_intake()
    jsn_alignment = next(
        row
        for row in result.clean_rows
        if row["season"] == "2025"
        and row["source_family"] == "alignment"
        and row["player_name"] == "Jaxon Smith-Njigba"
    )
    alignment_metrics = json.loads(str(jsn_alignment["metrics_json"]))
    assert alignment_metrics["plays_total"] > 0
    assert "grouped_slot" in alignment_metrics

    kittle_routes = next(
        row
        for row in result.clean_rows
        if row["season"] == "2025"
        and row["source_family"] == "te_routes"
        and row["player_name"] == "George Kittle"
    )
    route_metrics = json.loads(str(kittle_routes["metrics_json"]))
    assert "route_data_route" in route_metrics
    assert kittle_routes["source_status"] == "imported_route_data"

    puka_targets = next(
        row
        for row in result.clean_rows
        if row["season"] == "2025"
        and row["source_family"] == "targets"
        and row["player_name"] == "Puka Nacua"
    )
    target_metrics = json.loads(str(puka_targets["metrics_json"]))
    assert target_metrics["receiving_totals_tar"] == 208
    assert target_metrics["week_by_week_targets_tar_g"] == 10.9


def test_rotowire_role_usage_intake_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_role_usage_intake()
    paths = write_rotowire_role_usage_intake_outputs(tmp_path, result)

    assert paths["clean"].exists()
    assert paths["validation"].exists()
    assert paths["summary"].exists()
    assert "imported_route_data" in paths["clean"].read_text(encoding="utf-8")
