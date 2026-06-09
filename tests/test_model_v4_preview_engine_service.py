from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_preview_engine_service import (
    DEFAULT_V3_REPORT_ROOT,
    V4_COMPONENT_HEADER,
    V4_PREVIEW_OUTPUT_HEADER,
    V4_RECEIPT_HEADER,
    V4_SOURCE_COVERAGE_HEADER,
    V4_WARNING_HEADER,
    build_model_v4_preview,
)


def test_model_v4_preview_defaults_to_v4_scoped_source_reports() -> None:
    assert DEFAULT_V3_REPORT_ROOT == Path("local_exports/model_v4/source_reports")


def test_model_v4_preview_engine_writes_review_only_artifacts(tmp_path: Path) -> None:
    paths = _fixture_paths(tmp_path)

    result = build_model_v4_preview(
        truth_set_path=paths["truth"],
        v3_report_root=paths["reports"],
        projection_path=paths["projection"],
        young_prior_path=paths["young"],
        v3_2_root=paths["v3_2"],
        output_root=tmp_path / "out",
        preview_id="preview_test",
        computed_at="2026-05-16T00:00:00Z",
    )

    assert result.summary["review_status"] == "review_only"
    assert result.summary["active_rankings_overwritten"] is False
    assert result.summary["decision_ready_unlocked"] is False
    assert result.summary["preview_output_rows"] == 2
    assert result.summary["component_rows"] == 16
    assert result.summary["receipt_rows"] == 16
    assert result.summary["source_coverage_rows"] == 16

    outputs = _read(result.preview_outputs_path)
    assert _header(result.preview_outputs_path) == V4_PREVIEW_OUTPUT_HEADER
    assert outputs[0]["player"] == "Runner One"
    assert outputs[0]["review_status"] == "review_only"
    assert float(outputs[0]["dynasty_asset_value"]) > 0
    assert outputs[0]["value_basis"] == "weighted_sum"
    assert "missing_" in outputs[1]["review_warnings"]

    assert _header(result.normalized_components_path) == V4_COMPONENT_HEADER
    assert _header(result.receipts_path) == V4_RECEIPT_HEADER
    assert _header(result.source_coverage_path) == V4_SOURCE_COVERAGE_HEADER
    assert _header(result.warnings_path) == V4_WARNING_HEADER


def test_model_v4_preview_engine_keeps_active_rankings_unchanged(tmp_path: Path) -> None:
    paths = _fixture_paths(tmp_path)
    active_like_file = Path(paths["v3_2"]) / "model_outputs_scored_non_k.csv"
    before = active_like_file.read_text(encoding="utf-8")

    build_model_v4_preview(
        truth_set_path=paths["truth"],
        v3_report_root=paths["reports"],
        projection_path=paths["projection"],
        young_prior_path=paths["young"],
        v3_2_root=paths["v3_2"],
        output_root=tmp_path / "out",
        preview_id="preview_test",
        computed_at="2026-05-16T00:00:00Z",
    )

    assert active_like_file.read_text(encoding="utf-8") == before
    assert not (Path(paths["v3_2"]) / "v4_preview_outputs.csv").exists()


def test_model_v4_preview_engine_exposes_receipts_coverage_and_warnings(
    tmp_path: Path,
) -> None:
    paths = _fixture_paths(tmp_path)

    result = build_model_v4_preview(
        truth_set_path=paths["truth"],
        v3_report_root=paths["reports"],
        projection_path=paths["projection"],
        young_prior_path=paths["young"],
        v3_2_root=paths["v3_2"],
        output_root=tmp_path / "out",
        preview_id="preview_test",
        computed_at="2026-05-16T00:00:00Z",
    )

    receipts = _read(result.receipts_path)
    runner_production = next(
        row
        for row in receipts
        if row["player"] == "Runner One" and row["component"] == "production"
    )
    assert runner_production["source_status"] == "imported_real_data"
    assert "lve_points_no_first_downs" in runner_production["raw_values"]
    assert "rushing_attempts" in runner_production["raw_values"]
    assert "targets" in runner_production["raw_values"]
    assert "fumbles_lost" in runner_production["raw_values"]

    runner_first_downs = next(
        row
        for row in receipts
        if row["player"] == "Runner One"
        and row["component"] == "first_down_scoring_fit"
    )
    assert runner_first_downs["source_status"] == "imported_real_data"
    assert "rushing_first_downs" in runner_first_downs["raw_values"]
    assert "receiving_first_downs" in runner_first_downs["raw_values"]

    coverage = _read(result.source_coverage_path)
    runner_production_coverage = next(
        row
        for row in coverage
        if row["player"] == "Runner One" and row["section"] == "production"
    )
    assert runner_production_coverage["coverage_status"] == "covered"
    assert runner_production_coverage["source_status"] == "imported_real_data"

    runner_first_down_coverage = next(
        row
        for row in coverage
        if row["player"] == "Runner One"
        and row["section"] == "first_down_scoring_fit"
    )
    assert runner_first_down_coverage["coverage_status"] == "covered"
    assert runner_first_down_coverage["source_status"] == "imported_real_data"

    runner_usage = next(
        row
        for row in receipts
        if row["player"] == "Runner One" and row["component"] == "usage_opportunity"
    )
    assert runner_usage["source_status"] == "derived_real_data"
    assert "target_share" in runner_usage["raw_values"]
    assert "rb_carry_share" in runner_usage["raw_values"]
    assert "weighted_opportunities" in runner_usage["raw_values"]
    assert "route_participation_unavailable" in runner_usage["warning"]
    assert "routes_run_unavailable" in runner_usage["warning"]
    assert "tprr_unavailable" in runner_usage["warning"]
    assert "yprr_unavailable" in runner_usage["warning"]

    runner_snap = next(
        row
        for row in receipts
        if row["player"] == "Runner One" and row["component"] == "snap_proxy_role"
    )
    assert runner_snap["source_status"] == "imported_real_data"
    assert "offense_snaps" in runner_snap["raw_values"]
    assert "games_with_offensive_snaps" in runner_snap["raw_values"]
    assert "snap_share_proxy_only_not_route_participation" in runner_snap["warning"]
    assert "route_participation_unavailable" in runner_snap["warning"]

    runner_projection = next(
        row
        for row in receipts
        if row["player"] == "Runner One" and row["component"] == "projection"
    )
    assert runner_projection["source_status"] == "projection_stat_recompute_review_only"
    assert "estimated_from_history" in runner_projection["warning"]
    assert "first_down_projection_preview_only" in runner_projection["warning"]
    assert '"first_down_projection_status": "estimated_from_history"' in (
        runner_projection["raw_values"]
    )
    assert '"rushing_first_down_rate_scope": "player_recent"' in (
        runner_projection["raw_values"]
    )

    missing_projection = next(
        row
        for row in coverage
        if row["player"] == "Receiver Two" and row["section"] == "projection"
    )
    assert missing_projection["coverage_status"] == "missing"
    assert missing_projection["source_status"] == "missing_projection"

    receiver_young_prior = next(
        row
        for row in coverage
        if row["player"] == "Receiver Two" and row["section"] == "young_player_prior"
    )
    assert receiver_young_prior["coverage_status"] == "not_applicable"
    assert receiver_young_prior["source_status"] == "not_applicable"

    outputs = _read(result.preview_outputs_path)
    receiver = next(row for row in outputs if row["player"] == "Receiver Two")
    assert receiver["value_basis"] == "insufficient_evidence_not_rankable"
    assert receiver["missing_value_components"] == "usage_opportunity|snap_proxy_role|projection"
    assert "young_player_prior" not in receiver["unavailable_sections"]

    warnings = _read(result.warnings_path)
    assert any(
        row["player"] == "Receiver Two"
        and row["warning"] == "missing_projection_data"
        for row in warnings
    )


def _fixture_paths(tmp_path: Path) -> dict[str, Path]:
    truth = tmp_path / "truth_set.csv"
    reports = tmp_path / "reports"
    projection = tmp_path / "projections.csv"
    young = tmp_path / "young.csv"
    v3_2 = tmp_path / "v3_2"
    reports.mkdir()
    v3_2.mkdir()
    _write(
        truth,
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "nfl_team": "SF",
                "truth_set_group": "fixture",
                "reason_included": "test",
                "lifecycle_expected": "year_one_nfl_bridge",
                "roster_context": "test",
                "source_priority": "critical",
            },
            {
                "player_name": "Receiver Two",
                "position": "WR",
                "nfl_team": "KC",
                "truth_set_group": "fixture",
                "reason_included": "test",
                "lifecycle_expected": "established_veteran",
                "roster_context": "test",
                "source_priority": "high",
            },
        ],
    )
    _write(
        reports / "truth_set_v3_production_player_season.csv",
        [
            {
                "truth_set_player_name": "Runner One",
                "matched_player_name": "Runner One",
                "player_id": "00-rb",
                "season": "2024",
                "games": "17",
                "team": "SF",
                "position": "RB",
                "passing_yards": "0",
                "passing_tds": "0",
                "interceptions": "0",
                "rushing_attempts": "250",
                "rushing_yards": "1100",
                "rushing_tds": "9",
                "targets": "60",
                "receptions": "45",
                "receiving_yards": "350",
                "receiving_tds": "2",
                "rushing_first_downs": "55",
                "receiving_first_downs": "18",
                "fumbles_lost": "1",
                "source_status": "imported_real_data",
            },
            {
                "truth_set_player_name": "Receiver Two",
                "matched_player_name": "Receiver Two",
                "player_id": "00-wr",
                "season": "2024",
                "games": "17",
                "team": "KC",
                "position": "WR",
                "passing_yards": "0",
                "passing_tds": "0",
                "interceptions": "0",
                "rushing_attempts": "0",
                "rushing_yards": "0",
                "rushing_tds": "0",
                "targets": "100",
                "receptions": "70",
                "receiving_yards": "900",
                "receiving_tds": "6",
                "rushing_first_downs": "0",
                "receiving_first_downs": "44",
                "fumbles_lost": "0",
                "source_status": "imported_real_data",
            },
        ],
    )
    _write(
        reports / "truth_set_v3_usage_player_season.csv",
        [
            {
                "truth_set_player_name": "Runner One",
                "season": "2024",
                "team": "SF",
                "position": "RB",
                "target_share": "0.12",
                "rb_target_share": "0.12",
                "rushing_attempts": "250",
                "team_rushing_attempts": "500",
                "rb_carry_share": "0.5",
                "weighted_opportunities": "319",
                "red_zone_carries": "30",
                "red_zone_targets": "8",
                "goal_line_carries": "10",
                "goal_line_targets": "2",
                "short_yardage_carries": "25",
                "games_with_usage": "17",
                "source_status": "derived_real_data",
            }
        ],
    )
    _write(
        reports / "truth_set_v3_snap_share_player_season.csv",
        [
            {
                "truth_set_player_name": "Runner One",
                "matched_player_name": "Runner One",
                "season": "2024",
                "team": "SF",
                "position": "RB",
                "games": "17",
                "games_with_offensive_snaps": "16",
                "offense_snaps": "710",
                "avg_offense_pct": "0.72",
                "avg_snap_share": "0.72",
                "source_status": "imported_real_data",
            }
        ],
    )
    _write(
        projection,
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "nfl_team": "SF",
                "projected_rushing_attempts": "200",
                "projected_rushing_yards": "1000",
                "projected_rushing_tds": "8",
                "projected_targets": "50",
                "projected_receptions": "40",
                "projected_receiving_yards": "320",
                "projected_receiving_tds": "2",
                "projected_lve_points_if_calculable": "999",
            }
        ],
    )
    _write(
        young,
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "nfl_team": "SF",
                "draft_year": "2025",
                "nfl_draft_round": "1",
                "nfl_draft_pick": "20",
                "asset_lifecycle": "year_one_nfl_bridge",
                "draft_capital_prior_score": "90",
            }
        ],
    )
    _write(
        v3_2 / "stats_first_normalized_features.csv",
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "team": "SF",
                "confidence": "86",
                "warnings": "",
                "age_raw": "23",
                "injury_durability": "80",
                "role_security": "75",
            },
            {
                "player_name": "Receiver Two",
                "position": "WR",
                "team": "KC",
                "confidence": "70",
                "warnings": "missing_projection_data",
                "age_raw": "28",
                "injury_durability": "75",
                "role_security": "70",
            },
        ],
    )
    (v3_2 / "model_outputs_scored_non_k.csv").write_text(
        "player_name,score\nRunner One,1\n",
        encoding="utf-8",
    )
    return {
        "truth": truth,
        "reports": reports,
        "projection": projection,
        "young": young,
        "v3_2": v3_2,
    }


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = tuple(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
