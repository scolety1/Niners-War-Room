"""Audit CFBD/API feasibility for rookie historical feature coverage.

This is an audit/inventory script only. It does not tune, create a v2 board,
write production artifacts, or print API secrets.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.config.api_settings import get_api_settings  # noqa: E402


DEFAULT_OUTPUT_DIR = Path(
    "local_exports/rookie_framework/cfb_api_historical_feature_coverage_audit_20260615"
)
CFBD_PROCESSED_ROOT = Path(
    "local_exports/model_v4/prospect_sources/latest/files/source_project/data/"
    "college_football_data/processed"
)
CFBD_RAW_ROOT = Path(
    "local_exports/model_v4/prospect_sources/latest/files/source_project/data/"
    "college_football_data/raw"
)
UNTRACKED_CFBD_RAW_ROOT = Path("data/college_football_data/raw")
SAMPLE_YEARS = [2010, 2015, 2020, 2021, 2022, 2023, 2026]
POSITIONS = ["QB", "RB", "WR", "TE"]
STAT_CATEGORIES = ["passing", "rushing", "receiving"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def safe_int(value: str | int | None) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def bool_text(value: bool) -> str:
    return "yes" if value else "no"


def year_range(values: list[int]) -> str:
    if not values:
        return ""
    return f"{min(values)}-{max(values)}"


def inspect_api_config() -> list[dict[str, str]]:
    settings = get_api_settings()
    dotenv_exists = (REPO_ROOT / ".env").exists()
    return [
        {
            "item": "CFBD_API_KEY",
            "status": "configured" if bool(settings.cfbd_api_key) else "missing",
            "safe_detail": "value suppressed" if bool(settings.cfbd_api_key) else "no key in environment",
        },
        {
            "item": "CFBD_API_BASE",
            "status": "configured" if bool(settings.cfbd_api_base) else "missing",
            "safe_detail": settings.cfbd_api_base if settings.cfbd_api_base else "",
        },
        {
            "item": "MODEL_V4_LIVE_API_ENABLED",
            "status": "enabled" if settings.live_api_enabled else "disabled",
            "safe_detail": bool_text(settings.live_api_enabled),
        },
        {
            "item": "MODEL_V4_API_CACHE_ROOT",
            "status": "configured",
            "safe_detail": str(settings.api_cache_root.relative_to(REPO_ROOT))
            if settings.api_cache_root.is_relative_to(REPO_ROOT)
            else str(settings.api_cache_root),
        },
        {
            "item": ".env",
            "status": "present" if dotenv_exists else "absent",
            "safe_detail": "contents not read or printed" if dotenv_exists else "only .env.example present",
        },
    ]


def inspect_local_cache_files() -> list[dict[str, str]]:
    roots = [
        ("tracked_local_export_snapshot", REPO_ROOT / CFBD_RAW_ROOT),
        ("tracked_local_export_processed", REPO_ROOT / CFBD_PROCESSED_ROOT),
        ("untracked_data_cache", REPO_ROOT / UNTRACKED_CFBD_RAW_ROOT),
    ]
    rows: list[dict[str, str]] = []
    for cache_scope, root in roots:
        if not root.exists():
            rows.append(
                {
                    "cache_scope": cache_scope,
                    "path": str(root.relative_to(REPO_ROOT)),
                    "exists": "no",
                    "file_count": "0",
                    "year_coverage": "",
                    "notes": "not found",
                }
            )
            continue
        files = [path for path in root.rglob("*") if path.is_file()]
        years = years_for_cache_scope(cache_scope, root, files)
        rows.append(
            {
                "cache_scope": cache_scope,
                "path": str(root.relative_to(REPO_ROOT)),
                "exists": "yes",
                "file_count": str(len(files)),
                "year_coverage": year_range(sorted(years)),
                "notes": "read-only inventory; no data files modified",
            }
        )
    return rows


def years_for_cache_scope(cache_scope: str, root: Path, files: list[Path]) -> set[int]:
    years: set[int] = set()
    if cache_scope == "tracked_local_export_snapshot":
        for manifest in root.glob("cfbd_manifest_*.csv"):
            for row in read_csv(manifest):
                try:
                    params = json.loads(row.get("params_json", "{}"))
                except json.JSONDecodeError:
                    params = {}
                year = safe_int(params.get("year"))
                if year:
                    years.add(year)
        return years
    if cache_scope == "tracked_local_export_processed":
        for csv_file in files:
            if csv_file.suffix.lower() != ".csv":
                continue
            try:
                rows = read_csv(csv_file)
            except UnicodeDecodeError:
                continue
            for row in rows:
                for column in ["season", "year", "draft_year"]:
                    year = safe_int(row.get(column, ""))
                    if 1900 <= year <= 2100:
                        years.add(year)
        return years
    for path in files:
        for year in SAMPLE_YEARS + list(range(2010, 2027)):
            if str(year) in path.name:
                years.add(year)
    return years


def manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for manifest in sorted((REPO_ROOT / CFBD_RAW_ROOT).glob("cfbd_manifest_*.csv")):
        for row in read_csv(manifest):
            params = {}
            try:
                params = json.loads(row.get("params_json", "{}"))
            except json.JSONDecodeError:
                params = {}
            rows.append(
                {
                    "manifest": str(manifest.relative_to(REPO_ROOT)),
                    "table": row.get("table", ""),
                    "endpoint": row.get("endpoint", ""),
                    "year": str(params.get("year", "")),
                    "season_type": str(params.get("seasonType", "")),
                    "category": str(params.get("category", "")),
                    "csv_rows": row.get("csv_rows", ""),
                    "json_rows": row.get("json_rows", ""),
                }
            )
    return rows


def processed_coverage() -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for name in [
        "college_player_seasons_wide.csv",
        "college_market_share.csv",
        "college_team_seasons_wide.csv",
        "college_player_category_summary.csv",
        "draft_picks.csv",
        "roster.csv",
    ]:
        path = REPO_ROOT / CFBD_PROCESSED_ROOT / name
        result[name] = read_csv(path) if path.exists() else []
    return result


def build_sample_results(*, live_sample: bool) -> list[dict[str, str]]:
    settings = get_api_settings()
    rows: list[dict[str, str]] = []
    manifest = manifest_rows()
    by_year_category: dict[tuple[str, str], int] = defaultdict(int)
    team_rows_by_year: dict[str, int] = defaultdict(int)
    for row in manifest:
        if row["table"] == "player_stats_season" and row["season_type"] == "regular":
            by_year_category[(row["year"], row["category"])] += safe_int(row["csv_rows"])
        if row["table"] == "team_stats_season" and row["season_type"] == "regular":
            team_rows_by_year[row["year"]] += safe_int(row["csv_rows"])

    api_can_run = bool(settings.cfbd_api_key and settings.live_api_enabled and live_sample)
    for year in SAMPLE_YEARS:
        for category in STAT_CATEGORIES:
            cached_rows = by_year_category[(str(year), category)]
            if cached_rows:
                status = "cached_sample_available"
                note = "local CFBD raw manifest has regular-season rows"
            elif api_can_run:
                fetched_rows, note = fetch_cfbd_sample(
                    settings.cfbd_api_base,
                    settings.cfbd_api_key,
                    "/stats/player/season",
                    {"year": str(year), "seasonType": "regular", "category": category},
                )
                status = "live_sample_succeeded" if fetched_rows >= 0 else "live_sample_failed"
                cached_rows = max(fetched_rows, 0)
            else:
                status = "not_sampled_live_api_disabled_or_missing_key"
                note = "no local cache for sample year/category and live API gate was not open"
            rows.append(
                {
                    "year": str(year),
                    "sample_type": "player_stats_season",
                    "category": category,
                    "endpoint": "/stats/player/season",
                    "local_cached_rows": str(cached_rows),
                    "sample_status": status,
                    "notes": note,
                }
            )
        cached_team_rows = team_rows_by_year[str(year)]
        if cached_team_rows:
            status = "cached_sample_available"
            note = "local CFBD raw manifest has regular-season team stat rows"
        elif api_can_run:
            fetched_rows, note = fetch_cfbd_sample(
                settings.cfbd_api_base,
                settings.cfbd_api_key,
                "/stats/season",
                {"year": str(year), "seasonType": "regular"},
            )
            status = "live_sample_succeeded" if fetched_rows >= 0 else "live_sample_failed"
            cached_team_rows = max(fetched_rows, 0)
        else:
            status = "not_sampled_live_api_disabled_or_missing_key"
            note = "no local cache for sample year/team denominator and live API gate was not open"
        rows.append(
            {
                "year": str(year),
                "sample_type": "team_stats_season",
                "category": "team_denominators",
                "endpoint": "/stats/season",
                "local_cached_rows": str(cached_team_rows),
                "sample_status": status,
                "notes": note,
            }
        )
    return rows


def fetch_cfbd_sample(
    base: str, api_key: str, endpoint: str, params: dict[str, str]
) -> tuple[int, str]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{base.rstrip('/')}{endpoint}?{query}",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return -1, f"live API sample failed without exposing credentials: {type(exc).__name__}"
    if isinstance(payload, list):
        return len(payload), "live API sample returned a list payload"
    return 0, "live API sample returned a non-list payload"


def build_feature_coverage_matrix(processed: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    player_rows = processed["college_player_seasons_wide.csv"]
    share_rows = processed["college_market_share.csv"]
    team_rows = processed["college_team_seasons_wide.csv"]
    years = SAMPLE_YEARS
    categories_by_year: dict[str, set[str]] = defaultdict(set)
    player_count_by_year_category: dict[tuple[str, str], int] = defaultdict(int)
    for row in player_rows:
        if row.get("season_type") != "regular":
            continue
        year = row.get("season", "")
        category = row.get("category", "")
        categories_by_year[year].add(category)
        player_count_by_year_category[(year, category)] += 1

    share_by_year: dict[str, int] = defaultdict(int)
    for row in share_rows:
        if row.get("season_type") == "regular":
            share_by_year[row.get("season", "")] += 1

    team_by_year: dict[str, int] = defaultdict(int)
    for row in team_rows:
        if row.get("season_type") == "regular":
            team_by_year[row.get("season", "")] += 1

    rows: list[dict[str, str]] = []
    for year in years:
        year_text = str(year)
        for position in POSITIONS:
            if position == "QB":
                player_categories = ["passing", "rushing"]
                position_note = "QB passing plus rushing is available when player rows exist"
            elif position == "RB":
                player_categories = ["rushing", "receiving"]
                position_note = "RB rushing plus receiving is available when player rows exist"
            else:
                player_categories = ["receiving", "rushing"]
                position_note = f"{position} receiving plus occasional rushing is available when player rows exist"
            category_statuses = []
            for category in player_categories:
                count = player_count_by_year_category[(year_text, category)]
                category_statuses.append(f"{category}:{'yes' if count else 'no'}:{count}")
            any_category = any(player_count_by_year_category[(year_text, c)] for c in player_categories)
            team_available = team_by_year[year_text] > 0
            share_available = share_by_year[year_text] > 0
            rows.append(
                {
                    "year": year_text,
                    "position": position,
                    "player_stat_categories": "|".join(category_statuses),
                    "team_denominators_available": bool_text(team_available),
                    "market_share_processed_available": bool_text(share_available),
                    "coverage_status": coverage_status(any_category, team_available, share_available, year),
                    "feature_families_available": feature_families(any_category, team_available, share_available),
                    "missing_fields": missing_fields(any_category, team_available, share_available, year),
                    "notes": position_note,
                }
            )
    return rows


def coverage_status(
    any_category: bool, team_available: bool, share_available: bool, year: int
) -> str:
    if any_category and team_available and share_available:
        return "green_local_cache_available"
    if year == 2026 and not any_category:
        return "yellow_future_or_current_year_no_completed_stats"
    if any_category or team_available or share_available:
        return "yellow_partial_local_cache_available"
    return "red_not_available_locally"


def feature_families(any_category: bool, team_available: bool, share_available: bool) -> str:
    families = []
    if any_category:
        families.append("college_production_box_score")
    if team_available:
        families.append("team_denominators")
    if share_available:
        families.append("market_share_dominator")
    return "|".join(families)


def missing_fields(
    any_category: bool, team_available: bool, share_available: bool, year: int
) -> str:
    missing = []
    if not any_category:
        missing.append("player_season_stats")
    if not team_available:
        missing.append("team_stat_denominators")
    if not share_available:
        missing.append("processed_market_share")
    if year < 2021:
        missing.append("local_cfbd_cache_for_pre_2021")
    if year == 2026:
        missing.append("completed_2026_college_season")
    return "|".join(missing)


def build_feature_family_summary(processed: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    return [
        {
            "feature_family": "college_production_box_score",
            "available_years_local": processed_years(processed["college_player_seasons_wide.csv"], "season"),
            "private_score_allowed": "yes_if_time_safe_and_identity_matched",
            "api_or_cache_source": "CFBD /stats/player/season",
            "leakage_risk": "low",
            "notes": "passing/rushing/receiving categories are factual college production",
        },
        {
            "feature_family": "team_denominators",
            "available_years_local": processed_years(processed["college_team_seasons_wide.csv"], "season"),
            "private_score_allowed": "yes_if_time_safe_and_identity_matched",
            "api_or_cache_source": "CFBD /stats/season",
            "leakage_risk": "low",
            "notes": "team attempts/yards/plays style denominators support market share",
        },
        {
            "feature_family": "market_share_dominator",
            "available_years_local": processed_years(processed["college_market_share.csv"], "season"),
            "private_score_allowed": "yes_if_derived_from_same_season_raw_stats",
            "api_or_cache_source": "local processed CFBD college_market_share",
            "leakage_risk": "medium",
            "notes": "safe only when derived from same-season player/team stats, not future outcomes",
        },
        {
            "feature_family": "usage_advanced_route_charting",
            "available_years_local": "",
            "private_score_allowed": "no_local_cfbd_evidence_found",
            "api_or_cache_source": "not found in audited CFBD cache",
            "leakage_risk": "medium",
            "notes": "YPRR, route participation, missed tackles, YAC, pass-pro, contested catch still need licensed/manual files",
        },
        {
            "feature_family": "injury_history",
            "available_years_local": "",
            "private_score_allowed": "not_from_cfbd_cache",
            "api_or_cache_source": "not found in audited CFBD cache",
            "leakage_risk": "medium",
            "notes": "still requires Tim-provided/source-safe injury history",
        },
        {
            "feature_family": "draft_or_recruit_rank_fields",
            "available_years_local": processed_years(processed["draft_picks.csv"], "year"),
            "private_score_allowed": "partial",
            "api_or_cache_source": "CFBD /draft/picks and /recruiting/players",
            "leakage_risk": "high",
            "notes": "completed draft round/pick can be factual; preDraftRanking, grades, ratings, stars, and recruiting rankings stay quarantined unless separately approved",
        },
    ]


def processed_years(rows: list[dict[str, str]], column: str) -> str:
    years = sorted({safe_int(row.get(column, "")) for row in rows if safe_int(row.get(column, ""))})
    return year_range(years)


def build_missing_requests() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "needed_item": "CFBD_API_KEY plus explicit live cached sample approval",
            "why": "required to verify whether 2010-2020 player/team stats can be fetched now",
            "manual_backfill_avoidable_if_provided": "yes",
        },
        {
            "priority": "1",
            "needed_item": "approved cached CFBD export for 2010-2020 player stats and team stats",
            "why": "local CFBD cache currently verifies 2021-2023 only for completed historical years",
            "manual_backfill_avoidable_if_provided": "yes",
        },
        {
            "priority": "2",
            "needed_item": "historical college injury file",
            "why": "CFBD cache does not provide pre-draft injury history",
            "manual_backfill_avoidable_if_provided": "no",
        },
        {
            "priority": "2",
            "needed_item": "licensed route/advanced charting file",
            "why": "CFBD player/team box-score stats do not supply YPRR, pass pro, YAC, missed tackles, contested catch, or route participation",
            "manual_backfill_avoidable_if_provided": "no",
        },
        {
            "priority": "3",
            "needed_item": "historical ADP/market overlay",
            "why": "display-only value context can help manual draft use but must remain excluded from private tuning",
            "manual_backfill_avoidable_if_provided": "not_applicable_display_only",
        },
    ]


def write_readme(output_dir: Path, counts: dict[str, int]) -> None:
    text = "\n".join(
        [
            "# Rookie CFB API Historical Feature Coverage Audit",
            "",
            "Local-only exports for the CFBD/API coverage audit. These files are not",
            "production artifacts and are not app-readable ranking outputs.",
            "",
            f"- config rows: {counts['config_rows']}",
            f"- cache inventory rows: {counts['cache_inventory_rows']}",
            f"- sample result rows: {counts['sample_result_rows']}",
            f"- coverage matrix rows: {counts['coverage_matrix_rows']}",
            f"- feature family rows: {counts['feature_family_rows']}",
            f"- missing request rows: {counts['missing_request_rows']}",
            "",
            "No API keys are written here. Live API calls are skipped unless the",
            "repo's live API gate and credential are both explicitly configured.",
            "",
        ]
    )
    (output_dir / "README_CFB_API_HISTORICAL_FEATURE_COVERAGE_AUDIT_20260615.md").write_text(
        text, encoding="utf-8"
    )


def build_exports(output_dir: Path, *, live_sample: bool = False) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    processed = processed_coverage()
    config_rows = inspect_api_config()
    cache_rows = inspect_local_cache_files()
    sample_rows = build_sample_results(live_sample=live_sample)
    coverage_rows = build_feature_coverage_matrix(processed)
    family_rows = build_feature_family_summary(processed)
    missing_rows = build_missing_requests()

    write_csv(
        output_dir / "cfb_api_config_inventory_20260615.csv",
        config_rows,
        ["item", "status", "safe_detail"],
    )
    write_csv(
        output_dir / "cfb_api_cached_data_inventory_20260615.csv",
        cache_rows,
        ["cache_scope", "path", "exists", "file_count", "year_coverage", "notes"],
    )
    write_csv(
        output_dir / "cfb_api_sample_plan_and_results_20260615.csv",
        sample_rows,
        ["year", "sample_type", "category", "endpoint", "local_cached_rows", "sample_status", "notes"],
    )
    write_csv(
        output_dir / "cfb_api_feature_coverage_matrix_20260615.csv",
        coverage_rows,
        [
            "year",
            "position",
            "player_stat_categories",
            "team_denominators_available",
            "market_share_processed_available",
            "coverage_status",
            "feature_families_available",
            "missing_fields",
            "notes",
        ],
    )
    write_csv(
        output_dir / "cfb_api_feature_family_summary_20260615.csv",
        family_rows,
        [
            "feature_family",
            "available_years_local",
            "private_score_allowed",
            "api_or_cache_source",
            "leakage_risk",
            "notes",
        ],
    )
    write_csv(
        output_dir / "cfb_api_missing_fields_and_tim_requests_20260615.csv",
        missing_rows,
        ["priority", "needed_item", "why", "manual_backfill_avoidable_if_provided"],
    )
    counts = {
        "config_rows": len(config_rows),
        "cache_inventory_rows": len(cache_rows),
        "sample_result_rows": len(sample_rows),
        "coverage_matrix_rows": len(coverage_rows),
        "feature_family_rows": len(family_rows),
        "missing_request_rows": len(missing_rows),
    }
    write_readme(output_dir, counts)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--live-sample",
        action="store_true",
        help="Allow small live CFBD samples only when key and live API gate are configured.",
    )
    args = parser.parse_args(argv)
    counts = build_exports(args.output_dir, live_sample=args.live_sample)
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
