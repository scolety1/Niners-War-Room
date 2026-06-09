from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_named_player_review_service import (
    NAMED_PLAYER_REVIEW_HEADER,
    run_model_v4_named_player_review,
)
from src.services.model_v4_preview_engine_service import (
    V4_PREVIEW_OUTPUT_HEADER,
    V4_RECEIPT_HEADER,
)


def test_named_player_review_writes_receipt_backed_rows(tmp_path: Path) -> None:
    paths = _fixture_paths(tmp_path)

    result = run_model_v4_named_player_review(
        players=("Bijan Robinson", "Jaxon Smith-Njigba", "Missing Player"),
        preview_outputs_path=paths["preview"],
        receipts_path=paths["receipts"],
        output_csv_path=tmp_path / "named.csv",
        output_md_path=tmp_path / "named.md",
    )

    assert result.summary["review_status"] == "review_only"
    assert result.summary["matched_players"] == 2
    assert result.summary["missing_players"] == 1
    assert result.summary["decision_ready_unlocked"] is False
    assert result.summary["score_changes_applied"] is False
    assert _header(result.csv_path) == NAMED_PLAYER_REVIEW_HEADER

    bijan = result.rows[0]
    assert bijan["matched_player"] == "Bijan Robinson"
    assert bijan["overall_rank"] == 1
    assert "Production +15.00" in str(bijan["top_positive_receipt_drivers"])
    assert "No negative component contributions" in str(
        bijan["top_negative_receipt_drivers"]
    )
    assert "Age Dropoff +1.00" in str(bijan["top_negative_receipt_drivers"])

    missing = result.rows[2]
    assert missing["match_status"] == "missing_preview_output"
    assert "Missing v4 preview row" in str(missing["review_notes"])
    assert "Phase 3G Named Player Review" in result.markdown_path.read_text(
        encoding="utf-8"
    )


def test_named_player_review_flags_review_inspections(tmp_path: Path) -> None:
    paths = _fixture_paths(tmp_path)

    result = run_model_v4_named_player_review(
        players=("Bijan Robinson", "Jaxon Smith-Njigba", "Lamar Jackson", "Brock Bowers"),
        preview_outputs_path=paths["preview"],
        receipts_path=paths["receipts"],
        output_csv_path=tmp_path / "named.csv",
        output_md_path=tmp_path / "named.md",
    )

    by_inspection = {row["inspection"]: row for row in result.inspection_rows}
    assert by_inspection["RB vs WR balance"]["status"] == "review"
    assert by_inspection["QB suppression"]["status"] == "ready"
    assert by_inspection["TE suppression"]["status"] == "ready"
    assert by_inspection["Market and league-rank separation"]["status"] == "ready"


def test_named_player_review_catches_forbidden_private_context(
    tmp_path: Path,
) -> None:
    paths = _fixture_paths(tmp_path, include_market_receipt=True)

    result = run_model_v4_named_player_review(
        players=("Bijan Robinson",),
        preview_outputs_path=paths["preview"],
        receipts_path=paths["receipts"],
        output_csv_path=tmp_path / "named.csv",
        output_md_path=tmp_path / "named.md",
    )

    separation = next(
        row
        for row in result.inspection_rows
        if row["inspection"] == "Market and league-rank separation"
    )
    assert separation["status"] == "review"
    assert "Forbidden context token" in str(separation["finding"])


def _fixture_paths(
    tmp_path: Path,
    *,
    include_market_receipt: bool = False,
) -> dict[str, Path]:
    preview = tmp_path / "v4_preview_outputs.csv"
    receipts = tmp_path / "v4_receipt_rows.csv"
    _write(
        preview,
        V4_PREVIEW_OUTPUT_HEADER,
        [
            _preview_row("Bijan Robinson", "RB", "ATL", 70, "usable"),
            _preview_row(
                "Jaxon Smith-Njigba",
                "WR",
                "SEA",
                48,
                "usable",
                lifecycle="year_three_nfl_bridge",
                warnings="route_data_unavailable_free_public",
            ),
            _preview_row("Lamar Jackson", "QB", "BAL", 55, "usable"),
            _preview_row("Brock Bowers", "TE", "LV", 52, "usable"),
        ],
    )
    receipt_rows = [
        _receipt_row("Bijan Robinson", "RB", "production", 15),
        _receipt_row("Bijan Robinson", "RB", "age_dropoff", 1, warning="age_visible"),
        _receipt_row("Jaxon Smith-Njigba", "WR", "production", 8),
        _receipt_row(
            "Jaxon Smith-Njigba",
            "WR",
            "snap_proxy_role",
            0,
            warning="route_data_unavailable_free_public",
        ),
        _receipt_row("Lamar Jackson", "QB", "production", 12),
        _receipt_row("Brock Bowers", "TE", "production", 10),
    ]
    if include_market_receipt:
        receipt_rows.append(
            _receipt_row("Bijan Robinson", "RB", "market_liquidity", 2)
        )
    _write(receipts, V4_RECEIPT_HEADER, receipt_rows)
    return {"preview": preview, "receipts": receipts}


def _preview_row(
    player: str,
    position: str,
    team: str,
    value: float,
    confidence_label: str,
    *,
    lifecycle: str = "established_veteran",
    warnings: str = "",
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "nfl_team": team,
        "lifecycle": lifecycle,
        "truth_set_group": "fixture",
        "source_priority": "critical",
        "dynasty_asset_value": value,
        "confidence": 80,
        "confidence_label": confidence_label,
        "component_scores": '{"production": 80, "age_dropoff": 50}',
        "component_contributions": '{"production": 15, "age_dropoff": 1}',
        "review_warnings": warnings,
        "unavailable_sections": "",
        "review_status": "review_only",
        "formula_version": "test",
        "preview_engine_version": "test",
    }


def _receipt_row(
    player: str,
    position: str,
    component: str,
    contribution: float,
    *,
    warning: str = "",
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "component": component,
        "raw_fields_used": "",
        "raw_values": "{}",
        "normalized_score": 50,
        "source_status": "fixture",
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
