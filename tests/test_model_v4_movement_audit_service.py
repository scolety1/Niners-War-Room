from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.model_v4_movement_audit_service import (
    MOVEMENT_HEADER,
    run_model_v4_movement_audit,
)
from src.services.model_v4_preview_engine_service import V4_PREVIEW_OUTPUT_HEADER


def test_model_v4_movement_audit_classifies_projection_repairs(
    tmp_path: Path,
) -> None:
    phase4_path = tmp_path / "phase4.csv"
    current_path = tmp_path / "current.csv"
    _write(
        phase4_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [
            _row(
                "Veteran RB",
                "RB",
                50,
                {"production": 60, "projection": 0},
                warnings="missing_projection_data",
                truth_set_group="elite_rb_control",
            ),
            _row("Stable WR", "WR", 45, {"production": 50, "projection": 50}),
        ],
    )
    current_header = (
        *V4_PREVIEW_OUTPUT_HEADER[:7],
        "value_basis",
        "scored_component_weight",
        "missing_component_weight",
        "missing_value_components",
        *V4_PREVIEW_OUTPUT_HEADER[7:],
    )
    _write(
        current_path,
        current_header,
        [
            _row(
                "Veteran RB",
                "RB",
                58,
                {"production": 60, "projection": 0},
                warnings="missing_projection_data",
                truth_set_group="elite_rb_control",
                value_basis="evidence_adjusted_missing_not_zero",
                missing_value_components="projection",
            ),
            _row("Stable WR", "WR", 45.2, {"production": 50, "projection": 50}),
        ],
    )

    result = run_model_v4_movement_audit(
        phase4_preview_path=phase4_path,
        current_preview_path=current_path,
        output_csv_path=tmp_path / "movement.csv",
        output_md_path=tmp_path / "movement.md",
    )

    assert _header(result.csv_path) == MOVEMENT_HEADER
    veteran = next(row for row in result.rows if row["player"] == "Veteran RB")
    assert veteran["movement_magnitude"] == "large"
    assert veteran["movement_cause"] == "normalization repair"
    assert veteran["audit_groups"] == "elite_rb"
    assert result.summary["meaningful_movement_rows"] == 1
    assert "Phase 5 Movement Audit" in result.markdown_path.read_text(
        encoding="utf-8"
    )


def test_model_v4_movement_audit_detects_projection_component_delta(
    tmp_path: Path,
) -> None:
    phase4_path = tmp_path / "phase4.csv"
    current_path = tmp_path / "current.csv"
    _write(
        phase4_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [
            _row("Receiver", "WR", 44, {"production": 40, "projection": 20}),
        ],
    )
    _write(
        current_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [
            _row("Receiver", "WR", 48, {"production": 40, "projection": 42}),
        ],
    )

    result = run_model_v4_movement_audit(
        phase4_preview_path=phase4_path,
        current_preview_path=current_path,
        output_csv_path=tmp_path / "movement.csv",
        output_md_path=tmp_path / "movement.md",
    )

    assert result.rows[0]["movement_cause"] == "projection/first-down estimate repair"
    assert result.rows[0]["projection_delta"] == "22.00"


def _row(
    player: str,
    position: str,
    value: float,
    component_scores: dict[str, float],
    *,
    warnings: str = "",
    truth_set_group: str = "fixture",
    value_basis: str = "",
    missing_value_components: str = "",
) -> dict[str, object]:
    base = {
        "player": player,
        "position": position,
        "nfl_team": "TST",
        "lifecycle": "established_veteran",
        "truth_set_group": truth_set_group,
        "source_priority": "high",
        "dynasty_asset_value": value,
        "confidence": 70,
        "confidence_label": "review",
        "component_scores": json.dumps(component_scores),
        "component_contributions": "{}",
        "review_warnings": warnings,
        "unavailable_sections": "",
        "review_status": "review_only",
        "formula_version": "test",
        "preview_engine_version": "test",
    }
    if value_basis or missing_value_components:
        base.update(
            {
                "value_basis": value_basis,
                "scored_component_weight": "80",
                "missing_component_weight": "10",
                "missing_value_components": missing_value_components,
            }
        )
    return base


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
