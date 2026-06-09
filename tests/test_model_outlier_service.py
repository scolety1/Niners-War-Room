from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.model_outlier_service import (
    BUCKET_IDENTITY_ISSUE,
    BUCKET_MISSING_INJURY_PROJECTION,
    BUCKET_MISSING_MARKET_REFERENCE,
    BUCKET_ONE_FEATURE_DRIVEN,
    BUCKET_ONTO_SOMETHING,
    BUCKET_TRUE_RANKING_WEIRDNESS,
    OUTLIER_IDENTITY_AMBIGUITY,
    OUTLIER_IMPUTED_CORE,
    OUTLIER_MARKET_MODEL_GAP,
    OUTLIER_MARKET_REFERENCE_GAP,
    OUTLIER_ONE_FEATURE_DRIVEN,
    OUTLIER_STALE_SOURCE,
    OUTLIER_TOP3_LOW_CONFIDENCE,
    _identity_ambiguity_rows,
    _market_model_gap_rows,
    _stale_source_bucket,
    build_model_outlier_report,
)


def test_outlier_detector_flags_huge_market_model_gap(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _append_player(model_dir, "market_gap_fixture", "Market Gap Fixture", "WR")
    _append_features(
        model_dir,
        "market_gap_fixture",
        "WR",
        {
            "lve_projection_value": 96,
            "role_security": 94,
            "age_curve": 90,
            "target_earning_stability": 94,
            "market_liquidity": 35,
        },
    )

    report = build_model_outlier_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
        as_of_date="2026-05-07",
    )

    row = _player_outlier(report.rows, "Market Gap Fixture", OUTLIER_MARKET_MODEL_GAP)
    assert row["bucket"] == BUCKET_ONTO_SOMETHING
    assert "private minus trade liquidity" in row["reason"]


def test_market_model_gap_is_review_signal_not_blocker_when_sources_are_unclean() -> None:
    rows = _market_model_gap_rows(
        {
            "gap_review_fixture": {
                "player_id": "gap_review_fixture",
                "player": "Gap Review Fixture",
                "position": "WR",
                "team": "Fixture Team",
                "model_rank": 12,
                "position_rank": 8,
                "private_rank": 10,
                "market_rank": 75,
                "war_score": 88.0,
                "private_score": 90.0,
                "trade_liquidity": 58.0,
                "keeper_score": 87.0,
                "confidence_score": 64.0,
                "warning_status": "review_needed",
                "warning_reasons": "missing_projection",
                "model_version": "test",
            }
        }
    )

    assert rows
    assert rows[0]["bucket"] == BUCKET_MISSING_INJURY_PROJECTION
    assert rows[0]["severity"] == "medium"
    assert rows[0]["review_status"] == "needs_injury_projection_source"
    assert rows[0]["next_action"]
    assert "market-edge lead" in rows[0]["suggested_review"]


def test_market_model_gap_with_football_risk_can_be_edge_signal() -> None:
    rows = _market_model_gap_rows(
        {
            "injury_edge_fixture": {
                "player_id": "injury_edge_fixture",
                "player": "Injury Edge Fixture",
                "position": "RB",
                "team": "Fixture Team",
                "model_rank": 40,
                "position_rank": 12,
                "private_rank": 38,
                "market_rank": 92,
                "war_score": 82.0,
                "private_score": 85.0,
                "trade_liquidity": 62.0,
                "keeper_score": 81.0,
                "confidence_score": 84.0,
                "warning_status": "model_warning",
                "warning_reasons": "injury_risk|committee_risk",
                "model_version": "test",
            }
        }
    )

    assert rows
    assert rows[0]["bucket"] == BUCKET_ONTO_SOMETHING


def test_market_model_gap_ignores_deep_rank_noise() -> None:
    rows = _market_model_gap_rows(
        {
            "deep_noise_fixture": {
                "player_id": "deep_noise_fixture",
                "player": "Deep Noise Fixture",
                "position": "WR",
                "team": "Fixture Team",
                "model_rank": 214,
                "position_rank": 91,
                "private_rank": 210,
                "market_rank": 279,
                "war_score": 48.0,
                "private_score": 51.0,
                "trade_liquidity": 37.0,
                "keeper_score": 49.0,
                "confidence_score": 82.0,
                "warning_status": "ready",
                "warning_reasons": "",
                "model_version": "test",
            }
        }
    )

    assert rows == []


def test_neutral_market_reference_is_not_treated_as_real_market_gap() -> None:
    rows = _market_model_gap_rows(
        {
            "neutral_market_fixture": {
                "player_id": "neutral_market_fixture",
                "player": "Neutral Market Fixture",
                "position": "RB",
                "team": "Fixture Team",
                "model_rank": 20,
                "position_rank": 3,
                "private_rank": 8,
                "market_rank": 175,
                "war_score": 86.0,
                "private_score": 92.0,
                "trade_liquidity": 50.0,
                "keeper_score": 88.0,
                "confidence_score": 88.0,
                "warning_status": "ready",
                "warning_reasons": "",
                "model_version": "test",
            }
        }
    )

    assert rows
    assert rows[0]["bucket"] == BUCKET_MISSING_MARKET_REFERENCE
    assert rows[0]["outlier_type"] == OUTLIER_MARKET_REFERENCE_GAP
    assert rows[0]["review_status"] == "needs_market_reference"
    assert "neutral/defaulted" in rows[0]["reason"]


def test_outlier_detector_flags_position_top3_low_confidence(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _append_player(model_dir, "low_confidence_star", "Low Confidence Star", "QB")
    _append_features(
        model_dir,
        "low_confidence_star",
        "QB",
        {
            "lve_projection_value": 99,
            "role_security": 99,
            "age_curve": 99,
            "market_liquidity": 99,
            "position_replaceability": 99,
            "start_security": 99,
            "passing_td_yardage_output": 99,
            "rushing_value": 99,
            "passing_efficiency_epa": 99,
            "sack_avoidance": 99,
            "current_injury_durability": 99,
            "team_commitment_contract": 99,
        },
        source_key="projection_fixture_2026",
        source_confidence="estimated",
    )
    _make_source_stale_and_weak(model_dir, "projection_fixture_2026")

    report = build_model_outlier_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
        as_of_date="2026-05-07",
    )

    row = _player_outlier(report.rows, "Low Confidence Star", OUTLIER_TOP3_LOW_CONFIDENCE)
    assert row["bucket"] == BUCKET_MISSING_INJURY_PROJECTION
    assert row["severity"] == "high"


def test_outlier_detector_flags_high_rank_driven_by_one_feature(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _append_player(model_dir, "one_feature_rb", "One Feature RB", "RB")
    _append_features(
        model_dir,
        "one_feature_rb",
        "RB",
        {
            "lve_projection_value": 90,
            "role_security": 88,
            "age_curve": 88,
            "first_down_td_fit": 100,
            "injury_durability": 80,
        },
    )

    report = build_model_outlier_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
        as_of_date="2026-05-07",
    )

    row = _player_outlier(report.rows, "One Feature RB", OUTLIER_ONE_FEATURE_DRIVEN)
    assert row["source_feature"] == "first_down_td_fit"
    assert row["bucket"] == BUCKET_ONE_FEATURE_DRIVEN
    assert row["component"] == "lve_format_fit"
    assert row["severity"] == "medium"


def test_outlier_detector_flags_missing_imputed_core_data(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _append_player(model_dir, "missing_core_rb", "Missing Core RB", "RB")
    _append_features(
        model_dir,
        "missing_core_rb",
        "RB",
        {
            "lve_projection_value": 90,
            "role_security": 84,
            "age_curve": 82,
            "first_down_td_fit": 88,
            "injury_durability": 82,
            "touch_share": 0,
        },
    )
    _mark_feature_missing(model_dir, "missing_core_rb", "touch_share", "missing_touch_share")

    report = build_model_outlier_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
        as_of_date="2026-05-07",
    )

    row = _player_outlier(report.rows, "Missing Core RB", OUTLIER_IMPUTED_CORE)
    assert row["bucket"] == BUCKET_TRUE_RANKING_WEIRDNESS
    assert "missing touch share" in row["reason"]


def test_outlier_detector_flags_stale_sources(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _make_source_stale_and_weak(model_dir, "projection_fixture_2026")

    report = build_model_outlier_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
        as_of_date="2026-05-07",
    )

    row = _first_outlier(report.rows, OUTLIER_STALE_SOURCE)
    assert row["bucket"] == BUCKET_MISSING_INJURY_PROJECTION
    assert "stale source data" in row["reason"]


def test_stale_market_sources_are_market_reference_review_not_ranking_weirdness() -> None:
    bucket = _stale_source_bucket(
        {
            "fantasycalc_dynastyprocess_market_20260505",
            "fantasycalc_dynastyprocess_replaceability_20260505",
            "sleeper_player_metadata_20260505",
        }
    )

    assert bucket == BUCKET_MISSING_MARKET_REFERENCE


def test_outlier_detector_flags_identity_ambiguity(tmp_path: Path) -> None:
    model_dir = _fixture_model_dir(tmp_path)
    _write_identity_review(model_dir, "lamar_jackson")

    report = build_model_outlier_report(
        "sample_data/2026_pre_declaration",
        veteran_model_dir=model_dir,
        as_of_date="2026-05-07",
    )

    row = _player_outlier(report.rows, "Lamar Jackson", OUTLIER_IDENTITY_AMBIGUITY)
    assert row["severity"] == "blocking"
    assert row["bucket"] == BUCKET_IDENTITY_ISSUE


def test_identity_ambiguity_is_medium_when_ranking_is_not_high_value(
    tmp_path: Path,
) -> None:
    data_pack = tmp_path / "data_pack"
    shutil.copytree(Path("sample_data/2026_pre_declaration"), data_pack)
    source_root = tmp_path / "identity_sources"
    source_root.mkdir()
    _write_empty_identity_bridge(source_root)
    _append_data_pack_identity_player(
        data_pack,
        player_id="low_identity_fixture",
        player_name="Low Identity Fixture",
        position="WR",
        war_score=72,
    )

    rows = _identity_ambiguity_rows(
        data_pack,
        source_root,
        {
            "low_identity_fixture": {
                "player_id": "low_identity_fixture",
                "player": "Low Identity Fixture",
                "position": "WR",
                "team": "Fixture Team",
                "model_rank": 140,
                "position_rank": 65,
                "private_rank": 130,
                "market_rank": 145,
                "war_score": 72.0,
                "private_score": 72.0,
                "trade_liquidity": 72.0,
                "keeper_score": 72.0,
                "confidence_score": 82.0,
                "warning_status": "ready",
                "warning_reasons": "",
                "risk_flags": "",
                "model_version": "test",
            }
        },
    )

    row = _player_outlier(rows, "Low Identity Fixture", OUTLIER_IDENTITY_AMBIGUITY)
    assert row["severity"] == "medium"
    assert row["bucket"] == BUCKET_IDENTITY_ISSUE


def _fixture_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "veteran_model_v1"
    shutil.copytree(Path("sample_data/veteran_model_v1"), model_dir)
    return model_dir


def _append_player(
    model_dir: Path,
    player_id: str,
    player_name: str,
    position: str,
) -> None:
    path = model_dir / "veteran_player_inputs.csv"
    rows = _read_rows(path)
    rows.append(
        {
            "season": "2026",
            "snapshot_date": "2026-05-05",
            "player_id": player_id,
            "player_name": player_name,
            "position": position,
            "nfl_team": "FA",
            "age": "24.0",
            "team_id": "fixture",
            "team_name": "Fixture Team",
            "league_rank": "99",
            "is_league_rank_top5": "false",
            "source_snapshot_id": "outlier_fixture",
            "source_name": "outlier_fixture",
            "source_date": "2026-05-05",
            "data_quality_tier": "verified",
        }
    )
    _write_rows(path, rows)


def _append_features(
    model_dir: Path,
    player_id: str,
    position: str,
    features: dict[str, float],
    *,
    source_key: str = "projection_fixture_2026",
    source_confidence: str = "derived",
) -> None:
    path = model_dir / "veteran_feature_scores.csv"
    rows = _read_rows(path)
    for feature_name, score in features.items():
        rows.append(
            {
                "season": "2026",
                "snapshot_date": "2026-05-05",
                "player_id": player_id,
                "position": position,
                "feature_name": feature_name,
                "normalized_score": str(score),
                "source_key": _source_key(feature_name, source_key),
                "source_confidence": source_confidence,
                "is_missing": "false",
                "missing_reason": "",
                "is_user_override": "false",
                "override_reason": "",
            }
        )
    _write_rows(path, rows)


def _source_key(feature_name: str, default: str) -> str:
    if feature_name == "market_liquidity":
        return "market_rank_fixture_2026"
    if "injury" in feature_name:
        return "injury_fixture_2026"
    if feature_name in {"age_curve", "position_replaceability"}:
        return "manual_fixture_2026"
    return default


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


def _make_source_stale_and_weak(model_dir: Path, source_key: str) -> None:
    path = model_dir / "veteran_source_catalog.csv"
    rows = _read_rows(path)
    for row in rows:
        if row["source_key"] == source_key:
            row["source_date"] = "2026-01-01"
            row["freshness_window_hours"] = "24"
            row["reliability_score"] = "20"
    _write_rows(path, rows)


def _write_identity_review(model_dir: Path, player_id: str) -> None:
    path = model_dir / "active_roster_identity_review.csv"
    rows = [
        {
            "sleeper_id": player_id,
            "player_name": "Lamar Jackson",
            "position": "QB",
            "sleeper_gsis_id": "",
            "bridge_gsis_id": "",
            "bridge_pfr_id": "",
            "bridge_name": "",
            "matched_gsis_id": "",
            "stat_player_name": "",
            "match_method": "name_fallback_ambiguous",
            "match_status": "review_needed",
            "manual_review_required": "true",
        }
    ]
    _write_rows(path, rows)


def _write_empty_identity_bridge(source_root: Path) -> None:
    path = source_root / "sleeper_nflverse_identity_bridge.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sleeper_id",
                "player_id",
                "player_name",
                "position",
                "sleeper_gsis_id",
                "bridge_gsis_id",
                "bridge_pfr_id",
                "bridge_name",
                "matched_gsis_id",
                "stat_player_name",
                "match_method",
                "match_status",
                "manual_review_required",
                "team",
            ],
        )
        writer.writeheader()


def _append_data_pack_identity_player(
    data_pack: Path,
    *,
    player_id: str,
    player_name: str,
    position: str,
    war_score: float,
) -> None:
    players_path = data_pack / "dim_players.csv"
    players = _read_rows(players_path)
    players.append(
        {
            "player_id": player_id,
            "player_name": player_name,
            "merge_name": player_name.lower().replace(" ", "_"),
            "position": position,
            "nfl_team": "FA",
            "birth_date": "",
            "rookie_year": "2021",
            "height_in": "",
            "weight_lb": "",
            "sleeper_id": player_id,
            "fantasypros_id": "",
            "ktc_id": "",
            "fantasycalc_id": "",
            "pfr_id": "",
            "cfb_id": "",
            "active_flag": "1",
            "created_at": "2026-08-01",
            "updated_at": "2026-08-01",
        }
    )
    _write_rows(players_path, players)

    outputs_path = data_pack / "model_outputs.csv"
    outputs = _read_rows(outputs_path)
    output_row = {field: "" for field in outputs[0]}
    output_row.update(
        {
            "snapshot_date": "2026-08-01",
            "player_id": player_id,
            "player_name": player_name,
            "position": position,
            "private_score": str(war_score),
            "market_score": str(war_score),
            "war_score": str(war_score),
            "keeper_score": str(war_score),
            "drop_candidate_score": "20",
            "confidence_score": "82",
            "risk_level": "low",
            "recommendation": "bubble",
            "notes": "",
        }
    )
    outputs.append(output_row)
    _write_rows(outputs_path, outputs)


def _player_outlier(
    rows: list[dict[str, object]],
    player: str,
    outlier_type: str,
) -> dict[str, object]:
    matches = [
        row
        for row in rows
        if row["player"] == player and row["outlier_type"] == outlier_type
    ]
    assert matches
    return matches[0]


def _first_outlier(rows: list[dict[str, object]], outlier_type: str) -> dict[str, object]:
    matches = [row for row in rows if row["outlier_type"] == outlier_type]
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
