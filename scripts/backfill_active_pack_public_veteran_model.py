from __future__ import annotations

import csv
import json
import math
import shutil
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.lve_scoring import LVE_SCORING  # noqa: E402
from src.data.csv_schemas import CSV_SCHEMAS  # noqa: E402
from src.services.lve_stats_first_veteran_formula_service import (  # noqa: E402
    StatsFirstVeteranScore,
    score_stats_first_veteran_rows,
    stats_first_output_rows,
)
from src.services.market_influence_policy_service import cap_market_blended_value  # noqa: E402

ACTIVE_PACK = REPO_ROOT / "local_exports" / "data_packs" / "lve_sleeper_20260505_pdf_ranks"
OUTPUT_DIR = REPO_ROOT / "local_exports" / "active_veteran_model_public_sources"
FANTASYCALC_URL = (
    "https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=1&ppr=0"
)
DYNASTYPROCESS_URL = (
    "https://raw.githubusercontent.com/dynastyprocess/data/master/files/values.csv"
)
DYNASTYPROCESS_PLAYER_IDS_URL = (
    "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
)
SLEEPER_PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
NFLVERSE_PLAYER_STATS_URL_TEMPLATE = (
    "https://github.com/nflverse/nflverse-data/releases/download/stats_player/"
    "stats_player_week_{season}.csv"
)
NFLVERSE_PLAYER_STATS_URL = NFLVERSE_PLAYER_STATS_URL_TEMPLATE.format(season="YYYY")
NFLVERSE_PLAYERS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
)
NFLVERSE_SNAP_COUNTS_URL_TEMPLATE = (
    "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/"
    "snap_counts_{season}.csv.gz"
)
NFLVERSE_INJURIES_URL_TEMPLATE = (
    "https://github.com/nflverse/nflverse-data/releases/download/injuries/"
    "injuries_{season}.csv"
)
SNAPSHOT_DATE = "2026-pre-draft"
SEASON = "2026"
NFLVERSE_LATEST_STATS_SEASON: int | None = None
STATS_FIRST_NORMALIZED_FEATURE_FILE = "stats_first_normalized_features.csv"
STATS_FIRST_CONTRIBUTION_FILE = "stats_first_feature_contributions.csv"

FEATURES_BY_POSITION = {
    "QB": (
        "lve_projection_value",
        "role_security",
        "age_curve",
        "market_liquidity",
        "position_replaceability",
    ),
    "RB": (
        "lve_projection_value",
        "role_security",
        "age_curve",
        "first_down_td_fit",
        "injury_durability",
    ),
    "WR": (
        "lve_projection_value",
        "role_security",
        "age_curve",
        "target_earning_stability",
        "market_liquidity",
    ),
    "TE": (
        "lve_projection_value",
        "role_security",
        "age_curve",
        "route_share_stability",
        "position_replaceability",
    ),
}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    roster_rows = _read_csv(ACTIVE_PACK / "fact_rosters.csv")
    player_rows = _read_csv(ACTIVE_PACK / "dim_players.csv")
    players_by_id = {row["player_id"]: row for row in player_rows}
    fantasycalc = _fantasycalc_rows()
    dynastyprocess = _dynastyprocess_rows()
    sleeper_players = _sleeper_players()
    nflverse_profiles, identity_rows, injury_profiles = _nflverse_stat_profiles(sleeper_players)

    fc_by_sleeper = {
        str(row["player"].get("sleeperId")): row
        for row in fantasycalc
        if row.get("player", {}).get("sleeperId")
    }
    dp_by_name_pos = {
        (_slug(row["player"]), row["pos"]): row
        for row in dynastyprocess
        if row.get("player") and row.get("pos")
    }
    percentiles = _source_percentiles(fantasycalc, dynastyprocess)

    model_players = []
    feature_scores = []
    skipped_kickers = []
    for roster in roster_rows:
        position = roster["position"]
        player_id = roster["player_id"]
        if position == "K":
            skipped_kickers.append(roster)
            continue
        if position not in FEATURES_BY_POSITION:
            continue
        dim = players_by_id.get(player_id, {})
        sleeper = sleeper_players.get(player_id, {})
        fc = fc_by_sleeper.get(player_id)
        dp = dp_by_name_pos.get((_slug(roster["player_name"]), position))
        age = _age(roster, dim, sleeper, fc)
        model_players.append(
            {
                "season": SEASON,
                "snapshot_date": SNAPSHOT_DATE,
                "player_id": player_id,
                "player_name": roster["player_name"],
                "position": position,
                "nfl_team": roster.get("nfl_team") or sleeper.get("team") or "FA",
                "age": f"{age:.1f}" if age is not None else "",
                "team_id": roster.get("team_id", ""),
                "team_name": roster.get("team_name", ""),
                "league_rank": roster.get("league_rank", ""),
                "is_league_rank_top5": str(_is_top_five(roster_rows, roster)).lower(),
                "source_snapshot_id": "active_pack_stats_first_backfill_20260506",
                "source_name": "nflverse_sleeper_market_liquidity_public_backfill",
                "source_date": "2026-05-06",
                "data_quality_tier": "partial",
            }
        )
        for feature in FEATURES_BY_POSITION[position]:
            value, source_key, confidence, missing_reason = _feature_value(
                feature,
                position,
                player_id,
                roster["player_name"],
                age,
                fc,
                dp,
                sleeper,
                percentiles,
                nflverse_profiles.get(player_id),
                injury_profiles.get(player_id),
            )
            feature_scores.append(
                {
                    "season": SEASON,
                    "snapshot_date": SNAPSHOT_DATE,
                    "player_id": player_id,
                    "position": position,
                    "feature_name": feature,
                    "normalized_score": "" if value is None else f"{value:.1f}",
                    "source_key": source_key,
                    "source_confidence": confidence,
                    "is_missing": str(value is None).lower(),
                    "missing_reason": missing_reason,
                    "is_user_override": "false",
                    "override_reason": "",
                }
            )

    _write_model_input_dir(model_players, feature_scores)
    _write_identity_bridge(identity_rows, {row["player_id"] for row in roster_rows})
    computed_at = datetime.now(UTC).isoformat()
    stats_first_inputs = _stats_first_input_rows(
        model_players,
        feature_scores,
        nflverse_profiles,
        injury_profiles,
    )
    stats_first_scores = score_stats_first_veteran_rows(tuple(stats_first_inputs))
    stats_first_preview_rows = stats_first_output_rows(
        stats_first_scores,
        computed_at=computed_at,
    )
    normalized_path = OUTPUT_DIR / STATS_FIRST_NORMALIZED_FEATURE_FILE
    contribution_path = OUTPUT_DIR / STATS_FIRST_CONTRIBUTION_FILE
    _write_csv(
        normalized_path,
        tuple(stats_first_inputs[0].keys()) if stats_first_inputs else (),
        stats_first_inputs,
    )
    _write_csv(
        contribution_path,
        _stats_first_contribution_header(),
        _stats_first_contribution_rows(stats_first_scores),
    )
    generated_output = OUTPUT_DIR / "model_outputs_scored_non_k.csv"
    scored_rows = _live_model_output_rows_from_stats_first(stats_first_preview_rows)
    _write_csv(
        generated_output,
        CSV_SCHEMAS["model_outputs.csv"].all_columns,
        scored_rows,
    )
    final_rows = scored_rows + [_ignored_kicker_output(row) for row in skipped_kickers]
    model_output_path = ACTIVE_PACK / "model_outputs.csv"
    backup_path = ACTIVE_PACK / "model_outputs.placeholder_backup.csv"
    if not backup_path.exists():
        shutil.copy2(model_output_path, backup_path)
    _write_csv(model_output_path, CSV_SCHEMAS["model_outputs.csv"].all_columns, final_rows)
    _update_metadata_sources()
    print(f"Wrote {len(scored_rows)} scored rows and {len(skipped_kickers)} ignored kicker rows.")
    print(f"Updated {model_output_path}")
    print(f"Backed up placeholders at {backup_path}")
    return 0


def _stats_first_input_rows(
    player_rows: list[dict[str, object]],
    feature_rows: list[dict[str, object]],
    nflverse_profiles: dict[str, dict[str, float]],
    injury_profiles: dict[str, dict[str, float]],
) -> list[dict[str, object]]:
    feature_lookup = {
        (str(row["player_id"]), str(row["feature_name"])): row for row in feature_rows
    }
    rows: list[dict[str, object]] = []
    stale_stats = (
        NFLVERSE_LATEST_STATS_SEASON is not None
        and NFLVERSE_LATEST_STATS_SEASON < int(SEASON) - 1
    )
    for player in player_rows:
        player_id = str(player["player_id"])
        position = str(player["position"])
        profile = nflverse_profiles.get(player_id, {})
        warnings: set[str] = set()
        if stale_stats:
            warnings.add("data_warning_stale_sources")

        def value(
            feature_name: str,
            *,
            player_profile: dict[str, float] = profile,
            row_player_id: str = player_id,
        ) -> float | str:
            if feature_name in player_profile and player_profile[feature_name] is not None:
                return round(float(player_profile[feature_name]), 2)
            return _feature_score_value(feature_lookup, row_player_id, feature_name)

        lve_projection = value("lve_projection_value")
        role_security = value("role_security")
        age_curve = value("age_curve")
        injury = value("injury_durability")
        market = value("market_liquidity")
        first_down_td_fit = value("first_down_td_fit")
        target_earning = value("target_earning_stability")
        route_role = value("route_role")
        workload_earning = value("workload_earning")
        qb_rushing_profile = value("qb_rushing_profile")
        expected = value("expected_lve_points_score")
        weighted_ppg = value("weighted_recent_lve_ppg_score")
        efficiency = value("efficiency_score")

        if weighted_ppg == "":
            weighted_ppg = lve_projection
        if first_down_td_fit == "":
            first_down_td_fit = _avg_for_row(lve_projection, target_earning, role_security)
        if expected == "":
            expected = _expected_proxy(
                position,
                lve_projection,
                role_security,
                first_down_td_fit,
                target_earning,
            )
        if workload_earning == "":
            workload_earning = role_security if position == "RB" else ""
        if target_earning == "":
            target_earning = (
                _avg_for_row(role_security, lve_projection)
                if position in {"WR", "TE"}
                else ""
            )
        if route_role == "":
            route_role = role_security if position in {"WR", "TE"} else ""
        if qb_rushing_profile == "":
            qb_rushing_profile = first_down_td_fit if position == "QB" else ""
        if efficiency == "":
            efficiency = _avg_for_row(lve_projection, first_down_td_fit, target_earning)
        if injury == "":
            injury = _injury_score(
                position,
                {},
                _float_or_none(age_curve),
                injury_profiles.get(player_id),
            )
        if market == "":
            market = 50.0

        feature_values_by_name = {
            "weighted_recent_lve_ppg_score": weighted_ppg,
            "expected_lve_points_score": expected,
            "lve_projection_value": lve_projection,
            "role_security": role_security,
            "workload_earning": workload_earning,
            "target_earning_stability": target_earning,
            "route_role": route_role,
            "qb_rushing_profile": qb_rushing_profile,
            "first_down_td_fit": first_down_td_fit,
            "age_curve": age_curve,
            "injury_durability": injury,
        }
        required_features = _stats_first_required_features(position)
        missing_required = [
            feature
            for feature in required_features
            if _value_missing(feature_values_by_name.get(feature))
        ]
        if missing_required:
            warnings.add("data_warning_missing_inputs")
        if any(
            feature in missing_required
            for feature in ("lve_projection_value", "role_security")
        ):
            warnings.add("review_needed_missing_core_inputs")

        missing_penalty = min(25.0, len(missing_required) * 2.5)
        confidence = max(
            35.0,
            88.0
            - (len(missing_required) * 8.0)
            - (4.0 if stale_stats else 0.0)
            - (5.0 if not profile else 0.0),
        )
        rows.append(
            {
                "season": SEASON,
                "snapshot_date": SNAPSHOT_DATE,
                "player_id": player_id,
                "player_name": player["player_name"],
                "position": position,
                "team": player.get("nfl_team", ""),
                "weighted_recent_lve_ppg_score": _blank_or_round(weighted_ppg),
                "expected_lve_points_score": _blank_or_round(expected),
                "lve_projection_value": _blank_or_round(lve_projection),
                "role_security": _blank_or_round(role_security),
                "workload_earning": _blank_or_round(workload_earning),
                "target_earning_stability": _blank_or_round(target_earning),
                "route_role": _blank_or_round(route_role),
                "qb_rushing_profile": _blank_or_round(qb_rushing_profile),
                "first_down_td_fit": _blank_or_round(first_down_td_fit),
                "efficiency_score": _blank_or_round(efficiency),
                "age_curve": _blank_or_round(age_curve),
                "injury_durability": _blank_or_round(injury),
                "market_liquidity": _blank_or_round(market),
                "qb_replacement_level_baseline": 76.0,
                "rb_replacement_level_baseline": 72.0,
                "wr_replacement_level_baseline": 72.0,
                "te_replacement_level_baseline": 69.0,
                "confidence": round(confidence, 2),
                "missing_data_penalty": round(missing_penalty, 2),
                "warnings": "|".join(sorted(warnings)),
                "source_key": (
                    "nflverse_player_stats_recent_lve_20260506"
                    if profile
                    else "public_backfill_missing_nflverse_stats"
                ),
                "source_date": _nflverse_stats_source_date(),
                "source_file": NFLVERSE_PLAYER_STATS_URL if profile else "",
            }
        )
    return rows


def _feature_score_value(
    feature_lookup: dict[tuple[str, str], dict[str, object]],
    player_id: str,
    feature_name: str,
) -> float | str:
    row = feature_lookup.get((player_id, feature_name))
    if not row or str(row.get("is_missing") or "").lower() == "true":
        return ""
    value = str(row.get("normalized_score") or "")
    if not value:
        return ""
    try:
        return round(float(value), 2)
    except ValueError:
        return ""


def _stats_first_required_features(position: str) -> tuple[str, ...]:
    if position == "QB":
        return (
            "weighted_recent_lve_ppg_score",
            "expected_lve_points_score",
            "lve_projection_value",
            "role_security",
            "qb_rushing_profile",
            "age_curve",
        )
    if position == "RB":
        return (
            "weighted_recent_lve_ppg_score",
            "expected_lve_points_score",
            "lve_projection_value",
            "role_security",
            "workload_earning",
            "first_down_td_fit",
            "age_curve",
            "injury_durability",
        )
    if position == "WR":
        return (
            "weighted_recent_lve_ppg_score",
            "expected_lve_points_score",
            "lve_projection_value",
            "role_security",
            "target_earning_stability",
            "route_role",
            "age_curve",
        )
    if position == "TE":
        return (
            "weighted_recent_lve_ppg_score",
            "expected_lve_points_score",
            "lve_projection_value",
            "route_role",
            "target_earning_stability",
            "age_curve",
        )
    return ("lve_projection_value", "role_security", "age_curve")


def _expected_proxy(
    position: str,
    lve_projection: object,
    role_security: object,
    first_down_td_fit: object,
    target_earning: object,
) -> float | str:
    if position == "RB":
        return _avg_for_row(lve_projection, role_security, first_down_td_fit)
    if position in {"WR", "TE"}:
        return _avg_for_row(lve_projection, role_security, first_down_td_fit, target_earning)
    return _avg_for_row(lve_projection, role_security, first_down_td_fit)


def _avg_for_row(*values: object) -> float | str:
    present = [_float_or_none(value) for value in values]
    numbers = [value for value in present if value is not None]
    if not numbers:
        return ""
    return round(sum(numbers) / len(numbers), 2)


def _value_missing(value: object) -> bool:
    return value is None or str(value) == ""


def _float_or_none(value: object) -> float | None:
    try:
        text = str(value)
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _blank_or_round(value: object) -> float | str:
    number = _float_or_none(value)
    return "" if number is None else round(number, 2)


def _stats_first_contribution_header() -> tuple[str, ...]:
    return (
        "player_id",
        "player_name",
        "position",
        "component",
        "feature_name",
        "normalized_score",
        "feature_weight",
        "component_contribution",
        "model_version",
    )


def _stats_first_contribution_rows(
    scores: tuple[StatsFirstVeteranScore, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for score in scores:
        for contribution in score.contributions:
            rows.append(
                {
                    "player_id": contribution.player_id,
                    "player_name": score.player_name,
                    "position": score.position,
                    "component": contribution.component,
                    "feature_name": contribution.feature_name,
                    "normalized_score": contribution.normalized_score,
                    "feature_weight": contribution.feature_weight,
                    "component_contribution": contribution.component_contribution,
                    "model_version": score.model_version,
                }
            )
    return rows


def _live_model_output_rows_from_stats_first(
    preview_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    output_rows: list[dict[str, object]] = []
    for row in preview_rows:
        keeper = _model_float(row.get("keeper_score"))
        trade = _model_float(row.get("trade_value"))
        private = _model_float(row.get("private_lve_value"))
        market_trade_value = _model_float(row.get("market_trade_value"), trade)
        warning_status = str(row.get("warning_status") or "")
        risk_flags = str(row.get("risk_flags") or "")
        output_rows.append(
            {
                "snapshot_date": SNAPSHOT_DATE,
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "overall_rank": row.get("overall_rank", ""),
                "position_rank": row.get("position_rank", ""),
                "position_rank_label": row.get("position_rank_label", ""),
                "private_score": private,
                "market_score": market_trade_value,
                "war_score": cap_market_blended_value(
                    keeper,
                    (keeper * 0.70) + (trade * 0.30),
                ),
                "keeper_score": keeper,
                "drop_candidate_score": row.get("drop_candidate_score", ""),
                "veteran_base_value": private,
                "win_now_value": row.get("win_now_value", ""),
                "dynasty_hold_value": row.get("dynasty_hold_value", ""),
                "horizon_retention_score": row.get("horizon_retention_score", ""),
                "trade_value": trade,
                "market_trade_value": market_trade_value,
                "market_edge_score": row.get("market_edge_score", ""),
                "market_edge_label": row.get("market_edge_label", ""),
                "market_edge_warning": row.get("market_edge_warning", ""),
                "lve_format_fit": private,
                "structural_adjustment": row.get("structural_adjustment", ""),
                "cross_position_replacement_baseline": row.get(
                    "cross_position_replacement_baseline",
                    "",
                ),
                "lve_lineup_demand_adjustment": row.get(
                    "lve_lineup_demand_adjustment",
                    "",
                ),
                "league_rank_signal": 0,
                "top_five_release_pressure": 0,
                "league_rank_adjustment": 0,
                "missing_data_penalty": "",
                "risk_flags": risk_flags,
                "upside_flags": row.get("upside_flags", ""),
                "floor_flags": row.get("floor_flags", ""),
                "pick_adjusted_value": round(trade * 10, 1),
                "confidence_score": row.get("confidence_score", ""),
                "risk_level": _model_risk_level(warning_status, risk_flags),
                "warning_status": warning_status,
                "warning_reasons": row.get("warning_reasons", ""),
                "recommendation": _model_recommendation(
                    _model_float(row.get("drop_candidate_score")),
                    keeper,
                ),
                "model_version": row.get("model_version", ""),
                "computed_at": row.get("computed_at", ""),
                "rank_audit": row.get("rank_audit", ""),
                "notes": (
                    "Active public backfill uses the stats-first veteran engine. "
                    "Private score is football-stat driven; market_score is trade liquidity. "
                    "Rankings remain review-only while calibration gates are blocked."
                ),
            }
        )
    return output_rows


def _model_risk_level(warning_status: str, risk_flags: str) -> str:
    if warning_status in {"blocking", "review_needed"}:
        return "high"
    if risk_flags:
        return "medium"
    return "low"


def _model_recommendation(drop_score: float, keeper_score: float) -> str:
    if drop_score >= 55:
        return "shop/release"
    if drop_score >= 35:
        return "shop"
    if keeper_score >= 82:
        return "keep"
    return "bubble"


def _model_float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _feature_value(
    feature: str,
    position: str,
    player_id: str,
    player_name: str,
    age: float | None,
    fc: dict | None,
    dp: dict | None,
    sleeper: dict,
    percentiles: dict[str, dict[tuple[str, str], float]],
    nflverse: dict[str, float] | None,
    injury_profile: dict[str, float] | None,
) -> tuple[float | None, str, str, str]:
    fc_dynasty = percentiles["fc_dynasty"].get((position, player_id))
    fc_redraft = percentiles["fc_redraft"].get((position, player_id))
    dp_market = percentiles["dp_market"].get((position, _slug(player_name)))
    market = _avg_present(fc_dynasty, dp_market)
    projection = (nflverse or {}).get("lve_projection_value")
    role = (nflverse or {}).get("role_security")
    age_score = _age_curve(position, age)
    injury = _injury_score(position, sleeper, age_score, injury_profile)
    stat_source_missing = nflverse is None
    gap_fill_projection = _avg_present(fc_redraft, market)
    gap_fill_role = _avg_present(fc_redraft, market, _active_bonus(sleeper))

    if feature == "lve_projection_value":
        if projection is not None:
            return _feature_tuple(
                projection,
                "nflverse_player_stats_recent_lve_20260506",
                "verified",
            )
        return _gap_fill_tuple(
            gap_fill_projection,
            "fantasycalc_redraft_value_20260505",
            stat_source_missing,
        )
    if feature == "role_security":
        if role is not None:
            return _feature_tuple(role, "nflverse_role_stats_recent_20260506", "derived")
        return _gap_fill_tuple(
            gap_fill_role,
            "fantasycalc_dynastyprocess_role_proxy_20260505",
            stat_source_missing,
        )
    if feature == "age_curve":
        return _feature_tuple(age_score, "sleeper_player_metadata_20260505", "derived")
    if feature == "market_liquidity":
        return _feature_tuple(market, "fantasycalc_dynastyprocess_market_20260505", "derived")
    if feature == "injury_durability":
        source_key = (
            "nflverse_sleeper_injury_durability_20260506"
            if injury_profile
            else "sleeper_injury_metadata_20260505"
        )
        confidence = "derived" if injury_profile else "estimated"
        return _feature_tuple(injury, source_key, confidence)
    if feature == "first_down_td_fit":
        value = (nflverse or {}).get("first_down_td_fit")
        if value is not None:
            return _feature_tuple(value, "nflverse_first_down_td_fit_20260506", "derived")
        return _gap_fill_tuple(
            _avg_present(gap_fill_projection, gap_fill_role, age_score),
            "fantasycalc_lve_role_proxy_20260505",
            stat_source_missing,
        )
    if feature == "target_earning_stability":
        value = (nflverse or {}).get("target_earning_stability")
        if value is not None:
            return _feature_tuple(value, "nflverse_role_stats_recent_20260506", "derived")
        return _gap_fill_tuple(
            _avg_present(gap_fill_projection, age_score),
            "fantasycalc_dynastyprocess_wr_proxy_20260505",
            stat_source_missing,
        )
    if feature == "route_share_stability":
        value = (nflverse or {}).get("route_share_stability")
        if value is not None:
            return _feature_tuple(value, "nflverse_role_stats_recent_20260506", "derived")
        return _gap_fill_tuple(
            _avg_present(gap_fill_projection, age_score),
            "fantasycalc_dynastyprocess_te_proxy_20260505",
            stat_source_missing,
        )
    if feature == "position_replaceability":
        value = _replaceability_score(position, fc, dp, market)
        return _feature_tuple(
            value,
            "fantasycalc_dynastyprocess_replaceability_20260505",
            "estimated",
        )
    return None, "public_backfill_missing", "estimated", "unsupported feature"


def _feature_tuple(
    value: float | None,
    source_key: str,
    confidence: str,
) -> tuple[float | None, str, str, str]:
    if value is None:
        return None, source_key, confidence, "public source did not cover this player"
    return _clamp(value), source_key, confidence, ""


def _gap_fill_tuple(
    value: float | None,
    source_key: str,
    stat_source_missing: bool,
) -> tuple[float | None, str, str, str]:
    if stat_source_missing:
        return (
            None,
            source_key,
            "estimated",
            (
                "nflverse player-stat coverage missing for this player; no market "
                "gap-fill applied to private football value"
            ),
        )
    if value is None:
        return (
            None,
            source_key,
            "estimated",
            "no football-stat or gap-fill source covered this player",
        )
    return _clamp(value), source_key, "estimated", ""


def _write_model_input_dir(
    player_rows: list[dict[str, object]],
    feature_rows: list[dict[str, object]],
) -> None:
    shutil.copy2(
        REPO_ROOT / "sample_data" / "veteran_model_v1" / "veteran_feature_registry.csv",
        OUTPUT_DIR / "veteran_feature_registry.csv",
    )
    for file_name in ("veteran_manual_overrides.csv", "veteran_audit_notes.csv"):
        sample_path = REPO_ROOT / "sample_data" / "veteran_model_v1" / file_name
        rows: list[dict[str, object]] = []
        if file_name == "veteran_audit_notes.csv" and player_rows:
            rows.append(
                {
                    "note_id": "note_active_public_backfill_01",
                    "season": SEASON,
                    "player_id": player_rows[0]["player_id"],
                    "feature_name": "lve_projection_value",
                    "note_scope": "source",
                    "note_text": (
                        "Active-pack veteran scores now prefer nflverse football stats for "
                        "private value. Market data is used for trade liquidity only. If "
                        "public NFL stat history is unavailable, private football features "
                        "stay missing instead of being market-filled."
                    ),
                    "source_key": "nflverse_player_stats_recent_lve_20260506",
                    "affects_score": "false",
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        _write_csv(OUTPUT_DIR / file_name, _read_header(sample_path), rows)
    _write_csv(
        OUTPUT_DIR / "veteran_player_inputs.csv",
        (
            "season",
            "snapshot_date",
            "player_id",
            "player_name",
            "position",
            "nfl_team",
            "age",
            "team_id",
            "team_name",
            "league_rank",
            "is_league_rank_top5",
            "source_snapshot_id",
            "source_name",
            "source_date",
            "data_quality_tier",
        ),
        player_rows,
    )
    _write_csv(
        OUTPUT_DIR / "veteran_feature_scores.csv",
        (
            "season",
            "snapshot_date",
            "player_id",
            "position",
            "feature_name",
            "normalized_score",
            "source_key",
            "source_confidence",
            "is_missing",
            "missing_reason",
            "is_user_override",
            "override_reason",
        ),
        feature_rows,
    )
    source_rows = [
        _source_row(
            "nflverse_player_stats_recent_lve_20260506",
            "nflverse player stats recent weighted LVE scoring",
            "player_stats",
            NFLVERSE_PLAYER_STATS_URL,
            92,
            1,
            source_date=_nflverse_stats_source_date(),
            notes_extra=_nflverse_stats_coverage_note(),
        ),
        _source_row(
            "nflverse_role_stats_recent_20260506",
            "nflverse player stats plus snap-count role signals",
            "role_usage",
            f"{NFLVERSE_PLAYER_STATS_URL} | {NFLVERSE_SNAP_COUNTS_URL_TEMPLATE}",
            88,
            2,
            source_date=_nflverse_stats_source_date(),
            notes_extra=_nflverse_stats_coverage_note(),
        ),
        _source_row(
            "nflverse_snap_counts_recent_20260506",
            "nflverse snap counts recent offensive participation",
            "snap_counts",
            NFLVERSE_SNAP_COUNTS_URL_TEMPLATE.format(season="2022-2024"),
            88,
            4,
            source_date=_nflverse_stats_source_date(),
            notes_extra=_nflverse_stats_coverage_note(),
        ),
        _source_row(
            "nflverse_first_down_td_fit_20260506",
            "nflverse rushing and receiving first-down/TD scoring fit",
            "player_stats",
            NFLVERSE_PLAYER_STATS_URL,
            90,
            3,
            source_date=_nflverse_stats_source_date(),
            notes_extra=_nflverse_stats_coverage_note(),
        ),
        _source_row(
            "fantasycalc_redraft_value_20260505",
            "FantasyCalc current redraft value",
            "market_rank",
            FANTASYCALC_URL,
            78,
            1,
        ),
        _source_row(
            "fantasycalc_dynastyprocess_role_proxy_20260505",
            "FantasyCalc + DynastyProcess market gap-fill proxy",
            "market_proxy",
            "local derived public-source blend",
            48,
            5,
        ),
        _source_row(
            "sleeper_player_metadata_20260505",
            "Sleeper player metadata",
            "sleeper_api",
            SLEEPER_PLAYERS_URL,
            88,
            1,
        ),
        _source_row(
            "dynastyprocess_nflreadr_player_ids_20260506",
            "DynastyProcess/nflreadr fantasy player ID bridge",
            "player_identity",
            DYNASTYPROCESS_PLAYER_IDS_URL,
            90,
            2,
        ),
        _source_row(
            "nflverse_players_identity_20260506",
            "nflverse players identity release",
            "player_identity",
            NFLVERSE_PLAYERS_URL,
            92,
            3,
        ),
        _source_row(
            "fantasycalc_dynastyprocess_market_20260505",
            "FantasyCalc + DynastyProcess market value",
            "market_rank",
            f"{FANTASYCALC_URL} | {DYNASTYPROCESS_URL}",
            78,
            2,
        ),
        _source_row(
            "sleeper_injury_metadata_20260505",
            "Sleeper injury metadata",
            "injury",
            SLEEPER_PLAYERS_URL,
            60,
            1,
        ),
        _source_row(
            "nflverse_sleeper_injury_durability_20260506",
            "nflverse injury history plus Sleeper current status",
            "injury",
            f"{NFLVERSE_INJURIES_URL_TEMPLATE} | {SLEEPER_PLAYERS_URL}",
            82,
            2,
        ),
        _source_row(
            "fantasycalc_lve_role_proxy_20260505",
            "FantasyCalc LVE missing-stats gap-fill",
            "market_proxy",
            "local derived public-source blend",
            45,
            6,
        ),
        _source_row(
            "fantasycalc_dynastyprocess_wr_proxy_20260505",
            "FantasyCalc + DynastyProcess WR missing-stats gap-fill",
            "market_proxy",
            "local derived public-source blend",
            45,
            7,
        ),
        _source_row(
            "fantasycalc_dynastyprocess_te_proxy_20260505",
            "FantasyCalc + DynastyProcess TE missing-stats gap-fill",
            "market_proxy",
            "local derived public-source blend",
            45,
            8,
        ),
        _source_row(
            "fantasycalc_dynastyprocess_replaceability_20260505",
            "FantasyCalc + DynastyProcess format replaceability proxy",
            "market_proxy",
            "local derived public-source blend",
            60,
            9,
        ),
    ]
    source_header = tuple(
        _read_csv(REPO_ROOT / "sample_data" / "veteran_model_v1" / "veteran_source_catalog.csv")[
            0
        ].keys()
    )
    _write_csv(
        OUTPUT_DIR / "veteran_source_catalog.csv",
        source_header,
        source_rows,
    )


def _write_identity_bridge(
    identity_rows: list[dict[str, object]],
    active_roster_ids: set[str],
) -> None:
    header = (
        "sleeper_id",
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
    )
    sorted_rows = sorted(
        identity_rows,
        key=lambda row: (
            str(row["match_status"]),
            str(row["position"]),
            str(row["player_name"]),
        ),
    )
    _write_csv(
        OUTPUT_DIR / "sleeper_nflverse_identity_bridge.csv",
        header,
        sorted_rows,
    )
    _write_csv(
        OUTPUT_DIR / "active_roster_identity_review.csv",
        header,
        [row for row in sorted_rows if str(row["sleeper_id"]) in active_roster_ids],
    )


def _source_row(
    key: str,
    name: str,
    source_type: str,
    url: str,
    reliability: int,
    priority_rank: int,
    *,
    source_date: str | None = None,
    notes_extra: str = "",
) -> dict[str, object]:
    now = datetime.now(UTC).isoformat()
    source_family = _source_family(source_type)
    source_domain = _source_domain(source_type)
    source_format = "json" if source_type in {"sleeper_api", "market_rank"} else "csv"
    source_notes = (
        "Stats-first public backfill. Market ranks are trade-liquidity inputs, "
        "not private football value."
    )
    if notes_extra:
        source_notes = f"{source_notes} {notes_extra}"
    return {
        "source_key": key,
        "source_name": name,
        "source_type": source_type,
        "source_family": source_family,
        "source_domain": source_domain,
        "authority_tier": _authority_tier(source_type),
        "priority_rank": str(priority_rank),
        "required_for_modes": "keeper_review|draft_room",
        "freshness_window_hours": _source_freshness_window_hours(source_type),
        "source_format": source_format,
        "local_path": str(OUTPUT_DIR),
        "source_url": url,
        "source_path_or_url": url,
        "source_date": source_date or "2026-05-06",
        "retrieved_at": now,
        "captured_at_local": now,
        "effective_date": source_date or "2026-05-05",
        "season": SEASON,
        "scoring_context": "1qb_non_ppr_stats_first",
        "checksum_sha256": "",
        "parser_version": "stats_first_public_backfill_v1",
        "source_notes": source_notes,
        "is_active": "true",
        "reliability_score": str(reliability),
        "notes": "League rank not used as player quality.",
    }


def _source_freshness_window_hours(source_type: str) -> str:
    if source_type in {"player_stats", "role_usage", "snap_counts"}:
        return "8760"
    return "168"


def _source_family(source_type: str) -> str:
    if source_type == "sleeper_api":
        return "league_platform"
    if source_type == "market_rank":
        return "market_rank"
    if source_type == "market_proxy":
        return "market_proxy"
    if source_type == "player_identity":
        return "player_identity"
    if source_type == "player_stats":
        return "football_stats"
    if source_type in {"role_usage", "snap_counts"}:
        return "role_usage"
    if source_type == "projection":
        return "projection"
    if source_type == "injury":
        return "injury_report"
    return "manual_note"


def _source_domain(source_type: str) -> str:
    if source_type == "sleeper_api":
        return "league_state"
    if source_type == "market_rank":
        return "market"
    if source_type == "market_proxy":
        return "market"
    if source_type == "player_identity":
        return "identity"
    if source_type == "player_stats":
        return "production"
    if source_type in {"role_usage", "snap_counts"}:
        return "role_usage"
    if source_type == "projection":
        return "projection"
    if source_type == "injury":
        return "injury"
    return "note"


def _authority_tier(source_type: str) -> str:
    if source_type in {"sleeper_api", "league_pdf"}:
        return "tier_a_local_canonical"
    if source_type in {"player_stats", "role_usage", "snap_counts", "player_identity"}:
        return "tier_b_official_public"
    if source_type in {"market_rank", "market_proxy"}:
        return "tier_c_structured_market"
    if source_type == "injury":
        return "tier_d_editorial_estimate"
    return "tier_e_manual_unverified"


def _nflverse_stats_source_date() -> str:
    if NFLVERSE_LATEST_STATS_SEASON is None:
        return "2025-01-15"
    return f"{NFLVERSE_LATEST_STATS_SEASON + 1}-01-15"


def _nflverse_stats_coverage_note() -> str:
    if NFLVERSE_LATEST_STATS_SEASON is None:
        return "Latest covered nflverse player_stats season was not detected."
    return (
        f"Latest covered nflverse player_stats season detected at import time: "
        f"{NFLVERSE_LATEST_STATS_SEASON}. If the active league snapshot expects later "
        "NFL seasons, treat these rankings as stale/review-only."
    )


def _fantasycalc_rows() -> list[dict]:
    return json.loads(_url_text(FANTASYCALC_URL))


def _dynastyprocess_rows() -> list[dict[str, str]]:
    return list(csv.DictReader(_url_text(DYNASTYPROCESS_URL).splitlines()))


def _sleeper_players() -> dict[str, dict]:
    return json.loads(_url_text(SLEEPER_PLAYERS_URL))


def _url_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=45) as response:
        return response.read().decode("utf-8")


def _nflverse_stat_profiles(
    sleeper_players: dict[str, dict],
) -> tuple[
    dict[str, dict[str, float]],
    list[dict[str, object]],
    dict[str, dict[str, float]],
]:
    """Build stat-first model features from recent nflverse player stats.

    nflverse player_stats is the primary free/public structured source for the
    football part of this model. It gives us no-PPR scoring ingredients,
    rushing/receiving first downs, target share, air-yards share, WOPR, and
    EPA-style fields without treating market rank as a football stat.
    """

    global NFLVERSE_LATEST_STATS_SEASON

    columns = [
        "player_id",
        "player_display_name",
        "position",
        "season",
        "week",
        "season_type",
        "attempts",
        "passing_yards",
        "passing_tds",
        "passing_interceptions",
        "sacks_suffered",
        "passing_epa",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "rushing_first_downs",
        "rushing_epa",
        "receptions",
        "targets",
        "receiving_yards",
        "receiving_tds",
        "receiving_first_downs",
        "receiving_epa",
        "target_share",
        "air_yards_share",
        "wopr",
        "rushing_fumbles_lost",
        "receiving_fumbles_lost",
        "sack_fumbles_lost",
    ]
    stat_frames = []
    target_latest_season = int(SEASON) - 1
    for season in range(target_latest_season - 2, target_latest_season + 1):
        url = NFLVERSE_PLAYER_STATS_URL_TEMPLATE.format(season=season)
        try:
            stat_frames.append(
                pd.read_csv(
                    url,
                    usecols=columns,
                    low_memory=False,
                )
            )
        except Exception as exc:  # pragma: no cover - network/source availability guard
            print(f"WARNING: could not load nflverse player stats {season}: {exc}")
    if not stat_frames:
        return {}, [], {}
    stats = pd.concat(stat_frames, ignore_index=True)

    stats = stats[
        (stats["season_type"] == "REG")
        & (stats["position"].isin(FEATURES_BY_POSITION))
    ].copy()
    if stats.empty:
        return {}, [], {}
    latest_season = int(stats["season"].max())
    NFLVERSE_LATEST_STATS_SEASON = latest_season
    stats = stats[stats["season"] >= latest_season - 2].copy()
    numeric_columns = [
        column
        for column in columns
        if column not in {"player_id", "player_display_name", "position", "season_type"}
    ]
    for column in numeric_columns:
        stats[column] = pd.to_numeric(stats[column], errors="coerce").fillna(0.0)
    stats["season_weight"] = stats["season"].map(
        {
            latest_season: 1.0,
            latest_season - 1: 0.55,
            latest_season - 2: 0.25,
        }
    ).fillna(0.10)
    stats["lve_points"] = (
        (stats["passing_yards"] * LVE_SCORING["passing_yard"])
        + (stats["passing_tds"] * LVE_SCORING["passing_td"])
        + (stats["passing_interceptions"] * LVE_SCORING["interception"])
        + (stats["rushing_yards"] * LVE_SCORING["rushing_yard"])
        + (stats["rushing_tds"] * LVE_SCORING["rushing_td"])
        + (stats["receiving_yards"] * LVE_SCORING["receiving_yard"])
        + (stats["receiving_tds"] * LVE_SCORING["receiving_td"])
        + (
            (stats["rushing_first_downs"] + stats["receiving_first_downs"])
            * LVE_SCORING["rushing_receiving_first_down"]
        )
        + (
            stats["rushing_fumbles_lost"]
            + stats["receiving_fumbles_lost"]
            + stats["sack_fumbles_lost"]
        )
        * LVE_SCORING["fumble_lost"]
    )
    stats["rush_rec_first_down_td"] = (
        stats["rushing_first_downs"]
        + stats["receiving_first_downs"]
        + ((stats["rushing_tds"] + stats["receiving_tds"]) * 3.0)
    )
    stats["opportunities"] = stats["carries"] + stats["targets"]
    stats["qb_volume"] = stats["attempts"] + (stats["carries"] * 2.0)
    stats["receiving_earning"] = (
        (stats["target_share"].fillna(0.0) * 100.0)
        + (stats["wopr"].fillna(0.0) * 35.0)
        + (stats["air_yards_share"].fillna(0.0) * 25.0)
    )
    stats["total_epa"] = (
        stats["passing_epa"] + stats["rushing_epa"] + stats["receiving_epa"]
    )
    stats["total_yards"] = (
        stats["passing_yards"] + stats["rushing_yards"] + stats["receiving_yards"]
    )
    stats["qb_rushing_value"] = stats["rushing_yards"] + (stats["rushing_tds"] * 20.0)

    grouped = []
    for (gsis_id, position), group in stats.groupby(["player_id", "position"], dropna=True):
        weight = group["season_weight"]
        weight_sum = max(float(weight.sum()), 0.01)
        weighted_games = weight_sum

        grouped.append(
            {
                "gsis_id": gsis_id,
                "position": position,
                "display_name": (
                    str(group["player_display_name"].dropna().iloc[-1])
                    if not group["player_display_name"].dropna().empty
                    else ""
                ),
                "name_slug": _slug(
                    str(group["player_display_name"].dropna().iloc[-1])
                    if not group["player_display_name"].dropna().empty
                    else ""
                ),
                "lve_ppg": _weighted_per_game(group, "lve_points", weight, weighted_games),
                "games_weighted": weighted_games,
                "opportunities_pg": _weighted_per_game(
                    group, "opportunities", weight, weighted_games
                ),
                "qb_volume_pg": _weighted_per_game(group, "qb_volume", weight, weighted_games),
                "first_down_td_pg": _weighted_per_game(
                    group, "rush_rec_first_down_td", weight, weighted_games
                ),
                "targets_pg": _weighted_per_game(group, "targets", weight, weighted_games),
                "epa_pg": _weighted_per_game(group, "total_epa", weight, weighted_games),
                "yards_pg": _weighted_per_game(group, "total_yards", weight, weighted_games),
                "qb_rushing_pg": _weighted_per_game(
                    group,
                    "qb_rushing_value",
                    weight,
                    weighted_games,
                ),
                "target_share_score_raw": float(
                    (group["target_share"] * 100.0 * weight).sum() / weight_sum
                ),
                "wopr_score_raw": float(
                    (group["wopr"] * 100.0 * weight).sum() / weight_sum
                ),
                "earning_raw": float((group["receiving_earning"] * weight).sum() / weight_sum),
            }
        )
    if not grouped:
        return {}, [], {}

    by_gsis = {(row["position"], row["gsis_id"]): row for row in grouped}
    by_name_pos = _unique_name_position_rows(grouped)
    percentile_inputs = {
        "lve_ppg": {(row["position"], row["gsis_id"]): row["lve_ppg"] for row in grouped},
        "opportunities_pg": {
            (row["position"], row["gsis_id"]): row["opportunities_pg"] for row in grouped
        },
        "qb_volume_pg": {(row["position"], row["gsis_id"]): row["qb_volume_pg"] for row in grouped},
        "first_down_td_pg": {
            (row["position"], row["gsis_id"]): row["first_down_td_pg"] for row in grouped
        },
        "targets_pg": {(row["position"], row["gsis_id"]): row["targets_pg"] for row in grouped},
        "epa_pg": {(row["position"], row["gsis_id"]): row["epa_pg"] for row in grouped},
        "yards_pg": {(row["position"], row["gsis_id"]): row["yards_pg"] for row in grouped},
        "qb_rushing_pg": {
            (row["position"], row["gsis_id"]): row["qb_rushing_pg"] for row in grouped
        },
        "target_share_score_raw": {
            (row["position"], row["gsis_id"]): row["target_share_score_raw"] for row in grouped
        },
        "wopr_score_raw": {
            (row["position"], row["gsis_id"]): row["wopr_score_raw"] for row in grouped
        },
        "earning_raw": {(row["position"], row["gsis_id"]): row["earning_raw"] for row in grouped},
    }
    percentiles = {name: _percentile_map(values) for name, values in percentile_inputs.items()}

    id_bridge = _dynastyprocess_player_id_bridge()
    nflverse_player_identity = _nflverse_player_identity_lookup_from_source()
    snap_profiles = _nflverse_snap_profiles(latest_season)
    injury_profiles_by_gsis = _nflverse_injury_profiles(latest_season)
    profiles: dict[str, dict[str, float]] = {}
    injury_profiles: dict[str, dict[str, float]] = {}
    identity_rows: list[dict[str, object]] = []
    for sleeper_id, player in sleeper_players.items():
        player = sleeper_players.get(sleeper_id, {})
        position = player.get("position")
        if position not in FEATURES_BY_POSITION:
            continue
        sleeper_gsis = _id_text(player.get("gsis_id"))
        bridge = id_bridge.get(str(sleeper_id), {})
        bridge_gsis = _id_text(bridge.get("gsis_id"))
        bridge_pfr = _id_text(bridge.get("pfr_id"))
        stat_row, match_method = _resolve_stat_identity(
            position=position,
            sleeper_gsis=sleeper_gsis,
            bridge_gsis=bridge_gsis,
            sleeper_player=player,
            by_gsis=by_gsis,
            by_name_pos=by_name_pos,
        )
        identity_row = stat_row
        identity_match_method = match_method
        identity_bridge_pfr = bridge_pfr
        if identity_row is None and bridge_gsis:
            identity_row = {
                "gsis_id": bridge_gsis,
                "display_name": bridge.get("name", "")
                or player.get("full_name")
                or player.get("search_full_name")
                or "",
                "pfr_id": bridge_pfr,
            }
            identity_match_method = "dynastyprocess_sleeper_to_gsis"
        if identity_row is None:
            identity_row, identity_match_method = _resolve_player_identity(
                position=position,
                sleeper_player=player,
                identity_lookup=nflverse_player_identity,
            )
            if identity_row is not None and not identity_bridge_pfr:
                identity_bridge_pfr = _id_text(identity_row.get("pfr_id"))
        identity_rows.append(
            _identity_audit_row(
                sleeper_id=sleeper_id,
                player=player,
                position=position,
                sleeper_gsis=sleeper_gsis,
                bridge_gsis=bridge_gsis,
                bridge_pfr=identity_bridge_pfr,
                bridge_name=bridge.get("name", ""),
                stat_row=identity_row,
                match_method=identity_match_method,
            )
        )
        if stat_row is None:
            continue
        key = (position, stat_row["gsis_id"])
        injury_profile = injury_profiles_by_gsis.get(str(stat_row["gsis_id"]))
        if injury_profile is not None:
            injury_profiles[sleeper_id] = injury_profile
        lve = percentiles["lve_ppg"].get(key)
        games_score = _clamp(stat_row["games_weighted"] / 17.0 * 100.0)
        snap_score = _snap_score(position, player, bridge_pfr, snap_profiles)
        if position == "QB":
            role = _avg_present(percentiles["qb_volume_pg"].get(key), games_score)
            role = _avg_present(role, snap_score)
            replaceability = _avg_present(lve, percentiles["qb_volume_pg"].get(key))
            first_down_td = percentiles["first_down_td_pg"].get(key)
            efficiency = _avg_present(
                percentiles["epa_pg"].get(key),
                percentiles["yards_pg"].get(key),
                lve,
            )
            profiles[sleeper_id] = {
                "lve_projection_value": lve,
                "weighted_recent_lve_ppg_score": lve,
                "expected_lve_points_score": _avg_present(replaceability, role, lve),
                "role_security": role,
                "first_down_td_fit": first_down_td,
                "qb_rushing_profile": percentiles["qb_rushing_pg"].get(key),
                "efficiency_score": efficiency,
                "position_replaceability": replaceability,
            }
        elif position == "RB":
            role = _avg_present(percentiles["opportunities_pg"].get(key), games_score)
            role = _avg_present(role, snap_score)
            first_down_td = percentiles["first_down_td_pg"].get(key)
            efficiency = _avg_present(
                percentiles["epa_pg"].get(key),
                percentiles["yards_pg"].get(key),
                lve,
            )
            profiles[sleeper_id] = {
                "lve_projection_value": lve,
                "weighted_recent_lve_ppg_score": lve,
                "expected_lve_points_score": _avg_present(role, first_down_td, lve),
                "role_security": role,
                "workload_earning": role,
                "first_down_td_fit": first_down_td,
                "efficiency_score": efficiency,
            }
        elif position == "WR":
            target_earning = _avg_present(
                percentiles["target_share_score_raw"].get(key),
                percentiles["wopr_score_raw"].get(key),
                percentiles["targets_pg"].get(key),
                percentiles["earning_raw"].get(key),
            )
            role = _avg_present(target_earning, games_score)
            role = _avg_present(role, snap_score)
            first_down_td = percentiles["first_down_td_pg"].get(key)
            efficiency = _avg_present(
                percentiles["epa_pg"].get(key),
                percentiles["yards_pg"].get(key),
                lve,
                target_earning,
            )
            profiles[sleeper_id] = {
                "lve_projection_value": lve,
                "weighted_recent_lve_ppg_score": lve,
                "expected_lve_points_score": _avg_present(
                    role,
                    target_earning,
                    first_down_td,
                    lve,
                ),
                "role_security": role,
                "target_earning_stability": target_earning,
                "route_role": role,
                "first_down_td_fit": first_down_td,
                "efficiency_score": efficiency,
            }
        elif position == "TE":
            route_proxy = _avg_present(
                percentiles["target_share_score_raw"].get(key),
                percentiles["targets_pg"].get(key),
                percentiles["earning_raw"].get(key),
                games_score,
            )
            route_proxy = _avg_present(route_proxy, snap_score)
            replaceability = _avg_present(lve, route_proxy)
            first_down_td = percentiles["first_down_td_pg"].get(key)
            efficiency = _avg_present(
                percentiles["epa_pg"].get(key),
                percentiles["yards_pg"].get(key),
                lve,
                route_proxy,
            )
            profiles[sleeper_id] = {
                "lve_projection_value": lve,
                "weighted_recent_lve_ppg_score": lve,
                "expected_lve_points_score": _avg_present(
                    replaceability,
                    route_proxy,
                    first_down_td,
                ),
                "role_security": route_proxy,
                "target_earning_stability": route_proxy,
                "route_role": route_proxy,
                "route_share_stability": route_proxy,
                "first_down_td_fit": first_down_td,
                "efficiency_score": efficiency,
                "position_replaceability": replaceability,
            }
    return profiles, identity_rows, injury_profiles


def _weighted_per_game(
    group: pd.DataFrame,
    column: str,
    weight: pd.Series,
    denominator: float,
) -> float:
    return float((group[column] * weight).sum() / denominator)


def _resolve_stat_identity(
    *,
    position: str,
    sleeper_gsis: str,
    bridge_gsis: str,
    sleeper_player: dict,
    by_gsis: dict[tuple[str, str], dict[str, float | str]],
    by_name_pos: dict[tuple[str, str], dict[str, float | str]],
) -> tuple[dict[str, float | str] | None, str]:
    if sleeper_gsis:
        stat_row = by_gsis.get((position, sleeper_gsis))
        if stat_row is not None:
            return stat_row, "sleeper_gsis_exact"
    if bridge_gsis:
        stat_row = by_gsis.get((position, bridge_gsis))
        if stat_row is not None:
            return stat_row, "dynastyprocess_sleeper_to_gsis"
    stat_row = _exact_name_stat_match(position, sleeper_player, by_name_pos)
    if stat_row is not None:
        return stat_row, "unique_exact_name_position"
    return None, "unmatched"


def _nflverse_player_identity_lookup_from_source() -> dict[tuple[str, str, str], dict[str, str]]:
    try:
        rows = pd.read_csv(
            NFLVERSE_PLAYERS_URL,
            dtype=str,
            usecols=[
                "gsis_id",
                "display_name",
                "pfr_id",
                "espn_id",
                "position",
                "latest_team",
                "rookie_season",
                "draft_year",
            ],
        ).fillna("")
    except Exception as exc:  # pragma: no cover - network/source availability guard
        print(f"WARNING: could not load nflverse players identity map: {exc}")
        return {}
    return _nflverse_player_identity_lookup(rows.to_dict(orient="records"))


def _nflverse_player_identity_lookup(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str, str], dict[str, str]]:
    buckets: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        position = str(row.get("position") or "")
        team = str(row.get("latest_team") or "")
        name = str(row.get("display_name") or "")
        gsis_id = _id_text(row.get("gsis_id"))
        if position not in FEATURES_BY_POSITION or not team or not name or not gsis_id:
            continue
        for name_key in {_slug(name), _loose_slug(name)}:
            if name_key:
                buckets.setdefault((position, team, name_key), []).append(row)
    return {
        key: values[0]
        for key, values in buckets.items()
        if len({_id_text(value.get("gsis_id")) for value in values}) == 1
    }


def _resolve_player_identity(
    *,
    position: str,
    sleeper_player: dict,
    identity_lookup: dict[tuple[str, str, str], dict[str, str]],
) -> tuple[dict[str, str] | None, str]:
    team = str(sleeper_player.get("team") or "")
    if not team:
        return None, "unmatched"
    candidates = (
        sleeper_player.get("full_name"),
        sleeper_player.get("search_full_name"),
        sleeper_player.get("metadata", {}).get("full_name")
        if isinstance(sleeper_player.get("metadata"), dict)
        else None,
    )
    for candidate in candidates:
        if not candidate:
            continue
        for name_key in {_slug(str(candidate)), _loose_slug(str(candidate))}:
            match = identity_lookup.get((position, team, name_key))
            if match is not None:
                return match, "nflverse_players_name_position_team"
    return None, "unmatched"


def _identity_audit_row(
    *,
    sleeper_id: str,
    player: dict,
    position: str,
    sleeper_gsis: str,
    bridge_gsis: str,
    bridge_pfr: str,
    bridge_name: object,
    stat_row: dict[str, float | str] | None,
    match_method: str,
) -> dict[str, object]:
    full_name = player.get("full_name") or player.get("search_full_name") or ""
    matched_gsis = "" if stat_row is None else str(stat_row.get("gsis_id") or "")
    stat_name = "" if stat_row is None else str(stat_row.get("display_name") or "")
    return {
        "sleeper_id": sleeper_id,
        "player_name": full_name,
        "position": position,
        "sleeper_gsis_id": sleeper_gsis,
        "bridge_gsis_id": bridge_gsis,
        "bridge_pfr_id": bridge_pfr,
        "bridge_name": bridge_name or "",
        "matched_gsis_id": matched_gsis,
        "stat_player_name": stat_name,
        "match_method": match_method,
        "match_status": "matched" if stat_row is not None else "unmatched",
        "manual_review_required": str(
            stat_row is None or match_method == "unique_exact_name_position"
        ).lower(),
    }


def _unique_name_position_rows(
    rows: list[dict[str, float | str]],
) -> dict[tuple[str, str], dict[str, float | str]]:
    buckets: dict[tuple[str, str], list[dict[str, float | str]]] = {}
    for row in rows:
        name_slug = str(row.get("name_slug") or "")
        if name_slug:
            buckets.setdefault((str(row["position"]), name_slug), []).append(row)
    return {
        key: values[0]
        for key, values in buckets.items()
        if len({str(value.get("gsis_id") or "") for value in values}) == 1
    }


def _dynastyprocess_player_id_bridge() -> dict[str, dict[str, str]]:
    try:
        rows = pd.read_csv(
            DYNASTYPROCESS_PLAYER_IDS_URL,
            dtype=str,
            usecols=["sleeper_id", "gsis_id", "pfr_id", "name", "position", "team"],
        ).fillna("")
    except Exception as exc:  # pragma: no cover - network/source availability guard
        print(f"WARNING: could not load DynastyProcess player IDs: {exc}")
        return {}
    bridge: dict[str, dict[str, str]] = {}
    for row in rows.to_dict(orient="records"):
        sleeper_id = _id_text(row.get("sleeper_id"))
        gsis_id = _id_text(row.get("gsis_id"))
        if sleeper_id and gsis_id:
            bridge[sleeper_id] = {
                "gsis_id": gsis_id,
                "pfr_id": _id_text(row.get("pfr_id")),
                "name": str(row.get("name") or ""),
                "position": str(row.get("position") or ""),
                "team": str(row.get("team") or ""),
            }
    return bridge


def _nflverse_snap_profiles(
    latest_season: int,
) -> dict[str, dict[tuple[str, str], float]]:
    rows = []
    usecols = ["season", "game_type", "player", "pfr_player_id", "position", "offense_pct"]
    for season in range(latest_season - 2, latest_season + 1):
        url = NFLVERSE_SNAP_COUNTS_URL_TEMPLATE.format(season=season)
        try:
            season_rows = pd.read_csv(url, compression="gzip", usecols=usecols)
        except Exception as exc:  # pragma: no cover - network/source availability guard
            print(f"WARNING: could not load nflverse snap counts {season}: {exc}")
            continue
        rows.append(season_rows)
    if not rows:
        return {"pfr": {}, "name": {}}
    snaps = pd.concat(rows, ignore_index=True)
    snaps = snaps[
        (snaps["game_type"] == "REG")
        & (snaps["position"].isin(FEATURES_BY_POSITION))
    ].copy()
    if snaps.empty:
        return {"pfr": {}, "name": {}}
    snaps["offense_pct"] = pd.to_numeric(snaps["offense_pct"], errors="coerce").fillna(0.0)
    snaps["season_weight"] = snaps["season"].map(
        {
            latest_season: 1.0,
            latest_season - 1: 0.55,
            latest_season - 2: 0.25,
        }
    ).fillna(0.10)
    profiles = []
    for (pfr_id, position), group in snaps.groupby(["pfr_player_id", "position"], dropna=True):
        weight = group["season_weight"]
        denominator = max(float(weight.sum()), 0.01)
        profiles.append(
            {
                "pfr_id": _id_text(pfr_id),
                "position": position,
                "name_slug": _slug(
                    str(group["player"].dropna().iloc[-1])
                    if not group["player"].dropna().empty
                    else ""
                ),
                "snap_score": _clamp(
                    float((group["offense_pct"] * 100.0 * weight).sum() / denominator)
                ),
            }
        )
    by_pfr = {
        (str(row["position"]), str(row["pfr_id"])): float(row["snap_score"])
        for row in profiles
        if row.get("pfr_id")
    }
    name_buckets: dict[tuple[str, str], list[float]] = {}
    for row in profiles:
        name_slug = str(row.get("name_slug") or "")
        if name_slug:
            name_buckets.setdefault((str(row["position"]), name_slug), []).append(
                float(row["snap_score"])
            )
    by_name = {
        key: values[0]
        for key, values in name_buckets.items()
        if len(values) == 1
    }
    return {"pfr": by_pfr, "name": by_name}


def _snap_score(
    position: str,
    sleeper_player: dict,
    bridge_pfr: str,
    snap_profiles: dict[str, dict[tuple[str, str], float]],
) -> float | None:
    if bridge_pfr:
        value = snap_profiles["pfr"].get((position, bridge_pfr))
        if value is not None:
            return value
    for candidate in (
        sleeper_player.get("full_name"),
        sleeper_player.get("search_full_name"),
    ):
        if candidate:
            value = snap_profiles["name"].get((position, _slug(str(candidate))))
            if value is not None:
                return value
    return None


def _nflverse_injury_profiles(latest_season: int) -> dict[str, dict[str, float]]:
    rows = []
    usecols = [
        "season",
        "game_type",
        "week",
        "gsis_id",
        "position",
        "report_primary_injury",
        "report_status",
        "practice_primary_injury",
        "practice_status",
    ]
    for season in range(latest_season - 1, latest_season + 1):
        url = NFLVERSE_INJURIES_URL_TEMPLATE.format(season=season)
        try:
            season_rows = pd.read_csv(url, usecols=usecols)
        except Exception as exc:  # pragma: no cover - network/source availability guard
            print(f"WARNING: could not load nflverse injuries {season}: {exc}")
            continue
        rows.append(season_rows)
    if not rows:
        return {}
    injuries = pd.concat(rows, ignore_index=True)
    injuries = injuries[
        (injuries["game_type"] == "REG")
        & (injuries["position"].isin(FEATURES_BY_POSITION))
    ].copy()
    if injuries.empty:
        return {}
    injuries["week_index"] = (
        (pd.to_numeric(injuries["season"], errors="coerce").fillna(latest_season) * 100)
        + pd.to_numeric(injuries["week"], errors="coerce").fillna(0)
    )
    profiles: dict[str, dict[str, float]] = {}
    for gsis_id, group in injuries.groupby("gsis_id", dropna=True):
        position = str(group["position"].dropna().iloc[-1])
        status_penalty = 0.0
        lower_body_count = 0
        missed_or_limited_count = 0
        recent_weighted_events = 0.0
        max_week_index = float(group["week_index"].max())
        for row in group.to_dict(orient="records"):
            status = str(row.get("report_status") or row.get("practice_status") or "").lower()
            injury_text = " ".join(
                str(row.get(field) or "").lower()
                for field in ("report_primary_injury", "practice_primary_injury")
            )
            event_weight = 1.0 if float(row["week_index"]) >= max_week_index - 6 else 0.45
            if any(term in status for term in ("out", "doubtful", "did not participate")):
                status_penalty += 3.0 * event_weight
                missed_or_limited_count += 1
            elif any(term in status for term in ("questionable", "limited")):
                status_penalty += 1.4 * event_weight
                missed_or_limited_count += 1
            if _is_lower_body_injury(injury_text):
                lower_body_count += 1
                status_penalty += _lower_body_position_penalty(position) * event_weight
            recent_weighted_events += event_weight
        profiles[str(gsis_id)] = {
            "injury_event_count": float(len(group)),
            "missed_or_limited_count": float(missed_or_limited_count),
            "lower_body_count": float(lower_body_count),
            "recent_weighted_events": float(recent_weighted_events),
            "history_penalty": _clamp(status_penalty, 0.0, 34.0),
        }
    return profiles


def _is_lower_body_injury(text: str) -> bool:
    return any(
        token in text
        for token in (
            "ankle",
            "achilles",
            "knee",
            "hamstring",
            "quad",
            "groin",
            "hip",
            "leg",
            "foot",
            "toe",
            "calf",
        )
    )


def _lower_body_position_penalty(position: str) -> float:
    if position in {"RB", "WR"}:
        return 2.0
    if position == "TE":
        return 1.3
    return 0.8


def _exact_name_stat_match(
    position: str,
    sleeper_player: dict,
    by_name_pos: dict[tuple[str, str], dict[str, float | str]],
) -> dict[str, float | str] | None:
    candidates = (
        sleeper_player.get("full_name"),
        sleeper_player.get("search_full_name"),
        sleeper_player.get("metadata", {}).get("full_name")
        if isinstance(sleeper_player.get("metadata"), dict)
        else None,
    )
    for candidate in candidates:
        if candidate:
            match = by_name_pos.get((position, _slug(str(candidate))))
            if match is not None:
                return match
    return None


def _id_text(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return ""
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _source_percentiles(
    fantasycalc: list[dict],
    dynastyprocess: list[dict[str, str]],
) -> dict[str, dict[tuple[str, str], float]]:
    fc_dynasty_values = {}
    fc_redraft_values = {}
    for row in fantasycalc:
        player = row.get("player") or {}
        pos = player.get("position")
        sid = str(player.get("sleeperId") or "")
        if pos in FEATURES_BY_POSITION and sid:
            fc_dynasty_values[(pos, sid)] = float(row.get("value") or 0)
            fc_redraft_values[(pos, sid)] = float(row.get("redraftValue") or 0)
    dp_values = {}
    for row in dynastyprocess:
        pos = row.get("pos")
        if pos in FEATURES_BY_POSITION and row.get("player"):
            dp_values[(pos, _slug(row["player"]))] = float(row.get("value_1qb") or 0)
    return {
        "fc_dynasty": _percentile_map(fc_dynasty_values),
        "fc_redraft": _percentile_map(fc_redraft_values),
        "dp_market": _percentile_map(dp_values),
    }


def _percentile_map(values: dict[tuple[str, str], float]) -> dict[tuple[str, str], float]:
    by_pos: dict[str, list[tuple[tuple[str, str], float]]] = {}
    for key, value in values.items():
        by_pos.setdefault(key[0], []).append((key, value))
    result = {}
    for rows in by_pos.values():
        sorted_rows = sorted(rows, key=lambda item: item[1])
        denominator = max(1, len(sorted_rows) - 1)
        for index, (key, _) in enumerate(sorted_rows):
            result[key] = 100 * index / denominator
    return result


def _age(
    roster: dict[str, str],
    dim: dict[str, str],
    sleeper: dict,
    fc: dict | None,
) -> float | None:
    for value in (
        (fc or {}).get("player", {}).get("maybeAge") if fc else None,
        sleeper.get("age"),
        dim.get("age"),
    ):
        try:
            if value not in (None, "") and not math.isnan(float(value)):
                return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _age_curve(position: str, age: float | None) -> float | None:
    if age is None:
        return None
    if position == "QB":
        if age <= 24:
            return 78
        if age <= 31:
            return 92
        if age <= 35:
            return 80 - (age - 31) * 5
        return 48
    if position == "RB":
        if age <= 23:
            return 92
        if age <= 26:
            return 88
        if age <= 28:
            return 68 - (age - 26) * 10
        return max(25, 45 - (age - 28) * 8)
    if position == "WR":
        if age <= 24:
            return 88
        if age <= 29:
            return 90
        if age <= 31:
            return 72 - (age - 29) * 8
        return max(35, 55 - (age - 31) * 8)
    if position == "TE":
        if age <= 24:
            return 82
        if age <= 29:
            return 88
        if age <= 32:
            return 72 - (age - 29) * 6
        return max(35, 52 - (age - 32) * 8)
    return None


def _injury_score(
    position: str,
    sleeper: dict,
    age_score: float | None,
    injury_profile: dict[str, float] | None,
) -> float:
    status = str(sleeper.get("injury_status") or "").lower()
    if status in {"out", "ir", "pup"}:
        current_status_score = 35
    elif status in {"doubtful", "questionable"}:
        current_status_score = 58
    else:
        current_status_score = 86
    history_penalty = 0.0 if injury_profile is None else injury_profile.get("history_penalty", 0.0)
    age_injury_drag = 0.0
    if age_score is not None and age_score < 60:
        age_injury_drag = (60.0 - age_score) * (0.10 if position == "QB" else 0.18)
    return _clamp(current_status_score - history_penalty - age_injury_drag)


def _replaceability_score(
    position: str,
    fc: dict | None,
    dp: dict | None,
    market: float | None,
) -> float | None:
    if market is None:
        return None
    fc_pos_rank = (fc or {}).get("positionRank")
    try:
        pos_rank = float(fc_pos_rank)
    except (TypeError, ValueError):
        pos_rank = None
    if position == "QB":
        if pos_rank is None:
            return market * 0.7
        return _clamp(104 - pos_rank * 6)
    if position == "TE":
        if pos_rank is None:
            return market * 0.75
        return _clamp(104 - pos_rank * 7)
    return market


def _active_bonus(sleeper: dict) -> float:
    status = str(sleeper.get("status") or "").lower()
    return 75 if status in {"active", ""} else 45


def _avg_present(*values: float | None) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    return max(min_value, min(max_value, float(value)))


def _is_top_five(roster_rows: list[dict[str, str]], row: dict[str, str]) -> bool:
    team_rows = [r for r in roster_rows if r.get("team_id") == row.get("team_id")]
    ranked = sorted(
        (r for r in team_rows if _rank(r) is not None),
        key=lambda r: _rank(r) or 9999,
    )
    return row in ranked[:5]


def _rank(row: dict[str, str]) -> int | None:
    try:
        return int(float(row.get("league_rank") or row.get("official_rank") or ""))
    except ValueError:
        return None


def _ignored_kicker_output(row: dict[str, str]) -> dict[str, object]:
    return {
        "snapshot_date": SNAPSHOT_DATE,
        "player_id": row["player_id"],
        "player_name": row["player_name"],
        "position": row["position"],
        "private_score": 0,
        "market_score": 0,
        "war_score": 0,
        "keeper_score": 0,
        "drop_candidate_score": 100,
        "veteran_base_value": 0,
        "horizon_retention_score": 0,
        "trade_value": 0,
        "lve_format_fit": 0,
        "structural_adjustment": 0,
        "league_rank_signal": 0,
        "top_five_release_pressure": 0,
        "league_rank_adjustment": 0,
        "missing_data_penalty": 0,
        "risk_flags": "excluded_position",
        "upside_flags": "",
        "floor_flags": "",
        "smash_prob": "",
        "hit_prob": "",
        "useful_prob": "",
        "replaceable_prob": "",
        "miss_prob": "",
        "bust_prob": "",
        "pick_adjusted_value": 0,
        "confidence_score": 100,
        "risk_level": "ignored_position",
        "warning_status": "excluded",
        "warning_reasons": "kickers_excluded_by_user_policy",
        "recommendation": "exclude",
        "do_not_draft_before_pick": "",
        "model_version": "veteran_lve_public_backfill_v1",
        "computed_at": datetime.now(UTC).isoformat(),
        "notes": "Kicker excluded by user policy; not a model placeholder.",
    }


def _update_metadata_sources() -> None:
    path = ACTIVE_PACK / "metadata_sources.csv"
    rows = _read_csv(path)
    for row in rows:
        row["review_status"] = "reviewed"
        if row.get("file_name") == "model_outputs.csv":
            row["source_name"] = "Stats-first public veteran model backfill"
            row["source_type"] = "generated_model_output"
            row["source_url_or_description"] = (
                "nflverse player stats; Sleeper metadata; FantasyCalc/DynastyProcess "
                "trade-liquidity only"
            )
            row["notes"] = (
                "Placeholders replaced with stats-first public model outputs. "
                "Market ranks are not private football value; players without public NFL "
                "stat coverage stay confidence-limited instead of being market-filled."
            )
        elif row.get("notes"):
            row["notes"] = f"{row['notes']} Reviewed by active-pack validation."
        else:
            row["notes"] = "Reviewed by active-pack validation."
    _write_csv(path, tuple(rows[0].keys()), rows)


def _slug(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _loose_slug(value: str) -> str:
    compact = _slug(value)
    for suffix in ("iii", "jr", "sr", "ii", "iv", "v"):
        if compact.endswith(suffix):
            return compact[: -len(suffix)]
    return compact


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return tuple(next(reader))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
