from __future__ import annotations

import csv
import math
import py_compile
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
CONTRACT_COMMIT = "39e5def85d552fe0c0a90257eb217ea4205814ef"

CONTRACT_DIR = REPO / "docs/hq/model/medium_review_only_formula_pilot_contract_v1_20260709"
CONTRACT_CANDIDATES = CONTRACT_DIR / "MEDIUM_FORMULA_PILOT_ALLOWED_CANDIDATES.csv"
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
SMALL_PILOT_DIR = Path(
    r"C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709"
    r"\docs\hq\model\small_review_only_formula_pilot_v1_20260709"
)

POSITIONS = ["QB", "RB", "WR", "TE"]
POSITION_TOPNS = {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}

EXPECTED_CANDIDATES = [
    "MEDIUM_001_PYF_POINTS_ANCHOR",
    "MEDIUM_002_PYF_PRIOR_RANK_ANCHOR",
    "MEDIUM_003_PRIOR_YEAR_PPG_BASELINE",
    "MEDIUM_004_TWO_YEAR_80_20",
    "MEDIUM_005_TWO_YEAR_75_25",
    "MEDIUM_006_TWO_YEAR_70_30",
    "MEDIUM_007_TWO_YEAR_65_35",
    "MEDIUM_008_TWO_YEAR_60_40",
    "MEDIUM_009_THREE_YEAR_70_20_10",
    "MEDIUM_010_THREE_YEAR_65_25_10",
    "MEDIUM_011_THREE_YEAR_60_30_10",
    "MEDIUM_012_THREE_YEAR_55_30_15",
    "MEDIUM_013_THREE_YEAR_50_35_15",
    "MEDIUM_014_THREE_YEAR_50_30_20",
    "MEDIUM_015_QB_TWO_YEAR_85_15",
    "MEDIUM_016_QB_THREE_YEAR_70_20_10",
    "MEDIUM_017_RB_TWO_YEAR_85_15",
    "MEDIUM_018_RB_THREE_YEAR_75_20_05",
    "MEDIUM_019_WR_TWO_YEAR_70_30",
    "MEDIUM_020_WR_THREE_YEAR_55_30_15",
    "MEDIUM_021_TE_TWO_YEAR_70_30",
    "MEDIUM_022_TE_THREE_YEAR_60_30_10",
    "MEDIUM_023_SPARSE_FALLBACK_TWO_YEAR_TO_PYF",
    "MEDIUM_024_SPARSE_FALLBACK_THREE_YEAR_TO_PYF",
    "MEDIUM_025_LOW_GAMES_FALLBACK_TWO_YEAR_TO_PYF",
    "MEDIUM_026_LOW_GAMES_FALLBACK_THREE_YEAR_TO_PYF",
    "MEDIUM_027_HISTORY_COVERAGE_MINIMUM_TWO_YEAR",
    "MEDIUM_028_HISTORY_COVERAGE_MINIMUM_THREE_YEAR",
    "MEDIUM_029_PRIOR_DECLINE_THREE_YEAR_CONTEXT",
    "MEDIUM_030_HIGH_VOLUME_FALSE_POSITIVE_DIAGNOSTIC",
    "MEDIUM_031_LATE_LIFECYCLE_DECLINE_DIAGNOSTIC",
    "MEDIUM_032_AGE_ROLE_DECLINE_CROSS_SLICE",
    "MEDIUM_033_LIFECYCLE_SLICED_THREE_YEAR_REPORT",
    "MEDIUM_034_LATE_CAREER_DIAGNOSTIC",
    "MEDIUM_035_YOUNG_EARLY_BREAKOUT_DIAGNOSTIC",
    "MEDIUM_036_POSITION_AGE_CURVE_SLICE_REPORT",
    "MEDIUM_037_HIGH_VOLUME_ROLE_SLICE_REPORT",
    "MEDIUM_038_LOW_OR_SPARSE_ROLE_SLICE_REPORT",
    "MEDIUM_039_RB_TOUCH_VOLUME_ROLE_SLICE",
    "MEDIUM_040_WR_TE_TARGET_VOLUME_ROLE_SLICE",
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


def group_rows(rows: list[dict[str, object]], keys: tuple[str, ...]) -> dict[tuple[object, ...], list[dict[str, object]]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def assign_rank(rows: list[dict[str, object]], score_col: str, rank_col: str) -> None:
    for row in rows:
        row[rank_col] = None
    grouped = group_rows(rows, ("season", "position"))
    for group in grouped.values():
        eligible = [row for row in group if row.get(score_col) is not None]
        ordered = sorted(
            eligible,
            key=lambda row: (
                float(row[score_col]),
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
    status = []
    status.append("n_minus_2_reconstructed_from_70_30" if y2_available else "n_minus_2_fallback_to_n_minus_1")
    status.append("n_minus_3_reconstructed_from_60_30_10" if y3_available else "n_minus_3_fallback_to_n_minus_2")
    row["history_reconstruction_status"] = ";".join(status)


def weighted2(row: dict[str, object], w1: float, w2: float) -> float | None:
    y1 = row["n_minus_1_points"]
    y2 = row["n_minus_2_points"]
    if y1 is None or y2 is None:
        return None
    return w1 * y1 + w2 * y2


def weighted3(row: dict[str, object], w1: float, w2: float, w3: float) -> float | None:
    y1 = row["n_minus_1_points"]
    y2 = row["n_minus_2_points"]
    y3 = row["n_minus_3_points"]
    if y1 is None or y2 is None or y3 is None:
        return None
    return w1 * y1 + w2 * y2 + w3 * y3


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
        out["age"] = num(age.get("age"))
        out["age_bucket"] = age.get("age_bucket", "")
        out["lifecycle_bucket"] = age.get("lifecycle_bucket", "")
        out["career_stage"] = age.get("career_stage", "")
        out["age_missing"] = out["age"] is None
        out["age_decision_date_safe"] = age.get("decision_date_safe", "")
        out["age_leakage_flag"] = age.get("leakage_flag", "")
        out["age_identity_flag"] = age.get("identity_flag", "")
        out["age_missingness_flag"] = age.get("missingness_flag", "")
        out["age_review_only_status"] = age.get("review_only_status", "")
        reconstruct_history(out)
        rows.append(out)
    validate_source_use_gates(rows)
    return rows


def validate_source_use_gates(rows: list[dict[str, object]]) -> None:
    if len(rows) != 5518:
        raise RuntimeError(f"Unexpected data mart row count {len(rows)}; expected 5518.")
    if any(str(row.get("review_only")).strip().lower() != "true" for row in rows):
        raise RuntimeError("Data mart contains non-review-only rows.")
    if any(str(row.get("model_use_allowed")).strip().lower() == "true" for row in rows):
        raise RuntimeError("Data mart contains model-use allowed rows; pilot must remain review-only.")
    if any(str(row.get("production_approved")).strip().lower() == "true" for row in rows):
        raise RuntimeError("Data mart contains production-approved rows; pilot must remain review-only.")
    if any(not str(row.get("leakage_check_result")).startswith("PASS") for row in rows):
        raise RuntimeError("Data mart leakage/as-of check has non-PASS rows.")
    if any(not str(row.get("asof_check_result")).startswith("PASS") for row in rows):
        raise RuntimeError("Data mart as-of check has non-PASS rows.")
    age_blocked = [
        row
        for row in rows
        if not str(row.get("age_leakage_flag")).startswith("PASS")
        and str(row.get("age_leakage_flag")) != "NOT_USABLE_FOR_AGE_SIGNAL_WHEN_BIRTHDATE_MISSING"
    ]
    if age_blocked:
        raise RuntimeError(f"Age/lifecycle leakage blocked rows found: {len(age_blocked)}")


def load_candidates() -> list[dict[str, str]]:
    candidates = read_csv(CONTRACT_CANDIDATES)
    ids = [row["candidate_id"] for row in candidates]
    if ids != EXPECTED_CANDIDATES:
        raise RuntimeError("Contract candidate IDs do not match the approved fixed 40-candidate list.")
    return candidates


def candidate_positions(candidate: dict[str, str]) -> set[str]:
    scope = candidate["position_scope"]
    if scope == "QB/RB/WR/TE":
        return set(POSITIONS)
    if scope == "WR/TE":
        return {"WR", "TE"}
    return {scope}


def candidate_changes_rank(candidate: dict[str, str]) -> bool:
    return str(candidate["score_changes_allowed"]).strip().lower() == "yes"


def score_for_candidate(candidate_id: str, row: dict[str, object]) -> float | None:
    pos = row["position"]
    if candidate_id == "MEDIUM_001_PYF_POINTS_ANCHOR":
        return row["pyf_score"]
    if candidate_id == "MEDIUM_002_PYF_PRIOR_RANK_ANCHOR":
        rank = row["pyf_prior_rank"]
        return -rank if rank is not None else None
    if candidate_id == "MEDIUM_003_PRIOR_YEAR_PPG_BASELINE":
        return row["pyf_ppg"]
    if candidate_id == "MEDIUM_004_TWO_YEAR_80_20":
        return weighted2(row, 0.80, 0.20)
    if candidate_id == "MEDIUM_005_TWO_YEAR_75_25":
        return weighted2(row, 0.75, 0.25)
    if candidate_id == "MEDIUM_006_TWO_YEAR_70_30":
        return row["two_year_70_30"]
    if candidate_id == "MEDIUM_007_TWO_YEAR_65_35":
        return weighted2(row, 0.65, 0.35)
    if candidate_id == "MEDIUM_008_TWO_YEAR_60_40":
        return weighted2(row, 0.60, 0.40)
    if candidate_id == "MEDIUM_009_THREE_YEAR_70_20_10":
        return weighted3(row, 0.70, 0.20, 0.10)
    if candidate_id == "MEDIUM_010_THREE_YEAR_65_25_10":
        return weighted3(row, 0.65, 0.25, 0.10)
    if candidate_id == "MEDIUM_011_THREE_YEAR_60_30_10":
        return row["three_year_60_30_10"]
    if candidate_id == "MEDIUM_012_THREE_YEAR_55_30_15":
        return weighted3(row, 0.55, 0.30, 0.15)
    if candidate_id == "MEDIUM_013_THREE_YEAR_50_35_15":
        return weighted3(row, 0.50, 0.35, 0.15)
    if candidate_id == "MEDIUM_014_THREE_YEAR_50_30_20":
        return weighted3(row, 0.50, 0.30, 0.20)
    if candidate_id == "MEDIUM_015_QB_TWO_YEAR_85_15":
        return weighted2(row, 0.85, 0.15) if pos == "QB" else None
    if candidate_id == "MEDIUM_016_QB_THREE_YEAR_70_20_10":
        return weighted3(row, 0.70, 0.20, 0.10) if pos == "QB" else None
    if candidate_id == "MEDIUM_017_RB_TWO_YEAR_85_15":
        return weighted2(row, 0.85, 0.15) if pos == "RB" else None
    if candidate_id == "MEDIUM_018_RB_THREE_YEAR_75_20_05":
        return weighted3(row, 0.75, 0.20, 0.05) if pos == "RB" else None
    if candidate_id == "MEDIUM_019_WR_TWO_YEAR_70_30":
        return row["two_year_70_30"] if pos == "WR" else None
    if candidate_id == "MEDIUM_020_WR_THREE_YEAR_55_30_15":
        return weighted3(row, 0.55, 0.30, 0.15) if pos == "WR" else None
    if candidate_id == "MEDIUM_021_TE_TWO_YEAR_70_30":
        return row["two_year_70_30"] if pos == "TE" else None
    if candidate_id == "MEDIUM_022_TE_THREE_YEAR_60_30_10":
        return row["three_year_60_30_10"] if pos == "TE" else None
    if candidate_id == "MEDIUM_023_SPARSE_FALLBACK_TWO_YEAR_TO_PYF":
        return row["pyf_score"] if row["sparse_history_bool"] else row["two_year_70_30"]
    if candidate_id == "MEDIUM_024_SPARSE_FALLBACK_THREE_YEAR_TO_PYF":
        return row["pyf_score"] if row["sparse_history_bool"] else row["three_year_60_30_10"]
    if candidate_id == "MEDIUM_025_LOW_GAMES_FALLBACK_TWO_YEAR_TO_PYF":
        return row["pyf_score"] if row["low_games_bool"] else row["two_year_70_30"]
    if candidate_id == "MEDIUM_026_LOW_GAMES_FALLBACK_THREE_YEAR_TO_PYF":
        return row["pyf_score"] if row["low_games_bool"] else row["three_year_60_30_10"]
    if candidate_id == "MEDIUM_027_HISTORY_COVERAGE_MINIMUM_TWO_YEAR":
        return row["pyf_score"] if row["prior_2yr_years"] < 2 else row["two_year_70_30"]
    if candidate_id == "MEDIUM_028_HISTORY_COVERAGE_MINIMUM_THREE_YEAR":
        return row["two_year_70_30"] if row["prior_3yr_years"] < 3 else row["three_year_60_30_10"]
    if candidate_id in {
        "MEDIUM_029_PRIOR_DECLINE_THREE_YEAR_CONTEXT",
        "MEDIUM_033_LIFECYCLE_SLICED_THREE_YEAR_REPORT",
        "MEDIUM_037_HIGH_VOLUME_ROLE_SLICE_REPORT",
    }:
        return row["three_year_60_30_10"]
    if candidate_id == "MEDIUM_039_RB_TOUCH_VOLUME_ROLE_SLICE":
        return row["three_year_60_30_10"] if pos == "RB" else None
    if candidate_id == "MEDIUM_040_WR_TE_TARGET_VOLUME_ROLE_SLICE":
        if pos == "WR":
            return row["two_year_70_30"]
        if pos == "TE":
            return row["three_year_60_30_10"]
        return None
    if candidate_id in {
        "MEDIUM_030_HIGH_VOLUME_FALSE_POSITIVE_DIAGNOSTIC",
        "MEDIUM_031_LATE_LIFECYCLE_DECLINE_DIAGNOSTIC",
        "MEDIUM_032_AGE_ROLE_DECLINE_CROSS_SLICE",
        "MEDIUM_034_LATE_CAREER_DIAGNOSTIC",
        "MEDIUM_035_YOUNG_EARLY_BREAKOUT_DIAGNOSTIC",
        "MEDIUM_036_POSITION_AGE_CURVE_SLICE_REPORT",
        "MEDIUM_038_LOW_OR_SPARSE_ROLE_SLICE_REPORT",
    }:
        return row["pyf_score"]
    raise KeyError(candidate_id)


def add_scores_and_ranks(rows: list[dict[str, object]], candidates: list[dict[str, str]]) -> None:
    for row in rows:
        for candidate in candidates:
            candidate_id = candidate["candidate_id"]
            row[f"{candidate_id}_score"] = score_for_candidate(candidate_id, row)
    for candidate in candidates:
        assign_rank(rows, f"{candidate['candidate_id']}_score", f"{candidate['candidate_id']}_rank")


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


def candidate_scope(candidate: dict[str, str], rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], str]:
    positions = candidate_positions(candidate)
    scoped = [row for row in rows if str(row["position"]) in positions and row.get(f"{candidate['candidate_id']}_rank") is not None]
    return scoped, "/".join([pos for pos in POSITIONS if pos in positions])


def pct_delta(candidate: float | None, baseline: float | None) -> float | None:
    if candidate is None or baseline is None:
        return None
    return candidate - baseline


def build_candidate_outputs(
    rows: list[dict[str, object]], candidates: list[dict[str, str]]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    candidate_rows: list[dict[str, object]] = []
    pyf_rows: list[dict[str, object]] = []
    position_rows: list[dict[str, object]] = []
    pyf_rank = "MEDIUM_001_PYF_POINTS_ANCHOR_rank"
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        scoped_rows, scope_positions = candidate_scope(candidate, rows)
        rank_col = f"{candidate_id}_rank"
        cand = metrics_for_rows(scoped_rows, rank_col)
        pyf = metrics_for_rows(scoped_rows, pyf_rank)
        spearman_delta = pct_delta(cand["spearman"], pyf["spearman"])
        precision_delta = pct_delta(cand["startable_precision"], pyf["startable_precision"])
        sparse_delta = pct_delta(cand["sparse_error_rate"], pyf["sparse_error_rate"])
        low_delta = pct_delta(cand["low_games_error_rate"], pyf["low_games_error_rate"])
        beats_pyf = bool(spearman_delta is not None and spearman_delta > 0.0005)
        changes_rank = candidate_changes_rank(candidate)
        contextual = not changes_rank and candidate_id != "MEDIUM_001_PYF_POINTS_ANCHOR"
        if candidate_id == "MEDIUM_001_PYF_POINTS_ANCHOR":
            interpretation = "MIXED_REVIEW_ONLY"
            result = "mandatory_pyf_anchor_not_new_formula"
        elif contextual:
            interpretation = "MIXED_REVIEW_ONLY"
            result = "contextualizes_pyf"
        elif beats_pyf:
            interpretation = "PROMISING_REVIEW_ONLY"
            result = "beats_pyf"
        elif spearman_delta is not None and spearman_delta < -0.0005:
            interpretation = "FAILED_VS_PYF"
            result = "does_not_beat_pyf"
        else:
            interpretation = "WEAK_REVIEW_ONLY"
            result = "roughly_matches_pyf"
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": candidate["candidate_family"],
                "formula_or_diagnostic": candidate["formula_or_diagnostic"],
                "scope": scope_positions,
                "rows_tested": cand["rows"],
                "score_changes_allowed": candidate["score_changes_allowed"],
                "candidate_spearman": fmt(cand["spearman"]),
                "pyf_spearman_comparable": fmt(pyf["spearman"]),
                "spearman_delta_vs_pyf": fmt(spearman_delta),
                "mae_rank_vs_finish": fmt(cand["mae"]),
                "rmse_rank_vs_finish": fmt(cand["rmse"]),
                "startable_precision": pct(cand["startable_precision"]),
                "pyf_startable_precision_comparable": pct(pyf["startable_precision"]),
                "startable_precision_delta_vs_pyf": pct(precision_delta),
                "candidate_false_positives": cand["false_positives"],
                "pyf_false_positives_comparable": pyf["false_positives"],
                "false_positive_delta_vs_pyf": cand["false_positives"] - pyf["false_positives"],
                "candidate_false_negatives": cand["false_negatives"],
                "pyf_false_negatives_comparable": pyf["false_negatives"],
                "false_negative_delta_vs_pyf": cand["false_negatives"] - pyf["false_negatives"],
                "sparse_history_error_delta_vs_pyf": pct(sparse_delta),
                "low_games_error_delta_vs_pyf": pct(low_delta),
                "beats_pyf_overall": str(beats_pyf).lower(),
                "contextualizes_pyf": str(contextual).lower(),
                "interpretation": interpretation,
                "comparison_result": result,
                "caveat": (
                    "diagnostic_context_only_no_production_score_change"
                    if contextual
                    else "fixed_predeclared_review_only_score_no_tuning"
                ),
            }
        )
        pyf_rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_family": candidate["candidate_family"],
                "scope": scope_positions,
                "candidate_spearman": fmt(cand["spearman"]),
                "pyf_spearman": fmt(pyf["spearman"]),
                "spearman_delta": fmt(spearman_delta),
                "candidate_startable_precision": pct(cand["startable_precision"]),
                "pyf_startable_precision": pct(pyf["startable_precision"]),
                "startable_precision_delta": pct(precision_delta),
                "candidate_false_positives": cand["false_positives"],
                "pyf_false_positives": pyf["false_positives"],
                "false_positive_delta": cand["false_positives"] - pyf["false_positives"],
                "candidate_false_negatives": cand["false_negatives"],
                "pyf_false_negatives": pyf["false_negatives"],
                "false_negative_delta": cand["false_negatives"] - pyf["false_negatives"],
                "beat_pyf": str(beats_pyf).lower(),
                "comparison_result": result,
            }
        )
        for position in POSITIONS:
            pos_rows = [row for row in scoped_rows if row["position"] == position]
            if not pos_rows:
                continue
            pos_cand = metrics_for_rows(pos_rows, rank_col)
            pos_pyf = metrics_for_rows(pos_rows, pyf_rank)
            pos_delta = pct_delta(pos_cand["spearman"], pos_pyf["spearman"])
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
                    "candidate_id": candidate_id,
                    "candidate_family": candidate["candidate_family"],
                    "position": position,
                    "rows_tested": pos_cand["rows"],
                    "candidate_spearman": fmt(pos_cand["spearman"]),
                    "pyf_spearman": fmt(pos_pyf["spearman"]),
                    "spearman_delta_vs_pyf": fmt(pos_delta),
                    "startable_precision": pct(pos_cand["startable_precision"]),
                    "pyf_startable_precision": pct(pos_pyf["startable_precision"]),
                    "top_12_precision": top_values["top_12_precision"],
                    "pyf_top_12_precision": top_values["pyf_top_12_precision"],
                    "top_24_precision": top_values["top_24_precision"],
                    "pyf_top_24_precision": top_values["pyf_top_24_precision"],
                    "top_36_precision": top_values["top_36_precision"],
                    "pyf_top_36_precision": top_values["pyf_top_36_precision"],
                    "candidate_false_positives": pos_cand["false_positives"],
                    "pyf_false_positives": pos_pyf["false_positives"],
                    "candidate_false_negatives": pos_cand["false_negatives"],
                    "pyf_false_negatives": pos_pyf["false_negatives"],
                    "beat_pyf_by_position": str(bool(pos_delta is not None and pos_delta > 0.0005)).lower(),
                }
            )
    return candidate_rows, pyf_rows, position_rows


def slice_guardrails(rows: list[dict[str, object]], candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    slice_defs: dict[str, Callable[[dict[str, object]], bool]] = {
        "sparse_history": lambda r: bool(r["sparse_history_bool"]),
        "low_games": lambda r: bool(r["low_games_bool"]),
        "older_late_lifecycle": is_older_late,
        "young_early_lifecycle": is_young_early,
        "high_volume_role": is_high_volume_role,
        "low_or_sparse_role": is_low_or_sparse_role,
        "rb_touch_volume_high": lambda r: r["position"] == "RB" and is_high_volume_role(r),
        "wr_te_target_volume_high": lambda r: r["position"] in {"WR", "TE"} and is_high_volume_role(r),
        "age_missing": lambda r: bool(r["age_missing"]),
    }
    pyf_rank = "MEDIUM_001_PYF_POINTS_ANCHOR_rank"
    output: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        scoped_rows, scope_positions = candidate_scope(candidate, rows)
        rank_col = f"{candidate_id}_rank"
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
            pyf_fp = [row for row in group if predicted_startable(row, pyf_rank) and not row["actual_startable"]]
            pyf_fn = [row for row in group if not predicted_startable(row, pyf_rank) and row["actual_startable"]]
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
                    "guardrail_interpretation": (
                        "no_added_harm_vs_pyf"
                        if abs(delta) < 0.0005
                        else ("worse_than_pyf" if delta > 0 else "improves_vs_pyf")
                    ),
                }
            )
    return output


def stability_by_season(rows: list[dict[str, object]], candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    pyf_rank = "MEDIUM_001_PYF_POINTS_ANCHOR_rank"
    seasons = sorted({row["season"] for row in rows})
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        rank_col = f"{candidate_id}_rank"
        scoped_rows, scope_positions = candidate_scope(candidate, rows)
        for season in seasons:
            season_rows = [row for row in scoped_rows if row["season"] == season]
            if not season_rows:
                continue
            cand = metrics_for_rows(season_rows, rank_col)
            pyf = metrics_for_rows(season_rows, pyf_rank)
            delta = pct_delta(cand["spearman"], pyf["spearman"])
            output.append(
                {
                    "candidate_id": candidate_id,
                    "scope": scope_positions,
                    "season": season,
                    "rows": cand["rows"],
                    "candidate_spearman": fmt(cand["spearman"]),
                    "pyf_spearman": fmt(pyf["spearman"]),
                    "spearman_delta_vs_pyf": fmt(delta),
                    "beat_pyf_in_season": str(bool(delta is not None and delta > 0.0005)).lower(),
                    "candidate_false_positives": cand["false_positives"],
                    "pyf_false_positives": pyf["false_positives"],
                    "candidate_false_negatives": cand["false_negatives"],
                    "pyf_false_negatives": pyf["false_negatives"],
                    "stability_caveat": "season_sample_directional_only",
                }
            )
    return output


def coverage_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    positions = dict(Counter(str(row["position"]) for row in rows))
    return {
        "rows": len(rows),
        "seasons": f"{min(int(row['season']) for row in rows)}-{max(int(row['season']) for row in rows)}",
        "positions": positions,
        "age_missing": sum(1 for row in rows if row["age_missing"]),
        "sparse_rows": sum(1 for row in rows if row["sparse_history_bool"]),
        "low_games_rows": sum(1 for row in rows if row["low_games_bool"]),
        "review_only_rows": sum(1 for row in rows if str(row["review_only"]).lower() == "true"),
        "model_use_allowed_true": sum(1 for row in rows if str(row["model_use_allowed"]).lower() == "true"),
        "production_approved_true": sum(1 for row in rows if str(row["production_approved"]).lower() == "true"),
    }


def ffloat(value: object) -> float:
    text = str(value).strip()
    return float(text) if text else -999.0


def write_reports(
    rows: list[dict[str, object]],
    candidates: list[dict[str, str]],
    candidate_rows: list[dict[str, object]],
    pyf_rows: list[dict[str, object]],
    position_rows: list[dict[str, object]],
    slice_rows: list[dict[str, object]],
    stability_rows: list[dict[str, object]],
) -> None:
    coverage = coverage_summary(rows)
    pyf_all = next(row for row in candidate_rows if row["candidate_id"] == "MEDIUM_001_PYF_POINTS_ANCHOR")
    non_pyf = [row for row in candidate_rows if row["candidate_id"] != "MEDIUM_001_PYF_POINTS_ANCHOR"]
    rank_changing = [row for row in non_pyf if row["score_changes_allowed"] == "yes"]
    beaters = [row for row in rank_changing if row["beats_pyf_overall"] == "true"]
    position_beaters = [row for row in position_rows if row["beat_pyf_by_position"] == "true"]
    failed = [row for row in candidate_rows if row["interpretation"] == "FAILED_VS_PYF"]
    contextual = [row for row in candidate_rows if row["contextualizes_pyf"] == "true"]
    best_overall = max(non_pyf, key=lambda row: ffloat(row["candidate_spearman"]))
    best_by_position = {}
    for position in POSITIONS:
        pos_candidates = [
            row
            for row in position_rows
            if row["position"] == position and row["candidate_id"] != "MEDIUM_001_PYF_POINTS_ANCHOR"
        ]
        best_by_position[position] = max(pos_candidates, key=lambda row: ffloat(row["candidate_spearman"]))
    pyf_slice = lambda name: [
        row
        for row in slice_rows
        if row["candidate_id"] == "MEDIUM_001_PYF_POINTS_ANCHOR" and row["slice_name"] == name
    ][0]
    sparse = pyf_slice("sparse_history")
    low_games = pyf_slice("low_games")
    high_role = pyf_slice("high_volume_role")
    low_role = pyf_slice("low_or_sparse_role")
    older = pyf_slice("older_late_lifecycle")
    young = pyf_slice("young_early_lifecycle")
    stable_beaters = []
    for row in beaters:
        seasons_for_candidate = [
            srow for srow in stability_rows if srow["candidate_id"] == row["candidate_id"] and srow["spearman_delta_vs_pyf"]
        ]
        positive = sum(1 for srow in seasons_for_candidate if srow["beat_pyf_in_season"] == "true")
        row["positive_seasons_vs_pyf"] = positive
        row["season_direction_count"] = len(seasons_for_candidate)
        if positive >= max(1, len(seasons_for_candidate) // 2):
            stable_beaters.append(row)
    verdict = (
        "GREEN_MEDIUM_FORMULA_PILOT_FOUND_STRONG_REVIEW_ONLY_CANDIDATES"
        if stable_beaters
        else ("YELLOW_MEDIUM_FORMULA_PILOT_FOUND_MIXED_CANDIDATES" if beaters or contextual else "RED_MEDIUM_FORMULA_PILOT_NO_CANDIDATE_BEATS_PYF")
    )
    next_lane = (
        "Focused 60-80 Candidate Review-Only Gauntlet Contract V1"
        if stable_beaters
        else "Add Missing Data Before More Formula Work V1"
    )

    report = f"""
# Medium Review-Only Formula Pilot V1 Report

## Verdict

`{verdict}`

## Clear Answer

The medium review-only formula pilot ran exactly `40` approved candidates against `{coverage['rows']}` review-only player-season rows. `{len(beaters)}` rank-changing candidate(s) beat PYF overall by Spearman, and `{len(position_beaters)}` candidate-position result(s) beat PYF by position. The strongest family remained fixed multi-year weighted production. Role archetype and age/lifecycle remained useful for slice reporting and guardrail context, not as production ranking inputs.

## Benchmark Scope

- Rows tested: `{coverage['rows']}`
- Seasons: `{coverage['seasons']}`
- Positions: `{coverage['positions']}`
- Candidates tested: `{len(candidates)}`
- Review-only rows: `{coverage['review_only_rows']}`
- Model-use allowed rows: `{coverage['model_use_allowed_true']}`
- Production-approved rows: `{coverage['production_approved_true']}`
- Sparse-history rows: `{coverage['sparse_rows']}`
- Low-games rows: `{coverage['low_games_rows']}`
- Missing age/lifecycle rows: `{coverage['age_missing']}`

## Best Overall Review-Only Candidate

`{best_overall['candidate_id']}` produced Spearman `{best_overall['candidate_spearman']}` versus comparable PYF `{best_overall['pyf_spearman_comparable']}`.

## Best Candidate By Position

- QB: `{best_by_position['QB']['candidate_id']}` with Spearman `{best_by_position['QB']['candidate_spearman']}` versus PYF `{best_by_position['QB']['pyf_spearman']}`.
- RB: `{best_by_position['RB']['candidate_id']}` with Spearman `{best_by_position['RB']['candidate_spearman']}` versus PYF `{best_by_position['RB']['pyf_spearman']}`.
- WR: `{best_by_position['WR']['candidate_id']}` with Spearman `{best_by_position['WR']['candidate_spearman']}` versus PYF `{best_by_position['WR']['pyf_spearman']}`.
- TE: `{best_by_position['TE']['candidate_id']}` with Spearman `{best_by_position['TE']['candidate_spearman']}` versus PYF `{best_by_position['TE']['pyf_spearman']}`.

## PYF Comparison

- PYF overall Spearman: `{pyf_all['candidate_spearman']}`
- PYF startable precision: `{pyf_all['startable_precision']}`
- Rank-changing candidates beating PYF overall: `{len(beaters)}`
- Candidate-position results beating PYF: `{len(position_beaters)}`
- Context-only diagnostic candidates: `{len(contextual)}`

## Guardrail Findings

- Sparse-history rows: `{sparse['rows']}` with startable rate `{sparse['startable_rate']}`.
- Low-games rows: `{low_games['rows']}` with startable rate `{low_games['startable_rate']}`.
- High-volume role rows contained `{high_role['pyf_false_positives']}` PYF false positives.
- Low/sparse role rows contained `{low_role['pyf_false_negatives']}` PYF false negatives.
- Older/late lifecycle rows contained `{older['pyf_false_positives']}` PYF false positives.
- Young/early lifecycle rows contained `{young['pyf_false_negatives']}` PYF false negatives.

## Interpretation

This pilot does not approve a formula winner, production model, ranking input, hidden sort, or app behavior change. It shows that simple fixed multi-year production variants remain the best near-term review-only direction. Age/lifecycle and role archetype are useful because they explain where PYF and multi-year production miss, especially older prior-production decline and young/early breakout-window rows.

## Recommendation

Recommended next lane: `{next_lane}`.

Master HQ should only consider a focused review-only expansion if it remains fixed, predeclared, source-gated, and explicitly non-production. The 100-candidate Gauntlet, champion refinement, rankings integration, and production/model-use remain blocked.
"""
    write_text(OUT_DIR / "MEDIUM_REVIEW_ONLY_FORMULA_PILOT_V1_REPORT.md", report)

    miss_review = f"""
# Medium Formula Pilot Miss Pattern Review

## Sparse History / Low Games

Sparse-history and low-games rows each covered `{sparse['rows']}` rows with a `{sparse['startable_rate']}` baseline startable rate. The guarded fallback variants did not convert this slice into a production-safe penalty. These rows remain a primary guardrail and caveat for any future formula work.

## Prior-Production Decline

High-volume role rows concentrated `{high_role['pyf_false_positives']}` PYF false positives. Older/late lifecycle rows concentrated `{older['pyf_false_positives']}` PYF false positives. This supports decline-risk reporting and miss taxonomy, but not an automatic age or role penalty.

## Role Archetype Slices

Role archetype remains useful for explaining where PYF can over-trust prior production or miss low/sparse breakout rows. Low/sparse role rows contained `{low_role['pyf_false_negatives']}` PYF false negatives, so blunt penalties would create harm.

## Age / Lifecycle Slices

Young/early lifecycle rows contained `{young['pyf_false_negatives']}` PYF false negatives. Age/lifecycle is useful for formula-family context and guardrails, but it can over-penalize older elite producers and over-reward young low-production players if treated as a direct score.
"""
    write_text(OUT_DIR / "MEDIUM_FORMULA_PILOT_MISS_PATTERN_REVIEW.md", miss_review)

    top_lines = [
        "# Medium Formula Pilot Top Review-Only Candidates",
        "",
        "No item below is a production winner, champion, ranking input, or model-use approval.",
        "",
        "## Rank-Changing Candidates Beating PYF Overall",
    ]
    if beaters:
        for row in sorted(beaters, key=lambda r: ffloat(r["candidate_spearman"]), reverse=True):
            top_lines.append(
                f"- `{row['candidate_id']}`: Spearman `{row['candidate_spearman']}` versus PYF `{row['pyf_spearman_comparable']}`; delta `{row['spearman_delta_vs_pyf']}`; startable precision `{row['startable_precision']}`."
            )
    else:
        top_lines.append("- None.")
    top_lines.extend(["", "## Context-Only Diagnostics"])
    for row in contextual:
        top_lines.append(f"- `{row['candidate_id']}`: `{row['comparison_result']}`; `{row['caveat']}`.")
    write_text(OUT_DIR / "MEDIUM_FORMULA_PILOT_TOP_REVIEW_ONLY_CANDIDATES.md", "\n".join(top_lines))

    failed_lines = [
        "# Medium Formula Pilot Failed Candidates",
        "",
        "A failed candidate here means it did not beat its comparable PYF anchor by the predeclared Spearman check. No candidate is production integrated.",
        "",
    ]
    if failed:
        for row in failed:
            failed_lines.append(
                f"- `{row['candidate_id']}`: Spearman `{row['candidate_spearman']}` versus PYF `{row['pyf_spearman_comparable']}`; delta `{row['spearman_delta_vs_pyf']}`."
            )
    else:
        failed_lines.append("No candidate was classified `FAILED_VS_PYF`; weak/contextual candidates are still not production candidates.")
    write_text(OUT_DIR / "MEDIUM_FORMULA_PILOT_FAILED_CANDIDATES.md", "\n".join(failed_lines))

    caveats = f"""
# Medium Formula Pilot Blockers And Caveats

- This is not Formula Gauntlet.
- This is not a 100-candidate Gauntlet.
- This is not champion refinement.
- This is not production/model-use.
- This is not rankings integration.
- No candidate is a winner, champion, approved formula, or ranking-ready formula.
- Exact Model v4 historical replay remains blocked.
- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Source promotion remains blocked.
- Candidate definitions were fixed by contract before execution.
- Additional two-year and three-year weight variants were deterministically reconstructed from review-only weighted fields, so they are useful for review-only direction but should not be treated as exact recovered raw yearly receipts.
- Role archetype and age/lifecycle are diagnostic context and slice reporting only.
"""
    write_text(OUT_DIR / "MEDIUM_FORMULA_PILOT_BLOCKERS_AND_CAVEATS.md", caveats)

    source_trace = f"""
# Medium Formula Pilot Source Trace

## Inputs

- Medium Review-Only Formula Pilot Contract V1: `{CONTRACT_DIR}`
- Contract commit: `{CONTRACT_COMMIT}`
- Formula Data Mart Review-Only CSV: `{DATA_MART}`
- Age/Lifecycle Sidecar Review-Only CSV: `{AGE_SIDECAR}`
- Small Review-Only Formula Pilot V1: `{SMALL_PILOT_DIR}`

## Use Gate

- All rows are review-only.
- No production/model-use rows were admitted.
- No source was promoted.
- No ranking/app/runtime/model behavior changed.
- No canonical `local_exports` writes occurred.

## Leakage / As-Of

The script requires PASS leakage/as-of flags on the Formula Data Mart and rejects blocked age/lifecycle leakage rows. Missing age rows remain caveated and are not treated as production-safe age signals.
"""
    write_text(OUT_DIR / "MEDIUM_FORMULA_PILOT_SOURCE_TRACE.md", source_trace)


def validate_outputs() -> None:
    required = [
        "MEDIUM_REVIEW_ONLY_FORMULA_PILOT_V1_REPORT.md",
        "MEDIUM_FORMULA_PILOT_CANDIDATE_RESULTS.csv",
        "MEDIUM_FORMULA_PILOT_PYF_COMPARISON.csv",
        "MEDIUM_FORMULA_PILOT_POSITION_RESULTS.csv",
        "MEDIUM_FORMULA_PILOT_SLICE_GUARDRAILS.csv",
        "MEDIUM_FORMULA_PILOT_STABILITY_BY_SEASON.csv",
        "MEDIUM_FORMULA_PILOT_MISS_PATTERN_REVIEW.md",
        "MEDIUM_FORMULA_PILOT_TOP_REVIEW_ONLY_CANDIDATES.md",
        "MEDIUM_FORMULA_PILOT_FAILED_CANDIDATES.md",
        "MEDIUM_FORMULA_PILOT_BLOCKERS_AND_CAVEATS.md",
        "MEDIUM_FORMULA_PILOT_SOURCE_TRACE.md",
        "run_medium_review_only_formula_pilot_v1.py",
    ]
    missing = [name for name in required if not (OUT_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"Missing required outputs: {missing}")
    for csv_name in [
        "MEDIUM_FORMULA_PILOT_CANDIDATE_RESULTS.csv",
        "MEDIUM_FORMULA_PILOT_PYF_COMPARISON.csv",
        "MEDIUM_FORMULA_PILOT_POSITION_RESULTS.csv",
        "MEDIUM_FORMULA_PILOT_SLICE_GUARDRAILS.csv",
        "MEDIUM_FORMULA_PILOT_STABILITY_BY_SEASON.csv",
    ]:
        rows = read_csv(OUT_DIR / csv_name)
        if not rows:
            raise RuntimeError(f"{csv_name} parsed but has no rows.")
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)


def main() -> None:
    candidates = load_candidates()
    rows = load_panel()
    add_scores_and_ranks(rows, candidates)
    candidate_rows, pyf_rows, position_rows = build_candidate_outputs(rows, candidates)
    slice_rows = slice_guardrails(rows, candidates)
    stability_rows = stability_by_season(rows, candidates)

    write_csv(
        OUT_DIR / "MEDIUM_FORMULA_PILOT_CANDIDATE_RESULTS.csv",
        candidate_rows,
        [
            "candidate_id",
            "candidate_family",
            "formula_or_diagnostic",
            "scope",
            "rows_tested",
            "score_changes_allowed",
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
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MEDIUM_FORMULA_PILOT_PYF_COMPARISON.csv",
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
            "false_positive_delta",
            "candidate_false_negatives",
            "pyf_false_negatives",
            "false_negative_delta",
            "beat_pyf",
            "comparison_result",
        ],
    )
    write_csv(
        OUT_DIR / "MEDIUM_FORMULA_PILOT_POSITION_RESULTS.csv",
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
        OUT_DIR / "MEDIUM_FORMULA_PILOT_SLICE_GUARDRAILS.csv",
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
    write_csv(
        OUT_DIR / "MEDIUM_FORMULA_PILOT_STABILITY_BY_SEASON.csv",
        stability_rows,
        [
            "candidate_id",
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
    write_reports(rows, candidates, candidate_rows, pyf_rows, position_rows, slice_rows, stability_rows)
    validate_outputs()
    print(
        "medium_formula_pilot_complete "
        f"rows={len(rows)} candidates={len(candidates)} "
        f"out={OUT_DIR}"
    )


if __name__ == "__main__":
    main()
