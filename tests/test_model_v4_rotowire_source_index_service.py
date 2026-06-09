from pathlib import Path

from src.services.model_v4_rotowire_source_index_service import (
    build_rotowire_schema_catalog,
    build_rotowire_source_index,
    write_rotowire_source_index,
)


def test_rotowire_source_index_catalogs_manual_exports() -> None:
    result = build_rotowire_source_index()

    assert len(result.rows) >= 100
    assert result.summary["file_count"] == len(result.rows)
    assert result.summary["clean_file_count"] >= 90
    assert result.summary["active_file_count"] == sum(
        1 for row in result.rows if row["active_for_intake"]
    )
    assert result.summary["active_file_count"] >= 103

    by_path = {row["relative_path"]: row for row in result.rows}
    duplicate = by_path[
        "2021/passing/rotowire-passing-basic-stats (3).csv"
    ]
    assert duplicate["is_canonical_file"] is False
    assert duplicate["active_for_intake"] is False
    assert duplicate["inactive_reason"] == "duplicate_raw_export_preserved_but_not_read"

    canonical = by_path["2021/passing/basic.csv"]
    assert canonical["is_canonical_file"] is True
    assert canonical["active_for_intake"] is True

    projection = by_path[
        "2026/projections/rotowire_full_season_raw_stat_projections.csv"
    ]
    assert projection["allowed_use"] == "review_only"
    assert projection["model_lane"] == "projection_context"
    assert projection["validation_status"] == "clean"
    assert projection["data_rows"] == 719

    injury = by_path["2026/injuries/wr_injury_report.csv"]
    assert injury["allowed_use"] == "context_only"
    assert "absence is not healthy evidence" in str(injury["notes"])

    market = by_path["2026/market_context/rotowire_early_adp_all.csv"]
    assert market["model_lane"] == "market_context"
    assert market["allowed_use"] == "context_only"

    receiving_first_downs = by_path["2025/first_downs/receiving_first_downs.csv"]
    assert receiving_first_downs["model_lane"] == "direct_first_down_scoring_evidence"
    assert receiving_first_downs["allowed_use"] == "scoring_allowed"

    kick_returns = by_path["2025/returns/kick_returns.csv"]
    assert kick_returns["model_lane"] == "direct_return_scoring_evidence"
    assert kick_returns["allowed_use"] == "scoring_allowed"

    validation_file = by_path["first_downs_upload_validation.csv"]
    assert validation_file["active_for_intake"] is False
    assert validation_file["inactive_reason"] == "unclassified_not_active_for_intake"


def test_rotowire_source_index_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_source_index()
    paths = write_rotowire_source_index(tmp_path, result)

    assert paths["index"].exists()
    assert paths["summary"].exists()
    assert paths["schema"].exists()
    assert "rotowire_full_season_raw_stat_projections" in paths["index"].read_text(
        encoding="utf-8"
    )


def test_rotowire_schema_catalog_flags_duplicate_headers_and_stability() -> None:
    result = build_rotowire_source_index()
    catalog = build_rotowire_schema_catalog(index_rows=result.rows)
    by_key = {
        (row["source_family"], row["source_detail"]): row
        for row in catalog
    }

    receiving_basic = by_key[("receiving", "basic")]
    assert receiving_basic["schema_status"] == "stable"
    assert receiving_basic["file_count"] == 5
    assert receiving_basic["seasons"] == "2021|2022|2023|2024|2025"
    assert receiving_basic["duplicate_header_names"] == ""

    projection = by_key[("projections", "rotowire_full_season_raw_stat_projections")]
    assert projection["schema_status"] == "stable"
    assert "YDS" in str(projection["duplicate_header_names"])
