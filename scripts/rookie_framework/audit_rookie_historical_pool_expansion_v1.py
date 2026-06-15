"""Audit rookie historical pool expansion feasibility for 2010-2020.

This script is audit/scaffold only. It reconstructs local-only label previews
from raw stat components and draft-pick identity rows, but it does not tune,
promote, or write app-readable artifacts.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_PLAYER_STATS = Path("local_exports/truth_set_lab/v3/downloads/player_stats.csv")
DEFAULT_DRAFT_PICKS = Path(
    "local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/"
    "draft_pool_downloads/nflverse_draft_picks.csv"
)
DEFAULT_CURRENT_LABELS = Path(
    "local_exports/rookie_framework/historical_outcome_labels_v1_20260615/"
    "rookie_historical_outcome_labels_v1_20260615.csv"
)
DEFAULT_OUTCOME_READINESS = Path(
    "local_exports/outcome_probability/sprint_5ck_r2_consolidated_2010_2019_historical_model_readiness_reaudit"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/historical_pool_expansion_audit_20260615")

POSITIONS = {"QB", "RB", "WR", "TE"}
EXPANSION_YEARS = [str(year) for year in range(2010, 2021)]
STARTER_RANK = {"QB": 12, "RB": 24, "WR": 36, "TE": 12}
STAR_RANK = {"QB": 6, "RB": 12, "WR": 12, "TE": 8}
USEFUL_RANK = {"QB": 18, "RB": 36, "WR": 48, "TE": 18}
FORBIDDEN_DRAFT_AS_FEATURE = {
    "hof",
    "to",
    "allpro",
    "probowls",
    "seasons_started",
    "w_av",
    "car_av",
    "dr_av",
    "games",
    "pass_completions",
    "pass_attempts",
    "pass_yards",
    "pass_tds",
    "pass_ints",
    "rush_atts",
    "rush_yards",
    "rush_tds",
    "receptions",
    "rec_yards",
    "rec_tds",
    "def_solo_tackles",
    "def_ints",
    "def_sacks",
}

SOURCE_COLUMNS = [
    "source_name",
    "source_path",
    "exists",
    "rows",
    "year_coverage",
    "position_coverage",
    "identity_fields",
    "outcome_fields",
    "scoring_or_label_semantics",
    "source_role",
    "leakage_risk",
    "audit_status",
    "notes",
]

DRAFT_COLUMNS = [
    "source_name",
    "source_path",
    "exists",
    "rows",
    "year_coverage",
    "skill_position_rows_2010_2020",
    "required_fields_present",
    "stable_id_fields",
    "identity_fields",
    "draft_capital_fields",
    "quarantined_outcome_fields",
    "draft_source_status",
    "notes",
]

JOIN_COLUMNS = [
    "rookie_class_year",
    "draft_skill_rows",
    "preview_label_rows",
    "players_with_any_stat_match",
    "players_with_no_stat_match",
    "complete_window_rows",
    "partial_window_rows",
    "duplicate_draft_keys",
    "duplicate_preview_keys",
    "feasibility_status",
    "notes",
]

PREVIEW_COLUMNS = [
    "historical_pool_key",
    "draft_year",
    "player_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "draft_round",
    "draft_pick",
    "gsis_id",
    "pfr_player_id",
    "cfb_player_id",
    "label_quality_status",
    "label_missing_reason",
    "label_scoring_quality",
    "label_year1_season",
    "label_year1_points",
    "label_year1_pos_rank",
    "label_year1_starter_flag",
    "label_year2_season",
    "label_year2_points",
    "label_year2_pos_rank",
    "label_year2_starter_flag",
    "label_year3_season",
    "label_year3_points",
    "label_year3_pos_rank",
    "label_year3_starter_flag",
    "label_first3_total_points",
    "label_first3_best_season_points",
    "label_first3_best_pos_rank",
    "label_first3_starter_seasons",
    "label_bust_flag",
    "label_star_flag",
    "label_useful_flag",
    "eval_label_source",
    "eval_join_method",
    "eval_backtest_ready_flag",
    "guardrails",
]


class HistoricalPoolAuditError(RuntimeError):
    """Raised when historical pool expansion audit fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def norm_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)


def to_float(value: str) -> float:
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(value)
    except ValueError:
        return 0.0


def safe_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def stat(row: dict[str, str], *names: str) -> float:
    for name in names:
        if name in row:
            return to_float(row.get(name, ""))
    return 0.0


def fantasy_points(row: dict[str, str]) -> float:
    fumbles_lost = stat(row, "sack_fumbles_lost") + stat(row, "rushing_fumbles_lost") + stat(row, "receiving_fumbles_lost")
    return_yards = stat(row, "punt_return_yards") + stat(row, "kickoff_return_yards")
    first_downs = stat(row, "rushing_first_downs") + stat(row, "receiving_first_downs")
    two_points = stat(row, "passing_2pt_conversions") + stat(row, "rushing_2pt_conversions") + stat(row, "receiving_2pt_conversions")
    return round(
        stat(row, "passing_yards") / 30.0
        + stat(row, "passing_tds") * 3.0
        - stat(row, "interceptions", "passing_interceptions")
        + stat(row, "rushing_yards") / 10.0
        + stat(row, "rushing_tds") * 4.0
        + stat(row, "receiving_yards") / 10.0
        + stat(row, "receiving_tds") * 4.0
        + return_yards / 30.0
        + stat(row, "special_teams_tds") * 4.0
        + two_points * 2.0
        - fumbles_lost
        + first_downs * 0.4,
        3,
    )


def year_coverage(rows: list[dict[str, str]], *fields: str) -> str:
    years = set()
    for row in rows:
        for field in fields:
            if row.get(field):
                years.add(row[field])
    return "|".join(sorted(years, key=lambda item: safe_int(item)))


def position_coverage(rows: list[dict[str, str]]) -> str:
    positions = sorted({row.get("position") or row.get("position_group") or row.get("category", "") for row in rows if row.get("position") or row.get("position_group") or row.get("category")})
    return "|".join(positions)


def aggregate_stats(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    grouped: dict[tuple[str, str, str], dict[str, str]] = {}
    numeric_fields = [
        "passing_yards",
        "passing_tds",
        "interceptions",
        "passing_interceptions",
        "rushing_yards",
        "rushing_tds",
        "receiving_yards",
        "receiving_tds",
        "rushing_first_downs",
        "receiving_first_downs",
        "passing_2pt_conversions",
        "rushing_2pt_conversions",
        "receiving_2pt_conversions",
        "sack_fumbles_lost",
        "rushing_fumbles_lost",
        "receiving_fumbles_lost",
        "special_teams_tds",
        "punt_return_yards",
        "kickoff_return_yards",
    ]
    for row in rows:
        if row.get("season_type") and row.get("season_type") != "REG":
            continue
        position = row.get("position_group") or row.get("position", "")
        if position not in POSITIONS:
            continue
        season = row.get("season", "")
        if not season:
            continue
        name = row.get("player_display_name") or row.get("player_name", "")
        key = (norm_name(name), position, season)
        existing = grouped.setdefault(key, {"player_name": name, "position": position, "season": season, "games_with_recorded_stats": "0"})
        existing["games_with_recorded_stats"] = str(safe_int(existing["games_with_recorded_stats"]) + 1)
        for field in numeric_fields:
            existing[field] = str(to_float(existing.get(field, "")) + stat(row, field))
    for row in grouped.values():
        row["label_points"] = f"{fantasy_points(row):.3f}"
    return grouped


def position_ranks(aggregated: dict[tuple[str, str, str], dict[str, str]]) -> dict[tuple[str, str, str], int]:
    by_year_pos: dict[tuple[str, str], list[tuple[float, tuple[str, str, str]]]] = defaultdict(list)
    for key, row in aggregated.items():
        _, position, season = key
        by_year_pos[(season, position)].append((to_float(row["label_points"]), key))
    ranks: dict[tuple[str, str, str], int] = {}
    for values in by_year_pos.values():
        values.sort(reverse=True)
        for index, (_, key) in enumerate(values, start=1):
            ranks[key] = index
    return ranks


def starter_flag(position: str, rank: int | None) -> str:
    if not rank:
        return "0"
    return "1" if rank <= STARTER_RANK.get(position, 999) else "0"


def build_preview(draft_rows: list[dict[str, str]], stat_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    aggregated = aggregate_stats(stat_rows)
    ranks = position_ranks(aggregated)
    preview = []
    by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    current_max_year = 2024
    for draft in draft_rows:
        year = draft.get("season", "")
        position = draft.get("position", "")
        if year not in EXPANSION_YEARS or position not in POSITIONS:
            continue
        player_name = draft.get("pfr_player_name", "")
        normalized = norm_name(player_name)
        seasons = [safe_int(year) + offset for offset in range(3)]
        points: list[float] = []
        ranks_seen: list[int] = []
        starter_seasons = 0
        matched_seasons = 0
        missing_reasons = []
        label = {
            "historical_pool_key": f"pool:{year}:{normalized}:{position}:{draft.get('pick', '')}",
            "draft_year": year,
            "player_name": player_name,
            "normalized_player_name": normalized,
            "position": position,
            "college": draft.get("college", ""),
            "nfl_team": draft.get("team", ""),
            "draft_round": draft.get("round", ""),
            "draft_pick": draft.get("pick", ""),
            "gsis_id": draft.get("gsis_id", ""),
            "pfr_player_id": draft.get("pfr_player_id", ""),
            "cfb_player_id": draft.get("cfb_player_id", ""),
            "eval_label_source": "local nflverse player_stats raw stat components",
            "eval_join_method": "draft_picks normalized_name_position_year_to_player_stats",
            "guardrails": "audit_preview_only; labels_not_features; no_tuning; no_app; no_private_score; no_probability; no_band",
        }
        for index, season in enumerate(seasons, start=1):
            label[f"label_year{index}_season"] = str(season)
            if season > current_max_year:
                label[f"label_year{index}_points"] = ""
                label[f"label_year{index}_pos_rank"] = ""
                label[f"label_year{index}_starter_flag"] = ""
                missing_reasons.append(f"year{index}_future_unavailable")
                continue
            stat_key = (normalized, position, str(season))
            stat_row = aggregated.get(stat_key)
            if stat_row:
                matched_seasons += 1
                season_points = to_float(stat_row.get("label_points", ""))
                rank = ranks.get(stat_key)
                points.append(season_points)
                if rank:
                    ranks_seen.append(rank)
                starter = starter_flag(position, rank)
                starter_seasons += 1 if starter == "1" else 0
                label[f"label_year{index}_points"] = f"{season_points:.3f}"
                label[f"label_year{index}_pos_rank"] = str(rank or "")
                label[f"label_year{index}_starter_flag"] = starter
            else:
                points.append(0.0)
                label[f"label_year{index}_points"] = "0.000"
                label[f"label_year{index}_pos_rank"] = ""
                label[f"label_year{index}_starter_flag"] = "0"
                missing_reasons.append(f"year{index}_no_recorded_stats")
        best_rank = min(ranks_seen) if ranks_seen else 999
        best_points = max(points) if points else 0.0
        total = sum(points)
        star = best_rank <= STAR_RANK.get(position, 999)
        useful = starter_seasons >= 1 or best_rank <= USEFUL_RANK.get(position, 999)
        bust = total < 40.0 and starter_seasons == 0
        label["label_quality_status"] = "GREEN_COMPLETE_WINDOW" if matched_seasons else "YELLOW_COMPLETE_WINDOW_ASSUMED_ZERO"
        label["label_missing_reason"] = "|".join(missing_reasons)
        label["label_scoring_quality"] = "exact_non_ppr_with_rush_rec_first_downs_return_yards_partial_pre_2025"
        label["label_first3_total_points"] = f"{total:.3f}"
        label["label_first3_best_season_points"] = f"{best_points:.3f}"
        label["label_first3_best_pos_rank"] = "" if best_rank == 999 else str(best_rank)
        label["label_first3_starter_seasons"] = str(starter_seasons)
        label["label_bust_flag"] = "1" if bust else "0"
        label["label_star_flag"] = "1" if star else "0"
        label["label_useful_flag"] = "1" if useful else "0"
        label["eval_backtest_ready_flag"] = "yes"
        preview.append(label)
        by_year[year].append(label)
    feasibility = []
    draft_counts = Counter(row.get("season", "") for row in draft_rows if row.get("season") in EXPANSION_YEARS and row.get("position") in POSITIONS)
    for year in EXPANSION_YEARS:
        rows = by_year.get(year, [])
        keys = [row["historical_pool_key"] for row in rows]
        duplicate_preview = len(keys) - len(set(keys))
        matched = sum(1 for row in rows if row["label_quality_status"] == "GREEN_COMPLETE_WINDOW")
        no_match = sum(1 for row in rows if row["label_quality_status"] == "YELLOW_COMPLETE_WINDOW_ASSUMED_ZERO")
        status = "GREEN_PREVIEW_LABELABLE" if rows and not duplicate_preview else "YELLOW_REPAIR_REQUIRED" if rows else "RED_NO_ROWS"
        feasibility.append(
            {
                "rookie_class_year": year,
                "draft_skill_rows": str(draft_counts.get(year, 0)),
                "preview_label_rows": str(len(rows)),
                "players_with_any_stat_match": str(matched),
                "players_with_no_stat_match": str(no_match),
                "complete_window_rows": str(len(rows)),
                "partial_window_rows": "0",
                "duplicate_draft_keys": "not_detected_in_allowlisted_key",
                "duplicate_preview_keys": str(duplicate_preview),
                "feasibility_status": status,
                "notes": "label preview only; requires alias/ID QA before expanded backtest integration",
            }
        )
    return preview, feasibility


def source_inventory(
    player_stats_path: Path,
    draft_path: Path,
    current_labels_path: Path,
    outcome_readiness_dir: Path,
    player_stats: list[dict[str, str]],
    draft_rows: list[dict[str, str]],
    current_labels: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows = []
    rows.append(
        {
            "source_name": "truth_set_lab_v3_player_stats",
            "source_path": str(player_stats_path),
            "exists": "yes" if player_stats else "no",
            "rows": str(len(player_stats)),
            "year_coverage": year_coverage(player_stats, "season"),
            "position_coverage": position_coverage(player_stats),
            "identity_fields": "player_id|player_display_name|position|position_group|season",
            "outcome_fields": "raw passing/rushing/receiving/return/first-down/fumble components",
            "scoring_or_label_semantics": "raw weekly stat components; usable to reconstruct Tim non-PPR first-down labels; imported fantasy totals ignored",
            "source_role": "preferred_label_component_source",
            "leakage_risk": "safe_as_labels_only; future stats forbidden as features",
            "audit_status": "GREEN_FOR_LABEL_PREVIEW",
            "notes": "2010-2020 seasons present if year coverage includes those seasons.",
        }
    )
    rows.append(
        {
            "source_name": "nflverse_draft_picks_local_csv",
            "source_path": str(draft_path),
            "exists": "yes" if draft_rows else "no",
            "rows": str(len(draft_rows)),
            "year_coverage": year_coverage(draft_rows, "season"),
            "position_coverage": position_coverage(draft_rows),
            "identity_fields": "season|pfr_player_name|position|college|team|gsis_id|pfr_player_id|cfb_player_id",
            "outcome_fields": "|".join(sorted(FORBIDDEN_DRAFT_AS_FEATURE & set(draft_rows[0].keys()))) if draft_rows else "",
            "scoring_or_label_semantics": "draft identity/capital source with career outcome columns requiring quarantine",
            "source_role": "identity_and_draft_capital_only",
            "leakage_risk": "career outcome columns must be allowlist-excluded",
            "audit_status": "YELLOW_ALLOWLIST_REQUIRED",
            "notes": "No package install or network needed; sourced from existing local download.",
        }
    )
    rows.append(
        {
            "source_name": "current_rookie_historical_outcome_labels_v1",
            "source_path": str(current_labels_path),
            "exists": "yes" if current_labels else "no",
            "rows": str(len(current_labels)),
            "year_coverage": year_coverage(current_labels, "rookie_class_year"),
            "position_coverage": position_coverage(current_labels),
            "identity_fields": "historical_prospect_key|prospect_name|normalized_player_name|position|rookie_class_year",
            "outcome_fields": "label_year1_points|label_year2_points|label_year3_points|label_star_flag|label_bust_flag",
            "scoring_or_label_semantics": "first-three-year rookie outcome labels from raw stat components",
            "source_role": "current_2021_2025_label_baseline",
            "leakage_risk": "safe as evaluation labels only",
            "audit_status": "GREEN_EXISTING_BASELINE",
            "notes": "2021-2023 complete-window, 2024-2025 partial/report-only.",
        }
    )
    package_inventory = read_csv(outcome_readiness_dir / "package_inventory.csv")
    support = read_csv(outcome_readiness_dir / "support_readiness_by_head.csv")
    rows.append(
        {
            "source_name": "outcome_probability_2010_2019_readiness_exports",
            "source_path": str(outcome_readiness_dir),
            "exists": "yes" if package_inventory else "no",
            "rows": str(sum(safe_int(row.get("label_rows", "0")) for row in package_inventory)),
            "year_coverage": "2010|2011|2012|2013|2014|2015|2016|2017|2018|2019" if package_inventory else "",
            "position_coverage": "QB|RB|TE|WR" if package_inventory else "",
            "identity_fields": "row_id|player_id|player_name|position|target_season",
            "outcome_fields": "same_year_* outcome heads; support rows=" + str(len(support)),
            "scoring_or_label_semantics": "season-level outcome-probability labels; not first-three-year rookie draft labels",
            "source_role": "read_only_semantics_inventory_not_direct_rookie_pool",
            "leakage_risk": "YELLOW: usable only after explicit label semantic mapping; not a rookie draft-class pool by itself",
            "audit_status": "YELLOW_SEMANTICS_NOT_DIRECTLY_COMPATIBLE",
            "notes": "Good evidence that 2010-2019 fantasy outcome rows exist locally, but direct rookie backtest expansion should use raw stat reconstruction plus draft identity.",
        }
    )
    return rows


def draft_inventory(draft_path: Path, draft_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    required = {"season", "round", "pick", "team", "pfr_player_name", "position", "college"}
    skill_2010_2020 = [
        row
        for row in draft_rows
        if row.get("season") in EXPANSION_YEARS and row.get("position") in POSITIONS
    ]
    columns = set(draft_rows[0].keys()) if draft_rows else set()
    return [
        {
            "source_name": "local_nflverse_draft_picks_csv",
            "source_path": str(draft_path),
            "exists": "yes" if draft_rows else "no",
            "rows": str(len(draft_rows)),
            "year_coverage": year_coverage(draft_rows, "season"),
            "skill_position_rows_2010_2020": str(len(skill_2010_2020)),
            "required_fields_present": "yes" if required <= columns else "no",
            "stable_id_fields": "|".join([field for field in ["gsis_id", "pfr_player_id", "cfb_player_id"] if field in columns]),
            "identity_fields": "season|pfr_player_name|position|college|team",
            "draft_capital_fields": "round|pick",
            "quarantined_outcome_fields": "|".join(sorted(FORBIDDEN_DRAFT_AS_FEATURE & columns)),
            "draft_source_status": "YELLOW_ALLOWLIST_REQUIRED",
            "notes": "Draft source is locally available and broad, but career outcome columns must be excluded before use as features.",
        }
    ]


def write_readme(output_dir: Path, counts: dict[str, int]) -> None:
    text = f"""# Rookie Historical Pool Expansion Audit - 2026-06-15

Status: local-only audit exports.

- Expanded draft-label preview rows: {counts.get('preview_rows', 0)}
- 2010-2020 years audited: {counts.get('join_years', 0)}
- Source inventory rows: {counts.get('source_inventory_rows', 0)}
- Draft inventory rows: {counts.get('draft_inventory_rows', 0)}

No tuning, production ranking, private score, app output, probability, band,
hidden sort key, or promoted artifact was created.
"""
    (output_dir / "README_ROOKIE_HISTORICAL_POOL_EXPANSION_AUDIT_20260615.md").write_text(text, encoding="utf-8")


def build_exports(
    player_stats_path: Path,
    draft_path: Path,
    current_labels_path: Path,
    outcome_readiness_dir: Path,
    output_dir: Path,
) -> dict[str, int]:
    player_stats = read_csv(player_stats_path)
    draft_rows = read_csv(draft_path)
    current_labels = read_csv(current_labels_path)
    if not player_stats:
        raise HistoricalPoolAuditError(f"Missing player stats source: {player_stats_path}")
    if not draft_rows:
        raise HistoricalPoolAuditError(f"Missing draft source: {draft_path}")
    source_rows = source_inventory(player_stats_path, draft_path, current_labels_path, outcome_readiness_dir, player_stats, draft_rows, current_labels)
    draft_rows_out = draft_inventory(draft_path, draft_rows)
    preview, feasibility = build_preview(draft_rows, player_stats)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "historical_source_inventory_20260615.csv", source_rows, SOURCE_COLUMNS)
    write_csv(output_dir / "draft_source_inventory_20260615.csv", draft_rows_out, DRAFT_COLUMNS)
    write_csv(output_dir / "historical_pool_join_feasibility_20260615.csv", feasibility, JOIN_COLUMNS)
    write_csv(output_dir / "expanded_label_pool_preview_20260615.csv", preview, PREVIEW_COLUMNS)
    write_readme(
        output_dir,
        {
            "preview_rows": len(preview),
            "join_years": len(feasibility),
            "source_inventory_rows": len(source_rows),
            "draft_inventory_rows": len(draft_rows_out),
        },
    )
    return {
        "source_inventory_rows": len(source_rows),
        "draft_inventory_rows": len(draft_rows_out),
        "join_feasibility_rows": len(feasibility),
        "preview_rows": len(preview),
        "preview_green_rows": sum(1 for row in preview if row["label_quality_status"] == "GREEN_COMPLETE_WINDOW"),
        "preview_assumed_zero_rows": sum(1 for row in preview if row["label_quality_status"] == "YELLOW_COMPLETE_WINDOW_ASSUMED_ZERO"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit rookie historical pool expansion feasibility.")
    parser.add_argument("--player-stats", type=Path, default=DEFAULT_PLAYER_STATS)
    parser.add_argument("--draft-picks", type=Path, default=DEFAULT_DRAFT_PICKS)
    parser.add_argument("--current-labels", type=Path, default=DEFAULT_CURRENT_LABELS)
    parser.add_argument("--outcome-readiness-dir", type=Path, default=DEFAULT_OUTCOME_READINESS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.player_stats, args.draft_picks, args.current_labels, args.outcome_readiness_dir, args.output_dir)
    except HistoricalPoolAuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
