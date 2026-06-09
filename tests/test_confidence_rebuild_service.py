from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.confidence_rebuild_service import (
    BLOCKED_ACTION,
    LIMITED_ACTION,
    REVIEW_ACTION,
    build_confidence_rebuild_report,
)


def test_stale_source_lowers_confidence_and_explains_freshness(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _make_source_stale(model_dir, "projection_fixture_2026")

    report = build_confidence_rebuild_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
        as_of_date="2026-05-07",
    )

    row = _player_row(report.rows, "Lamar Jackson")
    explanation = _explanation_row(report.explanation_rows, "Lamar Jackson", "source_freshness")

    assert row["source_freshness_score"] < 60
    assert row["action_certainty"] in {REVIEW_ACTION, LIMITED_ACTION}
    assert "stale" in str(explanation["reason"]).lower()
    assert "stale_source_data" in str(row["confidence_warning_reasons"])


def test_missing_role_bucket_reduces_action_certainty(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "role_security", "missing_role_fixture")

    report = build_confidence_rebuild_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    row = _player_row(report.rows, "Lamar Jackson")
    explanation = _explanation_row(
        report.explanation_rows,
        "Lamar Jackson",
        "core_field_completeness",
    )

    assert row["action_certainty"] == BLOCKED_ACTION
    assert "role/usage" in str(row["missing_critical_inputs"])
    assert "Missing critical buckets=" in str(explanation["reason"])


def test_missing_injury_bucket_lowers_confidence_without_fake_stat(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(
        model_dir,
        "lamar_jackson",
        "current_injury_durability",
        "missing_injury_fixture",
    )

    report = build_confidence_rebuild_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    row = _player_row(report.rows, "Lamar Jackson")

    assert row["action_certainty"] == REVIEW_ACTION
    assert "injury" in str(row["review_gap_inputs"])
    assert "review_source_gap" in str(row["confidence_warning_reasons"])


def test_identity_ambiguity_blocks_action_certainty(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _write_identity_review(model_dir, "Lamar Jackson", "QB")

    report = build_confidence_rebuild_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    row = _player_row(report.rows, "Lamar Jackson")
    explanation = _explanation_row(
        report.explanation_rows,
        "Lamar Jackson",
        "identity_confidence",
    )

    assert row["action_certainty"] == BLOCKED_ACTION
    assert row["identity_confidence"] <= 35
    assert "identity" in str(row["certainty_reason"]).lower()
    assert "review" in str(explanation["reason"])


def test_feature_disagreement_lowers_confidence_and_keeps_score_adjustment_zero(
    tmp_path: Path,
) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _set_feature_score(model_dir, "lamar_jackson", "role_security", "5")

    report = build_confidence_rebuild_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    row = _player_row(report.rows, "Lamar Jackson")
    explanation = _explanation_row(
        report.explanation_rows,
        "Lamar Jackson",
        "feature_agreement",
    )

    assert row["feature_agreement"] < 45
    assert row["action_certainty"] in {REVIEW_ACTION, LIMITED_ACTION}
    assert row["score_adjustment_from_confidence"] == 0.0
    assert "spread" in str(explanation["reason"])


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


def _set_feature_score(
    model_dir: Path,
    player_id: str,
    feature_name: str,
    normalized_score: str,
) -> None:
    path = model_dir / "veteran_feature_scores.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["player_id"] == player_id and row["feature_name"] == feature_name:
            row["normalized_score"] = normalized_score
            row["is_missing"] = "false"
            row["missing_reason"] = ""
    _write_rows(path, rows)


def _make_source_stale(model_dir: Path, source_key: str) -> None:
    path = model_dir / "veteran_source_catalog.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["source_key"] == source_key:
            row["source_date"] = "2026-01-01"
            row["freshness_window_hours"] = "24"
            row["reliability_score"] = "40"
    _write_rows(path, rows)


def _write_identity_review(model_dir: Path, player_name: str, position: str) -> None:
    path = model_dir / "active_roster_identity_review.csv"
    rows = [
        {
            "sleeper_id": "",
            "player_id": "",
            "player_name": player_name,
            "position": position,
            "team": "",
            "sleeper_gsis_id": "",
            "bridge_gsis_id": "",
            "bridge_pfr_id": "",
            "bridge_name": "",
            "matched_gsis_id": "",
            "stat_player_name": "",
            "match_method": "name_fallback",
            "match_status": "review_needed",
            "manual_review_required": "true",
        }
    ]
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


def _explanation_row(
    rows: list[dict[str, object]],
    player: str,
    component: str,
) -> dict[str, object]:
    matches = [row for row in rows if row["player"] == player and row["component"] == component]
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
