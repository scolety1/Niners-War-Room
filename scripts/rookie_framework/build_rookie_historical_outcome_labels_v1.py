"""Build rookie historical outcome label package v1.

Labels are evaluation targets only. They intentionally use post-rookie NFL
results, but they must never be merged into rookie-time features or production
ranking/private-score pipelines.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_HISTORICAL_FEATURES = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/"
    "historical_rookie_backtest_feature_matrix.csv"
)
DEFAULT_WEEKLY_STATS = Path("local_exports/truth_set_lab/v3/downloads/player_stats.csv")
DEFAULT_WEEKLY_STATS_2025 = Path("local_exports/truth_set_lab/v3/downloads/player_stats_2025.csv")
DEFAULT_RANKING = Path("local_exports/rookie_framework/draft_ranking_model_v1_20260615/rookie_draft_ranking_v1_20260615.csv")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/historical_outcome_labels_v1_20260615")

LABEL_COLUMNS = [
    "historical_prospect_key",
    "prospect_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "rookie_class_year",
    "identity_match_status",
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
    "label_first3_coverage_seasons",
    "label_first3_total_points",
    "label_first3_best_season_points",
    "label_first3_best_pos_rank",
    "label_first3_starter_seasons",
    "label_first3_zero_or_low_value_flag",
    "label_bust_flag",
    "label_star_flag",
    "label_useful_flag",
    "eval_label_source",
    "eval_join_method",
    "eval_backtest_ready_flag",
    "market_display_rookie_pick_cost",
    "eval_roi_vs_market_cost",
    "eval_reach_flag",
    "eval_value_pick_flag",
]

COVERAGE_COLUMNS = [
    "rookie_class_year",
    "class_rows",
    "label_rows",
    "matched_stat_rows",
    "assumed_zero_rows",
    "full_three_year_rows",
    "partial_window_rows",
    "green_label_rows",
    "yellow_label_rows",
    "red_label_rows",
    "feasibility_status",
    "notes",
]

ISSUE_COLUMNS = ["issue_type", "rookie_class_year", "historical_prospect_key", "prospect_name", "position", "details"]

READINESS_COLUMNS = ["check_name", "status", "rows", "details", "safe_next_step"]

STARTER_RANK = {"QB": 12, "RB": 24, "WR": 36, "TE": 12}
STAR_RANK = {"QB": 6, "RB": 12, "WR": 12, "TE": 8}
USEFUL_RANK = {"QB": 18, "RB": 36, "WR": 48, "TE": 18}


class HistoricalLabelError(RuntimeError):
    """Raised when label package generation fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise HistoricalLabelError(f"Missing required input: {path}")
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
    fumbles_lost = (
        stat(row, "sack_fumbles_lost")
        + stat(row, "rushing_fumbles_lost")
        + stat(row, "receiving_fumbles_lost")
    )
    return_yards = stat(row, "punt_return_yards") + stat(row, "kickoff_return_yards")
    rush_rec_first_downs = stat(row, "rushing_first_downs") + stat(row, "receiving_first_downs")
    two_points = (
        stat(row, "passing_2pt_conversions")
        + stat(row, "rushing_2pt_conversions")
        + stat(row, "receiving_2pt_conversions")
    )
    points = (
        stat(row, "passing_yards") / 30.0
        + stat(row, "passing_tds") * 3.0
        - stat(row, "interceptions", "passing_interceptions") * 1.0
        + stat(row, "rushing_yards") / 10.0
        + stat(row, "rushing_tds") * 4.0
        + stat(row, "receiving_yards") / 10.0
        + stat(row, "receiving_tds") * 4.0
        + return_yards / 30.0
        + stat(row, "special_teams_tds") * 4.0
        + two_points * 2.0
        - fumbles_lost
        + rush_rec_first_downs * 0.4
    )
    return round(points, 3)


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
        if position not in {"QB", "RB", "WR", "TE"}:
            continue
        season = row.get("season", "")
        if season not in {"2021", "2022", "2023", "2024", "2025"}:
            continue
        player_name = row.get("player_display_name") or row.get("player_name", "")
        key = (norm_name(player_name), position, season)
        existing = grouped.setdefault(
            key,
            {
                "player_id": row.get("player_id", ""),
                "player_display_name": player_name,
                "position": position,
                "season": season,
                "games_with_recorded_stats": "0",
                "source_files": set(),
            },
        )
        existing["games_with_recorded_stats"] = str(safe_int(existing["games_with_recorded_stats"]) + 1)
        existing["source_files"].add(row.get("source_file", "") or ("player_stats_2025.csv" if season == "2025" else "player_stats.csv"))
        for field in numeric_fields:
            existing[field] = str(to_float(existing.get(field, "")) + stat(row, field))
    for row in grouped.values():
        row["label_points"] = str(fantasy_points(row))
        row["source_files"] = "|".join(sorted(str(item) for item in row["source_files"] if item))
    return grouped


def position_ranks(aggregated: dict[tuple[str, str, str], dict[str, str]]) -> dict[tuple[str, str, str], int]:
    by_year_pos: dict[tuple[str, str], list[tuple[float, tuple[str, str, str]]]] = defaultdict(list)
    for key, row in aggregated.items():
        _, position, season = key
        by_year_pos[(season, position)].append((to_float(row.get("label_points", "")), key))
    ranks: dict[tuple[str, str, str], int] = {}
    for values in by_year_pos.values():
        values.sort(reverse=True)
        for index, (_, key) in enumerate(values, start=1):
            ranks[key] = index
    return ranks


def label_status(draft_year: int, matched_seasons: int, assumed_zero_seasons: int, missing_future: int) -> tuple[str, str]:
    if missing_future:
        return "YELLOW_PARTIAL_WINDOW", f"{missing_future} future first-three-year season(s) unavailable"
    if matched_seasons:
        return "GREEN_COMPLETE_LABEL", ""
    if assumed_zero_seasons:
        return "YELLOW_ASSUMED_ZERO_NO_RECORDED_STATS", "no recorded stat rows found; zero outcome assumed with identity caveat"
    return "RED_NO_LABEL", "no outcome data available"


def starter_flag(position: str, rank: str) -> str:
    if not rank:
        return "0"
    return "1" if int(rank) <= STARTER_RANK.get(position, 999) else "0"


def build_label_rows(feature_rows: list[dict[str, str]], stats_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    aggregated = aggregate_stats(stats_rows)
    ranks = position_ranks(aggregated)
    rows: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    current_max_year = 2025
    for feature in feature_rows:
        draft_year = safe_int(feature.get("draft_year", ""))
        position = feature.get("position", "")
        player_key = norm_name(feature.get("prospect_name", ""))
        seasons = [draft_year + offset for offset in range(3)]
        label: dict[str, str] = {
            "historical_prospect_key": feature.get("historical_prospect_key", ""),
            "prospect_name": feature.get("prospect_name", ""),
            "normalized_player_name": feature.get("normalized_player_name", "") or player_key,
            "position": position,
            "college": feature.get("college", ""),
            "nfl_team": feature.get("nfl_team", ""),
            "rookie_class_year": str(draft_year),
            "identity_match_status": "name_position_year_match",
            "eval_label_source": "local truth_set_lab v3 nflverse player_stats weekly exports",
            "eval_join_method": "normalized_name_position_season",
            "market_display_rookie_pick_cost": "",
            "eval_roi_vs_market_cost": "",
            "eval_reach_flag": "market_labels_blocked_no_admitted_source",
            "eval_value_pick_flag": "market_labels_blocked_no_admitted_source",
        }
        points: list[float] = []
        ranks_seen: list[int] = []
        starter_seasons = 0
        matched = 0
        assumed_zero = 0
        missing_future = 0
        missing_reasons = []
        scoring_quality_notes = []
        for index, season in enumerate(seasons, start=1):
            label[f"label_year{index}_season"] = str(season)
            if season > current_max_year:
                label[f"label_year{index}_points"] = ""
                label[f"label_year{index}_pos_rank"] = ""
                label[f"label_year{index}_starter_flag"] = ""
                missing_future += 1
                missing_reasons.append(f"year{index}_season_{season}_future_unavailable")
                continue
            stat_key = (player_key, position, str(season))
            stat_row = aggregated.get(stat_key)
            if stat_row:
                matched += 1
                season_points = to_float(stat_row.get("label_points", ""))
                rank = ranks.get(stat_key, 0)
                label[f"label_year{index}_points"] = f"{season_points:.3f}"
                label[f"label_year{index}_pos_rank"] = str(rank) if rank else ""
                starter = starter_flag(position, str(rank) if rank else "")
                label[f"label_year{index}_starter_flag"] = starter
                points.append(season_points)
                if rank:
                    ranks_seen.append(rank)
                if starter == "1":
                    starter_seasons += 1
                if season < 2025:
                    scoring_quality_notes.append(f"season_{season}_return_yards_unavailable")
            else:
                assumed_zero += 1
                label[f"label_year{index}_points"] = "0.000"
                label[f"label_year{index}_pos_rank"] = ""
                label[f"label_year{index}_starter_flag"] = "0"
                points.append(0.0)
                missing_reasons.append(f"year{index}_season_{season}_no_recorded_stats")
                issues.append(
                    {
                        "issue_type": "assumed_zero_no_recorded_stats",
                        "rookie_class_year": str(draft_year),
                        "historical_prospect_key": feature.get("historical_prospect_key", ""),
                        "prospect_name": feature.get("prospect_name", ""),
                        "position": position,
                        "details": f"No {season} stat row found by normalized name/position; label set to 0 with caveat.",
                    }
                )
        best_rank = min(ranks_seen) if ranks_seen else 999
        total = sum(points)
        best_points = max(points) if points else 0.0
        star = best_rank <= STAR_RANK.get(position, 999)
        useful = starter_seasons >= 1 or best_rank <= USEFUL_RANK.get(position, 999)
        zero_low = total < 40.0 and starter_seasons == 0
        bust = zero_low or (best_rank > USEFUL_RANK.get(position, 999) and starter_seasons == 0 and missing_future == 0)
        quality, quality_reason = label_status(draft_year, matched, assumed_zero, missing_future)
        label["label_quality_status"] = quality
        label["label_missing_reason"] = "|".join(dict.fromkeys([quality_reason] + missing_reasons).keys()).strip("|")
        label["label_scoring_quality"] = (
            "exact_non_ppr_with_rush_rec_first_downs_return_yards_partial"
            if scoring_quality_notes
            else "exact_non_ppr_with_rush_rec_first_downs"
        )
        label["label_first3_coverage_seasons"] = str(matched + assumed_zero)
        label["label_first3_total_points"] = f"{total:.3f}"
        label["label_first3_best_season_points"] = f"{best_points:.3f}"
        label["label_first3_best_pos_rank"] = "" if best_rank == 999 else str(best_rank)
        label["label_first3_starter_seasons"] = str(starter_seasons)
        label["label_first3_zero_or_low_value_flag"] = "1" if zero_low else "0"
        label["label_bust_flag"] = "1" if bust else "0"
        label["label_star_flag"] = "1" if star else "0"
        label["label_useful_flag"] = "1" if useful else "0"
        label["eval_backtest_ready_flag"] = "yes" if quality in {"GREEN_COMPLETE_LABEL", "YELLOW_ASSUMED_ZERO_NO_RECORDED_STATS"} else "partial"
        rows.append(label)
    coverage = coverage_rows(rows)
    readiness = readiness_rows(rows)
    return rows, coverage, issues, readiness


def coverage_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_year[row["rookie_class_year"]].append(row)
    for year in ["2021", "2022", "2023", "2024", "2025"]:
        year_rows = by_year.get(year, [])
        green = sum(1 for row in year_rows if row["label_quality_status"] == "GREEN_COMPLETE_LABEL")
        yellow = sum(1 for row in year_rows if row["label_quality_status"].startswith("YELLOW"))
        red = sum(1 for row in year_rows if row["label_quality_status"].startswith("RED"))
        partial = sum(1 for row in year_rows if row["label_quality_status"] == "YELLOW_PARTIAL_WINDOW")
        assumed = sum(1 for row in year_rows if row["label_quality_status"] == "YELLOW_ASSUMED_ZERO_NO_RECORDED_STATS")
        feasibility = "GREEN_LABELABLE" if green + assumed == len(year_rows) and year_rows else "YELLOW_PARTIAL_LABELS" if year_rows else "RED_NO_LABELS"
        notes = "full first-three-year window available" if year in {"2021", "2022", "2023"} else "partial first-three-year window; future seasons unavailable"
        matched_stat_rows = sum(
            1
            for row in year_rows
            if row.get("label_year1_pos_rank") or row.get("label_year2_pos_rank") or row.get("label_year3_pos_rank")
        )
        output.append(
            {
                "rookie_class_year": year,
                "class_rows": str(len(year_rows)),
                "label_rows": str(len(year_rows)),
                "matched_stat_rows": str(matched_stat_rows),
                "assumed_zero_rows": str(assumed),
                "full_three_year_rows": str(len(year_rows) - partial),
                "partial_window_rows": str(partial),
                "green_label_rows": str(green),
                "yellow_label_rows": str(yellow),
                "red_label_rows": str(red),
                "feasibility_status": feasibility,
                "notes": notes,
            }
        )
    return output


def readiness_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    complete = [row for row in rows if row["eval_backtest_ready_flag"] == "yes"]
    partial = [row for row in rows if row["eval_backtest_ready_flag"] == "partial"]
    return [
        {
            "check_name": "historical_label_rows",
            "status": "pass" if rows else "fail",
            "rows": str(len(rows)),
            "details": "Label rows exist for historical feature matrix.",
            "safe_next_step": "join label package in a separate backtest readiness patch",
        },
        {
            "check_name": "full_window_backtest_ready_rows",
            "status": "pass" if complete else "fail",
            "rows": str(len(complete)),
            "details": "Rows with complete 2021-2023 first-three-year label windows, including assumed-zero no-stat outcomes.",
            "safe_next_step": "run backtest on complete-window rows only before tuning",
        },
        {
            "check_name": "partial_window_rows",
            "status": "warning" if partial else "pass",
            "rows": str(len(partial)),
            "details": "2024-2025 rows have incomplete first-three-year windows.",
            "safe_next_step": "exclude partial rows from first tuning run or evaluate year1/year2 only",
        },
        {
            "check_name": "market_labels",
            "status": "blocked",
            "rows": "0",
            "details": "No admitted rookie-cost/ADP market source was linked for labels.",
            "safe_next_step": "register display-only market cost source before ROI labels",
        },
    ]


def validate_labels(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise HistoricalLabelError("No label rows created.")
    keys = [row["historical_prospect_key"] for row in rows]
    if len(keys) != len(set(keys)):
        raise HistoricalLabelError("Duplicate historical_prospect_key labels.")
    for row in rows:
        if not row["prospect_name"] or not row["position"] or not row["rookie_class_year"]:
            raise HistoricalLabelError("Missing identity fields in label row.")
        for key, value in row.items():
            if key.startswith("feature_"):
                raise HistoricalLabelError(f"Feature-prefixed column leaked into label output: {key}")
        if row["label_star_flag"] == "1" and row["label_bust_flag"] == "1":
            raise HistoricalLabelError(f"Star and bust flags both set for {row['prospect_name']}")


def write_readme(output_dir: Path, rows: list[dict[str, str]], coverage: list[dict[str, str]]) -> None:
    counts = Counter(row["label_quality_status"] for row in rows)
    text = f"""# Rookie Historical Outcome Labels v1

Status: local-only evaluation labels.

Rows: {len(rows)}

Quality counts:

- GREEN_COMPLETE_LABEL: {counts.get('GREEN_COMPLETE_LABEL', 0)}
- YELLOW_ASSUMED_ZERO_NO_RECORDED_STATS: {counts.get('YELLOW_ASSUMED_ZERO_NO_RECORDED_STATS', 0)}
- YELLOW_PARTIAL_WINDOW: {counts.get('YELLOW_PARTIAL_WINDOW', 0)}

Coverage:

{chr(10).join(f"- {row['rookie_class_year']}: {row['feasibility_status']} ({row['class_rows']} rows)" for row in coverage)}

Labels are evaluation targets only. They must not be used as rookie-time
features, private scores, app outputs, probabilities, bands, hidden sort keys,
or promoted artifacts.
"""
    (output_dir / "README_ROOKIE_HISTORICAL_OUTCOME_LABELS_V1_20260615.md").write_text(text, encoding="utf-8")


def build_exports(
    historical_features: Path,
    weekly_stats: Path,
    weekly_stats_2025: Path,
    output_dir: Path,
) -> dict[str, int]:
    feature_rows = read_csv(historical_features)
    stats_rows = read_csv(weekly_stats) + read_csv(weekly_stats_2025)
    label_rows, coverage, issues, readiness = build_label_rows(feature_rows, stats_rows)
    validate_labels(label_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_historical_outcome_labels_v1_20260615.csv", label_rows, LABEL_COLUMNS)
    write_csv(output_dir / "rookie_historical_label_coverage_summary_20260615.csv", coverage, COVERAGE_COLUMNS)
    write_csv(output_dir / "rookie_historical_label_quality_issues_20260615.csv", issues, ISSUE_COLUMNS)
    write_csv(output_dir / "rookie_historical_backtest_readiness_20260615.csv", readiness, READINESS_COLUMNS)
    write_readme(output_dir, label_rows, coverage)
    counts = Counter(row["label_quality_status"] for row in label_rows)
    return {
        "label_rows": len(label_rows),
        "coverage_rows": len(coverage),
        "quality_issue_rows": len(issues),
        "green_complete_rows": counts.get("GREEN_COMPLETE_LABEL", 0),
        "yellow_assumed_zero_rows": counts.get("YELLOW_ASSUMED_ZERO_NO_RECORDED_STATS", 0),
        "yellow_partial_rows": counts.get("YELLOW_PARTIAL_WINDOW", 0),
        "backtest_ready_rows": sum(1 for row in label_rows if row["eval_backtest_ready_flag"] == "yes"),
        "partial_rows": sum(1 for row in label_rows if row["eval_backtest_ready_flag"] == "partial"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build rookie historical outcome labels v1.")
    parser.add_argument("--historical-features", type=Path, default=DEFAULT_HISTORICAL_FEATURES)
    parser.add_argument("--weekly-stats", type=Path, default=DEFAULT_WEEKLY_STATS)
    parser.add_argument("--weekly-stats-2025", type=Path, default=DEFAULT_WEEKLY_STATS_2025)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.historical_features, args.weekly_stats, args.weekly_stats_2025, args.output_dir)
    except HistoricalLabelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
