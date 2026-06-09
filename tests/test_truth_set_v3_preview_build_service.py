from __future__ import annotations

import csv
from pathlib import Path

from src.services.lve_normalization_service import NORMALIZED_FEATURE_HEADER
from src.services.truth_set_v3_preview_build_service import build_truth_set_v3_model_preview


def test_v3_preview_uses_structured_free_data_and_rejects_unsafe_sources(
    tmp_path: Path,
) -> None:
    active_output = tmp_path / "active_outputs.csv"
    active_normalized = tmp_path / "active_normalized.csv"
    v2_output = tmp_path / "v2_outputs.csv"
    production = tmp_path / "production.csv"
    usage = tmp_path / "usage.csv"
    snaps = tmp_path / "snaps.csv"
    projections = tmp_path / "projections.csv"
    bridge = tmp_path / "bridge.csv"
    injury = tmp_path / "injury.csv"
    market = tmp_path / "market.csv"
    route = tmp_path / "route.csv"

    _write(active_output, [_active_output("Young WR", "60")])
    _write(active_normalized, [_feature_row("Young WR", "WR")], list(NORMALIZED_FEATURE_HEADER))
    _write(v2_output, [_active_output("Young WR", "60")])
    _write(
        production,
        [
            _production_row(
                "Young WR",
                "WR",
                season="2024",
                games="17",
                targets="140",
                receiving_yards="1400",
                receiving_tds="9",
                receiving_first_downs="72",
            )
        ],
    )
    _write(
        usage,
        [
            {
                "truth_set_player_name": "Young WR",
                "matched_player_name": "Young WR",
                "player_id": "young_wr",
                "season": "2024",
                "games_with_usage": "17",
                "team": "TST",
                "position": "WR",
                "targets": "140",
                "team_targets": "560",
                "target_share": "0.25",
                "rb_target_share": "",
                "rushing_attempts": "4",
                "team_rushing_attempts": "430",
                "rb_carry_share": "",
                "weighted_opportunities": "170",
                "red_zone_carries": "1",
                "red_zone_targets": "20",
                "goal_line_carries": "0",
                "goal_line_targets": "5",
                "short_yardage_carries": "0",
            }
        ],
    )
    _write(
        snaps,
        [
            {
                "truth_set_player_name": "Young WR",
                "matched_player_name": "Young WR",
                "player_id": "young_wr",
                "season": "2024",
                "games": "17",
                "games_with_offensive_snaps": "17",
                "team": "TST",
                "position": "WR",
                "offense_snaps": "900",
                "avg_offense_pct": "0.86",
                "avg_snap_share": "0.86",
            }
        ],
    )
    _write(
        projections,
        [
            {
                "player_name": "Young WR",
                "position": "WR",
                "projection_availability_status": "projection_stat_line_present",
                "recomputed_lve_points": "185",
                "projection_source_quality_flags": "missing_first_down_projection",
            }
        ],
    )
    _write(
        bridge,
        [
            {
                "player_name": "Young WR",
                "asset_lifecycle": "year_two_nfl_bridge",
                "draft_year": "2024",
                "nfl_draft_round": "1",
                "nfl_draft_pick": "20",
                "draft_capital_prior_score": "90",
                "draft_capital_source_status": "derived_from_round_pick",
            }
        ],
    )
    _write(injury, [{"player_name": "Young WR", "current_injury": "", "source_url": ""}])
    _write(market, [{"player_name": "Young WR", "trade_value_number": "200"}])
    _write(
        route,
        [
            {
                "player_name": "Young WR",
                "position": "WR",
                "route_source_status": "unavailable_free_public",
            }
        ],
    )

    result = build_truth_set_v3_model_preview(
        active_output_path=active_output,
        active_normalized_path=active_normalized,
        v2_output_path=v2_output,
        production_season_path=production,
        usage_season_path=usage,
        snap_share_season_path=snaps,
        projection_recompute_path=projections,
        young_bridge_path=bridge,
        injury_path=injury,
        market_path=market,
        route_honesty_path=route,
        output_root=tmp_path / "previews",
        preview_id="v3_preview_test",
        computed_at="2026-05-15T00:00:00Z",
    )

    normalized_rows = _read(result.normalized_path)
    rejected_rows = _read(result.rejected_field_log_path)
    coverage_rows = _read(result.source_coverage_path)

    assert result.summary["review_status"] == "review_only"
    assert result.summary["active_outputs_overwritten"] is False
    assert normalized_rows[0]["route_role"] == "50.0"
    assert "route_data_unavailable_free_public" in normalized_rows[0]["warnings"]
    assert normalized_rows[0]["projection_source_status"] == "truth_set_v3_projection_recompute"
    assert normalized_rows[0]["weighted_recent_lve_ppg_score"] != "50"
    assert {
        "rejected_agent_production_csv",
        "rejected_agent_role_usage_csv",
        "supplied_non_lve_projection_points",
        "fake_route_values",
    }.issubset({row["field_group"] for row in rejected_rows})
    assert any(
        row["bucket"] == "route_participation"
        and row["source_status"] == "unavailable_free_public"
        and row["model_usage"] == "not_used"
        for row in coverage_rows
    )


def test_v3_preview_does_not_apply_unsourced_injury_as_health_boost(tmp_path: Path) -> None:
    paths = _minimal_paths(tmp_path, "Context RB", "RB")
    _write(paths["injury"], [{"player_name": "Context RB", "current_injury": "", "source_url": ""}])

    result = build_truth_set_v3_model_preview(
        active_output_path=paths["active_output"],
        active_normalized_path=paths["active_normalized"],
        v2_output_path=paths["v2_output"],
        production_season_path=paths["production"],
        usage_season_path=paths["usage"],
        snap_share_season_path=paths["snaps"],
        projection_recompute_path=paths["projections"],
        young_bridge_path=paths["bridge"],
        injury_path=paths["injury"],
        market_path=paths["market"],
        route_honesty_path=paths["route"],
        output_root=tmp_path / "previews",
        preview_id="v3_unsourced_injury",
        computed_at="2026-05-15T00:00:00Z",
    )

    coverage_rows = _read(result.source_coverage_path)
    normalized_rows = _read(result.normalized_path)

    assert any(
        row["bucket"] == "injury" and row["source_status"] == "unsourced_or_healthy_context"
        for row in coverage_rows
    )
    assert "v3_sourced_injury_context" not in normalized_rows[0]["warnings"]
    assert "route_data_unavailable_free_public" not in normalized_rows[0]["warnings"]
    assert any(
        row["bucket"] == "route_participation"
        and row["coverage_status"] == "not_applicable"
        for row in coverage_rows
    )


def _minimal_paths(tmp_path: Path, player: str, position: str) -> dict[str, Path]:
    paths = {
        "active_output": tmp_path / "active_outputs.csv",
        "active_normalized": tmp_path / "active_normalized.csv",
        "v2_output": tmp_path / "v2_outputs.csv",
        "production": tmp_path / "production.csv",
        "usage": tmp_path / "usage.csv",
        "snaps": tmp_path / "snaps.csv",
        "projections": tmp_path / "projections.csv",
        "bridge": tmp_path / "bridge.csv",
        "injury": tmp_path / "injury.csv",
        "market": tmp_path / "market.csv",
        "route": tmp_path / "route.csv",
    }
    _write(paths["active_output"], [_active_output(player, "60")])
    _write(
        paths["active_normalized"],
        [_feature_row(player, position)],
        list(NORMALIZED_FEATURE_HEADER),
    )
    _write(paths["v2_output"], [_active_output(player, "60")])
    _write(paths["production"], [_production_row(player, position)])
    _write(
        paths["usage"],
        [
            {
                "truth_set_player_name": player,
                "position": position,
                "season": "2024",
                "games_with_usage": "17",
                "targets": "25",
                "team_targets": "500",
                "target_share": "0.05",
                "rb_target_share": "0.07" if position == "RB" else "",
                "rushing_attempts": "120" if position == "RB" else "0",
                "team_rushing_attempts": "400",
                "rb_carry_share": "0.3" if position == "RB" else "",
                "weighted_opportunities": "140",
            }
        ],
    )
    _write(
        paths["snaps"],
        [
            {
                "truth_set_player_name": player,
                "position": position,
                "season": "2024",
                "games": "17",
                "avg_snap_share": "0.55",
            }
        ],
    )
    _write(
        paths["projections"],
        [
            {
                "player_name": player,
                "position": position,
                "projection_availability_status": "projection_stat_line_present",
                "recomputed_lve_points": "100",
                "projection_source_quality_flags": "",
            }
        ],
    )
    _write(paths["bridge"], [])
    _write(paths["injury"], [])
    _write(paths["market"], [])
    _write(
        paths["route"],
        [
            {
                "player_name": player,
                "position": position,
                "route_source_status": "unavailable_free_public",
            }
        ],
    )
    return paths


def _active_output(player: str, value: str) -> dict[str, str]:
    return {
        "player_name": player,
        "overall_rank": "1",
        "private_lve_value": value,
        "keeper_score": value,
        "trade_value": value,
        "confidence_score": "70",
    }


def _feature_row(player: str, position: str) -> dict[str, object]:
    row = {field: "" for field in NORMALIZED_FEATURE_HEADER}
    row.update(
        {
            "season": "2025",
            "player_id": player.lower().replace(" ", "_"),
            "gsis_id": player.lower().replace(" ", "_"),
            "player_name": player,
            "position": position,
            "team": "TST",
            "weighted_recent_lve_ppg_score": 50,
            "expected_lve_points_score": 50,
            "lve_projection_value": 50,
            "projection_source_status": "local_baseline_projection",
            "role_security": 50,
            "workload_earning": 50,
            "target_earning_stability": 50,
            "route_role": 75,
            "efficiency_score": 50,
            "first_down_td_fit": 50,
            "age_curve": 80,
            "age_raw": 24,
            "age_bucket": "prime_window",
            "age_source_status": "derived_real_data",
            "injury_durability": 75,
            "market_liquidity": "",
            "confidence": 80,
            "missing_data_penalty": 0,
            "warnings": "local_baseline_projection_not_independent",
            "source_version": "test",
            "computed_at": "2026-05-15T00:00:00Z",
            "experience_bucket": "established_veteran",
        }
    )
    return row


def _production_row(
    player: str,
    position: str,
    *,
    season: str = "2024",
    games: str = "17",
    targets: str = "20",
    receiving_yards: str = "200",
    receiving_tds: str = "1",
    receiving_first_downs: str = "10",
) -> dict[str, str]:
    return {
        "truth_set_player_name": player,
        "matched_player_name": player,
        "player_id": player.lower().replace(" ", "_"),
        "season": season,
        "games": games,
        "team": "TST",
        "position": position,
        "passing_yards": "0",
        "passing_tds": "0",
        "interceptions": "0",
        "rushing_attempts": "100" if position == "RB" else "0",
        "rushing_yards": "500" if position == "RB" else "0",
        "rushing_tds": "4" if position == "RB" else "0",
        "targets": targets,
        "receptions": "10",
        "receiving_yards": receiving_yards,
        "receiving_tds": receiving_tds,
        "rushing_first_downs": "30" if position == "RB" else "0",
        "receiving_first_downs": receiving_first_downs,
        "fumbles_lost": "0",
    }


def _write(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    resolved = fieldnames or sorted({key for row in rows for key in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=resolved, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
