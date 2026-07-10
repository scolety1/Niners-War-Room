from __future__ import annotations

import csv
import importlib.util
import math
import py_compile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_CLUSTERING_COMMIT = "c66e983f0f43f79bc5f2e55f9431f7d390e99c65"
PRIOR_GAUNTLET_COMMIT = "8f57c3b758606204f39787c7ff86e69ee514ed39"

GAUNTLET_DIR = Path(
    r"C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709"
    r"\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709"
)
GAUNTLET_SCRIPT = GAUNTLET_DIR / "run_full_review_only_formula_gauntlet_candidate_arena_v1.py"
CLUSTERING_DIR = Path(
    r"C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709"
    r"\docs\hq\model\gauntlet_candidate_diversity_clustering_audit_v1_20260709"
)
MEDIUM_DIR = Path(
    r"C:\NWR\Niners-War-Room-medium-review-only-formula-pilot-v1-20260709"
    r"\docs\hq\model\medium_review_only_formula_pilot_v1_20260709"
)
SMALL_DIR = Path(
    r"C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709"
    r"\docs\hq\model\small_review_only_formula_pilot_v1_20260709"
)
DATA_MART_DIR = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
)
AGE_MASTER_DIR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-master-review-v1-20260709"
    r"\docs\hq\master\age_lifecycle_master_review_v1_20260709"
)
ROLE_MASTER_DIR = REPO / "docs/hq/master/model_v4_role_archetype_master_review_v1_20260709"

PYF_REFERENCE_SPEARMAN = 0.741
MEDIUM_BEST_SPEARMAN = 0.754
PRIOR_GAUNTLET_BEST_SPEARMAN = 0.755
PRIOR_GAUNTLET_BEST_CANDIDATE = "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE"

SEED_SPEARMANS = {
    "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE": 0.755,
    "GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE": 0.749,
    "GAUNTLET_039_QB_THREE_55_30_15": 0.736,
    "GAUNTLET_057_TE_THREE_75_20_5": 0.719,
    "GAUNTLET_051_WR_THREE_65_25_10": 0.703,
    "GAUNTLET_093_ROLE_RB_TOUCH_ROLE_REPORT": 0.651,
}

SEED_META = {
    "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE": {
        "cluster_id": "C01",
        "neighborhood": "overall_decline_age_role_hybrid",
        "scope": "QB/RB/WR/TE",
    },
    "GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE": {
        "cluster_id": "C02",
        "neighborhood": "wr_te_hybrid_role_age",
        "scope": "WR/TE",
    },
    "GAUNTLET_039_QB_THREE_55_30_15": {
        "cluster_id": "C03",
        "neighborhood": "qb_three_year",
        "scope": "QB",
    },
    "GAUNTLET_057_TE_THREE_75_20_5": {
        "cluster_id": "C05",
        "neighborhood": "te_three_year",
        "scope": "TE",
    },
    "GAUNTLET_051_WR_THREE_65_25_10": {
        "cluster_id": "C06",
        "neighborhood": "wr_three_year",
        "scope": "WR",
    },
    "GAUNTLET_093_ROLE_RB_TOUCH_ROLE_REPORT": {
        "cluster_id": "C07",
        "neighborhood": "rb_role_touch_context",
        "scope": "RB",
    },
}


def load_gauntlet_module():
    if not GAUNTLET_SCRIPT.exists():
        raise FileNotFoundError(GAUNTLET_SCRIPT)
    spec = importlib.util.spec_from_file_location("accepted_gauntlet", GAUNTLET_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load accepted Gauntlet runner.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G = load_gauntlet_module()
POSITIONS = G.POSITIONS
POSITION_TOPNS = G.POSITION_TOPNS


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def num(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: float | None, places: int = 3) -> str:
    return "" if value is None else f"{value:.{places}f}"


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.1f}%"


def ffloat(value: object) -> float:
    parsed = num(value)
    return parsed if parsed is not None else -999.0


def add_refinement_features(rows: list[dict[str, object]]) -> None:
    G.normalize_group_scores(rows, ["prior_touches_num", "prior_targets_num", "prior_games_num"])
    G.assign_rank(rows, "pyf_score", "PYF_ANCHOR_rank")


def candidate(
    cid: str,
    seed: str,
    family: str,
    label: str,
    kind: str,
    params: dict[str, Any],
    inputs: str,
    positions: str | None = None,
    caveat: str = "review_only_fixed_predeclared_no_tuning",
) -> dict[str, Any]:
    meta = SEED_META[seed]
    return {
        "candidate_id": cid,
        "seed_candidate": seed,
        "cluster_id": meta["cluster_id"],
        "seed_neighborhood": meta["neighborhood"],
        "formula_family": family,
        "formula_definition": label,
        "score_kind": kind,
        "params": params,
        "position_scope": positions or meta["scope"],
        "input_fields": inputs,
        "weights": weights_text(params),
        "source_use_gate_status": "REVIEW_ONLY_SAFE_FORMULA_DATA_MART_FIELDS",
        "blocked_input_check": "PASS_NO_BLOCKED_INPUTS",
        "leakage_asof_check_status": "PASS_REVIEW_ONLY_ASOF_SAFE",
        "review_only_status": "REVIEW_ONLY_NOT_PRODUCTION_NOT_RANKING",
        "required_comparator": "PYF",
        "score_changes_allowed": "yes",
        "caveat": caveat,
    }


def weights_text(params: dict[str, Any]) -> str:
    parts = []
    for key in sorted(params):
        value = params[key]
        if isinstance(value, float):
            parts.append(f"{key}={value:.3f}")
        else:
            parts.append(f"{key}={value}")
    return ";".join(parts)


def cid(seq: int, slug: str) -> str:
    return f"REFINE_{seq:03d}_{slug}"


def build_registry() -> list[dict[str, Any]]:
    reg: list[dict[str, Any]] = []
    seq = 1

    def add(seed: str, family: str, slug: str, kind: str, params: dict[str, Any], inputs: str, scope: str | None = None, caveat: str = "review_only_fixed_predeclared_no_tuning") -> None:
        nonlocal seq
        reg.append(candidate(cid(seq, slug), seed, family, slug.lower(), kind, params, inputs, scope, caveat))
        seq += 1

    base_inputs = "pyf_prior_nwr_points;prior_2yr_weighted_nwr_points;prior_3yr_weighted_nwr_points"
    age_role_inputs = base_inputs + ";age_bucket;lifecycle_bucket;role_archetype;role_usage_bucket"
    role_inputs = base_inputs + ";role_archetype;role_usage_bucket;prior_touches"

    seed = "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE"
    for weights in [(0.70, 0.20, 0.10), (0.65, 0.25, 0.10), (0.60, 0.30, 0.10), (0.55, 0.30, 0.15), (0.50, 0.35, 0.15), (0.50, 0.30, 0.20)]:
        for late_guard in [0.00, 0.01, 0.02, 0.03]:
            add(
                seed,
                "A_OVERALL_DECLINE_AGE_ROLE_REFINEMENT",
                f"OVERALL_THREE_{int(weights[0]*100)}_{int(weights[1]*100)}_{int(weights[2]*100)}_LATE_{int(late_guard*1000)}",
                "modifier",
                {"base": "three", "w1": weights[0], "w2": weights[1], "w3": weights[2], "late_guard": late_guard, "high_volume_late_guard": late_guard / 2.0},
                age_role_inputs,
                "QB/RB/WR/TE",
                "review_only_decline_context_no_production_approval",
            )

    seed = "GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE"
    wrte_contexts = [
        ("PLAIN", {}),
        ("LATE_010", {"late_guard": 0.01}),
        ("YOUNG_010", {"young_context": 0.01}),
        ("LOWSPARSE_YOUNG_010", {"low_sparse_young_context": 0.01}),
    ]
    for weights in [(0.75, 0.20, 0.05), (0.70, 0.20, 0.10), (0.65, 0.25, 0.10), (0.60, 0.30, 0.10), (0.55, 0.30, 0.15), (0.70, 0.30, 0.00)]:
        for context_name, context in wrte_contexts:
            kind = "modifier"
            params = {"base": "three", "w1": weights[0], "w2": weights[1], "w3": weights[2], **context}
            if weights[2] == 0.0:
                kind = "modifier_two"
                params = {"base": "two", "w1": weights[0], "w2": weights[1], **context}
            add(
                seed,
                "B_WR_TE_HYBRID_ROLE_AGE_REFINEMENT",
                f"WRTE_{'TWO' if weights[2] == 0.0 else 'THREE'}_{int(weights[0]*100)}_{int(weights[1]*100)}_{int(weights[2]*100)}_{context_name}",
                kind,
                params,
                age_role_inputs,
                "WR/TE",
                "review_only_wr_te_role_age_context_not_ranking_input",
            )

    seed = "GAUNTLET_039_QB_THREE_55_30_15"
    qb_weights = [(0.70, 0.20, 0.10), (0.65, 0.25, 0.10), (0.60, 0.25, 0.15), (0.60, 0.30, 0.10), (0.55, 0.30, 0.15), (0.55, 0.25, 0.20), (0.50, 0.35, 0.15), (0.50, 0.30, 0.20), (0.45, 0.35, 0.20), (0.40, 0.35, 0.25)]
    for weights in qb_weights:
        add(seed, "C_QB_THREE_YEAR_REFINEMENT", f"QB_THREE_{int(weights[0]*100)}_{int(weights[1]*100)}_{int(weights[2]*100)}", "base", {"base": "three", "w1": weights[0], "w2": weights[1], "w3": weights[2]}, base_inputs, "QB")
        add(seed, "C_QB_THREE_YEAR_REFINEMENT", f"QB_THREE_{int(weights[0]*100)}_{int(weights[1]*100)}_{int(weights[2]*100)}_SPARSE25", "sparse_guard", {"base": "three", "w1": weights[0], "w2": weights[1], "w3": weights[2], "alpha": 0.25}, base_inputs, "QB", "review_only_sparse_guard_not_production_penalty")

    seed = "GAUNTLET_057_TE_THREE_75_20_5"
    te_defs = [
        ("THREE", (0.85, 0.10, 0.05)),
        ("THREE", (0.80, 0.15, 0.05)),
        ("THREE", (0.75, 0.20, 0.05)),
        ("THREE", (0.70, 0.20, 0.10)),
        ("THREE", (0.65, 0.25, 0.10)),
        ("THREE", (0.60, 0.30, 0.10)),
        ("THREE", (0.55, 0.30, 0.15)),
        ("TWO", (0.85, 0.15)),
        ("TWO", (0.80, 0.20)),
        ("TWO", (0.75, 0.25)),
        ("TWO", (0.70, 0.30)),
    ]
    for name, weights in te_defs:
        if name == "THREE":
            params = {"base": "three", "w1": weights[0], "w2": weights[1], "w3": weights[2]}
            slug = f"TE_THREE_{int(weights[0]*100)}_{int(weights[1]*100)}_{int(weights[2]*100)}"
        else:
            params = {"base": "two", "w1": weights[0], "w2": weights[1]}
            slug = f"TE_TWO_{int(weights[0]*100)}_{int(weights[1]*100)}"
        add(seed, "D_TE_THREE_YEAR_REFINEMENT", slug, "base", params, base_inputs, "TE")
        guarded = dict(params)
        guarded["alpha"] = 0.20
        add(seed, "D_TE_THREE_YEAR_REFINEMENT", f"{slug}_LOWGAMES20", "low_games_guard", guarded, base_inputs, "TE", "review_only_low_games_guard_not_production_penalty")

    seed = "GAUNTLET_051_WR_THREE_65_25_10"
    wr_defs = [
        ("THREE", (0.80, 0.15, 0.05)),
        ("THREE", (0.75, 0.20, 0.05)),
        ("THREE", (0.70, 0.20, 0.10)),
        ("THREE", (0.65, 0.25, 0.10)),
        ("THREE", (0.60, 0.30, 0.10)),
        ("THREE", (0.55, 0.30, 0.15)),
        ("TWO", (0.85, 0.15)),
        ("TWO", (0.80, 0.20)),
        ("TWO", (0.75, 0.25)),
        ("TWO", (0.70, 0.30)),
        ("TWO", (0.65, 0.35)),
    ]
    for name, weights in wr_defs:
        if name == "THREE":
            params = {"base": "three", "w1": weights[0], "w2": weights[1], "w3": weights[2]}
            slug = f"WR_THREE_{int(weights[0]*100)}_{int(weights[1]*100)}_{int(weights[2]*100)}"
        else:
            params = {"base": "two", "w1": weights[0], "w2": weights[1]}
            slug = f"WR_TWO_{int(weights[0]*100)}_{int(weights[1]*100)}"
        add(seed, "E_WR_THREE_YEAR_REFINEMENT", slug, "base", params, base_inputs, "WR")
        young = dict(params)
        young["young_context"] = 0.005
        add(seed, "E_WR_THREE_YEAR_REFINEMENT", f"{slug}_YOUNG005", "modifier" if name == "THREE" else "modifier_two", young, age_role_inputs, "WR", "review_only_wr_breakout_window_context")

    seed = "GAUNTLET_093_ROLE_RB_TOUCH_ROLE_REPORT"
    rb_defs = [
        ("THREE", (0.80, 0.15, 0.05)),
        ("THREE", (0.75, 0.20, 0.05)),
        ("THREE", (0.70, 0.20, 0.10)),
        ("THREE", (0.65, 0.25, 0.10)),
        ("THREE", (0.60, 0.30, 0.10)),
        ("THREE", (0.55, 0.30, 0.15)),
        ("TWO", (0.80, 0.20)),
        ("TWO", (0.75, 0.25)),
    ]
    for name, weights in rb_defs:
        if name == "THREE":
            params = {"base": "three", "w1": weights[0], "w2": weights[1], "w3": weights[2]}
            slug = f"RB_THREE_{int(weights[0]*100)}_{int(weights[1]*100)}_{int(weights[2]*100)}"
            modifier_kind = "modifier"
        else:
            params = {"base": "two", "w1": weights[0], "w2": weights[1]}
            slug = f"RB_TWO_{int(weights[0]*100)}_{int(weights[1]*100)}"
            modifier_kind = "modifier_two"
        add(seed, "F_RB_ROLE_TOUCH_REFINEMENT", slug, "base", params, base_inputs, "RB")
        guarded = dict(params)
        guarded["alpha"] = 0.20
        add(seed, "F_RB_ROLE_TOUCH_REFINEMENT", f"{slug}_SPARSE20", "sparse_guard", guarded, base_inputs, "RB", "review_only_sparse_guard_not_production_penalty")
        touch = dict(params)
        touch["high_touch_context"] = 0.005
        add(seed, "F_RB_ROLE_TOUCH_REFINEMENT", f"{slug}_TOUCH005", modifier_kind, touch, role_inputs, "RB", "review_only_touch_context_no_source_promotion")

    if not 120 <= len(reg) <= 180:
        raise RuntimeError(f"Refinement registry count {len(reg)} outside 120-180 target.")
    return reg


def scope_positions(scope: str) -> set[str]:
    return G.scope_positions(scope)


def base_score(cand: dict[str, Any], row: dict[str, object]) -> float | None:
    params = cand["params"]
    base = params["base"]
    if base == "two":
        return G.weighted2(row, params["w1"], params["w2"])
    if base == "three":
        return G.weighted3(row, params["w1"], params["w2"], params["w3"])
    raise KeyError(base)


def blend_with_pyf(score: float | None, row: dict[str, object], alpha: float) -> float | None:
    pyf = row.get("pyf_score")
    if score is None or pyf is None:
        return score
    return (1.0 - alpha) * float(score) + alpha * float(pyf)


def apply_modifiers(score: float | None, cand: dict[str, Any], row: dict[str, object]) -> float | None:
    if score is None:
        return None
    params = cand["params"]
    factor = 1.0
    late_guard = float(params.get("late_guard", 0.0))
    high_volume_late_guard = float(params.get("high_volume_late_guard", 0.0))
    young_context = float(params.get("young_context", 0.0))
    low_sparse_young_context = float(params.get("low_sparse_young_context", 0.0))
    high_touch_context = float(params.get("high_touch_context", 0.0))
    if late_guard and G.is_older_late(row):
        factor *= 1.0 - late_guard
    if high_volume_late_guard and G.is_high_volume_role(row) and G.is_older_late(row):
        factor *= 1.0 - high_volume_late_guard
    if young_context and G.is_young_early(row) and not bool(row.get("sparse_history_bool")):
        factor *= 1.0 + young_context
    if low_sparse_young_context and G.is_low_or_sparse_role(row) and G.is_young_early(row):
        factor *= 1.0 + low_sparse_young_context
    if high_touch_context and row["position"] == "RB" and G.is_high_volume_role(row) and not bool(row.get("sparse_history_bool")):
        factor *= 1.0 + high_touch_context
    return float(score) * factor


def raw_score(cand: dict[str, Any], row: dict[str, object]) -> float | None:
    if row["position"] not in scope_positions(cand["position_scope"]):
        return None
    kind = cand["score_kind"]
    if kind == "base":
        return base_score(cand, row)
    if kind in {"modifier", "modifier_two"}:
        return apply_modifiers(base_score(cand, row), cand, row)
    if kind == "sparse_guard":
        score = base_score(cand, row)
        if row["sparse_history_bool"]:
            return blend_with_pyf(score, row, float(cand["params"].get("alpha", 0.0)))
        return score
    if kind == "low_games_guard":
        score = base_score(cand, row)
        if row["low_games_bool"]:
            return blend_with_pyf(score, row, float(cand["params"].get("alpha", 0.0)))
        return score
    if kind == "winsor":
        return base_score(cand, row)
    raise KeyError(kind)


def add_scores_and_ranks(rows: list[dict[str, object]], registry: list[dict[str, Any]]) -> None:
    for row in rows:
        for cand in registry:
            row[f"{cand['candidate_id']}_score"] = raw_score(cand, row)
    for cand in registry:
        score_col = f"{cand['candidate_id']}_score"
        if cand["score_kind"] == "winsor":
            for group in G.group_rows(rows, ("season", "position")).values():
                vals = [row[score_col] for row in group if row.get(score_col) is not None]
                low = G.percentile(vals, cand["params"].get("low", 0.05))
                high = G.percentile(vals, cand["params"].get("high", 0.95))
                for row in group:
                    row[score_col] = G.clamp(row.get(score_col), low, high)
        G.assign_rank(rows, score_col, f"{cand['candidate_id']}_rank")


def candidate_scope(cand: dict[str, Any], rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], str]:
    positions = scope_positions(cand["position_scope"])
    scoped = [
        row
        for row in rows
        if str(row["position"]) in positions and row.get(f"{cand['candidate_id']}_rank") is not None
    ]
    return scoped, "/".join([pos for pos in POSITIONS if pos in positions])


def metric_delta(left: float | None, right: float | None) -> float | None:
    return None if left is None or right is None else left - right


def interpretation(sd_pyf: float | None, sd_gauntlet: float | None) -> str:
    if sd_pyf is None:
        return "BLOCKED_OR_INVALID"
    if sd_pyf < -0.0005:
        return "FAILED_VS_PYF"
    if sd_gauntlet is not None and sd_gauntlet > 0.0005:
        return "REFINED_PROMISING_REVIEW_ONLY"
    if sd_gauntlet is not None and sd_gauntlet < -0.005 and sd_pyf > 0.0005:
        return "FAILED_VS_GAUNTLET_BEST"
    if sd_pyf > 0.0005:
        return "REFINED_MIXED_REVIEW_ONLY"
    return "REFINED_WEAK_REVIEW_ONLY"


def build_metric_rows(
    rows: list[dict[str, object]], registry: list[dict[str, Any]]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    scorecard: list[dict[str, object]] = []
    pyf_compare: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []
    for cand in registry:
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        cm = G.metrics_for_rows(scoped, rank_col)
        pm = G.metrics_for_rows(scoped, "PYF_ANCHOR_rank")
        sd = metric_delta(cm["spearman"], pm["spearman"])
        sd_medium = metric_delta(cm["spearman"], MEDIUM_BEST_SPEARMAN)
        sd_gauntlet = metric_delta(cm["spearman"], PRIOR_GAUNTLET_BEST_SPEARMAN)
        seed_spearman = SEED_SPEARMANS[cand["seed_candidate"]]
        sd_seed = metric_delta(cm["spearman"], seed_spearman)
        pd = metric_delta(cm["startable_precision"], pm["startable_precision"])
        sparse_delta = metric_delta(cm["sparse_error_rate"], pm["sparse_error_rate"])
        low_delta = metric_delta(cm["low_games_error_rate"], pm["low_games_error_rate"])
        scorecard.append(
            {
                "candidate_id": cand["candidate_id"],
                "seed_candidate": cand["seed_candidate"],
                "cluster_id": cand["cluster_id"],
                "seed_neighborhood": cand["seed_neighborhood"],
                "formula_family": cand["formula_family"],
                "position_scope": cand["position_scope"],
                "rows_tested": cm["rows"],
                "candidate_spearman": fmt(cm["spearman"]),
                "pyf_spearman_comparable": fmt(pm["spearman"]),
                "spearman_delta_vs_pyf": fmt(sd),
                "medium_best_spearman": fmt(MEDIUM_BEST_SPEARMAN),
                "spearman_delta_vs_medium_best": fmt(sd_medium),
                "prior_gauntlet_best_spearman": fmt(PRIOR_GAUNTLET_BEST_SPEARMAN),
                "spearman_delta_vs_prior_gauntlet_best": fmt(sd_gauntlet),
                "seed_spearman": fmt(seed_spearman),
                "spearman_delta_vs_seed": fmt(sd_seed),
                "mae_rank_vs_finish": fmt(cm["mae"]),
                "rmse_rank_vs_finish": fmt(cm["rmse"]),
                "startable_precision": pct(cm["startable_precision"]),
                "pyf_startable_precision_comparable": pct(pm["startable_precision"]),
                "startable_precision_delta_vs_pyf": pct(pd),
                "candidate_false_positives": cm["false_positives"],
                "pyf_false_positives_comparable": pm["false_positives"],
                "false_positive_delta_vs_pyf": cm["false_positives"] - pm["false_positives"],
                "candidate_false_negatives": cm["false_negatives"],
                "pyf_false_negatives_comparable": pm["false_negatives"],
                "false_negative_delta_vs_pyf": cm["false_negatives"] - pm["false_negatives"],
                "sparse_history_error_delta_vs_pyf": pct(sparse_delta),
                "low_games_error_delta_vs_pyf": pct(low_delta),
                "beats_pyf_overall": str(bool(sd is not None and sd > 0.0005)).lower(),
                "beats_prior_gauntlet_best": str(bool(sd_gauntlet is not None and sd_gauntlet > 0.0005)).lower(),
                "beats_seed": str(bool(sd_seed is not None and sd_seed > 0.0005)).lower(),
                "interpretation": interpretation(sd, sd_gauntlet),
                "review_only_status": cand["review_only_status"],
                "caveat": cand["caveat"],
            }
        )
        pyf_compare.append(
            {
                "candidate_id": cand["candidate_id"],
                "seed_candidate": cand["seed_candidate"],
                "cluster_id": cand["cluster_id"],
                "seed_neighborhood": cand["seed_neighborhood"],
                "scope": scope,
                "candidate_spearman": fmt(cm["spearman"]),
                "pyf_spearman": fmt(pm["spearman"]),
                "spearman_delta": fmt(sd),
                "candidate_startable_precision": pct(cm["startable_precision"]),
                "pyf_startable_precision": pct(pm["startable_precision"]),
                "startable_precision_delta": pct(pd),
                "candidate_false_positives": cm["false_positives"],
                "pyf_false_positives": pm["false_positives"],
                "false_positive_delta": cm["false_positives"] - pm["false_positives"],
                "candidate_false_negatives": cm["false_negatives"],
                "pyf_false_negatives": pm["false_negatives"],
                "false_negative_delta": cm["false_negatives"] - pm["false_negatives"],
                "beat_pyf": str(bool(sd is not None and sd > 0.0005)).lower(),
            }
        )
        for position in POSITIONS:
            pos_rows = [row for row in scoped if row["position"] == position]
            if not pos_rows:
                continue
            pcm = G.metrics_for_rows(pos_rows, rank_col)
            ppm = G.metrics_for_rows(pos_rows, "PYF_ANCHOR_rank")
            psd = metric_delta(pcm["spearman"], ppm["spearman"])
            top_values: dict[str, object] = {}
            for top_n in [12, 24, 36]:
                if top_n in POSITION_TOPNS[position]:
                    top_values[f"top_{top_n}_precision"] = pct(G.top_precision(pos_rows, rank_col, top_n))
                    top_values[f"pyf_top_{top_n}_precision"] = pct(G.top_precision(pos_rows, "PYF_ANCHOR_rank", top_n))
                else:
                    top_values[f"top_{top_n}_precision"] = ""
                    top_values[f"pyf_top_{top_n}_precision"] = ""
            position_rows.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "seed_candidate": cand["seed_candidate"],
                    "cluster_id": cand["cluster_id"],
                    "seed_neighborhood": cand["seed_neighborhood"],
                    "formula_family": cand["formula_family"],
                    "position": position,
                    "rows_tested": pcm["rows"],
                    "candidate_spearman": fmt(pcm["spearman"]),
                    "pyf_spearman": fmt(ppm["spearman"]),
                    "spearman_delta_vs_pyf": fmt(psd),
                    "startable_precision": pct(pcm["startable_precision"]),
                    "pyf_startable_precision": pct(ppm["startable_precision"]),
                    "top_12_precision": top_values["top_12_precision"],
                    "pyf_top_12_precision": top_values["pyf_top_12_precision"],
                    "top_24_precision": top_values["top_24_precision"],
                    "pyf_top_24_precision": top_values["pyf_top_24_precision"],
                    "top_36_precision": top_values["top_36_precision"],
                    "pyf_top_36_precision": top_values["pyf_top_36_precision"],
                    "candidate_false_positives": pcm["false_positives"],
                    "pyf_false_positives": ppm["false_positives"],
                    "candidate_false_negatives": pcm["false_negatives"],
                    "pyf_false_negatives": ppm["false_negatives"],
                    "beat_pyf_by_position": str(bool(psd is not None and psd > 0.0005)).lower(),
                }
            )
    return scorecard, pyf_compare, position_rows


def build_slice_rows(rows: list[dict[str, object]], registry: list[dict[str, Any]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    predicates = G.slice_predicates()
    for cand in registry:
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        for slice_name, predicate in predicates.items():
            group = [row for row in scoped if predicate(row)]
            if not group:
                output.append(
                    {
                        "candidate_id": cand["candidate_id"],
                        "seed_candidate": cand["seed_candidate"],
                        "cluster_id": cand["cluster_id"],
                        "seed_neighborhood": cand["seed_neighborhood"],
                        "formula_family": cand["formula_family"],
                        "slice_name": slice_name,
                        "scope": scope,
                        "rows": 0,
                        "startable_hits": 0,
                        "startable_rate": "",
                        "candidate_false_positives": 0,
                        "pyf_false_positives": 0,
                        "false_positive_delta_vs_pyf": 0,
                        "candidate_false_negatives": 0,
                        "pyf_false_negatives": 0,
                        "false_negative_delta_vs_pyf": 0,
                        "candidate_error_rate": "",
                        "pyf_error_rate": "",
                        "harm_delta_vs_pyf": "",
                        "guardrail_interpretation": "slice_not_present",
                    }
                )
                continue
            cand_fp = [row for row in group if G.predicted_startable(row, rank_col) and not row["actual_startable"]]
            cand_fn = [row for row in group if not G.predicted_startable(row, rank_col) and row["actual_startable"]]
            pyf_fp = [row for row in group if G.predicted_startable(row, "PYF_ANCHOR_rank") and not row["actual_startable"]]
            pyf_fn = [row for row in group if not G.predicted_startable(row, "PYF_ANCHOR_rank") and row["actual_startable"]]
            cand_error = (len(cand_fp) + len(cand_fn)) / len(group)
            pyf_error = (len(pyf_fp) + len(pyf_fn)) / len(group)
            delta = cand_error - pyf_error
            output.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "seed_candidate": cand["seed_candidate"],
                    "cluster_id": cand["cluster_id"],
                    "seed_neighborhood": cand["seed_neighborhood"],
                    "formula_family": cand["formula_family"],
                    "slice_name": slice_name,
                    "scope": scope,
                    "rows": len(group),
                    "startable_hits": sum(1 for row in group if row["actual_startable"]),
                    "startable_rate": pct(sum(1 for row in group if row["actual_startable"]) / len(group)),
                    "candidate_false_positives": len(cand_fp),
                    "pyf_false_positives": len(pyf_fp),
                    "false_positive_delta_vs_pyf": len(cand_fp) - len(pyf_fp),
                    "candidate_false_negatives": len(cand_fn),
                    "pyf_false_negatives": len(pyf_fn),
                    "false_negative_delta_vs_pyf": len(cand_fn) - len(pyf_fn),
                    "candidate_error_rate": pct(cand_error),
                    "pyf_error_rate": pct(pyf_error),
                    "harm_delta_vs_pyf": pct(delta),
                    "guardrail_interpretation": "no_added_harm_vs_pyf" if abs(delta) < 0.0005 else ("worse_than_pyf" if delta > 0 else "improves_vs_pyf"),
                }
            )
    return output


def build_stability_rows(rows: list[dict[str, object]], registry: list[dict[str, Any]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    seasons = sorted({row["season"] for row in rows})
    for cand in registry:
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        for season in seasons:
            group = [row for row in scoped if row["season"] == season]
            if not group:
                continue
            cm = G.metrics_for_rows(group, rank_col)
            pm = G.metrics_for_rows(group, "PYF_ANCHOR_rank")
            delta = metric_delta(cm["spearman"], pm["spearman"])
            output.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "seed_candidate": cand["seed_candidate"],
                    "cluster_id": cand["cluster_id"],
                    "seed_neighborhood": cand["seed_neighborhood"],
                    "formula_family": cand["formula_family"],
                    "scope": scope,
                    "season": season,
                    "rows": cm["rows"],
                    "candidate_spearman": fmt(cm["spearman"]),
                    "pyf_spearman": fmt(pm["spearman"]),
                    "spearman_delta_vs_pyf": fmt(delta),
                    "beat_pyf_in_season": str(bool(delta is not None and delta > 0.0005)).lower(),
                    "candidate_false_positives": cm["false_positives"],
                    "pyf_false_positives": pm["false_positives"],
                    "candidate_false_negatives": cm["false_negatives"],
                    "pyf_false_negatives": pm["false_negatives"],
                    "stability_caveat": "season_sample_directional_only",
                }
            )
    return output


def build_outlier_rows(rows: list[dict[str, object]], registry: list[dict[str, Any]], scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    seasons = sorted({row["season"] for row in rows})
    score_by_id = {row["candidate_id"]: row for row in scorecard}
    for cand in registry:
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        base_delta = num(score_by_id[cand["candidate_id"]]["spearman_delta_vs_pyf"])
        loso: list[tuple[str, float | None]] = []
        for season in seasons:
            group = [row for row in scoped if row["season"] != season]
            cm = G.metrics_for_rows(group, rank_col)
            pm = G.metrics_for_rows(group, "PYF_ANCHOR_rank")
            loso.append((season, metric_delta(cm["spearman"], pm["spearman"])))
        valid = [(season, delta) for season, delta in loso if delta is not None]
        if not valid:
            continue
        min_item = min(valid, key=lambda item: item[1])
        max_item = max(valid, key=lambda item: item[1])
        shifts = [abs(delta - base_delta) for _, delta in valid if base_delta is not None]
        max_shift = max(shifts) if shifts else None
        positive_count = sum(1 for _, delta in valid if delta > 0.0005)
        output.append(
            {
                "candidate_id": cand["candidate_id"],
                "seed_candidate": cand["seed_candidate"],
                "cluster_id": cand["cluster_id"],
                "seed_neighborhood": cand["seed_neighborhood"],
                "formula_family": cand["formula_family"],
                "scope": scope,
                "overall_spearman_delta_vs_pyf": fmt(base_delta),
                "leave_one_season_out_positive_count": positive_count,
                "leave_one_season_out_total": len(valid),
                "min_loso_delta": fmt(min_item[1]),
                "min_loso_omitted_season": min_item[0],
                "max_loso_delta": fmt(max_item[1]),
                "max_loso_omitted_season": max_item[0],
                "max_abs_delta_shift": fmt(max_shift),
                "outlier_influence_flag": "direction_stable" if positive_count == len(valid) else ("mixed_loso_direction" if positive_count else "no_positive_loso_direction"),
            }
        )
    return output


def registry_rows(registry: list[dict[str, Any]]) -> list[dict[str, object]]:
    return [
        {
            "candidate_id": cand["candidate_id"],
            "seed_candidate": cand["seed_candidate"],
            "cluster_id": cand["cluster_id"],
            "seed_neighborhood": cand["seed_neighborhood"],
            "formula_family": cand["formula_family"],
            "formula_definition": cand["formula_definition"],
            "score_kind": cand["score_kind"],
            "params": weights_text(cand["params"]),
            "input_fields": cand["input_fields"],
            "weights": cand["weights"],
            "position_scope": cand["position_scope"],
            "source/use-gate status": cand["source_use_gate_status"],
            "blocked_input_check": cand["blocked_input_check"],
            "leakage/as-of check status": cand["leakage_asof_check_status"],
            "review_only_status": cand["review_only_status"],
            "required_comparator": cand["required_comparator"],
            "score_changes_allowed": cand["score_changes_allowed"],
            "caveat": cand["caveat"],
        }
        for cand in registry
    ]


def validate_registry(registry: list[dict[str, Any]]) -> None:
    blocked_terms = [
        "route",
        "yprr",
        "tprr",
        "return_scoring",
        "broad_pfr",
        "pfr_qb_passing",
        "pff",
        "elusive",
        "nwr_elusive_proxy_review_only",
        "red_zone",
        "local_exports",
    ]
    for cand in registry:
        blob = " ".join(str(cand.get(key, "")) for key in ["formula_definition", "input_fields", "caveat"]).lower()
        bad = [term for term in blocked_terms if term in blob]
        if bad:
            raise RuntimeError(f"Blocked input term {bad} found in {cand['candidate_id']}.")
        if cand["review_only_status"] != "REVIEW_ONLY_NOT_PRODUCTION_NOT_RANKING":
            raise RuntimeError(f"Non-review-only status for {cand['candidate_id']}.")


def coverage_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "rows": len(rows),
        "seasons": f"{min(int(row['season']) for row in rows)}-{max(int(row['season']) for row in rows)}",
        "positions": dict(Counter(str(row["position"]) for row in rows)),
        "sparse_rows": sum(1 for row in rows if row["sparse_history_bool"]),
        "low_games_rows": sum(1 for row in rows if row["low_games_bool"]),
        "review_only_rows": sum(1 for row in rows if str(row["review_only"]).lower() == "true"),
        "model_use_allowed_true": sum(1 for row in rows if str(row["model_use_allowed"]).lower() == "true"),
        "production_approved_true": sum(1 for row in rows if str(row["production_approved"]).lower() == "true"),
    }


def seed_neighborhood_results(scorecard: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_seed: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in scorecard:
        by_seed[str(row["seed_candidate"])].append(row)
    for seed, group in sorted(by_seed.items(), key=lambda item: SEED_META[item[0]]["cluster_id"]):
        best = max(group, key=lambda row: ffloat(row["candidate_spearman"]))
        beat_pyf = [row for row in group if row["beats_pyf_overall"] == "true"]
        beat_seed = [row for row in group if row["beats_seed"] == "true"]
        beat_gauntlet = [row for row in group if row["beats_prior_gauntlet_best"] == "true"]
        max_seed_delta = max((num(row["spearman_delta_vs_seed"]) or -999 for row in group), default=-999)
        rows.append(
            {
                "seed_candidate": seed,
                "cluster_id": SEED_META[seed]["cluster_id"],
                "seed_neighborhood": SEED_META[seed]["neighborhood"],
                "seed_reference_spearman": fmt(SEED_SPEARMANS[seed]),
                "refinement_candidates": len(group),
                "best_refined_candidate": best["candidate_id"],
                "best_refined_spearman": best["candidate_spearman"],
                "best_delta_vs_seed": best["spearman_delta_vs_seed"],
                "best_delta_vs_pyf": best["spearman_delta_vs_pyf"],
                "candidates_beating_pyf": len(beat_pyf),
                "candidates_beating_seed": len(beat_seed),
                "candidates_beating_prior_gauntlet_best": len(beat_gauntlet),
                "material_seed_improvement": str(max_seed_delta > 0.002).lower(),
                "neighborhood_interpretation": "materially_improved" if max_seed_delta > 0.002 else ("directionally_improved" if beat_seed else "no_seed_improvement"),
            }
        )
    return rows


def top_rows(rows: list[dict[str, object]], key: str, n: int = 10) -> list[dict[str, object]]:
    return sorted(rows, key=lambda row: ffloat(row[key]), reverse=True)[:n]


def write_leaderboards(
    scorecard: list[dict[str, object]],
    position_rows: list[dict[str, object]],
    seed_rows: list[dict[str, object]],
    slice_rows: list[dict[str, object]],
    outlier_rows: list[dict[str, object]],
) -> None:
    lines: list[str] = ["# Diverse Champion Refinement Leaderboards", ""]
    lines.extend(["## Best Overall Refined Candidates", ""])
    for row in top_rows(scorecard, "candidate_spearman", 12):
        lines.append(f"- `{row['candidate_id']}` `{row['candidate_spearman']}` delta_vs_pyf `{row['spearman_delta_vs_pyf']}` seed `{row['seed_candidate']}`")
    for position in POSITIONS:
        lines.extend(["", f"## Best {position} Refined Candidates", ""])
        choices = [row for row in position_rows if row["position"] == position]
        for row in top_rows(choices, "candidate_spearman", 8):
            lines.append(f"- `{row['candidate_id']}` `{row['candidate_spearman']}` delta_vs_pyf `{row['spearman_delta_vs_pyf']}`")
    lines.extend(["", "## Best By Seed Neighborhood", ""])
    for row in seed_rows:
        lines.append(f"- `{row['seed_neighborhood']}`: `{row['best_refined_candidate']}` Spearman `{row['best_refined_spearman']}` delta_vs_seed `{row['best_delta_vs_seed']}`")
    lines.extend(["", "## Most Stable Refined Candidates", ""])
    stable = sorted(outlier_rows, key=lambda row: (int(row["leave_one_season_out_positive_count"]), -ffloat(row["max_abs_delta_shift"]), ffloat(row["overall_spearman_delta_vs_pyf"])), reverse=True)
    for row in stable[:10]:
        lines.append(f"- `{row['candidate_id']}` positive LOSO `{row['leave_one_season_out_positive_count']}/{row['leave_one_season_out_total']}` max_shift `{row['max_abs_delta_shift']}`")
    for slice_name, title in [
        ("sparse_history", "Best Sparse-History Guardrail Candidates"),
        ("low_games", "Best Low-Games Guardrail Candidates"),
        ("prior_decline_proxy", "Best Prior-Decline Candidates"),
        ("older_late_lifecycle", "Best Age/Lifecycle-Context Candidates"),
        ("high_volume_role", "Best Role-Archetype-Context Candidates"),
    ]:
        lines.extend(["", f"## {title}", ""])
        choices = [row for row in slice_rows if row["slice_name"] == slice_name and row["rows"]]
        choices = sorted(choices, key=lambda row: (int(row["false_positive_delta_vs_pyf"]) if "false_positive_delta_vs_pyf" in row else 0, ffloat(row["harm_delta_vs_pyf"])))
        for row in choices[:8]:
            lines.append(f"- `{row['candidate_id']}` harm_delta `{row['harm_delta_vs_pyf']}` fp_delta `{row['false_positive_delta_vs_pyf']}` fn_delta `{row['false_negative_delta_vs_pyf']}`")
    write_text(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_LEADERBOARDS.md", "\n".join(lines))


def write_harmful_candidates(scorecard: list[dict[str, object]], slice_rows: list[dict[str, object]], outlier_rows: list[dict[str, object]]) -> None:
    failed = [row for row in scorecard if row["interpretation"] in {"FAILED_VS_PYF", "FAILED_VS_GAUNTLET_BEST"}]
    harmful_slices = [
        row
        for row in slice_rows
        if row["guardrail_interpretation"] == "worse_than_pyf" and str(row["slice_name"]) in {"sparse_history", "low_games", "older_late_lifecycle", "young_early_lifecycle"}
    ]
    unstable = [row for row in outlier_rows if row["outlier_influence_flag"] != "direction_stable"]
    lines = [
        "# Diverse Champion Refinement Harmful Candidates",
        "",
        "## Failed Or Weak Versus Key Comparators",
        "",
    ]
    for row in failed[:40]:
        lines.append(f"- `{row['candidate_id']}` `{row['interpretation']}` Spearman `{row['candidate_spearman']}` delta_vs_pyf `{row['spearman_delta_vs_pyf']}` delta_vs_gauntlet `{row['spearman_delta_vs_prior_gauntlet_best']}`")
    lines.extend(["", "## Guardrail Harm Flags", ""])
    for row in harmful_slices[:40]:
        lines.append(f"- `{row['candidate_id']}` slice `{row['slice_name']}` harm_delta `{row['harm_delta_vs_pyf']}`")
    lines.extend(["", "## Outlier / Season Stability Flags", ""])
    for row in unstable[:40]:
        lines.append(f"- `{row['candidate_id']}` `{row['outlier_influence_flag']}` positive_loso `{row['leave_one_season_out_positive_count']}/{row['leave_one_season_out_total']}`")
    write_text(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_HARMFUL_CANDIDATES.md", "\n".join(lines))


def write_markdown_reports(
    rows: list[dict[str, object]],
    registry: list[dict[str, Any]],
    scorecard: list[dict[str, object]],
    position_rows: list[dict[str, object]],
    seed_rows: list[dict[str, object]],
    slice_rows: list[dict[str, object]],
    outlier_rows: list[dict[str, object]],
) -> tuple[str, dict[str, object]]:
    coverage = coverage_summary(rows)
    best_overall = max(scorecard, key=lambda row: ffloat(row["candidate_spearman"]))
    beat_pyf = [row for row in scorecard if row["beats_pyf_overall"] == "true"]
    beat_gauntlet = [row for row in scorecard if row["beats_prior_gauntlet_best"] == "true"]
    position_best = {
        position: max([row for row in position_rows if row["position"] == position], key=lambda row: ffloat(row["candidate_spearman"]))
        for position in POSITIONS
    }
    material_seed_rows = [row for row in seed_rows if row["material_seed_improvement"] == "true"]
    stable = sorted(outlier_rows, key=lambda row: (int(row["leave_one_season_out_positive_count"]), -ffloat(row["max_abs_delta_shift"]), ffloat(row["overall_spearman_delta_vs_pyf"])), reverse=True)
    sparse_slice = [row for row in slice_rows if row["slice_name"] == "sparse_history"]
    low_slice = [row for row in slice_rows if row["slice_name"] == "low_games"]
    prior_decline = [row for row in slice_rows if row["slice_name"] == "prior_decline_proxy"]
    age_slice = [row for row in slice_rows if row["slice_name"] in {"older_late_lifecycle", "young_early_lifecycle"}]
    role_slice = [row for row in slice_rows if row["slice_name"] in {"high_volume_role", "low_or_sparse_role", "rb_high_touch_role", "receiver_high_target_role"}]
    verdict = (
        "GREEN_DIVERSE_CHAMPION_REFINEMENT_FOUND_STRONG_REFINED_CANDIDATES"
        if beat_gauntlet and material_seed_rows
        else ("YELLOW_DIVERSE_CHAMPION_REFINEMENT_MIXED_RESULTS" if beat_pyf else "RED_DIVERSE_CHAMPION_REFINEMENT_NO_IMPROVEMENT")
    )
    recommendation = (
        "Second refinement around top 3-5 refined review-only candidates."
        if beat_gauntlet and material_seed_rows
        else "Add missing data before more formula work."
    )
    best_positions_text = "; ".join(f"{pos}: {row['candidate_id']} ({row['candidate_spearman']})" for pos, row in position_best.items())
    summary = {
        "verdict": verdict,
        "rows": coverage["rows"],
        "registered": len(registry),
        "scored": len(scorecard),
        "seed_neighborhoods": len(seed_rows),
        "best_overall": best_overall["candidate_id"],
        "best_overall_spearman": best_overall["candidate_spearman"],
        "beat_pyf": len(beat_pyf),
        "beat_gauntlet": len(beat_gauntlet),
        "material_seed_improvements": len(material_seed_rows),
        "best_positions": best_positions_text,
        "recommendation": recommendation,
    }
    report = f"""
# Diverse Champion Refinement Predeclared Execution V1 Report

## Verdict

`{verdict}`

## Clear Answer

The review-only diverse champion refinement registered `{len(registry)}` fixed candidates before scoring and scored `{len(scorecard)}` candidates on the accepted Formula Data Mart substrate. The grid refined exactly the six approved seed neighborhoods. `{len(beat_pyf)}` refined candidates beat PYF overall. `{len(beat_gauntlet)}` refined candidates beat the prior full-Gauntlet best reference of `{PRIOR_GAUNTLET_BEST_SPEARMAN:.3f}`. `{len(material_seed_rows)}` seed neighborhoods produced a material improvement over their seed reference.

## Preserved Reference Benchmarks

- PYF Spearman: `{PYF_REFERENCE_SPEARMAN:.3f}`
- Prior best Gauntlet overall candidate: `{PRIOR_GAUNTLET_BEST_CANDIDATE}`, Spearman `{PRIOR_GAUNTLET_BEST_SPEARMAN:.3f}`
- Prior best QB: `GAUNTLET_020_THREE_YEAR_55_30_15`
- Prior best RB: `GAUNTLET_109_ROBUST_WINSOR_THREE_60_10`
- Prior best WR: `GAUNTLET_016_THREE_YEAR_75_20_5`
- Prior best TE: `GAUNTLET_016_THREE_YEAR_75_20_5`
- Prior candidates beating PYF overall: `90`
- Effective distinct promising clusters: `6`

## Benchmark Scope

- Rows tested: `{coverage['rows']}`
- Seasons: `{coverage['seasons']}`
- Positions: `{coverage['positions']}`
- Review-only rows: `{coverage['review_only_rows']}`
- Model-use allowed rows: `{coverage['model_use_allowed_true']}`
- Production-approved rows: `{coverage['production_approved_true']}`

## Best Overall Refined Review-Only Candidate

`{best_overall['candidate_id']}` from `{best_overall['formula_family']}` produced Spearman `{best_overall['candidate_spearman']}` versus PYF `{best_overall['pyf_spearman_comparable']}` and prior Gauntlet best `{PRIOR_GAUNTLET_BEST_SPEARMAN:.3f}`.

## Best Refined Candidate By Position

{chr(10).join(f"- {pos}: `{row['candidate_id']}` Spearman `{row['candidate_spearman']}` delta_vs_pyf `{row['spearman_delta_vs_pyf']}`" for pos, row in position_best.items())}

## Guardrails

- Sparse-history slice rows reviewed: `{sum(1 for row in sparse_slice if row['rows'])}` candidate-slice rows
- Low-games slice rows reviewed: `{sum(1 for row in low_slice if row['rows'])}` candidate-slice rows
- Prior-decline slice rows reviewed: `{sum(1 for row in prior_decline if row['rows'])}` candidate-slice rows
- Age/lifecycle slice rows reviewed: `{sum(1 for row in age_slice if row['rows'])}` candidate-slice rows
- Role-archetype slice rows reviewed: `{sum(1 for row in role_slice if row['rows'])}` candidate-slice rows
- Most stable candidate: `{stable[0]['candidate_id'] if stable else ''}` with LOSO `{stable[0]['leave_one_season_out_positive_count'] if stable else ''}/{stable[0]['leave_one_season_out_total'] if stable else ''}`

## Recommendation

{recommendation}

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Source promotion remains blocked.
- No app/runtime/model behavior changed.
- No production winner was selected.
"""
    write_text(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_PREDECLARED_EXECUTION_V1_REPORT.md", report)

    advancement = f"""
# Diverse Champion Refinement Advancement Recommendation

Recommended next lane: `{recommendation}`

This recommendation remains review-only. No candidate is production-ready, ranking-ready, or approved for hidden sort/recommendation logic. Because this refinement tied or trailed the accepted Gauntlet references, the next step should improve the data substrate before another formula neighborhood sprint.
"""
    write_text(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_ADVANCEMENT_RECOMMENDATION.md", advancement)

    caveats = f"""
# Diverse Champion Refinement Blockers And Caveats

- This run used only review-only Formula Data Mart fields.
- No route/YPRR/TPRR, return scoring, broad PFR, PFR QB passing, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, exact Model v4 replay fields, or current/future context were used.
- Age/lifecycle and role-archetype effects are review-only context. They are not production boosts, penalties, formula approvals, ranking inputs, hidden sorts, or recommendation logic.
- The refinement grid was fixed before scoring and no dynamic optimization was run.
- Exact Model v4 replay remains blocked.
- Production/model-use and rankings integration remain blocked.
"""
    write_text(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_BLOCKERS_AND_CAVEATS.md", caveats)

    source_trace = f"""
# Diverse Champion Refinement Source Trace

## Primary Inputs

- Gauntlet Candidate Diversity / Clustering Audit V1: `{CLUSTERING_DIR}`
- Prior clustering audit commit: `{PRIOR_CLUSTERING_COMMIT}`
- Full Review-Only Formula Gauntlet Candidate Arena V1: `{GAUNTLET_DIR}`
- Prior full Gauntlet commit: `{PRIOR_GAUNTLET_COMMIT}`
- Medium Review-Only Formula Pilot V1: `{MEDIUM_DIR}`
- Small Review-Only Formula Pilot V1: `{SMALL_DIR}`
- Formula Data Mart / Feature Availability Audit V1: `{DATA_MART_DIR}`
- Age / Lifecycle Master Review V1: `{AGE_MASTER_DIR}`
- Role Archetype Master Review V1: `{ROLE_MASTER_DIR}`

## Method

The script imported the accepted full-Gauntlet runner for the review-only data mart loader, source/use-gate checks, ranking metrics, slice predicates, stability logic, and benchmark helpers. The refinement registry was built and written before scoring. No candidate formulas were changed after metrics were calculated.

## Safety

No push, merge, production source promotion, ranking/app/runtime/model behavior change, exact replay, or canonical `local_exports` write occurred.
"""
    write_text(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_SOURCE_TRACE.md", source_trace)

    return verdict, summary


def validate_outputs() -> None:
    required = [
        "DIVERSE_CHAMPION_REFINEMENT_PREDECLARED_EXECUTION_V1_REPORT.md",
        "DIVERSE_CHAMPION_REFINEMENT_CANDIDATE_REGISTRY.csv",
        "DIVERSE_CHAMPION_REFINEMENT_METRICS_SCORECARD.csv",
        "DIVERSE_CHAMPION_REFINEMENT_PYF_COMPARISON.csv",
        "DIVERSE_CHAMPION_REFINEMENT_POSITION_RESULTS.csv",
        "DIVERSE_CHAMPION_REFINEMENT_SEED_NEIGHBORHOOD_RESULTS.csv",
        "DIVERSE_CHAMPION_REFINEMENT_SLICE_GUARDRAILS.csv",
        "DIVERSE_CHAMPION_REFINEMENT_STABILITY_BY_SEASON.csv",
        "DIVERSE_CHAMPION_REFINEMENT_OUTLIER_INFLUENCE_REVIEW.csv",
        "DIVERSE_CHAMPION_REFINEMENT_LEADERBOARDS.md",
        "DIVERSE_CHAMPION_REFINEMENT_HARMFUL_CANDIDATES.md",
        "DIVERSE_CHAMPION_REFINEMENT_ADVANCEMENT_RECOMMENDATION.md",
        "DIVERSE_CHAMPION_REFINEMENT_BLOCKERS_AND_CAVEATS.md",
        "DIVERSE_CHAMPION_REFINEMENT_SOURCE_TRACE.md",
        "run_diverse_champion_refinement_predeclared_execution_v1.py",
    ]
    missing = [name for name in required if not (OUT_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"Missing outputs: {missing}")
    for path in OUT_DIR.glob("*.csv"):
        read_csv(path)
    py_compile.compile(__file__, doraise=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = G.load_panel()
    add_refinement_features(rows)
    registry = build_registry()
    validate_registry(registry)

    registry_fieldnames = [
        "candidate_id",
        "seed_candidate",
        "cluster_id",
        "seed_neighborhood",
        "formula_family",
        "formula_definition",
        "score_kind",
        "params",
        "input_fields",
        "weights",
        "position_scope",
        "source/use-gate status",
        "blocked_input_check",
        "leakage/as-of check status",
        "review_only_status",
        "required_comparator",
        "score_changes_allowed",
        "caveat",
    ]
    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_CANDIDATE_REGISTRY.csv", registry_rows(registry), registry_fieldnames)

    add_scores_and_ranks(rows, registry)
    scorecard, pyf_compare, position_rows = build_metric_rows(rows, registry)
    slice_rows = build_slice_rows(rows, registry)
    stability_rows = build_stability_rows(rows, registry)
    outlier_rows = build_outlier_rows(rows, registry, scorecard)
    seed_rows = seed_neighborhood_results(scorecard)

    scorecard_fields = list(scorecard[0].keys())
    pyf_fields = list(pyf_compare[0].keys())
    position_fields = list(position_rows[0].keys())
    slice_fields = list(slice_rows[0].keys())
    stability_fields = list(stability_rows[0].keys())
    outlier_fields = list(outlier_rows[0].keys())
    seed_fields = list(seed_rows[0].keys())

    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_METRICS_SCORECARD.csv", scorecard, scorecard_fields)
    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_PYF_COMPARISON.csv", pyf_compare, pyf_fields)
    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_POSITION_RESULTS.csv", position_rows, position_fields)
    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_SEED_NEIGHBORHOOD_RESULTS.csv", seed_rows, seed_fields)
    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_SLICE_GUARDRAILS.csv", slice_rows, slice_fields)
    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_STABILITY_BY_SEASON.csv", stability_rows, stability_fields)
    write_csv(OUT_DIR / "DIVERSE_CHAMPION_REFINEMENT_OUTLIER_INFLUENCE_REVIEW.csv", outlier_rows, outlier_fields)

    write_leaderboards(scorecard, position_rows, seed_rows, slice_rows, outlier_rows)
    write_harmful_candidates(scorecard, slice_rows, outlier_rows)
    verdict, summary = write_markdown_reports(rows, registry, scorecard, position_rows, seed_rows, slice_rows, outlier_rows)
    validate_outputs()
    print(
        "diverse_champion_refinement_complete "
        f"verdict={verdict} rows={summary['rows']} registered={summary['registered']} "
        f"scored={summary['scored']} beat_pyf={summary['beat_pyf']} "
        f"beat_gauntlet={summary['beat_gauntlet']} best={summary['best_overall']}"
    )


if __name__ == "__main__":
    main()
