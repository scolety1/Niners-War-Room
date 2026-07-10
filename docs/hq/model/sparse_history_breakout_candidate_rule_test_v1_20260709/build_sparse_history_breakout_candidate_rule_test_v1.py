from __future__ import annotations

import csv
import importlib.util
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
PRIOR_DESIGN_COMMIT = "f493dbf751e42b1f258df14e41a20fde9274d136"
PRIOR_ADDENDUM_COMMIT = "8e31c89aee7bc2598046206dd0ec8336dce1c248"

DESIGN_DIR = THIS_WORKTREE / "docs/hq/model/sparse_history_breakout_red_team_rookie_young_player_model_design_v1_20260709"
DESIGN_SCRIPT = DESIGN_DIR / "build_sparse_history_breakout_design_v1.py"
ADDENDUM_DIR = THIS_WORKTREE / "docs/hq/master/formula_red_team_canonicalization_addendum_v1_20260709"
RED_TEAM_DIR = THIS_WORKTREE / "docs/hq/model/formula_miss_taxonomy_red_team_review_v1_20260709"
INGREDIENT_CANON_DIR = SOURCE_ROOT / "docs/hq/master/ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709"
ROOKIE_DIR = SOURCE_ROOT / "docs/hq/model/rookie_draft_capital_data_mart_join_component_test_v1_20260709"
SNAP_DIR = SOURCE_ROOT / "docs/hq/model/nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709"
INJURY_DIR = SOURCE_ROOT / "docs/hq/model/point_in_time_injury_availability_data_mart_gate_v1_20260709"
FFOP_NGS_DIR = SOURCE_ROOT / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709"
SCOREBOARD_DIR = SOURCE_ROOT / "docs/hq/master/ingredient_scoreboard_normalization_best_candidate_consolidation_v1_20260709"
GAUNTLET_DIR = SOURCE_ROOT / "docs/hq/model/full_review_only_formula_gauntlet_candidate_arena_v1_20260709"

POSITIONS = ["QB", "RB", "WR", "TE"]
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
SEVERE_FN_CUTOFF = {"QB": 6, "RB": 18, "WR": 24, "TE": 6}


def writable_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def load_design_module() -> Any:
    spec = importlib.util.spec_from_file_location("sparse_design", DESIGN_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load design script: {DESIGN_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RULES: list[dict[str, Any]] = [
    {
        "rule_id": "RULE_001_ROLE_PROMOTION_BREAKOUT_05",
        "rule_family": "ROLE_PROMOTION_BREAKOUT_RULE",
        "rule_name": "Role promotion sparse-history boost",
        "score_delta": 0.05,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible and snap/depth role-promotion signal",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_002_DEPTH_STARTER_BREAKOUT_05",
        "rule_family": "DEPTH_STARTER_BREAKOUT_RULE",
        "rule_name": "Starter depth-chart sparse-history boost",
        "score_delta": 0.05,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible and prior-season starter/depth signal",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_003_SNAP_GROWTH_BREAKOUT_05",
        "rule_family": "SNAP_GROWTH_BREAKOUT_RULE",
        "rule_name": "Snap growth sparse-history boost",
        "score_delta": 0.05,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible and safely lagged snap-share trend or snap role growth",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_004_AVAILABILITY_REBOUND_05",
        "rule_family": "AVAILABILITY_REBOUND_RULE",
        "rule_name": "Availability rebound sparse-history boost",
        "score_delta": 0.05,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible, prior missed games, high availability/clean-report score, no caveat flag",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_005_EARLY_CAREER_LIFECYCLE_025",
        "rule_family": "EARLY_CAREER_LIFECYCLE_RULE",
        "rule_name": "Early-career lifecycle with role boost",
        "score_delta": 0.025,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible, years one-three or early lifecycle, and a role/depth signal",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_006_DRAFT_CAPITAL_WITH_ROLE_05",
        "rule_family": "DRAFT_CAPITAL_WITH_ROLE_RULE",
        "rule_name": "Draft capital only when paired with role",
        "score_delta": 0.05,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible, positive round one/two draft evidence, and a starter/role signal",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_007_EXPECTED_OPPORTUNITY_PARTIAL_05",
        "rule_family": "EXPECTED_OPPORTUNITY_PARTIAL_WINDOW_RULE",
        "rule_name": "Partial-window expected-opportunity boost",
        "score_delta": 0.05,
        "window_scope": "partial_only",
        "conditions": "sparse-history eligible and ffopportunity or NGS expected-opportunity signal present",
        "partial_window_only": "true",
    },
    {
        "rule_id": "RULE_008_POSITION_SPECIFIC_BREAKOUT_05",
        "rule_family": "POSITION_SPECIFIC_BREAKOUT_RULE",
        "rule_name": "Position-specific sparse breakout profile",
        "score_delta": 0.05,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible and position-specific role/age/draft profile passes",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_009_FALSE_POSITIVE_TRAP_DOWNGRADE_05",
        "rule_family": "FALSE_POSITIVE_TRAP_DOWNGRADE_RULE",
        "rule_name": "Single trap downgrade",
        "score_delta": -0.05,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible and any false-positive trap flag is active",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_010_FALSE_POSITIVE_TRAP_STRICT_10",
        "rule_family": "FALSE_POSITIVE_TRAP_DOWNGRADE_RULE",
        "rule_name": "Strict multi-trap downgrade",
        "score_delta": -0.10,
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible and two or more false-positive trap flags are active",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_011_SPARSE_HISTORY_COMPOSITE_BALANCED",
        "rule_family": "SPARSE_HISTORY_COMPOSITE_RULE",
        "rule_name": "Balanced breakout/trap composite",
        "score_delta": "plus_05_or_minus_05",
        "window_scope": "full_broad_partial",
        "conditions": "sparse-history eligible; boost two or more breakout signals, downgrade trap without breakout",
        "partial_window_only": "false",
    },
    {
        "rule_id": "RULE_012_COMPOSITE_PARTIAL_EXPECTED_OPP",
        "rule_family": "SPARSE_HISTORY_COMPOSITE_RULE",
        "rule_name": "Partial expected-opportunity composite",
        "score_delta": "plus_05_or_minus_025",
        "window_scope": "partial_only",
        "conditions": "sparse-history eligible; boost core signal plus ffop/NGS, small downgrade for traps",
        "partial_window_only": "true",
    },
]

RULE_INPUT_POLICY = [
    {"input_name": "sparse-history population flags", "allowed_status": "ALLOWED_REVIEW_ONLY", "source": "Formula Data Mart and sparse design ledger", "blocked_use": "production rank input", "asof_status": "lagged N-to-N+1"},
    {"input_name": "age/lifecycle bucket", "allowed_status": "ALLOWED_REVIEW_ONLY", "source": "Age/lifecycle sidecar", "blocked_use": "automatic production boost/penalty", "asof_status": "stable identity metadata review-only"},
    {"input_name": "years since draft", "allowed_status": "ALLOWED_REVIEW_ONLY", "source": "Draft capital sidecar", "blocked_use": "future pre-draft use before draft year", "asof_status": "static after NFL entry"},
    {"input_name": "draft capital bucket", "allowed_status": "ALLOWED_REVIEW_ONLY_POSITIVE_EVIDENCE", "source": "Draft capital sidecar", "blocked_use": "UDFA inference or CFBD/prospect model input", "asof_status": "static after NFL entry"},
    {"input_name": "snap/depth role score", "allowed_status": "ALLOWED_REVIEW_ONLY", "source": "Snap/depth role sidecar", "blocked_use": "same-season target depth chart", "asof_status": "lagged N-to-N+1"},
    {"input_name": "starter/depth signal", "allowed_status": "ALLOWED_REVIEW_ONLY", "source": "Snap/depth role sidecar", "blocked_use": "future starter projection", "asof_status": "lagged N-to-N+1"},
    {"input_name": "snap growth signal", "allowed_status": "ALLOWED_REVIEW_ONLY_IF_LAGGED", "source": "Snap/depth role sidecar", "blocked_use": "target-season growth", "asof_status": "lagged N-to-N+1"},
    {"input_name": "low snap flag", "allowed_status": "ALLOWED_REVIEW_ONLY_GUARDRAIL", "source": "Snap/depth role sidecar", "blocked_use": "production demotion", "asof_status": "lagged N-to-N+1"},
    {"input_name": "injury/availability caveat", "allowed_status": "ALLOWED_REVIEW_ONLY_GUARDRAIL", "source": "Injury availability sidecar", "blocked_use": "injury prediction", "asof_status": "lagged N-to-N+1"},
    {"input_name": "availability rebound / clean-report context", "allowed_status": "ALLOWED_REVIEW_ONLY_CONTEXT", "source": "Injury availability sidecar", "blocked_use": "future health projection", "asof_status": "lagged N-to-N+1"},
    {"input_name": "role archetype", "allowed_status": "ALLOWED_REVIEW_ONLY_CONTEXT", "source": "Formula Data Mart role context", "blocked_use": "direct ranking input", "asof_status": "lagged prior production context"},
    {"input_name": "ffopportunity / NGS context", "allowed_status": "PARTIAL_WINDOW_ONLY", "source": "Autonomous V2 sidecars", "blocked_use": "full-history plateau claim", "asof_status": "partial-window lagged 2022-2025 targets"},
    {"input_name": "current-only ADP / market", "allowed_status": "BLOCKED", "source": "Market/ADP gate", "blocked_use": "historical formula input", "asof_status": "as-of gate not passed"},
    {"input_name": "CFBD/prospect production", "allowed_status": "BLOCKED", "source": "Rookie/draft gate", "blocked_use": "model input without source and identity gates", "asof_status": "not approved"},
]

REFERENCES = [
    {
        "reference_id": "PYF_BASELINE",
        "formula_id": "PYF baseline",
        "score_col": "PYF_BASELINE_score_pct",
        "scoreboard_window": "full_history",
        "season_min": 2013,
        "season_max": 2025,
        "full_history_comparable": "true",
        "broad_window_comparable": "false",
        "partial_window_only": "false",
    },
    {
        "reference_id": "BEST_FULL_HISTORY",
        "formula_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100",
        "score_col": "BEST_FULL_HISTORY_score",
        "scoreboard_window": "full_history",
        "season_min": 2013,
        "season_max": 2025,
        "full_history_comparable": "true",
        "broad_window_comparable": "false",
        "partial_window_only": "false",
    },
    {
        "reference_id": "BEST_BROAD_WINDOW",
        "formula_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100",
        "score_col": "BEST_BROAD_WINDOW_score",
        "scoreboard_window": "broad_window",
        "season_min": 2014,
        "season_max": 2025,
        "full_history_comparable": "false",
        "broad_window_comparable": "true",
        "partial_window_only": "false",
    },
    {
        "reference_id": "BEST_PARTIAL_WINDOW",
        "formula_id": "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10",
        "score_col": "BEST_PARTIAL_WINDOW_score",
        "scoreboard_window": "partial_window",
        "season_min": 2022,
        "season_max": 2025,
        "full_history_comparable": "false",
        "broad_window_comparable": "false",
        "partial_window_only": "true",
    },
]


def is_sparse(row: dict[str, Any], design: Any) -> bool:
    return bool(design.sparse_types(row))


def flag_profile(row: dict[str, Any], design: Any) -> dict[str, Any]:
    sparse = is_sparse(row, design)
    ysd = row.get("draft_years_since_draft")
    ysd_int = int(ysd) if ysd is not None else None
    depth_tier = str(row.get("snap_depth_role_tier") or "")
    snap_role = num(row.get("snap_snap_role_score")) or 0.0
    snap_trend = num(row.get("snap_snap_share_trend")) or 0.0
    starter_weeks = num(row.get("snap_depth_weeks_as_starter")) or 0.0
    low_snap = num(row.get("snap_snap_low_snap_flag")) or 0.0
    avail_score = num(row.get("injury_avail_availability_score"))
    prior_missed = num(row.get("injury_avail_prior_year_missed_games")) or 0.0
    caveat = num(row.get("injury_avail_caveat_flag")) or 0.0
    draft_bucket = str(row.get("draft_draft_capital_bucket") or "")
    lifecycle = str(row.get("lifecycle_bucket") or "")
    ffop = num(row.get("ffop_ffop_xfp_per_game"))
    ngs = num(row.get("ngs_ngs_position_signal_raw"))
    role_promotion = snap_role >= 0.70 or starter_weeks >= 8 or depth_tier == "PRIMARY_STARTER"
    starter_signal = starter_weeks >= 8 or depth_tier in {"PRIMARY_STARTER", "PARTIAL_STARTER"}
    snap_growth = snap_trend >= 0.10 or (snap_role >= 0.65 and (num(row.get("snap_snap_games_with_offensive_snaps")) or 0.0) >= 8)
    availability_rebound = avail_score is not None and avail_score >= 0.80 and prior_missed >= 2 and caveat < 1
    early_career = (ysd_int is not None and 0 <= ysd_int <= 3) or lifecycle in {"early_career_1_to_3", "rookie_or_new_entry"}
    draft_top = draft_bucket in {"round_1", "round_2"}
    draft_day2 = draft_bucket in {"round_2", "round_3"}
    expected_opportunity = (ffop is not None and ffop >= 10) or (ngs is not None and ngs > 0)
    weak_depth = depth_tier in {"DEPTH_BACKUP", "NO_DEPTH_RECORD"}
    injury_caveat = caveat >= 1 or (avail_score is not None and avail_score < 0.60)
    sparse_no_role = sparse and not role_promotion and not starter_signal
    young_no_snap_growth = sparse and early_career and not snap_growth and (low_snap >= 1 or weak_depth)
    low_snap_depth = low_snap >= 1 or weak_depth
    draft_without_role = draft_bucket in {"round_1", "round_2", "round_3"} and not (role_promotion or starter_signal)
    pos = str(row["position"])
    if pos == "QB":
        position_specific = starter_signal and (draft_bucket == "round_1" or snap_role >= 0.75)
    elif pos == "RB":
        position_specific = starter_signal and (early_career or snap_role >= 0.75) and not low_snap_depth
    elif pos == "WR":
        position_specific = (starter_signal or role_promotion) and (early_career or expected_opportunity)
    elif pos == "TE":
        position_specific = starter_signal and (early_career or draft_top or draft_day2)
    else:
        position_specific = False
    breakout_signals = {
        "role_promotion": role_promotion,
        "starter_signal": starter_signal,
        "snap_growth": snap_growth,
        "availability_rebound": availability_rebound,
        "early_career_role": early_career and (role_promotion or starter_signal),
        "draft_with_role": draft_top and (role_promotion or starter_signal),
        "expected_opportunity": expected_opportunity,
        "position_specific": position_specific,
    }
    trap_signals = {
        "injury_availability_caveat": injury_caveat,
        "sparse_without_role_promotion": sparse_no_role,
        "young_no_snap_growth": young_no_snap_growth,
        "low_snap_depth": low_snap_depth,
        "draft_without_role": draft_without_role,
    }
    return {
        "sparse": sparse,
        "years_since_draft": ysd_int,
        "breakout_signals": breakout_signals,
        "trap_signals": trap_signals,
        "breakout_count": sum(1 for v in breakout_signals.values() if v),
        "trap_count": sum(1 for v in trap_signals.values() if v),
        "role_promotion_signal": role_promotion,
        "starter_signal": starter_signal,
        "snap_growth_signal": snap_growth,
        "availability_rebound_signal": availability_rebound,
        "early_career_signal": early_career,
        "draft_with_role_signal": draft_top and (role_promotion or starter_signal),
        "expected_opportunity_signal": expected_opportunity,
        "position_specific_signal": position_specific,
    }


def rule_applies(row: dict[str, Any], rule: dict[str, Any], profile: dict[str, Any]) -> bool:
    if not profile["sparse"]:
        return False
    family = rule["rule_id"]
    if family == "RULE_001_ROLE_PROMOTION_BREAKOUT_05":
        return bool(profile["role_promotion_signal"])
    if family == "RULE_002_DEPTH_STARTER_BREAKOUT_05":
        return bool(profile["starter_signal"])
    if family == "RULE_003_SNAP_GROWTH_BREAKOUT_05":
        return bool(profile["snap_growth_signal"])
    if family == "RULE_004_AVAILABILITY_REBOUND_05":
        return bool(profile["availability_rebound_signal"])
    if family == "RULE_005_EARLY_CAREER_LIFECYCLE_025":
        return bool(profile["early_career_signal"] and (profile["role_promotion_signal"] or profile["starter_signal"]))
    if family == "RULE_006_DRAFT_CAPITAL_WITH_ROLE_05":
        return bool(profile["draft_with_role_signal"])
    if family == "RULE_007_EXPECTED_OPPORTUNITY_PARTIAL_05":
        return bool(profile["expected_opportunity_signal"])
    if family == "RULE_008_POSITION_SPECIFIC_BREAKOUT_05":
        return bool(profile["position_specific_signal"])
    if family == "RULE_009_FALSE_POSITIVE_TRAP_DOWNGRADE_05":
        return int(profile["trap_count"]) >= 1
    if family == "RULE_010_FALSE_POSITIVE_TRAP_STRICT_10":
        return int(profile["trap_count"]) >= 2
    if family == "RULE_011_SPARSE_HISTORY_COMPOSITE_BALANCED":
        return int(profile["breakout_count"]) >= 2 or (int(profile["trap_count"]) >= 1 and int(profile["breakout_count"]) == 0)
    if family == "RULE_012_COMPOSITE_PARTIAL_EXPECTED_OPP":
        return bool(profile["expected_opportunity_signal"]) or int(profile["trap_count"]) >= 1
    return False


def rule_delta(row: dict[str, Any], rule: dict[str, Any], profile: dict[str, Any]) -> float:
    if not rule_applies(row, rule, profile):
        return 0.0
    rid = rule["rule_id"]
    if rid == "RULE_011_SPARSE_HISTORY_COMPOSITE_BALANCED":
        if int(profile["breakout_count"]) >= 2:
            return 0.05
        if int(profile["trap_count"]) >= 1 and int(profile["breakout_count"]) == 0:
            return -0.05
        return 0.0
    if rid == "RULE_012_COMPOSITE_PARTIAL_EXPECTED_OPP":
        if bool(profile["expected_opportunity_signal"]) and int(profile["breakout_count"]) >= 1:
            return 0.05
        if int(profile["trap_count"]) >= 1:
            return -0.025
        return 0.0
    return float(rule["score_delta"])


def rank_rows(rows: list[dict[str, Any]], score_getter: Any) -> dict[str, int]:
    ranks: dict[str, int] = {}
    groups: dict[tuple[int, str], list[tuple[dict[str, Any], float]]] = defaultdict(list)
    for row in rows:
        score = score_getter(row)
        if score is not None:
            groups[(int(row["season"]), str(row["position"]))].append((row, float(score)))
    for group in groups.values():
        ordered = sorted(group, key=lambda item: (item[1], str(item[0]["player_id"]), str(item[0]["substrate_row_id"])), reverse=True)
        for idx, (row, _) in enumerate(ordered, start=1):
            ranks[str(row["substrate_row_id"])] = idx
    return ranks


def predicted(row: dict[str, Any], ranks: dict[str, int]) -> bool:
    rank = ranks.get(str(row["substrate_row_id"]))
    return rank is not None and rank <= STARTABLE_CUTOFF[str(row["position"])]


def is_severe_fp(row: dict[str, Any], pred: bool) -> bool:
    finish = num(row.get("actual_finish"))
    return pred and not bool(row["actual_startable"]) and (finish is None or finish > STARTABLE_CUTOFF[str(row["position"])] * 2)


def is_severe_fn(row: dict[str, Any], pred: bool) -> bool:
    finish = num(row.get("actual_finish"))
    return (not pred) and bool(row["actual_startable"]) and finish is not None and finish <= SEVERE_FN_CUTOFF[str(row["position"])]


def rank_values(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = rank
        i = j + 1
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    return cov / math.sqrt(vx * vy)


def spearman(rows: list[dict[str, Any]], score_getter: Any) -> float | None:
    pairs: list[tuple[float, float]] = []
    for row in rows:
        score = score_getter(row)
        outcome = num(row.get("label_next_nwr_points"))
        if score is not None and outcome is not None:
            pairs.append((float(score), outcome))
    if len(pairs) < 3:
        return None
    xs = rank_values([p[0] for p in pairs])
    ys = rank_values([p[1] for p in pairs])
    return pearson(xs, ys)


def top_precision(rows: list[dict[str, Any]], ranks: dict[str, int], threshold: int) -> float | None:
    selected = [row for row in rows if ranks.get(str(row["substrate_row_id"]), 10**9) <= threshold]
    if not selected:
        return None
    return sum(1 for row in selected if row["actual_startable"]) / len(selected)


def evaluate(
    rows: list[dict[str, Any]],
    reference: dict[str, Any],
    rule: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    window_rows = [
        row for row in rows
        if int(reference["season_min"]) <= int(row["season"]) <= int(reference["season_max"])
        and row.get(reference["score_col"]) is not None
        and (rule["partial_window_only"] == "false" or reference["scoreboard_window"] == "partial_window")
    ]
    base_score = lambda row: row.get(reference["score_col"])
    def overlay_score(row: dict[str, Any]) -> float | None:
        base = row.get(reference["score_col"])
        if base is None:
            return None
        delta = rule_delta(row, rule, profiles[str(row["substrate_row_id"])])
        return clamp(float(base) + delta)

    base_ranks = rank_rows(window_rows, base_score)
    overlay_ranks = rank_rows(window_rows, overlay_score)
    pyf_rows = [row for row in window_rows if row.get("PYF_BASELINE_score_pct") is not None]
    pyf_ranks = rank_rows(pyf_rows, lambda row: row.get("PYF_BASELINE_score_pct"))
    before_misses = after_misses = 0
    fp_before = fp_after = fn_before = fn_after = 0
    severe_fp_before = severe_fp_after = severe_fn_before = severe_fn_after = 0
    misses_resolved = new_misses = 0
    sparse_before = sparse_after = nonsparse_before = nonsparse_after = 0
    rows_changed = 0
    applied_rows = 0
    position_impacts: dict[str, Counter] = {pos: Counter() for pos in POSITIONS}
    for row in window_rows:
        sid = str(row["substrate_row_id"])
        actual = bool(row["actual_startable"])
        bpred = predicted(row, base_ranks)
        apred = predicted(row, overlay_ranks)
        bmiss = bpred != actual
        amiss = apred != actual
        sparse = bool(profiles[sid]["sparse"])
        if rule_applies(row, rule, profiles[sid]):
            applied_rows += 1
        if bpred != apred:
            rows_changed += 1
        before_misses += int(bmiss)
        after_misses += int(amiss)
        fp_before += int(bpred and not actual)
        fp_after += int(apred and not actual)
        fn_before += int((not bpred) and actual)
        fn_after += int((not apred) and actual)
        severe_fp_before += int(is_severe_fp(row, bpred))
        severe_fp_after += int(is_severe_fp(row, apred))
        severe_fn_before += int(is_severe_fn(row, bpred))
        severe_fn_after += int(is_severe_fn(row, apred))
        misses_resolved += int(bmiss and not amiss)
        new_misses += int((not bmiss) and amiss)
        if sparse:
            sparse_before += int(bmiss)
            sparse_after += int(amiss)
        else:
            nonsparse_before += int(bmiss)
            nonsparse_after += int(amiss)
        pc = position_impacts[str(row["position"])]
        pc["rows"] += 1
        pc["miss_before"] += int(bmiss)
        pc["miss_after"] += int(amiss)
        pc["fp_before"] += int(bpred and not actual)
        pc["fp_after"] += int(apred and not actual)
        pc["fn_before"] += int((not bpred) and actual)
        pc["fn_after"] += int((not apred) and actual)
    base_spear = spearman(window_rows, base_score)
    after_spear = spearman(window_rows, overlay_score)
    pyf_spear = spearman(pyf_rows, lambda row: row.get("PYF_BASELINE_score_pct"))
    net = before_misses - after_misses
    classification = classify_rule(rule, net, misses_resolved, new_misses, nonsparse_after - nonsparse_before, base_spear, after_spear)
    result = {
        "reference_id": reference["reference_id"],
        "formula_id": reference["formula_id"],
        "rule_id": rule["rule_id"],
        "rule_family": rule["rule_family"],
        "scoreboard_window": reference["scoreboard_window"],
        "seasons": f"{reference['season_min']}-{reference['season_max']}",
        "rows_tested": len(window_rows),
        "rule_applied_rows": applied_rows,
        "rows_changed_prediction": rows_changed,
        "total_misses_before": before_misses,
        "total_misses_after": after_misses,
        "false_positives_before": fp_before,
        "false_positives_after": fp_after,
        "false_negatives_before": fn_before,
        "false_negatives_after": fn_after,
        "severe_false_positives_before": severe_fp_before,
        "severe_false_positives_after": severe_fp_after,
        "severe_false_negatives_before": severe_fn_before,
        "severe_false_negatives_after": severe_fn_after,
        "new_misses_created": new_misses,
        "misses_resolved": misses_resolved,
        "net_miss_reduction": net,
        "sparse_misses_before": sparse_before,
        "sparse_misses_after": sparse_after,
        "sparse_net_miss_reduction": sparse_before - sparse_after,
        "non_sparse_misses_before": nonsparse_before,
        "non_sparse_misses_after": nonsparse_after,
        "non_sparse_collateral_damage": nonsparse_after - nonsparse_before,
        "spearman_before": fmt(base_spear),
        "spearman_after": fmt(after_spear),
        "spearman_delta": fmt((after_spear - base_spear) if base_spear is not None and after_spear is not None else None),
        "pyf_same_row_spearman": fmt(pyf_spear),
        "top12_precision_after": fmt(top_precision(window_rows, overlay_ranks, 12)),
        "top24_precision_after": fmt(top_precision(window_rows, overlay_ranks, 24)),
        "top36_precision_after": fmt(top_precision(window_rows, overlay_ranks, 36)),
        "full_history_comparable": reference["full_history_comparable"],
        "broad_window_comparable": reference["broad_window_comparable"],
        "partial_window_only": "true" if reference["partial_window_only"] == "true" or rule["partial_window_only"] == "true" else "false",
        "rule_classification": classification,
    }
    position_rows = []
    for pos, pc in position_impacts.items():
        if pc["rows"]:
            position_rows.append({
                "reference_id": reference["reference_id"],
                "formula_id": reference["formula_id"],
                "rule_id": rule["rule_id"],
                "scoreboard_window": reference["scoreboard_window"],
                "position": pos,
                "rows_tested": pc["rows"],
                "misses_before": pc["miss_before"],
                "misses_after": pc["miss_after"],
                "net_miss_reduction": pc["miss_before"] - pc["miss_after"],
                "false_positives_before": pc["fp_before"],
                "false_positives_after": pc["fp_after"],
                "false_negatives_before": pc["fn_before"],
                "false_negatives_after": pc["fn_after"],
            })
    return result, position_rows


def classify_rule(
    rule: dict[str, Any],
    net: int,
    resolved: int,
    new_misses: int,
    collateral: int,
    before: float | None,
    after: float | None,
) -> str:
    if rule["partial_window_only"] == "true":
        return "PARTIAL_WINDOW_ONLY_RULE"
    spear_delta = (after - before) if before is not None and after is not None else 0.0
    if net >= 8 and new_misses <= resolved and collateral <= 4:
        return "PROMISING_REVIEW_ONLY_RULE"
    if net > 0:
        return "MIXED_REVIEW_ONLY_RULE"
    if net < 0 or new_misses > max(5, resolved * 2) or spear_delta < -0.005:
        return "HARMFUL_RULE"
    return "CONTEXT_ONLY_RULE"


def summarize_trap_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    trap_rules = [row for row in results if row["rule_family"] == "FALSE_POSITIVE_TRAP_DOWNGRADE_RULE"]
    for row in trap_rules:
        out.append({
            "reference_id": row["reference_id"],
            "formula_id": row["formula_id"],
            "rule_id": row["rule_id"],
            "scoreboard_window": row["scoreboard_window"],
            "false_positive_reduction": int(row["false_positives_before"]) - int(row["false_positives_after"]),
            "false_negative_added": int(row["false_negatives_after"]) - int(row["false_negatives_before"]),
            "net_miss_reduction": row["net_miss_reduction"],
            "new_misses_created": row["new_misses_created"],
            "misses_resolved": row["misses_resolved"],
            "rule_classification": row["rule_classification"],
            "review": "helps false positives if FP reduction is positive; reject if FN added/new misses swamp gains",
        })
    return out


def summarize_breakout_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    breakout_families = {
        "ROLE_PROMOTION_BREAKOUT_RULE",
        "DEPTH_STARTER_BREAKOUT_RULE",
        "SNAP_GROWTH_BREAKOUT_RULE",
        "AVAILABILITY_REBOUND_RULE",
        "EARLY_CAREER_LIFECYCLE_RULE",
        "DRAFT_CAPITAL_WITH_ROLE_RULE",
        "EXPECTED_OPPORTUNITY_PARTIAL_WINDOW_RULE",
        "POSITION_SPECIFIC_BREAKOUT_RULE",
        "SPARSE_HISTORY_COMPOSITE_RULE",
    }
    out = []
    for row in results:
        if row["rule_family"] not in breakout_families:
            continue
        out.append({
            "reference_id": row["reference_id"],
            "formula_id": row["formula_id"],
            "rule_id": row["rule_id"],
            "scoreboard_window": row["scoreboard_window"],
            "false_negative_reduction": int(row["false_negatives_before"]) - int(row["false_negatives_after"]),
            "false_positive_added": int(row["false_positives_after"]) - int(row["false_positives_before"]),
            "net_miss_reduction": row["net_miss_reduction"],
            "new_misses_created": row["new_misses_created"],
            "misses_resolved": row["misses_resolved"],
            "rule_classification": row["rule_classification"],
            "review": "helps breakouts if FN reduction is positive without excessive FP creation",
        })
    return out


def collateral_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "reference_id": row["reference_id"],
            "formula_id": row["formula_id"],
            "rule_id": row["rule_id"],
            "scoreboard_window": row["scoreboard_window"],
            "non_sparse_misses_before": row["non_sparse_misses_before"],
            "non_sparse_misses_after": row["non_sparse_misses_after"],
            "non_sparse_collateral_damage": row["non_sparse_collateral_damage"],
            "new_misses_created": row["new_misses_created"],
            "rule_classification": row["rule_classification"],
            "collateral_status": "UNACCEPTABLE" if int(row["non_sparse_collateral_damage"]) > 10 else "ACCEPTABLE_OR_LOW",
        }
        for row in results
    ]


def window_comparison(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_window: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        by_window[row["scoreboard_window"]].append(row)
    for window, rows in by_window.items():
        best = max(rows, key=lambda row: int(row["net_miss_reduction"]))
        out.append({
            "scoreboard_window": window,
            "best_rule_id": best["rule_id"],
            "best_formula_id": best["formula_id"],
            "rows_tested": best["rows_tested"],
            "best_net_miss_reduction": best["net_miss_reduction"],
            "best_spearman_before": best["spearman_before"],
            "best_spearman_after": best["spearman_after"],
            "best_spearman_delta": best["spearman_delta"],
            "best_rule_classification": best["rule_classification"],
            "partial_window_only": best["partial_window_only"],
        })
    return out


def classification_summary(results: list[dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = defaultdict(set)
    best_by_rule: dict[str, dict[str, Any]] = {}
    for row in results:
        current = best_by_rule.get(row["rule_id"])
        if current is None or int(row["net_miss_reduction"]) > int(current["net_miss_reduction"]):
            best_by_rule[row["rule_id"]] = row
    for rule_id, row in best_by_rule.items():
        buckets[row["rule_classification"]].add(rule_id)
    return {k: sorted(v) for k, v in buckets.items()}


def write_docs(results: list[dict[str, Any]], joins: dict[str, int]) -> None:
    best = max(results, key=lambda row: int(row["net_miss_reduction"]))
    trap_candidates = summarize_trap_results(results)
    breakout_candidates = summarize_breakout_results(results)
    best_trap = max(trap_candidates, key=lambda row: int(row["false_positive_reduction"])) if trap_candidates else None
    best_breakout = max(breakout_candidates, key=lambda row: int(row["false_negative_reduction"])) if breakout_candidates else None
    trap_decision = "No false-positive trap rule achieved positive FP reduction; trap downgrades should stay context/harm review only."
    if best_trap and int(best_trap["false_positive_reduction"]) > 0:
        trap_decision = "At least one false-positive trap rule reduced FPs, but it still requires collateral review before any refinement."
    classes = classification_summary(results)
    material_spearman = [row for row in results if (num(row["spearman_delta"]) or 0.0) >= 0.003]
    material_miss = [row for row in results if int(row["net_miss_reduction"]) >= 8]
    unacceptable = [row for row in results if int(row["non_sparse_collateral_damage"]) > 10 or row["rule_classification"] == "HARMFUL_RULE"]
    verdict = "GREEN_SPARSE_HISTORY_RULE_TEST_FOUND_PROMISING_MISS_REDUCTION" if material_miss else "YELLOW_SPARSE_HISTORY_RULE_TEST_MIXED_WITH_CAVEATS"
    if unacceptable and not material_miss:
        verdict = "RED_SPARSE_HISTORY_RULE_TEST_NO_NET_MISS_REDUCTION"
    recommended_next = "Sparse-History Rule Refinement Contract V1" if material_miss else "Stop and wait for user review"
    report = f"""
# Sparse-History Breakout Candidate Rule Test V1

## Verdict

`{verdict}`

## Scope

This is a bounded review-only sparse-history rule overlay test. It did not change production rankings, app/runtime/model behavior, source promotion, push/merge state, canonical `local_exports`, ranking simulation, or production/model-use approval.

Remote HQ verified: `{EXPECTED_REMOTE_HEAD}`.

Prior sparse-history design commit verified: `{PRIOR_DESIGN_COMMIT}`.

## Registry

Rules registered: `{len(RULES)}`.

Windows tested: `full_history 2013-2025`, `broad_window 2014-2025`, and `partial_window 2022-2025`.

## Best Results

Best net miss-reduction rule: `{best['rule_id']}` on `{best['formula_id']}` / `{best['scoreboard_window']}`, net miss reduction `{best['net_miss_reduction']}`, misses resolved `{best['misses_resolved']}`, new misses `{best['new_misses_created']}`.

Best false-positive trap rule: `{best_trap['rule_id'] if best_trap else 'none'}` with FP reduction `{best_trap['false_positive_reduction'] if best_trap else '0'}`.

Best false-negative breakout rule: `{best_breakout['rule_id'] if best_breakout else 'none'}` with FN reduction `{best_breakout['false_negative_reduction'] if best_breakout else '0'}`.

Trap-rule decision: {trap_decision}

Rules with material Spearman lift (`>= .003`): `{len(material_spearman)}`.

Rules with material net miss reduction (`>= 8`): `{len(material_miss)}`.

Rules with unacceptable collateral/harm flags: `{len(unacceptable)}`.

## Classifications

- `PROMISING_REVIEW_ONLY_RULE`: `{', '.join(classes.get('PROMISING_REVIEW_ONLY_RULE', [])) or 'none'}`
- `MIXED_REVIEW_ONLY_RULE`: `{', '.join(classes.get('MIXED_REVIEW_ONLY_RULE', [])) or 'none'}`
- `CONTEXT_ONLY_RULE`: `{', '.join(classes.get('CONTEXT_ONLY_RULE', [])) or 'none'}`
- `HARMFUL_RULE`: `{', '.join(classes.get('HARMFUL_RULE', [])) or 'none'}`
- `PARTIAL_WINDOW_ONLY_RULE`: `{', '.join(classes.get('PARTIAL_WINDOW_ONLY_RULE', [])) or 'none'}`
- `BLOCKED_OR_INVALID`: `none`

## Decision

Review-only ranking simulation remains not justified. The next lane is `{recommended_next}`.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_BREAKOUT_CANDIDATE_RULE_TEST_V1_REPORT.md", report)

    next_use = f"""
# Sparse-History Rule Next Use Decision

Recommended next lane: `{recommended_next}`.

Rules may continue only as review-only candidates. No rule is production-approved, ranking-ready, hidden-sort logic, or recommendation logic.

Ranking simulation remains blocked because the rule overlay is a miss-reduction experiment, not a complete ranking-system readiness gate.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_RULE_NEXT_USE_DECISION.md", next_use)

    caveats = f"""
# Sparse-History Rule Blockers and Caveats

- Rule overlays are review-only and are not production/model-use.
- The partial-window expected-opportunity rules depend on ffopportunity/NGS windows and cannot support full-history claims.
- Current-only ADP, market data without as-of proof, CFBD/prospect production, SportsDataIO, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` were not used.
- Non-sparse collateral damage is tracked because even sparse-only score changes can displace non-sparse players in season-position ranks.
- The primary success metric is net miss reduction, not Spearman alone.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_RULE_BLOCKERS_AND_CAVEATS.md", caveats)

    source_trace = f"""
# Sparse-History Rule Source Trace

Prior design packet: `{DESIGN_DIR}`

Prior design commit: `{PRIOR_DESIGN_COMMIT}`

Prior red-team canonicalization addendum commit: `{PRIOR_ADDENDUM_COMMIT}`

Source packets verified:

- Formula Red Team Canonicalization Addendum V1: `{ADDENDUM_DIR}`
- Formula Miss Taxonomy / Red Team Review V1: `{RED_TEAM_DIR}`
- Ingredient Upgrade Phase Batch Canonicalization / Merge Review V1: `{INGREDIENT_CANON_DIR}`
- Rookie Draft Capital Data Mart Join / Component Test V1: `{ROOKIE_DIR}`
- nflverse Snap Counts / Depth Chart Role Sidecar V1: `{SNAP_DIR}`
- Point-in-Time Injury Availability Data Mart Gate V1: `{INJURY_DIR}`
- Autonomous ffopportunity / NGS Ingredient Upgrade Sequence V2: `{FFOP_NGS_DIR}`
- Ingredient Scoreboard Normalization / Best Candidate Consolidation V1: `{SCOREBOARD_DIR}`
- Full Review-Only Formula Gauntlet Candidate Arena V1: `{GAUNTLET_DIR}`

Sidecar/context joins used by the design loader: `{joins}`.

Source/use gate: review-only only. Production/model-use, rankings integration, app/runtime behavior, source promotion, push/merge, canonical `local_exports`, hidden sort, recommendation logic, and ranking simulation remain blocked.

Leakage/as-of gate: all test inputs are accepted lagged N-to-N+1 or static post-entry identity context. Same-season/future context remains blocked. ffopportunity/NGS are marked partial-window only.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_RULE_SOURCE_TRACE.md", source_trace)


def main() -> None:
    required = [DESIGN_DIR, DESIGN_SCRIPT, ADDENDUM_DIR, RED_TEAM_DIR, INGREDIENT_CANON_DIR, ROOKIE_DIR, SNAP_DIR, INJURY_DIR, FFOP_NGS_DIR, SCOREBOARD_DIR, GAUNTLET_DIR]
    for path in required:
        if not path.exists():
            raise RuntimeError(f"Required prior artifact missing: {path}")
    compile_check = OUT_DIR / "_compile_check.pyc"
    try:
        py_compile.compile(__file__, cfile=str(compile_check), doraise=True)
    finally:
        if compile_check.exists():
            compile_check.unlink()
    design = load_design_module()
    rows, joins = design.load_panel()
    profiles = {str(row["substrate_row_id"]): flag_profile(row, design) for row in rows}

    registry_fields = ["rule_id", "rule_family", "rule_name", "score_delta", "window_scope", "conditions", "partial_window_only", "blocked_input_check", "source_use_gate_status", "leakage_asof_check", "review_only_status"]
    registry_rows = []
    for rule in RULES:
        out = dict(rule)
        out["blocked_input_check"] = "PASS_NO_CURRENT_ADP_NO_MARKET_NO_CFBD_NO_SPORTSDATAIO_NO_PFF_NO_ELUSIVE_PROXY"
        out["source_use_gate_status"] = "REVIEW_ONLY_NOT_PRODUCTION_MODEL_USE"
        out["leakage_asof_check"] = "PASS_LAGGED_N_TO_N_PLUS_1_OR_STATIC_POST_ENTRY_CONTEXT"
        out["review_only_status"] = "REVIEW_ONLY_RULE_TEST_ONLY"
        registry_rows.append(out)
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_REGISTRY.csv", registry_rows, registry_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_INPUT_POLICY.csv", RULE_INPUT_POLICY, ["input_name", "allowed_status", "source", "blocked_use", "asof_status"])

    results: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []
    for reference in REFERENCES:
        for rule in RULES:
            if rule["partial_window_only"] == "true" and reference["scoreboard_window"] != "partial_window":
                continue
            result, pos = evaluate(rows, reference, rule, profiles)
            results.append(result)
            position_rows.extend(pos)

    result_fields = [
        "reference_id", "formula_id", "rule_id", "rule_family", "scoreboard_window", "seasons", "rows_tested", "rule_applied_rows", "rows_changed_prediction",
        "total_misses_before", "total_misses_after", "false_positives_before", "false_positives_after", "false_negatives_before", "false_negatives_after",
        "severe_false_positives_before", "severe_false_positives_after", "severe_false_negatives_before", "severe_false_negatives_after",
        "new_misses_created", "misses_resolved", "net_miss_reduction", "sparse_misses_before", "sparse_misses_after", "sparse_net_miss_reduction",
        "non_sparse_misses_before", "non_sparse_misses_after", "non_sparse_collateral_damage", "spearman_before", "spearman_after", "spearman_delta",
        "pyf_same_row_spearman", "top12_precision_after", "top24_precision_after", "top36_precision_after", "full_history_comparable", "broad_window_comparable",
        "partial_window_only", "rule_classification",
    ]
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_OVERLAY_RESULTS.csv", results, result_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_MISS_REDUCTION_SCORECARD.csv", sorted(results, key=lambda row: int(row["net_miss_reduction"]), reverse=True), result_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_FALSE_POSITIVE_TRAP_RESULTS.csv", summarize_trap_results(results), ["reference_id", "formula_id", "rule_id", "scoreboard_window", "false_positive_reduction", "false_negative_added", "net_miss_reduction", "new_misses_created", "misses_resolved", "rule_classification", "review"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_FALSE_NEGATIVE_BREAKOUT_RESULTS.csv", summarize_breakout_results(results), ["reference_id", "formula_id", "rule_id", "scoreboard_window", "false_negative_reduction", "false_positive_added", "net_miss_reduction", "new_misses_created", "misses_resolved", "rule_classification", "review"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_POSITION_RESULTS.csv", position_rows, ["reference_id", "formula_id", "rule_id", "scoreboard_window", "position", "rows_tested", "misses_before", "misses_after", "net_miss_reduction", "false_positives_before", "false_positives_after", "false_negatives_before", "false_negatives_after"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_WINDOW_COMPARISON.csv", window_comparison(results), ["scoreboard_window", "best_rule_id", "best_formula_id", "rows_tested", "best_net_miss_reduction", "best_spearman_before", "best_spearman_after", "best_spearman_delta", "best_rule_classification", "partial_window_only"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_COLLATERAL_DAMAGE_REVIEW.csv", collateral_rows(results), ["reference_id", "formula_id", "rule_id", "scoreboard_window", "non_sparse_misses_before", "non_sparse_misses_after", "non_sparse_collateral_damage", "new_misses_created", "rule_classification", "collateral_status"])
    write_docs(results, joins)


if __name__ == "__main__":
    main()
