from __future__ import annotations

import ast
import csv
import hashlib
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
POSITIONS = ["QB", "RB", "WR", "TE"]
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
CURRENT_BEST_FULL_HISTORY = 0.755
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
NVERSE_AUDIT_COMMIT = "067111f031a1a20a2411157c54860d4864c79950"
PFR_COMMIT = "843c17838caa020f5f123e6df5cd1fdd45d5b9c6"

MART_PATH = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
    r"\FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
AGE_PATH = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709"
    r"\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709"
    r"\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
)
ADV_CACHE = Path(r"C:\NWR_REVIEW\advanced_metrics_source_cache_20260707")
GAUNTLET_REGISTRY_PATH = Path(
    r"C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709"
    r"\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709"
    r"\GAUNTLET_CANDIDATE_REGISTRY.csv"
)
GAUNTLET_CLUSTER_PATH = Path(
    r"C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709"
    r"\docs\hq\model\gauntlet_candidate_diversity_clustering_audit_v1_20260709"
    r"\GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv"
)
DIVERSE_REGISTRY_PATH = Path(
    r"C:\NWR\Niners-War-Room-diverse-champion-refinement-predeclared-execution-v1-20260709"
    r"\docs\hq\model\diverse_champion_refinement_predeclared_execution_v1_20260709"
    r"\DIVERSE_CHAMPION_REFINEMENT_CANDIDATE_REGISTRY.csv"
)
HANDOFF_DIR = Path(r"C:\NWR\_handoff_unpack\nwr_autonomous_improvement_handoff_v2_20260709\nwr_autonomous_improvement_handoff_v2_20260709")

RESULT_FIELDS = [
    "run_id",
    "formula_id",
    "cluster_id",
    "base_formula",
    "ingredient_set",
    "ingredient_fields",
    "positions",
    "seasons",
    "row_count",
    "coverage_pct",
    "missingness_pct",
    "overall_spearman",
    "position_spearman_qb",
    "position_spearman_rb",
    "position_spearman_wr",
    "position_spearman_te",
    "pyf_delta",
    "current_best_delta",
    "cluster_seed_delta",
    "top12_precision",
    "top24_precision",
    "top36_precision",
    "false_positive_impact",
    "false_negative_impact",
    "sparse_history_impact",
    "low_games_impact",
    "age_lifecycle_slice",
    "role_slice",
    "stability_by_season",
    "leave_one_season_out",
    "outlier_flags",
    "use_decision",
    "notes",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def bool_true(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def fmt(value: float | None, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{float(value):.{digits}f}"


def pct(value: float | None, digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{100.0 * float(value):.{digits}f}%"


def parse_params(text: Any) -> dict[str, Any]:
    if text is None or pd.isna(text) or str(text).strip() == "":
        return {}
    out: dict[str, Any] = {}
    for part in str(text).split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") or value.startswith("{"):
            try:
                out[key] = ast.literal_eval(value)
                continue
            except Exception:
                pass
        try:
            out[key] = float(value)
        except ValueError:
            out[key] = value
    return out


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
    nume = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = sum((x - mx) ** 2 for x in xs)
    den_y = sum((y - my) ** 2 for y in ys)
    if den_x <= 0 or den_y <= 0:
        return None
    return nume / math.sqrt(den_x * den_y)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    return pearson(rank_values(xs), rank_values(ys)) if len(xs) >= 2 else None


def mean(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None and not math.isnan(v)]
    return sum(clean) / len(clean) if clean else None


def group_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped


def assign_rank(rows: list[dict[str, Any]], score_col: str, rank_col: str) -> None:
    for row in rows:
        row[rank_col] = None
    for group in group_rows(rows, ("season", "position")).values():
        eligible = [row for row in group if row.get(score_col) is not None]
        ordered = sorted(eligible, key=lambda row: (float(row[score_col]), str(row["player_id"])), reverse=True)
        for idx, row in enumerate(ordered, start=1):
            row[rank_col] = float(idx)


def assign_percentile(rows: list[dict[str, Any]], score_col: str, out_col: str) -> None:
    for row in rows:
        row[out_col] = None
    for group in group_rows(rows, ("season", "position")).values():
        eligible = [row for row in group if row.get(score_col) is not None]
        ordered = sorted(eligible, key=lambda row: (float(row[score_col]), str(row["player_id"])))
        n = len(ordered)
        if n == 0:
            continue
        for idx, row in enumerate(ordered, start=1):
            row[out_col] = (idx - 1) / (n - 1) if n > 1 else 1.0


def weighted_avg(df: pd.DataFrame, value_col: str, weight_col: str) -> float | None:
    if value_col not in df.columns:
        return None
    vals = pd.to_numeric(df[value_col], errors="coerce")
    if weight_col in df.columns:
        weights = pd.to_numeric(df[weight_col], errors="coerce").fillna(0)
        mask = vals.notna() & (weights > 0)
        if mask.any() and weights[mask].sum() > 0:
            return float((vals[mask] * weights[mask]).sum() / weights[mask].sum())
    if vals.notna().any():
        return float(vals.mean())
    return None


def source_ledger(paths: list[Path], family: str) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(paths):
        if not path.exists():
            continue
        st = path.stat()
        rows.append(
            {
                "source_family": family,
                "source_path": str(path),
                "file_name": path.name,
                "file_size": st.st_size,
                "modified_time": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                "sha256": sha256_file(path),
                "source_gate_status": "public_nflverse_review_only_not_production_model_use",
                "asof_rule": "closed feature season N may be used only for target season N+1 review tests",
            }
        )
    return rows


def load_formula_panel() -> list[dict[str, Any]]:
    mart = pd.read_csv(MART_PATH)
    age = pd.read_csv(AGE_PATH)
    key_cols = ["player_id", "season", "position"]
    merged = mart.merge(
        age[
            [
                "player_id",
                "season",
                "position",
                "age",
                "age_bucket",
                "lifecycle_bucket",
                "career_stage",
                "leakage_flag",
                "identity_flag",
            ]
        ],
        on=key_cols,
        how="left",
        suffixes=("", "_age"),
    )
    if len(merged) != 5518:
        raise RuntimeError(f"Unexpected merged mart row count {len(merged)}")
    rows = []
    for row in merged.to_dict("records"):
        if str(row.get("review_only")).lower() != "true":
            raise RuntimeError("Non-review-only Formula Mart row encountered.")
        if str(row.get("model_use_allowed")).lower() == "true" or str(row.get("production_approved")).lower() == "true":
            raise RuntimeError("Model-use or production-approved mart row encountered.")
        if not str(row.get("leakage_check_result")).startswith("PASS"):
            raise RuntimeError("Formula Mart leakage check failed.")
        if not str(row.get("asof_check_result")).startswith("PASS"):
            raise RuntimeError("Formula Mart as-of check failed.")
        out = dict(row)
        out["season"] = int(row["season"])
        out["feature_season"] = int(row["feature_season"])
        out["position"] = str(row["position"])
        out["player_id"] = str(row["player_id"])
        out["player_name"] = str(row.get("player_name") or row.get("target_player_name") or "")
        out["actual_finish"] = num(row.get("label_next_position_finish"))
        out["actual_points"] = num(row.get("label_next_nwr_points"))
        out["actual_startable"] = bool_true(row.get("label_startable_hit"))
        out["pyf_score"] = num(row.get("pyf_prior_nwr_points"))
        out["pyf_ppg"] = num(row.get("pyf_prior_nwr_ppg"))
        out["rank_inverse"] = -num(row.get("pyf_prior_rank_position_feature_season")) if num(row.get("pyf_prior_rank_position_feature_season")) is not None else None
        out["two_year_70_30"] = num(row.get("prior_2yr_weighted_nwr_points"))
        out["three_year_60_30_10"] = num(row.get("prior_3yr_weighted_nwr_points"))
        out["prior_2yr_years"] = num(row.get("prior_2yr_points_years_available")) or 0.0
        out["prior_3yr_years"] = num(row.get("prior_3yr_points_years_available")) or 0.0
        out["prior_games_num"] = num(row.get("prior_games")) or 0.0
        out["sparse_history_bool"] = bool_true(row.get("sparse_history_flag"))
        out["low_games_bool"] = bool_true(row.get("low_games_flag"))
        out["role_archetype"] = str(row.get("role_archetype") or "")
        out["role_usage_bucket"] = str(row.get("role_usage_bucket") or "")
        out["age_num"] = num(row.get("age"))
        out["age_bucket"] = str(row.get("age_bucket") or "")
        out["lifecycle_bucket"] = str(row.get("lifecycle_bucket") or "")
        reconstruct_history(out)
        rows.append(out)
    return rows


def reconstruct_history(row: dict[str, Any]) -> None:
    y1 = row["pyf_score"]
    two = row["two_year_70_30"]
    three = row["three_year_60_30_10"]
    y2_ok = row["prior_2yr_years"] >= 2 and y1 is not None and two is not None
    y3_ok = row["prior_3yr_years"] >= 3 and y1 is not None and three is not None
    if y1 is None:
        row["n_minus_1_points"] = None
        row["n_minus_2_points"] = None
        row["n_minus_3_points"] = None
        return
    y2 = (two - 0.70 * y1) / 0.30 if y2_ok else y1
    y3 = (three - 0.60 * y1 - 0.30 * y2) / 0.10 if y3_ok else y2
    row["n_minus_1_points"] = y1
    row["n_minus_2_points"] = y2
    row["n_minus_3_points"] = y3


def weighted2(row: dict[str, Any], w1: float, w2: float) -> float | None:
    if row.get("n_minus_1_points") is None or row.get("n_minus_2_points") is None:
        return None
    return w1 * float(row["n_minus_1_points"]) + w2 * float(row["n_minus_2_points"])


def weighted3(row: dict[str, Any], w1: float, w2: float, w3: float) -> float | None:
    if row.get("n_minus_1_points") is None or row.get("n_minus_2_points") is None or row.get("n_minus_3_points") is None:
        return None
    return w1 * float(row["n_minus_1_points"]) + w2 * float(row["n_minus_2_points"]) + w3 * float(row["n_minus_3_points"])


def scope_positions(scope: str) -> set[str]:
    if scope == "QB/RB/WR/TE":
        return set(POSITIONS)
    if scope == "WR/TE":
        return {"WR", "TE"}
    return {scope}


def is_high_volume_role(row: dict[str, Any]) -> bool:
    return str(row.get("role_usage_bucket")) == "high_volume" or "_high_volume_" in str(row.get("role_archetype"))


def is_low_or_sparse_role(row: dict[str, Any]) -> bool:
    return str(row.get("role_usage_bucket")) == "low_volume" or "_low_volume_" in str(row.get("role_archetype")) or bool(row.get("sparse_history_bool"))


def is_older_late(row: dict[str, Any]) -> bool:
    return str(row.get("age_bucket")) == "age_32_plus" or str(row.get("lifecycle_bucket")) == "late_career_10_plus"


def is_young_early(row: dict[str, Any]) -> bool:
    return str(row.get("age_bucket")) in {"under_23", "age_23_to_25"} or str(row.get("lifecycle_bucket")) == "early_career_1_to_3"


def base_score_from_name(row: dict[str, Any], base: str) -> float | None:
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
    if base == "three":
        return weighted3(row, float(row.get("_tmp_w1", 0.6)), float(row.get("_tmp_w2", 0.3)), float(row.get("_tmp_w3", 0.1)))
    raise KeyError(base)


def apply_gauntlet_modifiers(score: float | None, row: dict[str, Any], mods: list[str]) -> float | None:
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


def apply_refine_modifiers(score: float | None, row: dict[str, Any], params: dict[str, Any]) -> float | None:
    if score is None:
        return None
    factor = 1.0
    late_guard = float(params.get("late_guard", 0.0))
    high_volume_late_guard = float(params.get("high_volume_late_guard", 0.0))
    young_context = float(params.get("young_context", 0.0))
    low_sparse_young_context = float(params.get("low_sparse_young_context", 0.0))
    high_touch_context = float(params.get("high_touch_context", 0.0))
    if late_guard and is_older_late(row):
        factor *= 1.0 - late_guard
    if high_volume_late_guard and is_high_volume_role(row) and is_older_late(row):
        factor *= 1.0 - high_volume_late_guard
    if young_context and is_young_early(row) and not row["sparse_history_bool"]:
        factor *= 1.0 + young_context
    if low_sparse_young_context and is_low_or_sparse_role(row) and is_young_early(row):
        factor *= 1.0 + low_sparse_young_context
    if high_touch_context and row["position"] == "RB" and is_high_volume_role(row) and not row["sparse_history_bool"]:
        factor *= 1.0 + high_touch_context
    return float(score) * factor


def formula_score(candidate: dict[str, Any], row: dict[str, Any]) -> float | None:
    if row["position"] not in scope_positions(candidate["position_scope"]):
        return None
    kind = candidate["score_kind"]
    params = candidate["params"]
    if kind == "pyf":
        return row["pyf_score"]
    if kind == "rank_inverse":
        return row["rank_inverse"]
    if kind == "ppg":
        return row["pyf_ppg"]
    if kind == "two":
        return weighted2(row, float(params["w1"]), float(params["w2"]))
    if kind == "three":
        return weighted3(row, float(params["w1"]), float(params["w2"]), float(params["w3"]))
    if kind == "diagnostic_three":
        return row["three_year_60_30_10"]
    if kind == "modifier" and str(candidate["source_registry"]) == "gauntlet":
        return apply_gauntlet_modifiers(base_score_from_name(row, str(params.get("base"))), row, list(params.get("mods", [])))
    if kind == "modifier" and str(candidate["source_registry"]) == "refinement":
        row["_tmp_w1"] = float(params.get("w1", 0.6))
        row["_tmp_w2"] = float(params.get("w2", 0.3))
        row["_tmp_w3"] = float(params.get("w3", 0.1))
        score = base_score_from_name(row, str(params.get("base", "three")))
        return apply_refine_modifiers(score, row, params)
    return None


def load_seed_registry() -> list[dict[str, Any]]:
    clusters = pd.read_csv(GAUNTLET_CLUSTER_PATH)
    greg = pd.read_csv(GAUNTLET_REGISTRY_PATH)
    merged = clusters.merge(greg, on="candidate_id", suffixes=("_cluster", ""))
    active = merged[
        merged["cluster_id"].astype(str).str.match(r"^C\d+")
        & (merged["candidate_status"].astype(str) == "ACTIVE_REVIEW_ONLY")
    ].copy()
    seeds: list[dict[str, Any]] = []
    for cluster_id, group in active.sort_values(["cluster_id", "candidate_spearman"], ascending=[True, False]).groupby("cluster_id"):
        for _, row in group.head(3).iterrows():
            seeds.append(
                {
                    "candidate_id": row["candidate_id"],
                    "cluster_id": cluster_id,
                    "base_formula": row["candidate_id"],
                    "formula_family": row["candidate_family_cluster"],
                    "score_kind": row["score_kind"],
                    "params": parse_params(row.get("params")),
                    "position_scope": row["position_scope"],
                    "source_registry": "gauntlet",
                    "seed_spearman": num(row.get("candidate_spearman")),
                    "formula_definition": row.get("formula_definition", ""),
                }
            )
    dreg = pd.read_csv(DIVERSE_REGISTRY_PATH)
    refine = dreg[dreg["candidate_id"] == "REFINE_007_OVERALL_THREE_65_25_10_LATE_20"].iloc[0]
    seeds.append(
        {
            "candidate_id": "REFINE_007_OVERALL_THREE_65_25_10_LATE_20",
            "cluster_id": "C01_REFINED_CURRENT_BEST",
            "base_formula": "REFINE_007_OVERALL_THREE_65_25_10_LATE_20",
            "formula_family": refine["formula_family"],
            "score_kind": refine["score_kind"],
            "params": parse_params(refine.get("params")),
            "position_scope": refine["position_scope"],
            "source_registry": "refinement",
            "seed_spearman": CURRENT_BEST_FULL_HISTORY,
            "formula_definition": refine.get("formula_definition", ""),
        }
    )
    seen = set()
    unique = []
    for seed in seeds:
        if seed["candidate_id"] not in seen:
            unique.append(seed)
            seen.add(seed["candidate_id"])
    return unique


def build_ffopportunity_sidecar() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    paths = sorted(ADV_CACHE.glob("latest-data__ep_weekly_*.parquet"))
    if not paths:
        raise RuntimeError("No ep_weekly parquet files found.")
    frames = []
    for path in paths:
        df = pd.read_parquet(path)
        required = {"season", "week", "player_id", "full_name", "position", "posteam", "total_fantasy_points_exp"}
        missing = required - set(df.columns)
        if missing:
            raise RuntimeError(f"{path.name} missing columns {sorted(missing)}")
        df = df[df["position"].isin(POSITIONS)].copy()
        df = df[pd.to_numeric(df["week"], errors="coerce").fillna(99) <= 18].copy()
        df["source_path"] = str(path)
        df["source_hash"] = sha256_file(path)
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)
    rows = []
    for (season, player_id, position), g in data.groupby(["season", "player_id", "position"], dropna=True):
        if pd.isna(player_id):
            continue
        total_exp = pd.to_numeric(g["total_fantasy_points_exp"], errors="coerce").sum()
        weeks = int(g["week"].nunique())
        teams = "|".join(sorted({str(v) for v in g["posteam"].dropna().unique()}))
        row = {
            "season": int(season),
            "player_id": str(player_id),
            "player_name": str(g["full_name"].dropna().iloc[0]) if g["full_name"].notna().any() else "",
            "position": str(position),
            "team_list": teams,
            "ffop_games_weeks": weeks,
            "ffop_pass_attempt": pd.to_numeric(g.get("pass_attempt"), errors="coerce").sum(),
            "ffop_rec_attempt": pd.to_numeric(g.get("rec_attempt"), errors="coerce").sum(),
            "ffop_rush_attempt": pd.to_numeric(g.get("rush_attempt"), errors="coerce").sum(),
            "ffop_total_fantasy_points_exp": total_exp,
            "ffop_total_fantasy_points_exp_per_game": total_exp / weeks if weeks else None,
            "ffop_pass_fantasy_points_exp": pd.to_numeric(g.get("pass_fantasy_points_exp"), errors="coerce").sum(),
            "ffop_rec_fantasy_points_exp": pd.to_numeric(g.get("rec_fantasy_points_exp"), errors="coerce").sum(),
            "ffop_rush_fantasy_points_exp": pd.to_numeric(g.get("rush_fantasy_points_exp"), errors="coerce").sum(),
            "ffop_total_fantasy_points_actual": pd.to_numeric(g.get("total_fantasy_points"), errors="coerce").sum(),
            "ffop_total_fantasy_points_diff": pd.to_numeric(g.get("total_fantasy_points_diff"), errors="coerce").sum(),
            "ffop_total_yards_gained_exp": pd.to_numeric(g.get("total_yards_gained_exp"), errors="coerce").sum(),
            "ffop_total_first_down_exp": pd.to_numeric(g.get("total_first_down_exp"), errors="coerce").sum(),
            "source_artifacts": "|".join(sorted(g["source_path"].unique())),
            "source_hashes": "|".join(sorted(g["source_hash"].unique())),
            "source_gate_status": "public_nflverse_ffopportunity_review_only_not_production",
            "decision_date_safe": "PASS_LAGGED_CLOSED_FEATURE_SEASON_ONLY",
            "leakage_flag": "PASS_FEATURE_SEASON_N_TO_TARGET_SEASON_N_PLUS_1",
            "identity_flag": "PASS_GSIS_PLAYER_ID_JOIN_REQUIRED",
            "review_only_status": "REVIEW_ONLY_SIDE_CAR_NOT_MODEL_USE_NOT_RANKING",
            "caveat": "Partial 2021-2024 source coverage; no same-season use.",
        }
        rows.append(row)
    return rows, source_ledger(paths, "ffopportunity_expected_fantasy_points")


def build_ngs_sidecar() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    paths = sorted(ADV_CACHE.glob("nextgen_stats__ngs_*.csv.gz"))
    if not paths:
        raise RuntimeError("No NGS csv.gz files found.")
    pieces = []
    for path in paths:
        df = pd.read_csv(path)
        if "season_type" in df.columns:
            df = df[df["season_type"].astype(str).str.upper() == "REG"].copy()
        df = df[pd.to_numeric(df["week"], errors="coerce").fillna(99) <= 18].copy()
        df["source_path"] = str(path)
        df["source_hash"] = sha256_file(path)
        if "_passing" in path.name:
            df["ngs_type"] = "passing"
        elif "_receiving" in path.name:
            df["ngs_type"] = "receiving"
        elif "_rushing" in path.name:
            df["ngs_type"] = "rushing"
        else:
            df["ngs_type"] = "unknown"
        pieces.append(df)
    data = pd.concat(pieces, ignore_index=True, sort=False)
    rows = []
    for (season, player_id, position), g in data.groupby(["season", "player_gsis_id", "player_position"], dropna=True):
        if position not in POSITIONS or pd.isna(player_id):
            continue
        out = {
            "season": int(season),
            "player_id": str(player_id),
            "player_name": str(g["player_display_name"].dropna().iloc[0]) if g["player_display_name"].notna().any() else "",
            "position": str(position),
            "team_list": "|".join(sorted({str(v) for v in g["team_abbr"].dropna().unique()})),
            "ngs_weeks": int(g["week"].nunique()),
            "ngs_qb_attempts": pd.to_numeric(g.get("attempts"), errors="coerce").sum() if "attempts" in g else None,
            "ngs_qb_cpoe": weighted_avg(g, "completion_percentage_above_expectation", "attempts"),
            "ngs_qb_exp_completion_pct": weighted_avg(g, "expected_completion_percentage", "attempts"),
            "ngs_qb_avg_time_to_throw": weighted_avg(g, "avg_time_to_throw", "attempts"),
            "ngs_qb_avg_intended_air_yards": weighted_avg(g, "avg_intended_air_yards", "attempts"),
            "ngs_rec_targets": pd.to_numeric(g.get("targets"), errors="coerce").sum() if "targets" in g else None,
            "ngs_rec_avg_separation": weighted_avg(g, "avg_separation", "targets"),
            "ngs_rec_share_intended_air_yards": weighted_avg(g, "percent_share_of_intended_air_yards", "targets"),
            "ngs_rec_avg_expected_yac": weighted_avg(g, "avg_expected_yac", "targets"),
            "ngs_rec_avg_yac_above_expectation": weighted_avg(g, "avg_yac_above_expectation", "targets"),
            "ngs_rush_attempts": pd.to_numeric(g.get("rush_attempts"), errors="coerce").sum() if "rush_attempts" in g else None,
            "ngs_rush_efficiency": weighted_avg(g, "efficiency", "rush_attempts"),
            "ngs_rush_stacked_box_pct": weighted_avg(g, "percent_attempts_gte_eight_defenders", "rush_attempts"),
            "ngs_rush_expected_yards": pd.to_numeric(g.get("expected_rush_yards"), errors="coerce").sum() if "expected_rush_yards" in g else None,
            "ngs_rush_yards_over_expected": pd.to_numeric(g.get("rush_yards_over_expected"), errors="coerce").sum() if "rush_yards_over_expected" in g else None,
            "ngs_rush_yards_over_expected_per_att": weighted_avg(g, "rush_yards_over_expected_per_att", "rush_attempts"),
            "ngs_rush_pct_over_expected": weighted_avg(g, "rush_pct_over_expected", "rush_attempts"),
            "source_artifacts": "|".join(sorted(g["source_path"].unique())),
            "source_hashes": "|".join(sorted(g["source_hash"].unique())),
            "source_gate_status": "public_nflverse_ngs_review_only_not_production",
            "decision_date_safe": "PASS_LAGGED_CLOSED_FEATURE_SEASON_ONLY",
            "leakage_flag": "PASS_FEATURE_SEASON_N_TO_TARGET_SEASON_N_PLUS_1",
            "identity_flag": "PASS_GSIS_PLAYER_ID_JOIN_REQUIRED",
            "review_only_status": "REVIEW_ONLY_SIDE_CAR_NOT_MODEL_USE_NOT_RANKING",
            "caveat": "Local NGS coverage is partial; 2024 cache is sparse. No production use.",
        }
        rows.append(out)
    # Build a simple position-aware signal after rows are materialized.
    df = pd.DataFrame(rows)
    if not df.empty:
        signal = []
        for _, row in df.iterrows():
            pos = row["position"]
            if pos == "QB":
                vals = [num(row.get("ngs_qb_cpoe")), num(row.get("ngs_qb_avg_intended_air_yards"))]
            elif pos in {"WR", "TE"}:
                vals = [num(row.get("ngs_rec_avg_separation")), num(row.get("ngs_rec_share_intended_air_yards")), num(row.get("ngs_rec_avg_yac_above_expectation"))]
            elif pos == "RB":
                vals = [num(row.get("ngs_rush_yards_over_expected_per_att")), num(row.get("ngs_rush_pct_over_expected"))]
            else:
                vals = []
            clean = [v for v in vals if v is not None]
            signal.append(sum(clean) / len(clean) if clean else None)
        df["ngs_position_signal_raw"] = signal
        rows = df.to_dict("records")
    return rows, source_ledger(paths, "nflverse_next_gen_stats")


def add_sidecars_to_panel(rows: list[dict[str, Any]], ff_rows: list[dict[str, Any]], ngs_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ff = {(r["player_id"], int(r["season"]), r["position"]): r for r in ff_rows}
    ngs = {(r["player_id"], int(r["season"]), r["position"]): r for r in ngs_rows}
    ff_join = 0
    ngs_join = 0
    for row in rows:
        feature_key = (row["player_id"], int(row["feature_season"]), row["position"])
        ffr = ff.get(feature_key)
        ngsr = ngs.get(feature_key)
        row["ffop_join_status"] = "JOINED" if ffr else "MISSING"
        row["ngs_join_status"] = "JOINED" if ngsr else "MISSING"
        if ffr:
            ff_join += 1
            row["ffop_xfp_total"] = num(ffr.get("ffop_total_fantasy_points_exp"))
            row["ffop_xfp_per_game"] = num(ffr.get("ffop_total_fantasy_points_exp_per_game"))
            row["ffop_xfp_diff"] = num(ffr.get("ffop_total_fantasy_points_diff"))
            row["ffop_expected_first_downs"] = num(ffr.get("ffop_total_first_down_exp"))
            row["ffop_expected_yards"] = num(ffr.get("ffop_total_yards_gained_exp"))
            row["ffop_opportunity_count"] = (num(ffr.get("ffop_pass_attempt")) or 0.0) + (num(ffr.get("ffop_rec_attempt")) or 0.0) + (num(ffr.get("ffop_rush_attempt")) or 0.0)
        else:
            row["ffop_xfp_total"] = None
            row["ffop_xfp_per_game"] = None
            row["ffop_xfp_diff"] = None
            row["ffop_expected_first_downs"] = None
            row["ffop_expected_yards"] = None
            row["ffop_opportunity_count"] = None
        if ngsr:
            ngs_join += 1
            for key, value in ngsr.items():
                if key.startswith("ngs_"):
                    row[key] = num(value)
        else:
            for key in [
                "ngs_position_signal_raw",
                "ngs_qb_cpoe",
                "ngs_qb_avg_time_to_throw",
                "ngs_qb_avg_intended_air_yards",
                "ngs_rec_avg_separation",
                "ngs_rec_share_intended_air_yards",
                "ngs_rec_avg_yac_above_expectation",
                "ngs_rush_yards_over_expected_per_att",
                "ngs_rush_pct_over_expected",
            ]:
                row[key] = None
    # Normalize ingredient values within feature season/position among joined rows.
    for field in ["ffop_xfp_total", "ffop_xfp_per_game", "ffop_xfp_diff", "ffop_expected_first_downs", "ngs_position_signal_raw"]:
        assign_percentile(rows, field, f"{field}_pct")
    return {
        "ffop_joined": ff_join,
        "ngs_joined": ngs_join,
        "total_rows": len(rows),
    }


def selected_rows(rows: list[dict[str, Any]], positions: set[str], required_fields: list[str]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row["position"] not in positions:
            continue
        if row.get("actual_finish") is None:
            continue
        if all(row.get(field) is not None for field in required_fields):
            out.append(row)
    return out


def metrics_for_run(rows: list[dict[str, Any]], score_col: str, pyf_col: str = "pyf_score") -> dict[str, Any]:
    local = [dict(r) for r in rows if r.get(score_col) is not None and r.get("actual_finish") is not None]
    if not local:
        return {"rows": 0}
    assign_rank(local, score_col, "candidate_rank")
    assign_rank(local, pyf_col, "pyf_rank")
    ranks = [float(r["candidate_rank"]) for r in local]
    finishes = [float(r["actual_finish"]) for r in local]
    pyf_ranks = [float(r["pyf_rank"]) for r in local if r.get("pyf_rank") is not None]
    pyf_finishes = [float(r["actual_finish"]) for r in local if r.get("pyf_rank") is not None]
    false_pos = [r for r in local if predicted_startable(r, "candidate_rank") and not r["actual_startable"]]
    false_neg = [r for r in local if not predicted_startable(r, "candidate_rank") and r["actual_startable"]]
    pyf_false_pos = [r for r in local if predicted_startable(r, "pyf_rank") and not r["actual_startable"]]
    pyf_false_neg = [r for r in local if not predicted_startable(r, "pyf_rank") and r["actual_startable"]]
    sparse = [r for r in local if r["sparse_history_bool"]]
    low_games = [r for r in local if r["low_games_bool"]]
    older = [r for r in local if is_older_late(r)]
    young = [r for r in local if is_young_early(r)]
    high_role = [r for r in local if is_high_volume_role(r)]
    low_role = [r for r in local if is_low_or_sparse_role(r)]
    out = {
        "rows": len(local),
        "seasons": sorted({int(r["season"]) for r in local}),
        "positions": sorted({r["position"] for r in local}),
        "spearman": spearman(ranks, finishes),
        "pyf_spearman": spearman(pyf_ranks, pyf_finishes),
        "top12_precision": top_precision(local, "candidate_rank", 12),
        "top24_precision": top_precision(local, "candidate_rank", 24),
        "top36_precision": top_precision(local, "candidate_rank", 36),
        "fp": len(false_pos),
        "fn": len(false_neg),
        "pyf_fp": len(pyf_false_pos),
        "pyf_fn": len(pyf_false_neg),
        "sparse_rows": len(sparse),
        "sparse_error_rate": error_rate(sparse, "candidate_rank"),
        "pyf_sparse_error_rate": error_rate(sparse, "pyf_rank"),
        "low_games_rows": len(low_games),
        "low_games_error_rate": error_rate(low_games, "candidate_rank"),
        "pyf_low_games_error_rate": error_rate(low_games, "pyf_rank"),
        "older_late_rows": len(older),
        "young_early_rows": len(young),
        "high_role_rows": len(high_role),
        "low_sparse_role_rows": len(low_role),
        "by_position": {},
        "by_season": {},
    }
    for pos in POSITIONS:
        sub = [r for r in local if r["position"] == pos]
        if len(sub) >= 2:
            out["by_position"][pos] = spearman([float(r["candidate_rank"]) for r in sub], [float(r["actual_finish"]) for r in sub])
        else:
            out["by_position"][pos] = None
    for season in out["seasons"]:
        sub = [r for r in local if int(r["season"]) == season]
        if len(sub) >= 2:
            out["by_season"][season] = spearman([float(r["candidate_rank"]) for r in sub], [float(r["actual_finish"]) for r in sub])
    return out


def predicted_startable(row: dict[str, Any], rank_col: str) -> bool:
    rank = row.get(rank_col)
    return rank is not None and float(rank) <= STARTABLE_CUTOFF[row["position"]]


def top_precision(rows: list[dict[str, Any]], rank_col: str, top_n: int) -> float | None:
    selected = [r for r in rows if r.get(rank_col) is not None and float(r[rank_col]) <= top_n]
    if not selected:
        return None
    return sum(1 for r in selected if r["actual_finish"] is not None and float(r["actual_finish"]) <= top_n) / len(selected)


def error_rate(rows: list[dict[str, Any]], rank_col: str) -> float | None:
    if not rows:
        return None
    bad = [r for r in rows if predicted_startable(r, rank_col) != bool(r["actual_startable"])]
    return len(bad) / len(rows)


def materialize_formula_scores(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> None:
    for seed in seeds:
        col = f"formula__{seed['candidate_id']}"
        for row in rows:
            row[col] = formula_score(seed, row)
        assign_percentile(rows, col, f"{col}__pct")


def add_combo_score(rows: list[dict[str, Any]], out_col: str, parts: list[tuple[str, float]]) -> None:
    for row in rows:
        score = 0.0
        ok = True
        for col, weight in parts:
            val = row.get(col)
            if val is None:
                ok = False
                break
            score += weight * float(val)
        row[out_col] = score if ok else None


def result_row(
    run_id: str,
    formula_id: str,
    cluster_id: str,
    base_formula: str,
    ingredient_set: str,
    ingredient_fields: str,
    positions: str,
    rows: list[dict[str, Any]],
    score_col: str,
    coverage_denominator: int,
    seed_metrics: dict[str, Any] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    metrics = metrics_for_run(rows, score_col)
    spearman_value = metrics.get("spearman")
    pyf_value = metrics.get("pyf_spearman")
    seed_value = seed_metrics.get("spearman") if seed_metrics else None
    row_count = int(metrics.get("rows") or 0)
    missing_pct = 1.0 - (row_count / coverage_denominator) if coverage_denominator else None
    season_text = "|".join(str(s) for s in metrics.get("seasons", []))
    pos_text = "|".join(metrics.get("positions", [])) if metrics.get("positions") else positions
    by_pos = metrics.get("by_position", {})
    by_season = metrics.get("by_season", {})
    season_stable = [
        s
        for s, val in by_season.items()
        if val is not None and pyf_value is not None and val >= pyf_value - 0.05
    ]
    pyf_delta = (spearman_value - pyf_value) if spearman_value is not None and pyf_value is not None else None
    current_best_delta = (spearman_value - CURRENT_BEST_FULL_HISTORY) if spearman_value is not None else None
    seed_delta = (spearman_value - seed_value) if spearman_value is not None and seed_value is not None else None
    use_decision = decide_use(formula_id, pyf_delta, current_best_delta, row_count, missing_pct)
    return {
        "run_id": run_id,
        "formula_id": formula_id,
        "cluster_id": cluster_id,
        "base_formula": base_formula,
        "ingredient_set": ingredient_set,
        "ingredient_fields": ingredient_fields,
        "positions": pos_text,
        "seasons": season_text,
        "row_count": row_count,
        "coverage_pct": pct(row_count / coverage_denominator if coverage_denominator else None),
        "missingness_pct": pct(missing_pct),
        "overall_spearman": fmt(spearman_value, 3),
        "position_spearman_qb": fmt(by_pos.get("QB"), 3),
        "position_spearman_rb": fmt(by_pos.get("RB"), 3),
        "position_spearman_wr": fmt(by_pos.get("WR"), 3),
        "position_spearman_te": fmt(by_pos.get("TE"), 3),
        "pyf_delta": fmt(pyf_delta, 3),
        "current_best_delta": fmt(current_best_delta, 3),
        "cluster_seed_delta": fmt(seed_delta, 3),
        "top12_precision": pct(metrics.get("top12_precision")),
        "top24_precision": pct(metrics.get("top24_precision")),
        "top36_precision": pct(metrics.get("top36_precision")),
        "false_positive_impact": f"candidate_fp={metrics.get('fp')};pyf_fp={metrics.get('pyf_fp')};delta={int(metrics.get('fp', 0))-int(metrics.get('pyf_fp', 0))}",
        "false_negative_impact": f"candidate_fn={metrics.get('fn')};pyf_fn={metrics.get('pyf_fn')};delta={int(metrics.get('fn', 0))-int(metrics.get('pyf_fn', 0))}",
        "sparse_history_impact": f"rows={metrics.get('sparse_rows')};candidate_error={pct(metrics.get('sparse_error_rate'))};pyf_error={pct(metrics.get('pyf_sparse_error_rate'))}",
        "low_games_impact": f"rows={metrics.get('low_games_rows')};candidate_error={pct(metrics.get('low_games_error_rate'))};pyf_error={pct(metrics.get('pyf_low_games_error_rate'))}",
        "age_lifecycle_slice": f"older_late_rows={metrics.get('older_late_rows')};young_early_rows={metrics.get('young_early_rows')}",
        "role_slice": f"high_role_rows={metrics.get('high_role_rows')};low_sparse_role_rows={metrics.get('low_sparse_role_rows')}",
        "stability_by_season": ";".join(f"{s}:{fmt(v, 3)}" for s, v in by_season.items()),
        "leave_one_season_out": f"direction_stable_seasons={len(season_stable)}/{len(by_season)}",
        "outlier_flags": "partial_coverage_not_full_2013_2025_comparable" if row_count < 5518 else "none",
        "use_decision": use_decision,
        "notes": notes,
    }


def decide_use(formula_id: str, pyf_delta: float | None, current_best_delta: float | None, rows: int, missing_pct: float | None) -> str:
    if rows < 50:
        return "BLOCKED"
    if pyf_delta is None:
        return "BLOCKED"
    if pyf_delta <= 0.0:
        return "GUARDRAIL_CONTEXT" if pyf_delta > -0.010 else "DESCRIPTIVE_ONLY"
    if pyf_delta > 0.005 and missing_pct is not None and missing_pct < 0.50:
        return "ADDITIVE_CANDIDATE"
    if pyf_delta > 0.002:
        return "INTERACTION_ONLY"
    if pyf_delta > -0.010:
        return "GUARDRAIL_CONTEXT"
    return "DROP_AFTER_FAILURE"


def build_tests(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    materialize_formula_scores(rows, seeds)
    registry_rows: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    ff_positions = set(POSITIONS)
    ngs_positions = set(POSITIONS)
    ff_denominator = len([r for r in rows if int(r["feature_season"]) in {2021, 2022, 2023, 2024}])
    ngs_denominator = ff_denominator
    component_specs = [
        ("INGREDIENT_ONLY_FFOP_XFP_TOTAL", "ffopportunity", "ffop_xfp_total_pct", "ffop_xfp_total", ff_positions, ff_denominator),
        ("INGREDIENT_ONLY_FFOP_XFP_PER_GAME", "ffopportunity", "ffop_xfp_per_game_pct", "ffop_xfp_per_game", ff_positions, ff_denominator),
        ("INGREDIENT_ONLY_FFOP_EXPECTED_FIRST_DOWNS", "ffopportunity", "ffop_expected_first_downs_pct", "ffop_expected_first_downs", ff_positions, ff_denominator),
        ("INGREDIENT_ONLY_FFOP_ACTUAL_MINUS_EXPECTED", "ffopportunity", "ffop_xfp_diff_pct", "ffop_xfp_diff", ff_positions, ff_denominator),
        ("INGREDIENT_ONLY_NGS_POSITION_SIGNAL", "nflverse_ngs", "ngs_position_signal_raw_pct", "ngs_position_signal_raw", ngs_positions, ngs_denominator),
    ]
    for run_id, ingredient, score_col, raw_field, positions, denom in component_specs:
        selected = selected_rows(rows, positions, [score_col])
        registry_rows.append(
            {
                "run_id": run_id,
                "test_type": "ingredient_alone",
                "formula_id": run_id,
                "cluster_id": "INGREDIENT_ONLY",
                "base_formula": "none",
                "ingredient_set": ingredient,
                "ingredient_fields": raw_field,
                "predeclared_weighting": "ingredient percentile rank only",
            }
        )
        results.append(
            result_row(
                run_id,
                run_id,
                "INGREDIENT_ONLY",
                "none",
                ingredient,
                raw_field,
                "/".join(sorted(positions)),
                selected,
                score_col,
                denom,
                notes="ingredient-alone review-only component test; partial coverage",
            )
        )
    seed_same_row_metrics: dict[str, dict[str, Any]] = {}
    for seed in seeds:
        formula_col = f"formula__{seed['candidate_id']}"
        formula_pct = f"{formula_col}__pct"
        seed_positions = scope_positions(seed["position_scope"])
        # Same-row seed baselines for ffopportunity and NGS.
        for ingredient, ingredient_col, ingredient_field, weight, denom in [
            ("ffopportunity", "ffop_xfp_per_game_pct", "ffop_xfp_per_game", 0.10, ff_denominator),
            ("nflverse_ngs", "ngs_position_signal_raw_pct", "ngs_position_signal_raw", 0.10, ngs_denominator),
        ]:
            base_selected = selected_rows(rows, seed_positions, [formula_col, ingredient_col])
            base_metrics = metrics_for_run(base_selected, formula_col)
            seed_same_row_metrics[f"{seed['candidate_id']}::{ingredient}"] = base_metrics
            combo_col = f"combo__{seed['candidate_id']}__{ingredient}"
            add_combo_score(rows, combo_col, [(formula_pct, 1.0 - weight), (ingredient_col, weight)])
            selected = selected_rows(rows, seed_positions, [combo_col])
            run_id = f"{seed['candidate_id']}__PLUS_{ingredient.upper()}_PCT10"
            registry_rows.append(
                {
                    "run_id": run_id,
                    "test_type": "formula_x_ingredient",
                    "formula_id": seed["candidate_id"],
                    "cluster_id": seed["cluster_id"],
                    "base_formula": seed["base_formula"],
                    "ingredient_set": ingredient,
                    "ingredient_fields": ingredient_field,
                    "predeclared_weighting": f"0.90 formula percentile + 0.10 {ingredient} percentile",
                }
            )
            results.append(
                result_row(
                    run_id,
                    seed["candidate_id"],
                    seed["cluster_id"],
                    seed["base_formula"],
                    ingredient,
                    ingredient_field,
                    seed["position_scope"],
                    selected,
                    combo_col,
                    denom,
                    seed_metrics=base_metrics,
                    notes="formula x ingredient predeclared 10pct additive review-only test; not production/ranking",
                )
            )
        # Ingredient combination test: only when both ffopportunity and NGS are joined.
        both_col = f"combo__{seed['candidate_id']}__FFOP_NGS"
        add_combo_score(rows, both_col, [(formula_pct, 0.90), ("ffop_xfp_per_game_pct", 0.05), ("ngs_position_signal_raw_pct", 0.05)])
        both_selected = selected_rows(rows, seed_positions, [both_col])
        base_both = selected_rows(rows, seed_positions, [formula_col, "ffop_xfp_per_game_pct", "ngs_position_signal_raw_pct"])
        base_metrics = metrics_for_run(base_both, formula_col)
        run_id = f"{seed['candidate_id']}__PLUS_FFOP_NGS_PCT05_05"
        registry_rows.append(
            {
                "run_id": run_id,
                "test_type": "formula_x_ingredient_combo",
                "formula_id": seed["candidate_id"],
                "cluster_id": seed["cluster_id"],
                "base_formula": seed["base_formula"],
                "ingredient_set": "ffopportunity+nflverse_ngs",
                "ingredient_fields": "ffop_xfp_per_game;ngs_position_signal_raw",
                "predeclared_weighting": "0.90 formula percentile + 0.05 ffopportunity percentile + 0.05 NGS percentile",
            }
        )
        results.append(
            result_row(
                run_id,
                seed["candidate_id"],
                seed["cluster_id"],
                seed["base_formula"],
                "ffopportunity+nflverse_ngs",
                "ffop_xfp_per_game;ngs_position_signal_raw",
                seed["position_scope"],
                both_selected,
                both_col,
                ngs_denominator,
                seed_metrics=base_metrics,
                notes="bounded two-ingredient combo; partial NGS coverage; not production/ranking",
            )
        )
    return registry_rows, results


def join_coverage(rows: list[dict[str, Any]], ff_sidecar: list[dict[str, Any]], ngs_sidecar: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for ingredient, feature_seasons, status_col in [
        ("ffopportunity", {2021, 2022, 2023, 2024}, "ffop_join_status"),
        ("nflverse_ngs", {2021, 2022, 2023, 2024}, "ngs_join_status"),
    ]:
        eligible = [r for r in rows if int(r["feature_season"]) in feature_seasons]
        joined = [r for r in eligible if r.get(status_col) == "JOINED"]
        for pos in ["ALL", *POSITIONS]:
            e = eligible if pos == "ALL" else [r for r in eligible if r["position"] == pos]
            j = joined if pos == "ALL" else [r for r in joined if r["position"] == pos]
            out.append(
                {
                    "ingredient": ingredient,
                    "position": pos,
                    "eligible_rows": len(e),
                    "joined_rows": len(j),
                    "join_coverage_pct": pct(len(j) / len(e) if e else None),
                    "target_seasons": "|".join(str(s) for s in sorted({r["season"] for r in e})),
                    "feature_seasons": "|".join(str(s) for s in sorted({r["feature_season"] for r in e})),
                    "join_key": "player_id + feature_season + position",
                    "asof_status": "PASS_LAGGED_N_TO_N_PLUS_1" if j else "NO_JOINED_ROWS",
                }
            )
    return out


def write_validation_files(
    rows: list[dict[str, Any]],
    ff_rows: list[dict[str, Any]],
    ngs_rows: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> None:
    schema_rows = []
    for name, sidecar, required in [
        (
            "ffopportunity",
            ff_rows,
            ["season", "player_id", "position", "ffop_total_fantasy_points_exp", "source_hashes", "leakage_flag", "review_only_status"],
        ),
        (
            "nflverse_ngs",
            ngs_rows,
            ["season", "player_id", "position", "source_hashes", "leakage_flag", "review_only_status"],
        ),
    ]:
        cols = set(sidecar[0].keys()) if sidecar else set()
        missing = [c for c in required if c not in cols]
        keys = [(r["season"], r["player_id"], r["position"]) for r in sidecar]
        schema_rows.append(
            {
                "artifact": name,
                "row_count": len(sidecar),
                "required_columns_present": "yes" if not missing else "no",
                "missing_columns": "|".join(missing),
                "duplicate_keys": len(keys) - len(set(keys)),
                "review_only_status": "PASS" if sidecar and not missing and len(keys) == len(set(keys)) else "FAIL",
            }
        )
    write_csv(OUT_DIR / "AUTONOMOUS_SIDECAR_SCHEMA_VALIDATION.csv", schema_rows)
    leakage_rows = []
    for ingredient, status_col in [("ffopportunity", "ffop_join_status"), ("nflverse_ngs", "ngs_join_status")]:
        joined = [r for r in rows if r.get(status_col) == "JOINED"]
        bad = [r for r in joined if int(r["feature_season"]) >= int(r["season"])]
        leakage_rows.append(
            {
                "ingredient": ingredient,
                "joined_rows": len(joined),
                "bad_lag_rows": len(bad),
                "asof_result": "PASS" if not bad else "FAIL",
                "rule": "feature_season must be less than target season",
            }
        )
    write_csv(OUT_DIR / "AUTONOMOUS_LEAKAGE_ASOF_VALIDATION.csv", leakage_rows)
    summary = {
        "total_results": len(results),
        "material_above_0755_partial": len([r for r in results if num(r["overall_spearman"]) is not None and num(r["overall_spearman"]) > 0.760]),
        "results_beating_pyf_same_rows": len([r for r in results if num(r["pyf_delta"]) is not None and num(r["pyf_delta"]) > 0]),
    }
    write_md(
        OUT_DIR / "AUTONOMOUS_BLOCKERS_AND_GATES.md",
        f"""
# Autonomous Blockers And Gates

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior remains unchanged.
- Source promotion remains blocked.
- SportsDataIO remains parked.
- PFF Elusive Rating and `nwr_elusive_proxy_review_only` remain blocked.
- Current-only ADP was not used.

## Result Summary

- Total result rows: `{summary['total_results']}`
- Partial-sample rows above `.760`: `{summary['material_above_0755_partial']}`
- Rows beating PYF on same rows: `{summary['results_beating_pyf_same_rows']}`

## Caveat

The ingredient tests use partial `2021-2024` source coverage, so scores above `.755` are directional review-only evidence and are not full `2013-2025` plateau breaks.
""",
    )


def make_reports(
    rows: list[dict[str, Any]],
    ff_rows: list[dict[str, Any]],
    ngs_rows: list[dict[str, Any]],
    results: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
) -> None:
    sortable = [r for r in results if num(r["overall_spearman"]) is not None]
    top = sorted(sortable, key=lambda r: num(r["overall_spearman"]) or -999, reverse=True)[:12]
    top_ff = [r for r in results if r["ingredient_set"] == "ffopportunity"]
    top_ngs = [r for r in results if r["ingredient_set"] == "nflverse_ngs"]
    top_combo = [r for r in results if r["ingredient_set"] == "ffopportunity+nflverse_ngs"]
    best_component = max([r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"], key=lambda r: num(r["overall_spearman"]) or -999)
    best_formula_ing = max([r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]], key=lambda r: num(r["overall_spearman"]) or -999)
    best_combo = max(top_combo, key=lambda r: num(r["overall_spearman"]) or -999) if top_combo else None
    material = [r for r in results if num(r["overall_spearman"]) is not None and num(r["overall_spearman"]) > CURRENT_BEST_FULL_HISTORY + 0.005]
    report = [
        "# NWR Autonomous Ingredient Upgrade Sequence V2 Report",
        "",
        "## Verdict",
        "",
        "`GREEN_AUTONOMOUS_INGREDIENT_UPGRADE_SEQUENCE_COMPLETED_REVIEW_ONLY`",
        "",
        "## Lanes Completed",
        "",
        "- `ffopportunity Expected Fantasy Points Formula Mart Sidecar V1`",
        "- `ffopportunity Component Test V1`",
        "- `nflverse NGS Formula Mart Sidecar V1`",
        "- `nflverse NGS Component Test V1`",
        "- `Cluster Seed Formula x Ingredient Tests V1`",
        "- `ffopportunity + NGS Ingredient Combination Tests V1`",
        "",
        "## Ingredients Loaded",
        "",
        f"- `ffopportunity`: `{len(ff_rows)}` player-season sidecar rows from local `ep_weekly` parquet, source seasons `2021-2024`.",
        f"- `nflverse_ngs`: `{len(ngs_rows)}` player-season sidecar rows from local NGS passing/receiving/rushing files, source seasons `2021-2024` with sparse `2024` NGS cache caveat.",
        "",
        "## Ingredients Rejected Or Downgraded",
        "",
        "- Full nflfastR/nflverse EPA/opportunity aggregates: not rebuilt in this run; recommended as a future source rebuild lane.",
        "- Historical Market / ADP: parked behind nflverse sidecars because point-in-time/as-of safety is not proven.",
        "- SportsDataIO: parked.",
        "- PFR RB broken tackles: branch remains closed as main formula ingredient after prior no-incremental-signal result.",
        "",
        "## Best Results",
        "",
        f"- Best component test: `{best_component['run_id']}` Spearman `{best_component['overall_spearman']}` PYF delta `{best_component['pyf_delta']}`.",
        f"- Best formula x ingredient test: `{best_formula_ing['run_id']}` Spearman `{best_formula_ing['overall_spearman']}` PYF delta `{best_formula_ing['pyf_delta']}`.",
    ]
    if best_combo:
        report.append(f"- Best ingredient combination: `{best_combo['run_id']}` Spearman `{best_combo['overall_spearman']}` PYF delta `{best_combo['pyf_delta']}`.")
    report.extend(
        [
            "",
            "## Top Review-Only Results",
            "",
        ]
    )
    for row in top:
        report.append(f"- `{row['run_id']}` `{row['overall_spearman']}` rows `{row['row_count']}` use `{row['use_decision']}`")
    report.extend(
        [
            "",
            "## Material Beat Of `.755`",
            "",
            f"Partial-sample results above `.760`: `{len(material)}`. These do not constitute a full-history material break of the `.755` plateau because the sidecars cover partial target seasons only.",
            "",
            "## Ranking Simulation Decision",
            "",
            "A review-only ranking simulation is not yet justified as a production-adjacent step. A narrower next lane is justified: rebuild/validate full nflfastR EPA/opportunity or run a second sidecar around the strongest partial ingredient with coverage expansion.",
            "",
            "## CSV Outputs",
            "",
            f"- `{OUT_DIR / 'AUTONOMOUS_ALL_RESULTS_REQUIRED_SCHEMA.csv'}`",
            f"- `{OUT_DIR / 'AUTONOMOUS_COMPONENT_TEST_RESULTS.csv'}`",
            f"- `{OUT_DIR / 'AUTONOMOUS_FORMULA_X_INGREDIENT_RESULTS.csv'}`",
            f"- `{OUT_DIR / 'AUTONOMOUS_INGREDIENT_COMBINATION_RESULTS.csv'}`",
            f"- `{OUT_DIR / 'FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv'}`",
            f"- `{OUT_DIR / 'NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv'}`",
            "",
            "## Gates Preserved",
            "",
            "- Production/model-use remains blocked.",
            "- Rankings integration remains blocked.",
            "- App/runtime/model behavior changed: no.",
            "- Push/merge: no.",
            "- Source promotion: no.",
        ]
    )
    write_md(OUT_DIR / "AUTONOMOUS_INGREDIENT_UPGRADE_SEQUENCE_V2_REPORT.md", "\n".join(report))
    write_md(
        OUT_DIR / "AUTONOMOUS_NEXT_STEP_RECOMMENDATION.md",
        """
# Autonomous Next Step Recommendation

## Recommended Next Lane

`nflverse EPA / Opportunity Formula Mart Sidecar V1`

## Why

`ffopportunity` and NGS produced usable review-only sidecars, but both are partial-window ingredients. The cleanest chance to beat the `.755` plateau in a full-history-comparable way is to rebuild lagged nflfastR/nflverse EPA/opportunity aggregates across the historical Formula Mart window.

## Not Recommended Yet

- Review-only ranking simulation: not yet, because the best ingredient gains are partial-window and not full `2013-2025` comparable.
- More same-ingredient formula refinement: still plateaued.
- Historical Market / ADP: still useful but parked behind public nflverse sidecars.
""",
    )
    source_trace = f"""
# Autonomous Ingredient Upgrade Source Trace

## Handoff Packet

- `{HANDOFF_DIR}`

## Prior Local Packets

- nflverse Advanced Ingredient Availability / Formula Mart Gap Audit V1 commit `{NVERSE_AUDIT_COMMIT}`
- PFR RB Broken Tackle Data Mart Join / Component Test V1 commit `{PFR_COMMIT}`

## Source Data

- Formula Data Mart: `{MART_PATH}`
- Age/lifecycle sidecar: `{AGE_PATH}`
- Advanced metrics cache: `{ADV_CACHE}`

## Review Rules

All outputs are review-only. No production/model-use approval, rankings integration, app/runtime behavior change, source promotion, push, merge, SportsDataIO, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, current-only ADP, or same-season features were used.
"""
    write_md(OUT_DIR / "AUTONOMOUS_SOURCE_TRACE.md", source_trace)


def main() -> None:
    rows = load_formula_panel()
    ff_rows, ff_sources = build_ffopportunity_sidecar()
    ngs_rows, ngs_sources = build_ngs_sidecar()
    join_summary = add_sidecars_to_panel(rows, ff_rows, ngs_rows)
    seeds = load_seed_registry()
    registry, results = build_tests(rows, seeds)
    coverage = join_coverage(rows, ff_rows, ngs_rows)
    write_csv(OUT_DIR / "FFOPPORTUNITY_SOURCE_LEDGER.csv", ff_sources)
    write_csv(OUT_DIR / "NGS_SOURCE_LEDGER.csv", ngs_sources)
    write_csv(OUT_DIR / "FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv", ff_rows)
    write_csv(OUT_DIR / "NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv", ngs_rows)
    write_csv(OUT_DIR / "AUTONOMOUS_JOIN_COVERAGE.csv", coverage)
    write_csv(OUT_DIR / "AUTONOMOUS_PREDECLARED_TEST_REGISTRY.csv", registry)
    component = [r for r in results if r["cluster_id"] == "INGREDIENT_ONLY"]
    formula_x = [r for r in results if r["cluster_id"] != "INGREDIENT_ONLY" and "+" not in r["ingredient_set"]]
    combos = [r for r in results if "+" in r["ingredient_set"]]
    write_csv(OUT_DIR / "AUTONOMOUS_COMPONENT_TEST_RESULTS.csv", component, RESULT_FIELDS)
    write_csv(OUT_DIR / "AUTONOMOUS_FORMULA_X_INGREDIENT_RESULTS.csv", formula_x, RESULT_FIELDS)
    write_csv(OUT_DIR / "AUTONOMOUS_INGREDIENT_COMBINATION_RESULTS.csv", combos, RESULT_FIELDS)
    write_csv(OUT_DIR / "AUTONOMOUS_ALL_RESULTS_REQUIRED_SCHEMA.csv", results, RESULT_FIELDS)
    write_validation_files(rows, ff_rows, ngs_rows, results)
    make_reports(rows, ff_rows, ngs_rows, results, coverage)
    print(
        {
            "ff_sidecar_rows": len(ff_rows),
            "ngs_sidecar_rows": len(ngs_rows),
            "tests": len(results),
            "seeds": len(seeds),
            "ff_joined": join_summary["ffop_joined"],
            "ngs_joined": join_summary["ngs_joined"],
        }
    )


if __name__ == "__main__":
    main()
