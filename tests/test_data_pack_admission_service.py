from __future__ import annotations

import csv
import json
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES
from src.services.data_pack_admission_service import (
    admission_reason_rows,
    admission_summary_row,
    build_data_pack_admission_report,
)


def test_admission_blocks_pack_without_league_ranks(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    _write_pack(pack, league_rank="", placeholder=False)

    report = build_data_pack_admission_report(candidate_data_pack=pack, roster_limit=1)

    assert report.decision == "blocked"
    assert any(reason.area == "league_rank" for reason in report.reasons)
    assert admission_summary_row(report)["decision"] == "blocked"


def test_admission_requires_review_for_placeholder_outputs(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    _write_pack(pack, league_rank="10", placeholder=True)

    report = build_data_pack_admission_report(candidate_data_pack=pack, roster_limit=1)

    assert report.decision == "review"
    assert any(reason.area == "model_outputs" for reason in report.reasons)
    assert admission_reason_rows(report)


def test_admission_requires_review_for_diff_changes(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    _write_pack(baseline, league_rank="10", placeholder=False, team_id="niners")
    _write_pack(candidate, league_rank="12", placeholder=False, team_id="owls")

    report = build_data_pack_admission_report(
        baseline_data_pack=baseline,
        candidate_data_pack=candidate,
    )

    assert report.decision == "review"
    assert report.diff_change_count >= 1
    assert any(reason.area == "rosters" for reason in report.reasons)
    assert any(reason.area == "league_rank" for reason in report.reasons)


def test_admission_ready_for_clean_reviewed_pack(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    _write_pack(pack, league_rank="10", placeholder=False)

    report = build_data_pack_admission_report(candidate_data_pack=pack, roster_limit=1)

    assert report.decision == "ready"
    assert admission_reason_rows(report)[0]["severity"] == "ready"


def test_admission_blocks_zero_row_generated_applied_pack(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    _write_pack(pack, league_rank="10", placeholder=False)
    _write_applied_pack_manifest(pack, applied_row_count=0)

    report = build_data_pack_admission_report(candidate_data_pack=pack, roster_limit=1)

    assert report.decision == "blocked"
    assert any(
        reason.area == "generated_applied_pack" and reason.severity == "blocked"
        for reason in report.reasons
    )


def test_admission_includes_ready_generated_applied_pack_reason(
    tmp_path: Path,
) -> None:
    pack = tmp_path / "pack"
    _write_pack(pack, league_rank="10", placeholder=False)
    _write_applied_pack_manifest(pack, applied_row_count=1)

    report = build_data_pack_admission_report(candidate_data_pack=pack, roster_limit=1)
    rows = admission_reason_rows(report)

    assert report.decision == "ready"
    assert rows[0]["area"] == "generated_applied_pack"
    assert "Import Review" in rows[0]["action"]


def _write_pack(
    path: Path,
    *,
    league_rank: str,
    placeholder: bool,
    team_id: str = "niners",
) -> None:
    path.mkdir(parents=True)
    for file_name in REQUIRED_V1_FILES:
        schema = CSV_SCHEMAS[file_name]
        row = _row_for_file(
            file_name,
            league_rank=league_rank,
            placeholder=placeholder,
            team_id=team_id,
        )
        with (path / file_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(schema.all_columns))
            writer.writeheader()
            writer.writerow(row)


def _row_for_file(
    file_name: str,
    *,
    league_rank: str,
    placeholder: bool,
    team_id: str,
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
            "team_id": team_id,
            "team_name": team_id.title(),
            "player_id": "p1",
            "player_name": "Alpha Back",
            "league_rank": league_rank,
        }
    if file_name == "fact_official_rankings.csv":
        return {
            "snapshot_date": "2026-pre-draft",
            "season": "2026",
            "player_id": "p1",
            "player_name": "Alpha Back",
            "league_rank": league_rank,
        }
    if file_name == "fact_future_picks.csv":
        return {
            "snapshot_date": "2026-pre-draft",
            "season": "2026",
            "pick_year": "2026",
            "round": "1",
            "slot": "1",
            "pick_label": "2026 1.01",
            "current_team_id": "niners",
            "current_team_name": "Niners",
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
            "risk_level": "needs_model" if placeholder else "low",
            "notes": "Neutral placeholder" if placeholder else "Reviewed score.",
        }
    return {
        "snapshot_date": "2026-pre-draft",
        "data_pack_name": "pack",
        "file_name": file_name,
        "review_status": "reviewed",
    }


def _write_applied_pack_manifest(path: Path, *, applied_row_count: int) -> None:
    (path / "model_applied_pack_manifest.json").write_text(
        json.dumps(
            {
                "applied_pack_id": path.name,
                "applied_row_count": applied_row_count,
                "promotion_candidate_count": applied_row_count,
                "scoring_effect": "generated applied pack copy",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
