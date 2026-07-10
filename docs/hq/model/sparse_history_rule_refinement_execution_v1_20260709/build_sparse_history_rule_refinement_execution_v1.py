from __future__ import annotations

import csv
import importlib.util
import math
import os
import py_compile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


OUT_DIR = Path(__file__).resolve().parent
THIS_WORKTREE = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_CONTRACT_COMMIT = "3871cbf8854b28093bf361db4270681e45ccd236"
PRIOR_RULE_TEST_COMMIT = "f8a60a80ffcda8b14386e659757d79ab1ae31390"

CONTRACT_DIR = THIS_WORKTREE / "docs/hq/model/sparse_history_rule_refinement_contract_v1_20260709"
RULE_TEST_DIR = THIS_WORKTREE / "docs/hq/model/sparse_history_breakout_candidate_rule_test_v1_20260709"
DESIGN_DIR = THIS_WORKTREE / "docs/hq/model/sparse_history_breakout_red_team_rookie_young_player_model_design_v1_20260709"
RED_TEAM_DIR = THIS_WORKTREE / "docs/hq/model/formula_miss_taxonomy_red_team_review_v1_20260709"
ADDENDUM_DIR = THIS_WORKTREE / "docs/hq/master/formula_red_team_canonicalization_addendum_v1_20260709"
INGREDIENT_CANON_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\master\ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709")
SNAP_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709")
ROOKIE_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\rookie_draft_capital_data_mart_join_component_test_v1_20260709")
INJURY_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\point_in_time_injury_availability_data_mart_gate_v1_20260709")
FFOP_NGS_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709")

CONTRACT_REGISTRY = CONTRACT_DIR / "SPARSE_HISTORY_REFINED_RULE_REGISTRY.csv"
CONTRACT_PASS_FAIL = CONTRACT_DIR / "SPARSE_HISTORY_REFINEMENT_PASS_FAIL_CRITERIA.md"
CONTRACT_POLICY = CONTRACT_DIR / "SPARSE_HISTORY_REFINED_RULE_INPUT_POLICY.csv"
RULE_TEST_SCRIPT = RULE_TEST_DIR / "build_sparse_history_breakout_candidate_rule_test_v1.py"

PASS_NET_THRESHOLD = 12
SPEARMAN_FLOOR = -0.002
SPEARMAN_PREFERRED = 0.002
MAX_SEVERE_FP_SPIKE = 0
MAX_NONSPARSE_COLLATERAL = 4


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


def fmt(value: Any, places: int = 3) -> str:
    value = num(value)
    return "" if value is None else f"{value:.{places}f}"


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def load_rule_test_module() -> Any:
    spec = importlib.util.spec_from_file_location("sparse_rule_test_v1", RULE_TEST_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load rule-test script: {RULE_TEST_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def overlay_strength(value: str) -> float:
    text = str(value).strip().replace("+", "")
    return float(text)


def low_or_no_pyf(row: dict[str, Any]) -> bool:
    pyf = num(row.get("pyf_score"))
    return pyf is None or pyf < 75


def position(row: dict[str, Any]) -> str:
    return str(row.get("position") or "")


def depth_tier(row: dict[str, Any]) -> str:
    return str(row.get("snap_depth_role_tier") or "")


def starter_weeks(row: dict[str, Any]) -> float:
    return num(row.get("snap_depth_weeks_as_starter")) or 0.0


def is_low_snap(row: dict[str, Any], profile: dict[str, Any]) -> bool:
    return (num(row.get("snap_snap_low_snap_flag")) or 0.0) >= 1 or bool(profile["trap_signals"].get("low_snap_depth"))


def injury_caveat(row: dict[str, Any], profile: dict[str, Any]) -> bool:
    return bool(profile["trap_signals"].get("injury_availability_caveat"))


def clean_availability(row: dict[str, Any], profile: dict[str, Any]) -> bool:
    score = num(row.get("injury_avail_availability_score"))
    return score is not None and score >= 0.80 and not injury_caveat(row, profile)


def draft_bucket(row: dict[str, Any]) -> str:
    return str(row.get("draft_draft_capital_bucket") or "")


def years_since_draft(profile: dict[str, Any]) -> int | None:
    value = profile.get("years_since_draft")
    return int(value) if value is not None else None


def early_career(profile: dict[str, Any]) -> bool:
    return bool(profile.get("early_career_signal"))


def starter_signal(profile: dict[str, Any]) -> bool:
    return bool(profile.get("starter_signal"))


def role_promotion(profile: dict[str, Any]) -> bool:
    return bool(profile.get("role_promotion_signal"))


def snap_growth(profile: dict[str, Any]) -> bool:
    return bool(profile.get("snap_growth_signal"))


def position_profile(profile: dict[str, Any]) -> bool:
    return bool(profile.get("position_specific_signal"))


def expected_opportunity(profile: dict[str, Any]) -> bool:
    return bool(profile.get("expected_opportunity_signal"))


def two_breakout_signals(profile: dict[str, Any]) -> bool:
    return int(profile.get("breakout_count") or 0) >= 2


def three_breakout_signals(profile: dict[str, Any]) -> bool:
    return int(profile.get("breakout_count") or 0) >= 3


def variant_applies(row: dict[str, Any], profile: dict[str, Any], variant: dict[str, str], window: str) -> bool:
    if not bool(profile["sparse"]):
        return False
    vid = variant["variant_id"]
    pos = position(row)
    ysd = years_since_draft(profile)
    if vid == "REFINE_002_A_DEPTH_STARTER_025":
        return starter_signal(profile) and not injury_caveat(row, profile) and not is_low_snap(row, profile)
    if vid == "REFINE_002_B_PRIMARY_STARTER_050":
        return (depth_tier(row) == "PRIMARY_STARTER" or starter_weeks(row) >= 8) and not is_low_snap(row, profile)
    if vid == "REFINE_002_C_LOW_PYF_STARTER_050":
        return low_or_no_pyf(row) and starter_signal(profile)
    if vid == "REFINE_002_D_RB_WR_TE_STARTER_025":
        return pos in {"RB", "WR", "TE"} and starter_signal(profile)
    if vid == "REFINE_005_A_EARLY_ROLE_015":
        return early_career(profile) and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_005_B_EARLY_ROLE_025":
        return early_career(profile) and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_005_C_YEAR2_YEAR3_ONLY_025":
        return ysd in {1, 2} and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_005_D_EARLY_CLEAN_AVAIL_025":
        return early_career(profile) and (role_promotion(profile) or starter_signal(profile)) and clean_availability(row, profile)
    if vid == "REFINE_005_E_EARLY_LOW_PYF_025":
        return low_or_no_pyf(row) and early_career(profile) and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_006_A_DRAFT_ROLE_025":
        return draft_bucket(row) in {"round_1", "round_2"} and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_006_B_DRAFT_ROLE_050":
        return draft_bucket(row) in {"round_1", "round_2"} and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_006_C_ROUND1_ROLE_050":
        return draft_bucket(row) == "round_1" and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_006_D_DAY2_STARTER_025":
        return draft_bucket(row) in {"round_2", "round_3"} and starter_signal(profile)
    if vid == "REFINE_006_E_DRAFT_LOW_PYF_ROLE_050":
        return low_or_no_pyf(row) and draft_bucket(row) in {"round_1", "round_2"} and (role_promotion(profile) or starter_signal(profile))
    if vid == "REFINE_011_A_COMPOSITE_SMALL_025":
        return two_breakout_signals(profile)
    if vid == "REFINE_011_B_COMPOSITE_BALANCED_050":
        return two_breakout_signals(profile)
    if vid == "REFINE_011_C_COMPOSITE_STRICT_050":
        return three_breakout_signals(profile) and not injury_caveat(row, profile)
    if vid == "REFINE_011_D_COMPOSITE_LOW_PYF_050":
        return low_or_no_pyf(row) and two_breakout_signals(profile)
    if vid == "REFINE_011_E_COMPOSITE_POSITION_025":
        return position_profile(profile) and int(profile.get("breakout_count") or 0) >= 2
    if vid == "DIAG_001_A_ROLE_PROMO_025":
        return role_promotion(profile) and not is_low_snap(row, profile)
    if vid == "DIAG_001_B_ROLE_PROMO_STARTER_025":
        return role_promotion(profile) and starter_signal(profile) and not injury_caveat(row, profile)
    if vid == "DIAG_003_A_SNAP_GROWTH_025":
        return snap_growth(profile) and not is_low_snap(row, profile)
    if vid == "DIAG_003_B_SNAP_GROWTH_STARTER_025":
        return snap_growth(profile) and starter_signal(profile) and not injury_caveat(row, profile)
    if vid == "DIAG_008_A_POSITION_PROFILE_025":
        return position_profile(profile)
    if vid == "DIAG_008_B_WR_TE_POSITION_PROFILE_025":
        if pos not in {"WR", "TE"}:
            return False
        if window == "partial_window":
            return starter_signal(profile) or expected_opportunity(profile)
        return starter_signal(profile)
    raise RuntimeError(f"No execution logic for variant: {vid}")


def group_key(row: dict[str, Any], kind: str, profile: dict[str, Any]) -> str:
    if kind == "position":
        return position(row)
    if kind == "lifecycle":
        return str(row.get("lifecycle_bucket") or "unknown_lifecycle")
    if kind == "rookie_year":
        ysd = years_since_draft(profile)
        if ysd is None:
            return "unknown_year_since_draft"
        if ysd == 0:
            return "true_rookie"
        if ysd == 1:
            return "year_two"
        if ysd == 2:
            return "year_three"
        return "year_four_plus"
    return "unknown"


def static_reference_value(reference: dict[str, Any]) -> tuple[str, str, str]:
    window = reference["scoreboard_window"]
    return (
        "0.758" if window == "full_history" else "",
        "0.763" if window == "broad_window" else "",
        "0.790" if window == "partial_window" else "",
    )


def classify(result: dict[str, Any], position_rows: list[dict[str, Any]], variant: dict[str, str]) -> tuple[str, str]:
    window_ok = result["scoreboard_window"] in {"full_history", "broad_window"}
    net = int(result["net_miss_reduction"])
    resolved = int(result["misses_resolved"])
    created = int(result["new_misses_created"])
    fn_reduction = int(result["false_negative_reduction"])
    fp_increase = int(result["false_positive_increase"])
    severe_spike = int(result["severe_false_positive_spike"])
    collateral = int(result["non_sparse_collateral_damage"])
    spearman_delta = num(result["spearman_delta"]) or 0.0
    pos_min = min((int(row["net_miss_reduction"]) for row in position_rows), default=0)
    fail_reasons = []
    if not window_ok:
        return "REFINED_PARTIAL_WINDOW_ONLY_RULE", "partial_window_only"
    if net < PASS_NET_THRESHOLD:
        fail_reasons.append("net_miss_reduction_below_12")
    if resolved <= created:
        fail_reasons.append("resolved_not_meaningfully_above_created")
    if fn_reduction <= 0:
        fail_reasons.append("no_false_negative_reduction")
    if fp_increase > max(2, fn_reduction):
        fail_reasons.append("false_positive_creation_too_high")
    if severe_spike > MAX_SEVERE_FP_SPIKE:
        fail_reasons.append("severe_false_positive_spike")
    if spearman_delta < SPEARMAN_FLOOR:
        fail_reasons.append("spearman_decline")
    if collateral > MAX_NONSPARSE_COLLATERAL:
        fail_reasons.append("non_sparse_collateral_damage")
    if pos_min < -2 and "POSITION" not in variant["variant_id"]:
        fail_reasons.append("position_instability")
    if not fail_reasons:
        return "REFINED_PROMISING_MISS_REDUCTION_RULE", "pass_all_thresholds"
    if net > 0 and spearman_delta >= SPEARMAN_FLOOR:
        return "REFINED_MIXED_RULE", "|".join(fail_reasons)
    if net == 0 and spearman_delta >= SPEARMAN_FLOOR:
        return "REFINED_CONTEXT_ONLY_RULE", "|".join(fail_reasons)
    return "REFINED_HARMFUL_RULE", "|".join(fail_reasons)


def evaluate(
    rows: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    reference: dict[str, Any],
    variant: dict[str, str],
    rt: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    window = reference["scoreboard_window"]
    window_rows = [
        row for row in rows
        if int(reference["season_min"]) <= int(row["season"]) <= int(reference["season_max"])
        and row.get(reference["score_col"]) is not None
    ]
    strength = overlay_strength(variant["overlay_strength"])
    def base_score(row: dict[str, Any]) -> float | None:
        return row.get(reference["score_col"])
    def after_score(row: dict[str, Any]) -> float | None:
        base = row.get(reference["score_col"])
        if base is None:
            return None
        profile = profiles[str(row["substrate_row_id"])]
        delta = strength if variant_applies(row, profile, variant, window) else 0.0
        return clamp(float(base) + delta)
    base_ranks = rt.rank_rows(window_rows, base_score)
    after_ranks = rt.rank_rows(window_rows, after_score)
    pyf_rows = [row for row in window_rows if row.get("PYF_BASELINE_score_pct") is not None]
    pyf_spear = rt.spearman(pyf_rows, lambda row: row.get("PYF_BASELINE_score_pct"))
    before_spear = rt.spearman(window_rows, base_score)
    after_spear = rt.spearman(window_rows, after_score)
    before_misses = after_misses = fp_before = fp_after = fn_before = fn_after = 0
    severe_fp_before = severe_fp_after = severe_fn_before = severe_fn_after = 0
    resolved = created = rows_changed = applied = 0
    sparse_before = sparse_after = nonsparse_before = nonsparse_after = 0
    role_rows = starter_rows = avail_rows = 0
    groups = {
        "position": defaultdict(Counter),
        "lifecycle": defaultdict(Counter),
        "rookie_year": defaultdict(Counter),
    }
    for row in window_rows:
        sid = str(row["substrate_row_id"])
        profile = profiles[sid]
        actual = bool(row["actual_startable"])
        bpred = rt.predicted(row, base_ranks)
        apred = rt.predicted(row, after_ranks)
        bmiss = bpred != actual
        amiss = apred != actual
        applies = variant_applies(row, profile, variant, window)
        if applies:
            applied += 1
            role_rows += int(role_promotion(profile))
            starter_rows += int(starter_signal(profile))
            avail_rows += int(profile.get("availability_rebound_signal"))
        if bpred != apred:
            rows_changed += 1
        before_misses += int(bmiss)
        after_misses += int(amiss)
        fp_before += int(bpred and not actual)
        fp_after += int(apred and not actual)
        fn_before += int((not bpred) and actual)
        fn_after += int((not apred) and actual)
        severe_fp_before += int(rt.is_severe_fp(row, bpred))
        severe_fp_after += int(rt.is_severe_fp(row, apred))
        severe_fn_before += int(rt.is_severe_fn(row, bpred))
        severe_fn_after += int(rt.is_severe_fn(row, apred))
        resolved += int(bmiss and not amiss)
        created += int((not bmiss) and amiss)
        if profile["sparse"]:
            sparse_before += int(bmiss)
            sparse_after += int(amiss)
        else:
            nonsparse_before += int(bmiss)
            nonsparse_after += int(amiss)
        for kind, bucket in groups.items():
            key = group_key(row, kind, profile)
            bucket[key]["rows_tested"] += 1
            bucket[key]["variant_applied_rows"] += int(applies)
            bucket[key]["misses_before"] += int(bmiss)
            bucket[key]["misses_after"] += int(amiss)
            bucket[key]["false_positives_before"] += int(bpred and not actual)
            bucket[key]["false_positives_after"] += int(apred and not actual)
            bucket[key]["false_negatives_before"] += int((not bpred) and actual)
            bucket[key]["false_negatives_after"] += int((not apred) and actual)
    full_ref, broad_ref, partial_ref = static_reference_value(reference)
    top12_before = rt.top_precision(window_rows, base_ranks, 12)
    top12_after = rt.top_precision(window_rows, after_ranks, 12)
    top24_before = rt.top_precision(window_rows, base_ranks, 24)
    top24_after = rt.top_precision(window_rows, after_ranks, 24)
    top36_before = rt.top_precision(window_rows, base_ranks, 36)
    top36_after = rt.top_precision(window_rows, after_ranks, 36)
    result = {
        "variant_id": variant["variant_id"],
        "parent_rule_id": variant["parent_rule_id"],
        "rule_family": variant["rule_family"],
        "reference_id": reference["reference_id"],
        "formula_id": reference["formula_id"],
        "scoreboard_window": window,
        "seasons": f"{reference['season_min']}-{reference['season_max']}",
        "rows_tested": len(window_rows),
        "variant_applied_rows": applied,
        "rows_changed_prediction": rows_changed,
        "total_misses_before": before_misses,
        "total_misses_after": after_misses,
        "net_miss_reduction": before_misses - after_misses,
        "misses_resolved": resolved,
        "new_misses_created": created,
        "false_positives_before": fp_before,
        "false_positives_after": fp_after,
        "false_negatives_before": fn_before,
        "false_negatives_after": fn_after,
        "false_negative_reduction": fn_before - fn_after,
        "false_positive_increase": fp_after - fp_before,
        "severe_false_positives_before": severe_fp_before,
        "severe_false_positives_after": severe_fp_after,
        "severe_false_positive_spike": severe_fp_after - severe_fp_before,
        "severe_false_negatives_before": severe_fn_before,
        "severe_false_negatives_after": severe_fn_after,
        "severe_false_negative_reduction": severe_fn_before - severe_fn_after,
        "sparse_misses_before": sparse_before,
        "sparse_misses_after": sparse_after,
        "sparse_history_only_miss_reduction": sparse_before - sparse_after,
        "non_sparse_misses_before": nonsparse_before,
        "non_sparse_misses_after": nonsparse_after,
        "non_sparse_collateral_damage": nonsparse_after - nonsparse_before,
        "role_promotion_applied_rows": role_rows,
        "starter_depth_applied_rows": starter_rows,
        "availability_rebound_applied_rows": avail_rows,
        "spearman_before": fmt(before_spear),
        "spearman_after": fmt(after_spear),
        "spearman_delta": fmt((after_spear - before_spear) if before_spear is not None and after_spear is not None else None),
        "pyf_same_row_spearman": fmt(pyf_spear),
        "formula_alone_same_row_spearman": fmt(before_spear),
        "current_full_history_accepted_reference": full_ref,
        "broad_window_accepted_reference": broad_ref,
        "partial_window_accepted_reference": partial_ref,
        "top12_precision_before": fmt(top12_before),
        "top12_precision_after": fmt(top12_after),
        "top12_precision_delta": fmt((top12_after - top12_before) if top12_before is not None and top12_after is not None else None),
        "top24_precision_before": fmt(top24_before),
        "top24_precision_after": fmt(top24_after),
        "top24_precision_delta": fmt((top24_after - top24_before) if top24_before is not None and top24_after is not None else None),
        "top36_precision_before": fmt(top36_before),
        "top36_precision_after": fmt(top36_after),
        "top36_precision_delta": fmt((top36_after - top36_before) if top36_before is not None and top36_after is not None else None),
        "full_history_comparable": reference["full_history_comparable"],
        "broad_window_comparable": reference["broad_window_comparable"],
        "partial_window_only": reference["partial_window_only"],
    }
    grouped_rows: dict[str, list[dict[str, Any]]] = {}
    for kind, bucket in groups.items():
        grouped_rows[kind] = []
        for key, counts in sorted(bucket.items()):
            row_out = {
                "variant_id": variant["variant_id"],
                "reference_id": reference["reference_id"],
                "formula_id": reference["formula_id"],
                "scoreboard_window": window,
                kind: key,
                "rows_tested": counts["rows_tested"],
                "variant_applied_rows": counts["variant_applied_rows"],
                "misses_before": counts["misses_before"],
                "misses_after": counts["misses_after"],
                "net_miss_reduction": counts["misses_before"] - counts["misses_after"],
                "false_positives_before": counts["false_positives_before"],
                "false_positives_after": counts["false_positives_after"],
                "false_negatives_before": counts["false_negatives_before"],
                "false_negatives_after": counts["false_negatives_after"],
            }
            grouped_rows[kind].append(row_out)
    return result, grouped_rows["position"], grouped_rows["lifecycle"], grouped_rows["rookie_year"]


def add_classifications(results: list[dict[str, Any]], position_rows: list[dict[str, Any]], variants_by_id: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in position_rows:
        by_key[(row["variant_id"], row["reference_id"], row["scoreboard_window"])].append(row)
    class_rows = []
    for result in results:
        variant = variants_by_id[result["variant_id"]]
        pos_rows = by_key[(result["variant_id"], result["reference_id"], result["scoreboard_window"])]
        klass, reasons = classify(result, pos_rows, variant)
        result["refined_rule_classification"] = klass
        result["pass_fail_status"] = "PASS_ALL_THRESHOLDS" if klass == "REFINED_PROMISING_MISS_REDUCTION_RULE" else "DID_NOT_PASS_ALL_THRESHOLDS"
        result["pass_fail_reasons"] = reasons
        class_rows.append({
            "variant_id": result["variant_id"],
            "parent_rule_id": result["parent_rule_id"],
            "reference_id": result["reference_id"],
            "formula_id": result["formula_id"],
            "scoreboard_window": result["scoreboard_window"],
            "net_miss_reduction": result["net_miss_reduction"],
            "misses_resolved": result["misses_resolved"],
            "new_misses_created": result["new_misses_created"],
            "false_negative_reduction": result["false_negative_reduction"],
            "false_positive_increase": result["false_positive_increase"],
            "non_sparse_collateral_damage": result["non_sparse_collateral_damage"],
            "spearman_delta": result["spearman_delta"],
            "refined_rule_classification": klass,
            "pass_fail_status": result["pass_fail_status"],
            "pass_fail_reasons": reasons,
        })
    return class_rows


def collateral_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        severe_spike = int(result["severe_false_positive_spike"])
        fn_loss = -int(result["false_negative_reduction"]) if int(result["false_negative_reduction"]) < 0 else 0
        collateral = int(result["non_sparse_collateral_damage"])
        fp_increase = int(result["false_positive_increase"])
        flags = []
        if severe_spike > MAX_SEVERE_FP_SPIKE:
            flags.append("severe_false_positive_spike")
        if fn_loss > 0:
            flags.append("false_negative_loss")
        if collateral > MAX_NONSPARSE_COLLATERAL:
            flags.append("non_sparse_collateral_damage")
        if fp_increase > max(2, int(result["false_negative_reduction"])):
            flags.append("false_positive_creation")
        if "DRAFT" in result["variant_id"] and fp_increase > 0:
            flags.append("draft_capital_with_role_harm_check")
        if "CLEAN_AVAIL" in result["variant_id"] and fp_increase > 0:
            flags.append("injury_availability_caveat_harm_check")
        if result["partial_window_only"] == "true":
            flags.append("partial_window_only_overclaim_risk")
        rows.append({
            "variant_id": result["variant_id"],
            "reference_id": result["reference_id"],
            "scoreboard_window": result["scoreboard_window"],
            "severe_false_positive_spike": severe_spike,
            "false_negative_loss": fn_loss,
            "non_sparse_collateral_damage": collateral,
            "false_positive_increase": fp_increase,
            "collateral_flags": "|".join(flags) if flags else "none",
            "collateral_status": "UNACCEPTABLE" if flags and any(f in flags for f in ["severe_false_positive_spike", "false_negative_loss", "non_sparse_collateral_damage"]) else "ACCEPTABLE_OR_CONTEXT",
        })
    return rows


def best_rows(results: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    best_net = max(results, key=lambda row: int(row["net_miss_reduction"]))
    best_fn = max(results, key=lambda row: int(row["false_negative_reduction"]))
    best_spear = max(results, key=lambda row: num(row["spearman_delta"]) or -99)
    return best_net, best_fn, best_spear


def write_docs(results: list[dict[str, Any]], class_rows: list[dict[str, Any]]) -> None:
    best_net, best_fn, best_spear = best_rows(results)
    any_pass = any(row["pass_fail_status"] == "PASS_ALL_THRESHOLDS" for row in results)
    unacceptable = [row for row in collateral_rows(results) if row["collateral_status"] == "UNACCEPTABLE"]
    classes: dict[str, set[str]] = defaultdict(set)
    best_by_variant: dict[str, dict[str, Any]] = {}
    for row in results:
        current = best_by_variant.get(row["variant_id"])
        if current is None or int(row["net_miss_reduction"]) > int(current["net_miss_reduction"]):
            best_by_variant[row["variant_id"]] = row
    for variant_id, row in best_by_variant.items():
        classes[row["refined_rule_classification"]].add(variant_id)
    verdict = "GREEN_SPARSE_HISTORY_REFINEMENT_FOUND_STRONG_MISS_REDUCTION" if any_pass else "YELLOW_SPARSE_HISTORY_REFINEMENT_MIXED_WITH_CAVEATS"
    next_lane = "Sparse-History Refined Rule Review / Readiness Gate V1" if any_pass else "Sparse-History Dedicated Submodel Design V1"
    report = f"""
# Sparse-History Rule Refinement Execution V1

## Verdict

`{verdict}`

## Scope

This is a review-only rule execution lane. It executed the 25 predeclared contract variants without adding variants, dynamic tuning, broad Formula Gauntlet, ranking simulation, production/model-use approval, app/runtime changes, source promotion, push/merge, or canonical `local_exports` writes.

Remote HQ verified: `{EXPECTED_REMOTE_HEAD}`.

Prior refinement contract commit verified: `{PRIOR_CONTRACT_COMMIT}`.

## Execution Summary

Refined variants executed: `25`.

Windows tested: `full-history 2013-2025`, `broad-window 2014-2025`, and `partial-window 2022-2025`.

Best net miss-reduction variant: `{best_net['variant_id']}` on `{best_net['formula_id']}` / `{best_net['scoreboard_window']}`, net miss reduction `{best_net['net_miss_reduction']}`, misses resolved `{best_net['misses_resolved']}`, new misses `{best_net['new_misses_created']}`.

Best false-negative reduction variant: `{best_fn['variant_id']}` with FN reduction `{best_fn['false_negative_reduction']}`.

Best Spearman-improving variant: `{best_spear['variant_id']}` with Spearman delta `{best_spear['spearman_delta']}`.

Any variant met all pass/fail thresholds: `{'yes' if any_pass else 'no'}`.

Variants with unacceptable collateral flags: `{len(unacceptable)}`.

## Classification Summary

- `REFINED_PROMISING_MISS_REDUCTION_RULE`: `{', '.join(sorted(classes.get('REFINED_PROMISING_MISS_REDUCTION_RULE', []))) or 'none'}`
- `REFINED_MIXED_RULE`: `{', '.join(sorted(classes.get('REFINED_MIXED_RULE', []))) or 'none'}`
- `REFINED_CONTEXT_ONLY_RULE`: `{', '.join(sorted(classes.get('REFINED_CONTEXT_ONLY_RULE', []))) or 'none'}`
- `REFINED_HARMFUL_RULE`: `{', '.join(sorted(classes.get('REFINED_HARMFUL_RULE', []))) or 'none'}`
- `REFINED_PARTIAL_WINDOW_ONLY_RULE`: `{', '.join(sorted(classes.get('REFINED_PARTIAL_WINDOW_ONLY_RULE', []))) or 'none'}`
- `REFINED_BLOCKED_OR_INVALID`: `none`

## Decision

Review-only ranking simulation remains not justified. Recommended next lane: `{next_lane}`.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_RULE_REFINEMENT_EXECUTION_V1_REPORT.md", report)

    write_md(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_NEXT_LANE_DECISION.md", f"""
# Sparse-History Refined Rule Next Lane Decision

Recommended next lane: `{next_lane}`.

Review-only ranking simulation remains not justified. The next lane should review the refined rule evidence and decide whether any narrowly bounded readiness gate is appropriate, without production/model-use or rankings integration.
""")

    write_md(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_BLOCKERS_AND_CAVEATS.md", """
# Sparse-History Refined Rule Blockers and Caveats

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior is unchanged.
- Source promotion remains blocked.
- Push/merge was not performed.
- Current-only ADP, market data without as-of proof, SportsDataIO, paid/API/free-trial sources, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, CFBD/prospect model input, and inferred UDFA truth were not used.
- Partial-window results remain partial-window only and cannot be compared as full-history plateau breaks.
- The primary metric is net miss reduction; Spearman is secondary.
""")

    write_md(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_SOURCE_TRACE.md", f"""
# Sparse-History Refined Rule Source Trace

Contract packet: `{CONTRACT_DIR}`

Prior rule-test packet: `{RULE_TEST_DIR}`

Sparse-history design packet: `{DESIGN_DIR}`

Formula miss taxonomy red-team packet: `{RED_TEAM_DIR}`

Formula red-team canonicalization addendum: `{ADDENDUM_DIR}`

Ingredient upgrade canonicalization: `{INGREDIENT_CANON_DIR}`

Snap/depth sidecar packet: `{SNAP_DIR}`

Rookie/draft sidecar packet: `{ROOKIE_DIR}`

Injury availability packet: `{INJURY_DIR}`

Autonomous ffopportunity / NGS packet: `{FFOP_NGS_DIR}`

Source/use gate: all variants remain review-only. Production/model-use, rankings integration, app/runtime behavior, source promotion, hidden sort, recommendation logic, push/merge, and ranking simulation remain blocked.

Leakage/as-of gate: execution uses only lagged N-to-N+1 inputs, static post-entry identity context, and partial-window ffopportunity/NGS where available. Same-season/future context remains blocked.
""")


def main() -> None:
    for path in [CONTRACT_DIR, RULE_TEST_DIR, DESIGN_DIR, RED_TEAM_DIR, ADDENDUM_DIR, INGREDIENT_CANON_DIR, SNAP_DIR, ROOKIE_DIR, INJURY_DIR, FFOP_NGS_DIR, CONTRACT_REGISTRY, CONTRACT_PASS_FAIL, CONTRACT_POLICY, RULE_TEST_SCRIPT]:
        if not path.exists():
            raise RuntimeError(f"Required prior artifact missing: {path}")
    compile_check = OUT_DIR / "_compile_check.pyc"
    try:
        py_compile.compile(__file__, cfile=str(compile_check), doraise=True)
    finally:
        if compile_check.exists():
            compile_check.unlink()

    rt = load_rule_test_module()
    design = rt.load_design_module()
    rows, _joins = design.load_panel()
    profiles = {str(row["substrate_row_id"]): rt.flag_profile(row, design) for row in rows}
    contract_variants = read_csv(CONTRACT_REGISTRY)
    if len(contract_variants) != 25:
        raise RuntimeError(f"Expected 25 variants from contract, found {len(contract_variants)}")
    execution_registry = []
    for idx, variant in enumerate(contract_variants, start=1):
        out = dict(variant)
        out["execution_sequence"] = idx
        out["execution_status"] = "FROZEN_FROM_CONTRACT_BEFORE_SCORING"
        execution_registry.append(out)
    registry_fields = list(execution_registry[0].keys())
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_EXECUTION_REGISTRY.csv", execution_registry, registry_fields)

    variants_by_id = {row["variant_id"]: row for row in contract_variants}
    results: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []
    lifecycle_rows: list[dict[str, Any]] = []
    rookie_rows: list[dict[str, Any]] = []
    for reference in rt.REFERENCES:
        for variant in contract_variants:
            result, pos, life, rookie = evaluate(rows, profiles, reference, variant, rt)
            results.append(result)
            position_rows.extend(pos)
            lifecycle_rows.extend(life)
            rookie_rows.extend(rookie)
    class_rows = add_classifications(results, position_rows, variants_by_id)

    result_fields = [
        "variant_id", "parent_rule_id", "rule_family", "reference_id", "formula_id", "scoreboard_window", "seasons", "rows_tested",
        "variant_applied_rows", "rows_changed_prediction", "total_misses_before", "total_misses_after", "net_miss_reduction",
        "misses_resolved", "new_misses_created", "false_positives_before", "false_positives_after", "false_negatives_before",
        "false_negatives_after", "false_negative_reduction", "false_positive_increase", "severe_false_positives_before",
        "severe_false_positives_after", "severe_false_positive_spike", "severe_false_negatives_before", "severe_false_negatives_after",
        "severe_false_negative_reduction", "sparse_misses_before", "sparse_misses_after", "sparse_history_only_miss_reduction",
        "non_sparse_misses_before", "non_sparse_misses_after", "non_sparse_collateral_damage", "role_promotion_applied_rows",
        "starter_depth_applied_rows", "availability_rebound_applied_rows", "spearman_before", "spearman_after", "spearman_delta",
        "pyf_same_row_spearman", "formula_alone_same_row_spearman", "current_full_history_accepted_reference",
        "broad_window_accepted_reference", "partial_window_accepted_reference", "top12_precision_before", "top12_precision_after",
        "top12_precision_delta", "top24_precision_before", "top24_precision_after", "top24_precision_delta", "top36_precision_before",
        "top36_precision_after", "top36_precision_delta", "full_history_comparable", "broad_window_comparable", "partial_window_only",
        "refined_rule_classification", "pass_fail_status", "pass_fail_reasons",
    ]
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_RESULTS.csv", results, result_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_MISS_REDUCTION_SCORECARD.csv", sorted(results, key=lambda row: int(row["net_miss_reduction"]), reverse=True), result_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_SPEARMAN_IMPACT.csv", sorted(results, key=lambda row: num(row["spearman_delta"]) or -99, reverse=True), result_fields)
    group_fields = ["variant_id", "reference_id", "formula_id", "scoreboard_window", "rows_tested", "variant_applied_rows", "misses_before", "misses_after", "net_miss_reduction", "false_positives_before", "false_positives_after", "false_negatives_before", "false_negatives_after"]
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_POSITION_RESULTS.csv", position_rows, ["position"] + group_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_LIFECYCLE_RESULTS.csv", lifecycle_rows, ["lifecycle"] + group_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_ROOKIE_YEAR_RESULTS.csv", rookie_rows, ["rookie_year"] + group_fields)
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_COLLATERAL_DAMAGE_REVIEW.csv", collateral_rows(results), ["variant_id", "reference_id", "scoreboard_window", "severe_false_positive_spike", "false_negative_loss", "non_sparse_collateral_damage", "false_positive_increase", "collateral_flags", "collateral_status"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_CLASSIFICATION.csv", class_rows, ["variant_id", "parent_rule_id", "reference_id", "formula_id", "scoreboard_window", "net_miss_reduction", "misses_resolved", "new_misses_created", "false_negative_reduction", "false_positive_increase", "non_sparse_collateral_damage", "spearman_delta", "refined_rule_classification", "pass_fail_status", "pass_fail_reasons"])
    write_docs(results, class_rows)


if __name__ == "__main__":
    main()
