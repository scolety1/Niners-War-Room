"""Audit and repair rookie CFBD historical identity joins.

This script uses the local-only CFBD historical feature cache v1 outputs,
fetches only the approved 2009 regular-season CFBD endpoints when needed for
the 2010 draft class, and writes repair-audit exports. It does not tune, create
a v2 board, write app-readable artifacts, or print API secrets.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.config.api_settings import get_api_settings  # noqa: E402


BASE_CACHE = Path("local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/cfbd_identity_join_repair_20260615")
POSITIONS = {"QB", "RB", "WR", "TE"}
PLAYER_CATEGORIES = ["passing", "rushing", "receiving"]
TEAM_ALIASES = {
    "california": {"cal", "california"},
    "pennst": {"pennstate", "pennst"},
    "pennstate": {"pennstate", "pennst"},
    "oklahomast": {"oklahomastate", "oklahomast"},
    "mississippi": {"olemiss", "mississippi"},
    "floridast": {"floridastate", "floridast"},
    "fresnost": {"fresnostate", "fresnost"},
    "boisest": {"boisestate", "boisest"},
    "arizonast": {"arizonastate", "arizonast"},
    "michiganst": {"michiganstate", "michiganst"},
    "iowast": {"iowastate", "iowast"},
    "ncst": {"ncstate", "ncst"},
    "usf": {"southflorida", "usf"},
    "ucf": {"ucf", "centralflorida"},
    "utsa": {"utsa", "texassanantonio"},
}


def load_local_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key in {"CFBD_API_KEY", "CFBD_API_BASE", "MODEL_V4_LIVE_API_ENABLED"}:
            os.environ.setdefault(key, value.strip())


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)


def norm_field(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).lower()
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()


def team_matches(label_college: str, feature_team: str) -> bool:
    label = norm_text(label_college)
    team = norm_text(feature_team)
    if not label or not team:
        return False
    if label == team or label in team or team in label:
        return True
    return bool(TEAM_ALIASES.get(label, set()) & TEAM_ALIASES.get(team, {team}))


def safe_float(value: object) -> float:
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(str(value))
    except ValueError:
        return 0.0


def safe_int(value: object) -> int:
    try:
        if value is None or str(value).strip() == "":
            return 0
        return int(float(str(value)))
    except ValueError:
        return 0


def pct(num: float, den: float) -> str:
    return f"{num / den:.6f}" if den else ""


def fetch_json(base: str, key: str, endpoint: str, params: dict[str, str]) -> list[dict[str, object]]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{base.rstrip('/')}{endpoint}?{query}",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [row for row in payload if isinstance(row, dict)] if isinstance(payload, list) else []


def maybe_fetch_2009(output_dir: Path, *, sleep_seconds: float, force_refresh: bool) -> list[dict[str, object]]:
    load_local_dotenv()
    settings = get_api_settings()
    if not settings.cfbd_api_key:
        raise RuntimeError("CFBD_API_KEY is not configured; no request sent.")
    if not settings.live_api_enabled:
        raise RuntimeError("MODEL_V4_LIVE_API_ENABLED is not true; no request sent.")

    rows: list[dict[str, object]] = []
    raw_dir = output_dir / "raw_cfbd_2009_csv"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for category in PLAYER_CATEGORIES:
        path = raw_dir / f"player_stats_season_2009_regular_{category}.csv"
        params = {"year": "2009", "seasonType": "regular", "category": category}
        rows.append(
            cache_endpoint(
                path,
                settings.cfbd_api_base,
                settings.cfbd_api_key,
                "/stats/player/season",
                params,
                force_refresh,
                sleep_seconds,
            )
        )
    path = raw_dir / "team_stats_season_2009_regular.csv"
    rows.append(
        cache_endpoint(
            path,
            settings.cfbd_api_base,
            settings.cfbd_api_key,
            "/stats/season",
            {"year": "2009", "seasonType": "regular"},
            force_refresh,
            sleep_seconds,
        )
    )
    return rows


def cache_endpoint(
    path: Path,
    base: str,
    key: str,
    endpoint: str,
    params: dict[str, str],
    force_refresh: bool,
    sleep_seconds: float,
) -> dict[str, object]:
    if path.exists() and not force_refresh:
        rows = read_csv(path)
        return manifest_row(params, endpoint, "cache_hit", len(rows), len(rows[0].keys()) if rows else 0, path, "")
    try:
        rows = fetch_json(base, key, endpoint, params)
        columns = sorted({column for row in rows for column in row.keys()})
        write_csv(path, rows, columns)
        status = "fetched"
        error = ""
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        rows = []
        columns = []
        status = "fetch_failed"
        error = type(exc).__name__
    time.sleep(sleep_seconds)
    return manifest_row(params, endpoint, status, len(rows), len(columns), path, error)


def manifest_row(
    params: dict[str, str],
    endpoint: str,
    status: str,
    row_count: int,
    field_count: int,
    path: Path,
    error: str,
) -> dict[str, object]:
    return {
        "year": params.get("year", ""),
        "endpoint": endpoint,
        "category": params.get("category", "team_denominators"),
        "season_type": params.get("seasonType", ""),
        "status": status,
        "row_count": row_count,
        "field_count": field_count,
        "cache_path": str(path),
        "error_type": error,
    }


def build_2009_features(output_dir: Path) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    raw_dir = output_dir / "raw_cfbd_2009_csv"
    for category in PLAYER_CATEGORIES:
        path = raw_dir / f"player_stats_season_2009_regular_{category}.csv"
        for row in read_csv(path):
            player = row.get("player", "").strip()
            position = row.get("position", "").strip().upper()
            if not player or position not in POSITIONS:
                continue
            key = (
                "2009",
                row.get("playerId", "").strip(),
                player,
                row.get("team", "").strip(),
                position,
            )
            record = grouped.setdefault(
                key,
                {
                    "season": "2009",
                    "cfbd_player_id": row.get("playerId", "").strip(),
                    "player_name": player,
                    "normalized_player_name": norm_text(player),
                    "team": row.get("team", "").strip(),
                    "conference": row.get("conference", "").strip(),
                    "position": position,
                },
            )
            stat_type = norm_field(row.get("statType", ""))
            if stat_type:
                column = f"{category}_{stat_type}"
                record[column] = safe_float(record.get(column, 0)) + safe_float(row.get("stat"))
    players = list(grouped.values())
    for row in players:
        add_alias_columns(row)
    teams = build_2009_team_rows(output_dir)
    return add_share_columns(players, teams)


def build_2009_team_rows(output_dir: Path) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in read_csv(output_dir / "raw_cfbd_2009_csv" / "team_stats_season_2009_regular.csv"):
        team = row.get("team", "").strip()
        conference = row.get("conference", "").strip()
        stat_name = norm_field(row.get("statName", ""))
        if not team or not stat_name:
            continue
        record = grouped.setdefault(("2009", team), {"season": "2009", "team": team, "conference": conference})
        record[stat_name] = safe_float(record.get(stat_name, 0)) + safe_float(row.get("statValue"))
    return list(grouped.values())


def add_alias_columns(row: dict[str, object]) -> None:
    row["passing_yards"] = first_value(row, ["passing_yds", "passing_yards"])
    row["passing_tds"] = first_value(row, ["passing_td", "passing_tds"])
    row["passing_attempts"] = first_value(row, ["passing_att", "passing_attempts"])
    row["passing_completions"] = first_value(row, ["passing_completions", "passing_cmp"])
    row["passing_ints"] = first_value(row, ["passing_int", "passing_ints"])
    row["rushing_yards"] = first_value(row, ["rushing_yds", "rushing_yards"])
    row["rushing_tds"] = first_value(row, ["rushing_td", "rushing_tds"])
    row["rushing_attempts"] = first_value(row, ["rushing_car", "rushing_att", "rushing_attempts"])
    row["receiving_yards"] = first_value(row, ["receiving_yds", "receiving_yards"])
    row["receiving_tds"] = first_value(row, ["receiving_td", "receiving_tds"])
    row["receptions"] = first_value(row, ["receiving_rec", "receiving_receptions"])


def first_value(row: dict[str, object], columns: list[str]) -> str:
    for column in columns:
        value = safe_float(row.get(column))
        if value:
            return f"{value:.3f}"
    return ""


def add_share_columns(players: list[dict[str, object]], teams: list[dict[str, object]]) -> list[dict[str, object]]:
    teams_by_key = {(row.get("season", ""), row.get("team", "")): row for row in teams}
    out: list[dict[str, object]] = []
    for row in players:
        new = dict(row)
        team = teams_by_key.get((row.get("season", ""), row.get("team", "")), {})
        team_pass_yards = team_value(team, ["net_passing_yards", "passing_yards"])
        team_pass_attempts = team_value(team, ["pass_attempts", "passing_attempts"])
        team_pass_tds = team_value(team, ["passing_t_ds", "passing_tds", "passing_td"])
        team_rush_yards = team_value(team, ["rushing_yards"])
        team_rush_attempts = team_value(team, ["rushing_attempts", "rush_attempts"])
        team_rush_tds = team_value(team, ["rushing_t_ds", "rushing_tds", "rushing_td"])
        team_pass_completions = team_value(team, ["pass_completions", "passing_completions"])
        new["team_passing_yards"] = f"{team_pass_yards:.3f}" if team_pass_yards else ""
        new["team_pass_attempts"] = f"{team_pass_attempts:.3f}" if team_pass_attempts else ""
        new["team_passing_tds"] = f"{team_pass_tds:.3f}" if team_pass_tds else ""
        new["team_rushing_yards"] = f"{team_rush_yards:.3f}" if team_rush_yards else ""
        new["team_rushing_attempts"] = f"{team_rush_attempts:.3f}" if team_rush_attempts else ""
        new["team_rushing_tds"] = f"{team_rush_tds:.3f}" if team_rush_tds else ""
        new["team_pass_completions"] = f"{team_pass_completions:.3f}" if team_pass_completions else ""
        new["passing_yard_share"] = pct(safe_float(new.get("passing_yards")), team_pass_yards)
        new["passing_attempt_share"] = pct(safe_float(new.get("passing_attempts")), team_pass_attempts)
        new["passing_td_share"] = pct(safe_float(new.get("passing_tds")), team_pass_tds)
        new["rushing_yard_share"] = pct(safe_float(new.get("rushing_yards")), team_rush_yards)
        new["rushing_attempt_share"] = pct(safe_float(new.get("rushing_attempts")), team_rush_attempts)
        new["rushing_td_share"] = pct(safe_float(new.get("rushing_tds")), team_rush_tds)
        new["receiving_yard_share"] = pct(safe_float(new.get("receiving_yards")), team_pass_yards)
        new["reception_share"] = pct(safe_float(new.get("receptions")), team_pass_completions)
        new["receiving_td_share"] = pct(safe_float(new.get("receiving_tds")), team_pass_tds)
        new["source_safety"] = "cfbd_factual_regular_season_only"
        new["promotion_status"] = "local_feature_cache_only"
        new["production_allowed"] = "no"
        out.append(new)
    return out


def team_value(row: dict[str, object], columns: list[str]) -> float:
    for column in columns:
        value = safe_float(row.get(column))
        if value:
            return value
    return 0.0


FEATURE_COLUMNS = [
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
    "passing_ints",
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


def load_feature_rows(base_cache: Path, output_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        dict(row) for row in read_csv(base_cache / "cfbd_player_season_features_v1_20260615.csv")
    ]
    rows.extend(build_2009_features(output_dir))
    return rows


def feature_score(row: dict[str, object]) -> float:
    position = str(row.get("position", "")).upper()
    if position == "QB":
        return safe_float(row.get("passing_yards")) + safe_float(row.get("rushing_yards"))
    if position == "RB":
        return safe_float(row.get("rushing_yards")) + safe_float(row.get("receiving_yards"))
    return safe_float(row.get("receiving_yards")) + safe_float(row.get("rushing_yards"))


def name_parts(name: str) -> tuple[str, str]:
    cleaned = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    tokens = [re.sub(r"[^A-Za-z0-9]", "", token).lower() for token in cleaned.split()]
    tokens = [token for token in tokens if token and token not in {"jr", "sr", "ii", "iii", "iv", "v"}]
    if not tokens:
        return "", ""
    return tokens[0][:1], tokens[-1]


def index_features(features: list[dict[str, object]]) -> dict[str, dict[tuple[str, ...], list[dict[str, object]]]]:
    indexes: dict[str, dict[tuple[str, ...], list[dict[str, object]]]] = {
        "exact": defaultdict(list),
        "name_any_position": defaultdict(list),
        "last_initial": defaultdict(list),
    }
    for row in features:
        season = str(row.get("season", ""))
        name = str(row.get("normalized_player_name", ""))
        position = str(row.get("position", "")).upper()
        first_initial, last = name_parts(str(row.get("player_name", "")))
        indexes["exact"][(season, name, position)].append(row)
        indexes["name_any_position"][(season, name)].append(row)
        if first_initial and last:
            indexes["last_initial"][(season, first_initial, last, position)].append(row)
    return indexes


def repair_join_rows(
    base_cache: Path, output_dir: Path
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    original_rows = read_csv(base_cache / "cfbd_drafted_rookie_feature_join_v1_20260615.csv")
    features = load_feature_rows(base_cache, output_dir)
    indexes = index_features(features)
    repaired: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []
    duplicate_rows: list[dict[str, object]] = []

    for row in original_rows:
        analysis = analyze_row(row, indexes)
        repaired_row = build_repaired_row(row, analysis)
        repaired.append(repaired_row)
        audit_rows.append(
            {
                "historical_label_key": row.get("historical_label_key", ""),
                "draft_year": row.get("draft_year", ""),
                "expected_cfbd_feature_season": row.get("expected_cfbd_feature_season", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "college": row.get("college", ""),
                "before_status": row.get("cfbd_join_status", ""),
                "after_status": repaired_row.get("cfbd_join_status_after_repair", ""),
                "repair_classification": analysis["classification"],
                "repair_action": analysis["action"],
                "candidate_count": analysis["candidate_count"],
                "repair_notes": analysis["notes"],
            }
        )
        if analysis["candidate_count"] and "duplicate" in analysis["classification"]:
            for candidate in analysis.get("candidates", []):
                duplicate_rows.append(
                    {
                        "historical_label_key": row.get("historical_label_key", ""),
                        "draft_year": row.get("draft_year", ""),
                        "expected_cfbd_feature_season": row.get("expected_cfbd_feature_season", ""),
                        "label_player_name": row.get("player_name", ""),
                        "label_position": row.get("position", ""),
                        "label_college": row.get("college", ""),
                        "candidate_player_name": candidate.get("player_name", ""),
                        "candidate_position": candidate.get("position", ""),
                        "candidate_team": candidate.get("team", ""),
                        "candidate_cfbd_player_id": candidate.get("cfbd_player_id", ""),
                        "candidate_feature_score": f"{feature_score(candidate):.3f}",
                    }
                )
        elif analysis["classification"] == "duplicate_candidate_existing":
            duplicate_rows.append(
                {
                    "historical_label_key": row.get("historical_label_key", ""),
                    "draft_year": row.get("draft_year", ""),
                    "expected_cfbd_feature_season": row.get("expected_cfbd_feature_season", ""),
                    "label_player_name": row.get("player_name", ""),
                    "label_position": row.get("position", ""),
                    "label_college": row.get("college", ""),
                    "candidate_player_name": row.get("player_name", ""),
                    "candidate_position": row.get("position", ""),
                    "candidate_team": row.get("team", ""),
                    "candidate_cfbd_player_id": row.get("cfbd_player_id", ""),
                    "candidate_feature_score": "existing_v1_selected",
                }
            )
    return repaired, audit_rows, duplicate_rows


def analyze_row(row: dict[str, str], indexes: dict[str, dict[tuple[str, ...], list[dict[str, object]]]]) -> dict[str, object]:
    before = row.get("cfbd_join_status", "")
    if before in {"matched_name_position_season", "matched_with_duplicate_candidate_selection"}:
        return {
            "classification": "already_matched" if before == "matched_name_position_season" else "duplicate_candidate_existing",
            "action": "kept_existing_match",
            "status": before,
            "candidate": None,
            "candidates": [],
            "candidate_count": 0,
            "notes": "Existing v1 match retained.",
        }
    season = row.get("expected_cfbd_feature_season", "")
    name = row.get("normalized_player_name") or norm_text(row.get("player_name", ""))
    position = row.get("position", "").upper()
    college = row.get("college", "")
    exact = indexes["exact"].get((season, name, position), [])
    if exact:
        return choose_candidate(row, exact, "id_or_alias_repaired", "matched_exact_after_repair", "Exact normalized name/position matched after adding repair cache.")
    any_position = [
        candidate
        for candidate in indexes["name_any_position"].get((season, name), [])
        if team_matches(college, str(candidate.get("team", "")))
    ]
    if any_position:
        return choose_candidate(row, any_position, "position_mismatch_repaired", "matched_position_mismatch_repaired", "Exact name and college/team matched with CFBD position mismatch.")
    first_initial, last = name_parts(row.get("player_name", ""))
    alias = [
        candidate
        for candidate in indexes["last_initial"].get((season, first_initial, last, position), [])
        if team_matches(college, str(candidate.get("team", "")))
    ]
    if alias:
        return choose_candidate(row, alias, "alias_issue_repaired", "matched_alias_repaired", "First-initial/last-name plus college/team/position matched deterministically.")
    same_name = indexes["name_any_position"].get((season, name), [])
    if same_name:
        return {
            "classification": "position_mismatch_manual_review",
            "action": "not_repaired",
            "status": "unmatched_position_mismatch_manual_review",
            "candidate": None,
            "candidates": same_name,
            "candidate_count": len(same_name),
            "notes": "Same normalized name exists in CFBD season but college/team evidence was not deterministic.",
        }
    school_position = [
        candidate
        for key, candidates in indexes["exact"].items()
        if key[0] == season and key[2] == position
        for candidate in candidates
        if team_matches(college, str(candidate.get("team", "")))
    ]
    if school_position:
        return {
            "classification": "cfbd_missing_row_or_alias_not_deterministic",
            "action": "not_repaired",
            "status": "unmatched_cfbd_missing_or_alias_manual_review",
            "candidate": None,
            "candidates": [],
            "candidate_count": 0,
            "notes": "College/team and position have CFBD rows, but no deterministic player identity match.",
        }
    return {
        "classification": "cfbd_missing_row_or_no_college_stat_profile",
        "action": "not_repaired",
        "status": "unmatched_cfbd_missing_row",
        "candidate": None,
        "candidates": [],
        "candidate_count": 0,
        "notes": "No deterministic CFBD feature row found for expected season/name/position.",
    }


def choose_candidate(
    row: dict[str, str],
    candidates: list[dict[str, object]],
    classification: str,
    status: str,
    notes: str,
) -> dict[str, object]:
    ranked = sorted(candidates, key=feature_score, reverse=True)
    candidate = ranked[0]
    if len(ranked) > 1:
        classification = "duplicate_candidate_repaired"
        status = "matched_duplicate_candidate_selected"
        notes = f"{notes} Multiple candidates found; highest production row selected for audit export."
    return {
        "classification": classification,
        "action": "repaired",
        "status": status,
        "candidate": candidate,
        "candidates": ranked,
        "candidate_count": len(ranked),
        "notes": notes,
    }


JOIN_COLUMNS = [
    "historical_label_key",
    "draft_year",
    "expected_cfbd_feature_season",
    "player_name",
    "normalized_player_name",
    "position",
    "college",
    "draft_round",
    "overall_pick",
    "label_status",
    "backtest_ready",
    "partial_window_only",
    "cfbd_join_status_before_repair",
    "cfbd_join_status_after_repair",
    "repair_classification",
    "repair_action",
    "join_candidate_count_after_repair",
    "feature_source_safety",
    "promotion_status",
    "production_allowed",
] + FEATURE_COLUMNS


def build_repaired_row(row: dict[str, str], analysis: dict[str, object]) -> dict[str, object]:
    repaired: dict[str, object] = {
        "historical_label_key": row.get("historical_label_key", ""),
        "draft_year": row.get("draft_year", ""),
        "expected_cfbd_feature_season": row.get("expected_cfbd_feature_season", ""),
        "player_name": row.get("player_name", ""),
        "normalized_player_name": row.get("normalized_player_name", ""),
        "position": row.get("position", ""),
        "college": row.get("college", ""),
        "draft_round": row.get("draft_round", ""),
        "overall_pick": row.get("overall_pick", ""),
        "label_status": row.get("label_status", ""),
        "backtest_ready": row.get("backtest_ready", ""),
        "partial_window_only": row.get("partial_window_only", ""),
        "cfbd_join_status_before_repair": row.get("cfbd_join_status", ""),
        "cfbd_join_status_after_repair": analysis["status"],
        "repair_classification": analysis["classification"],
        "repair_action": analysis["action"],
        "join_candidate_count_after_repair": analysis["candidate_count"],
        "feature_source_safety": "cfbd_factual_regular_season_only",
        "promotion_status": "local_feature_cache_only",
        "production_allowed": "no",
    }
    candidate = analysis.get("candidate")
    if candidate:
        for column in FEATURE_COLUMNS:
            repaired[column] = candidate.get(column, "")
    elif row.get("cfbd_join_status", "").startswith("matched"):
        for column in FEATURE_COLUMNS:
            repaired[column] = row.get(column, "")
    return repaired


def build_summary(
    before_rows: list[dict[str, str]], after_rows: list[dict[str, object]], manifest: list[dict[str, object]]
) -> list[dict[str, object]]:
    before_counts = summarize_before(before_rows)
    after_counts = summarize_after(after_rows)
    rows: list[dict[str, object]] = []
    for key, count in before_counts.items():
        rows.append({"phase": "before", "metric": key, "row_count": count})
    for key, count in after_counts.items():
        rows.append({"phase": "after", "metric": key, "row_count": count})
    rows.append({"phase": "fetch_2009", "metric": "endpoint_rows", "row_count": len(manifest)})
    rows.append(
        {
            "phase": "fetch_2009",
            "metric": "failed_endpoint_rows",
            "row_count": sum(1 for row in manifest if row.get("status") == "fetch_failed"),
        }
    )
    return rows


def summarize_before(rows: list[dict[str, str]]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        status = row.get("cfbd_join_status", "")
        if status.startswith("matched"):
            counts["matched"] += 1
        elif status == "blocked_expected_season_outside_cache":
            counts["outside_cache"] += 1
        elif status == "unmatched_name_position_season":
            counts["unmatched"] += 1
        if "duplicate" in status:
            counts["duplicate"] += 1
    return counts


def summarize_after(rows: list[dict[str, object]]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        status = str(row.get("cfbd_join_status_after_repair", ""))
        if status.startswith("matched"):
            counts["matched"] += 1
        elif status.startswith("unmatched"):
            counts["unmatched"] += 1
        elif "outside_cache" in status:
            counts["outside_cache"] += 1
        if "duplicate" in status or "duplicate" in str(row.get("repair_classification", "")):
            counts["duplicate"] += 1
        if status.startswith("excluded"):
            counts["excluded"] += 1
    return counts


def write_readme(output_dir: Path, summary: list[dict[str, object]]) -> None:
    text = [
        "# Rookie CFBD Identity Join Repair",
        "",
        "Local-only repair audit exports. These files are not tuning inputs until",
        "HQ/Tim approves the repaired join for an enriched baseline run.",
        "",
    ]
    for row in summary:
        text.append(f"- {row['phase']} {row['metric']}: {row['row_count']}")
    text.append("")
    text.append("API secrets are not written. Raw 2009 endpoint cache is local-only.")
    (output_dir / "README_ROOKIE_CFBD_IDENTITY_JOIN_REPAIR_20260615.md").write_text(
        "\n".join(text), encoding="utf-8"
    )


def build_exports(
    output_dir: Path,
    *,
    base_cache: Path = BASE_CACHE,
    fetch_2009: bool = True,
    force_refresh: bool = False,
    sleep_seconds: float = 1.1,
) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    if fetch_2009:
        manifest = maybe_fetch_2009(output_dir, sleep_seconds=sleep_seconds, force_refresh=force_refresh)
    write_csv(
        output_dir / "cfbd_2009_fetch_manifest_20260615.csv",
        manifest,
        ["year", "endpoint", "category", "season_type", "status", "row_count", "field_count", "cache_path", "error_type"],
    )
    features_2009 = build_2009_features(output_dir)
    write_csv(output_dir / "cfbd_2009_player_season_features_20260615.csv", features_2009, FEATURE_COLUMNS)
    repaired, audit_rows, duplicate_rows = repair_join_rows(base_cache, output_dir)
    before_rows = read_csv(base_cache / "cfbd_drafted_rookie_feature_join_v1_20260615.csv")
    summary = build_summary(before_rows, repaired, manifest)
    write_csv(output_dir / "cfbd_identity_join_repair_audit_20260615.csv", audit_rows, [
        "historical_label_key",
        "draft_year",
        "expected_cfbd_feature_season",
        "player_name",
        "position",
        "college",
        "before_status",
        "after_status",
        "repair_classification",
        "repair_action",
        "candidate_count",
        "repair_notes",
    ])
    write_csv(output_dir / "cfbd_drafted_rookie_feature_join_repaired_20260615.csv", repaired, JOIN_COLUMNS)
    write_csv(output_dir / "cfbd_duplicate_candidate_review_20260615.csv", duplicate_rows, [
        "historical_label_key",
        "draft_year",
        "expected_cfbd_feature_season",
        "label_player_name",
        "label_position",
        "label_college",
        "candidate_player_name",
        "candidate_position",
        "candidate_team",
        "candidate_cfbd_player_id",
        "candidate_feature_score",
    ])
    write_csv(output_dir / "cfbd_identity_join_repair_summary_20260615.csv", summary, ["phase", "metric", "row_count"])
    write_readme(output_dir, summary)
    after_counts = summarize_after(repaired)
    return {
        "manifest_rows": len(manifest),
        "features_2009_rows": len(features_2009),
        "repair_audit_rows": len(audit_rows),
        "repaired_join_rows": len(repaired),
        "after_matched_rows": after_counts["matched"],
        "after_unmatched_rows": after_counts["unmatched"],
        "after_outside_cache_rows": after_counts["outside_cache"],
        "after_duplicate_rows": after_counts["duplicate"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-cache", type=Path, default=BASE_CACHE)
    parser.add_argument("--skip-fetch-2009", action="store_true")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.1)
    args = parser.parse_args(argv)
    counts = build_exports(
        args.output_dir,
        base_cache=args.base_cache,
        fetch_2009=not args.skip_fetch_2009,
        force_refresh=args.force_refresh,
        sleep_seconds=args.sleep_seconds,
    )
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
