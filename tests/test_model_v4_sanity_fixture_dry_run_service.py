from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_sanity_fixture_dry_run_service import (
    DRY_RUN_HEADER,
    load_v4_preview_players,
    run_model_v4_sanity_fixture_dry_run,
)
from src.services.model_v4_sanity_fixture_runner_service import FIXTURE_CONTRACT_HEADER


def test_sanity_fixture_dry_run_marks_ordering_disagreement_review(
    tmp_path: Path,
) -> None:
    paths = _fixture_paths(tmp_path)
    _write_fixture(
        paths["fixtures"],
        fixture_id="jsn_vs_tee",
        fixture_type="expected_ordering",
        players="Jaxon Smith-Njigba|Tee Higgins",
        expected_behavior="JSN should generally rank above Tee.",
    )

    result = run_model_v4_sanity_fixture_dry_run(
        fixture_contract_path=paths["fixtures"],
        preview_outputs_path=paths["preview"],
        receipts_path=paths["receipts"],
        output_csv_path=tmp_path / "dry.csv",
        output_md_path=tmp_path / "dry.md",
    )

    assert result.summary["review_status"] == "review_only"
    assert result.summary["review_count"] == 1
    row = result.rows[0]
    assert row["status"] == "review"
    assert row["disagreement_classification"] in {"data gap", "formula issue"}
    assert "Tee Higgins is above Jaxon Smith-Njigba" in row["likely_cause"]
    assert _header(result.csv_path) == DRY_RUN_HEADER
    assert "Fixture failures are review findings" in result.markdown_path.read_text(
        encoding="utf-8"
    )


def test_sanity_fixture_dry_run_reports_ready_when_fixture_is_met(
    tmp_path: Path,
) -> None:
    paths = _fixture_paths(tmp_path)
    _write_fixture(
        paths["fixtures"],
        fixture_id="rb_bijan_rb1_002",
        fixture_type="expected_review_if_disagrees",
        players="Bijan Robinson",
        expected_behavior="Bijan should be RB1.",
    )

    result = run_model_v4_sanity_fixture_dry_run(
        fixture_contract_path=paths["fixtures"],
        preview_outputs_path=paths["preview"],
        receipts_path=paths["receipts"],
        output_csv_path=tmp_path / "dry.csv",
        output_md_path=tmp_path / "dry.md",
    )

    assert result.summary["ready_count"] == 1
    assert result.rows[0]["status"] == "ready"
    assert "Bijan is RB1" in result.rows[0]["actual_behavior"]
    assert result.summary["decision_ready_unlocked"] is False
    assert result.summary["auto_fixes_applied"] is False


def test_sanity_fixture_dry_run_blocks_missing_preview_players(
    tmp_path: Path,
) -> None:
    paths = _fixture_paths(tmp_path)
    _write_fixture(
        paths["fixtures"],
        fixture_id="missing",
        fixture_type="expected_tier",
        players="Missing Player",
        expected_behavior="Missing player should be evaluated.",
    )

    result = run_model_v4_sanity_fixture_dry_run(
        fixture_contract_path=paths["fixtures"],
        preview_outputs_path=paths["preview"],
        receipts_path=paths["receipts"],
        output_csv_path=tmp_path / "dry.csv",
        output_md_path=tmp_path / "dry.md",
    )

    assert result.summary["blocked_count"] == 1
    assert result.rows[0]["status"] == "blocked"
    assert result.rows[0]["disagreement_classification"] == "data gap"
    assert result.rows[0]["missing_players"] == "Missing Player"


def test_sanity_fixture_dry_run_detects_lifecycle_mismatch(tmp_path: Path) -> None:
    paths = _fixture_paths(tmp_path)
    _write_fixture(
        paths["fixtures"],
        fixture_id="rookie_lane",
        fixture_type="expected_lifecycle",
        players="Veteran Wideout",
        expected_behavior="Incoming rookies belong in incoming_rookie lifecycle.",
    )

    result = run_model_v4_sanity_fixture_dry_run(
        fixture_contract_path=paths["fixtures"],
        preview_outputs_path=paths["preview"],
        receipts_path=paths["receipts"],
        output_csv_path=tmp_path / "dry.csv",
        output_md_path=tmp_path / "dry.md",
    )

    assert result.rows[0]["status"] == "review"
    assert result.rows[0]["disagreement_classification"] == "lifecycle issue"
    assert "Lifecycle mismatch" in result.rows[0]["likely_cause"]


def test_load_v4_preview_players_assigns_overall_and_position_ranks(
    tmp_path: Path,
) -> None:
    paths = _fixture_paths(tmp_path)

    players = load_v4_preview_players(paths["preview"])

    assert players["bijan robinson"].overall_rank == 1
    assert players["bijan robinson"].position_rank == 1
    assert players["tee higgins"].overall_rank < players["jaxon smith njigba"].overall_rank


def _fixture_paths(tmp_path: Path) -> dict[str, Path]:
    fixtures = tmp_path / "fixtures.csv"
    preview = tmp_path / "v4_preview_outputs.csv"
    receipts = tmp_path / "v4_receipts.csv"
    _write(
        preview,
        [
            _preview_row("Bijan Robinson", "RB", 80, "young_nfl_bridge"),
            _preview_row("Tee Higgins", "WR", 70, "established_veteran"),
            _preview_row(
                "Jaxon Smith-Njigba",
                "WR",
                60,
                "year_three_nfl_bridge",
                warnings="missing_route_data",
            ),
            _preview_row("Veteran Wideout", "WR", 55, "established_veteran"),
        ],
    )
    receipt_rows = []
    for player in ("Bijan Robinson", "Tee Higgins", "Jaxon Smith-Njigba", "Veteran Wideout"):
        for component in (
            "production",
            "first_down_scoring_fit",
            "usage_opportunity",
            "snap_proxy_role",
            "projection",
            "age_dropoff",
            "young_player_prior",
            "confidence",
        ):
            receipt_rows.append(
                {
                    "player": player,
                    "position": "RB" if player == "Bijan Robinson" else "WR",
                    "component": component,
                    "raw_fields_used": "",
                    "raw_values": "{}",
                    "normalized_score": "50",
                    "source_status": "fixture",
                    "contribution": "1",
                    "weight": "1",
                    "warning": "",
                    "unavailable_reason": "",
                    "review_only": "True",
                }
            )
    _write(receipts, receipt_rows)
    return {"fixtures": fixtures, "preview": preview, "receipts": receipts}


def _write_fixture(
    path: Path,
    *,
    fixture_id: str,
    fixture_type: str,
    players: str,
    expected_behavior: str,
) -> None:
    _write(
        path,
        [
            {
                "fixture_id": fixture_id,
                "fixture_name": fixture_id,
                "fixture_type": fixture_type,
                "players": players,
                "expected_behavior": expected_behavior,
                "review_severity": "high",
                "receipt_requirement": "Show receipts.",
                "football_logic": "Fixture logic.",
            }
        ],
        fieldnames=FIXTURE_CONTRACT_HEADER,
    )


def _preview_row(
    player: str,
    position: str,
    value: float,
    lifecycle: str,
    *,
    warnings: str = "",
) -> dict[str, object]:
    return {
        "player": player,
        "position": position,
        "nfl_team": "TST",
        "lifecycle": lifecycle,
        "truth_set_group": "fixture",
        "source_priority": "critical",
        "dynasty_asset_value": value,
        "confidence": "80",
        "confidence_label": "usable",
        "component_scores": "{}",
        "component_contributions": "{}",
        "review_warnings": warnings,
        "unavailable_sections": "",
        "review_status": "review_only",
        "formula_version": "test",
        "preview_engine_version": "test",
    }


def _write(
    path: Path,
    rows: list[dict[str, object]],
    *,
    fieldnames: tuple[str, ...] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames or tuple(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
