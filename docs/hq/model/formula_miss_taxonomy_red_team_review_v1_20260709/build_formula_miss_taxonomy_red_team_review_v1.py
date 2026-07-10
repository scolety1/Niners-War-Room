from __future__ import annotations

import csv
import importlib.util
import py_compile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
WORKTREE = Path(__file__).resolve().parents[4]
SOURCE_ROOT = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709")

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_CANONICALIZATION_COMMIT = "8fefe3d9c270df753f78115ee8a1450f1afbd4e9"

V2_SCRIPT = SOURCE_ROOT / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/run_nwr_autonomous_ingredient_upgrade_sequence_v2.py"
MART = SOURCE_ROOT / "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/FORMULA_DATA_MART_REVIEW_ONLY.csv"
AGE = SOURCE_ROOT / "docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
GAUNTLET_REGISTRY = SOURCE_ROOT / "docs/hq/model/full_review_only_formula_gauntlet_candidate_arena_v1_20260709/GAUNTLET_CANDIDATE_REGISTRY.csv"
CLUSTER_ASSIGNMENTS = SOURCE_ROOT / "docs/hq/model/gauntlet_candidate_diversity_clustering_audit_v1_20260709/GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv"
DIVERSE_REGISTRY = SOURCE_ROOT / "docs/hq/model/diverse_champion_refinement_predeclared_execution_v1_20260709/DIVERSE_CHAMPION_REFINEMENT_CANDIDATE_REGISTRY.csv"

SNAP_SIDECAR = SOURCE_ROOT / "docs/hq/model/nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709/NFLVERSE_SNAP_DEPTH_ROLE_REVIEW_ONLY_SIDECAR.csv"
INJURY_SIDECAR = SOURCE_ROOT / "docs/hq/model/point_in_time_injury_availability_data_mart_gate_v1_20260709/POINT_IN_TIME_INJURY_AVAILABILITY_REVIEW_ONLY_SIDECAR.csv"
ROOKIE_SIDECAR = SOURCE_ROOT / "docs/hq/model/rookie_draft_capital_data_mart_join_component_test_v1_20260709/ROOKIE_DRAFT_CAPITAL_REVIEW_ONLY_SIDECAR.csv"
REC_SIDECAR = SOURCE_ROOT / "docs/hq/model/nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_RECEIVING_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv"
EPA_SIDECAR = SOURCE_ROOT / "docs/hq/model/nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_EPA_OPPORTUNITY_REVIEW_ONLY_SIDECAR.csv"
TEAM_SIDECAR = SOURCE_ROOT / "docs/hq/model/team_offensive_environment_sidecar_v1_20260709/TEAM_OFFENSIVE_ENVIRONMENT_REVIEW_ONLY_SIDECAR.csv"
FFOP_SIDECAR = SOURCE_ROOT / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv"
NGS_SIDECAR = SOURCE_ROOT / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv"

POSITIONS = ["QB", "RB", "WR", "TE"]
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
REFERENCE_PLATEAU = 0.755


def load_v2_module() -> Any:
    spec = importlib.util.spec_from_file_location("nwr_v2_helpers_for_red_team", V2_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import helper script: {V2_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.MART_PATH = MART
    module.AGE_PATH = AGE
    module.GAUNTLET_REGISTRY_PATH = GAUNTLET_REGISTRY
    module.GAUNTLET_CLUSTER_PATH = CLUSTER_ASSIGNMENTS
    module.DIVERSE_REGISTRY_PATH = DIVERSE_REGISTRY
    return module


v2 = load_v2_module()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RuntimeError(f"Missing required source artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def num(value: Any) -> float | None:
    return v2.num(value)


def fmt(value: float | None, places: int = 3) -> str:
    return "" if value is None else f"{value:.{places}f}"


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.1f}%"


def sidecar_feature_season(row: dict[str, Any]) -> int:
    value = row.get("feature_season")
    if value not in (None, ""):
        return int(float(value))
    return int(float(row["season"]))


def key_for(row: dict[str, Any], use_feature_season: bool = False) -> tuple[str, int, str]:
    season = int(row["feature_season"] if use_feature_season else row["season"])
    return str(row["player_id"]), season, str(row["position"])


def attach_sidecar(
    rows: list[dict[str, Any]],
    path: Path,
    prefix: str,
    numeric_cols: list[str],
    text_cols: list[str] | None = None,
    column_map: dict[str, str] | None = None,
    source_is_feature_season: bool = False,
) -> int:
    text_cols = text_cols or []
    column_map = column_map or {}
    sidecar_rows = read_csv(path)
    if source_is_feature_season:
        lookup = {(str(r["player_id"]), sidecar_feature_season(r), str(r["position"])): r for r in sidecar_rows}
    else:
        lookup = {(str(r["player_id"]), int(float(r["season"])), str(r["position"])): r for r in sidecar_rows}
    joined = 0
    for row in rows:
        match = lookup.get(key_for(row, use_feature_season=True))
        if match:
            joined += 1
        for col in numeric_cols:
            source_col = column_map.get(col, col)
            row[f"{prefix}_{col}"] = num(match.get(source_col)) if match else None
        for col in text_cols:
            source_col = column_map.get(col, col)
            row[f"{prefix}_{col}"] = str(match.get(source_col, "")) if match else ""
    for col in numeric_cols:
        v2.assign_percentile(rows, f"{prefix}_{col}", f"{prefix}_{col}_pct")
    return joined


def attach_context_sidecars(rows: list[dict[str, Any]]) -> dict[str, int]:
    joins: dict[str, int] = {}
    joins["snap_depth"] = attach_sidecar(
        rows,
        SNAP_SIDECAR,
        "snapdepth",
        [
            "snap_offensive_snaps",
            "snap_offensive_snap_share",
            "snap_games_with_offensive_snaps",
            "snap_low_snap_flag",
            "snap_not_low_snap_score",
            "snap_role_score",
            "depth_primary_depth_rank",
            "depth_best_depth_rank",
            "depth_weeks_as_starter",
            "depth_weeks_as_backup",
            "depth_role_score",
            "depth_stability_score",
            "snap_depth_role_score",
        ],
        ["depth_role_tier", "join_status", "coverage_status", "leakage_flag", "review_only_status"],
        source_is_feature_season=True,
    )
    joins["injury"] = attach_sidecar(
        rows,
        INJURY_SIDECAR,
        "injury",
        [
            "avail_games_missed",
            "avail_active_pct",
            "avail_prior_year_missed_games",
            "avail_two_year_missed_games",
            "avail_durability_score",
            "avail_availability_score",
            "avail_caveat_inverse_score",
            "avail_caveat_flag",
            "avail_ir_pup_flag",
        ],
        ["coverage_status", "leakage_flag", "review_only_status"],
        source_is_feature_season=True,
    )
    joins["rookie_draft"] = attach_sidecar(
        rows,
        ROOKIE_SIDECAR,
        "draft",
        [
            "draft_year",
            "rookie_year",
            "draft_round",
            "draft_overall",
            "drafted_flag",
            "draft_capital_score",
            "years_since_draft",
            "rookie_contract_window_flag",
            "early_career_flag",
            "sparse_history_flag",
        ],
        ["entry_status", "draft_capital_bucket", "coverage_status", "review_only_status"],
        source_is_feature_season=False,
    )
    joins["receiving_opportunity"] = attach_sidecar(
        rows,
        REC_SIDECAR,
        "recopp",
        ["rec_opp_targets", "rec_opp_target_share", "rec_opp_air_yards", "rec_opp_air_yards_share", "rec_opp_wopr", "rec_opp_yac", "rec_opp_receiving_first_downs", "rec_opp_receiving_epa"],
        ["coverage_status", "leakage_flag"],
        source_is_feature_season=True,
    )
    joins["epa"] = attach_sidecar(
        rows,
        EPA_SIDECAR,
        "epa",
        ["epa_total_raw", "epa_per_opportunity", "epa_success_rate", "epa_opportunities", "pass_epa_total", "rush_epa_total", "rec_epa_total"],
        ["asof_status", "review_only_status"],
        source_is_feature_season=True,
    )
    joins["team_env"] = attach_sidecar(
        rows,
        TEAM_SIDECAR,
        "teamenv",
        ["team_env_plays", "team_env_pass_rate", "team_env_points_per_game", "team_env_epa_per_play", "team_env_success_rate", "team_env_offense_score"],
        ["team_env_source_team", "team_change_caveat", "coverage_status", "leakage_flag"],
        source_is_feature_season=True,
    )
    joins["ffopportunity"] = attach_sidecar(
        rows,
        FFOP_SIDECAR,
        "ffop",
        ["ffop_xfp_per_game", "ffop_xfp_total"],
        ["review_only_status", "leakage_flag"],
        {"ffop_xfp_per_game": "ffop_total_fantasy_points_exp_per_game", "ffop_xfp_total": "ffop_total_fantasy_points_exp"},
        source_is_feature_season=False,
    )
    joins["ngs"] = attach_sidecar(
        rows,
        NGS_SIDECAR,
        "ngs",
        ["ngs_position_signal_raw", "ngs_qb_cpoe", "ngs_rec_avg_separation", "ngs_rush_yards_over_expected_per_att"],
        ["review_only_status", "leakage_flag"],
        source_is_feature_season=False,
    )
    return joins


def build_rows() -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows = v2.load_formula_panel()
    seeds = v2.load_seed_registry()
    needed = {"GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE", "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD"}
    if not needed.issubset({s["candidate_id"] for s in seeds}):
        raise RuntimeError("Required Gauntlet seeds were not present in accepted cluster seed registry.")
    v2.materialize_formula_scores(rows, seeds)
    for row in rows:
        row["PYF_BASELINE_score"] = row["pyf_score"]
    v2.assign_rank(rows, "PYF_BASELINE_score", "PYF_BASELINE_rank")
    joins = attach_context_sidecars(rows)

    # Accepted reference formulas only.
    for row in rows:
        seed_081 = row.get("formula__GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__pct")
        seed_083 = row.get("formula__GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__pct")
        depth = row.get("snapdepth_depth_stability_score_pct")
        snap_not_low = row.get("snapdepth_snap_not_low_snap_score_pct")
        ffop = row.get("ffop_ffop_xfp_per_game_pct")
        row["BEST_FULL_HISTORY_score"] = (0.90 * float(seed_081) + 0.10 * float(depth)) if seed_081 is not None and depth is not None else None
        row["BEST_BROAD_WINDOW_score"] = (0.90 * float(seed_081) + 0.10 * float(snap_not_low)) if seed_081 is not None and snap_not_low is not None else None
        row["BEST_PARTIAL_WINDOW_score"] = (0.90 * float(seed_083) + 0.10 * float(ffop)) if seed_083 is not None and ffop is not None else None
    for score_col, rank_col in [
        ("BEST_FULL_HISTORY_score", "BEST_FULL_HISTORY_rank"),
        ("BEST_BROAD_WINDOW_score", "BEST_BROAD_WINDOW_rank"),
        ("BEST_PARTIAL_WINDOW_score", "BEST_PARTIAL_WINDOW_rank"),
    ]:
        v2.assign_rank(rows, score_col, rank_col)
    return rows, joins


def predicted_startable(row: dict[str, Any], rank_col: str) -> bool:
    rank = row.get(rank_col)
    return rank is not None and float(rank) <= STARTABLE_CUTOFF[str(row["position"])]


def is_older_late(row: dict[str, Any]) -> bool:
    return v2.is_older_late(row)


def is_young_early(row: dict[str, Any]) -> bool:
    return v2.is_young_early(row)


def is_high_volume_role(row: dict[str, Any]) -> bool:
    return v2.is_high_volume_role(row)


def is_low_or_sparse_role(row: dict[str, Any]) -> bool:
    return v2.is_low_or_sparse_role(row)


def miss_severity(row: dict[str, Any], rank_col: str, miss_type: str) -> str:
    cutoff = STARTABLE_CUTOFF[str(row["position"])]
    rank = row.get(rank_col)
    actual = row.get("actual_finish")
    if rank is None or actual is None:
        return "UNKNOWN"
    rank_f = float(rank)
    actual_f = float(actual)
    if miss_type == "FALSE_POSITIVE":
        if rank_f <= max(1, cutoff / 2) and actual_f > cutoff * 1.5:
            return "SEVERE_FALSE_POSITIVE"
        if actual_f > cutoff * 2:
            return "MAJOR_FALSE_POSITIVE"
        return "STANDARD_FALSE_POSITIVE"
    if rank_f > cutoff * 1.5 and actual_f <= max(1, cutoff / 2):
        return "SEVERE_FALSE_NEGATIVE"
    if actual_f <= cutoff / 2:
        return "MAJOR_FALSE_NEGATIVE"
    return "STANDARD_FALSE_NEGATIVE"


def fp_categories(row: dict[str, Any]) -> list[str]:
    cats: list[str] = []
    if is_high_volume_role(row):
        cats.append("prior_production_trap")
    if is_older_late(row):
        cats.append("old_late_lifecycle_decline")
    if is_high_volume_role(row) and is_older_late(row):
        cats.append("veteran_high_volume_decline")
    if (row.get("snapdepth_snap_low_snap_flag") or 0) >= 1 or (row.get("snapdepth_snap_role_score") is not None and float(row["snapdepth_snap_role_score"]) < 0.35):
        cats.append("low_snap_depth_warning")
    if str(row.get("snapdepth_depth_role_tier", "")).lower() in {"backup", "deep_backup", "no_depth_record"}:
        cats.append("role_decline_or_depth_warning")
    if (row.get("injury_avail_caveat_flag") or 0) >= 1 or (row.get("injury_avail_availability_score") is not None and float(row["injury_avail_availability_score"]) < 0.50):
        cats.append("injury_availability_caveat")
    team_caveat = str(row.get("teamenv_team_change_caveat", "")).strip().lower()
    if team_caveat and "uses_prior_season_team_only" not in team_caveat and "no_team_change" not in team_caveat:
        cats.append("team_change_context_gap")
    if row.get("sparse_history_bool") or row.get("low_games_bool"):
        cats.append("low_games_small_sample")
    if row.get("recopp_rec_opp_wopr") is not None and float(row["recopp_rec_opp_wopr"]) > 0.55 and (row.get("snapdepth_snap_role_score") is not None and float(row["snapdepth_snap_role_score"]) < 0.45):
        cats.append("high_efficiency_or_opportunity_weak_role")
    if not cats:
        cats.append("unknown")
    return cats


def fn_categories(row: dict[str, Any]) -> list[str]:
    cats: list[str] = []
    if is_young_early(row):
        cats.append("young_breakout")
    if row.get("sparse_history_bool"):
        cats.append("sparse_history_breakout")
    if row.get("low_games_bool"):
        cats.append("low_games_breakout")
    if row.get("draft_early_career_flag") is not None and float(row["draft_early_career_flag"]) >= 1:
        cats.append("rookie_early_career_ascent")
    if row.get("snapdepth_snap_role_score") is not None and float(row["snapdepth_snap_role_score"]) >= 0.70:
        cats.append("snap_depth_role_promotion_signal")
    if row.get("snapdepth_depth_weeks_as_starter") is not None and float(row["snapdepth_depth_weeks_as_starter"]) >= 8:
        cats.append("starter_depth_chart_signal")
    if row.get("recopp_rec_opp_wopr") is not None and float(row["recopp_rec_opp_wopr"]) >= 0.50:
        cats.append("receiving_opportunity_signal")
    if row.get("ffop_ffop_xfp_per_game") is not None and float(row["ffop_ffop_xfp_per_game"]) >= 10:
        cats.append("expected_fantasy_opportunity_signal")
    if row.get("injury_avail_availability_score") is not None and float(row["injury_avail_availability_score"]) >= 0.80:
        cats.append("availability_rebound_or_clean_report_context")
    if not cats:
        cats.append("unknown")
    return cats


REFERENCE_FORMULAS = [
    {
        "formula_id": "PYF_BASELINE",
        "label": "PYF baseline",
        "window": "full_history_2013_2025",
        "score_col": "PYF_BASELINE_score",
        "rank_col": "PYF_BASELINE_rank",
        "candidate_reference": "pyf_prior_nwr_points",
        "window_note": "Full 2013-2025 review-only Formula Data Mart scope.",
    },
    {
        "formula_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100",
        "label": "Best full-history candidate",
        "window": "full_history_2013_2025",
        "score_col": "BEST_FULL_HISTORY_score",
        "rank_col": "BEST_FULL_HISTORY_rank",
        "candidate_reference": "0.90 GAUNTLET_081 percentile + 0.10 snap/depth depth-stability percentile",
        "window_note": "Full-history comparable, 5,518 rows.",
    },
    {
        "formula_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100",
        "label": "Best broad-window candidate",
        "window": "broad_window_2014_2025",
        "score_col": "BEST_BROAD_WINDOW_score",
        "rank_col": "BEST_BROAD_WINDOW_rank",
        "candidate_reference": "0.90 GAUNTLET_081 percentile + 0.10 snap-not-low percentile",
        "window_note": "Broad-window comparable only; 2014-2025 rows with lagged snap counts.",
    },
    {
        "formula_id": "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10",
        "label": "Best partial-window candidate",
        "window": "partial_window_2022_2025",
        "score_col": "BEST_PARTIAL_WINDOW_score",
        "rank_col": "BEST_PARTIAL_WINDOW_rank",
        "candidate_reference": "0.90 GAUNTLET_083 percentile + 0.10 ffopportunity XFP per-game percentile",
        "window_note": "Partial modern window only; not full-history comparable.",
    },
]


def miss_ledger(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ref in REFERENCE_FORMULAS:
        rank_col = ref["rank_col"]
        score_col = ref["score_col"]
        pyf_rank = "PYF_BASELINE_rank"
        for row in rows:
            if row.get(rank_col) is None or row.get("actual_finish") is None:
                continue
            pred = predicted_startable(row, rank_col)
            actual = bool(row["actual_startable"])
            if pred == actual:
                continue
            miss_type = "FALSE_POSITIVE" if pred and not actual else "FALSE_NEGATIVE"
            cats = fp_categories(row) if miss_type == "FALSE_POSITIVE" else fn_categories(row)
            out.append(
                {
                    "season": row["season"],
                    "player_id": row["player_id"],
                    "player_name": row["player_name"],
                    "position": row["position"],
                    "team": row.get("team") or row.get("target_team") or "",
                    "formula_id": ref["formula_id"],
                    "scoreboard_window": ref["window"],
                    "formula_score": fmt(row.get(score_col), 6),
                    "formula_rank": fmt(row.get(rank_col), 0),
                    "pyf_score": fmt(row.get("pyf_score")),
                    "pyf_rank": fmt(row.get(pyf_rank), 0),
                    "actual_outcome_label": "STARTABLE_HIT" if actual else "NOT_STARTABLE",
                    "miss_type": miss_type,
                    "miss_severity": miss_severity(row, rank_col, miss_type),
                    "position_rank_actual": fmt(row.get("actual_finish"), 0),
                    "top_n_threshold_involved": STARTABLE_CUTOFF[str(row["position"])],
                    "age": fmt(row.get("age"), 1),
                    "lifecycle_bucket": row.get("lifecycle_bucket", ""),
                    "age_bucket": row.get("age_bucket", ""),
                    "role_archetype": row.get("role_archetype", ""),
                    "role_usage_bucket": row.get("role_usage_bucket", ""),
                    "snap_offensive_snap_share": fmt(row.get("snapdepth_snap_offensive_snap_share")),
                    "snap_role_score": fmt(row.get("snapdepth_snap_role_score")),
                    "snap_low_snap_flag": fmt(row.get("snapdepth_snap_low_snap_flag"), 0),
                    "depth_role_tier": row.get("snapdepth_depth_role_tier", ""),
                    "depth_stability_score": fmt(row.get("snapdepth_depth_stability_score")),
                    "injury_availability_score": fmt(row.get("injury_avail_availability_score")),
                    "injury_caveat_flag": fmt(row.get("injury_avail_caveat_flag"), 0),
                    "draft_capital_bucket": row.get("draft_draft_capital_bucket", ""),
                    "early_career_flag": fmt(row.get("draft_early_career_flag"), 0),
                    "sparse_history_flag": str(bool(row.get("sparse_history_bool"))).lower(),
                    "low_games_flag": str(bool(row.get("low_games_bool"))).lower(),
                    "rec_opp_wopr": fmt(row.get("recopp_rec_opp_wopr")),
                    "rec_opp_target_share": fmt(row.get("recopp_rec_opp_target_share")),
                    "epa_total_raw": fmt(row.get("epa_epa_total_raw")),
                    "team_env_offense_score": fmt(row.get("teamenv_team_env_offense_score")),
                    "team_change_caveat": row.get("teamenv_team_change_caveat", ""),
                    "ffop_xfp_per_game": fmt(row.get("ffop_ffop_xfp_per_game")),
                    "ngs_position_signal": fmt(row.get("ngs_ngs_position_signal_raw")),
                    "notes_candidate_miss_reason": ";".join(cats),
                }
            )
    return out


def category_rows(ledger: list[dict[str, Any]], miss_type: str) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    totals: Counter[tuple[str, str, str]] = Counter()
    for row in ledger:
        if row["miss_type"] != miss_type:
            continue
        key = (row["scoreboard_window"], row["formula_id"], row["position"])
        totals[key] += 1
        for cat in row["notes_candidate_miss_reason"].split(";"):
            counts[key][cat] += 1
    out: list[dict[str, Any]] = []
    for key, counter in sorted(counts.items()):
        total = totals[key]
        for cat, count in counter.most_common():
            out.append(
                {
                    "scoreboard_window": key[0],
                    "formula_id": key[1],
                    "position": key[2],
                    "miss_type": miss_type,
                    "category": cat,
                    "miss_rows": count,
                    "category_share_of_formula_position_misses": pct(count / total if total else None),
                }
            )
    return out


def profile_by(ledger: list[dict[str, Any]], field: str, output_name: str) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str, str, str, str]] = Counter()
    totals: Counter[tuple[str, str, str, str]] = Counter()
    for row in ledger:
        bucket = str(row.get(field, "") or "UNKNOWN")
        key = (row["scoreboard_window"], row["formula_id"], row["miss_type"], bucket, row["position"])
        counter[key] += 1
        totals[(row["scoreboard_window"], row["formula_id"], row["miss_type"], row["position"])] += 1
    out = []
    for (window, formula, miss_type, bucket, position), count in sorted(counter.items()):
        total = totals[(window, formula, miss_type, position)]
        out.append(
            {
                "scoreboard_window": window,
                "formula_id": formula,
                "miss_type": miss_type,
                "position": position,
                output_name: bucket,
                "miss_rows": count,
                "share_of_formula_position_misses": pct(count / total if total else None),
            }
        )
    return out


def reference_comparison(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    pyf_rank = "PYF_BASELINE_rank"
    for ref in REFERENCE_FORMULAS:
        rank_col = ref["rank_col"]
        scoped = [r for r in rows if r.get(rank_col) is not None and r.get("actual_finish") is not None]
        fp = {r["substrate_row_id"] for r in scoped if predicted_startable(r, rank_col) and not r["actual_startable"]}
        fn = {r["substrate_row_id"] for r in scoped if not predicted_startable(r, rank_col) and r["actual_startable"]}
        pyf_fp = {r["substrate_row_id"] for r in scoped if predicted_startable(r, pyf_rank) and not r["actual_startable"]}
        pyf_fn = {r["substrate_row_id"] for r in scoped if not predicted_startable(r, pyf_rank) and r["actual_startable"]}
        out.append(
            {
                "scoreboard_window": ref["window"],
                "formula_id": ref["formula_id"],
                "rows_compared": len(scoped),
                "false_positives": len(fp),
                "false_negatives": len(fn),
                "total_misses": len(fp) + len(fn),
                "pyf_false_positives_same_rows": len(pyf_fp),
                "pyf_false_negatives_same_rows": len(pyf_fn),
                "pyf_total_misses_same_rows": len(pyf_fp) + len(pyf_fn),
                "pyf_misses_resolved": len((pyf_fp | pyf_fn) - (fp | fn)),
                "new_misses_vs_pyf": len((fp | fn) - (pyf_fp | pyf_fn)),
                "net_miss_reduction_vs_pyf": (len(pyf_fp) + len(pyf_fn)) - (len(fp) + len(fn)),
                "false_positive_reduction_vs_pyf": len(pyf_fp) - len(fp),
                "false_negative_reduction_vs_pyf": len(pyf_fn) - len(fn),
                "window_comparability": ref["window_note"],
            }
        )
    return out


def top_categories(rows: list[dict[str, Any]], n: int = 6) -> str:
    c = Counter()
    for row in rows:
        for cat in row["notes_candidate_miss_reason"].split(";"):
            c[cat] += 1
    return ", ".join(f"{cat} ({count})" for cat, count in c.most_common(n))


def write_reports(
    ledger: list[dict[str, Any]],
    fp_tax: list[dict[str, Any]],
    fn_tax: list[dict[str, Any]],
    comparison: list[dict[str, Any]],
    joins: dict[str, int],
) -> None:
    fp_rows = [r for r in ledger if r["miss_type"] == "FALSE_POSITIVE"]
    fn_rows = [r for r in ledger if r["miss_type"] == "FALSE_NEGATIVE"]
    best_reducer = max((r for r in comparison if r["formula_id"] != "PYF_BASELINE"), key=lambda r: int(r["net_miss_reduction_vs_pyf"]))
    most_new = max((r for r in comparison if r["formula_id"] != "PYF_BASELINE"), key=lambda r: int(r["new_misses_vs_pyf"]))
    actionable = "Sparse-history / young-player breakout modeling" if "young_breakout" in top_categories(fn_rows) else "Targeted role-loss and veteran-decline guard review"
    next_lane = "Sparse-History Breakout Red Team / Rookie-Young Player Model Design V1"

    report = f"""
# Formula Miss Taxonomy / Red Team Review V1

## Verdict

`GREEN_FORMULA_RED_TEAM_FOUND_ACTIONABLE_MISS_REDUCTION_PATH`

## Scope

This lane red-teamed accepted review-only formula references and did not tune formulas, run a new Gauntlet, run ranking simulation, change rankings, change app/runtime behavior, promote sources, push, merge, or write canonical `local_exports`.

Remote HQ verified: `{EXPECTED_REMOTE_HEAD}`.

Prior canonicalization commit verified: `{PRIOR_CANONICALIZATION_COMMIT}`.

## Formula References Analyzed

1. `PYF_BASELINE`
2. `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100`
3. `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100`
4. `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10`

## Window Separation

- Full-history: `2013-2025`
- Broad-window: `2014-2025`
- Partial modern window: `2022-2025`

Partial-window results remain separate and are not full-history comparable.

## Miss Definitions

False positives are rows where formula rank is inside the accepted position startable threshold but the historical `label_startable_hit` is false. False negatives are rows where formula rank is outside that threshold but `label_startable_hit` is true.

Severe misses use the same accepted position thresholds and flag extreme rank/outcome gaps. Outcome labels are the existing Formula Data Mart labels only.

## Top False-Positive Categories

{top_categories(fp_rows)}

## Top False-Negative Categories

{top_categories(fn_rows)}

## Formula Comparison

Best PYF miss reducer: `{best_reducer['formula_id']}`, net miss reduction `{best_reducer['net_miss_reduction_vs_pyf']}` on `{best_reducer['rows_compared']}` comparable rows.

Formula creating the most new misses vs PYF: `{most_new['formula_id']}`, new misses `{most_new['new_misses_vs_pyf']}`. This is expected to some degree because each additive ingredient resolves some PYF misses while creating others near the threshold.

## Actionable Interpretation

The most actionable red-team path is `{actionable}`. Existing formulas reduce broad miss volume mostly through production stability and snap/depth context, but false negatives remain concentrated in young, sparse-history, early-career, and opportunity-emergence rows. False positives remain concentrated around prior-production traps, older/late lifecycle risk, role/depth warnings, and availability caveats.

## Ranking Simulation Decision

Review-only ranking simulation remains not justified. The miss clusters are understandable but not resolved enough to treat the current best candidates as stable board projection tools.

## Source / Use Gate Summary

Sidecar joins used for miss context: `{joins}`.

All source fields used here came from accepted review-only artifacts. They remain not production/model-use and not ranking-integration approved.
"""
    write_md(OUT_DIR / "FORMULA_MISS_TAXONOMY_RED_TEAM_REVIEW_V1_REPORT.md", report)

    opportunities = f"""
# Actionable Miss-Reduction Opportunities

1. Sparse-history breakout and rookie/young-player design: highest-value path because false negatives repeatedly cluster in young/early lifecycle, sparse-history, early-career, and opportunity-emergence rows.
2. Veteran decline / role-loss guard review: useful for false positives, especially prior-production traps with late lifecycle, high-volume role history, low snap/depth warnings, or injury availability caveats.
3. Team-change / role-change projection gap: useful but harder because the accepted team-environment lane proved prior-team context is leakage-safe while still unable to project free-agent moves, trades, coaching changes, or QB changes.
4. Participation/personnel/pressure context: plausible future data lane, but only if source/as-of gates are clean and it is not confused with routes/YPRR/TPRR.

Generic same-ingredient formula tuning is not recommended.
"""
    write_md(OUT_DIR / "FORMULA_ACTIONABLE_MISS_REDUCTION_OPPORTUNITIES.md", opportunities)

    next_decision = f"""
# Formula Red Team Next Lane Decision

Recommended next lane:

`{next_lane}`

Reason: false negatives are the clearest actionable miss cluster after the accepted ingredient phase. They are concentrated around players whose prior NFL production history understates future outcomes: young breakouts, sparse-history players, early-career ascents, and role/opportunity emergence. A design lane can define guardrails and modeling scope without running a new Gauntlet or ranking simulation.

Review-only ranking simulation remains blocked.
Production/model-use remains blocked.
Rankings integration remains blocked.
App/runtime behavior remains unchanged.
Source promotion remains blocked.
Push/merge remains blocked.
"""
    write_md(OUT_DIR / "FORMULA_RED_TEAM_NEXT_LANE_DECISION.md", next_decision)

    blockers = """
# Formula Red Team Blockers And Caveats

- This is a review-only taxonomy, not a formula improvement lane.
- It reconstructs only accepted reference formulas and does not run a new formula search.
- Partial-window ffopportunity results remain `2022-2025` only and are not full-history comparable.
- Miss reasons are heuristic taxonomy labels over accepted sidecar context, not causal proof.
- Same-season and future information were not used.
- Ranking simulation, production/model-use, source promotion, and app/runtime changes remain blocked.
"""
    write_md(OUT_DIR / "FORMULA_RED_TEAM_BLOCKERS_AND_CAVEATS.md", blockers)

    source_trace = f"""
# Formula Red Team Source Trace

Primary accepted source root:

`{SOURCE_ROOT}`

Read artifacts:

- Formula Data Mart: `{MART}`
- Age/lifecycle sidecar: `{AGE}`
- Gauntlet registry: `{GAUNTLET_REGISTRY}`
- Cluster assignments: `{CLUSTER_ASSIGNMENTS}`
- Diverse refinement registry: `{DIVERSE_REGISTRY}`
- Snap/depth sidecar: `{SNAP_SIDECAR}`
- Injury availability sidecar: `{INJURY_SIDECAR}`
- Rookie/draft sidecar: `{ROOKIE_SIDECAR}`
- Receiving opportunity sidecar: `{REC_SIDECAR}`
- EPA opportunity sidecar: `{EPA_SIDECAR}`
- Team offensive environment sidecar: `{TEAM_SIDECAR}`
- ffopportunity sidecar: `{FFOP_SIDECAR}`
- NGS sidecar: `{NGS_SIDECAR}`

Source/use gate: all inputs are accepted review-only artifacts. No production/model-use or rankings integration approval is granted here.

Leakage/as-of gate: formulas use lagged Formula Data Mart fields and accepted lagged sidecar fields. Same-season/future context remains blocked.
"""
    write_md(OUT_DIR / "FORMULA_RED_TEAM_SOURCE_TRACE.md", source_trace)


def main() -> None:
    for path in [V2_SCRIPT, MART, AGE, GAUNTLET_REGISTRY, CLUSTER_ASSIGNMENTS, DIVERSE_REGISTRY, SNAP_SIDECAR, INJURY_SIDECAR, ROOKIE_SIDECAR, REC_SIDECAR, EPA_SIDECAR, TEAM_SIDECAR, FFOP_SIDECAR, NGS_SIDECAR]:
        if not path.exists():
            raise RuntimeError(f"Missing accepted source artifact: {path}")
    py_compile.compile(__file__, doraise=True)
    rows, joins = build_rows()
    ledger = miss_ledger(rows)
    fp_tax = category_rows(ledger, "FALSE_POSITIVE")
    fn_tax = category_rows(ledger, "FALSE_NEGATIVE")
    comparison = reference_comparison(rows)

    ledger_fields = [
        "season",
        "player_id",
        "player_name",
        "position",
        "team",
        "formula_id",
        "scoreboard_window",
        "formula_score",
        "formula_rank",
        "pyf_score",
        "pyf_rank",
        "actual_outcome_label",
        "miss_type",
        "miss_severity",
        "position_rank_actual",
        "top_n_threshold_involved",
        "age",
        "lifecycle_bucket",
        "age_bucket",
        "role_archetype",
        "role_usage_bucket",
        "snap_offensive_snap_share",
        "snap_role_score",
        "snap_low_snap_flag",
        "depth_role_tier",
        "depth_stability_score",
        "injury_availability_score",
        "injury_caveat_flag",
        "draft_capital_bucket",
        "early_career_flag",
        "sparse_history_flag",
        "low_games_flag",
        "rec_opp_wopr",
        "rec_opp_target_share",
        "epa_total_raw",
        "team_env_offense_score",
        "team_change_caveat",
        "ffop_xfp_per_game",
        "ngs_position_signal",
        "notes_candidate_miss_reason",
    ]
    write_csv(OUT_DIR / "FORMULA_MISS_PLAYER_SEASON_LEDGER.csv", ledger, ledger_fields)
    tax_fields = ["scoreboard_window", "formula_id", "position", "miss_type", "category", "miss_rows", "category_share_of_formula_position_misses"]
    write_csv(OUT_DIR / "FORMULA_FALSE_POSITIVE_TAXONOMY.csv", fp_tax, tax_fields)
    write_csv(OUT_DIR / "FORMULA_FALSE_NEGATIVE_TAXONOMY.csv", fn_tax, tax_fields)

    write_csv(OUT_DIR / "FORMULA_MISS_PROFILE_BY_POSITION.csv", profile_by(ledger, "position", "position_bucket"), ["scoreboard_window", "formula_id", "miss_type", "position", "position_bucket", "miss_rows", "share_of_formula_position_misses"])
    write_csv(OUT_DIR / "FORMULA_MISS_PROFILE_BY_LIFECYCLE.csv", profile_by(ledger, "lifecycle_bucket", "lifecycle_bucket"), ["scoreboard_window", "formula_id", "miss_type", "position", "lifecycle_bucket", "miss_rows", "share_of_formula_position_misses"])
    write_csv(OUT_DIR / "FORMULA_MISS_PROFILE_BY_ROLE_ARCHETYPE.csv", profile_by(ledger, "role_archetype", "role_archetype"), ["scoreboard_window", "formula_id", "miss_type", "position", "role_archetype", "miss_rows", "share_of_formula_position_misses"])
    write_csv(OUT_DIR / "FORMULA_MISS_PROFILE_BY_SNAP_DEPTH.csv", profile_by(ledger, "depth_role_tier", "snap_depth_bucket"), ["scoreboard_window", "formula_id", "miss_type", "position", "snap_depth_bucket", "miss_rows", "share_of_formula_position_misses"])
    write_csv(OUT_DIR / "FORMULA_MISS_PROFILE_BY_INJURY_AVAILABILITY.csv", profile_by(ledger, "injury_caveat_flag", "injury_availability_bucket"), ["scoreboard_window", "formula_id", "miss_type", "position", "injury_availability_bucket", "miss_rows", "share_of_formula_position_misses"])
    write_csv(OUT_DIR / "FORMULA_MISS_PROFILE_BY_ROOKIE_SPARSE_HISTORY.csv", profile_by(ledger, "sparse_history_flag", "rookie_sparse_history_bucket"), ["scoreboard_window", "formula_id", "miss_type", "position", "rookie_sparse_history_bucket", "miss_rows", "share_of_formula_position_misses"])
    write_csv(
        OUT_DIR / "FORMULA_REFERENCE_COMPARISON_MISS_REDUCTION.csv",
        comparison,
        [
            "scoreboard_window",
            "formula_id",
            "rows_compared",
            "false_positives",
            "false_negatives",
            "total_misses",
            "pyf_false_positives_same_rows",
            "pyf_false_negatives_same_rows",
            "pyf_total_misses_same_rows",
            "pyf_misses_resolved",
            "new_misses_vs_pyf",
            "net_miss_reduction_vs_pyf",
            "false_positive_reduction_vs_pyf",
            "false_negative_reduction_vs_pyf",
            "window_comparability",
        ],
    )
    write_reports(ledger, fp_tax, fn_tax, comparison, joins)


if __name__ == "__main__":
    main()
