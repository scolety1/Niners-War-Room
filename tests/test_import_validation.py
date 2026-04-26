from __future__ import annotations

from src.data.csv_schemas import REQUIRED_V1_FILES


def test_required_v1_files_include_core_csvs() -> None:
    assert "dim_players.csv" in REQUIRED_V1_FILES
    assert "fact_rosters.csv" in REQUIRED_V1_FILES
    assert "metadata_sources.csv" in REQUIRED_V1_FILES
