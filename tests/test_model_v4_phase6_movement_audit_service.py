from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.model_v4_phase6_movement_audit_service import (
    PHASE_6_MOVEMENT_HEADER,
    MovementCauseContext,
    classify_phase6_movement_cause,
    run_model_v4_phase6_movement_audit,
)
from src.services.model_v4_preview_engine_service import V4_PREVIEW_OUTPUT_HEADER


def test_phase6_movement_audit_classifies_formula_patch_causes(
    tmp_path: Path,
) -> None:
    phase5_path = tmp_path / "phase5.csv"
    phase6_path = tmp_path / "phase6.csv"
    _write(
        phase5_path,
        [
            _row(
                "Receiver",
                "WR",
                50,
                {"production": 70, "usage_opportunity": 60, "projection": 50},
                {"production": 18.2, "usage_opportunity": 14.4, "projection": 5},
            ),
            _row("Quarterback", "QB", 55, {"production": 80}, {"production": 19.2}),
            _row("Tight End", "TE", 48, {"production": 65}, {"production": 14.3}),
        ],
    )
    _write(
        phase6_path,
        [
            _row(
                "Receiver",
                "WR",
                53,
                {"production": 70, "usage_opportunity": 60, "projection": 50},
                {"production": 15.4, "usage_opportunity": 12, "projection": 9.5},
            ),
            _row(
                "Quarterback",
                "QB",
                62,
                {"production": 80, "position_scarcity_suppression": 40},
                {"production": 19.2, "position_scarcity_suppression": 7.2},
            ),
            _row(
                "Tight End",
                "TE",
                52,
                {"production": 65, "no_premium_suppression": 35},
                {"production": 14.3, "no_premium_suppression": 3.5},
            ),
        ],
    )

    result = run_model_v4_phase6_movement_audit(
        phase5_preview_path=phase5_path,
        current_preview_path=phase6_path,
        output_csv_path=tmp_path / "phase6_movement.csv",
        output_md_path=tmp_path / "phase6_movement.md",
    )

    causes = {row["player"]: row["movement_cause"] for row in result.rows}
    assert causes["Receiver"] == "WR production/projection weighting patch"
    assert causes["Quarterback"] == "QB suppression patch"
    assert causes["Tight End"] == "TE suppression patch"
    assert _header(result.csv_path) == PHASE_6_MOVEMENT_HEADER
    assert "Phase 6 Movement Audit" in result.markdown_path.read_text(encoding="utf-8")


def test_phase6_movement_classifier_detects_missing_data_penalty() -> None:
    row = _row(
        "Veteran",
        "RB",
        50,
        {"production": 50},
        {"production": 12},
        value_basis="evidence_adjusted_missing_not_zero",
        missing_value_components="projection",
    )
    current = dict(row)
    current["dynasty_asset_value"] = "48"

    cause = classify_phase6_movement_cause(
        MovementCauseContext(
            previous=row,
            current=current,
            score_deltas={component: 0.0 for component in _COMPONENTS},
            contribution_deltas={component: 0.0 for component in _COMPONENTS},
            value_delta=-2.0,
            rank_delta=0,
            warning_delta={"added": (), "removed": ()},
        )
    )

    assert cause == "confidence/missing-data patch"


_COMPONENTS = (
    "production",
    "first_down_scoring_fit",
    "usage_opportunity",
    "snap_proxy_role",
    "projection",
    "age_dropoff",
    "young_player_prior",
    "position_scarcity_suppression",
    "no_premium_suppression",
)


def _row(
    player: str,
    position: str,
    value: float,
    component_scores: dict[str, float],
    component_contributions: dict[str, float],
    *,
    value_basis: str = "weighted_sum",
    missing_value_components: str = "",
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "nfl_team": "TST",
        "lifecycle": "established_veteran",
        "truth_set_group": "fixture",
        "source_priority": "high",
        "dynasty_asset_value": value,
        "value_basis": value_basis,
        "scored_component_weight": "100",
        "missing_component_weight": "0",
        "missing_value_components": missing_value_components,
        "confidence": 75,
        "confidence_label": "review",
        "component_scores": json.dumps(component_scores),
        "component_contributions": json.dumps(component_contributions),
        "review_warnings": "",
        "unavailable_sections": "",
        "review_status": "review_only",
        "formula_version": "test",
        "preview_engine_version": "test",
    }


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=V4_PREVIEW_OUTPUT_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
