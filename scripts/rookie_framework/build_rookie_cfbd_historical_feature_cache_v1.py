"""Build a local-only CFBD historical feature cache for rookie audits.

This fetches only approved CollegeFootballData regular-season endpoints:
passing, rushing, receiving, and team season stats for 2010-2023. It writes
local-only exports, builds source-safe college production/team denominator
features, and joins them to the drafted QB/RB/WR/TE historical pool.

No API key is printed or written. No tuning, v2 board, app wiring, probability,
band, production ranking, or promoted artifact is created.
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
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.config.api_settings import get_api_settings  # noqa: E402


YEARS = list(range(2010, 2024))
PLAYER_CATEGORIES = ["passing", "rushing", "receiving"]
POSITIONS = {"QB", "RB", "WR", "TE"}
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/cfbd_historical_feature_cache_v1_20260615")
DEFAULT_LABELS = Path(
    "local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/"
    "expanded_historical_labels_v2_20260615.csv"
)


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


def write_csv(path: Path, rows: Iterable[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def norm_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)


def norm_field(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).lower()
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return value


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


def pct(numerator: float, denominator: float) -> str:
    if denominator <= 0:
        return ""
    return f"{numerator / denominator:.6f}"


def request_cfbd(base: str, key: str, endpoint: str, params: dict[str, str]) -> list[dict[str, object]]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{base.rstrip('/')}{endpoint}?{query}",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        return []
    return [row for row in payload if isinstance(row, dict)]


def endpoint_cache_path(output_dir: Path, year: int, category: str) -> Path:
    return output_dir / "raw_cfbd_csv" / f"player_stats_season_{year}_regular_{category}.csv"


def team_cache_path(output_dir: Path, year: int) -> Path:
    return output_dir / "raw_cfbd_csv" / f"team_stats_season_{year}_regular.csv"


def cache_endpoint(
    *,
    output_dir: Path,
    api_base: str,
    api_key: str,
    endpoint: str,
    params: dict[str, str],
    path: Path,
    force_refresh: bool,
    sleep_seconds: float,
) -> dict[str, object]:
    if path.exists() and not force_refresh:
        rows = read_csv(path)
        return {
            "year": params.get("year", ""),
            "endpoint": endpoint,
            "category": params.get("category", "team_denominators"),
            "season_type": params.get("seasonType", ""),
            "status": "cache_hit",
            "row_count": len(rows),
            "field_count": len(rows[0].keys()) if rows else 0,
            "cache_path": str(path.relative_to(output_dir)),
            "error_type": "",
        }
    try:
        payload = request_cfbd(api_base, api_key, endpoint, params)
        columns = sorted({key for row in payload for key in row.keys()})
        write_csv(path, payload, columns)
        status = "fetched"
        error_type = ""
        row_count = len(payload)
        field_count = len(columns)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        status = "fetch_failed"
        error_type = type(exc).__name__
        row_count = 0
        field_count = 0
    time.sleep(sleep_seconds)
    return {
        "year": params.get("year", ""),
        "endpoint": endpoint,
        "category": params.get("category", "team_denominators"),
        "season_type": params.get("seasonType", ""),
        "status": status,
        "row_count": row_count,
        "field_count": field_count,
        "cache_path": str(path.relative_to(output_dir)),
        "error_type": error_type,
    }


def fetch_cache(output_dir: Path, *, force_refresh: bool, sleep_seconds: float) -> list[dict[str, object]]:
    load_local_dotenv()
    settings = get_api_settings()
    if not settings.cfbd_api_key:
        raise RuntimeError("CFBD_API_KEY is not configured; no request sent.")
    if not settings.live_api_enabled:
        raise RuntimeError("MODEL_V4_LIVE_API_ENABLED is not true; no request sent.")

    manifest: list[dict[str, object]] = []
    for year in YEARS:
        for category in PLAYER_CATEGORIES:
            manifest.append(
                cache_endpoint(
                    output_dir=output_dir,
                    api_base=settings.cfbd_api_base,
                    api_key=settings.cfbd_api_key,
                    endpoint="/stats/player/season",
                    params={"year": str(year), "seasonType": "regular", "category": category},
                    path=endpoint_cache_path(output_dir, year, category),
                    force_refresh=force_refresh,
                    sleep_seconds=sleep_seconds,
                )
            )
        manifest.append(
            cache_endpoint(
                output_dir=output_dir,
                api_base=settings.cfbd_api_base,
                api_key=settings.cfbd_api_key,
                endpoint="/stats/season",
                params={"year": str(year), "seasonType": "regular"},
                path=team_cache_path(output_dir, year),
                force_refresh=force_refresh,
                sleep_seconds=sleep_seconds,
            )
        )
    return manifest


def build_player_seasons(output_dir: Path) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str, str, str], dict[str, object]] = {}
    for year in YEARS:
        for category in PLAYER_CATEGORIES:
            for row in read_csv(endpoint_cache_path(output_dir, year, category)):
                player_id = str(row.get("playerId") or row.get("player_id") or "").strip()
                player = str(row.get("player", "")).strip()
                team = str(row.get("team", "")).strip()
                conference = str(row.get("conference", "")).strip()
                position = str(row.get("position", "")).strip().upper()
                if not player or position not in POSITIONS:
                    continue
                key = (str(year), player_id, player, team, conference, position)
                record = grouped.setdefault(
                    key,
                    {
                        "season": str(year),
                        "cfbd_player_id": player_id,
                        "player_name": player,
                        "normalized_player_name": norm_name(player),
                        "team": team,
                        "conference": conference,
                        "position": position,
                    },
                )
                stat_type = norm_field(str(row.get("statType", "")))
                stat_value = safe_float(row.get("stat", ""))
                if not stat_type:
                    continue
                record[f"{category}_{stat_type}"] = record.get(f"{category}_{stat_type}", 0.0)
                record[f"{category}_{stat_type}"] = safe_float(record[f"{category}_{stat_type}"]) + stat_value
    rows = list(grouped.values())
    for row in rows:
        add_feature_aliases(row)
    rows.sort(key=lambda row: (safe_int(row["season"]), str(row["position"]), str(row["player_name"])))
    return rows


def add_feature_aliases(row: dict[str, object]) -> None:
    row["passing_yards"] = value_from(row, ["passing_yds", "passing_yards"])
    row["passing_tds"] = value_from(row, ["passing_td", "passing_tds"])
    row["passing_attempts"] = value_from(row, ["passing_att", "passing_attempts"])
    row["passing_completions"] = value_from(row, ["passing_completions", "passing_cmp"])
    row["passing_ints"] = value_from(row, ["passing_int", "passing_ints"])
    row["rushing_yards"] = value_from(row, ["rushing_yds", "rushing_yards"])
    row["rushing_tds"] = value_from(row, ["rushing_td", "rushing_tds"])
    row["rushing_attempts"] = value_from(row, ["rushing_car", "rushing_att", "rushing_attempts"])
    row["receiving_yards"] = value_from(row, ["receiving_yds", "receiving_yards"])
    row["receiving_tds"] = value_from(row, ["receiving_td", "receiving_tds"])
    row["receptions"] = value_from(row, ["receiving_rec", "receiving_receptions"])


def value_from(row: dict[str, object], columns: list[str]) -> str:
    for column in columns:
        value = safe_float(row.get(column, ""))
        if value:
            return f"{value:.3f}"
    return ""


def build_team_seasons(output_dir: Path) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for year in YEARS:
        for row in read_csv(team_cache_path(output_dir, year)):
            team = str(row.get("team", "")).strip()
            conference = str(row.get("conference", "")).strip()
            stat_name = norm_field(str(row.get("statName", "")))
            if not team or not stat_name:
                continue
            key = (str(year), team, conference)
            record = grouped.setdefault(
                key,
                {"season": str(year), "team": team, "conference": conference},
            )
            record[stat_name] = safe_float(record.get(stat_name, 0.0)) + safe_float(row.get("statValue", ""))
    rows = list(grouped.values())
    rows.sort(key=lambda row: (safe_int(row["season"]), str(row["team"])))
    return rows


def add_market_share_features(
    player_rows: list[dict[str, object]], team_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    team_lookup = {
        (str(row.get("season", "")), str(row.get("team", ""))): row for row in team_rows
    }
    enriched: list[dict[str, object]] = []
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
        out["production_allowed"] = "no"
        out["promotion_status"] = "local_feature_cache_only"
        enriched.append(out)
    return enriched


def lookup_team_value(row: dict[str, object], columns: list[str]) -> float:
    for column in columns:
        value = safe_float(row.get(column, ""))
        if value:
            return value
    return 0.0


def join_drafted_pool(
    labels_path: Path, feature_rows: list[dict[str, object]]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    labels = [
        row
        for row in read_csv(labels_path)
        if safe_int(row.get("draft_year")) in range(2010, 2024)
        and row.get("position", "").upper() in POSITIONS
    ]
    by_key: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for feature in feature_rows:
        by_key[
            (
                str(feature.get("season", "")),
                str(feature.get("normalized_player_name", "")),
                str(feature.get("position", "")).upper(),
            )
        ].append(feature)

    joined: list[dict[str, object]] = []
    for label in labels:
        draft_year = safe_int(label.get("draft_year"))
        expected_season = draft_year - 1
        base = {
            "historical_label_key": label.get("historical_label_key", ""),
            "draft_year": str(draft_year),
            "expected_cfbd_feature_season": str(expected_season),
            "player_name": label.get("player_name", ""),
            "normalized_player_name": label.get("normalized_player_name") or norm_name(label.get("player_name", "")),
            "position": label.get("position", ""),
            "college": label.get("college", ""),
            "draft_round": label.get("draft_round", ""),
            "overall_pick": label.get("overall_pick", ""),
            "label_status": label.get("historical_label_status", ""),
            "backtest_ready": label.get("backtest_ready", ""),
            "partial_window_only": label.get("partial_window_only", ""),
            "feature_source_safety": "cfbd_factual_regular_season_only",
            "promotion_status": "local_feature_cache_only",
            "production_allowed": "no",
        }
        if expected_season < min(YEARS) or expected_season > max(YEARS):
            base["cfbd_join_status"] = "blocked_expected_season_outside_cache"
            base["join_candidate_count"] = "0"
            joined.append(base)
            continue
        candidates = by_key.get(
            (str(expected_season), str(base["normalized_player_name"]), str(base["position"]).upper()),
            [],
        )
        if not candidates:
            base["cfbd_join_status"] = "unmatched_name_position_season"
            base["join_candidate_count"] = "0"
            joined.append(base)
            continue
        best = sorted(candidates, key=position_feature_score, reverse=True)[0]
        status = "matched_name_position_season"
        if len(candidates) > 1:
            status = "matched_with_duplicate_candidate_selection"
        merged = dict(base)
        for column in JOIN_FEATURE_COLUMNS:
            merged[column] = best.get(column, "")
        merged["cfbd_join_status"] = status
        merged["join_candidate_count"] = str(len(candidates))
        joined.append(merged)

    summary_counter = Counter(row["cfbd_join_status"] for row in joined)
    by_year_position = Counter(
        (row["draft_year"], row["position"], row["cfbd_join_status"]) for row in joined
    )
    summary = [
        {
            "bucket": "overall",
            "draft_year": "",
            "position": "",
            "cfbd_join_status": status,
            "row_count": count,
        }
        for status, count in sorted(summary_counter.items())
    ]
    for (year, position, status), count in sorted(by_year_position.items()):
        summary.append(
            {
                "bucket": "year_position",
                "draft_year": year,
                "position": position,
                "cfbd_join_status": status,
                "row_count": count,
            }
        )
    return joined, summary


def position_feature_score(row: dict[str, object]) -> float:
    position = str(row.get("position", "")).upper()
    if position == "QB":
        return safe_float(row.get("passing_yards")) + safe_float(row.get("rushing_yards"))
    if position == "RB":
        return safe_float(row.get("rushing_yards")) + safe_float(row.get("receiving_yards"))
    return safe_float(row.get("receiving_yards")) + safe_float(row.get("rushing_yards"))


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
JOIN_FEATURE_COLUMNS = BASE_PLAYER_COLUMNS
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
    "cfbd_join_status",
    "join_candidate_count",
    "feature_source_safety",
    "promotion_status",
    "production_allowed",
] + JOIN_FEATURE_COLUMNS


def build_exports(
    output_dir: Path,
    labels_path: Path,
    *,
    force_refresh: bool = False,
    sleep_seconds: float = 1.1,
    skip_fetch: bool = False,
) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    if not skip_fetch:
        manifest = fetch_cache(output_dir, force_refresh=force_refresh, sleep_seconds=sleep_seconds)
        write_csv(
            output_dir / "cfbd_historical_fetch_manifest_v1_20260615.csv",
            manifest,
            [
                "year",
                "endpoint",
                "category",
                "season_type",
                "status",
                "row_count",
                "field_count",
                "cache_path",
                "error_type",
            ],
        )
    elif (output_dir / "cfbd_historical_fetch_manifest_v1_20260615.csv").exists():
        manifest = read_csv(output_dir / "cfbd_historical_fetch_manifest_v1_20260615.csv")

    player_rows = add_market_share_features(
        build_player_seasons(output_dir),
        build_team_seasons(output_dir),
    )
    team_rows = build_team_seasons(output_dir)
    joined_rows, join_summary = join_drafted_pool(labels_path, player_rows)

    write_csv(output_dir / "cfbd_player_season_features_v1_20260615.csv", player_rows, BASE_PLAYER_COLUMNS)
    team_columns = sorted({key for row in team_rows for key in row.keys()})
    write_csv(output_dir / "cfbd_team_season_denominators_v1_20260615.csv", team_rows, team_columns)
    write_csv(output_dir / "cfbd_drafted_rookie_feature_join_v1_20260615.csv", joined_rows, JOIN_COLUMNS)
    write_csv(
        output_dir / "cfbd_drafted_rookie_join_coverage_v1_20260615.csv",
        join_summary,
        ["bucket", "draft_year", "position", "cfbd_join_status", "row_count"],
    )
    write_readme(output_dir, manifest, player_rows, team_rows, joined_rows)
    return {
        "manifest_rows": len(manifest),
        "player_feature_rows": len(player_rows),
        "team_feature_rows": len(team_rows),
        "drafted_join_rows": len(joined_rows),
        "matched_join_rows": sum(
            1 for row in joined_rows if str(row.get("cfbd_join_status", "")).startswith("matched")
        ),
        "unmatched_join_rows": sum(1 for row in joined_rows if row.get("cfbd_join_status") == "unmatched_name_position_season"),
        "outside_cache_rows": sum(1 for row in joined_rows if row.get("cfbd_join_status") == "blocked_expected_season_outside_cache"),
    }


def write_readme(
    output_dir: Path,
    manifest: list[dict[str, object]],
    player_rows: list[dict[str, object]],
    team_rows: list[dict[str, object]],
    joined_rows: list[dict[str, object]],
) -> None:
    statuses = Counter(str(row.get("status", "")) for row in manifest)
    joins = Counter(str(row.get("cfbd_join_status", "")) for row in joined_rows)
    text = [
        "# Rookie CFBD Historical Feature Cache v1",
        "",
        "Local-only CFBD cache and derived feature exports. These files are not",
        "production rankings, app-readable outputs, probabilities, bands, or promoted artifacts.",
        "",
        f"- endpoint manifest rows: {len(manifest)}",
        f"- fetch/cache statuses: {dict(sorted(statuses.items()))}",
        f"- player feature rows: {len(player_rows)}",
        f"- team denominator rows: {len(team_rows)}",
        f"- drafted join rows: {len(joined_rows)}",
        f"- join statuses: {dict(sorted(joins.items()))}",
        "",
        "API keys are not written. Raw payloads are cached as local CSV endpoint",
        "exports only under this local_exports directory.",
        "",
    ]
    (output_dir / "README_CFBD_HISTORICAL_FEATURE_CACHE_V1_20260615.md").write_text(
        "\n".join(text), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.1)
    args = parser.parse_args(argv)
    counts = build_exports(
        args.output_dir,
        args.labels,
        force_refresh=args.force_refresh,
        sleep_seconds=args.sleep_seconds,
        skip_fetch=args.skip_fetch,
    )
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
