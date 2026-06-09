from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.confidence_calibration_audit_service import (
    build_confidence_calibration_audit,
)


def test_confidence_calibration_flags_misleading_high_confidence(
    tmp_path: Path,
) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "role_security", "missing_role_fixture")

    report = build_confidence_calibration_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    row = _player_row(report.rows, "Lamar Jackson")

    assert row["actual_confidence_tier"] == "usable"
    assert row["expected_confidence_tier"] == "blocked"
    assert row["mismatch_flag"] is True
    assert "role/usage" in str(row["missing_proxy_buckets"])
    assert "claims usable certainty" in str(row["mismatch_reason"])


def test_confidence_calibration_keeps_matching_limited_confidence_unflagged(
    tmp_path: Path,
) -> None:
    model_dir = _fixture_model_dir(tmp_path)

    report = build_confidence_calibration_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    row = _player_row(report.rows, "Lamar Jackson")

    assert row["mismatch_flag"] is False
    assert row["confidence_tier_gap"] <= 0


def test_confidence_calibration_summary_counts_mismatches(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "role_security", "missing_role_fixture")

    report = build_confidence_calibration_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )
    summary = {str(row["metric"]): row for row in report.summary_rows}

    assert summary["players"]["value"] > 0
    assert summary["mismatch_players"]["value"] >= 1
    assert "expected_blocked" in summary
    assert "actual_usable" in summary


def test_confidence_calibration_uses_visible_stats_first_preview_confidence(
    tmp_path: Path,
) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _write_rows(
        model_dir / "stats_first_veteran_model_preview_outputs.csv",
        [
            {
                "player_id": "lamar_jackson",
                "player_name": "Lamar Jackson",
                "position": "QB",
                "team": "BAL",
                "confidence_score": "61",
            }
        ],
    )

    report = build_confidence_calibration_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    row = _player_row(report.rows, "Lamar Jackson")

    assert row["confidence"] == 61.0
    assert row["actual_confidence_tier"] == "review"


def _fixture_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "veteran_model_v1"
    shutil.copytree(Path("sample_data/veteran_model_v1"), model_dir)
    _write_identity_ready(model_dir, "Lamar Jackson", "QB")
    return model_dir


def _mark_feature_missing(
    model_dir: Path,
    player_id: str,
    feature_name: str,
    missing_reason: str,
) -> None:
    path = model_dir / "veteran_feature_scores.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["player_id"] == player_id and row["feature_name"] == feature_name:
            row["normalized_score"] = ""
            row["is_missing"] = "true"
            row["missing_reason"] = missing_reason
    _write_rows(path, rows)


def _write_identity_ready(model_dir: Path, player_name: str, position: str) -> None:
    rows = [
        {
            "sleeper_id": "",
            "player_id": "",
            "player_name": player_name,
            "position": position,
            "team": "BAL",
            "sleeper_gsis_id": "",
            "bridge_gsis_id": "",
            "bridge_pfr_id": "jackla00",
            "bridge_name": player_name,
            "matched_gsis_id": "00-0034796",
            "stat_player_name": player_name,
            "match_method": "manual",
            "match_status": "matched",
            "manual_review_required": "false",
        }
    ]
    _write_rows(model_dir / "active_roster_identity_review.csv", rows)


def _player_row(rows: list[dict[str, object]], player: str) -> dict[str, object]:
    matches = [row for row in rows if row["player"] == player]
    assert matches
    return matches[0]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
