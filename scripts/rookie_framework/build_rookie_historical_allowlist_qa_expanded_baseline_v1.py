"""Build rookie historical allowlist, QA, labels v2, and expanded baseline.

This is a local-only data-quality and baseline script. It does not tune, create
a v2 current board, promote artifacts, or write app-readable outputs.
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
DEFAULT_CURRENT_FEATURES = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/"
    "historical_rookie_backtest_feature_matrix.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615")

POSITIONS = {"QB", "RB", "WR", "TE"}
EXPANSION_YEARS = [str(year) for year in range(2010, 2021)]
COMPLETE_CURRENT_YEARS = {"2021", "2022", "2023"}
PARTIAL_CURRENT_YEARS = {"2024", "2025"}
STARTER_RANK = {"QB": 12, "RB": 24, "WR": 36, "TE": 12}
STAR_RANK = {"QB": 6, "RB": 12, "WR": 12, "TE": 8}
USEFUL_RANK = {"QB": 18, "RB": 36, "WR": 48, "TE": 18}

DRAFT_IDENTITY = {"season", "team", "gsis_id", "pfr_player_id", "cfb_player_id", "pfr_player_name", "position", "college"}
DRAFT_CAPITAL = {"round", "pick"}
DRAFT_DISPLAY = {"category", "side", "age"}
DRAFT_QUARANTINE = {
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

ALLOWLIST_COLUMNS = ["column_name", "classification", "reason", "used_in_features", "used_in_labels", "used_in_display"]
QA_COLUMNS = [
    "draft_year",
    "player_name",
    "position",
    "draft_round",
    "overall_pick",
    "original_join_status",
    "qa_classification",
    "repair_action",
    "post_repair_join_status",
    "label_status_after_qa",
    "notes",
]
REPAIR_COLUMNS = [
    "draft_year",
    "player_name",
    "original_position",
    "repaired_position",
    "repair_type",
    "join_key_used",
    "evidence",
    "scoring_impact",
    "notes",
]
LABEL_COLUMNS = [
    "historical_label_key",
    "source_pool",
    "draft_year",
    "player_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "draft_round",
    "overall_pick",
    "gsis_id",
    "pfr_player_id",
    "cfb_player_id",
    "historical_label_status",
    "backtest_ready",
    "partial_window_only",
    "star_label",
    "bust_label",
    "useful_label",
    "starter_season_count",
    "best_first_3_years_pos_finish",
    "year1_points",
    "year2_points",
    "year3_points",
    "three_year_points",
    "label_quality_notes",
    "label_scoring_quality",
    "guardrails",
]
BASELINE_COLUMNS = [
    "metric_scope",
    "scope_value",
    "bucket",
    "rows",
    "stars_total",
    "stars_captured",
    "star_capture_rate",
    "bust_count",
    "bust_rate",
    "avg_three_year_points",
    "avg_baseline_score",
    "notes",
]
SUMMARY_COLUMNS = [
    "summary_scope",
    "scope_value",
    "rows",
    "star_count",
    "star_rate",
    "bust_count",
    "bust_rate",
    "avg_three_year_points",
    "notes",
]
MISS_COLUMNS = [
    "miss_type",
    "baseline_rank",
    "class_rank",
    "draft_year",
    "player_name",
    "position",
    "baseline_score",
    "three_year_points",
    "star_label",
    "bust_label",
    "historical_label_status",
    "notes",
]


class ExpandedBaselineError(RuntimeError):
    """Raised when expanded baseline build fails."""


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


def to_float(value: str, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


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
        + stat(row, "special_teams_tds") * 4.0
        + two_points * 2.0
        - fumbles_lost
        + first_downs * 0.4,
        3,
    )


def draft_allowlist(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    columns = list(rows[0].keys()) if rows else []
    output = []
    for column in columns:
        if column in DRAFT_IDENTITY:
            classification = "allow_identity"
            reason = "identity/join/display field available at draft time"
            used_features = "no"
            used_labels = "no"
            used_display = "yes"
        elif column in DRAFT_CAPITAL:
            classification = "allow_draft_capital"
            reason = "draft capital available at rookie draft time"
            used_features = "yes"
            used_labels = "no"
            used_display = "yes"
        elif column in DRAFT_DISPLAY:
            classification = "allow_display"
            reason = "context/display only; not used in scoring"
            used_features = "no"
            used_labels = "no"
            used_display = "yes"
        elif column in DRAFT_QUARANTINE:
            classification = "quarantine_future_or_career"
            reason = "career/future outcome field in draft source"
            used_features = "no"
            used_labels = "no"
            used_display = "no"
        else:
            classification = "quarantine_ambiguous"
            reason = "unrecognized draft-source column; quarantine by default"
            used_features = "no"
            used_labels = "no"
            used_display = "no"
        output.append(
            {
                "column_name": column,
                "classification": classification,
                "reason": reason,
                "used_in_features": used_features,
                "used_in_labels": used_labels,
                "used_in_display": used_display,
            }
        )
    return output


def aggregate_stats(
    rows: list[dict[str, str]],
    draft_position_by_id: dict[str, str] | None = None,
) -> tuple[dict[tuple[str, str, str], dict[str, str]], dict[tuple[str, str], list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    grouped: dict[tuple[str, str, str], dict[str, str]] = {}
    by_id_pos: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_name_anypos: dict[str, list[dict[str, str]]] = defaultdict(list)
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
    ]
    for row in rows:
        if row.get("season_type") and row.get("season_type") != "REG":
            continue
        player_id = row.get("player_id", "")
        position = row.get("position_group") or row.get("position", "")
        position_repair_source = ""
        if position not in POSITIONS and draft_position_by_id and player_id in draft_position_by_id:
            position = draft_position_by_id[player_id]
            position_repair_source = "draft_identity_position_by_gsis_id"
        if position not in POSITIONS:
            continue
        season = row.get("season", "")
        name = row.get("player_display_name") or row.get("player_name", "")
        key = (norm_name(name), position, season)
        existing = grouped.setdefault(key, {"player_id": player_id, "player_name": name, "position": position, "season": season, "games_with_recorded_stats": "0", "position_repair_source": ""})
        if position_repair_source:
            existing["position_repair_source"] = position_repair_source
        existing["games_with_recorded_stats"] = str(safe_int(existing["games_with_recorded_stats"]) + 1)
        for field in numeric_fields:
            existing[field] = str(to_float(existing.get(field, "")) + stat(row, field))
    for row in grouped.values():
        row["label_points"] = f"{fantasy_points(row):.3f}"
        by_id_pos[(row.get("player_id", ""), row["position"])].append(row)
        by_name_anypos[norm_name(row["player_name"])].append(row)
    return grouped, by_id_pos, by_name_anypos


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


def choose_position(rows: list[dict[str, str]]) -> str:
    counts = Counter(row["position"] for row in rows)
    return counts.most_common(1)[0][0] if counts else ""


def rows_for_window(rows: list[dict[str, str]], seasons: set[str]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("season") in seasons]


def build_label_from_matches(
    draft: dict[str, str],
    position: str,
    matches_by_season: dict[str, dict[str, str]],
    ranks: dict[tuple[str, str, str], int],
    status: str,
    notes: str,
    backtest_ready: str = "yes",
) -> dict[str, str]:
    year = draft.get("season", "")
    seasons = [str(safe_int(year) + offset) for offset in range(3)]
    points = []
    ranks_seen = []
    starter_seasons = 0
    missing = []
    for season in seasons:
        row = matches_by_season.get(season)
        if row:
            pts = to_float(row.get("label_points", ""))
            rank = ranks.get((norm_name(row["player_name"]), row["position"], season))
            points.append(pts)
            if rank:
                ranks_seen.append(rank)
            if starter_flag(row["position"], rank) == "1":
                starter_seasons += 1
        else:
            points.append(0.0)
            missing.append(f"{season}_no_recorded_stats")
    best_rank = min(ranks_seen) if ranks_seen else 999
    total = sum(points)
    best_points = max(points) if points else 0.0
    star = best_rank <= STAR_RANK.get(position, 999)
    useful = starter_seasons >= 1 or best_rank <= USEFUL_RANK.get(position, 999)
    bust = total < 40.0 and starter_seasons == 0
    return {
        "historical_label_key": f"expanded:{year}:{norm_name(draft.get('pfr_player_name', ''))}:{position}:{draft.get('pick', '')}",
        "source_pool": "expanded_2010_2020",
        "draft_year": year,
        "player_name": draft.get("pfr_player_name", ""),
        "normalized_player_name": norm_name(draft.get("pfr_player_name", "")),
        "position": position,
        "college": draft.get("college", ""),
        "nfl_team": draft.get("team", ""),
        "draft_round": draft.get("round", ""),
        "overall_pick": draft.get("pick", ""),
        "gsis_id": draft.get("gsis_id", ""),
        "pfr_player_id": draft.get("pfr_player_id", ""),
        "cfb_player_id": draft.get("cfb_player_id", ""),
        "historical_label_status": status,
        "backtest_ready": backtest_ready,
        "partial_window_only": "no",
        "star_label": "1" if star else "0",
        "bust_label": "1" if bust else "0",
        "useful_label": "1" if useful else "0",
        "starter_season_count": str(starter_seasons),
        "best_first_3_years_pos_finish": "" if best_rank == 999 else str(best_rank),
        "year1_points": f"{points[0]:.3f}",
        "year2_points": f"{points[1]:.3f}",
        "year3_points": f"{points[2]:.3f}",
        "three_year_points": f"{total:.3f}",
        "label_quality_notes": "|".join([notes] + missing).strip("|"),
        "label_scoring_quality": "exact_non_ppr_with_rush_rec_first_downs_return_yards_partial_pre_2025",
        "guardrails": "labels_eval_only; no_tuning; no_app; no_private_score; no_probability; no_band",
    }


def build_expanded_2010_2020(
    draft_rows: list[dict[str, str]],
    stat_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    draft_position_by_id = {
        row.get("gsis_id", ""): row.get("position", "")
        for row in draft_rows
        if row.get("season", "") in EXPANSION_YEARS and row.get("position", "") in POSITIONS and row.get("gsis_id")
    }
    aggregated, by_id_pos, by_name_anypos = aggregate_stats(stat_rows, draft_position_by_id)
    ranks = position_ranks(aggregated)
    labels = []
    qa_rows = []
    repairs = []
    for draft in draft_rows:
        year = draft.get("season", "")
        original_position = draft.get("position", "")
        if year not in EXPANSION_YEARS or original_position not in POSITIONS:
            continue
        seasons = {str(safe_int(year) + offset) for offset in range(3)}
        normalized = norm_name(draft.get("pfr_player_name", ""))
        same_position = {
            season: aggregated[(normalized, original_position, season)]
            for season in seasons
            if (normalized, original_position, season) in aggregated
        }
        qa_class = ""
        repair_action = "none"
        post_join = "joined_by_normalized_name_position" if same_position else "no_first3_stat_match"
        label_status = "GREEN_COMPLETE"
        notes = ""
        repaired_position = original_position
        matches = same_position
        if same_position and any(row.get("position_repair_source") == "draft_identity_position_by_gsis_id" for row in same_position.values()):
            qa_class = "id_repaired"
            repair_action = "used_gsis_id_to_recover_blank_position_stat_rows"
            post_join = "joined_by_gsis_id_inferred_draft_position"
            notes = "identity-only gsis_id repair for blank local stat position"
        elif not same_position:
            id_rows = rows_for_window(by_id_pos.get((draft.get("gsis_id", ""), original_position), []), seasons)
            anypos_rows = rows_for_window(by_name_anypos.get(normalized, []), seasons)
            if id_rows:
                qa_class = "id_repaired"
                repair_action = "used_gsis_id_to_recover_first3_stat_rows"
                post_join = "joined_by_gsis_id_position"
                matches = {row["season"]: row for row in id_rows}
                notes = "identity-only gsis_id repair"
            elif anypos_rows:
                repaired_position = choose_position(anypos_rows)
                qa_class = "position_mismatch_repaired"
                repair_action = f"normalized_position_from_{original_position}_to_{repaired_position}"
                post_join = "joined_by_normalized_name_repaired_position"
                matches = {row["season"]: row for row in anypos_rows if row["position"] == repaired_position}
                notes = "identity-only position normalization repair"
            else:
                later_rows = by_name_anypos.get(normalized, [])
                if later_rows:
                    qa_class = "stat_source_coverage_gap"
                    repair_action = "excluded_from_model_pool_pending_manual_review"
                    post_join = "no_first3_stat_match_later_stats_exist"
                    label_status = "EXCLUDED"
                    notes = "later stat rows exist outside first-three-year window; exclude pending manual review"
                else:
                    qa_class = "true_zero_no_nfl_fantasy_stats"
                    repair_action = "kept_zero_label_after_no_local_stat_evidence"
                    label_status = "YELLOW_ASSUMED_ZERO"
                    notes = "no local first-three-year stat evidence; zero outcome retained with caveat"
        else:
            qa_class = "not_assumed_zero"
        if qa_class != "not_assumed_zero":
            qa_rows.append(
                {
                    "draft_year": year,
                    "player_name": draft.get("pfr_player_name", ""),
                    "position": original_position,
                    "draft_round": draft.get("round", ""),
                    "overall_pick": draft.get("pick", ""),
                    "original_join_status": "YELLOW_COMPLETE_WINDOW_ASSUMED_ZERO",
                    "qa_classification": qa_class,
                    "repair_action": repair_action,
                    "post_repair_join_status": post_join,
                    "label_status_after_qa": label_status,
                    "notes": notes,
                }
            )
        if qa_class in {"id_repaired", "position_mismatch_repaired"}:
            repairs.append(
                {
                    "draft_year": year,
                    "player_name": draft.get("pfr_player_name", ""),
                    "original_position": original_position,
                    "repaired_position": repaired_position,
                    "repair_type": qa_class,
                    "join_key_used": "gsis_id" if qa_class == "id_repaired" else "normalized_name",
                    "evidence": f"matched_seasons={'|'.join(sorted(matches))}",
                    "scoring_impact": "identity_only_repair_no_player_specific_score_rule",
                    "notes": notes,
                }
            )
        labels.append(
            build_label_from_matches(
                draft,
                repaired_position,
                matches,
                ranks,
                label_status,
                notes,
                backtest_ready="no" if label_status == "EXCLUDED" else "yes",
            )
        )
    return labels, qa_rows, repairs


def current_features_by_key(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("historical_prospect_key", ""): row for row in rows if row.get("historical_prospect_key")}


def append_current_labels(label_rows: list[dict[str, str]], feature_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    features = current_features_by_key(feature_rows)
    output = []
    for row in label_rows:
        year = row.get("rookie_class_year", "")
        feature = features.get(row.get("historical_prospect_key", ""), {})
        if year in COMPLETE_CURRENT_YEARS:
            status = "GREEN_COMPLETE" if row.get("eval_backtest_ready_flag") == "yes" else "YELLOW_ASSUMED_ZERO"
            backtest_ready = "yes"
            partial = "no"
        elif year in PARTIAL_CURRENT_YEARS:
            status = "YELLOW_PARTIAL_WINDOW"
            backtest_ready = "no"
            partial = "yes"
        else:
            continue
        output.append(
            {
                "historical_label_key": row.get("historical_prospect_key", ""),
                "source_pool": "current_2021_2025_v1",
                "draft_year": year,
                "player_name": row.get("prospect_name", ""),
                "normalized_player_name": row.get("normalized_player_name", ""),
                "position": row.get("position", ""),
                "college": row.get("college", ""),
                "nfl_team": row.get("nfl_team", ""),
                "draft_round": feature.get("draft_round", ""),
                "overall_pick": feature.get("draft_pick", ""),
                "gsis_id": "",
                "pfr_player_id": "",
                "cfb_player_id": "",
                "historical_label_status": status,
                "backtest_ready": backtest_ready,
                "partial_window_only": partial,
                "star_label": row.get("label_star_flag", ""),
                "bust_label": row.get("label_bust_flag", ""),
                "useful_label": row.get("label_useful_flag", ""),
                "starter_season_count": row.get("label_first3_starter_seasons", ""),
                "best_first_3_years_pos_finish": row.get("label_first3_best_pos_rank", ""),
                "year1_points": row.get("label_year1_points", ""),
                "year2_points": row.get("label_year2_points", ""),
                "year3_points": row.get("label_year3_points", ""),
                "three_year_points": row.get("label_first3_total_points", ""),
                "label_quality_notes": row.get("label_missing_reason", ""),
                "label_scoring_quality": row.get("label_scoring_quality", ""),
                "guardrails": "labels_eval_only; no_tuning; no_app; no_private_score; no_probability; no_band",
            }
        )
    return output


def draft_points(round_no: str, pick: str) -> float:
    round_value = safe_int(round_no)
    pick_value = to_float(pick)
    round_score = {1: 82, 2: 66, 3: 52, 4: 38, 5: 28, 6: 20, 7: 14}.get(round_value, 6)
    pick_bonus = max(0.0, 18.0 - pick_value / 8.0) if pick_value else 0.0
    return max(0.0, min(100.0, round_score + pick_bonus))


def position_score(position: str) -> float:
    return {"RB": 72.0, "WR": 70.0, "TE": 42.0, "QB": 24.0}.get(position, 40.0)


def baseline_score(row: dict[str, str]) -> float:
    score = draft_points(row.get("draft_round", ""), row.get("overall_pick", "")) * 0.78 + position_score(row.get("position", "")) * 0.22
    return round(score, 3)


def baseline_rows(labels: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [dict(row) for row in labels if row.get("backtest_ready") == "yes" and row.get("partial_window_only") == "no"]
    for row in rows:
        row["baseline_score"] = f"{baseline_score(row):.3f}"
    rows.sort(key=lambda row: (-to_float(row["baseline_score"]), to_float(row.get("overall_pick", ""), 999), row.get("player_name", "")))
    class_counts: Counter[str] = Counter()
    for index, row in enumerate(rows, start=1):
        row["baseline_rank"] = str(index)
        class_counts[row["draft_year"]] += 1
        row["class_rank"] = str(class_counts[row["draft_year"]])
    return rows


def avg(values: list[float]) -> str:
    return f"{sum(values) / len(values):.3f}" if values else ""


def metric_for(rows: list[dict[str, str]], scope: str, value: str, bucket: int) -> dict[str, str]:
    rank_field = "baseline_rank" if scope == "overall" else "class_rank" if scope == "year" else "position_rank"
    scoped = rows
    if scope == "year":
        scoped = [row for row in rows if row["draft_year"] == value]
    elif scope == "position":
        scoped = [row for row in rows if row["position"] == value]
        scoped = sorted(scoped, key=lambda row: (-to_float(row["baseline_score"]), to_float(row.get("overall_pick", ""), 999), row["player_name"]))
        for index, row in enumerate(scoped, start=1):
            row["position_rank"] = str(index)
    top = [row for row in scoped if safe_int(row.get(rank_field, "999999")) <= bucket]
    stars_total = sum(1 for row in scoped if row["star_label"] == "1")
    stars = sum(1 for row in top if row["star_label"] == "1")
    busts = sum(1 for row in top if row["bust_label"] == "1")
    return {
        "metric_scope": scope,
        "scope_value": value,
        "bucket": f"top_{bucket}",
        "rows": str(len(top)),
        "stars_total": str(stars_total),
        "stars_captured": str(stars),
        "star_capture_rate": avg([stars / stars_total]) if stars_total else "",
        "bust_count": str(busts),
        "bust_rate": avg([busts / len(top)]) if top else "",
        "avg_three_year_points": avg([to_float(row["three_year_points"]) for row in top]),
        "avg_baseline_score": avg([to_float(row["baseline_score"]) for row in top]),
        "notes": "expanded draft-capital/position baseline; no tuning",
    }


def expanded_baseline(labels: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    rows = baseline_rows(labels)
    metrics = []
    for bucket in [12, 24, 36]:
        metrics.append(metric_for(rows, "overall", "all", bucket))
    for year in sorted({row["draft_year"] for row in rows}, key=safe_int):
        for bucket in [12, 24, 36]:
            metrics.append(metric_for(rows, "year", year, bucket))
    for position in sorted({row["position"] for row in rows}):
        for bucket in [12, 24, 36]:
            metrics.append(metric_for(rows, "position", position, bucket))
    summary = []
    for scope, values in [
        ("year", sorted({row["draft_year"] for row in rows}, key=safe_int)),
        ("position", sorted({row["position"] for row in rows})),
    ]:
        for value in values:
            scoped = [row for row in rows if row["draft_year"] == value] if scope == "year" else [row for row in rows if row["position"] == value]
            stars = sum(1 for row in scoped if row["star_label"] == "1")
            busts = sum(1 for row in scoped if row["bust_label"] == "1")
            summary.append(
                {
                    "summary_scope": scope,
                    "scope_value": value,
                    "rows": str(len(scoped)),
                    "star_count": str(stars),
                    "star_rate": avg([stars / len(scoped)]) if scoped else "",
                    "bust_count": str(busts),
                    "bust_rate": avg([busts / len(scoped)]) if scoped else "",
                    "avg_three_year_points": avg([to_float(row["three_year_points"]) for row in scoped]),
                    "notes": "complete-window backtest-ready rows only",
                }
            )
    misses = []
    for row in rows:
        if safe_int(row["baseline_rank"]) <= 36 and row["bust_label"] == "1":
            misses.append({**miss_row(row), "miss_type": "high_ranked_bust", "notes": "diagnosis only; no player-specific tuning"})
        if safe_int(row["baseline_rank"]) > 36 and row["star_label"] == "1":
            misses.append({**miss_row(row), "miss_type": "missed_star", "notes": "diagnosis only; no player-specific tuning"})
    return metrics, summary, misses


def miss_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "baseline_rank": row.get("baseline_rank", ""),
        "class_rank": row.get("class_rank", ""),
        "draft_year": row.get("draft_year", ""),
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "baseline_score": row.get("baseline_score", ""),
        "three_year_points": row.get("three_year_points", ""),
        "star_label": row.get("star_label", ""),
        "bust_label": row.get("bust_label", ""),
        "historical_label_status": row.get("historical_label_status", ""),
    }


def validate_outputs(allowlist: list[dict[str, str]], labels: list[dict[str, str]]) -> None:
    bad = [row["column_name"] for row in allowlist if row["classification"].startswith("quarantine") and row["used_in_features"] == "yes"]
    if bad:
        raise ExpandedBaselineError("Quarantined draft fields marked as features: " + ", ".join(bad))
    keys = [row["historical_label_key"] for row in labels]
    if len(keys) != len(set(keys)):
        raise ExpandedBaselineError("Duplicate expanded historical label keys.")
    for row in labels:
        if row["backtest_ready"] == "yes" and (not row["player_name"] or not row["position"] or not row["draft_year"]):
            raise ExpandedBaselineError("Backtest-ready row missing identity fields.")


def write_readme(output_dir: Path, counts: dict[str, int]) -> None:
    text = f"""# Rookie Historical Allowlist QA Expanded Baseline

Status: local-only data-quality and expanded baseline package.

- Expanded label rows v2: {counts.get('expanded_label_rows', 0)}
- Backtest-ready complete-window rows: {counts.get('backtest_ready_rows', 0)}
- Partial/report-only rows: {counts.get('partial_rows', 0)}
- Assumed-zero rows audited: {counts.get('qa_rows', 0)}
- Repair rows: {counts.get('repair_rows', 0)}

No tuning, v2 board, production ranking, private score, app output,
probability, band, hidden sort key, or promoted artifact was created.
"""
    (output_dir / "README_ROOKIE_HISTORICAL_ALLOWLIST_QA_EXPANDED_BASELINE_20260615.md").write_text(text, encoding="utf-8")


def build_exports(
    player_stats_path: Path,
    draft_path: Path,
    current_labels_path: Path,
    current_features_path: Path,
    output_dir: Path,
) -> dict[str, int]:
    stats = read_csv(player_stats_path)
    drafts = read_csv(draft_path)
    current_labels = read_csv(current_labels_path)
    current_features = read_csv(current_features_path)
    if not stats:
        raise ExpandedBaselineError(f"Missing player stats source: {player_stats_path}")
    if not drafts:
        raise ExpandedBaselineError(f"Missing draft source: {draft_path}")
    allowlist = draft_allowlist(drafts)
    expanded_rows, qa_rows, repair_rows = build_expanded_2010_2020(drafts, stats)
    current_rows = append_current_labels(current_labels, current_features)
    labels = expanded_rows + current_rows
    validate_outputs(allowlist, labels)
    metrics, summary, misses = expanded_baseline(labels)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "draft_source_allowlist_audit_20260615.csv", allowlist, ALLOWLIST_COLUMNS)
    write_csv(output_dir / "assumed_zero_qa_20260615.csv", qa_rows, QA_COLUMNS)
    write_csv(output_dir / "alias_id_repair_actions_20260615.csv", repair_rows, REPAIR_COLUMNS)
    write_csv(output_dir / "expanded_historical_labels_v2_20260615.csv", labels, LABEL_COLUMNS)
    write_csv(output_dir / "expanded_baseline_results_20260615.csv", metrics, BASELINE_COLUMNS)
    write_csv(output_dir / "expanded_baseline_year_position_summary_20260615.csv", summary, SUMMARY_COLUMNS)
    write_csv(output_dir / "expanded_baseline_top_misses_and_busts_20260615.csv", misses, MISS_COLUMNS)
    counts = {
        "allowlist_rows": len(allowlist),
        "qa_rows": len(qa_rows),
        "repair_rows": len(repair_rows),
        "expanded_label_rows": len(labels),
        "expanded_2010_2020_rows": len(expanded_rows),
        "current_2021_2025_rows": len(current_rows),
        "backtest_ready_rows": sum(1 for row in labels if row["backtest_ready"] == "yes" and row["partial_window_only"] == "no"),
        "partial_rows": sum(1 for row in labels if row["partial_window_only"] == "yes"),
        "excluded_rows": sum(1 for row in labels if row["historical_label_status"] == "EXCLUDED"),
        "baseline_metric_rows": len(metrics),
        "baseline_miss_rows": len(misses),
    }
    write_readme(output_dir, counts)
    return counts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build rookie historical allowlist QA expanded baseline.")
    parser.add_argument("--player-stats", type=Path, default=DEFAULT_PLAYER_STATS)
    parser.add_argument("--draft-picks", type=Path, default=DEFAULT_DRAFT_PICKS)
    parser.add_argument("--current-labels", type=Path, default=DEFAULT_CURRENT_LABELS)
    parser.add_argument("--current-features", type=Path, default=DEFAULT_CURRENT_FEATURES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.player_stats, args.draft_picks, args.current_labels, args.current_features, args.output_dir)
    except ExpandedBaselineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
