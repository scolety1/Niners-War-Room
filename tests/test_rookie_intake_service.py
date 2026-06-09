from __future__ import annotations

import csv
from pathlib import Path

from src.services.rookie_intake_service import build_rookie_intake_report

SAMPLE_DIR = Path("sample_data/rookie_model_v1")


def test_sample_rookie_intake_is_ready() -> None:
    report = build_rookie_intake_report(SAMPLE_DIR)

    assert not report.has_errors
    assert report.ready_count == 10
    assert report.blocked_count == 0
    assert report.issues == ()


def test_rookie_intake_flags_bad_values_and_duplicate_ids(tmp_path) -> None:
    _copy_source_files(tmp_path)
    _write_prospects(
        tmp_path / "rookie_prospect_inputs.csv",
        [
            {
                "player_id": "bad id",
                "player_name": "Bad One",
                "position": "WR",
                "class_year": "2026",
                "model_mode": "post_draft",
                "source_snapshot_id": "fixture",
                "source_name": "manual",
                "source_date": "2026-05-05",
                "data_completeness_status": "partial",
                "draft_capital": "101",
                "target_earning": "",
                "efficiency_dominance": "70",
                "age_trajectory": "65",
                "chain_moving": "60",
                "rookie_opportunity_score": "75",
            },
            {
                "player_id": "bad id",
                "player_name": "Bad Two",
                "position": "WR",
                "class_year": "2026",
                "model_mode": "post_draft",
                "source_snapshot_id": "fixture",
                "source_name": "manual",
                "source_date": "2026-05-05",
                "data_completeness_status": "partial",
                "draft_capital": "80",
                "target_earning": "80",
                "efficiency_dominance": "70",
                "age_trajectory": "65",
                "chain_moving": "60",
                "rookie_opportunity_score": "75",
            },
        ],
    )

    report = build_rookie_intake_report(tmp_path)
    issue_pairs = {(issue.severity, issue.issue) for issue in report.issues}

    assert ("error", "player_id must be a stable lowercase slug.") in issue_pairs
    assert ("error", "Duplicate player_id.") in issue_pairs
    assert ("error", "Normalized feature score must be 0-100.") in issue_pairs
    assert ("warning", "Missing core rookie feature.") in issue_pairs
    assert report.blocked_count == 2


def test_rookie_intake_allows_one_missing_core_feature_with_penalty(tmp_path) -> None:
    _copy_source_files(tmp_path)
    _write_prospects(
        tmp_path / "rookie_prospect_inputs.csv",
        [
            {
                "player_id": "partial_wr",
                "player_name": "Partial WR",
                "position": "WR",
                "class_year": "2026",
                "model_mode": "post_draft",
                "source_snapshot_id": "fixture",
                "source_name": "manual",
                "source_date": "2026-05-05",
                "data_completeness_status": "partial",
                "draft_capital": "80",
                "target_earning": "",
                "efficiency_dominance": "70",
                "age_trajectory": "65",
                "chain_moving": "60",
                "rookie_opportunity_score": "75",
            }
        ],
    )

    report = build_rookie_intake_report(tmp_path)

    assert not report.has_errors
    assert report.rows[0].readiness == "scored_with_confidence_penalty"
    assert report.rows[0].model_output_allowed is True


def test_rookie_intake_blocks_three_missing_core_features(tmp_path) -> None:
    _copy_source_files(tmp_path)
    _write_prospects(
        tmp_path / "rookie_prospect_inputs.csv",
        [
            {
                "player_id": "thin_wr",
                "player_name": "Thin WR",
                "position": "WR",
                "class_year": "2026",
                "model_mode": "post_draft",
                "source_snapshot_id": "fixture",
                "source_name": "manual",
                "source_date": "2026-05-05",
                "data_completeness_status": "partial",
                "draft_capital": "80",
                "target_earning": "",
                "efficiency_dominance": "",
                "age_trajectory": "",
                "chain_moving": "60",
                "rookie_opportunity_score": "75",
            }
        ],
    )

    report = build_rookie_intake_report(tmp_path)

    assert report.rows[0].readiness == "blocked"
    assert report.rows[0].model_output_allowed is False


def _copy_source_files(target_dir: Path) -> None:
    for filename in ("rookie_feature_registry.csv", "veteran_opportunity_benchmarks.csv"):
        (target_dir / filename).write_text(
            (SAMPLE_DIR / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def _write_prospects(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
