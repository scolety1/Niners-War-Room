from __future__ import annotations

import csv
import json
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES
from src.services.data_pack_catalog_service import (
    applied_pack_notice_for_path,
    catalog_rows,
    discover_data_packs,
)


def test_discover_data_packs_includes_default_and_generated_pack(tmp_path: Path) -> None:
    default_pack = tmp_path / "sample_data" / "2026_pre_declaration"
    generated_pack = tmp_path / "local_exports" / "data_packs" / "fresh_pack"
    _write_minimal_pack(default_pack, "2026-pre-draft")
    _write_minimal_pack(generated_pack, "2026-current")

    entries = discover_data_packs(
        project_root=tmp_path,
        default_data_pack="sample_data/2026_pre_declaration",
    )

    names = [entry.name for entry in entries]
    assert "2026_pre_declaration" in names
    assert "fresh_pack" in names
    assert entries[0].source_group == "default"
    assert all(entry.error_count == 0 for entry in entries)

    rows = catalog_rows(entries)
    assert {row["name"] for row in rows} == set(names)


def test_discover_data_packs_marks_invalid_pack_with_error(tmp_path: Path) -> None:
    invalid_pack = tmp_path / "local_exports" / "data_packs" / "bad_pack"
    invalid_pack.mkdir(parents=True)
    (invalid_pack / "fact_rosters.csv").write_text("bad\n", encoding="utf-8")

    entries = discover_data_packs(
        project_root=tmp_path,
        default_data_pack="missing_default",
    )

    assert entries[0].name == "bad_pack"
    assert entries[0].error_count > 0


def test_discover_data_packs_shows_applied_pack_admission_status(
    tmp_path: Path,
) -> None:
    generated_pack = tmp_path / "local_exports" / "data_packs" / "applied_pack"
    _write_minimal_pack(generated_pack, "2026-current")
    _write_applied_pack_manifest(generated_pack, applied_row_count=1)

    entries = discover_data_packs(
        project_root=tmp_path,
        default_data_pack="missing_default",
    )
    rows = catalog_rows(entries)

    assert entries[0].applied_pack_status == "review"
    assert entries[0].applied_row_count == 1
    assert "applied review" in entries[0].status_label
    assert rows[0]["applied_pack_status"] == "review"
    assert rows[0]["applied_rows"] == 1


def test_discover_data_packs_blocks_zero_row_applied_pack(tmp_path: Path) -> None:
    generated_pack = tmp_path / "local_exports" / "data_packs" / "zero_applied"
    _write_minimal_pack(generated_pack, "2026-current")
    _write_applied_pack_manifest(generated_pack, applied_row_count=0)

    entries = discover_data_packs(
        project_root=tmp_path,
        default_data_pack="missing_default",
    )

    assert entries[0].applied_pack_status == "blocked"
    assert "zero applied model rows" in entries[0].applied_pack_reason


def test_applied_pack_notice_for_selected_pack(tmp_path: Path) -> None:
    generated_pack = tmp_path / "local_exports" / "data_packs" / "zero_applied"
    _write_minimal_pack(generated_pack, "2026-current")
    _write_applied_pack_manifest(generated_pack, applied_row_count=0)
    plain_pack = tmp_path / "local_exports" / "data_packs" / "plain_pack"
    _write_minimal_pack(plain_pack, "2026-current")
    entries = discover_data_packs(
        project_root=tmp_path,
        default_data_pack="missing_default",
    )

    notice = applied_pack_notice_for_path(entries, generated_pack)
    plain_notice = applied_pack_notice_for_path(entries, plain_pack)

    assert notice is not None
    assert notice["applied_pack_status"] == "blocked"
    assert "Do not use" in str(notice["next_action"])
    assert plain_notice is None


def _write_minimal_pack(path: Path, snapshot_date: str) -> None:
    path.mkdir(parents=True)
    for file_name in REQUIRED_V1_FILES:
        schema = CSV_SCHEMAS[file_name]
        row = _row_for_file(file_name, snapshot_date)
        with (path / file_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(schema.all_columns))
            writer.writeheader()
            writer.writerow(row)


def _row_for_file(file_name: str, snapshot_date: str) -> dict[str, object]:
    common_player = {
        "player_id": "p1",
        "player_name": "Alpha Back",
        "position": "RB",
        "nfl_team": "MIA",
    }
    if file_name == "dim_players.csv":
        return common_player
    if file_name == "fact_rosters.csv":
        return {
            "snapshot_date": snapshot_date,
            "season": "2026",
            "team_id": "niners",
            "team_name": "Niners",
            "player_id": "p1",
            "player_name": "Alpha Back",
            "official_rank": "10",
        }
    if file_name == "fact_official_rankings.csv":
        return {
            "snapshot_date": snapshot_date,
            "season": "2026",
            "player_id": "p1",
            "official_rank": "10",
        }
    if file_name == "fact_future_picks.csv":
        return {
            "snapshot_date": snapshot_date,
            "season": "2026",
            "pick_year": "2026",
            "round": "1",
            "slot": "1",
            "pick_label": "2026 1.01",
        }
    if file_name == "fact_pick_values.csv":
        return {
            "snapshot_date": snapshot_date,
            "pick_year": "2026",
            "pick_label": "2026 1.01",
            "round": "1",
            "slot": "1",
            "overall_pick": "1",
            "base_value_1000": "1000",
            "final_pick_value": "1000",
        }
    if file_name == "model_outputs.csv":
        return {
            "snapshot_date": snapshot_date,
            "player_id": "p1",
            "player_name": "Alpha Back",
        }
    return {
        "snapshot_date": snapshot_date,
        "data_pack_name": "pack",
        "file_name": file_name,
    }


def _write_applied_pack_manifest(path: Path, *, applied_row_count: int) -> None:
    (path / "model_applied_pack_manifest.json").write_text(
        json.dumps(
            {
                "applied_pack_id": path.name,
                "applied_row_count": applied_row_count,
                "promotion_candidate_count": applied_row_count,
                "scoring_effect": "generated pack admission only",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
