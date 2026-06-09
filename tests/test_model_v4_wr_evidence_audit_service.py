from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_preview_engine_service import (
    V4_PREVIEW_OUTPUT_HEADER,
    V4_RECEIPT_HEADER,
)
from src.services.model_v4_wr_evidence_audit_service import (
    WR_EVIDENCE_AUDIT_HEADER,
    run_model_v4_wr_evidence_audit,
)


def test_wr_evidence_audit_writes_component_comparison_rows(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.csv"
    receipts_path = tmp_path / "receipts.csv"
    _write(
        preview_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [
            _preview_row(
                "Puka Nacua",
                72,
                warnings="snap_share_proxy_only_not_route_participation|missing_first_down_projection",
            ),
            _preview_row(
                "Jaxon Smith-Njigba",
                68,
                lifecycle="year_three_nfl_bridge",
                warnings="young_player_prior_review_only",
            ),
            _preview_row("Tee Higgins", 55),
        ],
    )
    _write(
        receipts_path,
        V4_RECEIPT_HEADER,
        [
            _receipt_row("Puka Nacua", "production", 80, 19.2),
            _receipt_row("Puka Nacua", "first_down_scoring_fit", 60, 8.4),
            _receipt_row("Puka Nacua", "usage_opportunity", 70, 16.8),
            _receipt_row(
                "Puka Nacua",
                "snap_proxy_role",
                75,
                6,
                warning="snap_share_proxy_only_not_route_participation",
            ),
            _receipt_row(
                "Puka Nacua",
                "projection",
                80,
                8,
                warning="missing_first_down_projection",
            ),
            _receipt_row("Puka Nacua", "age_dropoff", 90, 9),
            _receipt_row("Puka Nacua", "young_player_prior", 0, 0),
            _receipt_row("Jaxon Smith-Njigba", "production", 75, 18),
            _receipt_row("Jaxon Smith-Njigba", "usage_opportunity", 65, 15.6),
            _receipt_row(
                "Jaxon Smith-Njigba",
                "young_player_prior",
                50,
                0.2,
                warning="young_player_prior_review_only",
            ),
            _receipt_row("Tee Higgins", "production", 50, 12),
        ],
    )

    result = run_model_v4_wr_evidence_audit(
        players=("Puka Nacua", "Jaxon Smith-Njigba", "Missing WR"),
        preview_outputs_path=preview_path,
        receipts_path=receipts_path,
        output_csv_path=tmp_path / "wr.csv",
        output_md_path=tmp_path / "wr.md",
    )

    assert _header(result.csv_path) == WR_EVIDENCE_AUDIT_HEADER
    puka = result.rows[0]
    assert puka["matched_player"] == "Puka Nacua"
    assert puka["overall_preview_rank"] == 1
    assert puka["wr_preview_rank"] == 1
    assert puka["production_score"] == "80.00"
    assert puka["production_contribution"] == "19.20"
    assert puka["route_data_unavailable"] is True
    assert puka["first_down_projection_gap"] is True

    jsn = result.rows[1]
    assert jsn["young_bridge_review"] is True
    assert result.rows[2]["match_status"] == "missing_preview_output"
    assert result.summary["score_changes_applied"] is False
    assert "Phase 4 WR Evidence Audit" in result.markdown_path.read_text(
        encoding="utf-8"
    )


def test_wr_evidence_audit_flags_candidate_formula_imbalance(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview.csv"
    receipts_path = tmp_path / "receipts.csv"
    _write(
        preview_path,
        V4_PREVIEW_OUTPUT_HEADER,
        [_preview_row("CeeDee Lamb", 58, confidence_label="usable")],
    )
    _write(
        receipts_path,
        V4_RECEIPT_HEADER,
        [
            _receipt_row("CeeDee Lamb", "production", 70, 16.8),
            _receipt_row("CeeDee Lamb", "usage_opportunity", 70, 16.8),
            _receipt_row("CeeDee Lamb", "projection", 60, 6.0),
            _receipt_row("CeeDee Lamb", "first_down_scoring_fit", 60, 8.4),
        ],
    )

    result = run_model_v4_wr_evidence_audit(
        players=("CeeDee Lamb",),
        preview_outputs_path=preview_path,
        receipts_path=receipts_path,
        output_csv_path=tmp_path / "wr.csv",
        output_md_path=tmp_path / "wr.md",
    )

    assert result.rows[0]["true_formula_imbalance_review"] is True
    assert result.summary["true_formula_imbalance_review_rows"] == 1


def _preview_row(
    player: str,
    value: float,
    *,
    lifecycle: str = "established_veteran",
    warnings: str = "",
    confidence_label: str = "usable",
) -> dict[str, object]:
    return {
        "player": player,
        "position": "WR",
        "nfl_team": "TST",
        "lifecycle": lifecycle,
        "truth_set_group": "fixture",
        "source_priority": "critical",
        "dynasty_asset_value": value,
        "confidence": 80,
        "confidence_label": confidence_label,
        "component_scores": "{}",
        "component_contributions": "{}",
        "review_warnings": warnings,
        "unavailable_sections": "",
        "review_status": "review_only",
        "formula_version": "test",
        "preview_engine_version": "test",
    }


def _receipt_row(
    player: str,
    component: str,
    normalized_score: float,
    contribution: float,
    *,
    warning: str = "",
    source_status: str = "imported_real_data",
) -> dict[str, object]:
    return {
        "player": player,
        "position": "WR",
        "component": component,
        "raw_fields_used": "fixture",
        "raw_values": "{}",
        "normalized_score": normalized_score,
        "source_status": source_status,
        "contribution": contribution,
        "weight": 1,
        "warning": warning,
        "unavailable_reason": "",
        "review_only": True,
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
