from __future__ import annotations

import csv
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES
from src.services.data_pack_health_service import (
    build_data_pack_health_report,
    coverage_report_rows,
    health_check_rows,
    health_issue_rows,
    health_summary_row,
    readiness_status_rows,
)


def test_health_report_blocks_when_league_ranks_are_missing(tmp_path: Path) -> None:
    _write_pack(tmp_path, official_rank="", model_placeholder=True)

    report = build_data_pack_health_report(tmp_path, roster_limit=1)

    assert report.readiness == "blocked"
    assert report.league_rank_coverage_pct == 0
    assert report.placeholder_model_output_count == 1
    assert any(check.check_name == "league_rank_coverage" for check in report.checks)
    coverage = {row["coverage_area"]: row for row in coverage_report_rows(report)}
    assert coverage["league_rank_rows"]["status"] == "blocked"
    assert coverage["league_rank_rows"]["decision_blocking"] is True
    assert health_summary_row(report)["readiness"] == "blocked"
    assert health_check_rows(report)
    assert health_issue_rows(report)


def test_health_report_requires_review_for_neutral_model_outputs(
    tmp_path: Path,
) -> None:
    _write_pack(tmp_path, official_rank="12", model_placeholder=True)

    report = build_data_pack_health_report(tmp_path, roster_limit=1)

    assert report.readiness == "review"
    assert report.league_rank_coverage_pct == 100
    assert report.placeholder_model_output_count == 1
    assert any(check.check_name == "model_outputs" for check in report.checks)
    rows = {row["status_area"]: row for row in readiness_status_rows(report)}
    assert rows["data_ready"]["status"] == "ready"
    assert rows["model_ready"]["status"] == "needs_scores"
    assert rows["decision_ready"]["status"] == "review_only"
    assert "not final calls" in rows["decision_ready"]["what_it_means"]
    coverage = {row["coverage_area"]: row for row in coverage_report_rows(report)}
    assert coverage["model_outputs"]["status"] == "review"
    assert coverage["model_outputs"]["covered"] == "0"
    assert "placeholder" in coverage["model_outputs"]["detail"]


def test_health_report_counts_rank_table_as_roster_rank_fallback(
    tmp_path: Path,
) -> None:
    _write_pack(
        tmp_path,
        official_rank="",
        model_placeholder=False,
        roster_league_rank="",
        ranking_league_rank="12",
    )

    report = build_data_pack_health_report(tmp_path, roster_limit=1)

    assert report.readiness == "ready"
    assert report.league_rank_coverage_pct == 100
    coverage = {row["coverage_area"]: row for row in coverage_report_rows(report)}
    assert coverage["league_rank_rows"]["status"] == "ready"
    assert coverage["league_rank_rows"]["coverage_pct"] == 100


def test_health_report_is_ready_for_reviewed_scored_pack(tmp_path: Path) -> None:
    _write_pack(tmp_path, official_rank="12", model_placeholder=False)

    report = build_data_pack_health_report(tmp_path, roster_limit=1)

    assert report.readiness == "ready"
    assert report.error_count == 0
    assert report.warning_count == 0
    assert report.placeholder_model_output_count == 0
    rows = {row["status_area"]: row for row in readiness_status_rows(report)}
    assert rows["data_ready"]["status"] == "ready"
    assert rows["model_ready"]["status"] == "under_recalibration"
    assert rows["decision_ready"]["status"] == "review_only"
    assert "not final calls" in rows["decision_ready"]["what_it_means"]
    assert "review-only" in rows["model_ready"]["next_action"]
    coverage = {row["coverage_area"]: row for row in coverage_report_rows(report)}
    assert {row["status"] for row in coverage.values()} == {"ready"}


def _write_pack(
    path: Path,
    *,
    official_rank: str,
    model_placeholder: bool,
    roster_league_rank: str | None = None,
    ranking_league_rank: str | None = None,
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for file_name in REQUIRED_V1_FILES:
        schema = CSV_SCHEMAS[file_name]
        row = _row_for_file(
            file_name,
            official_rank=official_rank,
            model_placeholder=model_placeholder,
            roster_league_rank=roster_league_rank,
            ranking_league_rank=ranking_league_rank,
        )
        with (path / file_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(schema.all_columns))
            writer.writeheader()
            writer.writerow(row)


def _row_for_file(
    file_name: str,
    *,
    official_rank: str,
    model_placeholder: bool,
    roster_league_rank: str | None,
    ranking_league_rank: str | None,
) -> dict[str, object]:
    if file_name == "dim_players.csv":
        return {
            "player_id": "p1",
            "player_name": "Alpha Back",
            "position": "RB",
            "active_flag": "1",
        }
    if file_name == "fact_rosters.csv":
        return {
            "snapshot_date": "2026-pre-draft",
            "season": "2026",
            "team_id": "niners",
            "team_name": "Niners",
            "player_id": "p1",
            "player_name": "Alpha Back",
            "official_rank": official_rank,
            "league_rank": roster_league_rank
            if roster_league_rank is not None
            else official_rank,
        }
    if file_name == "fact_official_rankings.csv":
        return {
            "snapshot_date": "2026-pre-draft",
            "season": "2026",
            "player_id": "p1",
            "player_name": "Alpha Back",
            "official_rank": official_rank,
            "league_rank": ranking_league_rank
            if ranking_league_rank is not None
            else official_rank,
        }
    if file_name == "fact_future_picks.csv":
        return {
            "snapshot_date": "2026-pre-draft",
            "season": "2026",
            "pick_year": "2026",
            "round": "1",
            "slot": "1",
            "pick_label": "2026 1.01",
            "original_team_id": "niners",
            "current_team_id": "niners",
        }
    if file_name == "fact_pick_values.csv":
        return {
            "snapshot_date": "2026-pre-draft",
            "pick_year": "2026",
            "pick_label": "2026 1.01",
            "round": "1",
            "slot": "1",
            "overall_pick": "1",
            "base_value_1000": "1000",
            "final_pick_value": "1000",
        }
    if file_name == "model_outputs.csv":
        return {
            "snapshot_date": "2026-pre-draft",
            "player_id": "p1",
            "player_name": "Alpha Back",
            "risk_level": "needs_model" if model_placeholder else "low",
            "notes": (
                "Neutral placeholder generated from refreshed Sleeper data."
                if model_placeholder
                else "Reviewed score."
            ),
        }
    return {
        "snapshot_date": "2026-pre-draft",
        "data_pack_name": "pack",
        "file_name": file_name,
        "review_status": "reviewed",
    }
