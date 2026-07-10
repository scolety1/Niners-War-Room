from __future__ import annotations

import csv
import math
import py_compile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_MEDIUM_COMMIT = "bd0331d17a0bccee2c5d73d28d3a013822ddbee2"

MEDIUM_DIR = REPO / "docs/hq/model/medium_review_only_formula_pilot_v1_20260709"
MEDIUM_CONTRACT_DIR = REPO / "docs/hq/model/medium_review_only_formula_pilot_contract_v1_20260709"
SMALL_DIR = Path(
    r"C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709"
    r"\docs\hq\model\small_review_only_formula_pilot_v1_20260709"
)
DATA_MART_DIR = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
)
DATA_MART = DATA_MART_DIR / "FORMULA_DATA_MART_REVIEW_ONLY.csv"
UPGRADE_SWEEP_DIR = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-remaining-upgrade-sweep-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_remaining_upgrade_sweep_v1_20260709"
)
AGE_DIR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709"
    r"\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709"
)
AGE_SIDECAR = AGE_DIR / "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
AGE_MASTER_DIR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-master-review-v1-20260709"
    r"\docs\hq\master\age_lifecycle_master_review_v1_20260709"
)
ROLE_MASTER_DIR = REPO / "docs/hq/master/model_v4_role_archetype_master_review_v1_20260709"
CONFIDENCE_DIR = REPO / "docs/hq/model/model_v4_confidence_cap_component_signal_test_v1_20260709"
PFR_ADDENDUM_DIR = REPO / "docs/hq/master/nwr_full_system_audit_pfr_rb_broken_tackle_addendum_v1_20260709"
RED_ZONE_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-red-zone-exact-receipt-regeneration-pilot-v1-20260709"
    r"\docs\hq\data_hygiene\model_v4_red_zone_exact_receipt_regeneration_pilot_v1_20260709"
)

POSITIONS = ["QB", "RB", "WR", "TE"]
POSITION_TOPNS = {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
SLICE_NAMES = [
    "sparse_history",
    "low_games",
    "older_late_lifecycle",
    "young_early_lifecycle",
    "high_volume_role",
    "low_or_sparse_role",
    "prior_decline_proxy",
    "rb_high_touch_role",
    "receiver_high_target_role",
    "age_missing",
]


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
        out = float(text)
    except ValueError:
        return None
    return out if math.isfinite(out) else None


def bool_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def fmt(value: float | None, places: int = 3) -> str:
    return "" if value is None else f"{value:.{places}f}"


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.1f}%"


def mean(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def rmse(errors: list[float]) -> float | None:
    return math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else None


def rank_values(values: list[float]) -> list[float]:
    pairs = sorted((value, idx) for idx, value in enumerate(values))
    ranks = [0.0] * len(values)
    idx = 0
    while idx < len(pairs):
        end = idx + 1
        while end < len(pairs) and pairs[end][0] == pairs[idx][0]:
            end += 1
        avg_rank = (idx + 1 + end) / 2.0
        for _, original_idx in pairs[idx:end]:
            ranks[original_idx] = avg_rank
        idx = end
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = sum((x - mx) ** 2 for x in xs)
    den_y = sum((y - my) ** 2 for y in ys)
    if den_x <= 0 or den_y <= 0:
        return None
    return numerator / math.sqrt(den_x * den_y)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    return pearson(rank_values(xs), rank_values(ys)) if len(xs) >= 2 else None


def percentile(values: list[float], q: float) -> float | None:
    clean = sorted(v for v in values if v is not None)
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    idx = q * (len(clean) - 1)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return clean[lo]
    return clean[lo] * (hi - idx) + clean[hi] * (idx - lo)


def clamp(value: float | None, low: float | None, high: float | None) -> float | None:
    if value is None:
        return None
    if low is not None:
        value = max(value, low)
    if high is not None:
        value = min(value, high)
    return value


def is_high_volume_role(row: dict[str, object]) -> bool:
    return str(row.get("role_usage_bucket")) == "high_volume" or "_high_volume_" in str(row.get("role_archetype"))


def is_low_or_sparse_role(row: dict[str, object]) -> bool:
    return (
        str(row.get("role_usage_bucket")) == "low_volume"
        or "_low_volume_" in str(row.get("role_archetype"))
        or bool(row.get("sparse_history_bool"))
    )


def is_older_late(row: dict[str, object]) -> bool:
    return str(row.get("age_bucket")) == "age_32_plus" or str(row.get("lifecycle_bucket")) == "late_career_10_plus"


def is_young_early(row: dict[str, object]) -> bool:
    return str(row.get("age_bucket")) in {"under_23", "age_23_to_25"} or str(row.get("lifecycle_bucket")) == "early_career_1_to_3"


def is_prior_decline_proxy(row: dict[str, object]) -> bool:
    return is_high_volume_role(row) and (is_older_late(row) or bool(row.get("actual_startable")) is False)


def group_rows(rows: list[dict[str, object]], keys: tuple[str, ...]) -> dict[tuple[object, ...], list[dict[str, object]]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def assign_rank(rows: list[dict[str, object]], score_col: str, rank_col: str) -> None:
    for row in rows:
        row[rank_col] = None
    for group in group_rows(rows, ("season", "position")).values():
        eligible = [row for row in group if row.get(score_col) is not None]
        ordered = sorted(
            eligible,
            key=lambda row: (float(row[score_col]), str(row["player_id"]), str(row["substrate_row_id"])),
            reverse=True,
        )
        for idx, row in enumerate(ordered, start=1):
            row[rank_col] = float(idx)


def predicted_startable(row: dict[str, object], rank_col: str) -> bool:
    rank = row.get(rank_col)
    return bool(rank is not None and float(rank) <= STARTABLE_CUTOFF[str(row["position"])])


def top_precision(rows: list[dict[str, object]], rank_col: str, top_n: int) -> float | None:
    selected = [row for row in rows if row.get(rank_col) is not None and float(row[rank_col]) <= top_n]
    if not selected:
        return None
    return sum(1 for row in selected if row["actual_finish"] is not None and row["actual_finish"] <= top_n) / len(selected)


def reconstruct_history(row: dict[str, object]) -> None:
    y1 = row["pyf_score"]
    two = row["two_year_70_30"]
    three = row["three_year_60_30_10"]
    y2_available = (row["prior_2yr_years"] or 0.0) >= 2 and y1 is not None and two is not None
    y3_available = (row["prior_3yr_years"] or 0.0) >= 3 and y1 is not None and three is not None
    if y1 is None:
        row["n_minus_1_points"] = None
        row["n_minus_2_points"] = None
        row["n_minus_3_points"] = None
        row["history_reconstruction_status"] = "missing_prior_year_points"
        return
    y2 = (two - 0.70 * y1) / 0.30 if y2_available else y1
    y3 = (three - 0.60 * y1 - 0.30 * y2) / 0.10 if y3_available else y2
    row["n_minus_1_points"] = y1
    row["n_minus_2_points"] = y2
    row["n_minus_3_points"] = y3
    row["history_reconstruction_status"] = ";".join(
        [
            "n_minus_2_reconstructed_from_70_30" if y2_available else "n_minus_2_fallback_to_n_minus_1",
            "n_minus_3_reconstructed_from_60_30_10" if y3_available else "n_minus_3_fallback_to_n_minus_2",
        ]
    )


def weighted2(row: dict[str, object], w1: float, w2: float) -> float | None:
    y1 = row["n_minus_1_points"]
    y2 = row["n_minus_2_points"]
    return None if y1 is None or y2 is None else w1 * y1 + w2 * y2


def weighted3(row: dict[str, object], w1: float, w2: float, w3: float) -> float | None:
    y1 = row["n_minus_1_points"]
    y2 = row["n_minus_2_points"]
    y3 = row["n_minus_3_points"]
    return None if y1 is None or y2 is None or y3 is None else w1 * y1 + w2 * y2 + w3 * y3


def exp2(row: dict[str, object], recent_weight: float) -> float | None:
    return weighted2(row, recent_weight, 1.0 - recent_weight)


def exp3(row: dict[str, object], decay: float) -> float | None:
    weights = [1.0, decay, decay * decay]
    total = sum(weights)
    return weighted3(row, weights[0] / total, weights[1] / total, weights[2] / total)


def normalize_group_scores(rows: list[dict[str, object]], columns: list[str]) -> None:
    for col in columns:
        for group in group_rows(rows, ("season", "position")).values():
            vals = [row[col] for row in group if row.get(col) is not None]
            m = mean(vals)
            if m is None:
                for row in group:
                    row[f"{col}_z"] = None
                continue
            variance = sum((v - m) ** 2 for v in vals) / len(vals) if vals else 0.0
            sd = math.sqrt(variance)
            for row in group:
                value = row.get(col)
                row[f"{col}_z"] = None if value is None or sd <= 0 else (float(value) - m) / sd


def load_panel() -> list[dict[str, object]]:
    mart = read_csv(DATA_MART)
    ages = read_csv(AGE_SIDECAR)
    age_key = {(r["player_id"], r["season"], r["position"]): r for r in ages}
    if len(age_key) != len(ages):
        raise RuntimeError("Age/lifecycle sidecar has duplicate player_id+season+position keys.")
    rows: list[dict[str, object]] = []
    for row in mart:
        key = (row["player_id"], row["season"], row["position"])
        age = age_key.get(key)
        if age is None:
            raise RuntimeError(f"Missing age/lifecycle sidecar row for {key}.")
        out: dict[str, object] = dict(row)
        out["season"] = str(row["season"])
        out["position"] = str(row["position"])
        out["player_id"] = str(row["player_id"])
        out["player_name"] = str(row.get("player_name") or row.get("target_player_name") or "")
        out["substrate_row_id"] = str(row["substrate_row_id"])
        out["actual_finish"] = num(row["label_next_position_finish"])
        out["actual_points"] = num(row["label_next_nwr_points"])
        out["actual_startable"] = bool_true(row["label_startable_hit"])
        out["pyf_score"] = num(row["pyf_prior_nwr_points"])
        out["pyf_ppg"] = num(row["pyf_prior_nwr_ppg"])
        out["pyf_prior_rank"] = num(row["pyf_prior_rank_position_feature_season"])
        out["rank_inverse"] = -out["pyf_prior_rank"] if out["pyf_prior_rank"] is not None else None
        out["two_year_70_30"] = num(row["prior_2yr_weighted_nwr_points"])
        out["three_year_60_30_10"] = num(row["prior_3yr_weighted_nwr_points"])
        out["prior_2yr_years"] = num(row["prior_2yr_points_years_available"]) or 0.0
        out["prior_3yr_years"] = num(row["prior_3yr_points_years_available"]) or 0.0
        out["prior_games_num"] = num(row["prior_games"]) or 0.0
        out["prior_touches_num"] = num(row["prior_touches"]) or 0.0
        out["prior_targets_num"] = num(row["prior_targets"]) or 0.0
        out["sparse_history_bool"] = bool_true(row["sparse_history_flag"])
        out["low_games_bool"] = bool_true(row["low_games_flag"])
        out["role_archetype"] = str(row["role_archetype"])
        out["role_usage_bucket"] = str(row["role_usage_bucket"])
        out["confidence_status"] = str(row["confidence_status"])
        out["confidence_cap_value_num"] = num(row["confidence_cap_value"])
        out["age"] = num(age.get("age"))
        out["age_bucket"] = age.get("age_bucket", "")
        out["lifecycle_bucket"] = age.get("lifecycle_bucket", "")
        out["career_stage"] = age.get("career_stage", "")
        out["age_missing"] = out["age"] is None
        out["age_leakage_flag"] = age.get("leakage_flag", "")
        out["age_identity_flag"] = age.get("identity_flag", "")
        reconstruct_history(out)
        rows.append(out)
    validate_source_use_gates(rows)
    normalize_group_scores(rows, ["pyf_score", "pyf_ppg", "rank_inverse", "two_year_70_30", "three_year_60_30_10"])
    return rows


def validate_source_use_gates(rows: list[dict[str, object]]) -> None:
    if len(rows) != 5518:
        raise RuntimeError(f"Unexpected data mart row count {len(rows)}; expected 5518.")
    if any(str(row.get("review_only")).strip().lower() != "true" for row in rows):
        raise RuntimeError("Formula Data Mart contains non-review-only rows.")
    if any(str(row.get("model_use_allowed")).strip().lower() == "true" for row in rows):
        raise RuntimeError("Formula Data Mart contains model-use rows.")
    if any(str(row.get("production_approved")).strip().lower() == "true" for row in rows):
        raise RuntimeError("Formula Data Mart contains production-approved rows.")
    if any(not str(row.get("leakage_check_result")).startswith("PASS") for row in rows):
        raise RuntimeError("Formula Data Mart leakage check has non-PASS rows.")
    if any(not str(row.get("asof_check_result")).startswith("PASS") for row in rows):
        raise RuntimeError("Formula Data Mart as-of check has non-PASS rows.")
    age_blocked = [
        row
        for row in rows
        if not str(row.get("age_leakage_flag")).startswith("PASS")
        and str(row.get("age_leakage_flag")) != "NOT_USABLE_FOR_AGE_SIGNAL_WHEN_BIRTHDATE_MISSING"
    ]
    if age_blocked:
        raise RuntimeError(f"Age/lifecycle blocked leakage rows found: {len(age_blocked)}")


def candidate(
    cid: str,
    family: str,
    label: str,
    kind: str,
    params: dict[str, Any] | None = None,
    positions: str = "QB/RB/WR/TE",
    status: str = "ACTIVE_REVIEW_ONLY",
    blocked_reason: str = "",
    caveat: str = "fixed_review_only_no_tuning",
) -> dict[str, Any]:
    return {
        "candidate_id": cid,
        "candidate_family": family,
        "candidate_label": label,
        "score_kind": kind,
        "params": params or {},
        "position_scope": positions,
        "candidate_status": status,
        "blocked_reason": blocked_reason,
        "score_changes_allowed": "yes" if status == "ACTIVE_REVIEW_ONLY" and kind not in {"diagnostic_pyf", "diagnostic_three"} else "no",
        "review_only_use": "review_only_formula_candidate" if status == "ACTIVE_REVIEW_ONLY" else "blocked_or_not_tested",
        "required_comparator": "PYF",
        "formula_definition": label,
        "caveat": caveat,
    }


def build_registry() -> list[dict[str, Any]]:
    reg: list[dict[str, Any]] = []
    add = reg.append
    seq = 1

    def cid(slug: str) -> str:
        nonlocal seq
        out = f"GAUNTLET_{seq:03d}_{slug}"
        seq += 1
        return out

    # A. PYF / simple baseline family
    add(candidate(cid("PYF_POINTS_ANCHOR"), "A_PYF_SIMPLE_BASELINE", "score=pyf_prior_nwr_points", "pyf"))
    add(candidate(cid("PYF_PRIOR_RANK_ANCHOR"), "A_PYF_SIMPLE_BASELINE", "score=inverse_pyf_prior_rank", "rank_inverse"))
    add(candidate(cid("PRIOR_YEAR_PPG_BASELINE"), "A_PYF_SIMPLE_BASELINE", "score=pyf_prior_nwr_ppg", "ppg"))
    add(candidate(cid("PYF_WINSOR_05"), "A_PYF_SIMPLE_BASELINE", "score=winsorized_pyf_5_95", "winsor", {"base": "pyf", "low": 0.05, "high": 0.95}))
    add(candidate(cid("PYF_WINSOR_10"), "A_PYF_SIMPLE_BASELINE", "score=winsorized_pyf_10_90", "winsor", {"base": "pyf", "low": 0.10, "high": 0.90}))

    # B. Two-year weighted production
    for w1, w2 in [(0.90, 0.10), (0.85, 0.15), (0.80, 0.20), (0.75, 0.25), (0.70, 0.30), (0.65, 0.35), (0.60, 0.40), (0.55, 0.45), (0.50, 0.50)]:
        add(candidate(cid(f"TWO_YEAR_{int(w1*100)}_{int(w2*100)}"), "B_TWO_YEAR_WEIGHTED_PRODUCTION", f"score={w1:.2f}*N1+{w2:.2f}*N2", "two", {"w1": w1, "w2": w2}))

    # C. Three-year weighted production
    for w1, w2, w3 in [(0.80, 0.15, 0.05), (0.75, 0.20, 0.05), (0.70, 0.20, 0.10), (0.65, 0.25, 0.10), (0.60, 0.30, 0.10), (0.55, 0.30, 0.15), (0.50, 0.35, 0.15), (0.50, 0.30, 0.20), (0.45, 0.35, 0.20), (0.40, 0.35, 0.25)]:
        add(candidate(cid(f"THREE_YEAR_{int(w1*100)}_{int(w2*100)}_{int(w3*100)}"), "C_THREE_YEAR_WEIGHTED_PRODUCTION", f"score={w1:.2f}*N1+{w2:.2f}*N2+{w3:.2f}*N3", "three", {"w1": w1, "w2": w2, "w3": w3}))

    # D. Exponential decay production
    for w in [0.90, 0.80, 0.70, 0.60]:
        add(candidate(cid(f"EXP2_RECENT_{int(w*100)}"), "D_EXPONENTIAL_DECAY_PRODUCTION", f"score=exp2_recent_weight_{w:.2f}", "exp2", {"recent": w}))
    for decay in [0.75, 0.60, 0.50, 0.40]:
        add(candidate(cid(f"EXP3_DECAY_{int(decay*100)}"), "D_EXPONENTIAL_DECAY_PRODUCTION", f"score=exp3_decay_{decay:.2f}", "exp3", {"decay": decay}))

    # E. Position-specific production
    pos_defs = {
        "QB": [(0.85, 0.15), (0.75, 0.25), (0.70, 0.30), (0.70, 0.20, 0.10), (0.65, 0.25, 0.10), (0.60, 0.30, 0.10), (0.55, 0.30, 0.15)],
        "RB": [(0.85, 0.15), (0.75, 0.25), (0.70, 0.30), (0.75, 0.20, 0.05), (0.70, 0.20, 0.10), (0.60, 0.30, 0.10), (0.55, 0.30, 0.15)],
        "WR": [(0.80, 0.20), (0.75, 0.25), (0.70, 0.30), (0.70, 0.20, 0.10), (0.65, 0.25, 0.10), (0.60, 0.30, 0.10), (0.55, 0.30, 0.15)],
        "TE": [(0.80, 0.20), (0.75, 0.25), (0.70, 0.30), (0.75, 0.20, 0.05), (0.70, 0.20, 0.10), (0.65, 0.25, 0.10), (0.60, 0.30, 0.10)],
    }
    for pos, defs in pos_defs.items():
        for weights in defs:
            if len(weights) == 2:
                w1, w2 = weights
                add(candidate(cid(f"{pos}_TWO_{int(w1*100)}_{int(w2*100)}"), "E_POSITION_SPECIFIC_PRODUCTION", f"{pos}_only_two_year_{w1:.2f}_{w2:.2f}", "two", {"w1": w1, "w2": w2}, pos))
            else:
                w1, w2, w3 = weights
                add(candidate(cid(f"{pos}_THREE_{int(w1*100)}_{int(w2*100)}_{int(w3*100)}"), "E_POSITION_SPECIFIC_PRODUCTION", f"{pos}_only_three_year_{w1:.2f}_{w2:.2f}_{w3:.2f}", "three", {"w1": w1, "w2": w2, "w3": w3}, pos))

    # F. Sparse-history guarded family
    sparse_defs = [("two", {"w1": 0.80, "w2": 0.20}), ("two", {"w1": 0.70, "w2": 0.30}), ("two", {"w1": 0.60, "w2": 0.40}), ("three", {"w1": 0.70, "w2": 0.20, "w3": 0.10}), ("three", {"w1": 0.65, "w2": 0.25, "w3": 0.10}), ("three", {"w1": 0.60, "w2": 0.30, "w3": 0.10}), ("three", {"w1": 0.55, "w2": 0.30, "w3": 0.15}), ("two", {"w1": 0.50, "w2": 0.50})]
    for kind, params in sparse_defs:
        add(candidate(cid(f"SPARSE_FALLBACK_{kind.upper()}_{len(reg)}"), "F_SPARSE_HISTORY_GUARD", "if_sparse_then_PYF_else_base", "sparse_guard", {"base": kind, **params}, caveat="guardrail_review_only_not_penalty"))

    # G. Low-games guarded family
    for kind, params in sparse_defs:
        add(candidate(cid(f"LOW_GAMES_FALLBACK_{kind.upper()}_{len(reg)}"), "G_LOW_GAMES_GUARD", "if_low_games_then_PYF_else_base", "low_games_guard", {"base": kind, **params}, caveat="guardrail_review_only_not_penalty"))

    # H. Prior-production decline guard family
    decline_defs = [
        ("THREE_CONTEXT", "diagnostic_three", {}),
        ("HIGH_VOLUME_DIAGNOSTIC", "diagnostic_pyf", {}),
        ("LATE_LIFECYCLE_DIAGNOSTIC", "diagnostic_pyf", {}),
        ("AGE_ROLE_CROSS_SLICE", "diagnostic_three", {}),
        ("SMALL_LATE_GUARD_THREE", "modifier", {"base": "three_60_30_10", "mods": ["late_guard"]}),
        ("SMALL_HIGH_VOLUME_LATE_GUARD", "modifier", {"base": "three_60_30_10", "mods": ["high_volume_late_guard"]}),
        ("DECLINE_COMBO_GUARD", "modifier", {"base": "three_65_25_10", "mods": ["late_guard", "high_volume_late_guard"]}),
    ]
    for slug, kind, params in decline_defs:
        add(candidate(cid(f"DECLINE_{slug}"), "H_PRIOR_PRODUCTION_DECLINE_GUARD", f"prior_decline_{slug.lower()}", kind, params, caveat="review_only_decline_context_no_production_penalty"))

    # I. Age/lifecycle context family
    age_defs = [
        ("LIFECYCLE_THREE_REPORT", "diagnostic_three", {}),
        ("LATE_CAREER_REVIEW", "diagnostic_pyf", {}),
        ("YOUNG_BREAKOUT_REVIEW", "diagnostic_pyf", {}),
        ("POSITION_AGE_CURVE_REPORT", "diagnostic_pyf", {}),
        ("THREE_SMALL_LATE_GUARD", "modifier", {"base": "three_60_30_10", "mods": ["late_guard"]}),
        ("TWO_YOUNG_CONTEXT", "modifier", {"base": "two_70_30", "mods": ["young_context"]}),
        ("THREE_YOUNG_NOT_SPARSE_CONTEXT", "modifier", {"base": "three_60_30_10", "mods": ["young_not_sparse_context"]}),
    ]
    for slug, kind, params in age_defs:
        add(candidate(cid(f"AGE_{slug}"), "I_AGE_LIFECYCLE_CONTEXT", f"age_lifecycle_{slug.lower()}", kind, params, caveat="review_only_age_context_not_rank_input"))

    # J. Role archetype context family
    role_defs = [
        ("HIGH_VOLUME_REPORT", "diagnostic_three", {}),
        ("LOW_SPARSE_REPORT", "diagnostic_pyf", {}),
        ("RB_TOUCH_ROLE_REPORT", "diagnostic_three", {}, "RB"),
        ("WR_TE_TARGET_ROLE_REPORT", "diagnostic_three", {}, "WR/TE"),
        ("HIGH_VOLUME_LATE_GUARD", "modifier", {"base": "three_60_30_10", "mods": ["high_volume_late_guard"]}),
        ("LOW_SPARSE_YOUNG_CONTEXT", "modifier", {"base": "two_70_30", "mods": ["low_sparse_young_context"]}),
        ("ROLE_BALANCED_CONTEXT", "modifier", {"base": "three_65_25_10", "mods": ["high_volume_late_guard", "low_sparse_young_context"]}),
    ]
    for item in role_defs:
        slug, kind, params = item[0], item[1], item[2]
        positions = item[3] if len(item) > 3 else "QB/RB/WR/TE"
        add(candidate(cid(f"ROLE_{slug}"), "J_ROLE_ARCHETYPE_CONTEXT", f"role_archetype_{slug.lower()}", kind, params, positions, caveat="review_only_role_context_not_rank_input"))

    # K. Hybrid production + age/role family
    hybrid_defs = [
        ("THREE_60_ROLE_AGE_SMALL", "modifier", {"base": "three_60_30_10", "mods": ["late_guard", "low_sparse_young_context"]}),
        ("THREE_65_ROLE_AGE_SMALL", "modifier", {"base": "three_65_25_10", "mods": ["late_guard", "young_not_sparse_context"]}),
        ("TWO_70_ROLE_AGE_SMALL", "modifier", {"base": "two_70_30", "mods": ["high_volume_late_guard", "young_context"]}),
        ("QB_THREE_55_AGE_ROLE", "modifier", {"base": "three_55_30_15", "mods": ["late_guard"]}, "QB"),
        ("RB_THREE_60_ROLE_AGE", "modifier", {"base": "three_60_30_10", "mods": ["high_volume_late_guard"]}, "RB"),
        ("WR_TE_THREE_65_ROLE_AGE", "modifier", {"base": "three_65_25_10", "mods": ["low_sparse_young_context"]}, "WR/TE"),
    ]
    for item in hybrid_defs:
        slug, kind, params = item[0], item[1], item[2]
        positions = item[3] if len(item) > 3 else "QB/RB/WR/TE"
        add(candidate(cid(f"HYBRID_{slug}"), "K_HYBRID_PRODUCTION_AGE_ROLE", f"hybrid_{slug.lower()}", kind, params, positions, caveat="small_review_only_modifier_not_production_logic"))

    # L. Robust / winsorized production family
    robust_defs = [
        ("WINSOR_PYF_05", "pyf", 0.05, 0.95),
        ("WINSOR_TWO_70_05", "two_70_30", 0.05, 0.95),
        ("WINSOR_THREE_60_05", "three_60_30_10", 0.05, 0.95),
        ("WINSOR_PYF_10", "pyf", 0.10, 0.90),
        ("WINSOR_TWO_70_10", "two_70_30", 0.10, 0.90),
        ("WINSOR_THREE_60_10", "three_60_30_10", 0.10, 0.90),
        ("ROBUST_RANK_THREE", "three_60_30_10", 0.02, 0.98),
    ]
    for slug, base, low, high in robust_defs:
        add(candidate(cid(f"ROBUST_{slug}"), "L_ROBUST_WINSORIZED_PRODUCTION", f"robust_{slug.lower()}", "winsor", {"base": base, "low": low, "high": high}, caveat="outlier_reduction_review_only"))

    # M. Hybrid rank / points family
    hybrid_rank_defs = [
        ("PYF_POINTS_RANK_80_20", 0.80, 0.20, "pyf_score_z", "rank_inverse_z"),
        ("PYF_POINTS_RANK_60_40", 0.60, 0.40, "pyf_score_z", "rank_inverse_z"),
        ("TWO_POINTS_RANK_70_30", 0.70, 0.30, "two_year_70_30_z", "rank_inverse_z"),
        ("THREE_POINTS_RANK_70_30", 0.70, 0.30, "three_year_60_30_10_z", "rank_inverse_z"),
    ]
    for slug, w1, w2, left, right in hybrid_rank_defs:
        add(candidate(cid(f"RANK_POINTS_{slug}"), "M_HYBRID_RANK_POINTS", f"rank_points_{slug.lower()}", "z_hybrid", {"w1": w1, "w2": w2, "left": left, "right": right}, caveat="rank_points_review_only"))

    # N. RB-only broken tackle context family. Actual values are not in the Formula Data Mart.
    for slug in ["PFR_RB_BRK_TKL_RAW", "PFR_RB_BRK_TKL_PER_GAME", "PFR_RB_BRK_TKL_PER_ATTEMPT_DIAGNOSTIC"]:
        add(candidate(cid(slug), "N_RB_ONLY_BROKEN_TACKLE_CONTEXT", slug.lower(), "blocked", positions="RB", status="BLOCKED_OR_INVALID", blocked_reason="actual_pfr_broken_tackle_values_not_in_formula_data_mart", caveat="pfr_not_production_approved"))

    # O. Partial red-zone context family. Safe only for 2024-2025 lagged review use, not full 2013-2025 comparison.
    for slug in ["RED_ZONE_CARRIES_PARTIAL", "RED_ZONE_TARGETS_PARTIAL", "RED_ZONE_TD_OPPORTUNITY_PARTIAL"]:
        add(candidate(cid(slug), "O_PARTIAL_RED_ZONE_CONTEXT", slug.lower(), "blocked", status="BLOCKED_OR_INVALID", blocked_reason="partial_2024_2025_only_not_fair_for_2013_2025_gauntlet", caveat="red_zone_partial_review_only_with_caveats"))

    if len(reg) != 120:
        raise RuntimeError(f"Registry count {len(reg)} != 120")
    return reg


def scope_positions(scope: str) -> set[str]:
    if scope == "QB/RB/WR/TE":
        return set(POSITIONS)
    if scope == "WR/TE":
        return {"WR", "TE"}
    return {scope}


def base_score(row: dict[str, object], base: str) -> float | None:
    if base == "pyf":
        return row["pyf_score"]
    if base == "two_70_30":
        return row["two_year_70_30"]
    if base == "three_60_30_10":
        return row["three_year_60_30_10"]
    if base == "three_65_25_10":
        return weighted3(row, 0.65, 0.25, 0.10)
    if base == "three_55_30_15":
        return weighted3(row, 0.55, 0.30, 0.15)
    raise KeyError(base)


def apply_modifiers(score: float | None, row: dict[str, object], mods: list[str]) -> float | None:
    if score is None:
        return None
    factor = 1.0
    for mod in mods:
        if mod == "late_guard" and is_older_late(row):
            factor *= 0.98
        elif mod == "high_volume_late_guard" and is_high_volume_role(row) and is_older_late(row):
            factor *= 0.96
        elif mod == "young_context" and is_young_early(row):
            factor *= 1.01
        elif mod == "young_not_sparse_context" and is_young_early(row) and not row["sparse_history_bool"]:
            factor *= 1.015
        elif mod == "low_sparse_young_context" and is_low_or_sparse_role(row) and is_young_early(row):
            factor *= 1.01
    return score * factor


def raw_score(candidate_row: dict[str, Any], row: dict[str, object]) -> float | None:
    if candidate_row["candidate_status"] != "ACTIVE_REVIEW_ONLY":
        return None
    if row["position"] not in scope_positions(candidate_row["position_scope"]):
        return None
    kind = candidate_row["score_kind"]
    params = candidate_row["params"]
    if kind == "pyf":
        return row["pyf_score"]
    if kind == "rank_inverse":
        return row["rank_inverse"]
    if kind == "ppg":
        return row["pyf_ppg"]
    if kind == "two":
        return weighted2(row, params["w1"], params["w2"])
    if kind == "three":
        return weighted3(row, params["w1"], params["w2"], params["w3"])
    if kind == "exp2":
        return exp2(row, params["recent"])
    if kind == "exp3":
        return exp3(row, params["decay"])
    if kind == "sparse_guard":
        if row["sparse_history_bool"]:
            return row["pyf_score"]
        return weighted2(row, params["w1"], params["w2"]) if params["base"] == "two" else weighted3(row, params["w1"], params["w2"], params["w3"])
    if kind == "low_games_guard":
        if row["low_games_bool"]:
            return row["pyf_score"]
        return weighted2(row, params["w1"], params["w2"]) if params["base"] == "two" else weighted3(row, params["w1"], params["w2"], params["w3"])
    if kind == "diagnostic_pyf":
        return row["pyf_score"]
    if kind == "diagnostic_three":
        return row["three_year_60_30_10"]
    if kind == "modifier":
        return apply_modifiers(base_score(row, params["base"]), row, list(params["mods"]))
    if kind == "winsor":
        return base_score(row, params["base"])
    if kind == "z_hybrid":
        left = row.get(params["left"])
        right = row.get(params["right"])
        if left is None or right is None:
            return None
        return params["w1"] * float(left) + params["w2"] * float(right)
    if kind == "blocked":
        return None
    raise KeyError(kind)


def add_scores_and_ranks(rows: list[dict[str, object]], registry: list[dict[str, Any]]) -> None:
    for row in rows:
        for cand in registry:
            row[f"{cand['candidate_id']}_score"] = raw_score(cand, row)
    for cand in registry:
        if cand["score_kind"] == "winsor" and cand["candidate_status"] == "ACTIVE_REVIEW_ONLY":
            score_col = f"{cand['candidate_id']}_score"
            for group in group_rows(rows, ("season", "position")).values():
                vals = [row[score_col] for row in group if row.get(score_col) is not None]
                low = percentile(vals, cand["params"]["low"])
                high = percentile(vals, cand["params"]["high"])
                for row in group:
                    row[score_col] = clamp(row.get(score_col), low, high)
        assign_rank(rows, f"{cand['candidate_id']}_score", f"{cand['candidate_id']}_rank")


def candidate_scope(cand: dict[str, Any], rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], str]:
    positions = scope_positions(cand["position_scope"])
    scoped = [
        row
        for row in rows
        if str(row["position"]) in positions and row.get(f"{cand['candidate_id']}_rank") is not None
    ]
    return scoped, "/".join([pos for pos in POSITIONS if pos in positions])


def metrics_for_rows(rows: list[dict[str, object]], rank_col: str) -> dict[str, object]:
    eligible = [row for row in rows if row.get(rank_col) is not None and row["actual_finish"] is not None]
    ranks = [float(row[rank_col]) for row in eligible]
    finishes = [float(row["actual_finish"]) for row in eligible]
    errors = [rank - finish for rank, finish in zip(ranks, finishes)]
    pred = [row for row in eligible if predicted_startable(row, rank_col)]
    false_pos = [row for row in eligible if predicted_startable(row, rank_col) and not row["actual_startable"]]
    false_neg = [row for row in eligible if not predicted_startable(row, rank_col) and row["actual_startable"]]
    sparse = [row for row in eligible if row["sparse_history_bool"]]
    low_games = [row for row in eligible if row["low_games_bool"]]
    sparse_errors = [row for row in sparse if predicted_startable(row, rank_col) != bool(row["actual_startable"])]
    low_games_errors = [row for row in low_games if predicted_startable(row, rank_col) != bool(row["actual_startable"])]
    return {
        "rows": len(eligible),
        "spearman": spearman(ranks, finishes),
        "mae": mean([abs(error) for error in errors]),
        "rmse": rmse(errors),
        "startable_precision": (sum(1 for row in pred if row["actual_startable"]) / len(pred)) if pred else None,
        "predicted_startable_rows": len(pred),
        "false_positives": len(false_pos),
        "false_negatives": len(false_neg),
        "sparse_rows": len(sparse),
        "sparse_error_rate": (len(sparse_errors) / len(sparse)) if sparse else None,
        "low_games_rows": len(low_games),
        "low_games_error_rate": (len(low_games_errors) / len(low_games)) if low_games else None,
    }


def metric_delta(left: float | None, right: float | None) -> float | None:
    return None if left is None or right is None else left - right


def build_metric_rows(
    rows: list[dict[str, object]], registry: list[dict[str, Any]]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    pyf_rank = "GAUNTLET_001_PYF_POINTS_ANCHOR_rank"
    scorecard: list[dict[str, object]] = []
    pyf_compare: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []
    for cand in registry:
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        if cand["candidate_status"] != "ACTIVE_REVIEW_ONLY":
            scorecard.append(blocked_scorecard_row(cand, scope))
            pyf_compare.append(blocked_pyf_row(cand, scope))
            continue
        cm = metrics_for_rows(scoped, rank_col)
        pm = metrics_for_rows(scoped, pyf_rank)
        sd = metric_delta(cm["spearman"], pm["spearman"])
        pd = metric_delta(cm["startable_precision"], pm["startable_precision"])
        sparse_delta = metric_delta(cm["sparse_error_rate"], pm["sparse_error_rate"])
        low_delta = metric_delta(cm["low_games_error_rate"], pm["low_games_error_rate"])
        beats_pyf = bool(sd is not None and sd > 0.0005)
        context_only = cand["score_changes_allowed"] == "no" and cand["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"
        if cand["candidate_id"] == "GAUNTLET_001_PYF_POINTS_ANCHOR":
            interpretation = "MIXED_REVIEW_ONLY"
            comparison = "mandatory_pyf_anchor_not_new_formula"
        elif context_only:
            interpretation = "MIXED_REVIEW_ONLY"
            comparison = "contextualizes_pyf"
        elif beats_pyf:
            interpretation = "PROMISING_REVIEW_ONLY"
            comparison = "beats_pyf"
        elif sd is not None and sd < -0.0005:
            interpretation = "FAILED_VS_PYF"
            comparison = "does_not_beat_pyf"
        else:
            interpretation = "WEAK_REVIEW_ONLY"
            comparison = "roughly_matches_pyf"
        scorecard.append(
            {
                "candidate_id": cand["candidate_id"],
                "candidate_family": cand["candidate_family"],
                "candidate_label": cand["candidate_label"],
                "candidate_status": cand["candidate_status"],
                "score_changes_allowed": cand["score_changes_allowed"],
                "scope": scope,
                "rows_tested": cm["rows"],
                "candidate_spearman": fmt(cm["spearman"]),
                "pyf_spearman_comparable": fmt(pm["spearman"]),
                "spearman_delta_vs_pyf": fmt(sd),
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
                "beats_pyf_overall": str(beats_pyf).lower(),
                "contextualizes_pyf": str(context_only).lower(),
                "interpretation": interpretation,
                "comparison_result": comparison,
                "blocked_reason": "",
                "caveat": cand["caveat"],
            }
        )
        pyf_compare.append(
            {
                "candidate_id": cand["candidate_id"],
                "candidate_family": cand["candidate_family"],
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
                "beat_pyf": str(beats_pyf).lower(),
                "comparison_result": comparison,
            }
        )
        for position in POSITIONS:
            pos_rows = [row for row in scoped if row["position"] == position]
            if not pos_rows:
                continue
            pcm = metrics_for_rows(pos_rows, rank_col)
            ppm = metrics_for_rows(pos_rows, pyf_rank)
            psd = metric_delta(pcm["spearman"], ppm["spearman"])
            top_values: dict[str, object] = {}
            for top_n in [12, 24, 36]:
                if top_n in POSITION_TOPNS[position]:
                    top_values[f"top_{top_n}_precision"] = pct(top_precision(pos_rows, rank_col, top_n))
                    top_values[f"pyf_top_{top_n}_precision"] = pct(top_precision(pos_rows, pyf_rank, top_n))
                else:
                    top_values[f"top_{top_n}_precision"] = ""
                    top_values[f"pyf_top_{top_n}_precision"] = ""
            position_rows.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "candidate_family": cand["candidate_family"],
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


def blocked_scorecard_row(cand: dict[str, Any], scope: str) -> dict[str, object]:
    return {
        "candidate_id": cand["candidate_id"],
        "candidate_family": cand["candidate_family"],
        "candidate_label": cand["candidate_label"],
        "candidate_status": cand["candidate_status"],
        "score_changes_allowed": cand["score_changes_allowed"],
        "scope": scope,
        "rows_tested": 0,
        "candidate_spearman": "",
        "pyf_spearman_comparable": "",
        "spearman_delta_vs_pyf": "",
        "mae_rank_vs_finish": "",
        "rmse_rank_vs_finish": "",
        "startable_precision": "",
        "pyf_startable_precision_comparable": "",
        "startable_precision_delta_vs_pyf": "",
        "candidate_false_positives": "",
        "pyf_false_positives_comparable": "",
        "false_positive_delta_vs_pyf": "",
        "candidate_false_negatives": "",
        "pyf_false_negatives_comparable": "",
        "false_negative_delta_vs_pyf": "",
        "sparse_history_error_delta_vs_pyf": "",
        "low_games_error_delta_vs_pyf": "",
        "beats_pyf_overall": "false",
        "contextualizes_pyf": "false",
        "interpretation": "BLOCKED_OR_INVALID",
        "comparison_result": "blocked_or_invalid",
        "blocked_reason": cand["blocked_reason"],
        "caveat": cand["caveat"],
    }


def blocked_pyf_row(cand: dict[str, Any], scope: str) -> dict[str, object]:
    return {
        "candidate_id": cand["candidate_id"],
        "candidate_family": cand["candidate_family"],
        "scope": scope,
        "candidate_spearman": "",
        "pyf_spearman": "",
        "spearman_delta": "",
        "candidate_startable_precision": "",
        "pyf_startable_precision": "",
        "startable_precision_delta": "",
        "candidate_false_positives": "",
        "pyf_false_positives": "",
        "false_positive_delta": "",
        "candidate_false_negatives": "",
        "pyf_false_negatives": "",
        "false_negative_delta": "",
        "beat_pyf": "false",
        "comparison_result": "blocked_or_invalid",
    }


def slice_predicates() -> dict[str, Callable[[dict[str, object]], bool]]:
    return {
        "sparse_history": lambda r: bool(r["sparse_history_bool"]),
        "low_games": lambda r: bool(r["low_games_bool"]),
        "older_late_lifecycle": is_older_late,
        "young_early_lifecycle": is_young_early,
        "high_volume_role": is_high_volume_role,
        "low_or_sparse_role": is_low_or_sparse_role,
        "prior_decline_proxy": is_prior_decline_proxy,
        "rb_high_touch_role": lambda r: r["position"] == "RB" and is_high_volume_role(r),
        "receiver_high_target_role": lambda r: r["position"] in {"WR", "TE"} and is_high_volume_role(r),
        "age_missing": lambda r: bool(r["age_missing"]),
    }


def build_slice_rows(rows: list[dict[str, object]], registry: list[dict[str, Any]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    pyf_rank = "GAUNTLET_001_PYF_POINTS_ANCHOR_rank"
    predicates = slice_predicates()
    for cand in registry:
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        if cand["candidate_status"] != "ACTIVE_REVIEW_ONLY":
            for slice_name in SLICE_NAMES:
                output.append(blocked_slice_row(cand, slice_name, scope))
            continue
        for slice_name, predicate in predicates.items():
            group = [row for row in scoped if predicate(row)]
            if not group:
                output.append(empty_slice_row(cand, slice_name, scope))
                continue
            cand_fp = [row for row in group if predicted_startable(row, rank_col) and not row["actual_startable"]]
            cand_fn = [row for row in group if not predicted_startable(row, rank_col) and row["actual_startable"]]
            pyf_fp = [row for row in group if predicted_startable(row, pyf_rank) and not row["actual_startable"]]
            pyf_fn = [row for row in group if not predicted_startable(row, pyf_rank) and row["actual_startable"]]
            cand_error = (len(cand_fp) + len(cand_fn)) / len(group)
            pyf_error = (len(pyf_fp) + len(pyf_fn)) / len(group)
            delta = cand_error - pyf_error
            output.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "candidate_family": cand["candidate_family"],
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


def empty_slice_row(cand: dict[str, Any], slice_name: str, scope: str) -> dict[str, object]:
    return {
        "candidate_id": cand["candidate_id"],
        "candidate_family": cand["candidate_family"],
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


def blocked_slice_row(cand: dict[str, Any], slice_name: str, scope: str) -> dict[str, object]:
    row = empty_slice_row(cand, slice_name, scope)
    row["guardrail_interpretation"] = "blocked_or_invalid"
    return row


def build_stability_rows(rows: list[dict[str, object]], registry: list[dict[str, Any]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    seasons = sorted({row["season"] for row in rows})
    pyf_rank = "GAUNTLET_001_PYF_POINTS_ANCHOR_rank"
    for cand in registry:
        if cand["candidate_status"] != "ACTIVE_REVIEW_ONLY":
            continue
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        for season in seasons:
            group = [row for row in scoped if row["season"] == season]
            if not group:
                continue
            cm = metrics_for_rows(group, rank_col)
            pm = metrics_for_rows(group, pyf_rank)
            delta = metric_delta(cm["spearman"], pm["spearman"])
            output.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "candidate_family": cand["candidate_family"],
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
    pyf_rank = "GAUNTLET_001_PYF_POINTS_ANCHOR_rank"
    score_by_id = {row["candidate_id"]: row for row in scorecard}
    for cand in registry:
        if cand["candidate_status"] != "ACTIVE_REVIEW_ONLY":
            continue
        scoped, scope = candidate_scope(cand, rows)
        rank_col = f"{cand['candidate_id']}_rank"
        base_delta = num(score_by_id[cand["candidate_id"]]["spearman_delta_vs_pyf"])
        loso: list[tuple[str, float | None]] = []
        for season in seasons:
            group = [row for row in scoped if row["season"] != season]
            cm = metrics_for_rows(group, rank_col)
            pm = metrics_for_rows(group, pyf_rank)
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
                "candidate_family": cand["candidate_family"],
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
    rows: list[dict[str, object]] = []
    for cand in registry:
        params = ";".join(f"{k}={v}" for k, v in cand["params"].items())
        rows.append(
            {
                "candidate_id": cand["candidate_id"],
                "candidate_family": cand["candidate_family"],
                "candidate_label": cand["candidate_label"],
                "formula_definition": cand["formula_definition"],
                "score_kind": cand["score_kind"],
                "params": params,
                "position_scope": cand["position_scope"],
                "candidate_status": cand["candidate_status"],
                "blocked_reason": cand["blocked_reason"],
                "score_changes_allowed": cand["score_changes_allowed"],
                "review_only_use": cand["review_only_use"],
                "required_comparator": cand["required_comparator"],
                "allowed_inputs": allowed_inputs_for(cand),
                "caveat": cand["caveat"],
            }
        )
    return rows


def allowed_inputs_for(cand: dict[str, Any]) -> str:
    family = cand["candidate_family"]
    base = "pyf_prior_nwr_points;prior_2yr_weighted_nwr_points;prior_3yr_weighted_nwr_points"
    if family.startswith("A_"):
        return "pyf_prior_nwr_points;pyf_prior_nwr_ppg;pyf_prior_rank_position_feature_season"
    if family.startswith(("B_", "C_", "D_", "E_", "F_", "G_", "L_", "M_")):
        return base
    if family.startswith(("H_", "I_", "K_")):
        return base + ";age_lifecycle_bucket;age_bucket;role_archetype"
    if family.startswith("J_"):
        return base + ";role_archetype;role_usage_bucket"
    if family.startswith("N_"):
        return "pfr_rush_brk_tkl__raw;pfr_rush_brk_tkl__per_game"
    if family.startswith("O_"):
        return "red_zone_partial_2024_2025_review_only_receipts"
    return base


def ffloat(value: object) -> float:
    parsed = num(value)
    return parsed if parsed is not None else -999.0


def coverage_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "rows": len(rows),
        "seasons": f"{min(int(row['season']) for row in rows)}-{max(int(row['season']) for row in rows)}",
        "positions": dict(Counter(str(row["position"]) for row in rows)),
        "sparse_rows": sum(1 for row in rows if row["sparse_history_bool"]),
        "low_games_rows": sum(1 for row in rows if row["low_games_bool"]),
        "age_missing": sum(1 for row in rows if row["age_missing"]),
        "review_only_rows": sum(1 for row in rows if str(row["review_only"]).lower() == "true"),
        "model_use_allowed_true": sum(1 for row in rows if str(row["model_use_allowed"]).lower() == "true"),
        "production_approved_true": sum(1 for row in rows if str(row["production_approved"]).lower() == "true"),
    }


def write_reports(
    rows: list[dict[str, object]],
    registry: list[dict[str, Any]],
    scorecard: list[dict[str, object]],
    position_rows: list[dict[str, object]],
    slice_rows: list[dict[str, object]],
    stability_rows: list[dict[str, object]],
    outlier_rows: list[dict[str, object]],
) -> None:
    coverage = coverage_summary(rows)
    active_scorecard = [row for row in scorecard if row["candidate_status"] == "ACTIVE_REVIEW_ONLY"]
    blocked_scorecard = [row for row in scorecard if row["candidate_status"] != "ACTIVE_REVIEW_ONLY"]
    pyf = next(row for row in scorecard if row["candidate_id"] == "GAUNTLET_001_PYF_POINTS_ANCHOR")
    non_pyf_active = [row for row in active_scorecard if row["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"]
    beaters = [row for row in non_pyf_active if row["beats_pyf_overall"] == "true" and row["score_changes_allowed"] == "yes"]
    position_beaters = [row for row in position_rows if row["beat_pyf_by_position"] == "true"]
    best_overall = max(non_pyf_active, key=lambda row: ffloat(row["candidate_spearman"]))
    best_by_position: dict[str, dict[str, object]] = {}
    for position in POSITIONS:
        choices = [row for row in position_rows if row["position"] == position and row["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"]
        best_by_position[position] = max(choices, key=lambda row: ffloat(row["candidate_spearman"]))
    pyf_slice = lambda name: [
        row
        for row in slice_rows
        if row["candidate_id"] == "GAUNTLET_001_PYF_POINTS_ANCHOR" and row["slice_name"] == name
    ][0]
    sparse = pyf_slice("sparse_history")
    low_games = pyf_slice("low_games")
    high_role = pyf_slice("high_volume_role")
    low_role = pyf_slice("low_or_sparse_role")
    older = pyf_slice("older_late_lifecycle")
    young = pyf_slice("young_early_lifecycle")
    stable = sorted(
        [row for row in outlier_rows if row["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"],
        key=lambda row: (int(row["leave_one_season_out_positive_count"]), -ffloat(row["max_abs_delta_shift"]), ffloat(row["overall_spearman_delta_vs_pyf"])),
        reverse=True,
    )
    stable_top = stable[0] if stable else None
    verdict = (
        "GREEN_REVIEW_ONLY_GAUNTLET_FOUND_STRONG_CANDIDATE_NEIGHBORHOODS"
        if len(beaters) >= 10 and stable_top and int(stable_top["leave_one_season_out_positive_count"]) >= 10
        else ("YELLOW_REVIEW_ONLY_GAUNTLET_MIXED_RESULTS" if beaters else "RED_REVIEW_ONLY_GAUNTLET_NO_CANDIDATE_BEATS_PYF")
    )
    candidate_families = len(set(cand["candidate_family"] for cand in registry))
    report = f"""
# Full Review-Only Formula Gauntlet Candidate Arena V1 Report

## Verdict

`{verdict}`

## Clear Answer

The full review-only Formula Gauntlet Candidate Arena registered exactly `120` fixed candidates before scoring. `{len(active_scorecard)}` candidates were scored with review-safe Formula Data Mart fields and `{len(blocked_scorecard)}` were blocked/invalid because PFR broken-tackle values or fair full-window red-zone values were not present in the mart. The best neighborhoods remained fixed multi-year production, especially three-year weighted variants. This is a review-only reference benchmark, not production accuracy or rankings integration.

## Benchmark Scope

- Rows tested: `{coverage['rows']}`
- Seasons: `{coverage['seasons']}`
- Positions: `{coverage['positions']}`
- Candidate registry rows: `{len(registry)}`
- Scored candidates: `{len(active_scorecard)}`
- Blocked/invalid candidates: `{len(blocked_scorecard)}`
- Candidate families represented: `{candidate_families}`
- Review-only rows: `{coverage['review_only_rows']}`
- Model-use allowed rows: `{coverage['model_use_allowed_true']}`
- Production-approved rows: `{coverage['production_approved_true']}`

## PYF Baseline

- PYF overall Spearman: `{pyf['candidate_spearman']}`
- PYF startable precision: `{pyf['startable_precision']}`

## Best Overall Review-Only Candidate

`{best_overall['candidate_id']}` from `{best_overall['candidate_family']}` produced Spearman `{best_overall['candidate_spearman']}` versus comparable PYF `{best_overall['pyf_spearman_comparable']}`.

## Best Candidate By Position

- QB: `{best_by_position['QB']['candidate_id']}` with Spearman `{best_by_position['QB']['candidate_spearman']}` versus PYF `{best_by_position['QB']['pyf_spearman']}`.
- RB: `{best_by_position['RB']['candidate_id']}` with Spearman `{best_by_position['RB']['candidate_spearman']}` versus PYF `{best_by_position['RB']['pyf_spearman']}`.
- WR: `{best_by_position['WR']['candidate_id']}` with Spearman `{best_by_position['WR']['candidate_spearman']}` versus PYF `{best_by_position['WR']['pyf_spearman']}`.
- TE: `{best_by_position['TE']['candidate_id']}` with Spearman `{best_by_position['TE']['candidate_spearman']}` versus PYF `{best_by_position['TE']['pyf_spearman']}`.

## PYF Comparison

- Score-changing candidates beating PYF overall: `{len(beaters)}`
- Candidate-position rows beating PYF: `{len(position_beaters)}`

## Guardrail Findings

- Sparse-history rows: `{sparse['rows']}` with startable rate `{sparse['startable_rate']}`.
- Low-games rows: `{low_games['rows']}` with startable rate `{low_games['startable_rate']}`.
- High-volume role rows contained `{high_role['pyf_false_positives']}` PYF false positives.
- Low/sparse role rows contained `{low_role['pyf_false_negatives']}` PYF false negatives.
- Older/late lifecycle rows contained `{older['pyf_false_positives']}` PYF false positives.
- Young/early lifecycle rows contained `{young['pyf_false_negatives']}` PYF false negatives.

## PFR / Red-Zone Findings

- PFR RB broken tackle candidates were registered but blocked because the Formula Data Mart has only status metadata, not actual `pfr_rush_brk_tkl__raw` or per-game values.
- Red-zone candidates were registered but blocked because available red-zone receipts are partial 2024-2025 lagged review-only context, not a fair 2013-2025 formula input.

## Stability

The stability review uses season-level and leave-one-season-out directional checks. Strong candidates were not driven by a single outlier season when the leave-one-season-out direction remained positive for most omitted seasons. See `GAUNTLET_STABILITY_BY_SEASON.csv` and `GAUNTLET_OUTLIER_INFLUENCE_REVIEW.csv`.

## Recommendation

Recommended next lane: `Champion Refinement Contract V1 around top 3-8 review-only candidates`.

This recommendation is for a contract/design lane only. Production/model-use, rankings integration, app/runtime changes, source promotion, exact replay claims, and final champion selection remain blocked.
"""
    write_text(OUT_DIR / "FULL_REVIEW_ONLY_FORMULA_GAUNTLET_CANDIDATE_ARENA_V1_REPORT.md", report)

    write_top_candidates(scorecard, position_rows, slice_rows, outlier_rows)
    write_position_leaderboards(position_rows)
    write_failed_candidates(scorecard)
    write_miss_pattern_review(slice_rows)
    write_blockers_and_caveats(blocked_scorecard)
    write_advancement_recommendation(best_overall, beaters, stable_top)
    write_source_trace()


def write_top_candidates(
    scorecard: list[dict[str, object]],
    position_rows: list[dict[str, object]],
    slice_rows: list[dict[str, object]],
    outlier_rows: list[dict[str, object]],
) -> None:
    active = [row for row in scorecard if row["candidate_status"] == "ACTIVE_REVIEW_ONLY" and row["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"]
    top = sorted(active, key=lambda row: ffloat(row["candidate_spearman"]), reverse=True)[:20]
    sparse_best = sorted(
        [row for row in slice_rows if row["slice_name"] == "sparse_history" and row["guardrail_interpretation"] in {"no_added_harm_vs_pyf", "improves_vs_pyf"}],
        key=lambda row: (row["guardrail_interpretation"] == "improves_vs_pyf", -abs(ffloat(row["harm_delta_vs_pyf"].replace("%", "")))),
        reverse=True,
    )[:10]
    stability_by_id = {row["candidate_id"]: row for row in outlier_rows}
    lines = [
        "# Gauntlet Top Review-Only Candidates",
        "",
        "No item below is a production winner, champion, ranking input, or model-use approval.",
        "",
        "## Best Overall Candidates",
    ]
    for row in top:
        stable = stability_by_id.get(row["candidate_id"], {})
        lines.append(
            f"- `{row['candidate_id']}`: `{row['candidate_family']}`, Spearman `{row['candidate_spearman']}` vs PYF `{row['pyf_spearman_comparable']}`, delta `{row['spearman_delta_vs_pyf']}`, LOSO positive `{stable.get('leave_one_season_out_positive_count', '')}/{stable.get('leave_one_season_out_total', '')}`."
        )
    lines.extend(["", "## Sparse / Low-Games Guardrail Standouts"])
    for row in sparse_best:
        lines.append(
            f"- `{row['candidate_id']}`: sparse rows `{row['rows']}`, harm delta `{row['harm_delta_vs_pyf']}`, interpretation `{row['guardrail_interpretation']}`."
        )
    write_text(OUT_DIR / "GAUNTLET_TOP_REVIEW_ONLY_CANDIDATES.md", "\n".join(lines))


def write_position_leaderboards(position_rows: list[dict[str, object]]) -> None:
    lines = ["# Gauntlet Position Leaderboards", ""]
    for position in POSITIONS:
        lines.extend([f"## {position}", ""])
        rows = [row for row in position_rows if row["position"] == position and row["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"]
        for row in sorted(rows, key=lambda r: ffloat(r["candidate_spearman"]), reverse=True)[:12]:
            lines.append(
                f"- `{row['candidate_id']}`: Spearman `{row['candidate_spearman']}` vs PYF `{row['pyf_spearman']}`, delta `{row['spearman_delta_vs_pyf']}`, startable precision `{row['startable_precision']}`."
            )
        lines.append("")
    write_text(OUT_DIR / "GAUNTLET_POSITION_LEADERBOARDS.md", "\n".join(lines))


def write_failed_candidates(scorecard: list[dict[str, object]]) -> None:
    failed = [row for row in scorecard if row["interpretation"] in {"FAILED_VS_PYF", "WEAK_REVIEW_ONLY", "BLOCKED_OR_INVALID"}]
    lines = [
        "# Gauntlet Failed Or Weak Candidates",
        "",
        "Failed, weak, or blocked candidates remain review artifacts only. No production behavior changed.",
        "",
    ]
    for row in failed:
        lines.append(
            f"- `{row['candidate_id']}` (`{row['candidate_family']}`): `{row['interpretation']}`; Spearman `{row['candidate_spearman']}` vs PYF `{row['pyf_spearman_comparable']}`; reason `{row['blocked_reason'] or row['comparison_result']}`."
        )
    write_text(OUT_DIR / "GAUNTLET_FAILED_OR_WEAK_CANDIDATES.md", "\n".join(lines))


def write_miss_pattern_review(slice_rows: list[dict[str, object]]) -> None:
    pyf_slice = lambda name: [
        row
        for row in slice_rows
        if row["candidate_id"] == "GAUNTLET_001_PYF_POINTS_ANCHOR" and row["slice_name"] == name
    ][0]
    sparse = pyf_slice("sparse_history")
    low_games = pyf_slice("low_games")
    high_role = pyf_slice("high_volume_role")
    low_role = pyf_slice("low_or_sparse_role")
    older = pyf_slice("older_late_lifecycle")
    young = pyf_slice("young_early_lifecycle")
    text = f"""
# Gauntlet Miss Pattern Review

## Sparse History And Low Games

Sparse-history rows covered `{sparse['rows']}` rows with a `{sparse['startable_rate']}` startable rate. Low-games rows covered `{low_games['rows']}` rows with a `{low_games['startable_rate']}` startable rate. These slices remain caution zones, not production penalties.

## Prior-Production Decline

High-volume role rows contained `{high_role['pyf_false_positives']}` PYF false positives. Older/late lifecycle rows contained `{older['pyf_false_positives']}` PYF false positives. These are useful decline-risk review slices.

## Breakout Windows

Young/early lifecycle rows contained `{young['pyf_false_negatives']}` PYF false negatives, and low/sparse role rows contained `{low_role['pyf_false_negatives']}` PYF false negatives. These slices warn against blunt low-volume or youth penalties.
"""
    write_text(OUT_DIR / "GAUNTLET_MISS_PATTERN_REVIEW.md", text)


def write_blockers_and_caveats(blocked: list[dict[str, object]]) -> None:
    lines = [
        "# Gauntlet Blockers And Caveats",
        "",
        "- This is review-only.",
        "- This is not production/model-use.",
        "- This is not rankings integration.",
        "- This is not app/runtime work.",
        "- No source was promoted.",
        "- No exact Model v4 replay field was used.",
        "- No current/future context was used as historical input.",
        "- Candidate definitions were fixed in code before scoring.",
        "- Additional weight variants use deterministic reconstruction from review-only weighted fields; they are not recovered raw yearly receipt chains.",
        "",
        "## Blocked Candidate Families",
    ]
    for row in blocked:
        lines.append(f"- `{row['candidate_id']}`: `{row['blocked_reason']}`.")
    write_text(OUT_DIR / "GAUNTLET_BLOCKERS_AND_CAVEATS.md", "\n".join(lines))


def write_advancement_recommendation(best: dict[str, object], beaters: list[dict[str, object]], stable_top: dict[str, object] | None) -> None:
    stable_text = "not_available"
    if stable_top:
        stable_text = f"`{stable_top['candidate_id']}` LOSO positive `{stable_top['leave_one_season_out_positive_count']}/{stable_top['leave_one_season_out_total']}`"
    text = f"""
# Gauntlet Advancement Recommendation

## Recommendation

Recommended next lane: `Champion Refinement Contract V1 around top 3-8 review-only candidates`.

## Basis

- Best overall review-only candidate: `{best['candidate_id']}`.
- Score-changing candidates beating PYF overall: `{len(beaters)}`.
- Stability signal: {stable_text}.

## Required Limits For The Next Lane

- Contract/design first.
- Fixed candidate neighborhood only.
- No production/model-use.
- No ranking integration.
- No app/runtime behavior changes.
- No source promotion.
- No final champion selection.
"""
    write_text(OUT_DIR / "GAUNTLET_ADVANCEMENT_RECOMMENDATION.md", text)


def write_source_trace() -> None:
    text = f"""
# Gauntlet Source Trace

## Local / Canonical Inputs

- Medium Review-Only Formula Pilot V1: `{MEDIUM_DIR}`
- Medium Review-Only Formula Pilot Contract V1: `{MEDIUM_CONTRACT_DIR}`
- Small Review-Only Formula Pilot V1: `{SMALL_DIR}`
- Formula Data Mart / Feature Availability Audit V1: `{DATA_MART_DIR}`
- Formula Data Mart Review-Only CSV: `{DATA_MART}`
- Remaining Data Upgrades Sweep V1: `{UPGRADE_SWEEP_DIR}`
- Age/Lifecycle Sidecar: `{AGE_SIDECAR}`
- Age/Lifecycle Master Review V1: `{AGE_MASTER_DIR}`
- Role Archetype Master Review V1: `{ROLE_MASTER_DIR}`
- Confidence Cap Component Signal Test V1: `{CONFIDENCE_DIR}`
- PFR RB Broken Tackle Addendum V1: `{PFR_ADDENDUM_DIR}`
- Red Zone Exact Receipt Regeneration Pilot V1: `{RED_ZONE_DIR}`

## Use Gate

All scored candidate inputs came from the review-only Formula Data Mart and age/lifecycle sidecar. PFR RB broken-tackle and red-zone candidate families were registered but blocked because the data available in the mart was insufficient for fair full-window scoring.

## Safety

No source was promoted. No production/model-use was approved. No ranking, app, runtime, model, or formula behavior was changed.
"""
    write_text(OUT_DIR / "GAUNTLET_SOURCE_TRACE.md", text)


def validate_outputs() -> None:
    required = [
        "FULL_REVIEW_ONLY_FORMULA_GAUNTLET_CANDIDATE_ARENA_V1_REPORT.md",
        "GAUNTLET_CANDIDATE_REGISTRY.csv",
        "GAUNTLET_CANDIDATE_METRICS_SCORECARD.csv",
        "GAUNTLET_PYF_COMPARISON.csv",
        "GAUNTLET_POSITION_RESULTS.csv",
        "GAUNTLET_SLICE_GUARDRAILS.csv",
        "GAUNTLET_STABILITY_BY_SEASON.csv",
        "GAUNTLET_OUTLIER_INFLUENCE_REVIEW.csv",
        "GAUNTLET_TOP_REVIEW_ONLY_CANDIDATES.md",
        "GAUNTLET_POSITION_LEADERBOARDS.md",
        "GAUNTLET_FAILED_OR_WEAK_CANDIDATES.md",
        "GAUNTLET_MISS_PATTERN_REVIEW.md",
        "GAUNTLET_BLOCKERS_AND_CAVEATS.md",
        "GAUNTLET_ADVANCEMENT_RECOMMENDATION.md",
        "GAUNTLET_SOURCE_TRACE.md",
        "run_full_review_only_formula_gauntlet_candidate_arena_v1.py",
    ]
    missing = [name for name in required if not (OUT_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"Missing required outputs: {missing}")
    for csv_name in [
        "GAUNTLET_CANDIDATE_REGISTRY.csv",
        "GAUNTLET_CANDIDATE_METRICS_SCORECARD.csv",
        "GAUNTLET_PYF_COMPARISON.csv",
        "GAUNTLET_POSITION_RESULTS.csv",
        "GAUNTLET_SLICE_GUARDRAILS.csv",
        "GAUNTLET_STABILITY_BY_SEASON.csv",
        "GAUNTLET_OUTLIER_INFLUENCE_REVIEW.csv",
    ]:
        rows = read_csv(OUT_DIR / csv_name)
        if not rows:
            raise RuntimeError(f"{csv_name} parsed but has no rows.")
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)


def main() -> None:
    registry = build_registry()
    rows = load_panel()
    write_csv(
        OUT_DIR / "GAUNTLET_CANDIDATE_REGISTRY.csv",
        registry_rows(registry),
        [
            "candidate_id",
            "candidate_family",
            "candidate_label",
            "formula_definition",
            "score_kind",
            "params",
            "position_scope",
            "candidate_status",
            "blocked_reason",
            "score_changes_allowed",
            "review_only_use",
            "required_comparator",
            "allowed_inputs",
            "caveat",
        ],
    )
    add_scores_and_ranks(rows, registry)
    scorecard, pyf_compare, position_rows = build_metric_rows(rows, registry)
    slice_rows = build_slice_rows(rows, registry)
    stability_rows = build_stability_rows(rows, registry)
    outlier_rows = build_outlier_rows(rows, registry, scorecard)
    write_csv(
        OUT_DIR / "GAUNTLET_CANDIDATE_METRICS_SCORECARD.csv",
        scorecard,
        [
            "candidate_id",
            "candidate_family",
            "candidate_label",
            "candidate_status",
            "score_changes_allowed",
            "scope",
            "rows_tested",
            "candidate_spearman",
            "pyf_spearman_comparable",
            "spearman_delta_vs_pyf",
            "mae_rank_vs_finish",
            "rmse_rank_vs_finish",
            "startable_precision",
            "pyf_startable_precision_comparable",
            "startable_precision_delta_vs_pyf",
            "candidate_false_positives",
            "pyf_false_positives_comparable",
            "false_positive_delta_vs_pyf",
            "candidate_false_negatives",
            "pyf_false_negatives_comparable",
            "false_negative_delta_vs_pyf",
            "sparse_history_error_delta_vs_pyf",
            "low_games_error_delta_vs_pyf",
            "beats_pyf_overall",
            "contextualizes_pyf",
            "interpretation",
            "comparison_result",
            "blocked_reason",
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_PYF_COMPARISON.csv",
        pyf_compare,
        [
            "candidate_id",
            "candidate_family",
            "scope",
            "candidate_spearman",
            "pyf_spearman",
            "spearman_delta",
            "candidate_startable_precision",
            "pyf_startable_precision",
            "startable_precision_delta",
            "candidate_false_positives",
            "pyf_false_positives",
            "false_positive_delta",
            "candidate_false_negatives",
            "pyf_false_negatives",
            "false_negative_delta",
            "beat_pyf",
            "comparison_result",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_POSITION_RESULTS.csv",
        position_rows,
        [
            "candidate_id",
            "candidate_family",
            "position",
            "rows_tested",
            "candidate_spearman",
            "pyf_spearman",
            "spearman_delta_vs_pyf",
            "startable_precision",
            "pyf_startable_precision",
            "top_12_precision",
            "pyf_top_12_precision",
            "top_24_precision",
            "pyf_top_24_precision",
            "top_36_precision",
            "pyf_top_36_precision",
            "candidate_false_positives",
            "pyf_false_positives",
            "candidate_false_negatives",
            "pyf_false_negatives",
            "beat_pyf_by_position",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_SLICE_GUARDRAILS.csv",
        slice_rows,
        [
            "candidate_id",
            "candidate_family",
            "slice_name",
            "scope",
            "rows",
            "startable_hits",
            "startable_rate",
            "candidate_false_positives",
            "pyf_false_positives",
            "false_positive_delta_vs_pyf",
            "candidate_false_negatives",
            "pyf_false_negatives",
            "false_negative_delta_vs_pyf",
            "candidate_error_rate",
            "pyf_error_rate",
            "harm_delta_vs_pyf",
            "guardrail_interpretation",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_STABILITY_BY_SEASON.csv",
        stability_rows,
        [
            "candidate_id",
            "candidate_family",
            "scope",
            "season",
            "rows",
            "candidate_spearman",
            "pyf_spearman",
            "spearman_delta_vs_pyf",
            "beat_pyf_in_season",
            "candidate_false_positives",
            "pyf_false_positives",
            "candidate_false_negatives",
            "pyf_false_negatives",
            "stability_caveat",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_OUTLIER_INFLUENCE_REVIEW.csv",
        outlier_rows,
        [
            "candidate_id",
            "candidate_family",
            "scope",
            "overall_spearman_delta_vs_pyf",
            "leave_one_season_out_positive_count",
            "leave_one_season_out_total",
            "min_loso_delta",
            "min_loso_omitted_season",
            "max_loso_delta",
            "max_loso_omitted_season",
            "max_abs_delta_shift",
            "outlier_influence_flag",
        ],
    )
    write_reports(rows, registry, scorecard, position_rows, slice_rows, stability_rows, outlier_rows)
    validate_outputs()
    print(
        "full_review_only_gauntlet_complete "
        f"rows={len(rows)} candidates={len(registry)} out={OUT_DIR}"
    )


if __name__ == "__main__":
    main()
