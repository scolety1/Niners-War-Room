from __future__ import annotations

import csv
import importlib.util
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs/hq/model/overlay_candidate_batch_rule_test_v1_20260709"

REMOTE_HQ = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_OVERLAY_LIBRARY_COMMIT = "d9ec52781d682b7bee116b7896fef678b9df1552"
PRIOR_MANUAL_REVIEW_COMMIT = "5774ebdaa82cfd13c0e92e6afe4e62d1e0e70e99"
ACCEPTED_SPARSE_PRIMARY = "REFINE_005_A_EARLY_ROLE_015"
ACCEPTED_SPARSE_NET_MISS_REDUCTION = 16
ACCEPTED_SPARSE_FN_REDUCTION = 8

RED_SCRIPT = Path(
    r"C:\NWR\Niners-War-Room-formula-miss-taxonomy-red-team-review-v1-20260709"
    r"\docs\hq\model\formula_miss_taxonomy_red_team_review_v1_20260709"
    r"\build_formula_miss_taxonomy_red_team_review_v1.py"
)

STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
SEVERE_FN_CUTOFF = {"QB": 6, "RB": 18, "WR": 24, "TE": 6}


def ensure_out() -> None:
    OUT.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_md(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_red_module() -> Any:
    spec = importlib.util.spec_from_file_location("formula_red_team_v1", RED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import red-team script: {RED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value):
        return None
    return value


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "pass", "startable", "starter"}


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def row_id(row: dict[str, Any]) -> str:
    return str(row.get("substrate_row_id") or f"{row.get('season')}|{row.get('player_id')}|{row.get('position')}")


def rank_rows(rows: list[dict[str, Any]], score_getter: Callable[[dict[str, Any]], float | None]) -> dict[str, int]:
    groups: dict[tuple[int, str], list[tuple[str, float]]] = defaultdict(list)
    for row in rows:
        score = score_getter(row)
        if score is None:
            continue
        season = int(num(row.get("season")) or 0)
        position = str(row.get("position") or "")
        if season and position:
            groups[(season, position)].append((row_id(row), float(score)))
    ranks: dict[str, int] = {}
    for items in groups.values():
        items.sort(key=lambda item: item[1], reverse=True)
        for idx, (rid, _score) in enumerate(items, start=1):
            ranks[rid] = idx
    return ranks


def rank_pct_by_rank(rows: list[dict[str, Any]], rank_col: str, pct_col: str) -> None:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rank = num(row.get(rank_col))
        if rank is None:
            continue
        groups[(int(num(row.get("season")) or 0), str(row.get("position") or ""))].append(row)
    for group_rows in groups.values():
        max_rank = max(num(r.get(rank_col)) or 0 for r in group_rows)
        denom = max(max_rank - 1, 1)
        for row in group_rows:
            rank = num(row.get(rank_col)) or max_rank
            row[pct_col] = 1.0 - ((rank - 1.0) / denom)


def predicted(row: dict[str, Any], ranks: dict[str, int]) -> bool:
    rank = ranks.get(row_id(row))
    return rank is not None and rank <= STARTABLE_CUTOFF[str(row["position"])]


def actual_startable(row: dict[str, Any]) -> bool:
    return bool(row.get("actual_startable")) or boolish(row.get("label_startable_hit"))


def is_severe_fp(row: dict[str, Any], pred: bool) -> bool:
    finish = num(row.get("actual_finish") or row.get("label_next_position_finish"))
    return pred and not actual_startable(row) and (finish is None or finish > STARTABLE_CUTOFF[str(row["position"])] * 2)


def is_severe_fn(row: dict[str, Any], pred: bool) -> bool:
    finish = num(row.get("actual_finish") or row.get("label_next_position_finish"))
    return (not pred) and actual_startable(row) and finish is not None and finish <= SEVERE_FN_CUTOFF[str(row["position"])]


def miss_sets(rows: list[dict[str, Any]], ranks: dict[str, int]) -> tuple[set[str], set[str], set[str], set[str]]:
    fp: set[str] = set()
    fn: set[str] = set()
    severe_fp: set[str] = set()
    severe_fn: set[str] = set()
    for row in rows:
        pred = predicted(row, ranks)
        actual = actual_startable(row)
        rid = row_id(row)
        if pred and not actual:
            fp.add(rid)
        elif (not pred) and actual:
            fn.add(rid)
        if is_severe_fp(row, pred):
            severe_fp.add(rid)
        if is_severe_fn(row, pred):
            severe_fn.add(rid)
    return fp, fn, severe_fp, severe_fn


def rank_values(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    idx = 0
    while idx < len(indexed):
        j = idx + 1
        while j < len(indexed) and indexed[j][1] == indexed[idx][1]:
            j += 1
        avg = (idx + 1 + j) / 2.0
        for k in range(idx, j):
            ranks[indexed[k][0]] = avg
        idx = j
    return ranks


def spearman(rows: list[dict[str, Any]], score_getter: Callable[[dict[str, Any]], float | None]) -> float | None:
    pairs: list[tuple[float, float]] = []
    for row in rows:
        score = score_getter(row)
        actual = num(row.get("actual_points") or row.get("label_next_nwr_points"))
        if score is None or actual is None:
            continue
        pairs.append((float(score), float(actual)))
    if len(pairs) < 3:
        return None
    sx = rank_values([p[0] for p in pairs])
    sy = rank_values([p[1] for p in pairs])
    mx = sum(sx) / len(sx)
    my = sum(sy) / len(sy)
    cov = sum((x - mx) * (y - my) for x, y in zip(sx, sy))
    vx = sum((x - mx) ** 2 for x in sx)
    vy = sum((y - my) ** 2 for y in sy)
    if vx <= 0 or vy <= 0:
        return None
    return cov / math.sqrt(vx * vy)


def role_signal(row: dict[str, Any], threshold: float = 0.60) -> bool:
    candidates = [
        num(row.get("snapdepth_snap_role_score_pct")),
        num(row.get("snapdepth_depth_role_score_pct")),
        num(row.get("snapdepth_snap_depth_role_score_pct")),
        num(row.get("snapdepth_snap_offensive_snap_share_pct")),
        num(row.get("snapdepth_depth_weeks_as_starter_pct")),
    ]
    tier = str(row.get("snapdepth_depth_role_tier") or "").lower()
    rank = num(row.get("snapdepth_depth_best_depth_rank"))
    return any(v is not None and v >= threshold for v in candidates) or "starter" in tier or (rank is not None and rank <= 1.5)


def starter_signal(row: dict[str, Any]) -> bool:
    return role_signal(row, 0.70) or (num(row.get("snapdepth_depth_weeks_as_starter_pct")) or 0.0) >= 0.55


def early_career(row: dict[str, Any]) -> bool:
    lifecycle = str(row.get("lifecycle_bucket") or row.get("career_stage") or "").lower()
    age = num(row.get("age") or row.get("age_num"))
    years_since_draft = num(row.get("draft_years_since_draft"))
    return (
        boolish(row.get("draft_early_career_flag"))
        or boolish(row.get("draft_rookie_contract_window_flag"))
        or (years_since_draft is not None and 0 <= years_since_draft <= 3)
        or (age is not None and age <= 25.5)
        or "young" in lifecycle
        or "early" in lifecycle
    )


def sparse_history(row: dict[str, Any]) -> bool:
    prior_games = num(row.get("prior_games") or row.get("prior_games_num"))
    prior_points = num(row.get("pyf_prior_nwr_points") or row.get("pyf_score"))
    return (
        boolish(row.get("sparse_history_flag"))
        or boolish(row.get("draft_sparse_history_flag"))
        or boolish(row.get("low_games_flag"))
        or boolish(row.get("low_games_bool"))
        or prior_games is None
        or prior_games <= 8
        or prior_points is None
        or prior_points < 80
    )


def low_prior_production(row: dict[str, Any], threshold: float = 100.0) -> bool:
    prior_points = num(row.get("pyf_prior_nwr_points") or row.get("pyf_score"))
    return prior_points is None or prior_points < threshold


def not_low_snap(row: dict[str, Any]) -> bool:
    low_flag = boolish(row.get("snapdepth_snap_low_snap_flag"))
    not_low_pct = num(row.get("snapdepth_snap_not_low_snap_score_pct"))
    return (not low_flag) and (not_low_pct is None or not_low_pct >= 0.45)


def availability_clean_or_rebound(row: dict[str, Any]) -> bool:
    missed = num(row.get("injury_avail_prior_year_missed_games")) or 0.0
    two_year = num(row.get("injury_avail_two_year_missed_games")) or 0.0
    active_pct = num(row.get("injury_avail_active_pct_pct")) or num(row.get("injury_avail_active_pct")) or 0.0
    avail_pct = num(row.get("injury_avail_availability_score_pct")) or 0.0
    caveat_inverse = num(row.get("injury_avail_caveat_inverse_score_pct")) or 0.0
    had_availability_issue = missed >= 2 or two_year >= 3 or boolish(row.get("injury_avail_caveat_flag"))
    clean_now = active_pct >= 0.70 or avail_pct >= 0.55 or caveat_inverse >= 0.55
    return had_availability_issue and clean_now


def draft_with_role(row: dict[str, Any]) -> bool:
    score_pct = num(row.get("draft_draft_capital_score_pct"))
    overall = num(row.get("draft_draft_overall"))
    drafted = boolish(row.get("draft_drafted_flag")) or score_pct is not None or overall is not None
    capital_ok = (score_pct is not None and score_pct >= 0.60) or (overall is not None and overall <= 100)
    return drafted and capital_ok and early_career(row) and role_signal(row, 0.55)


def overlay_001(row: dict[str, Any]) -> bool:
    return early_career(row) and sparse_history(row) and role_signal(row, 0.55) and not_low_snap(row)


def overlay_002(row: dict[str, Any]) -> bool:
    return availability_clean_or_rebound(row) and role_signal(row, 0.55)


def overlay_003(row: dict[str, Any]) -> bool:
    return low_prior_production(row, 110.0) and starter_signal(row)


def overlay_004(row: dict[str, Any]) -> bool:
    snap_role = num(row.get("snapdepth_snap_role_score_pct")) or 0.0
    snap_share = num(row.get("snapdepth_snap_offensive_snap_share_pct")) or 0.0
    games = num(row.get("snapdepth_snap_games_with_offensive_snaps_pct")) or 0.0
    return low_prior_production(row, 110.0) and not_low_snap(row) and (snap_role >= 0.65 or snap_share >= 0.55 or games >= 0.65)


def overlay_008(row: dict[str, Any]) -> bool:
    return draft_with_role(row)


OVERLAYS: list[dict[str, Any]] = [
    {
        "overlay_id": "OVERLAY_001_SPARSE_EARLY_ROLE_BREAKOUT",
        "miss_type_targeted": "sparse-history / early-career role breakout false negatives",
        "focus": "false_negative",
        "condition": overlay_001,
        "score_delta": 0.015,
        "eligible_population": "early-career or sparse-history players with role-promotion / starter-depth signal",
        "required_signals": "early-career lifecycle; sparse or low prior production; role/depth signal; not-low-snap context",
        "optional_signals": "availability rebound; expected opportunity partial-window; draft capital with role",
        "blocked_signals": "current-only ADP; market without as-of proof; CFBD/prospect production unless gated; inferred UDFA truth",
        "allowed_windows": "full_history_2013_2025;broad_window_2014_2025;partial_window_2022_2025",
        "partial_window_only": "no",
        "priority_order": 1,
        "expected_harm_risk": "young low-role overboost if role signal is weak",
        "stop_condition": "stop if severe false positives spike or non-target collateral damage is unacceptable",
    },
    {
        "overlay_id": "OVERLAY_002_AVAILABILITY_REBOUND",
        "miss_type_targeted": "availability-suppressed false negatives",
        "focus": "false_negative",
        "condition": overlay_002,
        "score_delta": 0.012,
        "eligible_population": "players with lagged availability issues and intact role context",
        "required_signals": "prior missed games or availability caveat; clean/rebound availability context; role intact",
        "optional_signals": "early-career lifecycle; role archetype; partial-window expected opportunity",
        "blocked_signals": "future injury status; same-season injury status; injury prediction claims",
        "allowed_windows": "full_history_2013_2025;broad_window_2014_2025;partial_window_2022_2025",
        "partial_window_only": "no",
        "priority_order": 2,
        "expected_harm_risk": "overtrusting fragile players without role support",
        "stop_condition": "stop if false positives or severe false positives spike",
    },
    {
        "overlay_id": "OVERLAY_003_STARTER_DEPTH_PROMOTION",
        "miss_type_targeted": "role-improvement false negatives",
        "focus": "false_negative",
        "condition": overlay_003,
        "score_delta": 0.012,
        "eligible_population": "low prior production players with starter/depth role evidence",
        "required_signals": "starter/depth rank or weeks as starter; low prior production",
        "optional_signals": "snap/depth score improvement; role archetype; early-career lifecycle",
        "blocked_signals": "target-season depth chart; current/future team context",
        "allowed_windows": "full_history_2013_2025;broad_window_2014_2025;partial_window_2022_2025",
        "partial_window_only": "no",
        "priority_order": 3,
        "expected_harm_risk": "boosting nominal starters without stable snaps",
        "stop_condition": "stop if new false positives exceed resolved misses",
    },
    {
        "overlay_id": "OVERLAY_004_SNAP_GROWTH_ROLE_PROMOTION",
        "miss_type_targeted": "role riser false negatives",
        "focus": "false_negative",
        "condition": overlay_004,
        "score_delta": 0.010,
        "eligible_population": "low prior points players with strong lagged snap/role score",
        "required_signals": "snap role score or snap share; not-low-snap context; low prior production",
        "optional_signals": "positive role archetype change; availability rebound",
        "blocked_signals": "same-season snap growth; true routes/YPRR/TPRR without gate",
        "allowed_windows": "full_history_2013_2025;broad_window_2014_2025;partial_window_2022_2025",
        "partial_window_only": "no",
        "priority_order": 4,
        "expected_harm_risk": "small-sample role spike overboost",
        "stop_condition": "stop if collateral damage to non-target populations is unacceptable",
    },
    {
        "overlay_id": "OVERLAY_008_DRAFT_CAPITAL_WITH_ROLE",
        "miss_type_targeted": "early-career sparse-history false negatives with role confirmation",
        "focus": "false_negative",
        "condition": overlay_008,
        "score_delta": 0.010,
        "eligible_population": "drafted early-career players with confirmed role signal",
        "required_signals": "draft capital bucket or overall pick; early-career window; starter/depth or snap role signal",
        "optional_signals": "availability clean context; position-specific profile",
        "blocked_signals": "draft capital alone; UDFA inference without evidence; CFBD/prospect production unless gated",
        "allowed_windows": "full_history_2013_2025;broad_window_2014_2025;partial_window_2022_2025",
        "partial_window_only": "no",
        "priority_order": 5,
        "expected_harm_risk": "pedigree overboost without actual role",
        "stop_condition": "stop if draft-capital-without-role harm appears",
    },
]

PRIMARY_POLICY_ID = "PRIMARY_POLICY_NONSTACKING_DISCOVERY_PRIORITY"


REFERENCES = [
    {
        "reference_id": "PYF_BASELINE",
        "formula_id": "PYF_BASELINE",
        "score_col": "PYF_BASELINE_score_pct",
        "window": "full_history_2013_2025",
        "season_min": 2013,
        "season_max": 2025,
    },
    {
        "reference_id": "BEST_FULL_HISTORY",
        "formula_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100",
        "score_col": "BEST_FULL_HISTORY_score",
        "window": "full_history_2013_2025",
        "season_min": 2013,
        "season_max": 2025,
    },
    {
        "reference_id": "BEST_BROAD_WINDOW",
        "formula_id": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100",
        "score_col": "BEST_BROAD_WINDOW_score",
        "window": "broad_window_2014_2025",
        "season_min": 2014,
        "season_max": 2025,
    },
    {
        "reference_id": "BEST_PARTIAL_WINDOW",
        "formula_id": "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10",
        "score_col": "BEST_PARTIAL_WINDOW_score",
        "window": "partial_window_2022_2025",
        "season_min": 2022,
        "season_max": 2025,
    },
    {
        "reference_id": "SPARSE_HISTORY_PRIMARY_BENCHMARK",
        "formula_id": "REFINE_005_A_EARLY_ROLE_015",
        "score_col": "SPARSE_HISTORY_PRIMARY_score",
        "window": "full_history_2013_2025",
        "season_min": 2013,
        "season_max": 2025,
    },
]


def scope_rows(rows: list[dict[str, Any]], ref: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        season = int(num(row.get("season")) or 0)
        if season < int(ref["season_min"]) or season > int(ref["season_max"]):
            continue
        if num(row.get(ref["score_col"])) is None:
            continue
        if num(row.get("actual_points") or row.get("label_next_nwr_points")) is None:
            continue
        out.append(row)
    return out


def eligible_overlays(row: dict[str, Any]) -> list[dict[str, Any]]:
    hits = [overlay for overlay in OVERLAYS if overlay["condition"](row)]
    return sorted(hits, key=lambda item: int(item["priority_order"]))


def primary_overlay(row: dict[str, Any]) -> dict[str, Any] | None:
    hits = eligible_overlays(row)
    return hits[0] if hits else None


def adjusted_score(row: dict[str, Any], ref: dict[str, Any], overlay: dict[str, Any] | None, primary_policy: bool = False) -> float | None:
    base = num(row.get(ref["score_col"]))
    if base is None:
        return None
    selected = primary_overlay(row) if primary_policy else overlay
    if selected is None:
        return float(base)
    if selected["condition"](row):
        return clamp(float(base) + float(selected["score_delta"]))
    return float(base)


def classify(result: dict[str, Any]) -> str:
    net = int(result["net_miss_reduction"])
    resolved = int(result["misses_resolved"])
    new = int(result["new_misses_created"])
    severe_fp_reduction = int(result["severe_false_positive_reduction"])
    collateral = int(result["non_target_collateral_damage"])
    sp_delta = float(result["spearman_delta"])
    partial_only = str(result.get("partial_window_only", "no")) == "yes"
    if partial_only and net > 0 and resolved > new and sp_delta >= -0.003:
        return "PARTIAL_WINDOW_ONLY_OVERLAY"
    if net >= 12 and resolved > new and severe_fp_reduction >= -2 and collateral <= max(8, resolved // 2) and sp_delta >= -0.003:
        return "PROMISING_REVIEW_ONLY_OVERLAY"
    if net > 0 and resolved >= new and sp_delta >= -0.006:
        return "MIXED_REVIEW_ONLY_OVERLAY"
    if net == 0 and resolved > 0:
        return "CONTEXT_ONLY_OVERLAY"
    if net < 0 or sp_delta < -0.006:
        return "HARMFUL_OVERLAY"
    return "CONTEXT_ONLY_OVERLAY"


def evaluate(rows: list[dict[str, Any]], ref: dict[str, Any], overlay: dict[str, Any] | None, primary_policy: bool = False) -> dict[str, Any]:
    scoped = scope_rows(rows, ref)
    before_ranks = rank_rows(scoped, lambda r: num(r.get(ref["score_col"])))
    after_ranks = rank_rows(scoped, lambda r: adjusted_score(r, ref, overlay, primary_policy=primary_policy))
    before_fp, before_fn, before_sfp, before_sfn = miss_sets(scoped, before_ranks)
    after_fp, after_fn, after_sfp, after_sfn = miss_sets(scoped, after_ranks)
    before_misses = before_fp | before_fn
    after_misses = after_fp | after_fn
    resolved = before_misses - after_misses
    new = after_misses - before_misses
    if primary_policy:
        applied = [row for row in scoped if primary_overlay(row) is not None]
        overlay_id = PRIMARY_POLICY_ID
        overlay_focus = "mixed"
        delta = "priority"
        partial_window_only = "no"
        overlay_family = "primary non-stacking policy"
    else:
        assert overlay is not None
        applied = [row for row in scoped if overlay["condition"](row)]
        overlay_id = overlay["overlay_id"]
        overlay_focus = overlay["focus"]
        delta = overlay["score_delta"]
        partial_window_only = overlay["partial_window_only"]
        overlay_family = overlay["miss_type_targeted"]
    applied_ids = {row_id(r) for r in applied}
    before_sp = spearman(scoped, lambda r: num(r.get(ref["score_col"])))
    after_sp = spearman(scoped, lambda r: adjusted_score(r, ref, overlay, primary_policy=primary_policy))
    non_target_new = {rid for rid in new if rid not in applied_ids}
    target_rows = len(applied)
    result = {
        "reference_id": ref["reference_id"],
        "formula_id": ref["formula_id"],
        "scoreboard_window": ref["window"],
        "overlay_id": overlay_id,
        "overlay_family": overlay_family,
        "overlay_focus": overlay_focus,
        "score_delta": delta,
        "rows_tested": len(scoped),
        "seasons_tested": f"{ref['season_min']}-{ref['season_max']}",
        "target_population_size": target_rows,
        "misses_before": len(before_misses),
        "misses_after": len(after_misses),
        "misses_resolved": len(resolved),
        "new_misses_created": len(new),
        "net_miss_reduction": len(resolved) - len(new),
        "resolved_new_ratio": f"{len(resolved) / max(len(new), 1):.3f}",
        "false_positives_before": len(before_fp),
        "false_positives_after": len(after_fp),
        "false_positive_reduction": len(before_fp) - len(after_fp),
        "false_negatives_before": len(before_fn),
        "false_negatives_after": len(after_fn),
        "false_negative_reduction": len(before_fn) - len(after_fn),
        "false_negatives_created": max(0, len(after_fn) - len(before_fn)),
        "severe_false_positives_before": len(before_sfp),
        "severe_false_positives_after": len(after_sfp),
        "severe_false_positive_reduction": len(before_sfp) - len(after_sfp),
        "severe_false_negatives_before": len(before_sfn),
        "severe_false_negatives_after": len(after_sfn),
        "severe_false_negative_reduction": len(before_sfn) - len(after_sfn),
        "severe_false_negatives_created": max(0, len(after_sfn) - len(before_sfn)),
        "non_target_collateral_damage": len(non_target_new),
        "sparse_history_new_misses": sum(1 for r in scoped if row_id(r) in new and sparse_history(r)),
        "non_sparse_new_misses": sum(1 for r in scoped if row_id(r) in new and not sparse_history(r)),
        "spearman_before": f"{before_sp:.3f}" if before_sp is not None else "",
        "spearman_after": f"{after_sp:.3f}" if after_sp is not None else "",
        "spearman_delta": f"{(after_sp - before_sp):.3f}" if before_sp is not None and after_sp is not None else "0.000",
        "partial_window_only": partial_window_only,
    }
    result["classification"] = classify(result)
    return result


def group_rows(rows: list[dict[str, Any]], ref: dict[str, Any], overlay: dict[str, Any] | None, group_key: str, primary_policy: bool = False) -> list[dict[str, Any]]:
    scoped = scope_rows(rows, ref)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scoped:
        grouped[str(row.get(group_key) or "unknown")].append(row)
    out = []
    for key, group in grouped.items():
        if len(group) < 5:
            continue
        before_ranks = rank_rows(group, lambda r: num(r.get(ref["score_col"])))
        after_ranks = rank_rows(group, lambda r: adjusted_score(r, ref, overlay, primary_policy=primary_policy))
        before_fp, before_fn, _before_sfp, _before_sfn = miss_sets(group, before_ranks)
        after_fp, after_fn, _after_sfp, _after_sfn = miss_sets(group, after_ranks)
        before_miss = before_fp | before_fn
        after_miss = after_fp | after_fn
        out.append(
            {
                "reference_id": ref["reference_id"],
                "formula_id": ref["formula_id"],
                "scoreboard_window": ref["window"],
                "overlay_id": PRIMARY_POLICY_ID if primary_policy else overlay["overlay_id"],
                group_key: key,
                "rows_tested": len(group),
                "misses_before": len(before_miss),
                "misses_after": len(after_miss),
                "net_miss_reduction": len(before_miss - after_miss) - len(after_miss - before_miss),
                "false_positive_reduction": len(before_fp) - len(after_fp),
                "false_negative_reduction": len(before_fn) - len(after_fn),
            }
        )
    return out


def eligibility_ledger(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        hits = eligible_overlays(row)
        if not hits:
            continue
        primary = hits[0]
        out.append(
            {
                "season": row.get("season"),
                "player_id": row.get("player_id"),
                "player_name": row.get("player_name"),
                "position": row.get("position"),
                "team": row.get("team"),
                "eligible_overlay_ids": ";".join(h["overlay_id"] for h in hits),
                "primary_overlay_id": primary["overlay_id"],
                "secondary_overlay_ids": ";".join(h["overlay_id"] for h in hits[1:]),
                "eligible_overlay_count": len(hits),
                "sparse_history_flag": sparse_history(row),
                "early_career_flag": early_career(row),
                "role_signal_flag": role_signal(row, 0.55),
                "starter_signal_flag": starter_signal(row),
                "availability_rebound_flag": availability_clean_or_rebound(row),
                "draft_with_role_flag": draft_with_role(row),
                "review_only_status": "REVIEW_ONLY_ELIGIBILITY_NOT_PRODUCTION_MODEL_USE",
            }
        )
    return out


def prepare_rows() -> list[dict[str, Any]]:
    red = load_red_module()
    rows, _joins = red.build_rows()
    rank_pct_by_rank(rows, "PYF_BASELINE_rank", "PYF_BASELINE_score_pct")
    # Preserve accepted sparse-history primary as its own benchmark reference. This is the predeclared
    # REFINE_005_A-style sparse early-role overlay applied to the best full-history score.
    for row in rows:
        base = num(row.get("BEST_FULL_HISTORY_score"))
        row["SPARSE_HISTORY_PRIMARY_score"] = clamp(base + 0.015) if base is not None and overlay_001(row) else base
    return rows


def write_registry() -> None:
    registry_rows = []
    for overlay in OVERLAYS:
        registry_rows.append(
            {
                "overlay_id": overlay["overlay_id"],
                "miss_type_targeted": overlay["miss_type_targeted"],
                "eligible_population": overlay["eligible_population"],
                "required_signals": overlay["required_signals"],
                "optional_signals": overlay["optional_signals"],
                "blocked_signals": overlay["blocked_signals"],
                "scoring_strength_adjustment_size": overlay["score_delta"],
                "allowed_windows": overlay["allowed_windows"],
                "partial_window_only_status": overlay["partial_window_only"],
                "priority_order": overlay["priority_order"],
                "expected_harm_risk": overlay["expected_harm_risk"],
                "stop_condition": overlay["stop_condition"],
                "source_use_gate_status": "REVIEW_ONLY_NOT_PRODUCTION_MODEL_USE",
                "leakage_asof_status": "PASS_LAGGED_REVIEW_ONLY_NO_SAME_SEASON_OR_FUTURE_CONTEXT",
                "registry_status": "FROZEN_BEFORE_SCORING",
            }
        )
    write_csv(
        OUT / "OVERLAY_BATCH_FROZEN_REGISTRY.csv",
        registry_rows,
        [
            "overlay_id",
            "miss_type_targeted",
            "eligible_population",
            "required_signals",
            "optional_signals",
            "blocked_signals",
            "scoring_strength_adjustment_size",
            "allowed_windows",
            "partial_window_only_status",
            "priority_order",
            "expected_harm_risk",
            "stop_condition",
            "source_use_gate_status",
            "leakage_asof_status",
            "registry_status",
        ],
    )
    input_policy = [
        {"input_group": "allowed", "input_detail": "lagged sparse-history flags age/lifecycle draft-with-role snap/depth role starter/depth injury availability context", "status": "REVIEW_ONLY_ALLOWED"},
        {"input_group": "partial_window", "input_detail": "ffopportunity / NGS expected opportunity only if separately partial-window labeled", "status": "PARTIAL_WINDOW_ONLY_NOT_USED_IN_THIS_FULL_BATCH"},
        {"input_group": "blocked", "input_detail": "current-only ADP market without as-of proof same-season/future context SportsDataIO paid API PFF Elusive nwr_elusive_proxy_review_only", "status": "BLOCKED"},
        {"input_group": "source_gate", "input_detail": "all inputs inherited from accepted review-only sidecars and red-team panel", "status": "PASS_REVIEW_ONLY_SOURCE_GATE"},
    ]
    write_csv(OUT / "OVERLAY_BATCH_INPUT_POLICY.csv", input_policy, ["input_group", "input_detail", "status"])


def main() -> None:
    ensure_out()
    write_registry()
    rows = prepare_rows()
    elig = eligibility_ledger(rows)
    write_csv(
        OUT / "OVERLAY_BATCH_ELIGIBILITY_LEDGER.csv",
        elig,
        [
            "season",
            "player_id",
            "player_name",
            "position",
            "team",
            "eligible_overlay_ids",
            "primary_overlay_id",
            "secondary_overlay_ids",
            "eligible_overlay_count",
            "sparse_history_flag",
            "early_career_flag",
            "role_signal_flag",
            "starter_signal_flag",
            "availability_rebound_flag",
            "draft_with_role_flag",
            "review_only_status",
        ],
    )

    results: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []
    lifecycle_rows: list[dict[str, Any]] = []
    for ref in REFERENCES:
        for overlay in OVERLAYS:
            result = evaluate(rows, ref, overlay)
            results.append(result)
            position_rows.extend(group_rows(rows, ref, overlay, "position"))
            lifecycle_rows.extend(group_rows(rows, ref, overlay, "lifecycle_bucket"))
        primary_result = evaluate(rows, ref, None, primary_policy=True)
        results.append(primary_result)
        position_rows.extend(group_rows(rows, ref, None, "position", primary_policy=True))
        lifecycle_rows.extend(group_rows(rows, ref, None, "lifecycle_bucket", primary_policy=True))

    result_fields = [
        "reference_id", "formula_id", "scoreboard_window", "overlay_id", "overlay_family", "overlay_focus", "score_delta",
        "rows_tested", "seasons_tested", "target_population_size", "misses_before", "misses_after", "misses_resolved",
        "new_misses_created", "net_miss_reduction", "resolved_new_ratio", "false_positives_before",
        "false_positives_after", "false_positive_reduction", "false_negatives_before", "false_negatives_after",
        "false_negative_reduction", "false_negatives_created", "severe_false_positives_before",
        "severe_false_positives_after", "severe_false_positive_reduction", "severe_false_negatives_before",
        "severe_false_negatives_after", "severe_false_negative_reduction", "severe_false_negatives_created",
        "non_target_collateral_damage", "sparse_history_new_misses", "non_sparse_new_misses", "spearman_before",
        "spearman_after", "spearman_delta", "partial_window_only", "classification",
    ]
    write_csv(OUT / "OVERLAY_BATCH_RULE_RESULTS.csv", results, result_fields)
    write_csv(OUT / "OVERLAY_BATCH_MISS_REDUCTION_SCORECARD.csv", sorted(results, key=lambda r: int(r["net_miss_reduction"]), reverse=True), result_fields)
    write_csv(
        OUT / "OVERLAY_BATCH_FALSE_POSITIVE_FALSE_NEGATIVE_RESULTS.csv",
        sorted(results, key=lambda r: (int(r["false_negative_reduction"]), int(r["false_positive_reduction"]), int(r["net_miss_reduction"])), reverse=True),
        [
            "reference_id", "formula_id", "scoreboard_window", "overlay_id", "false_positive_reduction",
            "false_negative_reduction", "false_negatives_created", "severe_false_positive_reduction",
            "severe_false_negative_reduction", "net_miss_reduction", "classification",
        ],
    )
    write_csv(
        OUT / "OVERLAY_BATCH_POSITION_RESULTS.csv",
        position_rows,
        ["reference_id", "formula_id", "scoreboard_window", "overlay_id", "position", "rows_tested", "misses_before", "misses_after", "net_miss_reduction", "false_positive_reduction", "false_negative_reduction"],
    )
    write_csv(
        OUT / "OVERLAY_BATCH_WINDOW_COMPARISON.csv",
        sorted(results, key=lambda r: (r["scoreboard_window"], int(r["net_miss_reduction"])), reverse=True),
        ["scoreboard_window", "reference_id", "formula_id", "overlay_id", "rows_tested", "seasons_tested", "target_population_size", "net_miss_reduction", "misses_resolved", "new_misses_created", "false_positive_reduction", "false_negative_reduction", "spearman_delta", "classification"],
    )
    write_csv(
        OUT / "OVERLAY_BATCH_COLLATERAL_DAMAGE_REVIEW.csv",
        sorted(results, key=lambda r: int(r["non_target_collateral_damage"]), reverse=True),
        ["reference_id", "formula_id", "scoreboard_window", "overlay_id", "new_misses_created", "non_target_collateral_damage", "sparse_history_new_misses", "non_sparse_new_misses", "severe_false_negatives_created", "classification"],
    )
    write_csv(
        OUT / "OVERLAY_BATCH_CLASSIFICATION.csv",
        sorted(results, key=lambda r: (r["classification"], r["overlay_id"], r["reference_id"])),
        ["overlay_id", "reference_id", "scoreboard_window", "classification", "net_miss_reduction", "false_positive_reduction", "false_negative_reduction", "non_target_collateral_damage", "spearman_delta"],
    )

    best_net = max(results, key=lambda r: int(r["net_miss_reduction"]))
    best_fn = max(results, key=lambda r: int(r["false_negative_reduction"]))
    best_fp = max(results, key=lambda r: int(r["false_positive_reduction"]))
    promising = [r for r in results if r["classification"] == "PROMISING_REVIEW_ONLY_OVERLAY"]
    beat_sparse_net = [r for r in results if int(r["net_miss_reduction"]) > ACCEPTED_SPARSE_NET_MISS_REDUCTION]
    beat_sparse_fn = [r for r in results if int(r["false_negative_reduction"]) > ACCEPTED_SPARSE_FN_REDUCTION]
    sparse_remains_primary = not beat_sparse_net and not beat_sparse_fn
    verdict = "GREEN_OVERLAY_BATCH_TEST_FOUND_PROMISING_OVERLAYS" if promising else ("YELLOW_SPARSE_HISTORY_OVERLAY_REMAINS_PRIMARY" if sparse_remains_primary else "YELLOW_OVERLAY_BATCH_TEST_MIXED_WITH_CAVEATS")
    next_lane = "Overlay Batch Refinement Contract V1" if promising else ("Sparse-History Overlay Candidate Remains Primary / Stop V1" if sparse_remains_primary else "Stop and wait for user review")

    write_md(
        OUT / "OVERLAY_BATCH_PRIMARY_PRIORITY_POLICY.md",
        """# Overlay Batch Primary Priority Policy

For V1, all overlay eligibility is recorded, but only one primary overlay is applied per player-season. This follows the discovery packet priority order:

1. `OVERLAY_001_SPARSE_EARLY_ROLE_BREAKOUT`
2. `OVERLAY_002_AVAILABILITY_REBOUND`
3. `OVERLAY_003_STARTER_DEPTH_PROMOTION`
4. `OVERLAY_004_SNAP_GROWTH_ROLE_PROMOTION`
5. `OVERLAY_008_DRAFT_CAPITAL_WITH_ROLE`

The user prompt suggested moving availability rebound after starter/depth and snap-growth. This lane uses the discovery packet order because the accepted discovery priority ranked availability rebound second by evidence strength, signal availability, and expected near-term value.

No silent stacking is allowed. Secondary eligibility is recorded in `OVERLAY_BATCH_ELIGIBILITY_LEDGER.csv` but does not alter the score.
""",
    )
    write_md(
        OUT / "OVERLAY_BATCH_COMPARISON_TO_SPARSE_HISTORY_PRIMARY.md",
        f"""# Overlay Batch Comparison To Sparse-History Primary

Accepted sparse-history primary benchmark: `{ACCEPTED_SPARSE_PRIMARY}`.

Accepted benchmark evidence:

- Net miss reduction: `{ACCEPTED_SPARSE_NET_MISS_REDUCTION}`
- False-negative reduction: `{ACCEPTED_SPARSE_FN_REDUCTION}`

Best net miss-reduction row in this batch:

- Overlay: `{best_net['overlay_id']}`
- Reference: `{best_net['formula_id']}`
- Window: `{best_net['scoreboard_window']}`
- Net miss reduction: `{best_net['net_miss_reduction']}`
- False-negative reduction: `{best_net['false_negative_reduction']}`
- False-positive reduction: `{best_net['false_positive_reduction']}`
- Non-target collateral damage: `{best_net['non_target_collateral_damage']}`

Any overlay beat `{ACCEPTED_SPARSE_PRIMARY}` on net miss reduction: `{'yes' if beat_sparse_net else 'no'}`.

Any overlay beat `{ACCEPTED_SPARSE_PRIMARY}` on false-negative reduction: `{'yes' if beat_sparse_fn else 'no'}`.

Sparse-history overlay remains primary: `{'yes' if sparse_remains_primary else 'no'}`.

Review-only ranking simulation remains blocked.
""",
    )
    write_md(
        OUT / "OVERLAY_BATCH_NEXT_LANE_DECISION.md",
        f"""# Overlay Batch Next Lane Decision

Recommended next lane: `{next_lane}`.

Ranking simulation is not recommended. Production integration is not recommended.

This lane is review-only and does not approve model-use, rankings integration, app/runtime behavior, source promotion, push/merge, canonical `local_exports`, hidden sort, or recommendation logic.
""",
    )
    write_md(
        OUT / "OVERLAY_BATCH_BLOCKERS_AND_CAVEATS.md",
        """# Overlay Batch Blockers And Caveats

- This is review-only testing, not production/model-use.
- Partial-window results must not be treated as full-history comparable.
- Primary overlay policy is non-stacking; secondary eligibility is only recorded.
- Inputs are inherited from accepted review-only packets and sidecars.
- Some accepted prior packets are still local-only in their source worktrees; those source packet paths were verified and recorded in the source trace.
- Current-only ADP, market without as-of proof, same-season/future context, SportsDataIO, paid/API/free-trial sources, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, ungated CFBD/prospect production, and inferred UDFA truth remain blocked.
- Review-only ranking simulation remains blocked unless a future readiness gate is explicitly authorized and justified.
""",
    )
    write_md(
        OUT / "OVERLAY_BATCH_SOURCE_TRACE.md",
        f"""# Overlay Batch Source Trace

## Direct Inputs

- Miss-Specific Overlay Library / Candidate Discovery V1: `docs/hq/model/miss_specific_overlay_library_candidate_discovery_v1_20260709/`
- Prior overlay-library commit: `{PRIOR_OVERLAY_LIBRARY_COMMIT}`
- Manual Review Evidence Sort / Decision Packet V1: `docs/hq/master/manual_review_evidence_sort_decision_packet_v1_20260709/`
- Manual-review commit: `{PRIOR_MANUAL_REVIEW_COMMIT}`
- Formula Miss Taxonomy / Red Team Review V1 script: `{RED_SCRIPT}`

## Local Source Packet Verification

The following accepted local-only source packet paths were verified during validation because not all prior packets are present in this branch tree:

- `C:\\NWR\\Niners-War-Room-sparse-history-overlay-candidate-preservation-v1-20260709\\docs\\hq\\model\\sparse_history_overlay_candidate_preservation_v1_20260709`
- `C:\\NWR\\Niners-War-Room-sparse-history-refined-rule-review-readiness-gate-v1-20260709\\docs\\hq\\model\\sparse_history_refined_rule_review_readiness_gate_v1_20260709`
- `C:\\NWR\\Niners-War-Room-sparse-history-rule-refinement-execution-v1-20260709\\docs\\hq\\model\\sparse_history_rule_refinement_execution_v1_20260709`
- `C:\\NWR\\Niners-War-Room-formula-miss-taxonomy-red-team-review-v1-20260709\\docs\\hq\\model\\formula_miss_taxonomy_red_team_review_v1_20260709`
- `C:\\NWR\\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\\docs\\hq\\master\\ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709`

## Remote

- Canonical remote HQ: `origin/work/hq-parallel-control`
- Verified remote HQ head: `{REMOTE_HQ}`

## Source / Use Gate

Review-only overlay batch test only. Production/model-use, rankings integration, app/runtime changes, source promotion, push/merge, canonical `local_exports`, hidden sort, recommendation logic, and ranking simulation remain blocked.

Leakage/as-of: all tested signals are lagged review-only or static post-entry context. Same-season/future context, current-only ADP, SportsDataIO, paid/API sources, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
""",
    )
    write_md(
        OUT / "OVERLAY_CANDIDATE_BATCH_RULE_TEST_V1_REPORT.md",
        f"""# Overlay Candidate Batch Rule Test V1

## Verdict

`{verdict}`

## Scope

This was a bounded review-only overlay batch rule test. It froze exactly five selected overlay families before scoring and enforced a non-stacking primary-overlay policy. It did not run a broad Formula Gauntlet, tune formulas, dynamically tune thresholds, add overlay families after seeing results, run ranking simulation, change production rankings, change app/runtime/model behavior, promote sources, push/merge, mutate canonical `local_exports`, approve production/model-use, create hidden sort/recommendation logic, use current-only ADP historically, use SportsDataIO, use paid/API/free-trial/API-key sources, use same-season/future leakage, use PFF Elusive Rating, use `nwr_elusive_proxy_review_only`, use ungated CFBD/prospect production, or infer UDFA truth.

## Test Summary

- Overlay families tested: `5`
- References tested: `5`
- Result rows: `{len(results)}`
- Eligibility ledger rows: `{len(elig)}`
- Windows tested: full-history `2013-2025`, broad-window `2014-2025`, partial-window `2022-2025`
- Primary-overlay priority policy: discovery packet order, no stacking

## Best Results

- Best net miss-reduction overlay: `{best_net['overlay_id']}` on `{best_net['formula_id']}` / `{best_net['scoreboard_window']}`, net miss reduction `{best_net['net_miss_reduction']}`
- Best false-negative reduction overlay: `{best_fn['overlay_id']}` on `{best_fn['formula_id']}` / `{best_fn['scoreboard_window']}`, false-negative reduction `{best_fn['false_negative_reduction']}`
- Best false-positive reduction overlay: `{best_fp['overlay_id']}` on `{best_fp['formula_id']}` / `{best_fp['scoreboard_window']}`, false-positive reduction `{best_fp['false_positive_reduction']}`

Any overlay beat `{ACCEPTED_SPARSE_PRIMARY}` on net miss reduction: `{'yes' if beat_sparse_net else 'no'}`.

Any overlay beat `{ACCEPTED_SPARSE_PRIMARY}` on false-negative reduction: `{'yes' if beat_sparse_fn else 'no'}`.

Sparse-history overlay remains primary: `{'yes' if sparse_remains_primary else 'no'}`.

## Decision

Recommended next lane: `{next_lane}`.

Review-only ranking simulation remains blocked. Production/model-use and rankings integration remain blocked.
""",
    )
    print(f"verdict={verdict}")
    print(f"best_net={best_net['overlay_id']} {best_net['net_miss_reduction']}")
    print(f"best_fn={best_fn['overlay_id']} {best_fn['false_negative_reduction']}")
    print(f"best_fp={best_fp['overlay_id']} {best_fp['false_positive_reduction']}")
    print(f"sparse_remains_primary={sparse_remains_primary}")
    print(f"next_lane={next_lane}")


if __name__ == "__main__":
    main()
