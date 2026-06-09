from pathlib import Path

from src.services.model_v4_first_down_canonicalization_service import (
    build_canonical_first_downs,
    write_canonical_first_down_outputs,
)


def test_first_down_canonicalization_cleans_known_export_issues() -> None:
    result = build_canonical_first_downs()
    validation = {
        (row["season"], row["stat_family"]): row for row in result.validation_rows
    }

    assert len(result.rushing_rows) == 350
    assert len(result.receiving_rows) == 575

    rushing_2024 = validation[("2024", "rushing")]
    assert rushing_2024["header_present"] is False
    assert rushing_2024["header_inferred"] is True
    assert rushing_2024["clean_rows"] == 125

    receiving_2024 = validation[("2024", "receiving")]
    assert receiving_2024["repeated_header_rows_removed"] == 1
    assert receiving_2024["clean_rows"] == 275

    receiving_2025 = validation[("2025", "receiving")]
    assert receiving_2025["exact_duplicate_rows_removed"] == 50
    assert receiving_2025["clean_rows"] == 300


def test_first_down_canonicalization_marks_imported_real_data_and_safe_joins() -> None:
    result = build_canonical_first_downs()

    jsn = next(
        row
        for row in result.receiving_rows
        if row["season"] == "2025" and row["player_name"] == "Jaxon Smith-Njigba"
    )
    assert jsn["source_status"] == "imported_real_data"
    assert jsn["receiving_first_downs"] == 79
    assert jsn["nfl_team"] == "SEA"
    assert jsn["position"] == "WR"
    assert jsn["join_status"] == "matched"

    taylor = next(
        row
        for row in result.rushing_rows
        if row["season"] == "2025" and row["player_name"] == "Jonathan Taylor"
    )
    assert taylor["source_status"] == "imported_real_data"
    assert taylor["rushing_first_downs"] == 84
    assert taylor["join_status"] == "matched"

    audric = next(
        row
        for row in result.rushing_rows
        if row["season"] == "2025" and row["player_name"] == "Audric Estimé"
    )
    assert audric["source_status"] == "imported_real_data"
    assert audric["join_status"] == "missing_join"
    assert "missing_rotowire_identity_join" in str(audric["cleanup_warnings"])
    assert result.summary["admitted_rushing_rows"] > 0
    assert result.summary["admitted_receiving_rows"] > 0


def test_first_down_canonicalization_produces_receipts_and_coverage() -> None:
    result = build_canonical_first_downs()

    assert len(result.receipt_rows) == len(result.rushing_rows) + len(result.receiving_rows)
    assert len(result.coverage_rows) == len(result.receipt_rows)

    receipt = next(
        row
        for row in result.receipt_rows
        if row["season"] == "2025"
        and row["player_name"] == "Jaxon Smith-Njigba"
        and row["stat_family"] == "receiving"
    )
    assert receipt["source_status"] == "imported_real_data"
    assert "receiving_first_downs" in str(receipt["normalized_fields_json"])

    coverage = next(
        row
        for row in result.coverage_rows
        if row["season"] == "2025"
        and row["player_name"] == "Jaxon Smith-Njigba"
        and row["stat_family"] == "receiving"
    )
    assert coverage["has_first_down_evidence"] is True
    assert coverage["coverage_status"] == "covered"


def test_first_down_canonicalization_writes_outputs(tmp_path: Path) -> None:
    result = build_canonical_first_downs()
    paths = write_canonical_first_down_outputs(tmp_path, result)

    assert paths["rushing"].exists()
    assert paths["receiving"].exists()
    assert paths["admitted_rushing"].exists()
    assert paths["admitted_receiving"].exists()
    assert paths["validation"].exists()
    assert paths["receipts"].exists()
    assert paths["coverage"].exists()
    assert "imported_real_data" in paths["receiving"].read_text(encoding="utf-8")
    assert "missing_join" not in paths["admitted_receiving"].read_text(encoding="utf-8")
