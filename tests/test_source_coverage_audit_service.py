from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.source_coverage_audit_service import build_source_coverage_audit


def test_source_coverage_reports_player_feature_buckets(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    assert report.issues == []
    assert report.player_rows
    assert {row["bucket"] for row in report.bucket_rows} >= {
        "production",
        "projections",
        "role/usage",
        "injury",
        "age/bio",
        "identity",
        "market",
        "league rank",
    }
    lamar_projection = _feature_row(report.feature_rows, "Lamar Jackson", "projections")
    assert lamar_projection["feature_name"] == "lve_projection_value"
    assert lamar_projection["feature_data_status"] == "real"
    lamar_identity = _feature_row(report.feature_rows, "Lamar Jackson", "identity")
    assert lamar_identity["feature_data_status"] == "real"


def test_missing_critical_bucket_lowers_coverage_confidence_and_blocks(
    tmp_path: Path,
) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "role_security")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    player = _player_row(report.player_rows, "Lamar Jackson")
    role_bucket = _bucket_row(report.bucket_rows, "Lamar Jackson", "role/usage")

    assert role_bucket["coverage_class"] == "critical"
    assert role_bucket["decision_effect"] == "blocks_decision_trust"
    assert role_bucket["gap_acceptance_status"] == "not_allowed"
    assert role_bucket["confidence_penalty"] > 0
    assert player["coverage_adjusted_confidence"] < player["model_confidence"]
    assert "role/usage" in str(player["missing_critical_inputs"])
    assert player["coverage_status"] == "blocked_critical_coverage"


def test_missing_projection_bucket_is_review_gap_not_critical(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "lve_projection_value")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    player = _player_row(report.player_rows, "Lamar Jackson")
    projection_bucket = _bucket_row(report.bucket_rows, "Lamar Jackson", "projections")

    assert projection_bucket["coverage_class"] == "review"
    assert projection_bucket["decision_blocking_bucket"] is False
    assert projection_bucket["decision_effect"] == "confidence_penalty_review_needed"
    assert projection_bucket["gap_acceptance_status"] == "review_needed"
    assert projection_bucket["source_gap_scope"] == "future paid-data candidate"
    assert projection_bucket["source_gap_summary"] == "needs paid/free source upgrade"
    assert "projections" in str(player["review_gap_inputs"])
    assert "projections" not in str(player["missing_critical_inputs"])


def test_missing_feature_does_not_show_neutral_fake_stat(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "lve_projection_value")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    feature = _feature_row(report.feature_rows, "Lamar Jackson", "projections")

    assert feature["feature_data_status"] == "missing"
    assert feature["normalized_score"] == ""
    assert feature["coverage_credit"] == 0.0
    assert feature["missing_reason"] == "missing_projection_fixture"


def test_missing_injury_bucket_is_review_not_decision_blocker(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "current_injury_durability")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    player = _player_row(report.player_rows, "Lamar Jackson")
    injury_bucket = _bucket_row(report.bucket_rows, "Lamar Jackson", "injury")
    lamar_injury_blockers = [
        row
        for row in report.missing_critical_rows
        if row["player"] == "Lamar Jackson" and row["bucket"] == "injury"
    ]

    assert injury_bucket["coverage_class"] == "review"
    assert injury_bucket["critical_bucket"] is False
    assert injury_bucket["review_bucket"] is True
    assert injury_bucket["decision_blocking_bucket"] is False
    assert injury_bucket["gap_acceptance_status"] == "review_needed"
    assert injury_bucket["bucket_status"] == "missing"
    assert player["coverage_status"] == "review_coverage"
    assert lamar_injury_blockers == []
    assert report.review_gap_rows


def test_estimated_source_counts_as_imputed_not_full_coverage(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _set_source_confidence(model_dir, "lamar_jackson", "role_security", "estimated")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    role_bucket = _bucket_row(report.bucket_rows, "Lamar Jackson", "role/usage")
    role_feature = _feature_row(report.feature_rows, "Lamar Jackson", "role/usage")

    assert role_feature["feature_data_status"] == "estimated_or_proxy"
    assert role_bucket["bucket_status"] == "review"
    assert role_bucket["coverage_pct"] == 75.0
    assert role_bucket["imputed_feature_count"] == 1


def test_league_rank_bucket_uses_governance_rank_not_model_stat(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    league_rank = _feature_row(report.feature_rows, "Lamar Jackson", "league rank")

    assert league_rank["feature_name"] == "__league_rank__"
    assert league_rank["feature_data_status"] == "real"
    assert league_rank["normalized_score"] == 31
    assert league_rank["scoring_status"] == "governance_only"


def test_accepted_review_gap_still_keeps_confidence_penalty_visible(
    tmp_path: Path,
) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _mark_feature_missing(model_dir, "lamar_jackson", "current_injury_durability")
    _write_gap_acceptance(model_dir, "lamar_jackson", "injury")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    player = _player_row(report.player_rows, "Lamar Jackson")
    injury_bucket = _bucket_row(report.bucket_rows, "Lamar Jackson", "injury")

    assert injury_bucket["gap_acceptance_status"] == "accepted"
    assert injury_bucket["decision_effect"] == "confidence_penalty_accepted"
    assert injury_bucket["confidence_penalty"] > 0
    assert injury_bucket["source_gap_scope"] == "optional accepted"
    assert injury_bucket["source_gap_summary"] == (
        "accepted optional gap; confidence penalty retained"
    )
    assert "injury" in str(player["accepted_review_gap_inputs"])
    assert "injury" not in str(player["unaccepted_review_gap_inputs"])
    assert "optional accepted" in str(player["source_gap_scopes"])
    assert report.accepted_review_gap_rows


def test_qb_age_bio_bucket_uses_stats_first_age_curve_only(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    age_bucket = _bucket_row(report.bucket_rows, "Lamar Jackson", "age/bio")

    assert age_bucket["expected_features"] == "age_curve"
    assert age_bucket["bucket_status"] == "ready"
    assert age_bucket["missing_features"] == ""


def test_stats_first_young_bridge_prior_turns_missing_production_into_review(
    tmp_path: Path,
) -> None:
    model_dir = _stats_first_model_dir(tmp_path)

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    young_bucket = _bucket_row(report.bucket_rows, "Luther Burden", "production")
    young_feature = _feature_row(report.feature_rows, "Luther Burden", "production")
    older_bucket = _bucket_row(report.bucket_rows, "Old Missing WR", "production")

    assert young_feature["feature_name"] == "young_nfl_bridge_production_prior"
    assert young_feature["feature_data_status"] == "estimated_or_proxy"
    assert young_bucket["bucket_status"] == "review"
    assert young_bucket["missing_feature_count"] == 0
    assert young_bucket["imputed_feature_count"] == 1
    assert older_bucket["bucket_status"] == "missing"
    assert older_bucket["missing_feature_count"] == 1


def test_stats_first_warning_marks_role_usage_as_proxy_coverage(tmp_path: Path) -> None:
    model_dir = _stats_first_model_dir(tmp_path)
    _set_stats_first_normalized_warnings(
        model_dir,
        "12519",
        "missing_lve_scoring_history|missing_participation_proxy",
    )

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    role_bucket = _bucket_row(report.bucket_rows, "Luther Burden", "role/usage")
    role_feature = _feature_row(report.feature_rows, "Luther Burden", "role/usage")
    player = _player_row(report.player_rows, "Luther Burden")

    assert role_feature["feature_data_status"] == "estimated_or_proxy"
    assert role_bucket["bucket_status"] == "review"
    assert role_bucket["coverage_class"] == "critical"
    assert role_bucket["decision_effect"] == "blocks_decision_trust"
    assert role_bucket["source_gap_scope"] == "roster-critical"
    assert role_bucket["source_gap_summary"] == (
        "blocks roster review until source evidence is fixed"
    )
    assert "role/usage" in str(player["critical_review_inputs"])
    assert player["source_gap_summary"] == (
        "blocks roster review until source evidence is fixed"
    )


def test_stats_first_stale_production_season_is_critical_review(
    tmp_path: Path,
) -> None:
    model_dir = _stats_first_model_dir(tmp_path)
    _set_stats_first_normalized_season(model_dir, "12519", "2024")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    production_bucket = _bucket_row(report.bucket_rows, "Luther Burden", "production")
    player = _player_row(report.player_rows, "Luther Burden")

    assert production_bucket["bucket_status"] == "review"
    assert production_bucket["coverage_class"] == "critical"
    assert production_bucket["decision_effect"] == "blocks_decision_trust"
    assert "production" in str(player["critical_review_inputs"])


def test_stats_first_warning_marks_injury_as_optional_review_gap(
    tmp_path: Path,
) -> None:
    model_dir = _stats_first_model_dir(tmp_path)
    _set_stats_first_normalized_warnings(
        model_dir,
        "12519",
        "missing_lve_scoring_history|no_injury_report_rows",
    )

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    injury_bucket = _bucket_row(report.bucket_rows, "Luther Burden", "injury")
    injury_feature = _feature_row(report.feature_rows, "Luther Burden", "injury")

    assert injury_feature["feature_data_status"] == "estimated_or_proxy"
    assert injury_bucket["bucket_status"] == "review"
    assert injury_bucket["coverage_class"] == "review"
    assert injury_bucket["decision_effect"] == "confidence_penalty_review_needed"


def test_source_gap_summary_splits_draft_critical_from_roster_critical(
    tmp_path: Path,
) -> None:
    model_dir = _stats_first_model_dir(tmp_path)
    _set_player_team(model_dir, "old_wr", "")

    report = build_source_coverage_audit(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
    )

    old_production = _bucket_row(report.bucket_rows, "Old Missing WR", "production")
    summaries = {
        str(row["source_gap_scope"]): row
        for row in report.summary_rows
        if row["summary_type"] == "source_gap_scope"
    }

    assert old_production["source_gap_scope"] == "draft-critical"
    assert old_production["source_gap_summary"] == "not enough for draft"
    assert "draft-critical" in summaries
    assert summaries["draft-critical"]["source_gap_summary"] == "not enough for draft"


def _fixture_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "veteran_model_v1"
    shutil.copytree(Path("sample_data/veteran_model_v1"), model_dir)
    _write_identity_review(model_dir, "Lamar Jackson", "QB")
    return model_dir


def _stats_first_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "stats_first_model"
    model_dir.mkdir()
    _write_rows(
        model_dir / "veteran_player_inputs.csv",
        [
            {
                "season": "2026",
                "snapshot_date": "2026-pre-draft",
                "player_id": "12519",
                "player_name": "Luther Burden",
                "position": "WR",
                "nfl_team": "CHI",
                "age": "22.4",
                "team_id": "niners",
                "team_name": "Niners",
                "league_rank": "56",
                "is_league_rank_top5": "true",
                "source_snapshot_id": "test",
                "source_name": "test",
                "source_date": "2026-05-08",
                "data_quality_tier": "partial",
            },
            {
                "season": "2026",
                "snapshot_date": "2026-pre-draft",
                "player_id": "old_wr",
                "player_name": "Old Missing WR",
                "position": "WR",
                "nfl_team": "CHI",
                "age": "29.0",
                "team_id": "niners",
                "team_name": "Niners",
                "league_rank": "156",
                "is_league_rank_top5": "false",
                "source_snapshot_id": "test",
                "source_name": "test",
                "source_date": "2026-05-08",
                "data_quality_tier": "partial",
            },
        ],
    )
    _write_rows(
        model_dir / "stats_first_normalized_features.csv",
        [
            _stats_first_normalized_row(
                player_id="00-0040735",
                sleeper_id="12519",
                player_name="Luther Burden",
                young_weight="0.35",
                young_prior="82",
            ),
            _stats_first_normalized_row(
                player_id="old_wr",
                sleeper_id="old_wr",
                player_name="Old Missing WR",
                young_weight="",
                young_prior="",
            ),
        ],
    )
    _write_rows(
        model_dir / "stats_first_source_coverage.csv",
        [
            _stats_first_coverage_row(
                player_id="00-0040735",
                player_name="Luther Burden",
            ),
            _stats_first_coverage_row(
                player_id="old_wr",
                player_name="Old Missing WR",
            ),
        ],
    )
    return model_dir


def _stats_first_normalized_row(
    *,
    player_id: str,
    sleeper_id: str,
    player_name: str,
    young_weight: str,
    young_prior: str,
) -> dict[str, str]:
    return {
        "season": "2025",
        "as_of_week": "",
        "player_id": player_id,
        "gsis_id": player_id,
        "sleeper_id": sleeper_id,
        "player_name": player_name,
        "position": "WR",
        "team": "CHI",
        "weighted_recent_lve_ppg_score": "50",
        "expected_lve_points_score": "50",
        "lve_projection_value": "50",
        "role_security": "25",
        "workload_earning": "0",
        "target_earning_stability": "0",
        "route_role": "0",
        "efficiency_score": "50",
        "first_down_td_fit": "50",
        "age_curve": "90",
        "injury_durability": "100",
        "private_stat_value": "40",
        "market_liquidity": "",
        "confidence": "52",
        "missing_data_penalty": "16",
        "warnings": "missing_lve_scoring_history|missing_projection_features",
        "source_version": "fixture",
        "computed_at": "2026-05-08T00:00:00Z",
        "experience_bucket": "year_one_nfl_player" if young_weight else "established_veteran",
        "young_nfl_bridge_prior_score": young_prior,
        "young_nfl_bridge_weight": young_weight,
        "young_nfl_bridge_source": "draft_capital_prior" if young_weight else "",
    }


def _stats_first_coverage_row(
    *,
    player_id: str,
    player_name: str,
) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "WR",
        "team": "CHI",
        "production": "review_missing",
        "role_usage": "review",
        "projection": "review_missing",
        "injury": "ready",
        "age_bio": "ready",
        "market_liquidity": "review_missing",
        "critical_missing_buckets": "production",
        "review_missing_buckets": "projection|market/liquidity",
        "confidence": "52",
        "decision_effect": "blocks_decision_ready",
    }


def _set_stats_first_normalized_warnings(
    model_dir: Path,
    sleeper_id: str,
    warnings: str,
) -> None:
    path = model_dir / "stats_first_normalized_features.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["sleeper_id"] == sleeper_id:
            row["warnings"] = warnings
    _write_rows(path, rows)


def _set_stats_first_normalized_season(
    model_dir: Path,
    sleeper_id: str,
    season: str,
) -> None:
    path = model_dir / "stats_first_normalized_features.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["sleeper_id"] == sleeper_id:
            row["season"] = season
            row["warnings"] = ""
    _write_rows(path, rows)


def _set_player_team(model_dir: Path, player_id: str, team_name: str) -> None:
    path = model_dir / "veteran_player_inputs.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["player_id"] == player_id:
            row["team_name"] = team_name
    _write_rows(path, rows)


def _mark_feature_missing(model_dir: Path, player_id: str, feature_name: str) -> None:
    path = model_dir / "veteran_feature_scores.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["player_id"] == player_id and row["feature_name"] == feature_name:
            row["normalized_score"] = ""
            row["is_missing"] = "true"
            row["missing_reason"] = "missing_projection_fixture"
    _write_rows(path, rows)


def _set_source_confidence(
    model_dir: Path,
    player_id: str,
    feature_name: str,
    source_confidence: str,
) -> None:
    path = model_dir / "veteran_feature_scores.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["player_id"] == player_id and row["feature_name"] == feature_name:
            row["source_confidence"] = source_confidence
    _write_rows(path, rows)


def _write_identity_review(model_dir: Path, player_name: str, position: str) -> None:
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


def _write_gap_acceptance(model_dir: Path, player_id: str, bucket: str) -> None:
    rows = [
        {
            "player_id": player_id,
            "bucket": bucket,
            "gap_type": "missing_optional_source",
            "review_status": "accepted",
            "accepted_reason": "Temporary accepted gap for test fixture.",
            "confidence_penalty_retained": "true",
            "reviewed_by": "test",
            "reviewed_at": "2026-05-08T00:00:00-06:00",
        }
    ]
    _write_rows(model_dir / "source_coverage_gap_acceptances.csv", rows)


def _player_row(rows: list[dict[str, object]], player: str) -> dict[str, object]:
    matches = [row for row in rows if row["player"] == player]
    assert matches
    return matches[0]


def _bucket_row(
    rows: list[dict[str, object]],
    player: str,
    bucket: str,
) -> dict[str, object]:
    matches = [row for row in rows if row["player"] == player and row["bucket"] == bucket]
    assert matches
    return matches[0]


def _feature_row(
    rows: list[dict[str, object]],
    player: str,
    bucket: str,
) -> dict[str, object]:
    matches = [row for row in rows if row["player"] == player and row["bucket"] == bucket]
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
