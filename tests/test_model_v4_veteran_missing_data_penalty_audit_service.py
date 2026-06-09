from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_preview_engine_service import (
    V4_PREVIEW_OUTPUT_HEADER,
    V4_SOURCE_COVERAGE_HEADER,
)
from src.services.model_v4_veteran_missing_data_penalty_audit_service import (
    PHASE_5H_HEADER,
    run_veteran_missing_data_penalty_audit,
)


def test_veteran_missing_data_penalty_audit_reports_adjusted_rows(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview.csv"
    coverage_path = tmp_path / "coverage.csv"
    _write(
        preview_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [
            {
                "player": "Veteran Receiver",
                "position": "WR",
                "nfl_team": "KC",
                "lifecycle": "established_veteran",
                "truth_set_group": "fixture",
                "source_priority": "high",
                "dynasty_asset_value": "52.00",
                "value_basis": "evidence_adjusted_missing_not_zero",
                "scored_component_weight": "80",
                "missing_component_weight": "10",
                "missing_value_components": "projection",
                "confidence": "55",
                "confidence_label": "review",
                "component_scores": "{}",
                "component_contributions": "{}",
                "review_warnings": "missing_projection_data",
                "unavailable_sections": "projection",
                "review_status": "review_only",
                "formula_version": "test",
                "preview_engine_version": "test",
            }
        ],
    )
    _write(
        coverage_path,
        V4_SOURCE_COVERAGE_HEADER,
        [
            _coverage("Veteran Receiver", "production", "covered"),
            _coverage("Veteran Receiver", "projection", "missing"),
            _coverage(
                "Veteran Receiver",
                "young_player_prior",
                "not_applicable",
                source_status="not_applicable",
            ),
        ],
    )

    result = run_veteran_missing_data_penalty_audit(
        preview_outputs_path=preview_path,
        source_coverage_path=coverage_path,
        output_csv_path=tmp_path / "phase_5h.csv",
        output_md_path=tmp_path / "phase_5h.md",
    )

    assert _header(result.csv_path) == PHASE_5H_HEADER
    assert result.rows[0]["root_cause"] == "truth_set_projection_coverage_gap"
    assert "excluded from established-veteran value denominator" in result.rows[0][
        "action_taken"
    ]
    assert result.rows[0]["not_applicable_sections"] == "young_player_prior"
    assert result.summary["evidence_adjusted_rows"] == 1
    assert "No fake production" in result.markdown_path.read_text(encoding="utf-8")


def _coverage(
    player: str,
    section: str,
    coverage_status: str,
    *,
    source_status: str = "fixture",
) -> dict[str, object]:
    return {
        "player": player,
        "position": "WR",
        "section": section,
        "source_status": source_status,
        "coverage_status": coverage_status,
        "warning": "",
        "unavailable_reason": "",
    }


def _write(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
