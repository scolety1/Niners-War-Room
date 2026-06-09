from __future__ import annotations

import csv
from pathlib import Path

from src.services.historical_replay_contract_service import (
    HISTORICAL_REPLAY_TEMPLATE_HEADERS,
    build_historical_replay_contract_report,
    historical_replay_coverage_rows,
    historical_replay_issue_rows,
)


def test_historical_replay_contract_templates_are_ready() -> None:
    report = build_historical_replay_contract_report()

    assert report.status == "ready"
    assert report.error_count == 0
    assert {row.file_name for row in report.coverage_rows} == set(
        HISTORICAL_REPLAY_TEMPLATE_HEADERS
    )
    assert {row["status"] for row in historical_replay_coverage_rows(report)} == {"ready"}


def test_historical_replay_contract_blocks_missing_headers(tmp_path: Path) -> None:
    _write_contract_set(tmp_path)
    _write_csv(tmp_path / "model_replay_inputs.csv", ("season", "player"), [])

    report = build_historical_replay_contract_report(tmp_path)

    assert report.status == "blocked"
    assert report.error_count == 1
    coverage = {
        row["file_name"]: row for row in historical_replay_coverage_rows(report)
    }
    assert coverage["model_replay_inputs.csv"]["status"] == "blocked"
    assert "model_rank" in coverage["model_replay_inputs.csv"]["missing_columns"]


def test_historical_replay_contract_rejects_hindsight_in_as_of_files(
    tmp_path: Path,
) -> None:
    _write_contract_set(tmp_path)
    header = HISTORICAL_REPLAY_TEMPLATE_HEADERS["model_replay_inputs.csv"] + (
        "outcome_score",
    )
    _write_csv(
        tmp_path / "model_replay_inputs.csv",
        header,
        [
            {
                "season": "2024",
                "player": "Example Rookie",
                "position": "WR",
                "model_rank": "1",
                "model_score": "92",
                "model_recommendation": "draft",
                "model_version": "as_of_v1",
                "as_of_date": "2024-08-01",
                "input_source_snapshot_id": "source_2024",
                "confidence": "reviewed",
                "notes": "",
                "outcome_score": "88",
            }
        ],
    )

    report = build_historical_replay_contract_report(tmp_path)

    assert report.status == "blocked"
    issues = historical_replay_issue_rows(report)
    assert any("cannot contain outcome_score" in row["issue"] for row in issues)


def test_historical_replay_contract_rejects_duplicate_pick_rows(tmp_path: Path) -> None:
    _write_contract_set(tmp_path)
    _write_csv(
        tmp_path / "offline_rookie_notes.csv",
        HISTORICAL_REPLAY_TEMPLATE_HEADERS["offline_rookie_notes.csv"],
        [
            _offline_note("2025", "1", "One Rookie"),
            _offline_note("2025", "1", "Duplicate Rookie"),
        ],
    )

    report = build_historical_replay_contract_report(tmp_path)

    assert report.status == "blocked"
    assert any(issue.issue == "Duplicate historical replay row." for issue in report.issues)


def _write_contract_set(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for file_name, header in HISTORICAL_REPLAY_TEMPLATE_HEADERS.items():
        _write_csv(path / file_name, header, [])


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _offline_note(season: str, pick: str, player: str) -> dict[str, str]:
    return {
        "season": season,
        "rookie_pick_number": pick,
        "team": "Niners",
        "player": player,
        "position": "WR",
        "source": "notebook",
        "confidence": "handwritten_note",
        "provenance_note": "Offline handwritten rookie draft note.",
        "needs_traded_pick_review": "true",
        "source_snapshot_id": f"notes_{season}",
        "transcribed_by": "codex",
        "transcribed_at": "2026-05-05T00:00:00-06:00",
        "notes": "",
    }
