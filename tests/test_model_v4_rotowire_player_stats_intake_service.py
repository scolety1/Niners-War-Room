import json
from pathlib import Path

from src.services.model_v4_rotowire_player_stats_intake_service import (
    build_rotowire_player_stats_intake,
    write_rotowire_player_stats_intake_outputs,
)


def test_rotowire_player_stats_intake_reads_only_canonical_stats_files() -> None:
    result = build_rotowire_player_stats_intake()

    assert len(result.validation_rows) == 60
    assert result.summary["seasons"] == "2021|2022|2023|2024|2025"
    assert result.summary["source_families"] == "passing|receiving|rushing"
    assert result.summary["model_scores_changed"] is False

    source_files = {row["source_file"] for row in result.clean_rows}
    assert "2021/passing/basic.csv" in source_files
    assert "2021/passing/rotowire-passing-basic-stats (3).csv" not in source_files


def test_rotowire_player_stats_intake_preserves_grouped_duplicate_headers() -> None:
    result = build_rotowire_player_stats_intake()
    projection = next(
        row
        for row in result.clean_rows
        if row["source_file"] == "2025/receiving/advanced.csv"
        and row["player_name"] == "Jaxon Smith-Njigba"
    )
    metrics = json.loads(str(projection["metrics_json"]))

    assert metrics["receiving_tar"] == 162
    assert metrics["routes_run_rts"] == 509
    assert metrics["routes_run_tprr"] == 31.8
    assert metrics["air_yards_ay_depth_of_target_ay"] == 1807
    assert metrics["team_ay"] == 49.3
    assert metrics["after_catch_avg"] == 4.6
    assert projection["source_status"] == "imported_real_data"


def test_rotowire_player_stats_intake_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_player_stats_intake()
    paths = write_rotowire_player_stats_intake_outputs(tmp_path, result)

    assert paths["clean"].exists()
    assert paths["validation"].exists()
    assert paths["summary"].exists()
    assert "Jaxon Smith-Njigba" in paths["clean"].read_text(encoding="utf-8")
