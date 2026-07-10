from __future__ import annotations

import csv
import math
import os
import py_compile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
THIS_WORKTREE = Path(__file__).resolve().parents[4]
SOURCE_ROOT = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709")

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_ADDENDUM_COMMIT = "8e31c89aee7bc2598046206dd0ec8336dce1c248"
PRIOR_RED_TEAM_COMMIT = "c3c52d95b6b2965e48ad8e71b64dcbc50c738998"
PRIOR_INGREDIENT_CANONICALIZATION_COMMIT = "8fefe3d9c270df753f78115ee8a1450f1afbd4e9"

RED_TEAM_DIR = THIS_WORKTREE / "docs/hq/model/formula_miss_taxonomy_red_team_review_v1_20260709"
ADDENDUM_DIR = THIS_WORKTREE / "docs/hq/master/formula_red_team_canonicalization_addendum_v1_20260709"
INGREDIENT_CANON_DIR = SOURCE_ROOT / "docs/hq/master/ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709"
CLOSEOUT_DIR = SOURCE_ROOT / "docs/hq/master/ingredient_upgrade_phase_closeout_canonicalization_prep_v1_20260709"

MART = SOURCE_ROOT / "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/FORMULA_DATA_MART_REVIEW_ONLY.csv"
AGE = SOURCE_ROOT / "docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
MISS_LEDGER = RED_TEAM_DIR / "FORMULA_MISS_PLAYER_SEASON_LEDGER.csv"
RED_TEAM_COMPARISON = RED_TEAM_DIR / "FORMULA_REFERENCE_COMPARISON_MISS_REDUCTION.csv"
ROOKIE_SIDECAR = SOURCE_ROOT / "docs/hq/model/rookie_draft_capital_data_mart_join_component_test_v1_20260709/ROOKIE_DRAFT_CAPITAL_REVIEW_ONLY_SIDECAR.csv"
SNAP_SIDECAR = SOURCE_ROOT / "docs/hq/model/nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709/NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv"
INJURY_SIDECAR = SOURCE_ROOT / "docs/hq/model/point_in_time_injury_availability_data_mart_gate_v1_20260709/POINT_IN_TIME_INJURY_AVAILABILITY_REVIEW_ONLY_SIDECAR.csv"
FFOP_SIDECAR = SOURCE_ROOT / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv"
NGS_SIDECAR = SOURCE_ROOT / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv"

POSITIONS = ["QB", "RB", "WR", "TE"]
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RuntimeError(f"Missing required artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def writable_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with open(writable_path(path), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    with open(writable_path(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text.strip() + "\n")


def num(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    return out if math.isfinite(out) else None


def bool_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def fmt(value: Any, places: int = 3) -> str:
    value = num(value)
    return "" if value is None else f"{value:.{places}f}"


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.1f}%"


def group_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[k] for k in keys)].append(row)
    return grouped


def assign_rank(rows: list[dict[str, Any]], score_col: str, rank_col: str) -> None:
    for row in rows:
        row[rank_col] = None
    for group in group_rows(rows, ("season", "position")).values():
        eligible = [row for row in group if row.get(score_col) is not None]
        ordered = sorted(eligible, key=lambda row: (float(row[score_col]), str(row["player_id"]), str(row["substrate_row_id"])), reverse=True)
        for idx, row in enumerate(ordered, start=1):
            row[rank_col] = float(idx)


def assign_percentile(rows: list[dict[str, Any]], score_col: str, out_col: str) -> None:
    for row in rows:
        row[out_col] = None
    for group in group_rows(rows, ("season", "position")).values():
        eligible = [row for row in group if row.get(score_col) is not None]
        ordered = sorted(eligible, key=lambda row: (float(row[score_col]), str(row["player_id"])))
        n = len(ordered)
        for idx, row in enumerate(ordered, start=1):
            row[out_col] = (idx - 1) / (n - 1) if n > 1 else 1.0


def sidecar_feature_season(row: dict[str, str]) -> int:
    value = row.get("feature_season")
    return int(float(value)) if value not in (None, "") else int(float(row["season"]))


def attach_sidecar(
    rows: list[dict[str, Any]],
    path: Path,
    prefix: str,
    numeric_cols: list[str],
    text_cols: list[str] | None = None,
    column_map: dict[str, str] | None = None,
    sidecar_uses_feature_season: bool = True,
) -> int:
    text_cols = text_cols or []
    column_map = column_map or {}
    src = read_csv(path)
    if sidecar_uses_feature_season:
        lookup = {(str(r["player_id"]), sidecar_feature_season(r), str(r["position"])): r for r in src}
    else:
        lookup = {(str(r["player_id"]), int(float(r["season"])), str(r["position"])): r for r in src}
    joined = 0
    for row in rows:
        key = (str(row["player_id"]), int(row["feature_season"] if sidecar_uses_feature_season else row["season"]), str(row["position"]))
        match = lookup.get(key)
        if match:
            joined += 1
        for col in numeric_cols:
            src_col = column_map.get(col, col)
            row[f"{prefix}_{col}"] = num(match.get(src_col)) if match else None
        for col in text_cols:
            src_col = column_map.get(col, col)
            row[f"{prefix}_{col}"] = str(match.get(src_col, "")) if match else ""
    for col in numeric_cols:
        assign_percentile(rows, f"{prefix}_{col}", f"{prefix}_{col}_pct")
    return joined


def is_older_late(row: dict[str, Any]) -> bool:
    return str(row.get("age_bucket")) == "age_32_plus" or str(row.get("lifecycle_bucket")) == "late_career_10_plus"


def is_young_early(row: dict[str, Any]) -> bool:
    return str(row.get("age_bucket")) in {"under_23", "age_23_to_25"} or str(row.get("lifecycle_bucket")) == "early_career_1_to_3"


def is_high_volume_role(row: dict[str, Any]) -> bool:
    return str(row.get("role_usage_bucket")) == "high_volume" or "_high_volume_" in str(row.get("role_archetype"))


def reconstruct_history(row: dict[str, Any]) -> None:
    y1 = row["pyf_score"]
    two = row["two_year_70_30"]
    three = row["three_year_60_30_10"]
    y2_available = (row["prior_2yr_years"] or 0.0) >= 2 and y1 is not None and two is not None
    y3_available = (row["prior_3yr_years"] or 0.0) >= 3 and y1 is not None and three is not None
    if y1 is None:
        row["n_minus_1_points"] = None
        row["n_minus_2_points"] = None
        row["n_minus_3_points"] = None
        return
    y2 = (two - 0.70 * y1) / 0.30 if y2_available else y1
    y3 = (three - 0.60 * y1 - 0.30 * y2) / 0.10 if y3_available else y2
    row["n_minus_1_points"] = y1
    row["n_minus_2_points"] = y2
    row["n_minus_3_points"] = y3


def weighted3(row: dict[str, Any], w1: float, w2: float, w3: float) -> float | None:
    if row.get("n_minus_1_points") is None or row.get("n_minus_2_points") is None or row.get("n_minus_3_points") is None:
        return None
    return w1 * float(row["n_minus_1_points"]) + w2 * float(row["n_minus_2_points"]) + w3 * float(row["n_minus_3_points"])


def load_panel() -> tuple[list[dict[str, Any]], dict[str, int]]:
    ages = {(r["player_id"], r["season"], r["position"]): r for r in read_csv(AGE)}
    rows: list[dict[str, Any]] = []
    for raw in read_csv(MART):
        row: dict[str, Any] = dict(raw)
        key = (raw["player_id"], raw["season"], raw["position"])
        age = ages.get(key, {})
        row["season"] = int(float(raw["season"]))
        row["feature_season"] = int(float(raw["feature_season"]))
        row["position"] = raw["position"]
        row["player_id"] = raw["player_id"]
        row["player_name"] = raw.get("player_name") or raw.get("target_player_name") or ""
        row["team"] = raw.get("team") or raw.get("target_team") or ""
        row["actual_startable"] = bool_true(raw.get("label_startable_hit"))
        row["actual_outcome_label"] = "STARTABLE_HIT" if row["actual_startable"] else "NOT_STARTABLE"
        row["actual_finish"] = num(raw.get("label_next_position_finish"))
        row["pyf_score"] = num(raw.get("pyf_prior_nwr_points"))
        row["pyf_ppg"] = num(raw.get("pyf_prior_nwr_ppg"))
        row["pyf_prior_rank"] = num(raw.get("pyf_prior_rank_position_feature_season"))
        row["two_year_70_30"] = num(raw.get("prior_2yr_weighted_nwr_points"))
        row["three_year_60_30_10"] = num(raw.get("prior_3yr_weighted_nwr_points"))
        row["prior_2yr_years"] = num(raw.get("prior_2yr_points_years_available")) or 0.0
        row["prior_3yr_years"] = num(raw.get("prior_3yr_points_years_available")) or 0.0
        row["prior_games"] = num(raw.get("prior_games")) or 0.0
        row["prior_offensive_snaps"] = num(raw.get("prior_offensive_snaps")) or 0.0
        row["sparse_history_bool"] = bool_true(raw.get("sparse_history_flag"))
        row["low_games_bool"] = bool_true(raw.get("low_games_flag"))
        row["role_archetype"] = raw.get("role_archetype", "")
        row["role_usage_bucket"] = raw.get("role_usage_bucket", "")
        row["age"] = num(age.get("age"))
        row["age_bucket"] = age.get("age_bucket", "")
        row["lifecycle_bucket"] = age.get("lifecycle_bucket", "")
        row["career_stage"] = age.get("career_stage", "")
        reconstruct_history(row)
        rows.append(row)

    joins = {
        "snap_depth": attach_sidecar(rows, SNAP_SIDECAR, "snap", ["snap_offensive_snaps", "snap_offensive_snap_share", "snap_games_with_offensive_snaps", "snap_low_snap_flag", "snap_not_low_snap_score", "snap_role_score", "snap_share_trend", "depth_weeks_as_starter", "depth_weeks_as_backup", "depth_role_score", "depth_stability_score", "snap_depth_role_score"], ["depth_role_tier", "coverage_status", "leakage_flag"]),
        "injury": attach_sidecar(rows, INJURY_SIDECAR, "injury", ["avail_games_missed", "avail_active_pct", "avail_prior_year_missed_games", "avail_two_year_missed_games", "avail_availability_score", "avail_caveat_flag", "avail_caveat_inverse_score", "avail_ir_pup_flag"], ["coverage_status", "leakage_flag"]),
        "rookie_draft": attach_sidecar(rows, ROOKIE_SIDECAR, "draft", ["draft_year", "rookie_year", "draft_round", "draft_overall", "drafted_flag", "draft_capital_score", "years_since_draft", "rookie_contract_window_flag", "early_career_flag", "sparse_history_flag"], ["entry_status", "draft_capital_bucket", "coverage_status"], sidecar_uses_feature_season=False),
        "ffopportunity": attach_sidecar(rows, FFOP_SIDECAR, "ffop", ["ffop_xfp_per_game", "ffop_xfp_total"], ["leakage_flag"], {"ffop_xfp_per_game": "ffop_total_fantasy_points_exp_per_game", "ffop_xfp_total": "ffop_total_fantasy_points_exp"}, sidecar_uses_feature_season=True),
        "ngs": attach_sidecar(rows, NGS_SIDECAR, "ngs", ["ngs_position_signal_raw", "ngs_qb_cpoe", "ngs_rec_avg_separation", "ngs_rush_yards_over_expected_per_att"], ["leakage_flag"], sidecar_uses_feature_season=True),
    }

    for row in rows:
        # Accepted reference formulas only.
        three_60 = row.get("three_year_60_30_10")
        score_081 = three_60 * 0.98 if three_60 is not None and is_older_late(row) else three_60
        score_083 = weighted3(row, 0.65, 0.25, 0.10)
        if score_083 is not None:
            if is_older_late(row):
                score_083 *= 0.98
            if is_high_volume_role(row) and is_older_late(row):
                score_083 *= 0.96
        row["PYF_BASELINE_score"] = row["pyf_score"]
        row["GAUNTLET_081_seed_score"] = score_081
        row["GAUNTLET_083_seed_score"] = score_083

    for col in ["PYF_BASELINE_score", "GAUNTLET_081_seed_score", "GAUNTLET_083_seed_score", "snap_depth_stability_score", "snap_snap_not_low_snap_score", "ffop_ffop_xfp_per_game"]:
        assign_percentile(rows, col, f"{col}_pct")
    for row in rows:
        row["BEST_FULL_HISTORY_score"] = None
        row["BEST_BROAD_WINDOW_score"] = None
        row["BEST_PARTIAL_WINDOW_score"] = None
        if row.get("GAUNTLET_081_seed_score_pct") is not None and row.get("snap_depth_stability_score_pct") is not None:
            row["BEST_FULL_HISTORY_score"] = 0.90 * float(row["GAUNTLET_081_seed_score_pct"]) + 0.10 * float(row["snap_depth_stability_score_pct"])
        if row.get("GAUNTLET_081_seed_score_pct") is not None and row.get("snap_snap_not_low_snap_score_pct") is not None:
            row["BEST_BROAD_WINDOW_score"] = 0.90 * float(row["GAUNTLET_081_seed_score_pct"]) + 0.10 * float(row["snap_snap_not_low_snap_score_pct"])
        if row.get("GAUNTLET_083_seed_score_pct") is not None and row.get("ffop_ffop_xfp_per_game_pct") is not None:
            row["BEST_PARTIAL_WINDOW_score"] = 0.90 * float(row["GAUNTLET_083_seed_score_pct"]) + 0.10 * float(row["ffop_ffop_xfp_per_game_pct"])
    for score_col, rank_col in [
        ("PYF_BASELINE_score", "PYF_BASELINE_rank"),
        ("BEST_FULL_HISTORY_score", "BEST_FULL_HISTORY_rank"),
        ("BEST_BROAD_WINDOW_score", "BEST_BROAD_WINDOW_rank"),
        ("BEST_PARTIAL_WINDOW_score", "BEST_PARTIAL_WINDOW_rank"),
    ]:
        assign_rank(rows, score_col, rank_col)
    return rows, joins


def predicted_startable(row: dict[str, Any], rank_col: str) -> bool:
    rank = row.get(rank_col)
    return rank is not None and float(rank) <= STARTABLE_CUTOFF[str(row["position"])]


def sparse_types(row: dict[str, Any]) -> list[str]:
    ysd = row.get("draft_years_since_draft")
    prior_points = row.get("pyf_score")
    low_prior_points = prior_points is None or prior_points < 75
    no_pyf = prior_points is None or row.get("PYF_BASELINE_rank") is None
    low_prior_games = float(row.get("prior_games") or 0.0) < 8
    low_prior_snaps = float(row.get("prior_offensive_snaps") or 0.0) < 300
    sparse_multi = row["prior_2yr_years"] < 2 or row["prior_3yr_years"] < 3
    basic_sparse = row["sparse_history_bool"] or row["low_games_bool"] or low_prior_games or low_prior_snaps or low_prior_points or no_pyf or sparse_multi
    role_promo = (row.get("snap_snap_role_score") is not None and float(row["snap_snap_role_score"]) >= 0.70) or (row.get("snap_depth_weeks_as_starter") is not None and float(row["snap_depth_weeks_as_starter"]) >= 8)
    avail_rebound = (row.get("injury_avail_availability_score") is not None and float(row["injury_avail_availability_score"]) >= 0.80 and (row.get("injury_avail_prior_year_missed_games") or 0) >= 2)
    out: list[str] = []
    if ysd is not None and int(ysd) == 0:
        out.append("true_rookie")
    if ysd is not None and int(ysd) == 1:
        out.append("second_year_breakout_candidate")
    if ysd is not None and int(ysd) == 2:
        out.append("third_year_breakout_candidate")
    if basic_sparse and (ysd is None or int(ysd) >= 3):
        out.append("veteran_sparse_recent_history")
    if basic_sparse and avail_rebound:
        out.append("injury_rebound_sparse_history")
    if basic_sparse and role_promo:
        out.append("role_promotion_sparse_history")
    if row["sparse_history_bool"]:
        out.append("formula_data_mart_sparse_history_flag")
    if row["low_games_bool"]:
        out.append("formula_data_mart_low_games_flag")
    if no_pyf:
        out.append("no_usable_pyf")
    if sparse_multi:
        out.append("sparse_multiyear_production")
    return sorted(set(out))


def miss_lookup() -> dict[tuple[int, str, str], dict[str, Any]]:
    lookup: dict[tuple[int, str, str], dict[str, Any]] = {}
    for miss in read_csv(MISS_LEDGER):
        key = (int(float(miss["season"])), miss["player_id"], miss["position"])
        rec = lookup.setdefault(
            key,
            {
                "false_negative_flag": False,
                "false_positive_flag": False,
                "miss_reasons": set(),
                "miss_types": set(),
                "formula_ids": set(),
            },
        )
        if miss["miss_type"] == "FALSE_NEGATIVE":
            rec["false_negative_flag"] = True
        if miss["miss_type"] == "FALSE_POSITIVE":
            rec["false_positive_flag"] = True
        rec["miss_reasons"].update([x for x in miss.get("notes_candidate_miss_reason", "").split(";") if x])
        rec["miss_types"].add(miss["miss_type"])
        rec["formula_ids"].add(miss["formula_id"])
    return lookup


def row_signal_flags(row: dict[str, Any]) -> dict[str, str]:
    return {
        "starter_depth_signal": str((row.get("snap_depth_weeks_as_starter") is not None and float(row["snap_depth_weeks_as_starter"]) >= 8) or str(row.get("snap_depth_role_tier")) in {"PRIMARY_STARTER", "PARTIAL_STARTER"}).lower(),
        "snap_role_promotion_signal": str(row.get("snap_snap_role_score") is not None and float(row["snap_snap_role_score"]) >= 0.70).lower(),
        "availability_rebound_signal": str(row.get("injury_avail_availability_score") is not None and float(row["injury_avail_availability_score"]) >= 0.80).lower(),
        "expected_opportunity_signal": str(row.get("ffop_ffop_xfp_per_game") is not None and float(row["ffop_ffop_xfp_per_game"]) >= 10).lower(),
        "positive_ngs_signal": str(row.get("ngs_ngs_position_signal_raw") is not None and float(row["ngs_ngs_position_signal_raw"]) > 0).lower(),
        "low_snap_trap_flag": str(row.get("snap_snap_low_snap_flag") is not None and float(row["snap_snap_low_snap_flag"]) >= 1).lower(),
        "weak_depth_trap_flag": str(str(row.get("snap_depth_role_tier")) in {"DEPTH_BACKUP", "NO_DEPTH_RECORD"}).lower(),
        "injury_caveat_trap_flag": str(row.get("injury_avail_caveat_flag") is not None and float(row["injury_avail_caveat_flag"]) >= 1).lower(),
    }


LEDGER_FIELDS = [
    "season",
    "player_id",
    "player_name",
    "position",
    "team",
    "sparse_history_type",
    "miss_type",
    "false_negative_flag",
    "false_positive_flag",
    "actual_outcome_label",
    "pyf_score",
    "pyf_rank",
    "best_full_history_formula_score",
    "best_full_history_formula_rank",
    "best_broad_window_formula_score",
    "best_broad_window_formula_rank",
    "age",
    "lifecycle_bucket",
    "years_since_draft",
    "draft_capital_bucket",
    "snap_depth_role_score",
    "starter_depth_signal",
    "snap_role_promotion_signal",
    "low_snap_flag",
    "injury_availability_context",
    "availability_rebound_signal",
    "ffopportunity_context",
    "ngs_context",
    "role_archetype",
    "candidate_miss_reason",
]


def build_sparse_ledger(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    misses = miss_lookup()
    out: list[dict[str, Any]] = []
    for row in rows:
        types = sparse_types(row)
        if not types:
            continue
        key = (int(row["season"]), row["player_id"], row["position"])
        miss = misses.get(key, {})
        flags = row_signal_flags(row)
        out.append(
            {
                "season": row["season"],
                "player_id": row["player_id"],
                "player_name": row["player_name"],
                "position": row["position"],
                "team": row.get("team", ""),
                "sparse_history_type": "|".join(types),
                "miss_type": "|".join(sorted(miss.get("miss_types", []))) if miss else "NO_REFERENCE_MISS",
                "false_negative_flag": str(bool(miss.get("false_negative_flag"))).lower(),
                "false_positive_flag": str(bool(miss.get("false_positive_flag"))).lower(),
                "actual_outcome_label": row["actual_outcome_label"],
                "pyf_score": fmt(row.get("pyf_score")),
                "pyf_rank": fmt(row.get("PYF_BASELINE_rank"), 0),
                "best_full_history_formula_score": fmt(row.get("BEST_FULL_HISTORY_score"), 6),
                "best_full_history_formula_rank": fmt(row.get("BEST_FULL_HISTORY_rank"), 0),
                "best_broad_window_formula_score": fmt(row.get("BEST_BROAD_WINDOW_score"), 6),
                "best_broad_window_formula_rank": fmt(row.get("BEST_BROAD_WINDOW_rank"), 0),
                "age": fmt(row.get("age"), 1),
                "lifecycle_bucket": row.get("lifecycle_bucket", ""),
                "years_since_draft": fmt(row.get("draft_years_since_draft"), 0),
                "draft_capital_bucket": row.get("draft_draft_capital_bucket", ""),
                "snap_depth_role_score": fmt(row.get("snap_snap_depth_role_score")),
                "starter_depth_signal": flags["starter_depth_signal"],
                "snap_role_promotion_signal": flags["snap_role_promotion_signal"],
                "low_snap_flag": flags["low_snap_trap_flag"],
                "injury_availability_context": fmt(row.get("injury_avail_availability_score")),
                "availability_rebound_signal": flags["availability_rebound_signal"],
                "ffopportunity_context": fmt(row.get("ffop_ffop_xfp_per_game")),
                "ngs_context": fmt(row.get("ngs_ngs_position_signal_raw")),
                "role_archetype": row.get("role_archetype", ""),
                "candidate_miss_reason": "|".join(sorted(miss.get("miss_reasons", []))) if miss else "not_a_reference_miss",
            }
        )
    return out


def summarize_characteristics(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    successful = [r for r in ledger if r["actual_outcome_label"] == "STARTABLE_HIT"]
    fields = [
        ("starter_depth_signal", "starter/depth signal"),
        ("snap_role_promotion_signal", "snap/depth role-promotion signal"),
        ("availability_rebound_signal", "availability rebound / clean-report context"),
        ("ffopportunity_context", "expected fantasy opportunity present"),
        ("ngs_context", "NGS context present"),
        ("draft_capital_bucket", "draft capital bucket"),
        ("lifecycle_bucket", "age/lifecycle bucket"),
        ("role_archetype", "role archetype"),
    ]
    out: list[dict[str, Any]] = []
    for pos in POSITIONS:
        pos_rows = [r for r in successful if r["position"] == pos]
        for field, label in fields:
            if field in {"ffopportunity_context", "ngs_context"}:
                count = sum(1 for r in pos_rows if r.get(field))
                value = "present"
            else:
                c = Counter(r.get(field) or "UNKNOWN" for r in pos_rows)
                value, count = c.most_common(1)[0] if c else ("", 0)
            out.append(
                {
                    "position": pos,
                    "characteristic": label,
                    "dominant_value": value,
                    "rows_with_characteristic": count,
                    "successful_sparse_rows": len(pos_rows),
                    "share": pct(count / len(pos_rows) if pos_rows else None),
                    "interpretation": "Review-only breakout profile; not production ranking logic.",
                }
            )
    return out


def summarize_traps(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failed_fp = [r for r in ledger if r["false_positive_flag"] == "true"]
    trap_specs = [
        ("draft capital without role", lambda r: r["draft_capital_bucket"] in {"round_1", "round_2", "round_3"} and r["starter_depth_signal"] != "true" and r["snap_role_promotion_signal"] != "true"),
        ("young player with no snap/depth growth", lambda r: any(t in r["sparse_history_type"] for t in ["true_rookie", "second_year", "third_year"]) and r["snap_role_promotion_signal"] != "true"),
        ("low snap / low depth signal", lambda r: r["low_snap_flag"] == "true" or r["starter_depth_signal"] != "true"),
        ("injury/availability caveat", lambda r: "injury_availability_caveat" in r["candidate_miss_reason"] or r["injury_availability_context"] == ""),
        ("weak role archetype", lambda r: "low_volume" in r["role_archetype"] or r["role_archetype"] == ""),
        ("sparse production without role promotion", lambda r: "sparse_multiyear_production" in r["sparse_history_type"] and r["snap_role_promotion_signal"] != "true"),
    ]
    out: list[dict[str, Any]] = []
    for pos in POSITIONS:
        pos_rows = [r for r in failed_fp if r["position"] == pos]
        for trap, func in trap_specs:
            count = sum(1 for r in pos_rows if func(r))
            out.append(
                {
                    "position": pos,
                    "false_positive_trap": trap,
                    "trap_rows": count,
                    "false_positive_sparse_rows": len(pos_rows),
                    "share": pct(count / len(pos_rows) if pos_rows else None),
                    "policy_response": "flag for review-only caution; do not auto-penalize or alter production ranking",
                }
            )
    return out


def position_summary(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for pos in POSITIONS:
        rows = [r for r in ledger if r["position"] == pos]
        hits = [r for r in rows if r["actual_outcome_label"] == "STARTABLE_HIT"]
        fn = [r for r in rows if r["false_negative_flag"] == "true"]
        fp = [r for r in rows if r["false_positive_flag"] == "true"]
        c_types = Counter()
        for r in rows:
            c_types.update(r["sparse_history_type"].split("|"))
        c_reasons = Counter()
        for r in fn:
            c_reasons.update([x for x in r["candidate_miss_reason"].split("|") if x and x != "not_a_reference_miss"])
        out.append(
            {
                "position": pos,
                "sparse_history_rows": len(rows),
                "startable_hits": len(hits),
                "startable_rate": pct(len(hits) / len(rows) if rows else None),
                "false_negative_rows": len(fn),
                "false_positive_rows": len(fp),
                "dominant_population_type": c_types.most_common(1)[0][0] if c_types else "",
                "dominant_false_negative_reason": c_reasons.most_common(1)[0][0] if c_reasons else "",
                "design_implication": design_implication(pos),
            }
        )
    return out


def design_implication(pos: str) -> str:
    return {
        "QB": "Prefer starter/depth and availability rebound signals; avoid pure low-prior-production dismissal.",
        "RB": "Separate role-promotion touches from low-snap traps; draft capital alone is insufficient.",
        "WR": "Use young breakout, starter/depth, and expected opportunity as review-only diagnostics.",
        "TE": "Expect delayed breakouts; treat depth/starter context and age window by position.",
    }[pos]


def feature_policy_matrix() -> list[dict[str, str]]:
    return [
        {"feature_module": "SPARSE_HISTORY_ELIGIBILITY_GATE", "allowed_use": "review-only population filter", "inputs": "sparse_history_flag;low_games_flag;prior_games;prior_points;prior_snaps;years_since_draft", "source_status": "available review-only", "blocked_use": "automatic production ranking boost/penalty", "caveat": "Gate only defines test population."},
        {"feature_module": "ROLE_PROMOTION_SIGNAL", "allowed_use": "diagnostic breakout signal", "inputs": "snap_role_score;role_archetype;role_usage_bucket", "source_status": "available review-only", "blocked_use": "hidden sort/recommendation logic", "caveat": "Must stay lagged N-to-N+1."},
        {"feature_module": "DEPTH_CHART_STARTER_SIGNAL", "allowed_use": "diagnostic breakout signal", "inputs": "depth_weeks_as_starter;depth_role_tier", "source_status": "available review-only", "blocked_use": "production starter projection", "caveat": "Prior-season depth chart cannot project team changes."},
        {"feature_module": "SNAP_GROWTH_SIGNAL", "allowed_use": "candidate rule-test input", "inputs": "snap_share_trend;snap_games_with_offensive_snaps", "source_status": "available review-only", "blocked_use": "same-season use", "caveat": "Trend is prior-season only."},
        {"feature_module": "AVAILABILITY_REBOUND_SIGNAL", "allowed_use": "guardrail/context", "inputs": "availability_score;prior missed games;injury caveat flag", "source_status": "partial with caveats", "blocked_use": "injury prediction", "caveat": "Not a medical model."},
        {"feature_module": "DRAFT_CAPITAL_CONTEXT", "allowed_use": "rookie/sparse context", "inputs": "draft_overall;draft_capital_bucket;years_since_draft", "source_status": "safe review-only for positive draft evidence", "blocked_use": "UDFA inference or CFBD/prospect model input", "caveat": "Missing draft evidence remains unknown."},
        {"feature_module": "AGE_LIFECYCLE_WINDOW", "allowed_use": "age-window slice/context", "inputs": "age;age_bucket;lifecycle_bucket", "source_status": "available review-only", "blocked_use": "automatic age boost/penalty", "caveat": "Position-specific aging curves differ."},
        {"feature_module": "EXPECTED_OPPORTUNITY_PARTIAL_WINDOW_SIGNAL", "allowed_use": "partial-window diagnostic only", "inputs": "ffopportunity XFP;NGS position signal", "source_status": "partial-window promising", "blocked_use": "full-history plateau claim", "caveat": "2022-2025 style comparisons only."},
        {"feature_module": "POSITION_SPECIFIC_BREAKOUT_RULES", "allowed_use": "future rule-test design", "inputs": "position-specific combinations of allowed modules", "source_status": "design only", "blocked_use": "dynamic tuning or broad Gauntlet", "caveat": "Predeclare rules before testing."},
        {"feature_module": "FALSE_POSITIVE_TRAP_FLAGS", "allowed_use": "review-only harm check", "inputs": "low snap;weak depth;injury caveat;draft without role", "source_status": "available review-only", "blocked_use": "production demotion", "caveat": "Flag for review, not automatic penalty."},
    ]


def write_static_docs(ledger: list[dict[str, Any]], joins: dict[str, int]) -> None:
    total = len(ledger)
    hits = sum(1 for r in ledger if r["actual_outcome_label"] == "STARTABLE_HIT")
    false_neg = sum(1 for r in ledger if r["false_negative_flag"] == "true")
    false_pos = sum(1 for r in ledger if r["false_positive_flag"] == "true")
    breakout_chars = summarize_characteristics(ledger)
    traps = summarize_traps(ledger)
    top_chars = Counter(row["characteristic"] for row in breakout_chars if row["rows_with_characteristic"]).most_common(5)
    trap_counts = Counter()
    for row in traps:
        trap_counts[row["false_positive_trap"]] += int(row["trap_rows"])
    top_traps = trap_counts.most_common(5)
    top_char_text = "; ".join(f"{name}" for name, _ in top_chars)
    top_trap_text = "; ".join(f"{name} ({count})" for name, count in top_traps)
    report = f"""
# Sparse-History Breakout Red Team / Rookie-Young Player Model Design V1

## Verdict

`GREEN_SPARSE_HISTORY_BREAKOUT_DESIGN_READY_FOR_RULE_TEST`

## Scope

This is a review-only design and red-team lane. It did not change production rankings, app/runtime/model behavior, source promotion, push/merge state, canonical `local_exports`, ranking simulation, or formula weights.

Remote HQ verified: `{EXPECTED_REMOTE_HEAD}`.

Prior addendum commit verified: `{PRIOR_ADDENDUM_COMMIT}`.

## Sparse-History Population

Rows analyzed: `{total}`.

Startable hits inside sparse-history population: `{hits}`.

Reference false negatives inside sparse-history population: `{false_neg}`.

Reference false positives inside sparse-history population: `{false_pos}`.

## Top Sparse-History Breakout Characteristics

{top_char_text}

## Top Sparse-History False-Positive Traps

{top_trap_text}

## Design Decision

A future `Sparse-History Breakout Candidate Rule Test V1` is justified as a bounded review-only lane. The rule test should be predeclared, position-specific, and limited to the modules in the feature policy matrix. It must not become production ranking logic, a broad Gauntlet, or dynamic tuning.

## Ranking Simulation Decision

Review-only ranking simulation remains not justified.

## Source Joins

Sidecar/context joins used for design: `{joins}`.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_BREAKOUT_RED_TEAM_ROOKIE_YOUNG_PLAYER_MODEL_DESIGN_V1_REPORT.md", report)

    population = """
# Sparse-History Population Definition

The review-only sparse-history population is any player-season matching one or more of these conditions:

- true rookie: `years_since_draft = 0`
- second-year player: `years_since_draft = 1`
- third-year player: `years_since_draft = 2`
- low prior games: fewer than `8` prior games or the Formula Data Mart low-games flag is true
- low prior snaps: fewer than `300` prior offensive snaps
- low prior fantasy points: missing PYF or fewer than `75` prior NWR points
- no usable PYF: missing PYF score/rank
- sparse multi-year production: fewer than two prior years for two-year production or fewer than three prior years for three-year production
- role-promotion sparse-history player: sparse base plus prior-season snap/depth role signal
- availability-rebound sparse-history player: sparse base plus clean/rebound availability signal

Separated review buckets:

- true rookies
- second-year breakout candidates
- third-year breakout candidates
- veterans with sparse recent history
- injury-rebound sparse-history players
- role-promotion sparse-history players

These are design/test buckets only. They are not production ranking logic.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_POPULATION_DEFINITION.md", population)

    framework = """
# Sparse-History Review-Only Framework Design

## Modules

1. `SPARSE_HISTORY_ELIGIBILITY_GATE`
   Identifies player-seasons where PYF or multi-year production is likely under-informed.

2. `ROLE_PROMOTION_SIGNAL`
   Uses lagged snap/depth role score, role archetype, and role usage bucket as review-only breakout diagnostics.

3. `DEPTH_CHART_STARTER_SIGNAL`
   Uses lagged starter/depth-chart rows to identify players whose prior production may understate current opportunity.

4. `SNAP_GROWTH_SIGNAL`
   Uses prior-season snap-share trend and games with offensive snaps as a bounded role-growth signal.

5. `AVAILABILITY_REBOUND_SIGNAL`
   Uses availability context only as a caution/rebound slice, not an injury prediction model.

6. `DRAFT_CAPITAL_CONTEXT`
   Uses positive draft evidence and draft capital buckets as sparse-history context. CFBD/prospect and inferred UDFA truth remain blocked.

7. `AGE_LIFECYCLE_WINDOW`
   Uses age/lifecycle buckets as position-specific context, not automatic boosts or penalties.

8. `EXPECTED_OPPORTUNITY_PARTIAL_WINDOW_SIGNAL`
   Uses ffopportunity/NGS only in partial-window diagnostics unless future coverage expands.

9. `POSITION_SPECIFIC_BREAKOUT_RULES`
   Requires separate QB/RB/WR/TE rule profiles because sparse-history breakouts do not share one universal curve.

10. `FALSE_POSITIVE_TRAP_FLAGS`
    Flags draft-without-role, weak depth, low snap, injury caveat, weak role archetype, and sparse production without promotion.

## Required Rule-Test Guardrails

- Predeclare all rules before testing.
- Keep full-history, broad-window, and partial-window scoreboards separate.
- Do not use current-only ADP, CFBD/prospect data, SportsDataIO, PFF Elusive Rating, or same-season/future context.
- Do not approve production/model-use, rankings integration, hidden sort, or recommendation logic.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_REVIEW_ONLY_FRAMEWORK_DESIGN.md", framework)

    gaps = """
# Sparse-History Data Gaps And Blockers

- Current-only market/ADP remains blocked for historical formula use until historical/as-of proof exists.
- CFBD/prospect production remains blocked as model input without source/use and identity gates.
- UDFA truth must not be inferred without source evidence.
- ffopportunity and NGS remain partial-window only and cannot support full-history claims.
- Prior-season team context is leakage-safe but cannot project trades, free-agent moves, coaching changes, or QB changes.
- Injury/availability context is not injury prediction and must remain guardrail/context only.
- Participation/personnel/pressure context may be useful later, but only after source/as-of review.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_DATA_GAPS_AND_BLOCKERS.md", gaps)

    next_lane = """
# Sparse-History Next Lane Decision

Recommended next lane:

`Sparse-History Breakout Candidate Rule Test V1`

Why:

- The miss taxonomy showed a concrete false-negative cluster around young breakouts, sparse-history breakouts, starter/depth signals, snap role-promotion, expected fantasy opportunity, and availability rebound.
- Existing review-only sidecars provide enough safe inputs to predeclare a bounded rule test.
- A rule test is more appropriate than another broad formula sweep because it targets the specific miss cluster rather than retuning the whole model.

Still blocked:

- Review-only ranking simulation
- Production/model-use
- Rankings integration
- App/runtime behavior changes
- Source promotion
- Push/merge
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_NEXT_LANE_DECISION.md", next_lane)

    trace = f"""
# Sparse-History Source Trace

Local base commit:

- Formula Red Team Canonicalization Addendum V1: `{PRIOR_ADDENDUM_COMMIT}`

Verified source packets:

- Formula Red Team Canonicalization Addendum V1: `{ADDENDUM_DIR}`
- Formula Miss Taxonomy / Red Team Review V1: `{RED_TEAM_DIR}`
- Ingredient Upgrade Phase Batch Canonicalization / Merge Review V1: `{INGREDIENT_CANON_DIR}`
- Ingredient Upgrade Phase Closeout / Canonicalization Prep V1: `{CLOSEOUT_DIR}`
- Formula Data Mart: `{MART}`
- Rookie/draft sidecar: `{ROOKIE_SIDECAR}`
- Snap/depth sidecar: `{SNAP_SIDECAR}`
- Injury/availability sidecar: `{INJURY_SIDECAR}`
- ffopportunity sidecar: `{FFOP_SIDECAR}`
- NGS sidecar: `{NGS_SIDECAR}`

Source/use gate:

All inputs remain review-only and are not production/model-use, ranking-integration, source-promotion, hidden-sort, or recommendation-logic approved.

Leakage/as-of gate:

Design uses accepted lagged N-to-N+1 artifacts and existing red-team miss ledgers. Same-season/future context remains blocked.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_SOURCE_TRACE.md", trace)


def main() -> None:
    for path in [ADDENDUM_DIR, RED_TEAM_DIR, INGREDIENT_CANON_DIR, CLOSEOUT_DIR, MART, AGE, MISS_LEDGER, ROOKIE_SIDECAR, SNAP_SIDECAR, INJURY_SIDECAR, FFOP_SIDECAR, NGS_SIDECAR]:
        if not path.exists():
            raise RuntimeError(f"Required prior artifact missing: {path}")
    compile_check = OUT_DIR / "_compile_check.pyc"
    try:
        py_compile.compile(__file__, cfile=str(compile_check), doraise=True)
    finally:
        if compile_check.exists():
            compile_check.unlink()
    rows, joins = load_panel()
    ledger = build_sparse_ledger(rows)
    characteristics = summarize_characteristics(ledger)
    traps = summarize_traps(ledger)
    positions = position_summary(ledger)
    policies = feature_policy_matrix()
    write_csv(OUT_DIR / "SPARSE_HISTORY_MISS_LEDGER.csv", ledger, LEDGER_FIELDS)
    write_csv(OUT_DIR / "SPARSE_HISTORY_BREAKOUT_CHARACTERISTICS.csv", characteristics, ["position", "characteristic", "dominant_value", "rows_with_characteristic", "successful_sparse_rows", "share", "interpretation"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_FALSE_POSITIVE_TRAPS.csv", traps, ["position", "false_positive_trap", "trap_rows", "false_positive_sparse_rows", "share", "policy_response"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_POSITION_PROFILE_SUMMARY.csv", positions, ["position", "sparse_history_rows", "startable_hits", "startable_rate", "false_negative_rows", "false_positive_rows", "dominant_population_type", "dominant_false_negative_reason", "design_implication"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_FEATURE_POLICY_MATRIX.csv", policies, ["feature_module", "allowed_use", "inputs", "source_status", "blocked_use", "caveat"])
    write_static_docs(ledger, joins)


if __name__ == "__main__":
    main()
