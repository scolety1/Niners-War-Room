from __future__ import annotations

import json
from pathlib import Path

from src.services.nflverse_refresh_health_service import (
    CANONICAL_DATASET_IDS,
    build_nflverse_dataset_health,
    dataset_registry_rows,
)


def test_dataset_registry_has_packet_canonical_rows_once() -> None:
    rows = dataset_registry_rows()

    assert [row["dataset_id"] for row in rows] == list(CANONICAL_DATASET_IDS)
    assert len(rows) == 25
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["rank_logic_allowed"] for row in rows} == {"false"}
    assert rows[-1]["dataset_id"] == "ff_rankings"
    assert rows[-1]["policy_status"] == "blocked_policy"


def test_dataset_health_isolates_failed_dataset_without_zero_default(tmp_path: Path) -> None:
    snapshot = tmp_path / "shared" / "scheduled_ingest" / "nflverse" / "run"
    status_root = tmp_path / "status"
    snapshot.mkdir(parents=True)
    (snapshot / "player_stats_weekly.csv").write_text(
        "season,week,player_id,player_name\n2025,1,p1,Drake Maye\n",
        encoding="utf-8",
    )
    metadata = {
        "created_at": "2026-06-30T12:00:00+00:00",
        "package_version": "test",
        "seasons": [2025],
        "datasets": [
            {
                "name": "player_stats_weekly",
                "file_name": "player_stats_weekly.csv",
                "status": "ok",
                "row_count": 1,
                "column_count": 4,
                "field_names": ["season", "week", "player_id", "player_name"],
            },
            {
                "name": "injuries",
                "file_name": "injuries.csv",
                "status": "failed",
                "row_count": None,
                "column_count": None,
                "field_names": [],
                "error": "planned failure",
            },
        ],
    }
    (snapshot / "snapshot_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    rows = build_nflverse_dataset_health(
        shared_root=tmp_path / "shared",
        status_root=status_root,
        snapshot_dir=snapshot,
    )
    by_dataset = {row.dataset_id: row for row in rows}

    assert by_dataset["player_stats_weekly"].execution_status == "succeeded"
    assert by_dataset["player_stats_weekly"].row_count == "1"
    assert by_dataset["injuries"].execution_status == "failed"
    assert by_dataset["injuries"].row_count == "Not enough information"
    assert by_dataset["injuries"].status == "RED"
    assert by_dataset["ff_rankings"].status == "BLOCKED"
    assert by_dataset["ff_rankings"].execution_status == "blocked_policy"
    assert all(row.model_use_allowed == "false" for row in rows)
    assert all(row.training_allowed == "false" for row in rows)
    assert all(row.rank_logic_allowed == "false" for row in rows)


def test_missing_required_fields_fail_schema_without_clean_default(tmp_path: Path) -> None:
    snapshot = tmp_path / "shared" / "scheduled_ingest" / "nflverse" / "bad_schema"
    snapshot.mkdir(parents=True)
    (snapshot / "player_stats_weekly.csv").write_text(
        "player_id,player_name\np1,Drake Maye\n",
        encoding="utf-8",
    )
    metadata = {
        "created_at": "2026-06-30T12:00:00+00:00",
        "package_version": "test",
        "seasons": [2025],
        "datasets": [
            {
                "name": "player_stats_weekly",
                "file_name": "player_stats_weekly.csv",
                "status": "ok",
                "row_count": 1,
                "column_count": 2,
                "field_names": ["player_id", "player_name"],
            }
        ],
    }
    (snapshot / "snapshot_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    weekly = next(
        row
        for row in build_nflverse_dataset_health(
            shared_root=tmp_path / "shared",
            status_root=tmp_path / "status",
            snapshot_dir=snapshot,
        )
        if row.dataset_id == "player_stats_weekly"
    )

    assert weekly.schema_status == "fail"
    assert weekly.coverage_status == "fail"
    assert weekly.status == "RED"
    assert "zero/false/healthy/clean" in weekly.user_explanation
