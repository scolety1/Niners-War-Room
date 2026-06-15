"""Audit source-safe historical rookie feature-family availability.

This is an inventory and join-feasibility audit only. It does not tune, create
a v2 board, write app-readable outputs, or promote artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


DEFAULT_LABELS = Path(
    "local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/"
    "expanded_historical_labels_v2_20260615.csv"
)
DEFAULT_CURRENT_FEATURES = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/"
    "admitted_prospect_current_feature_matrix.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/historical_feature_family_availability_audit_20260615")
POSITIONS = {"QB", "RB", "WR", "TE", "FB"}


SOURCE_CANDIDATES = [
    {
        "source_id": "nflverse_draft_picks",
        "path": "local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/nflverse_draft_picks.csv",
        "family": "draft_capital_identity",
    },
    {
        "source_id": "rotowire_cfb_stats_all",
        "path": "local_exports/model_v4/prospect_sources/latest/files/source_project/data/rotowire/processed/rotowire_cfb_stats_all.csv",
        "family": "college_production",
    },
    {
        "source_id": "rotowire_cfb_targets_all",
        "path": "local_exports/model_v4/prospect_sources/latest/files/source_project/data/rotowire/processed/rotowire_cfb_targets_all.csv",
        "family": "target_earning_receiving_role",
    },
    {
        "source_id": "rotowire_cfb_advanced_team_stats_all",
        "path": "local_exports/model_v4/prospect_sources/latest/files/source_project/data/rotowire/processed/rotowire_cfb_advanced_team_stats_all.csv",
        "family": "team_context_market_share_denominators",
    },
    {
        "source_id": "combine_skill_positions_all",
        "path": "local_exports/model_v4/prospect_sources/latest/files/source_project/data/third_party/nfl_draft_data/processed/combine_skill_positions_all.csv",
        "family": "athletic_testing",
    },
    {
        "source_id": "rotowire_workout_stats",
        "path": "local_exports/model_v4/prospect_sources/latest/files/source_project/data/rotowire/processed/rotowire_workout_stats.csv",
        "family": "workout_athletic_testing",
    },
    {
        "source_id": "rotowire_cfb_injury_report_2026",
        "path": "local_exports/model_v4/prospect_sources/latest/files/source_project/data/rotowire/processed/rotowire_cfb_injury_report_2026.csv",
        "family": "current_injury_flags",
    },
    {
        "source_id": "rotowire_rookie_rankings_2026",
        "path": "local_exports/model_v4/prospect_sources/latest/files/source_project/data/rotowire/processed/rotowire_rookie_rankings_2026.csv",
        "family": "display_only_rankings_and_stat_context",
    },
    {
        "source_id": "historical_rookie_backtest_feature_matrix",
        "path": "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/historical_rookie_backtest_feature_matrix.csv",
        "family": "historical_joined_feature_matrix_2021_2025",
    },
    {
        "source_id": "admitted_prospect_current_feature_matrix",
        "path": "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/admitted_prospect_current_feature_matrix.csv",
        "family": "current_2026_joined_feature_matrix",
    },
    {
        "source_id": "expanded_historical_labels_v2",
        "path": "local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/expanded_historical_labels_v2_20260615.csv",
        "family": "evaluation_labels",
    },
    {
        "source_id": "draft_ranking_model_v1",
        "path": "local_exports/rookie_framework/draft_ranking_model_v1_20260615/rookie_draft_ranking_v1_20260615.csv",
        "family": "current_manual_board_output",
    },
]


def norm_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", value)
    return re.sub(r"[^a-z0-9]", "", value)


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


def safe_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def year_values(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    values = set()
    for row in rows:
        for column in columns:
            value = row.get(column, "")
            if value and str(value).strip():
                values.add(str(value).strip())
    return sorted(values, key=safe_int)


def position_values(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    values = set()
    for row in rows:
        for column in columns:
            value = row.get(column, "")
            if value and str(value).strip():
                values.add(str(value).strip())
    return sorted(values)


def classify_source(source_id: str, family: str, columns: list[str]) -> tuple[str, str]:
    joined = " ".join([source_id, family, " ".join(columns)]).lower()
    if source_id == "nflverse_draft_picks":
        return "allowed_feature", "use_now"
    if source_id in {
        "rotowire_cfb_stats_all",
        "rotowire_cfb_targets_all",
        "rotowire_cfb_advanced_team_stats_all",
        "combine_skill_positions_all",
        "rotowire_workout_stats",
        "rotowire_cfb_injury_report_2026",
        "historical_rookie_backtest_feature_matrix",
        "admitted_prospect_current_feature_matrix",
    }:
        return "allowed_feature", "backfill_candidate"
    if source_id in {"rotowire_rookie_rankings_2026", "draft_ranking_model_v1"}:
        return "blocked_public_rank_projection_adp", "display_only"
    if "label" in family or "outcome" in joined or "post_draft_outcomes" in joined:
        return "evaluation_label_only", "label_only"
    if "rank" in joined or "adp" in joined or "market" in joined or "projection" in joined or "consensus" in joined:
        return "blocked_public_rank_projection_adp", "display_only"
    if "probability" in joined or "band" in joined or "outcome_probability" in joined:
        return "blocked_probability_or_band", "quarantine"
    if any(term in joined for term in ["w_av", "car_av", "dr_av", "probowls", "allpro", "seasons_started", "career"]):
        if "nflverse_draft_picks" in source_id:
            return "allowed_feature", "backfill_candidate"
        return "blocked_future_or_career", "quarantine"
    return "unknown_needs_human_review", "needs_tim_file"


def inspect_source(candidate: dict[str, str]) -> dict[str, str]:
    path = REPO_ROOT / candidate["path"]
    if not path.exists():
        return {
            "source_id": candidate["source_id"],
            "path": candidate["path"],
            "exists": "no",
            "row_count": "0",
            "year_coverage": "",
            "position_coverage": "",
            "key_columns": "",
            "stable_ids_available": "",
            "likely_join_keys": "",
            "feature_family": candidate["family"],
            "leakage_classification": "unknown_needs_human_review",
            "recommended_action": "needs_tim_file",
            "notes": "source not found locally",
        }
    rows = read_csv(path)
    columns = list(rows[0].keys()) if rows else []
    years = year_values(rows, ["season", "year", "draft_year", "rookie_class_year"])
    positions = position_values(rows, ["position", "position_group", "pos"])
    stable_ids = [column for column in columns if column in {"gsis_id", "pfr_player_id", "cfb_player_id", "player_id", "espn_athlete_id", "nfl_person_id", "canonical_prospect_key", "historical_prospect_key"}]
    likely_join_keys = []
    if stable_ids:
        likely_join_keys.extend(stable_ids)
    for column in ["player", "player_name", "pfr_player_name", "prospect_name", "normalized_player_name", "position", "college", "team", "draft_year", "season", "year"]:
        if column in columns:
            likely_join_keys.append(column)
    classification, action = classify_source(candidate["source_id"], candidate["family"], columns)
    return {
        "source_id": candidate["source_id"],
        "path": candidate["path"],
        "exists": "yes",
        "row_count": str(len(rows)),
        "year_coverage": f"{years[0]}-{years[-1]}" if years else "",
        "position_coverage": "|".join(position for position in positions if position in POSITIONS) or "|".join(positions[:12]),
        "key_columns": "|".join(columns[:28]),
        "stable_ids_available": "|".join(stable_ids),
        "likely_join_keys": "|".join(dict.fromkeys(likely_join_keys)),
        "feature_family": candidate["family"],
        "leakage_classification": classification,
        "recommended_action": action,
        "notes": source_note(candidate["source_id"], years, positions),
    }


def source_note(source_id: str, years: list[str], positions: list[str]) -> str:
    if source_id in {"rotowire_cfb_stats_all", "rotowire_cfb_targets_all", "rotowire_cfb_advanced_team_stats_all"}:
        return "local CFB source appears to cover 2020-2025 only; valuable for 2021-2023 historical plus 2026 current, not 2010-2019"
    if source_id == "combine_skill_positions_all":
        return "broad 2006-2026 athletic source; source-license status needs human acceptance before private scoring"
    if source_id == "rotowire_workout_stats":
        return "workout source covers current and some historical draft years; join repair likely needed"
    if source_id == "rotowire_rookie_rankings_2026":
        return "rankings/market-like source; display-only context, not private score"
    return ""


def classify_column(source_id: str, column: str) -> tuple[str, str]:
    c = column.lower()
    if c in {"round", "pick", "draft_round", "draft_pick", "overall_pick"}:
        return "allowed_feature", "draft capital"
    if source_id == "nflverse_draft_picks" and (
        c
        in {
            "to",
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
    ):
        return "blocked_future_or_career", "future/career NFL outcome field in draft source"
    if c in {"age", "age_at_draft", "date_of_birth", "dob", "early_declare", "college_class"}:
        return "allowed_feature", "age/experience feature if rookie-time source-safe"
    if c in {
        "player",
        "player_name",
        "prospect_name",
        "pfr_player_name",
        "normalized_player_name",
        "gsis_id",
        "pfr_player_id",
        "cfb_player_id",
        "player_id",
        "espn_athlete_id",
        "nfl_person_id",
        "team",
        "college",
        "school",
        "nfl_team",
        "season",
        "year",
        "draft_year",
        "position",
        "position_group",
        "first_name",
        "last_name",
        "category",
        "side",
    }:
        return "identity_display_only", "identity/display/join/grouping only"
    if any(term in c for term in ["rank", "adp", "projection", "consensus", "market", "comparison", "grade"]):
        return "blocked_public_rank_projection_adp", "display-only or quarantine"
    if any(term in c for term in ["w_av", "car_av", "dr_av", "probowls", "allpro", "seasons_started", "hof", "career", "games_started"]):
        return "blocked_future_or_career", "future/career outcome field"
    if any(term in c for term in ["star_label", "bust_label", "useful_label", "points", "pos_finish", "starter_season", "label"]):
        return "evaluation_label_only", "evaluation label only"
    if any(term in c for term in ["height", "weight", "forty", "shuttle", "cone", "vertical", "broad", "bench", "arm", "hand", "wingspan", "ten_yard", "twenty_yard"]):
        return "allowed_feature", "athletic/size feature if source accepted"
    if any(term in c for term in ["passing", "rushing", "receiving", "target", "receptions", "yards", "tds", "attempt", "games", "pass_pct", "run_pct", "plays"]):
        return "allowed_feature", "pre-draft college production/team context if time-safe"
    if any(term in c for term in ["injury", "status", "return_date"]):
        return "allowed_feature", "pre-draft/current injury flag if date-safe"
    if c in {"source", "source_file", "source_repo", "source_license_status", "dataset", "measurement_scope", "collected_at_utc", "receipt_pointers_json", "source_status_json"}:
        return "identity_display_only", "source receipt/audit metadata"
    return "unknown_needs_human_review", "needs column-level review"


def column_audit(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for item in inventory:
        if item["exists"] != "yes":
            continue
        path = REPO_ROOT / item["path"]
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
        for column in columns:
            classification, reason = classify_column(item["source_id"], column)
            rows.append(
                {
                    "source_id": item["source_id"],
                    "column_name": column,
                    "column_classification": classification,
                    "reason": reason,
                    "private_score_allowed": "yes" if classification == "allowed_feature" else "no",
                }
            )
    return rows


def expanded_pool(labels_path: Path) -> list[dict[str, str]]:
    rows = read_csv(labels_path)
    return [
        row
        for row in rows
        if row.get("backtest_ready") == "yes"
        and row.get("partial_window_only") == "no"
        and 2010 <= safe_int(row.get("draft_year", "")) <= 2023
    ]


def current_pool(current_features_path: Path) -> list[dict[str, str]]:
    if not current_features_path.exists():
        return []
    return read_csv(current_features_path)


def source_key(row: dict[str, str], name_columns: list[str], year_column: str, position_column: str = "position") -> tuple[str, str, str]:
    name = ""
    for column in name_columns:
        if row.get(column):
            name = row[column]
            break
    return (norm_name(name), row.get(position_column, ""), row.get(year_column, ""))


def build_index(rows: list[dict[str, str]], name_columns: list[str], year_column: str, position_column: str = "position") -> dict[tuple[str, str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = source_key(row, name_columns, year_column, position_column)
        if key[0] and key[1] and key[2]:
            index[key].append(row)
    return index


def join_preview_for_source(source_id: str, source_path: Path, historical_rows: list[dict[str, str]], current_rows: list[dict[str, str]]) -> dict[str, str]:
    if not source_path.exists():
        return join_result(source_id, "not_found", 0, 0, 0, 0, 0, "missing source")
    source_rows = read_csv(source_path)
    if source_id == "rotowire_cfb_stats_all":
        return join_by_final_college_season(source_id, source_rows, historical_rows, current_rows, ["player"])
    if source_id == "rotowire_cfb_targets_all":
        return join_by_final_college_season(source_id, source_rows, historical_rows, current_rows, ["player"])
    if source_id == "combine_skill_positions_all":
        return join_by_draft_year(source_id, source_rows, historical_rows, current_rows, ["player"], "year")
    if source_id == "rotowire_workout_stats":
        return join_by_draft_year(source_id, source_rows, historical_rows, current_rows, ["player"], "draft_year")
    if source_id == "historical_rookie_backtest_feature_matrix":
        source_keys = {row.get("historical_prospect_key", "") for row in source_rows}
        attempted = sum(1 for row in historical_rows if row.get("historical_label_key", "").startswith("backtest:"))
        joined = sum(1 for row in historical_rows if row.get("historical_label_key", "") in source_keys)
        return join_result(source_id, "historical_prospect_key", attempted, joined, attempted - joined, 0, 0, "2021-2023 historical matrix joins by key; 2010-2020 absent")
    if source_id == "admitted_prospect_current_feature_matrix":
        joined = len(source_rows)
        return join_result(source_id, "canonical_current_matrix", len(current_rows), joined, max(0, len(current_rows) - joined), 0, 0, "current 2026 matrix is already joined")
    if source_id == "nflverse_draft_picks":
        ids = {(row.get("season", ""), row.get("pick", ""), row.get("position", "")) for row in source_rows}
        attempted = len(historical_rows)
        joined = sum(1 for row in historical_rows if (row.get("draft_year", ""), row.get("overall_pick", ""), row.get("position", "")) in ids)
        return join_result(source_id, "draft_year_pick_position", attempted, joined, attempted - joined, 0, 0, "draft source underlies expanded pool; career columns quarantined")
    return join_result(source_id, "not_attempted", 0, 0, 0, 0, 0, "join not attempted for non-feature or display-only source")


def join_by_final_college_season(source_id: str, source_rows: list[dict[str, str]], historical_rows: list[dict[str, str]], current_rows: list[dict[str, str]], name_columns: list[str]) -> dict[str, str]:
    index = build_index(source_rows, name_columns, "season")
    attempted = len(historical_rows) + len(current_rows)
    joined = 0
    duplicate = 0
    for row in historical_rows:
        final_year = str(safe_int(row.get("draft_year", "")) - 1)
        matches = index.get((norm_name(row.get("player_name", "")), row.get("position", ""), final_year), [])
        if matches:
            joined += 1
        if len(matches) > 1:
            duplicate += 1
    for row in current_rows:
        final_year = str(safe_int(row.get("draft_year", "")) - 1)
        matches = index.get((norm_name(row.get("prospect_name", "")), row.get("position", ""), final_year), [])
        if matches:
            joined += 1
        if len(matches) > 1:
            duplicate += 1
    note = "joins by normalized player + position + final college season; older 2010-2020 mostly unavailable if final college season before 2020"
    return join_result(source_id, "normalized_name_position_final_college_season", attempted, joined, attempted - joined, duplicate, 0, note)


def join_by_draft_year(source_id: str, source_rows: list[dict[str, str]], historical_rows: list[dict[str, str]], current_rows: list[dict[str, str]], name_columns: list[str], year_column: str) -> dict[str, str]:
    index = build_index(source_rows, name_columns, year_column)
    attempted = len(historical_rows) + len(current_rows)
    joined = 0
    duplicate = 0
    for row in historical_rows:
        matches = index.get((norm_name(row.get("player_name", "")), row.get("position", ""), row.get("draft_year", "")), [])
        if matches:
            joined += 1
        if len(matches) > 1:
            duplicate += 1
    for row in current_rows:
        matches = index.get((norm_name(row.get("prospect_name", "")), row.get("position", ""), row.get("draft_year", "")), [])
        if matches:
            joined += 1
        if len(matches) > 1:
            duplicate += 1
    return join_result(source_id, f"normalized_name_position_{year_column}", attempted, joined, attempted - joined, duplicate, 0, "name/position/year join preview; stable source IDs do not align to expanded pool IDs yet")


def join_result(source_id: str, method: str, attempted: int, joined: int, unjoined: int, duplicates: int, ambiguous: int, notes: str) -> dict[str, str]:
    confidence = "not_attempted"
    if attempted:
        ratio = joined / attempted
        if ratio >= 0.85 and duplicates == 0:
            confidence = "high"
        elif ratio >= 0.45:
            confidence = "medium"
        elif ratio > 0:
            confidence = "low"
        else:
            confidence = "none"
    return {
        "source_id": source_id,
        "join_method": method,
        "attempted_rows": str(attempted),
        "joined_rows": str(joined),
        "unjoined_rows": str(unjoined),
        "duplicate_keys": str(duplicates),
        "ambiguous_matches": str(ambiguous),
        "join_confidence": confidence,
        "repair_needed": "yes" if confidence in {"low", "medium"} or duplicates or ambiguous else "no",
        "notes": notes,
    }


def feature_family_matrix() -> list[dict[str, str]]:
    rows = [
        ("draft_capital_round_pick", "cross_position", "available_now", "2010-2023;2026", "QB|RB|WR|TE", "high", "medium", "use_now", "round/pick only; career columns quarantined"),
        ("age_at_draft", "cross_position", "available_now", "2010-2023 via nflverse age; 2026 partial", "QB|RB|WR|TE", "medium", "medium", "backfill_candidate", "age available in draft source for historical; DOB/early declare richer file still useful"),
        ("college_production_basic", "cross_position", "available_with_join_repair", "2021-2023;2026", "QB|RB|WR|TE", "high", "medium", "backfill_candidate", "RotoWire CFB stats cover seasons 2020-2025; not enough for 2010-2019"),
        ("college_target_earning", "WR_TE_RB", "available_with_join_repair", "2021-2023;2026", "RB|WR|TE", "high", "medium", "backfill_candidate", "RotoWire targets cover 2020-2025; highest-value WR feature family found"),
        ("college_team_context_market_share_denominators", "cross_position", "available_with_join_repair", "2021-2023;2026", "QB|RB|WR|TE", "high", "medium", "backfill_candidate", "team stats can support shares if team names normalize cleanly"),
        ("combine_athletic_testing", "cross_position", "available_with_join_repair", "2010-2023;2026", "QB|RB|WR|TE", "medium", "medium", "backfill_candidate", "combine/pro-day source has broad year coverage but source license status needs acceptance"),
        ("rotowire_workout_testing", "cross_position", "available_with_join_repair", "2016-2023;2026", "QB|RB|WR|TE", "medium", "medium", "backfill_candidate", "helpful current/historical workout supplement"),
        ("rookie_time_injury_flags", "cross_position", "available_now", "2026 only", "QB|RB|WR|TE", "medium", "high", "backfill_candidate", "current CFB injury report is useful for 2026; historical equivalent missing"),
        ("landing_spot_opportunity", "cross_position", "available_now", "2026 current matrix only", "QB|RB|WR|TE", "medium", "medium", "needs_tim_file", "current depth chart context exists; historical time-safe landing spot context not found"),
        ("historical_adp_market", "cross_position", "not_found", "", "QB|RB|WR|TE", "display_only", "display_only", "needs_tim_file", "ADP/market allowed only as display overlay"),
        ("route_yprr_advanced_charting", "WR_TE", "not_found", "", "WR|TE", "high", "medium", "needs_tim_file", "likely strongest missing WR star-capture feature family"),
        ("pre_draft_injury_history_historical", "cross_position", "not_found", "", "QB|RB|WR|TE", "medium", "high", "needs_tim_file", "highest-value missing bust-avoidance feature family"),
    ]
    return [
        {
            "feature_family": item[0],
            "scope": item[1],
            "availability_status": item[2],
            "year_coverage": item[3],
            "position_coverage": item[4],
            "star_capture_usefulness": item[5],
            "bust_avoidance_usefulness": item[6],
            "recommended_next_action": item[7],
            "notes": item[8],
        }
        for item in rows
    ]


def missing_data_requests() -> list[dict[str, str]]:
    rows = [
        ("1", "college_player_season_stats_2010_2026.csv", "fills 2010-2019 college production gap and improves WR/RB/TE/QB feature depth", "2010-2026", "CSV one row per player-season", "season, player_name, school, position, games, pass/rush/receiving stats, targets if available", "pre-draft seasons only; no NFL outcomes"),
        ("1", "historical_targets_market_share_2010_2026.csv", "highest likely WR star-capture improvement", "2010-2026", "CSV one row per player-season", "season, player_name, school, position, targets, receptions, receiving_yards, team_targets or target_share", "do not include rankings/projections"),
        ("1", "rookie_age_early_declare_2010_2026.csv", "age-adjusted production and early declare status", "2010-2026", "CSV one row per player", "player_name, school, position, draft_year, DOB or age_at_draft, college_class, early_declare", "identity fields not scoring boosts by themselves"),
        ("1", "pre_draft_injury_flags_2010_2026.csv", "best missing bust-avoidance input", "2010-2026", "CSV one row per injury/event", "player_name, school, position, draft_year, injury_type, date/season, severity, known_pre_draft", "must be known before rookie draft"),
        ("2", "combine_athletic_testing_2010_2026.csv", "improves archetype and athletic context if Tim has cleaner licensed source", "2010-2026", "CSV one row per player", "draft_year, player_name, school, position, height, weight, forty, vertical, broad, three_cone, shuttle, bench", "avoid prospect grades/projections as private score"),
        ("2", "historical_rookie_adp_display_only_2010_2026.csv", "helps value overlay and trade-down language", "2010-2026", "CSV one row per player/source/date", "draft_year, player_name, position, rookie_adp, source, timestamp", "display-only; never private quality score"),
        ("3", "historical_factual_scouting_notes.csv", "can support warning flags if structured carefully", "2010-2026", "CSV fact rows", "draft_year, player_name, position, source, fact_type, fact_text, known_pre_draft", "no rankings, comps, projections, or hindsight blurbs as score inputs"),
    ]
    return [
        {
            "priority": item[0],
            "requested_file_type": item[1],
            "why_it_helps": item[2],
            "required_years": item[3],
            "ideal_format": item[4],
            "required_columns": item[5],
            "leakage_warning": item[6],
            "proprietary_note": "paid/proprietary is okay only if Tim already has the right to use it locally",
        }
        for item in rows
    ]


def backfill_plan() -> list[dict[str, str]]:
    rows = [
        ("1", "Backfill draft age and draft capital", "nflverse_draft_picks", "GREEN", "high", "round/pick/age only; quarantine career columns"),
        ("2", "Backfill 2021-2023 + 2026 CFB production/targets/team context", "rotowire_cfb_stats_all; rotowire_cfb_targets_all; rotowire_cfb_advanced_team_stats_all", "YELLOW", "medium", "requires final college season join QA and 2010-2019 gap acknowledgement"),
        ("3", "Backfill combine/workout athletic testing", "combine_skill_positions_all; rotowire_workout_stats", "YELLOW", "medium", "requires source/license acceptance and name-position-year join repair"),
        ("4", "Backfill 2026 current injury flags", "rotowire_cfb_injury_report_2026", "GREEN", "medium", "current only; do not treat missing historical injuries as no-risk"),
        ("5", "Do not tune richer model until feature backfill is validated", "all", "YELLOW", "n/a", "another tuning pass is premature without feature matrix update"),
    ]
    return [
        {
            "step": item[0],
            "backfill_action": item[1],
            "source_ids": item[2],
            "leakage_gate": item[3],
            "join_readiness": item[4],
            "notes": item[5],
        }
        for item in rows
    ]


def build_exports(labels_path: Path, current_features_path: Path, output_dir: Path) -> dict[str, int]:
    inventory = [inspect_source(candidate) for candidate in SOURCE_CANDIDATES]
    historical_rows = expanded_pool(labels_path)
    current_rows = current_pool(current_features_path)
    joins = []
    for candidate in SOURCE_CANDIDATES:
        joins.append(join_preview_for_source(candidate["source_id"], REPO_ROOT / candidate["path"], historical_rows, current_rows))
    columns = column_audit(inventory)
    matrix = feature_family_matrix()
    missing = missing_data_requests()
    plan = backfill_plan()

    write_csv(
        output_dir / "historical_feature_source_inventory_20260615.csv",
        inventory,
        [
            "source_id",
            "path",
            "exists",
            "row_count",
            "year_coverage",
            "position_coverage",
            "key_columns",
            "stable_ids_available",
            "likely_join_keys",
            "feature_family",
            "leakage_classification",
            "recommended_action",
            "notes",
        ],
    )
    write_csv(
        output_dir / "allowed_blocked_column_audit_20260615.csv",
        columns,
        ["source_id", "column_name", "column_classification", "reason", "private_score_allowed"],
    )
    write_csv(
        output_dir / "feature_join_feasibility_20260615.csv",
        joins,
        ["source_id", "join_method", "attempted_rows", "joined_rows", "unjoined_rows", "duplicate_keys", "ambiguous_matches", "join_confidence", "repair_needed", "notes"],
    )
    write_csv(
        output_dir / "feature_family_availability_matrix_20260615.csv",
        matrix,
        ["feature_family", "scope", "availability_status", "year_coverage", "position_coverage", "star_capture_usefulness", "bust_avoidance_usefulness", "recommended_next_action", "notes"],
    )
    write_csv(
        output_dir / "missing_data_request_for_tim_20260615.csv",
        missing,
        ["priority", "requested_file_type", "why_it_helps", "required_years", "ideal_format", "required_columns", "leakage_warning", "proprietary_note"],
    )
    write_csv(
        output_dir / "recommended_feature_backfill_plan_20260615.csv",
        plan,
        ["step", "backfill_action", "source_ids", "leakage_gate", "join_readiness", "notes"],
    )
    (output_dir / "README_ROOKIE_HISTORICAL_FEATURE_FAMILY_AVAILABILITY_AUDIT_20260615.md").write_text(
        "# Rookie Historical Feature-Family Availability Audit\n\n"
        "Local-only source inventory and join-feasibility exports. No tuning, v2 board, app wiring, probabilities, "
        "bands, hidden sort keys, production promotion, or committed local exports.\n",
        encoding="utf-8",
    )
    return {
        "source_inventory_rows": len(inventory),
        "column_audit_rows": len(columns),
        "join_rows": len(joins),
        "feature_family_rows": len(matrix),
        "missing_request_rows": len(missing),
        "backfill_plan_rows": len(plan),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--current-features", type=Path, default=DEFAULT_CURRENT_FEATURES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build_exports(args.labels, args.current_features, args.output_dir)
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
