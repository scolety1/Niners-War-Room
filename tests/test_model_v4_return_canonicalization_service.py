from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_return_canonicalization_service import (
    build_canonical_returns,
    write_canonical_return_outputs,
)


def test_return_canonicalization_cleans_known_export_issues() -> None:
    result = build_canonical_returns()
    validation = {
        (row["season"], row["stat_family"]): row for row in result.validation_rows
    }

    assert len(result.canonical_rows) == 302

    kick_2025 = validation[("2025", "kick")]
    assert kick_2025["header_present"] is False
    assert kick_2025["header_inferred"] is True
    assert kick_2025["shifted_header_inferred"] is True
    assert kick_2025["clean_rows"] == 125
    assert "shifted_header_expected_player_header_inferred" in str(kick_2025["notes"])

    punt_2024 = validation[("2024", "punt")]
    assert punt_2024["repeated_header_rows_removed"] == 1
    assert punt_2024["clean_rows"] == 75


def test_return_canonicalization_aggregates_kick_and_punt_scoring() -> None:
    result = build_canonical_returns()

    chimere = next(
        row
        for row in result.canonical_rows
        if row["season"] == "2025" and row["player_name"] == "Chimere Dike"
    )
    assert chimere["source_status"] == "imported_real_data"
    assert chimere["kick_return_yards"] == 1588
    assert chimere["punt_return_yards"] == 398
    assert chimere["return_yards_total"] == 1986
    assert chimere["return_td_total"] == 2
    assert chimere["return_lve_points"] == 74.2
    assert (
        chimere["scoring_role"]
        == "small_direct_return_scoring_evidence_not_talent_signal"
    )
    assert result.summary["admitted_return_rows"] > 0


def test_return_canonicalization_produces_receipts_and_coverage() -> None:
    result = build_canonical_returns()

    assert len(result.receipt_rows) == len(result.canonical_rows)
    assert len(result.coverage_rows) == len(result.canonical_rows)

    receipt = next(
        row
        for row in result.receipt_rows
        if row["season"] == "2025" and row["player_name"] == "Chimere Dike"
    )
    assert receipt["source_status"] == "imported_real_data"
    assert receipt["component"] == "return_scoring"
    assert "return_lve_points" in str(receipt["normalized_fields_json"])
    assert str(LVE_SCORING["return_yard"]) in str(receipt["scoring_constants_json"])

    coverage = next(
        row
        for row in result.coverage_rows
        if row["season"] == "2025" and row["player_name"] == "Chimere Dike"
    )
    assert coverage["has_return_evidence"] is True
    assert coverage["source_status"] == "imported_real_data"


def test_return_canonicalization_writes_outputs(tmp_path: Path) -> None:
    result = build_canonical_returns()
    paths = write_canonical_return_outputs(tmp_path, result)

    assert paths["canonical"].exists()
    assert paths["admitted"].exists()
    assert paths["validation"].exists()
    assert paths["receipts"].exists()
    assert paths["coverage"].exists()
    assert "small_direct_return_scoring_evidence" in paths["canonical"].read_text(
        encoding="utf-8"
    )
    assert "ambiguous_join" not in paths["admitted"].read_text(encoding="utf-8")
