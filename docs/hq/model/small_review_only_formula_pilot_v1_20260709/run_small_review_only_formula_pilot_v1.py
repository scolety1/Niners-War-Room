from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
CONTRACT_COMMIT = "9758b7272aa6be6beb8cd0ee3d89bbe80b049277"

CONTRACT_DIR = REPO / "docs/hq/model/small_review_only_formula_pilot_contract_v1_20260709"
CONTRACT_CANDIDATES = CONTRACT_DIR / "SMALL_FORMULA_PILOT_ALLOWED_CANDIDATES.csv"
DATA_MART_DIR = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
)
DATA_MART = DATA_MART_DIR / "FORMULA_DATA_MART_REVIEW_ONLY.csv"
AGE_DIR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709"
    r"\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709"
)
AGE_SIDECAR = AGE_DIR / "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"

POSITIONS = ["QB", "RB", "WR", "TE"]
POSITION_TOPNS = {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}
# Reuse the accepted NWR review format from the role-archetype signal test.
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}


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
    if text == "":
        return None
    try:
        value_float = float(text)
    except ValueError:
        return None
    return value_float if math.isfinite(value_float) else None


def bool_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def fmt(value: float | None, places: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{places}f}"


def pct(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value * 100:.1f}%"


def mean(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def std(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    m = sum(clean) / len(clean)
    return math.sqrt(sum((v - m) ** 2 for v in clean) / len(clean))


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
    if len(xs) < 2:
        return None
    return pearson(rank_values(xs), rank_values(ys))


def pct_delta(candidate: float | None, baseline: float | None) -> str:
    if candidate is None or baseline is None:
        return ""
    return fmt(candidate - baseline)


def group_rows(rows: list[dict[str, object]], keys: tuple[str, ...]) -> dict[tuple[object, ...], list[dict[str, object]]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def assign_rank(rows: list[dict[str, object]], score_col: str, rank_col: str) -> None:
    grouped = group_rows(rows, ("season", "position"))
    for group in grouped.values():
        ordered = sorted(
            group,
            key=lambda row: (
                row[score_col] if row[score_col] is not None else -999999999.0,
                str(row["player_id"]),
                str(row["substrate_row_id"]),
            ),
            reverse=True,
        )
        for idx, row in enumerate(ordered, start=1):
            row[rank_col] = float(idx)


def predicted_startable(row: dict[str, object], rank_col: str) -> bool:
    rank = row.get(rank_col)
    if rank is None:
        return False
    return float(rank) <= STARTABLE_CUTOFF[str(row["position"])]


def load_panel() -> list[dict[str, object]]:
    mart = read_csv(DATA_MART)
    ages = read_csv(AGE_SIDECAR)
    age_key = {(r["player_id"], r["season"], r["position"]): r for r in ages}
    if len(age_key) != len(ages):
        raise RuntimeError("Age/lifecycle sidecar has duplicate keys.")
    output: list[dict[str, object]] = []
    missing_age_rows = 0
    for row in mart:
        key = (row["player_id"], row["season"], row["position"])
        age = age_key.get(key)
        if age is None:
            raise RuntimeError(f"Missing age/lifecycle row for {key}")
        out: dict[str, object] = dict(row)
        out["age"] = num(age.get("age"))
        out["age_bucket"] = age.get("age_bucket", "")
        out["lifecycle_bucket"] = age.get("lifecycle_bucket", "")
        out["career_stage"] = age.get("career_stage", "")
        out["age_missing"] = out["age"] is None
        out["age_decision_date_safe"] = age.get("decision_date_safe", "")
        out["age_leakage_flag"] = age.get("leakage_flag", "")
        out["age_identity_flag"] = age.get("identity_flag", "")
        out["age_review_only_status"] = age.get("review_only_status", "")
        out["season"] = str(row["season"])
        out["position"] = str(row["position"])
        out["player_id"] = str(row["player_id"])
        out["substrate_row_id"] = str(row["substrate_row_id"])
        out["actual_finish"] = num(row["label_next_position_finish"])
        out["actual_points"] = num(row["label_next_nwr_points"])
        out["actual_startable"] = bool_true(row["label_startable_hit"])
        out["pyf_score"] = num(row["pyf_prior_nwr_points"])
        out["two_year_score"] = num(row["prior_2yr_weighted_nwr_points"])
        out["three_year_score"] = num(row["prior_3yr_weighted_nwr_points"])
        out["prior_games_num"] = num(row["prior_games"]) or 0.0
        out["sparse_history_bool"] = str(row["sparse_history_flag"]).strip().lower() == "true"
        out["low_games_bool"] = str(row["low_games_flag"]).strip().lower() == "true"
        out["role_archetype"] = str(row["role_archetype"])
        out["role_usage_bucket"] = str(row["role_usage_bucket"])
        out["confidence_status"] = str(row["confidence_status"])
        out["confidence_cap_value_num"] = num(row["confidence_cap_value"])
        if out["age_missing"]:
            missing_age_rows += 1
        output.append(out)
    if missing_age_rows > 8:
        raise RuntimeError(f"Unexpected age missingness: {missing_age_rows}")
    return output


def load_candidates() -> list[dict[str, str]]:
    candidates = read_csv(CONTRACT_CANDIDATES)
    if len(candidates) != 15:
        raise RuntimeError(f"Contract candidate count is {len(candidates)}, expected 15.")
    return candidates


def candidate_scope(candidate_id: str, rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], str, str, bool]:
    position_by_id = {
        "PILOT_004_POSITION_SPECIFIC_PYF_QB": "QB",
        "PILOT_005_POSITION_SPECIFIC_PYF_RB": "RB",
        "PILOT_006_POSITION_SPECIFIC_PYF_WR": "WR",
        "PILOT_007_POSITION_SPECIFIC_PYF_TE": "TE",
    }
    if candidate_id in position_by_id:
        pos = position_by_id[candidate_id]
        return [row for row in rows if row["position"] == pos], pos, "position_diagnostic", False
    if candidate_id == "PILOT_002_TWO_YEAR_WEIGHTED_PRODUCTION_70_30":
        return rows, "QB/RB/WR/TE", "two_year_score", True
    if candidate_id == "PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10":
        return rows, "QB/RB/WR/TE", "three_year_score", True
    return rows, "QB/RB/WR/TE", "pyf_score", candidate_id == "PILOT_001_PYF_BASELINE"


def top_precision(rows: list[dict[str, object]], rank_col: str, top_n: int) -> float | None:
    selected = [row for row in rows if row.get(rank_col) is not None and float(row[rank_col]) <= top_n]
    if not selected:
        return None
    return sum(1 for row in selected if row["actual_finish"] is not None and row["actual_finish"] <= top_n) / len(selected)


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
    sparse_errors = [
        row
        for row in sparse
        if predicted_startable(row, rank_col) != bool(row["actual_startable"])
    ]
    low_games_errors = [
        row
        for row in low_games
        if predicted_startable(row, rank_col) != bool(row["actual_startable"])
    ]
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


def add_scores_and_ranks(rows: list[dict[str, object]]) -> None:
    for row in rows:
        row["PILOT_001_PYF_BASELINE_score"] = row["pyf_score"]
        row["PILOT_002_TWO_YEAR_WEIGHTED_PRODUCTION_70_30_score"] = row["two_year_score"]
        row["PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10_score"] = row["three_year_score"]
        for candidate_id in [
            "PILOT_004_POSITION_SPECIFIC_PYF_QB",
            "PILOT_005_POSITION_SPECIFIC_PYF_RB",
            "PILOT_006_POSITION_SPECIFIC_PYF_WR",
            "PILOT_007_POSITION_SPECIFIC_PYF_TE",
            "PILOT_008_SPARSE_HISTORY_GUARDED_PYF",
            "PILOT_009_LOW_GAMES_GUARDED_PYF",
            "PILOT_010_PRIOR_DECLINE_GUARDED_PYF",
            "PILOT_011_AGE_LIFECYCLE_GUARDED_PYF",
            "PILOT_012_ROLE_ARCHETYPE_SLICE_AWARE_PYF",
            "PILOT_013_AGE_ROLE_CONTEXT_DIAGNOSTIC",
            "PILOT_014_CONFIDENCE_COVERAGE_CAUTION_DIAGNOSTIC",
            "PILOT_015_PYF_PLUS_SIMPLE_GUARDRAIL_STACK_REVIEW_ONLY",
        ]:
            row[f"{candidate_id}_score"] = row["pyf_score"]
    candidate_ids = [
        "PILOT_001_PYF_BASELINE",
        "PILOT_002_TWO_YEAR_WEIGHTED_PRODUCTION_70_30",
        "PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10",
        "PILOT_004_POSITION_SPECIFIC_PYF_QB",
        "PILOT_005_POSITION_SPECIFIC_PYF_RB",
        "PILOT_006_POSITION_SPECIFIC_PYF_WR",
        "PILOT_007_POSITION_SPECIFIC_PYF_TE",
        "PILOT_008_SPARSE_HISTORY_GUARDED_PYF",
        "PILOT_009_LOW_GAMES_GUARDED_PYF",
        "PILOT_010_PRIOR_DECLINE_GUARDED_PYF",
        "PILOT_011_AGE_LIFECYCLE_GUARDED_PYF",
        "PILOT_012_ROLE_ARCHETYPE_SLICE_AWARE_PYF",
        "PILOT_013_AGE_ROLE_CONTEXT_DIAGNOSTIC",
        "PILOT_014_CONFIDENCE_COVERAGE_CAUTION_DIAGNOSTIC",
        "PILOT_015_PYF_PLUS_SIMPLE_GUARDRAIL_STACK_REVIEW_ONLY",
    ]
    for candidate_id in candidate_ids:
        assign_rank(rows, f"{candidate_id}_score", f"{candidate_id}_rank")


def candidate_results(rows: list[dict[str, object]], candidates: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    pyf_all = metrics_for_rows(rows, "PILOT_001_PYF_BASELINE_rank")
    results: list[dict[str, object]] = []
    pyf_comparison_rows: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []

    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        scoped_rows, scope_positions, score_mode, changes_rank = candidate_scope(candidate_id, rows)
        rank_col = f"{candidate_id}_rank"
        candidate_metrics = metrics_for_rows(scoped_rows, rank_col)
        comparable_pyf = metrics_for_rows(scoped_rows, "PILOT_001_PYF_BASELINE_rank")
        spearman_delta = (
            candidate_metrics["spearman"] - comparable_pyf["spearman"]
            if candidate_metrics["spearman"] is not None and comparable_pyf["spearman"] is not None
            else None
        )
        precision_delta = (
            candidate_metrics["startable_precision"] - comparable_pyf["startable_precision"]
            if candidate_metrics["startable_precision"] is not None and comparable_pyf["startable_precision"] is not None
            else None
        )
        fp_delta = candidate_metrics["false_positives"] - comparable_pyf["false_positives"]
        fn_delta = candidate_metrics["false_negatives"] - comparable_pyf["false_negatives"]
        sparse_delta = (
            candidate_metrics["sparse_error_rate"] - comparable_pyf["sparse_error_rate"]
            if candidate_metrics["sparse_error_rate"] is not None and comparable_pyf["sparse_error_rate"] is not None
            else None
        )
        low_delta = (
            candidate_metrics["low_games_error_rate"] - comparable_pyf["low_games_error_rate"]
            if candidate_metrics["low_games_error_rate"] is not None and comparable_pyf["low_games_error_rate"] is not None
            else None
        )
        beats_pyf = bool(spearman_delta is not None and spearman_delta > 0.0005)
        contextual = (not changes_rank) and candidate_id != "PILOT_001_PYF_BASELINE"
        if beats_pyf:
            interpretation = "PROMISING_REVIEW_ONLY"
        elif contextual:
            interpretation = "MIXED_REVIEW_ONLY"
        elif candidate_id == "PILOT_001_PYF_BASELINE":
            interpretation = "ANCHOR_BASELINE"
        elif spearman_delta is not None and spearman_delta < -0.0005:
            interpretation = "FAILED_VS_PYF"
        else:
            interpretation = "WEAK_REVIEW_ONLY"
        caveat = (
            "pyf_equivalent_diagnostic_context_no_rank_change"
            if contextual
            else "predeclared_fixed_score_no_weight_tuning"
        )
        if candidate_id == "PILOT_001_PYF_BASELINE":
            caveat = "mandatory_anchor_not_new_formula"
        results.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": candidate["candidate_family"],
                "positions": scope_positions,
                "rows_tested": candidate_metrics["rows"],
                "score_mode": score_mode,
                "changes_rank_vs_pyf": str(changes_rank).lower(),
                "spearman_overall": fmt(candidate_metrics["spearman"]),
                "pyf_spearman_comparable": fmt(comparable_pyf["spearman"]),
                "spearman_delta_vs_pyf": fmt(spearman_delta),
                "mae_rank_vs_finish": fmt(candidate_metrics["mae"]),
                "rmse_rank_vs_finish": fmt(candidate_metrics["rmse"]),
                "startable_precision": pct(candidate_metrics["startable_precision"]),
                "pyf_startable_precision_comparable": pct(comparable_pyf["startable_precision"]),
                "startable_precision_delta_vs_pyf": pct(precision_delta),
                "candidate_false_positives": candidate_metrics["false_positives"],
                "pyf_false_positives_comparable": comparable_pyf["false_positives"],
                "false_positive_delta_vs_pyf": fp_delta,
                "candidate_false_negatives": candidate_metrics["false_negatives"],
                "pyf_false_negatives_comparable": comparable_pyf["false_negatives"],
                "false_negative_delta_vs_pyf": fn_delta,
                "sparse_history_error_delta_vs_pyf": pct(sparse_delta),
                "low_games_error_delta_vs_pyf": pct(low_delta),
                "beats_pyf_overall": str(beats_pyf).lower(),
                "contextualizes_pyf": str(contextual).lower(),
                "interpretation": interpretation,
                "caveat": caveat,
            }
        )
        pyf_comparison_rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": candidate["candidate_family"],
                "scope": scope_positions,
                "candidate_spearman": fmt(candidate_metrics["spearman"]),
                "pyf_spearman": fmt(comparable_pyf["spearman"]),
                "spearman_delta": fmt(spearman_delta),
                "candidate_startable_precision": pct(candidate_metrics["startable_precision"]),
                "pyf_startable_precision": pct(comparable_pyf["startable_precision"]),
                "startable_precision_delta": pct(precision_delta),
                "candidate_false_positives": candidate_metrics["false_positives"],
                "pyf_false_positives": comparable_pyf["false_positives"],
                "candidate_false_negatives": candidate_metrics["false_negatives"],
                "pyf_false_negatives": comparable_pyf["false_negatives"],
                "beat_pyf": str(beats_pyf).lower(),
                "comparison_result": "beats_pyf" if beats_pyf else ("contextualizes_pyf" if contextual else "does_not_beat_pyf"),
            }
        )

        for position in POSITIONS:
            pos_group = [row for row in scoped_rows if row["position"] == position]
            if not pos_group:
                continue
            pos_candidate = metrics_for_rows(pos_group, rank_col)
            pos_pyf = metrics_for_rows(pos_group, "PILOT_001_PYF_BASELINE_rank")
            pos_spearman_delta = (
                pos_candidate["spearman"] - pos_pyf["spearman"]
                if pos_candidate["spearman"] is not None and pos_pyf["spearman"] is not None
                else None
            )
            top_values: dict[str, object] = {}
            for top_n in [12, 24, 36]:
                if top_n in POSITION_TOPNS[position]:
                    top_values[f"top_{top_n}_precision"] = pct(top_precision(pos_group, rank_col, top_n))
                    top_values[f"pyf_top_{top_n}_precision"] = pct(top_precision(pos_group, "PILOT_001_PYF_BASELINE_rank", top_n))
                else:
                    top_values[f"top_{top_n}_precision"] = ""
                    top_values[f"pyf_top_{top_n}_precision"] = ""
            position_rows.append(
                {
                    "candidate_id": candidate_id,
                    "position": position,
                    "rows_tested": pos_candidate["rows"],
                    "candidate_spearman": fmt(pos_candidate["spearman"]),
                    "pyf_spearman": fmt(pos_pyf["spearman"]),
                    "spearman_delta": fmt(pos_spearman_delta),
                    "startable_precision": pct(pos_candidate["startable_precision"]),
                    "pyf_startable_precision": pct(pos_pyf["startable_precision"]),
                    "top_12_precision": top_values["top_12_precision"],
                    "pyf_top_12_precision": top_values["pyf_top_12_precision"],
                    "top_24_precision": top_values["top_24_precision"],
                    "pyf_top_24_precision": top_values["pyf_top_24_precision"],
                    "top_36_precision": top_values["top_36_precision"],
                    "pyf_top_36_precision": top_values["pyf_top_36_precision"],
                    "candidate_false_positives": pos_candidate["false_positives"],
                    "candidate_false_negatives": pos_candidate["false_negatives"],
                    "beat_pyf_by_position": str(bool(pos_spearman_delta is not None and pos_spearman_delta > 0.0005)).lower(),
                }
            )
    return results, pyf_comparison_rows, position_rows


def slice_guardrails(rows: list[dict[str, object]], candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    slice_defs = {
        "sparse_history": lambda r: bool(r["sparse_history_bool"]),
        "low_games": lambda r: bool(r["low_games_bool"]),
        "older_late_lifecycle": lambda r: str(r.get("age_bucket")) == "age_32_plus" or "late" in str(r.get("lifecycle_bucket")),
        "young_early_lifecycle": lambda r: str(r.get("age_bucket")) in {"age_under_23", "age_23_24"} or "early" in str(r.get("lifecycle_bucket")),
        "high_volume_role": lambda r: "_high_volume_" in str(r.get("role_archetype")),
        "low_or_sparse_role": lambda r: "_low_volume_" in str(r.get("role_archetype")) or bool(r["sparse_history_bool"]),
        "confidence_low_or_partial": lambda r: "full_component_coverage" not in str(r.get("confidence_status")),
    }
    output: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        scoped_rows, scope_positions, _, _ = candidate_scope(candidate_id, rows)
        rank_col = f"{candidate_id}_rank"
        pyf_rank_col = "PILOT_001_PYF_BASELINE_rank"
        for slice_name, predicate in slice_defs.items():
            group = [row for row in scoped_rows if predicate(row)]
            if not group:
                output.append(
                    {
                        "candidate_id": candidate_id,
                        "slice_name": slice_name,
                        "scope": scope_positions,
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
            cand_fp = [row for row in group if predicted_startable(row, rank_col) and not row["actual_startable"]]
            cand_fn = [row for row in group if not predicted_startable(row, rank_col) and row["actual_startable"]]
            pyf_fp = [row for row in group if predicted_startable(row, pyf_rank_col) and not row["actual_startable"]]
            pyf_fn = [row for row in group if not predicted_startable(row, pyf_rank_col) and row["actual_startable"]]
            cand_error = (len(cand_fp) + len(cand_fn)) / len(group)
            pyf_error = (len(pyf_fp) + len(pyf_fn)) / len(group)
            delta = cand_error - pyf_error
            output.append(
                {
                    "candidate_id": candidate_id,
                    "slice_name": slice_name,
                    "scope": scope_positions,
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


def coverage_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    age_missing = sum(1 for row in rows if row["age_missing"])
    age_leakage_caveat = sum(
        1
        for row in rows
        if not str(row["age_leakage_flag"]).startswith("PASS")
        and str(row["age_leakage_flag"]) == "NOT_USABLE_FOR_AGE_SIGNAL_WHEN_BIRTHDATE_MISSING"
    )
    age_identity_caveat = sum(
        1
        for row in rows
        if not str(row["age_identity_flag"]).startswith("PASS")
        and str(row["age_identity_flag"]) in {"JOIN_MISSING_DP_GSIS", "IDENTITY_REVIEW_REQUIRED_DUPLICATE_GSIS_DOB_CONFLICT"}
    )
    age_leakage_blocked = sum(
        1
        for row in rows
        if not str(row["age_leakage_flag"]).startswith("PASS")
        and str(row["age_leakage_flag"]) != "NOT_USABLE_FOR_AGE_SIGNAL_WHEN_BIRTHDATE_MISSING"
    )
    age_identity_blocked = sum(
        1
        for row in rows
        if not str(row["age_identity_flag"]).startswith("PASS")
        and str(row["age_identity_flag"]) not in {"JOIN_MISSING_DP_GSIS", "IDENTITY_REVIEW_REQUIRED_DUPLICATE_GSIS_DOB_CONFLICT"}
    )
    return {
        "rows": len(rows),
        "seasons": f"{min(int(row['season']) for row in rows)}-{max(int(row['season']) for row in rows)}",
        "positions": dict(Counter(str(row["position"]) for row in rows)),
        "age_missing": age_missing,
        "age_missing_rate": age_missing / len(rows),
        "review_only_rows": sum(1 for row in rows if str(row["review_only"]).lower() == "true"),
        "model_use_allowed_true": sum(1 for row in rows if str(row["model_use_allowed"]).lower() == "true"),
        "production_approved_true": sum(1 for row in rows if str(row["production_approved"]).lower() == "true"),
        "leakage_fail_rows": sum(1 for row in rows if not str(row["leakage_check_result"]).startswith("PASS")),
        "asof_fail_rows": sum(1 for row in rows if not str(row["asof_check_result"]).startswith("PASS")),
        "age_leakage_caveat_rows": age_leakage_caveat,
        "age_identity_caveat_rows": age_identity_caveat,
        "age_leakage_blocked_rows": age_leakage_blocked,
        "age_identity_blocked_rows": age_identity_blocked,
    }


def write_reports(rows: list[dict[str, object]], candidates: list[dict[str, str]], candidate_rows: list[dict[str, object]], pyf_rows: list[dict[str, object]], position_rows: list[dict[str, object]], slice_rows: list[dict[str, object]]) -> None:
    coverage = coverage_summary(rows)
    best_overall = max(
        [row for row in candidate_rows if row["candidate_id"] != "PILOT_001_PYF_BASELINE"],
        key=lambda row: float(row["spearman_overall"] or "-999"),
    )
    beaters = [row for row in candidate_rows if row["beats_pyf_overall"] == "true"]
    position_beaters = [row for row in position_rows if row["beat_pyf_by_position"] == "true"]
    failed = [row for row in candidate_rows if row["interpretation"] == "FAILED_VS_PYF"]
    contextual = [row for row in candidate_rows if row["contextualizes_pyf"] == "true"]
    best_by_position = {}
    for position in POSITIONS:
        position_candidates = [
            row
            for row in position_rows
            if row["position"] == position and row["candidate_id"] != "PILOT_001_PYF_BASELINE"
        ]
        best_by_position[position] = max(
            position_candidates,
            key=lambda row: float(row["candidate_spearman"] or "-999"),
        )
    pyf_all = next(row for row in candidate_rows if row["candidate_id"] == "PILOT_001_PYF_BASELINE")
    role_high = [row for row in slice_rows if row["candidate_id"] == "PILOT_001_PYF_BASELINE" and row["slice_name"] == "high_volume_role"][0]
    role_low = [row for row in slice_rows if row["candidate_id"] == "PILOT_001_PYF_BASELINE" and row["slice_name"] == "low_or_sparse_role"][0]
    older = [row for row in slice_rows if row["candidate_id"] == "PILOT_001_PYF_BASELINE" and row["slice_name"] == "older_late_lifecycle"][0]
    young = [row for row in slice_rows if row["candidate_id"] == "PILOT_001_PYF_BASELINE" and row["slice_name"] == "young_early_lifecycle"][0]
    sparse = [row for row in slice_rows if row["candidate_id"] == "PILOT_001_PYF_BASELINE" and row["slice_name"] == "sparse_history"][0]
    low_games = [row for row in slice_rows if row["candidate_id"] == "PILOT_001_PYF_BASELINE" and row["slice_name"] == "low_games"][0]
    verdict = (
        "GREEN_SMALL_FORMULA_PILOT_FOUND_PROMISING_REVIEW_ONLY_CANDIDATES"
        if beaters
        else "YELLOW_SMALL_FORMULA_PILOT_MIXED_RESULTS"
    )
    if not beaters and len(failed) >= 2:
        verdict = "RED_SMALL_FORMULA_PILOT_NO_CANDIDATE_BEATS_PYF"

    report = f"""
# Small Review-Only Formula Pilot V1 Report

## Verdict

`{verdict}`

## Clear Answer

The small review-only formula pilot tested exactly `15` approved candidates on `5,518` player-season rows. The only candidates that changed rankings were the predeclared two-year and three-year weighted production variants; the role, age/lifecycle, sparse-history, low-games, and confidence-cap candidates were run as PYF-centered diagnostics by contract. `{len(beaters)}` candidate(s) beat PYF overall by Spearman, while the context candidates mainly preserved useful guardrail and miss-taxonomy direction rather than producing new formula superiority.

## Benchmark Scope

- Rows tested: `{coverage['rows']}`
- Seasons: `{coverage['seasons']}`
- Position coverage: `{coverage['positions']}`
- Candidates tested: `{len(candidates)}`
- Review-only rows: `{coverage['review_only_rows']}`
- Model-use allowed rows: `{coverage['model_use_allowed_true']}`
- Production-approved rows: `{coverage['production_approved_true']}`
- Age/lifecycle missing rows: `{coverage['age_missing']}` ({pct(coverage['age_missing_rate'])})

## Best Overall Candidate

Best non-PYF overall candidate by Spearman: `{best_overall['candidate_id']}` with Spearman `{best_overall['spearman_overall']}` versus comparable PYF `{best_overall['pyf_spearman_comparable']}`.

## Best Candidate By Position

- QB: `{best_by_position['QB']['candidate_id']}` with Spearman `{best_by_position['QB']['candidate_spearman']}` versus PYF `{best_by_position['QB']['pyf_spearman']}`.
- RB: `{best_by_position['RB']['candidate_id']}` with Spearman `{best_by_position['RB']['candidate_spearman']}` versus PYF `{best_by_position['RB']['pyf_spearman']}`.
- WR: `{best_by_position['WR']['candidate_id']}` with Spearman `{best_by_position['WR']['candidate_spearman']}` versus PYF `{best_by_position['WR']['pyf_spearman']}`.
- TE: `{best_by_position['TE']['candidate_id']}` with Spearman `{best_by_position['TE']['candidate_spearman']}` versus PYF `{best_by_position['TE']['pyf_spearman']}`.

## PYF Comparison

- PYF overall Spearman: `{pyf_all['spearman_overall']}`
- PYF startable precision: `{pyf_all['startable_precision']}`
- Candidate(s) beating PYF overall: `{len(beaters)}`
- Candidate-position results beating PYF: `{len(position_beaters)}`

## Guardrail Findings

- Sparse-history rows: `{sparse['rows']}` with startable rate `{sparse['startable_rate']}`.
- Low-games rows: `{low_games['rows']}` with startable rate `{low_games['startable_rate']}`.
- High-volume role rows contained `{role_high['pyf_false_positives']}` PYF false positives.
- Low/sparse role rows contained `{role_low['pyf_false_negatives']}` PYF false negatives.
- Older/late lifecycle rows contained `{older['pyf_false_positives']}` PYF false positives.
- Young/early lifecycle rows contained `{young['pyf_false_negatives']}` PYF false negatives.

## Interpretation

This pilot does not approve a formula winner. It supports a small next step only if Master HQ wants another review-only lane. Weighted production variants may be considered for cautious review-only refinement because they were predeclared and tested without tuning. Role archetype and age/lifecycle remain useful as slice reporting and guardrail context. Confidence cap remains caution/coverage context only.

## Recommended Next Lane

Recommended next lane: `Medium Review-Only Formula Pilot Contract V1`.

That lane should predeclare a modest expansion around fixed multi-year production variants, position-specific reporting, and guardrail slice reporting. It must not run 100 candidates, tune weights, select winners, change rankings, or approve production/model-use.

## Current Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Gauntlet remains blocked.
- Champion refinement remains blocked.
- No source was promoted.
- No ranking/app/runtime/model behavior changed.
"""
    write_text(OUT_DIR / "SMALL_REVIEW_ONLY_FORMULA_PILOT_V1_REPORT.md", report)

    miss_review = f"""
# Small Formula Pilot Miss Pattern Review

## Sparse History And Low Games

Sparse-history rows (`{sparse['rows']}`) and low-games rows (`{low_games['rows']}`) remain high-risk slices. Their startable rates were `{sparse['startable_rate']}` and `{low_games['startable_rate']}` respectively under the baseline slice review. The pilot did not allow automatic penalties, so these flags should remain review-only guardrails rather than ranking logic.

## Prior-Production Decline

High-volume role rows concentrated `{role_high['pyf_false_positives']}` PYF false positives. This supports role archetype as review-only miss taxonomy, not a formula weight or ranking adjustment.

## Age / Lifecycle

Older/late lifecycle rows contained `{older['pyf_false_positives']}` PYF false positives, while young/early lifecycle rows contained `{young['pyf_false_negatives']}` PYF false negatives. This supports age/lifecycle as review-only formula-family context and guardrail reporting.

## Confidence / Coverage

Confidence cap did not function as a ranking signal in prior evidence and was preserved here only as caution/coverage context.
"""
    write_text(OUT_DIR / "SMALL_FORMULA_PILOT_MISS_PATTERN_REVIEW.md", miss_review)

    top_lines = [
        "# Small Formula Pilot Top Review-Only Candidates",
        "",
        "No candidate is a production winner, champion, ranking input, or model-use approval.",
        "",
    ]
    if beaters:
        top_lines.append("## Candidates Beating PYF Overall")
        for row in beaters:
            top_lines.append(
                f"- `{row['candidate_id']}`: Spearman `{row['spearman_overall']}` versus PYF `{row['pyf_spearman_comparable']}`; startable precision `{row['startable_precision']}`."
            )
    else:
        top_lines.append("No candidate beat PYF overall.")
    top_lines.append("")
    top_lines.append("## Context Candidates")
    top_lines.append(
        "The PYF-equivalent context candidates are useful only for diagnostics, miss taxonomy, and guardrail reporting."
    )
    for row in contextual:
        top_lines.append(f"- `{row['candidate_id']}`: `{row['interpretation']}`; `{row['caveat']}`.")
    write_text(OUT_DIR / "SMALL_FORMULA_PILOT_TOP_REVIEW_ONLY_CANDIDATES.md", "\n".join(top_lines))

    failed_lines = [
        "# Small Formula Pilot Failed Candidates",
        "",
        "A failed candidate here means it did not beat the comparable PYF anchor by the predeclared Spearman check. It does not imply production harm because no ranking integration occurred.",
        "",
    ]
    if failed:
        for row in failed:
            failed_lines.append(
                f"- `{row['candidate_id']}`: Spearman delta `{row['spearman_delta_vs_pyf']}`, false-positive delta `{row['false_positive_delta_vs_pyf']}`, false-negative delta `{row['false_negative_delta_vs_pyf']}`."
            )
    else:
        failed_lines.append("No candidate was classified as `FAILED_VS_PYF`; non-beating diagnostics are classified as mixed/weak review-only context.")
    write_text(OUT_DIR / "SMALL_FORMULA_PILOT_FAILED_CANDIDATES.md", "\n".join(failed_lines))

    caveats = """
# Small Formula Pilot Blockers And Caveats

- This is not Formula Gauntlet.
- This is not a 100-candidate run.
- This is not champion refinement.
- This is not tuning or optimization.
- No production winner was selected.
- No ranking output changed.
- No app/runtime/model behavior changed.
- No source was promoted.
- Exact Model v4 replay remains blocked.
- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Context candidates that preserve PYF rankings should not be misread as independent formula improvements.
- Age/lifecycle can create false confidence if used as an automatic boost or penalty.
- Role archetype can create false confidence if used as a formula weight or direct ranking input.
- Confidence cap remains caution/coverage context only.
"""
    write_text(OUT_DIR / "SMALL_FORMULA_PILOT_BLOCKERS_AND_CAVEATS.md", caveats)

    source_trace = f"""
# Small Formula Pilot Source Trace

## Inputs

- Contract: `{CONTRACT_DIR}`
- Contract commit: `{CONTRACT_COMMIT}`
- Formula Data Mart: `{DATA_MART}`
- Age/Lifecycle Sidecar: `{AGE_SIDECAR}`
- Canonical remote expected at lane start: `{EXPECTED_REMOTE_HEAD}`

## Use-Gate Summary

- PYF / prior-year points: mandatory anchor baseline.
- Two-year and three-year production: review-only fixed-weight comparisons, no tuning.
- Role archetype: review-only guardrail/miss taxonomy context only.
- Age/lifecycle: review-only formula-family and guardrail context only.
- Confidence cap: caution/coverage context only.

## Guardrails

- No source promotion.
- No Formula Gauntlet.
- No 100-candidate run.
- No champion refinement.
- No ranking/app/runtime/model behavior change.
- No production/model-use.
- No exact Model v4 replay claim.

## Validation Notes

- Candidate count enforced by script: `{len(candidates)}`.
- Data mart row count: `{coverage['rows']}`.
- Leakage fail rows in mart: `{coverage['leakage_fail_rows']}`.
- As-of fail rows in mart: `{coverage['asof_fail_rows']}`.
- Age/lifecycle leakage caveat rows: `{coverage['age_leakage_caveat_rows']}`.
- Age/lifecycle identity caveat rows: `{coverage['age_identity_caveat_rows']}`.
- Age/lifecycle leakage blocked rows: `{coverage['age_leakage_blocked_rows']}`.
- Age/lifecycle identity blocked rows: `{coverage['age_identity_blocked_rows']}`.
"""
    write_text(OUT_DIR / "SMALL_FORMULA_PILOT_SOURCE_TRACE.md", source_trace)


def main() -> None:
    candidates = load_candidates()
    rows = load_panel()
    add_scores_and_ranks(rows)
    coverage = coverage_summary(rows)
    if coverage["rows"] != 5518:
        raise RuntimeError(f"Unexpected row count: {coverage['rows']}")
    if coverage["model_use_allowed_true"] != 0 or coverage["production_approved_true"] != 0:
        raise RuntimeError("Production/model-use guard failed.")
    if coverage["leakage_fail_rows"] != 0 or coverage["asof_fail_rows"] != 0:
        raise RuntimeError("Formula mart leakage/as-of guard failed.")
    if coverage["age_leakage_blocked_rows"] != 0 or coverage["age_identity_blocked_rows"] != 0:
        raise RuntimeError("Age/lifecycle leakage or identity guard failed.")

    cand_rows, pyf_rows, pos_rows = candidate_results(rows, candidates)
    slice_rows = slice_guardrails(rows, candidates)

    write_csv(
        OUT_DIR / "SMALL_FORMULA_PILOT_CANDIDATE_RESULTS.csv",
        cand_rows,
        [
            "candidate_id",
            "candidate_family",
            "positions",
            "rows_tested",
            "score_mode",
            "changes_rank_vs_pyf",
            "spearman_overall",
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
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "SMALL_FORMULA_PILOT_PYF_COMPARISON.csv",
        pyf_rows,
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
            "candidate_false_negatives",
            "pyf_false_negatives",
            "beat_pyf",
            "comparison_result",
        ],
    )
    write_csv(
        OUT_DIR / "SMALL_FORMULA_PILOT_POSITION_RESULTS.csv",
        pos_rows,
        [
            "candidate_id",
            "position",
            "rows_tested",
            "candidate_spearman",
            "pyf_spearman",
            "spearman_delta",
            "startable_precision",
            "pyf_startable_precision",
            "top_12_precision",
            "pyf_top_12_precision",
            "top_24_precision",
            "pyf_top_24_precision",
            "top_36_precision",
            "pyf_top_36_precision",
            "candidate_false_positives",
            "candidate_false_negatives",
            "beat_pyf_by_position",
        ],
    )
    write_csv(
        OUT_DIR / "SMALL_FORMULA_PILOT_SLICE_GUARDRAILS.csv",
        slice_rows,
        [
            "candidate_id",
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
    write_reports(rows, candidates, cand_rows, pyf_rows, pos_rows, slice_rows)


if __name__ == "__main__":
    main()
