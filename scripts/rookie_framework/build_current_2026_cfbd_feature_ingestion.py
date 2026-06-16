"""Build current 2026 rookie CFBD feature ingestion exports.

This is local/export-only. It caches approved CFBD 2024/2025 regular-season
passing, rushing, receiving, and team denominator stats, joins them to the
current rookie advisory board, and appends source-safe CFBD feature columns
without changing production rankings or app outputs.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_cfbd_historical_feature_cache_v1 import (
    add_feature_aliases,
    load_local_dotenv,
    lookup_team_value,
    norm_field,
    norm_name,
    pct,
    request_cfbd,
    safe_float,
    safe_int,
)
from scripts.rookie_framework.build_rookie_wr_feature_quality_pass_20260615 import (
    capped,
    wr_signal_score,
    wr_warning_penalty,
)
from src.config.api_settings import get_api_settings


OUTPUT_DIR = Path("local_exports/rookie_framework/current_2026_cfbd_feature_ingestion_20260615")
CURRENT_BOARD = Path("local_exports/rookie_framework/draft_ranking_model_v1_20260615/rookie_draft_ranking_v1_20260615.csv")
HISTORICAL_PLAYER_FEATURES = Path(
    "local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615/"
    "cfbd_player_season_features_v1_20260615.csv"
)
PLAYER_CATEGORIES = ["passing", "rushing", "receiving"]
SEASONS = [2024, 2025]
POSITIONS = ["QB", "RB", "WR", "TE"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def endpoint_cache_path(output_dir: Path, season: int, category: str) -> Path:
    return output_dir / "raw_cfbd_csv" / f"player_stats_season_{season}_regular_{category}.csv"


def team_cache_path(output_dir: Path, season: int) -> Path:
    return output_dir / "raw_cfbd_csv" / f"team_stats_season_{season}_regular.csv"


def fetch_or_cache_endpoint(
    output_dir: Path,
    *,
    endpoint: str,
    params: dict[str, str],
    path: Path,
    force_refresh: bool,
    sleep_seconds: float,
) -> dict[str, object]:
    if path.exists() and not force_refresh:
        rows = read_csv(path)
        return {
            "season": params.get("year", ""),
            "endpoint": endpoint,
            "category": params.get("category", "team_denominators"),
            "status": "cache_hit",
            "row_count": len(rows),
            "field_count": len(rows[0].keys()) if rows else 0,
            "cache_path": str(path.relative_to(output_dir)),
            "error_type": "",
        }
    load_local_dotenv()
    settings = get_api_settings()
    if not settings.cfbd_api_key or not settings.live_api_enabled:
        return {
            "season": params.get("year", ""),
            "endpoint": endpoint,
            "category": params.get("category", "team_denominators"),
            "status": "not_fetched_live_api_disabled_or_missing_key",
            "row_count": 0,
            "field_count": 0,
            "cache_path": str(path.relative_to(output_dir)),
            "error_type": "",
        }
    try:
        payload = request_cfbd(settings.cfbd_api_base, settings.cfbd_api_key, endpoint, params)
        columns = sorted({key for row in payload for key in row.keys()})
        write_csv(path, payload, columns)
        status = "fetched"
        error_type = ""
        row_count = len(payload)
        field_count = len(columns)
    except Exception as exc:  # noqa: BLE001 - safe manifest only; no secret text.
        status = "fetch_failed"
        error_type = type(exc).__name__
        row_count = 0
        field_count = 0
    time.sleep(sleep_seconds)
    return {
        "season": params.get("year", ""),
        "endpoint": endpoint,
        "category": params.get("category", "team_denominators"),
        "status": status,
        "row_count": row_count,
        "field_count": field_count,
        "cache_path": str(path.relative_to(output_dir)),
        "error_type": error_type,
    }


def fetch_current_cache(output_dir: Path, *, force_refresh: bool, skip_fetch: bool, sleep_seconds: float) -> list[dict[str, object]]:
    manifest = []
    if skip_fetch:
        return manifest
    for season in SEASONS:
        for category in PLAYER_CATEGORIES:
            manifest.append(
                fetch_or_cache_endpoint(
                    output_dir,
                    endpoint="/stats/player/season",
                    params={"year": str(season), "seasonType": "regular", "category": category},
                    path=endpoint_cache_path(output_dir, season, category),
                    force_refresh=force_refresh,
                    sleep_seconds=sleep_seconds,
                )
            )
        manifest.append(
            fetch_or_cache_endpoint(
                output_dir,
                endpoint="/stats/season",
                params={"year": str(season), "seasonType": "regular"},
                path=team_cache_path(output_dir, season),
                force_refresh=force_refresh,
                sleep_seconds=sleep_seconds,
            )
        )
    return manifest


def build_player_seasons(output_dir: Path) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str, str, str], dict[str, object]] = {}
    for season in SEASONS:
        for category in PLAYER_CATEGORIES:
            for row in read_csv(endpoint_cache_path(output_dir, season, category)):
                player_id = str(row.get("playerId") or row.get("player_id") or "").strip()
                player = str(row.get("player", "")).strip()
                team = str(row.get("team", "")).strip()
                conference = str(row.get("conference", "")).strip()
                position = str(row.get("position", "")).strip().upper()
                if not player or position not in POSITIONS:
                    continue
                key = (str(season), player_id, player, team, conference, position)
                record = grouped.setdefault(
                    key,
                    {
                        "season": str(season),
                        "cfbd_player_id": player_id,
                        "player_name": player,
                        "normalized_player_name": norm_name(player),
                        "team": team,
                        "conference": conference,
                        "position": position,
                    },
                )
                stat_type = norm_field(str(row.get("statType", "")))
                if not stat_type:
                    continue
                record[f"{category}_{stat_type}"] = safe_float(record.get(f"{category}_{stat_type}", 0.0)) + safe_float(row.get("stat", ""))
    rows = list(grouped.values())
    for row in rows:
        add_feature_aliases(row)
    rows.sort(key=lambda row: (safe_int(row["season"]), str(row["position"]), str(row["player_name"])))
    return add_market_share_features(rows, build_team_seasons(output_dir))


def build_team_seasons(output_dir: Path) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for season in SEASONS:
        for row in read_csv(team_cache_path(output_dir, season)):
            team = str(row.get("team", "")).strip()
            conference = str(row.get("conference", "")).strip()
            stat_name = norm_field(str(row.get("statName", "")))
            if not team or not stat_name:
                continue
            key = (str(season), team, conference)
            record = grouped.setdefault(key, {"season": str(season), "team": team, "conference": conference})
            record[stat_name] = safe_float(record.get(stat_name, 0.0)) + safe_float(row.get("statValue", ""))
    rows = list(grouped.values())
    rows.sort(key=lambda row: (safe_int(row["season"]), str(row["team"])))
    return rows


def add_market_share_features(player_rows: list[dict[str, object]], team_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    team_lookup = {(str(row.get("season", "")), str(row.get("team", ""))): row for row in team_rows}
    output = []
    for row in player_rows:
        out = dict(row)
        team = team_lookup.get((str(row.get("season", "")), str(row.get("team", ""))), {})
        team_pass_yards = lookup_team_value(team, ["net_passing_yards", "passing_yards"])
        team_pass_attempts = lookup_team_value(team, ["pass_attempts", "passing_attempts"])
        team_pass_tds = lookup_team_value(team, ["passing_t_ds", "passing_tds", "passing_td"])
        team_rush_yards = lookup_team_value(team, ["rushing_yards"])
        team_rush_attempts = lookup_team_value(team, ["rushing_attempts", "rush_attempts"])
        team_rush_tds = lookup_team_value(team, ["rushing_t_ds", "rushing_tds", "rushing_td"])
        team_pass_completions = lookup_team_value(team, ["pass_completions", "passing_completions"])
        out["team_passing_yards"] = f"{team_pass_yards:.3f}" if team_pass_yards else ""
        out["team_pass_attempts"] = f"{team_pass_attempts:.3f}" if team_pass_attempts else ""
        out["team_passing_tds"] = f"{team_pass_tds:.3f}" if team_pass_tds else ""
        out["team_rushing_yards"] = f"{team_rush_yards:.3f}" if team_rush_yards else ""
        out["team_rushing_attempts"] = f"{team_rush_attempts:.3f}" if team_rush_attempts else ""
        out["team_rushing_tds"] = f"{team_rush_tds:.3f}" if team_rush_tds else ""
        out["team_pass_completions"] = f"{team_pass_completions:.3f}" if team_pass_completions else ""
        out["passing_yard_share"] = pct(safe_float(out.get("passing_yards")), team_pass_yards)
        out["passing_attempt_share"] = pct(safe_float(out.get("passing_attempts")), team_pass_attempts)
        out["passing_td_share"] = pct(safe_float(out.get("passing_tds")), team_pass_tds)
        out["rushing_yard_share"] = pct(safe_float(out.get("rushing_yards")), team_rush_yards)
        out["rushing_attempt_share"] = pct(safe_float(out.get("rushing_attempts")), team_rush_attempts)
        out["rushing_td_share"] = pct(safe_float(out.get("rushing_tds")), team_rush_tds)
        out["receiving_yard_share"] = pct(safe_float(out.get("receiving_yards")), team_pass_yards)
        out["reception_share"] = pct(safe_float(out.get("receptions")), team_pass_completions)
        out["receiving_td_share"] = pct(safe_float(out.get("receiving_tds")), team_pass_tds)
        out["source_safety"] = "cfbd_factual_regular_season_only"
        out["promotion_status"] = "local_feature_cache_only"
        out["production_allowed"] = "no"
        output.append(out)
    return output


def load_career_pool(current_rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    by_id: dict[str, list[dict[str, object]]] = {}
    for row in [*read_csv(HISTORICAL_PLAYER_FEATURES), *current_rows]:
        player_id = str(row.get("cfbd_player_id", "")).strip()
        if player_id:
            by_id.setdefault(player_id, []).append(row)
    for rows in by_id.values():
        rows.sort(key=lambda row: safe_int(row.get("season")))
    return by_id


def join_current_board(board_rows: list[dict[str, str]], feature_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_name_pos: dict[tuple[str, str], list[dict[str, object]]] = {}
    for feature in feature_rows:
        by_name_pos.setdefault((str(feature.get("normalized_player_name", "")), str(feature.get("position", "")).upper()), []).append(feature)
    joined = []
    for board in board_rows:
        position = board.get("position", "").upper()
        school = board.get("school", "")
        candidates = []
        seen_candidate_keys = set()
        for normalized in current_identity_keys(board):
            for row in by_name_pos.get((normalized, position), []):
                if safe_int(row.get("season")) not in SEASONS:
                    continue
                candidate_key = (row.get("season"), row.get("cfbd_player_id"), row.get("team"))
                if candidate_key in seen_candidate_keys:
                    continue
                seen_candidate_keys.add(candidate_key)
                candidates.append(row)
        exact_school = [row for row in candidates if str(row.get("team", "")).lower() == school.lower()]
        pool = exact_school or candidates
        pool.sort(key=lambda row: (safe_int(row.get("season")), source_feature_score(row)), reverse=True)
        selected = pool[0] if pool else {}
        status = "matched_name_position_school" if exact_school else "matched_name_position" if selected else "unmatched_current_identity"
        unique_ids = {str(row.get("cfbd_player_id", "")).strip() for row in pool if str(row.get("cfbd_player_id", "")).strip()}
        if len(unique_ids) > 1:
            status = f"{status}_duplicate_candidates"
        out = dict(board)
        out["cfbd_current_join_status"] = status
        out["cfbd_join_candidate_count"] = str(len(pool))
        out["cfbd_feature_season"] = selected.get("season", "")
        for column in FEATURE_COPY_COLUMNS:
            out[f"cfbd_{column}"] = selected.get(column, "")
        out["cfbd_denominator_status"] = denominator_status(out)
        out["cfbd_warning_flags"] = current_warning_flags(out)
        joined.append(out)
    return joined


def current_identity_keys(board: dict[str, str]) -> set[str]:
    keys = {
        norm_name(board.get("player_name", "")),
        norm_name(board.get("normalized_name", "")),
    }
    player_id = board.get("player_id", "")
    parts = player_id.split(":")
    if len(parts) >= 3:
        keys.add(norm_name(parts[2]))
    return {key for key in keys if key}


def source_feature_score(row: dict[str, object]) -> float:
    position = str(row.get("position", "")).upper()
    if position == "QB":
        return safe_float(row.get("passing_yards")) + safe_float(row.get("rushing_yards"))
    if position == "RB":
        return safe_float(row.get("rushing_yards")) + safe_float(row.get("receiving_yards"))
    return safe_float(row.get("receiving_yards")) + safe_float(row.get("rushing_yards"))


FEATURE_COPY_COLUMNS = [
    "cfbd_player_id",
    "player_name",
    "team",
    "conference",
    "position",
    "passing_yards",
    "passing_tds",
    "passing_attempts",
    "passing_completions",
    "rushing_yards",
    "rushing_tds",
    "rushing_attempts",
    "receiving_yards",
    "receiving_tds",
    "receptions",
    "team_passing_yards",
    "team_pass_attempts",
    "team_passing_tds",
    "team_rushing_yards",
    "team_rushing_attempts",
    "team_rushing_tds",
    "team_pass_completions",
    "passing_yard_share",
    "passing_attempt_share",
    "passing_td_share",
    "rushing_yard_share",
    "rushing_attempt_share",
    "rushing_td_share",
    "receiving_yard_share",
    "reception_share",
    "receiving_td_share",
    "source_safety",
    "promotion_status",
    "production_allowed",
]


def denominator_status(row: dict[str, object]) -> str:
    position = str(row.get("position", "")).upper()
    if not str(row.get("cfbd_current_join_status", "")).startswith("matched"):
        return "not_available_unmatched"
    if position == "QB":
        fields = ["cfbd_passing_yard_share", "cfbd_passing_attempt_share", "cfbd_passing_td_share"]
    elif position == "RB":
        fields = ["cfbd_rushing_yard_share", "cfbd_rushing_attempt_share", "cfbd_rushing_td_share"]
    else:
        fields = ["cfbd_receiving_yard_share", "cfbd_reception_share", "cfbd_receiving_td_share"]
    return "denominator_ready" if all(str(row.get(field, "")).strip() for field in fields) else "denominator_missing"


def current_warning_flags(row: dict[str, object]) -> str:
    warnings = []
    if "duplicate_candidates" in str(row.get("cfbd_current_join_status", "")):
        warnings.append("CFBD_DUPLICATE_CANDIDATE_REVIEW")
    if row.get("cfbd_denominator_status") == "denominator_missing":
        warnings.append("CFBD_DENOMINATOR_MISSING")
    if row.get("cfbd_denominator_status") == "not_available_unmatched":
        warnings.append("CFBD_UNMATCHED_CURRENT_IDENTITY")
    if safe_int(row.get("cfbd_feature_season")) < 2025 and str(row.get("cfbd_current_join_status", "")).startswith("matched"):
        warnings.append("CFBD_NO_2025_PROFILE_SELECTED")
    return "|".join(warnings) if warnings else "none"


def build_wr_feature_rows(joined_rows: list[dict[str, object]], career_pool: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    rows = []
    for row in joined_rows:
        if row.get("position") != "WR":
            continue
        player_id = str(row.get("cfbd_cfbd_player_id", "")).strip()
        career = [item for item in career_pool.get(player_id, []) if 2022 <= safe_int(item.get("season")) <= 2025]
        receiving_yards = [safe_float(item.get("receiving_yards")) for item in career]
        receptions = [safe_float(item.get("receptions")) for item in career]
        receiving_tds = [safe_float(item.get("receiving_tds")) for item in career]
        yard_shares = [safe_float(item.get("receiving_yard_share")) for item in career if str(item.get("receiving_yard_share", "")).strip()]
        reception_shares = [safe_float(item.get("reception_share")) for item in career if str(item.get("reception_share", "")).strip()]
        td_shares = [safe_float(item.get("receiving_td_share")) for item in career if str(item.get("receiving_td_share", "")).strip()]
        final_receptions = safe_float(row.get("cfbd_receptions"))
        final_ypr = safe_float(row.get("cfbd_receiving_yards")) / final_receptions if final_receptions >= 20 else 0.0
        productive = sum(1 for item in career if safe_float(item.get("receiving_yards")) >= 500 or safe_float(item.get("receiving_yard_share")) >= 0.18)
        meaningful_share = sum(1 for item in career if safe_float(item.get("receiving_yard_share")) >= 0.20 or safe_float(item.get("reception_share")) >= 0.18)
        best_yards = max(receiving_yards) if receiving_yards else 0.0
        best_yard_share = max(yard_shares) if yard_shares else 0.0
        best_reception_share = max(reception_shares) if reception_shares else 0.0
        best_td_share = max(td_shares) if td_shares else 0.0
        one_year_spike = productive == 1 and (best_yards >= 800 or best_yard_share >= 0.25)
        strong_late = safe_float(row.get("draft_capital", "").split("round=")[-1].split(";")[0] if "round=" in str(row.get("draft_capital", "")) else "") >= 3 and best_yards >= 900
        weak_early = safe_int(str(row.get("draft_capital", "")).split("round=")[-1].split(";")[0] if "round=" in str(row.get("draft_capital", "")) else "") <= 2 and best_yards < 650 and best_yard_share < 0.20
        no_production = best_yards < 350 and best_yard_share < 0.12
        denominator_missing = row.get("cfbd_denominator_status") != "denominator_ready"
        signal = wr_signal_score(
            final_yards=safe_float(row.get("cfbd_receiving_yards")),
            final_receptions=final_receptions,
            final_tds=safe_float(row.get("cfbd_receiving_tds")),
            final_yard_share=safe_float(row.get("cfbd_receiving_yard_share")),
            final_reception_share=safe_float(row.get("cfbd_reception_share")),
            final_td_share=safe_float(row.get("cfbd_receiving_td_share")),
            ypr=final_ypr,
            best_yards=best_yards,
            best_yard_share=best_yard_share,
            best_reception_share=best_reception_share,
            best_td_share=best_td_share,
            career_yards=sum(receiving_yards),
            career_receptions=sum(receptions),
            career_tds=sum(receiving_tds),
            productive_seasons=productive,
            meaningful_share_seasons=meaningful_share,
            strong_late=strong_late,
        )
        penalty = wr_warning_penalty(
            one_year_spike=one_year_spike,
            weak_early=weak_early,
            no_production=no_production,
            denominator_missing=denominator_missing,
            identity_warning="duplicate_candidates" in str(row.get("cfbd_current_join_status", "")),
        )
        rows.append(
            {
                "rookie_rank": row.get("rookie_rank", ""),
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "school": row.get("school", ""),
                "cfbd_current_join_status": row.get("cfbd_current_join_status", ""),
                "cfbd_feature_season": row.get("cfbd_feature_season", ""),
                "cfbd_denominator_status": row.get("cfbd_denominator_status", ""),
                "wr_career_seasons_found": str(len(career)),
                "wr_best_receiving_yards": f"{best_yards:.3f}",
                "wr_best_receiving_yard_share": f"{best_yard_share:.3f}" if yard_shares else "",
                "wr_career_receiving_yards": f"{sum(receiving_yards):.3f}",
                "wr_productive_seasons": str(productive),
                "wr_meaningful_share_seasons": str(meaningful_share),
                "wr_one_year_spike_flag": "yes" if one_year_spike else "no",
                "wr_early_capital_weak_profile_warning": "yes" if weak_early else "no",
                "wr_no_meaningful_production_warning": "yes" if no_production else "no",
                "wr_feature_signal_score": f"{capped(signal, 0.0, 100.0):.3f}",
                "wr_warning_penalty": f"{penalty:.3f}",
                "production_allowed": "no",
                "app_wiring_allowed": "no",
                "promotion_status": "local_manual_feature_context_only",
            }
        )
    return rows


def coverage_by_position(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for position in POSITIONS:
        scoped = [row for row in rows if row.get("position") == position]
        matched = [row for row in scoped if str(row.get("cfbd_current_join_status", "")).startswith("matched")]
        denom = [row for row in matched if row.get("cfbd_denominator_status") == "denominator_ready"]
        output.append(
            {
                "position": position,
                "current_rows": len(scoped),
                "matched_rows": len(matched),
                "unmatched_rows": len(scoped) - len(matched),
                "denominator_ready_rows": len(denom),
                "matched_rate": f"{len(matched) / len(scoped):.3f}" if scoped else "0.000",
                "denominator_ready_rate": f"{len(denom) / len(scoped):.3f}" if scoped else "0.000",
            }
        )
    return output


def rank_movement(old_rows: list[dict[str, str]], new_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    old_rank = {row["player_id"]: safe_int(row.get("rookie_rank")) for row in old_rows}
    rows = []
    for row in new_rows:
        before = old_rank.get(str(row.get("player_id", "")), 0)
        after = safe_int(row.get("rookie_rank"))
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "old_rank": before,
                "feature_ingested_rank": after,
                "rank_delta": before - after,
                "movement_reason": "rank preserved; CFBD features appended for manual context only",
            }
        )
    rows.sort(key=lambda row: (abs(int(row["rank_delta"])), -int(row["old_rank"])), reverse=True)
    return rows


def write_readme(output_dir: Path, coverage: list[dict[str, object]], candidate_created: bool) -> None:
    text = [
        "# Current 2026 CFBD Feature Ingestion",
        "",
        "Local-only current rookie CFBD feature ingestion exports.",
        "",
        f"- candidate/v2 board created: {'yes' if candidate_created else 'no'}",
        f"- coverage by position: {coverage}",
        "",
        "The feature-ingested board preserves existing rank order and appends source-safe CFBD context only.",
        "No production ranking, app wiring, probabilities, bands, hidden sort keys, or promoted artifacts.",
    ]
    (output_dir / "README_CURRENT_2026_CFBD_FEATURE_INGESTION_20260615.md").write_text("\n".join(text), encoding="utf-8")


MANIFEST_COLUMNS = ["season", "endpoint", "category", "status", "row_count", "field_count", "cache_path", "error_type"]
BASE_PLAYER_COLUMNS = [
    "season",
    "cfbd_player_id",
    "player_name",
    "normalized_player_name",
    "team",
    "conference",
    "position",
    "passing_yards",
    "passing_tds",
    "passing_attempts",
    "passing_completions",
    "rushing_yards",
    "rushing_tds",
    "rushing_attempts",
    "receiving_yards",
    "receiving_tds",
    "receptions",
    "team_passing_yards",
    "team_pass_attempts",
    "team_passing_tds",
    "team_rushing_yards",
    "team_rushing_attempts",
    "team_rushing_tds",
    "team_pass_completions",
    "passing_yard_share",
    "passing_attempt_share",
    "passing_td_share",
    "rushing_yard_share",
    "rushing_attempt_share",
    "rushing_td_share",
    "receiving_yard_share",
    "reception_share",
    "receiving_td_share",
    "source_safety",
    "promotion_status",
    "production_allowed",
]


def all_columns(rows: list[dict[str, object]]) -> list[str]:
    columns = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def build_exports(
    *,
    output_dir: Path,
    current_board: Path,
    force_refresh: bool = False,
    skip_fetch: bool = False,
    sleep_seconds: float = 1.1,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = fetch_current_cache(output_dir, force_refresh=force_refresh, skip_fetch=skip_fetch, sleep_seconds=sleep_seconds)
    player_features = build_player_seasons(output_dir)
    board_rows = read_csv(current_board)
    joined = join_current_board(board_rows, player_features)
    career_pool = load_career_pool(player_features)
    wr_features = build_wr_feature_rows(joined, career_pool)
    coverage = coverage_by_position(joined)
    movement = rank_movement(board_rows, joined)
    candidate_created = False
    write_csv(output_dir / "cfbd_current_2026_fetch_manifest_20260615.csv", manifest, MANIFEST_COLUMNS)
    write_csv(output_dir / "cfbd_current_2026_player_features_20260615.csv", player_features, BASE_PLAYER_COLUMNS)
    write_csv(output_dir / "current_2026_cfbd_feature_join_20260615.csv", joined, all_columns(joined))
    write_csv(output_dir / "current_2026_cfbd_feature_coverage_by_position_20260615.csv", coverage, ["position", "current_rows", "matched_rows", "unmatched_rows", "denominator_ready_rows", "matched_rate", "denominator_ready_rate"])
    write_csv(output_dir / "current_2026_wr_feature_quality_table_20260615.csv", wr_features, all_columns(wr_features))
    write_csv(output_dir / "current_2026_feature_ingested_manual_board_20260615.csv", joined, all_columns(joined))
    write_csv(output_dir / "current_2026_rank_movement_20260615.csv", movement, ["player_id", "player_name", "position", "old_rank", "feature_ingested_rank", "rank_delta", "movement_reason"])
    write_readme(output_dir, coverage, candidate_created)
    return {
        "manifest": manifest,
        "player_features": player_features,
        "joined": joined,
        "wr_features": wr_features,
        "coverage": coverage,
        "rank_movement": movement,
        "candidate_created": candidate_created,
        "manifest_statuses": Counter(row["status"] for row in manifest),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--current-board", type=Path, default=CURRENT_BOARD)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.1)
    args = parser.parse_args(argv)
    result = build_exports(
        output_dir=args.output_dir,
        current_board=args.current_board,
        force_refresh=args.force_refresh,
        skip_fetch=args.skip_fetch,
        sleep_seconds=args.sleep_seconds,
    )
    coverage = {row["position"]: row for row in result["coverage"]}
    print(f"player_feature_rows={len(result['player_features'])}")
    print(f"current_board_rows={len(result['joined'])}")
    print("coverage=" + ";".join(f"{pos}:{coverage[pos]['matched_rows']}/{coverage[pos]['current_rows']}" for pos in POSITIONS))
    print(f"candidate_created={'yes' if result['candidate_created'] else 'no'}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
