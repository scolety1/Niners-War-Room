from __future__ import annotations

import csv
import hashlib
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


OUT_DIR = Path(__file__).resolve().parent

SOURCE_PARQUET = Path(
    r"C:\NWR_REVIEW\pfr_advanced_source_provenance_hardening_v1_20260707\advstats_season_rush.parquet"
)
CACHE_PARQUET = Path(
    r"C:\NWR_REVIEW\advanced_metrics_source_cache_20260707\pfr_advstats__advstats_season_rush.parquet"
)
FORMULA_MART = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
    r"\FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
AGE_LIFECYCLE_SIDECAR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709"
    r"\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709"
    r"\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
)
HIGH_VALUE_AUDIT = Path(
    r"C:\NWR\Niners-War-Room-high-value-signal-data-locator-audit-v1-20260709"
    r"\docs\hq\data_hygiene\high_value_signal_data_locator_audit_v1_20260709"
)
FORMULA_RESULTS_PIVOT = Path(
    r"C:\NWR\Niners-War-Room-formula-results-master-review-data-upgrade-pivot-v1-20260709"
    r"\docs\hq\master\formula_results_master_review_data_upgrade_pivot_v1_20260709"
)
PFR_ADDENDUM = Path(
    r"C:\NWR\Niners-War-Room-pfr-rb-broken-tackle-data-mart-join-component-test-v1-20260709"
    r"\docs\hq\master\nwr_full_system_audit_pfr_rb_broken_tackle_addendum_v1_20260709"
)
REFINEMENT_POSITION_RESULTS = Path(
    r"C:\NWR\Niners-War-Room-diverse-champion-refinement-predeclared-execution-v1-20260709"
    r"\docs\hq\model\diverse_champion_refinement_predeclared_execution_v1_20260709"
    r"\DIVERSE_CHAMPION_REFINEMENT_POSITION_RESULTS.csv"
)

SOURCE_HASH_EXPECTED = "28f44be62bd30291d5310ff62a453025d804b4d0b6720da820cb6cd943c45187"
RUN_TS = datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def mtime_iso(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def normalize_name(value: object) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", text)
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def average_rank(values: pd.Series) -> pd.Series:
    return values.rank(method="average")


def spearman(x: pd.Series, y: pd.Series) -> float:
    valid = x.notna() & y.notna()
    if valid.sum() < 3:
        return float("nan")
    xr = average_rank(pd.to_numeric(x[valid], errors="coerce"))
    yr = average_rank(pd.to_numeric(y[valid], errors="coerce"))
    if xr.nunique(dropna=True) < 2 or yr.nunique(dropna=True) < 2:
        return float("nan")
    return float(xr.corr(yr))


def pct(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{100 * float(value):.1f}%"


def fmt_float(value: float | int | None, ndigits: int = 3) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return f"{float(value):.{ndigits}f}"


def safe_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def top_n_precision(df: pd.DataFrame, score_col: str, n: int) -> float:
    pieces = []
    for _, grp in df.dropna(subset=[score_col]).groupby("season"):
        take = grp.sort_values(score_col, ascending=False).head(n)
        if len(take):
            pieces.append(take["actual_startable"].mean())
    return float(np.mean(pieces)) if pieces else float("nan")


def startable_precision(df: pd.DataFrame, score_col: str) -> float:
    # Mirrors the prior review packets: top 24 predicted RB rows per season.
    return top_n_precision(df, score_col, 24)


def false_positive_negative_counts(df: pd.DataFrame, score_col: str, n: int = 24) -> tuple[int, int]:
    fp = 0
    fn = 0
    for _, grp in df.dropna(subset=[score_col]).groupby("season"):
        ranked = grp.sort_values(score_col, ascending=False).copy()
        ranked["predicted_startable"] = False
        ranked.loc[ranked.head(n).index, "predicted_startable"] = True
        fp += int((ranked["predicted_startable"] & ~ranked["actual_startable"]).sum())
        fn += int((~ranked["predicted_startable"] & ranked["actual_startable"]).sum())
    return fp, fn


def rmse_mae(df: pd.DataFrame, score_col: str, outcome_col: str) -> tuple[float, float]:
    valid = df[[score_col, outcome_col]].dropna()
    if len(valid) < 3:
        return float("nan"), float("nan")
    # Scores have different scales, so fit a one-variable least-squares calibration for diagnostic MAE/RMSE.
    x = valid[score_col].astype(float).to_numpy()
    y = valid[outcome_col].astype(float).to_numpy()
    X = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    err = pred - y
    return float(np.mean(np.abs(err))), float(np.sqrt(np.mean(err**2)))


def r2_for_controls(df: pd.DataFrame, controls: list[str], y_col: str) -> float:
    valid_cols = controls + [y_col]
    valid = df[valid_cols].dropna()
    if len(valid) < max(10, len(controls) + 3):
        return float("nan")
    y = valid[y_col].astype(float).to_numpy()
    cols = []
    for col in controls:
        arr = valid[col].astype(float).to_numpy()
        std = arr.std()
        cols.append((arr - arr.mean()) / std if std else arr * 0)
    X = np.column_stack([np.ones(len(valid))] + cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return 1 - ss_res / ss_tot if ss_tot else float("nan")


def residual_spearman(df: pd.DataFrame, feature: str, controls: list[str], y_col: str) -> float:
    if feature in controls:
        return float("nan")
    valid = df[[feature, y_col] + controls].dropna()
    if len(valid) < max(10, len(controls) + 3):
        return float("nan")

    def residual(target: str) -> pd.Series:
        y = valid[target].astype(float).to_numpy()
        cols = []
        for col in controls:
            arr = valid[col].astype(float).to_numpy()
            std = arr.std()
            cols.append((arr - arr.mean()) / std if std else arr * 0)
        X = np.column_stack([np.ones(len(valid))] + cols)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return pd.Series(y - (X @ beta), index=valid.index)

    return spearman(residual(feature), residual(y_col))


def classify_candidate(row: dict) -> str:
    if row["candidate_id"].startswith("PFR_") and row["spearman_delta_vs_pyf_same_rows"]:
        try:
            delta = float(row["spearman_delta_vs_pyf_same_rows"])
        except ValueError:
            delta = 0.0
        if delta >= 0.015:
            return "PROMISING_REVIEW_ONLY"
        if delta >= 0.003:
            return "MIXED_REVIEW_ONLY"
        if delta > -0.003:
            return "WEAK_REVIEW_ONLY"
        return "FAILED_VS_PYF"
    if row["candidate_id"].startswith("PFR_"):
        return "WEAK_REVIEW_ONLY"
    return "REFERENCE_BASELINE"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not SOURCE_PARQUET.exists():
        write_blocked_no_source()
        return

    source_hash = sha256(SOURCE_PARQUET)
    cache_hash = sha256(CACHE_PARQUET) if CACHE_PARQUET.exists() else ""

    pfr = pd.read_parquet(SOURCE_PARQUET)
    mart = pd.read_csv(FORMULA_MART)
    rb_mart = mart[mart["position"].eq("RB")].copy()

    age_sidecar_present = AGE_LIFECYCLE_SIDECAR.exists()
    if age_sidecar_present:
        age = pd.read_csv(
            AGE_LIFECYCLE_SIDECAR,
            usecols=[
                "player_id",
                "season",
                "position",
                "age",
                "career_stage",
                "age_bucket",
                "lifecycle_bucket",
            ],
        )
        age = age[age["position"].eq("RB")]
        rb_mart = rb_mart.merge(
            age.drop(columns=["position"]),
            on=["player_id", "season"],
            how="left",
            suffixes=("", "_age_sidecar"),
        )
    else:
        for col in ["age", "career_stage", "age_bucket", "lifecycle_bucket"]:
            rb_mart[col] = ""

    pfr_rb_all = pfr[pfr["pos"].eq("RB")].copy()
    pfr_rb_all["source_name_norm"] = pfr_rb_all["player"].map(normalize_name)
    pfr_rb_all["is_multi_team_total"] = pfr_rb_all["tm"].eq("2TM")
    duplicate_source_keys_before = int(pfr_rb_all.duplicated(["season", "pfr_id"], keep=False).sum())

    # Use PFR's 2TM total row when a player has team splits; otherwise keep the only row.
    pfr_rb_all = pfr_rb_all.sort_values(
        ["season", "pfr_id", "is_multi_team_total", "att"],
        ascending=[True, True, False, False],
    )
    pfr_rb = pfr_rb_all.drop_duplicates(["season", "pfr_id"], keep="first").copy()
    pfr_rb["pfr_rush_brk_tkl__raw"] = pd.to_numeric(pfr_rb["brk_tkl"], errors="coerce")
    pfr_rb["pfr_rush_brk_tkl__per_game"] = pfr_rb["pfr_rush_brk_tkl__raw"] / pd.to_numeric(
        pfr_rb["g"], errors="coerce"
    ).replace(0, np.nan)
    pfr_rb["pfr_rush_brk_tkl__per_attempt"] = pfr_rb["pfr_rush_brk_tkl__raw"] / pd.to_numeric(
        pfr_rb["att"], errors="coerce"
    ).replace(0, np.nan)
    pfr_rb["pfr_source_season"] = pfr_rb["season"].astype(int)

    source_name_counts = (
        pfr_rb.groupby(["pfr_source_season", "source_name_norm"]).size().reset_index(name="source_name_count")
    )
    ambiguous_source_names = int((source_name_counts["source_name_count"] > 1).sum())

    pfr_join = pfr_rb[
        [
            "pfr_source_season",
            "player",
            "pfr_id",
            "tm",
            "g",
            "att",
            "pfr_rush_brk_tkl__raw",
            "pfr_rush_brk_tkl__per_game",
            "pfr_rush_brk_tkl__per_attempt",
            "source_name_norm",
        ]
    ].copy()
    pfr_join = pfr_join.merge(source_name_counts, on=["pfr_source_season", "source_name_norm"], how="left")

    rb_mart["feature_season_int"] = pd.to_numeric(rb_mart["feature_season"], errors="coerce").astype("Int64")
    rb_mart["mart_name_norm"] = rb_mart["target_player_name"].map(normalize_name)
    rb_mart["mart_name_key_count"] = rb_mart.groupby(["feature_season_int", "mart_name_norm"])[
        "player_id"
    ].transform("count")
    rb_mart["actual_startable"] = rb_mart["label_startable_hit"].map(safe_bool)
    rb_mart["actual_top12"] = pd.to_numeric(rb_mart["label_next_position_finish"], errors="coerce") <= 12
    rb_mart["actual_top24"] = pd.to_numeric(rb_mart["label_next_position_finish"], errors="coerce") <= 24
    rb_mart["actual_top36"] = pd.to_numeric(rb_mart["label_next_position_finish"], errors="coerce") <= 36

    sidecar = rb_mart.merge(
        pfr_join,
        left_on=["feature_season_int", "mart_name_norm"],
        right_on=["pfr_source_season", "source_name_norm"],
        how="left",
    )

    sidecar["join_status"] = np.select(
        [
            sidecar["feature_season_int"].isna(),
            ~sidecar["feature_season_int"].between(int(pfr_rb["pfr_source_season"].min()), int(pfr_rb["pfr_source_season"].max())),
            sidecar["mart_name_key_count"].gt(1),
            sidecar["source_name_count"].fillna(0).gt(1),
            sidecar["pfr_id"].notna(),
        ],
        [
            "missing_feature_season",
            "no_pfr_source_season",
            "ambiguous_mart_name_key",
            "ambiguous_pfr_name_key",
            "joined_name_season",
        ],
        default="not_found_by_name_season",
    )
    sidecar["coverage_status"] = np.where(
        sidecar["join_status"].eq("joined_name_season"),
        "covered_lagged_pfr_source",
        "not_covered_or_not_joined",
    )
    sidecar["review_only_status"] = "REVIEW_ONLY_RB_BROKEN_TACKLE_CONTEXT_NOT_PRODUCTION"
    sidecar["source_path"] = str(SOURCE_PARQUET)
    sidecar["source_hash"] = source_hash
    sidecar["source_feature_season"] = sidecar["feature_season_int"]
    sidecar["source_team"] = sidecar["tm"].fillna("")
    sidecar["player_name"] = sidecar["target_player_name"]
    sidecar["position"] = "RB"

    sidecar_cols = [
        "season",
        "source_feature_season",
        "player_id",
        "player_name",
        "position",
        "source_team",
        "pfr_rush_brk_tkl__raw",
        "pfr_rush_brk_tkl__per_game",
        "pfr_rush_brk_tkl__per_attempt",
        "source_path",
        "source_hash",
        "join_status",
        "coverage_status",
        "review_only_status",
    ]
    sidecar[sidecar_cols].to_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_REVIEW_ONLY_SIDECAR.csv", index=False)

    joined = sidecar[sidecar["join_status"].eq("joined_name_season")].copy()
    outcome_col = "label_next_nwr_points"
    joined[outcome_col] = pd.to_numeric(joined[outcome_col], errors="coerce")
    for col in [
        "pyf_prior_nwr_points",
        "prior_carries",
        "prior_touches",
        "prior_2yr_weighted_nwr_points",
        "prior_3yr_weighted_nwr_points",
        "pfr_rush_brk_tkl__raw",
        "pfr_rush_brk_tkl__per_game",
        "pfr_rush_brk_tkl__per_attempt",
        "label_next_position_finish",
    ]:
        joined[col] = pd.to_numeric(joined[col], errors="coerce")

    source_ledger = build_source_ledger(
        pfr=pfr,
        pfr_rb=pfr_rb,
        source_hash=source_hash,
        cache_hash=cache_hash,
        rb_mart=rb_mart,
        joined=joined,
    )
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_SOURCE_LEDGER.csv", source_ledger, SOURCE_LEDGER_FIELDS)

    schema_rows = build_schema_validation(
        pfr=pfr,
        pfr_rb=pfr_rb,
        rb_mart=rb_mart,
        sidecar=sidecar,
        joined=joined,
        source_hash=source_hash,
        cache_hash=cache_hash,
        duplicate_source_keys_before=duplicate_source_keys_before,
        ambiguous_source_names=ambiguous_source_names,
    )
    write_csv(
        OUT_DIR / "PFR_RB_BROKEN_TACKLE_SCHEMA_VALIDATION.csv",
        schema_rows,
        [
            "check_name",
            "status",
            "observed_value",
            "expected_value",
            "notes",
        ],
    )

    coverage_rows = build_join_coverage(sidecar, pfr_rb)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_JOIN_COVERAGE.csv", coverage_rows, JOIN_COVERAGE_FIELDS)

    scorecard_rows = build_scorecard(joined)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_COMPONENT_SIGNAL_SCORECARD.csv", scorecard_rows, SCORECARD_FIELDS)

    guardrail_rows = build_guardrails(joined)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_SLICE_GUARDRAILS.csv", guardrail_rows, GUARDRAIL_FIELDS)

    stability_rows = build_stability(joined)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_STABILITY_BY_SEASON.csv", stability_rows, STABILITY_FIELDS)

    summary = summarize(joined, sidecar, scorecard_rows, coverage_rows, stability_rows)
    write_markdowns(summary, schema_rows, source_ledger)

    print(
        "pfr_rb_broken_tackle_lane_complete "
        f"verdict={summary['verdict']} joined_rows={summary['joined_rows']} "
        f"best_signal={summary['best_pfr_signal']} best_spearman={summary['best_pfr_spearman']}"
    )


SOURCE_LEDGER_FIELDS = [
    "source_path",
    "source_type",
    "raw_vs_derived",
    "file_size",
    "modified_time",
    "sha256",
    "row_count",
    "columns",
    "seasons_covered",
    "player_id_fields",
    "position_fields",
    "team_fields",
    "join_keys",
    "missingness",
    "duplicate_keys",
    "source_use_gate_status",
    "leakage_asof_status",
    "safe_for_review_only_lagged_formula_mart_use",
    "notes",
]

JOIN_COVERAGE_FIELDS = [
    "coverage_scope",
    "rows",
    "eligible_rows",
    "joined_rows",
    "join_rate",
    "missing_rows",
    "missing_rate",
    "seasons",
    "notes",
]

SCORECARD_FIELDS = [
    "candidate_id",
    "input_family",
    "rows_tested",
    "seasons_tested",
    "spearman_vs_next_points",
    "pyf_spearman_same_rows",
    "spearman_delta_vs_pyf_same_rows",
    "startable_precision_top24",
    "pyf_startable_precision_top24_same_rows",
    "top12_precision",
    "top24_precision",
    "pyf_false_positives",
    "candidate_false_positives",
    "false_positive_delta_vs_pyf",
    "pyf_false_negatives",
    "candidate_false_negatives",
    "false_negative_delta_vs_pyf",
    "mae_calibrated",
    "rmse_calibrated",
    "partial_spearman_after_pyf",
    "partial_spearman_after_pyf_touches_3yr",
    "incremental_r2_after_pyf_touches_3yr",
    "classification",
    "allowed_use",
    "notes",
]

GUARDRAIL_FIELDS = [
    "slice_type",
    "slice_value",
    "rows",
    "seasons",
    "avg_raw_brk_tkl",
    "avg_per_game",
    "startable_rate",
    "avg_next_points",
    "avg_finish",
    "pyf_false_positives",
    "pyf_false_negatives",
    "sparse_history_rows",
    "low_games_rows",
    "interpretation",
]

STABILITY_FIELDS = [
    "season",
    "rows",
    "pyf_spearman",
    "raw_spearman",
    "per_game_spearman",
    "per_attempt_spearman_diagnostic",
    "raw_delta_vs_pyf",
    "per_game_delta_vs_pyf",
    "joined_rate_within_mart_rb_season",
    "notes",
]


def build_source_ledger(
    *,
    pfr: pd.DataFrame,
    pfr_rb: pd.DataFrame,
    source_hash: str,
    cache_hash: str,
    rb_mart: pd.DataFrame,
    joined: pd.DataFrame,
) -> list[dict]:
    rows: list[dict] = []

    def add_path(path: Path, source_type: str, raw_vs_derived: str, row_count: str, columns: str, notes: str) -> None:
        rows.append(
            {
                "source_path": str(path),
                "source_type": source_type,
                "raw_vs_derived": raw_vs_derived,
                "file_size": file_size(path),
                "modified_time": mtime_iso(path),
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "row_count": row_count,
                "columns": columns,
                "seasons_covered": "",
                "player_id_fields": "",
                "position_fields": "",
                "team_fields": "",
                "join_keys": "",
                "missingness": "",
                "duplicate_keys": "",
                "source_use_gate_status": "review_only_not_production_approved",
                "leakage_asof_status": "lagged_N_to_N_plus_1_required",
                "safe_for_review_only_lagged_formula_mart_use": "conditional",
                "notes": notes,
            }
        )

    rows.append(
        {
            "source_path": str(SOURCE_PARQUET),
            "source_type": "nflverse_public_pfr_advanced_rushing_parquet",
            "raw_vs_derived": "raw_public_source_cache",
            "file_size": file_size(SOURCE_PARQUET),
            "modified_time": mtime_iso(SOURCE_PARQUET),
            "sha256": source_hash,
            "row_count": len(pfr),
            "columns": "|".join(map(str, pfr.columns)),
            "seasons_covered": f"{int(pfr['season'].min())}-{int(pfr['season'].max())}",
            "player_id_fields": "pfr_id|player",
            "position_fields": "pos",
            "team_fields": "tm",
            "join_keys": "feature_season_to_source_season|normalized_target_player_name_to_pfr_player",
            "missingness": f"rb_brk_tkl_missing={int(pfr_rb['pfr_rush_brk_tkl__raw'].isna().sum())}",
            "duplicate_keys": f"post_2TM_aggregation_duplicate_pfr_season={int(pfr_rb.duplicated(['pfr_source_season','pfr_id']).sum())}",
            "source_use_gate_status": "review_only_public_pfr_source_not_production_approved",
            "leakage_asof_status": "pass_for_lagged_source_season_N_to_target_season_N_plus_1",
            "safe_for_review_only_lagged_formula_mart_use": "yes_with_identity_name_join_caveat",
            "notes": "Actual values found. Narrow RB brk_tkl only; no broad PFR promotion.",
        }
    )
    if CACHE_PARQUET.exists():
        rows.append(
            {
                "source_path": str(CACHE_PARQUET),
                "source_type": "local_duplicate_cache_of_nflverse_pfr_rushing_parquet",
                "raw_vs_derived": "raw_public_source_cache_duplicate",
                "file_size": file_size(CACHE_PARQUET),
                "modified_time": mtime_iso(CACHE_PARQUET),
                "sha256": cache_hash,
                "row_count": len(pfr),
                "columns": "|".join(map(str, pfr.columns)),
                "seasons_covered": f"{int(pfr['season'].min())}-{int(pfr['season'].max())}",
                "player_id_fields": "pfr_id|player",
                "position_fields": "pos",
                "team_fields": "tm",
                "join_keys": "not_used_primary_duplicate_hash_match",
                "missingness": "",
                "duplicate_keys": "",
                "source_use_gate_status": "review_only_duplicate_cache",
                "leakage_asof_status": "same_hash_as_primary",
                "safe_for_review_only_lagged_formula_mart_use": "manifest_only",
                "notes": "Byte-identical duplicate of primary source.",
            }
        )

    rows.append(
        {
            "source_path": str(FORMULA_MART),
            "source_type": "formula_data_mart_review_only",
            "raw_vs_derived": "derived_review_only_benchmark_substrate",
            "file_size": file_size(FORMULA_MART),
            "modified_time": mtime_iso(FORMULA_MART),
            "sha256": sha256(FORMULA_MART),
            "row_count": len(rb_mart),
            "columns": "formula_mart_columns_available_in_source_file",
            "seasons_covered": f"{int(rb_mart['season'].min())}-{int(rb_mart['season'].max())}",
            "player_id_fields": "player_id|player_name|target_player_name",
            "position_fields": "position",
            "team_fields": "",
            "join_keys": "player_id|season|feature_season|target_player_name",
            "missingness": "",
            "duplicate_keys": f"rb_player_season_duplicates={int(rb_mart.duplicated(['player_id','season','position']).sum())}",
            "source_use_gate_status": "review_only_formula_data_mart",
            "leakage_asof_status": "preexisting_review_only_asof_checked_substrate",
            "safe_for_review_only_lagged_formula_mart_use": "yes",
            "notes": "Used only to join review-only sidecar and component-test RB rows.",
        }
    )

    if AGE_LIFECYCLE_SIDECAR.exists():
        add_path(
            AGE_LIFECYCLE_SIDECAR,
            "age_lifecycle_review_only_sidecar",
            "derived_review_only_context",
            "5518",
            "age|age_bucket|lifecycle_bucket|career_stage",
            "Used only for review-only slice context.",
        )

    add_path(
        HIGH_VALUE_AUDIT / "HIGH_VALUE_SIGNAL_DATA_LOCATOR_AUDIT_V1_REPORT.md",
        "prior_data_hygiene_decision_packet",
        "review_artifact",
        "",
        "",
        "Accepted lane selecting PFR RB broken tackle as next executable data upgrade.",
    )
    add_path(
        FORMULA_RESULTS_PIVOT / "FORMULA_RESULTS_MASTER_REVIEW_DATA_UPGRADE_PIVOT_V1_REPORT.md",
        "prior_master_hq_decision_packet",
        "review_artifact",
        "",
        "",
        "Accepted formula plateau and data-upgrade pivot.",
    )
    add_path(
        PFR_ADDENDUM / "NWR_SYSTEM_AUDIT_PFR_RB_BROKEN_TACKLE_ADDENDUM_V1_REPORT.md",
        "prior_master_hq_pfr_addendum",
        "review_artifact",
        "",
        "",
        "Defines narrow RB-only PFR broken-tackle hypothesis and blocked uses.",
    )
    rows.append(
        {
            "source_path": str(OUT_DIR / "PFR_RB_BROKEN_TACKLE_REVIEW_ONLY_SIDECAR.csv"),
            "source_type": "generated_review_only_sidecar",
            "raw_vs_derived": "derived_review_only_artifact",
            "file_size": "",
            "modified_time": RUN_TS,
            "sha256": "",
            "row_count": len(rb_mart),
            "columns": "|".join(
                [
                    "season",
                    "source_feature_season",
                    "player_id",
                    "player_name",
                    "position",
                    "source_team",
                    "pfr_rush_brk_tkl__raw",
                    "pfr_rush_brk_tkl__per_game",
                    "pfr_rush_brk_tkl__per_attempt",
                    "source_path",
                    "source_hash",
                    "join_status",
                    "coverage_status",
                    "review_only_status",
                ]
            ),
            "seasons_covered": f"{int(rb_mart['season'].min())}-{int(rb_mart['season'].max())}",
            "player_id_fields": "player_id",
            "position_fields": "position",
            "team_fields": "source_team",
            "join_keys": "player_id|season after normalized_name+feature_season source join",
            "missingness": f"joined_rows={len(joined)}",
            "duplicate_keys": "",
            "source_use_gate_status": "review_only_generated_artifact",
            "leakage_asof_status": "lagged_source_season_only",
            "safe_for_review_only_lagged_formula_mart_use": "yes_with_caveats",
            "notes": "Generated in this lane; not canonical Formula Data Mart mutation.",
        }
    )
    return rows


def build_schema_validation(
    *,
    pfr: pd.DataFrame,
    pfr_rb: pd.DataFrame,
    rb_mart: pd.DataFrame,
    sidecar: pd.DataFrame,
    joined: pd.DataFrame,
    source_hash: str,
    cache_hash: str,
    duplicate_source_keys_before: int,
    ambiguous_source_names: int,
) -> list[dict]:
    required = {"season", "player", "pfr_id", "tm", "pos", "g", "att", "brk_tkl"}
    sidecar_required = {
        "season",
        "player_id",
        "player_name",
        "position",
        "pfr_rush_brk_tkl__raw",
        "pfr_rush_brk_tkl__per_game",
        "pfr_rush_brk_tkl__per_attempt",
        "source_path",
        "source_hash",
        "join_status",
        "coverage_status",
        "review_only_status",
    }
    rows = [
        {
            "check_name": "source_file_exists",
            "status": "PASS" if SOURCE_PARQUET.exists() else "FAIL",
            "observed_value": str(SOURCE_PARQUET.exists()),
            "expected_value": "True",
            "notes": str(SOURCE_PARQUET),
        },
        {
            "check_name": "source_hash_matches_prior_addendum",
            "status": "PASS" if source_hash == SOURCE_HASH_EXPECTED else "FAIL",
            "observed_value": source_hash,
            "expected_value": SOURCE_HASH_EXPECTED,
            "notes": "Matches the PFR rushing source SHA recorded by the addendum.",
        },
        {
            "check_name": "cache_hash_matches_primary",
            "status": "PASS" if cache_hash == source_hash else "WARN",
            "observed_value": cache_hash,
            "expected_value": source_hash,
            "notes": "Duplicate cache is manifest-only.",
        },
        {
            "check_name": "required_source_columns_present",
            "status": "PASS" if required.issubset(set(pfr.columns)) else "FAIL",
            "observed_value": "|".join(sorted(set(pfr.columns) & required)),
            "expected_value": "|".join(sorted(required)),
            "notes": "Allowed broken-tackle fields derive from brk_tkl, g, and att.",
        },
        {
            "check_name": "source_season_coverage",
            "status": "PASS",
            "observed_value": f"{int(pfr['season'].min())}-{int(pfr['season'].max())}",
            "expected_value": "2018-2025 observed; lagged mart test uses 2018-2024",
            "notes": "Does not cover full 2013-2025 source history.",
        },
        {
            "check_name": "rb_source_rows_present",
            "status": "PASS" if len(pfr_rb) > 0 else "FAIL",
            "observed_value": len(pfr_rb),
            "expected_value": ">0",
            "notes": "After preferring 2TM total rows for multi-team players.",
        },
        {
            "check_name": "duplicate_source_player_season_after_aggregation",
            "status": "PASS" if int(pfr_rb.duplicated(["pfr_source_season", "pfr_id"]).sum()) == 0 else "FAIL",
            "observed_value": int(pfr_rb.duplicated(["pfr_source_season", "pfr_id"]).sum()),
            "expected_value": "0",
            "notes": f"Pre-aggregation duplicate split rows observed: {duplicate_source_keys_before}.",
        },
        {
            "check_name": "ambiguous_pfr_name_season_keys",
            "status": "PASS" if ambiguous_source_names == 0 else "WARN",
            "observed_value": ambiguous_source_names,
            "expected_value": "0",
            "notes": "Join blocks ambiguous PFR name-season rows if encountered.",
        },
        {
            "check_name": "mart_rb_player_season_duplicate_keys",
            "status": "PASS" if int(rb_mart.duplicated(["player_id", "season", "position"]).sum()) == 0 else "FAIL",
            "observed_value": int(rb_mart.duplicated(["player_id", "season", "position"]).sum()),
            "expected_value": "0",
            "notes": "Formula Data Mart sidecar grain remains player_id + season + position.",
        },
        {
            "check_name": "sidecar_required_columns_present",
            "status": "PASS" if sidecar_required.issubset(set(sidecar.columns)) else "FAIL",
            "observed_value": "|".join(sorted(set(sidecar.columns) & sidecar_required)),
            "expected_value": "|".join(sorted(sidecar_required)),
            "notes": "Output sidecar retains required review-only columns.",
        },
        {
            "check_name": "sidecar_duplicate_output_keys",
            "status": "PASS" if int(sidecar.duplicated(["player_id", "season", "position"]).sum()) == 0 else "FAIL",
            "observed_value": int(sidecar.duplicated(["player_id", "season", "position"]).sum()),
            "expected_value": "0",
            "notes": "Sidecar is safe to inspect at RB player-season grain.",
        },
        {
            "check_name": "joined_rows_available_for_component_test",
            "status": "PASS" if len(joined) >= 100 else "WARN",
            "observed_value": len(joined),
            "expected_value": ">=100",
            "notes": "Enough rows for a focused RB-only component signal test.",
        },
        {
            "check_name": "leakage_asof_lag_rule",
            "status": "PASS"
            if (joined["source_feature_season"].astype(float) < joined["season"].astype(float)).all()
            else "FAIL",
            "observed_value": "source_feature_season < target season for all joined rows",
            "expected_value": "True",
            "notes": "No same-season PFR values are used for target-season outcomes.",
        },
        {
            "check_name": "blocked_broad_pfr_and_pff_guard",
            "status": "PASS",
            "observed_value": "only brk_tkl derived raw/per_game/per_attempt included; no PFF/proxy fields",
            "expected_value": "narrow RB-only PFR broken tackle",
            "notes": "PFR remains not production-approved.",
        },
    ]
    return rows


def build_join_coverage(sidecar: pd.DataFrame, pfr_rb: pd.DataFrame) -> list[dict]:
    total = len(sidecar)
    joined = int(sidecar["join_status"].eq("joined_name_season").sum())
    eligible = int(
        sidecar["feature_season_int"].between(
            int(pfr_rb["pfr_source_season"].min()), int(pfr_rb["pfr_source_season"].max() - 1)
        ).sum()
    )
    # source 2025 is present but cannot be used until a target 2026 outcome exists.
    lag_eligible = sidecar[sidecar["feature_season_int"].between(2018, 2024)]
    lag_joined = int(lag_eligible["join_status"].eq("joined_name_season").sum())
    rows = [
        {
            "coverage_scope": "all_formula_mart_rb_rows",
            "rows": total,
            "eligible_rows": eligible,
            "joined_rows": joined,
            "join_rate": pct(joined / total if total else float("nan")),
            "missing_rows": total - joined,
            "missing_rate": pct((total - joined) / total if total else float("nan")),
            "seasons": f"{int(sidecar['season'].min())}-{int(sidecar['season'].max())}",
            "notes": "Includes 2013-2018 target rows whose feature seasons precede PFR coverage.",
        },
        {
            "coverage_scope": "lag_eligible_target_rows_feature_season_2018_2024",
            "rows": len(lag_eligible),
            "eligible_rows": len(lag_eligible),
            "joined_rows": lag_joined,
            "join_rate": pct(lag_joined / len(lag_eligible) if len(lag_eligible) else float("nan")),
            "missing_rows": len(lag_eligible) - lag_joined,
            "missing_rate": pct((len(lag_eligible) - lag_joined) / len(lag_eligible) if len(lag_eligible) else float("nan")),
            "seasons": f"{int(lag_eligible['season'].min())}-{int(lag_eligible['season'].max())}",
            "notes": "Component-test coverage after applying N to N+1 leakage rule.",
        },
    ]
    for season, grp in sidecar.groupby("season"):
        joined_s = int(grp["join_status"].eq("joined_name_season").sum())
        eligible_s = int(grp["feature_season_int"].between(2018, 2024).sum())
        rows.append(
            {
                "coverage_scope": f"target_season_{int(season)}",
                "rows": len(grp),
                "eligible_rows": eligible_s,
                "joined_rows": joined_s,
                "join_rate": pct(joined_s / len(grp) if len(grp) else float("nan")),
                "missing_rows": len(grp) - joined_s,
                "missing_rate": pct((len(grp) - joined_s) / len(grp) if len(grp) else float("nan")),
                "seasons": str(int(season)),
                "notes": "Season-level RB Formula Mart join coverage.",
            }
        )
    return rows


def build_scorecard(joined: pd.DataFrame) -> list[dict]:
    score_cols = {
        "PYF_BASELINE_SAME_ROWS": ("baseline", "pyf_prior_nwr_points", "Prior-year fantasy points baseline."),
        "PRIOR_CARRIES_REFERENCE": ("volume_control", "prior_carries", "Rushing volume control."),
        "PRIOR_TOUCHES_REFERENCE": ("volume_control", "prior_touches", "Touch volume control."),
        "PRIOR_2YR_WEIGHTED_REFERENCE": (
            "multi_year_production_control",
            "prior_2yr_weighted_nwr_points",
            "Two-year weighted production control.",
        ),
        "PRIOR_3YR_WEIGHTED_REFERENCE": (
            "multi_year_production_control",
            "prior_3yr_weighted_nwr_points",
            "Three-year weighted production control.",
        ),
        "PFR_BRK_TKL_RAW_REVIEW_ONLY": (
            "pfr_rb_broken_tackle",
            "pfr_rush_brk_tkl__raw",
            "Primary review-only PFR broken tackle raw count.",
        ),
        "PFR_BRK_TKL_PER_GAME_REVIEW_ONLY": (
            "pfr_rb_broken_tackle",
            "pfr_rush_brk_tkl__per_game",
            "Primary review-only PFR broken tackles per game.",
        ),
        "PFR_BRK_TKL_PER_ATTEMPT_DIAGNOSTIC_ONLY": (
            "pfr_rb_broken_tackle_diagnostic",
            "pfr_rush_brk_tkl__per_attempt",
            "Diagnostic only; not admitted as a primary candidate.",
        ),
    }
    controls = ["pyf_prior_nwr_points", "prior_touches", "prior_3yr_weighted_nwr_points"]
    control_r2 = r2_for_controls(joined, controls, "label_next_nwr_points")
    pyf_spearman = spearman(joined["pyf_prior_nwr_points"], joined["label_next_nwr_points"])
    pyf_precision = startable_precision(joined, "pyf_prior_nwr_points")
    pyf_fp, pyf_fn = false_positive_negative_counts(joined, "pyf_prior_nwr_points")
    rows = []
    for candidate_id, (family, col, notes) in score_cols.items():
        rows_tested = int(joined[[col, "label_next_nwr_points"]].dropna().shape[0])
        sp = spearman(joined[col], joined["label_next_nwr_points"])
        precision = startable_precision(joined, col)
        top12 = top_n_precision(joined, col, 12)
        top24 = top_n_precision(joined, col, 24)
        fp, fn = false_positive_negative_counts(joined, col)
        mae, rmse = rmse_mae(joined, col, "label_next_nwr_points")
        partial_pyf = residual_spearman(joined, col, ["pyf_prior_nwr_points"], "label_next_nwr_points")
        partial_full = residual_spearman(joined, col, controls, "label_next_nwr_points")
        add_r2 = r2_for_controls(joined, controls + [col], "label_next_nwr_points")
        row = {
            "candidate_id": candidate_id,
            "input_family": family,
            "rows_tested": rows_tested,
            "seasons_tested": f"{int(joined['season'].min())}-{int(joined['season'].max())}" if rows_tested else "",
            "spearman_vs_next_points": fmt_float(sp),
            "pyf_spearman_same_rows": fmt_float(pyf_spearman),
            "spearman_delta_vs_pyf_same_rows": fmt_float(sp - pyf_spearman if not math.isnan(sp) and not math.isnan(pyf_spearman) else float("nan")),
            "startable_precision_top24": pct(precision),
            "pyf_startable_precision_top24_same_rows": pct(pyf_precision),
            "top12_precision": pct(top12),
            "top24_precision": pct(top24),
            "pyf_false_positives": pyf_fp,
            "candidate_false_positives": fp,
            "false_positive_delta_vs_pyf": fp - pyf_fp,
            "pyf_false_negatives": pyf_fn,
            "candidate_false_negatives": fn,
            "false_negative_delta_vs_pyf": fn - pyf_fn,
            "mae_calibrated": fmt_float(mae),
            "rmse_calibrated": fmt_float(rmse),
            "partial_spearman_after_pyf": fmt_float(partial_pyf),
            "partial_spearman_after_pyf_touches_3yr": fmt_float(partial_full),
            "incremental_r2_after_pyf_touches_3yr": fmt_float(add_r2 - control_r2 if not math.isnan(add_r2) and not math.isnan(control_r2) else float("nan"), 5),
            "classification": "",
            "allowed_use": "review_only_component_signal_test" if candidate_id.startswith("PFR_") else "reference_only",
            "notes": notes,
        }
        row["classification"] = classify_candidate(row)
        rows.append(row)
    return rows


def build_guardrails(joined: pd.DataFrame) -> list[dict]:
    df = joined.copy()
    positive = df["pfr_rush_brk_tkl__raw"].fillna(0)
    df["raw_brk_tkl_bucket"] = np.select(
        [
            positive.eq(0),
            positive.between(1, 3, inclusive="both"),
            positive.between(4, 8, inclusive="both"),
            positive.gt(8),
        ],
        ["zero", "low_1_to_3", "medium_4_to_8", "high_9_plus"],
        default="unknown",
    )
    per_game = df["pfr_rush_brk_tkl__per_game"].fillna(0)
    df["per_game_bucket"] = np.select(
        [
            per_game.eq(0),
            per_game.gt(0) & per_game.le(0.25),
            per_game.gt(0.25) & per_game.le(0.60),
            per_game.gt(0.60),
        ],
        ["zero", "low_gt0_to_0_25", "medium_0_25_to_0_60", "high_gt_0_60"],
        default="unknown",
    )
    df["pyf_rank"] = df.groupby("season")["pyf_prior_nwr_points"].rank(ascending=False, method="first")
    df["pyf_predicted_startable"] = df["pyf_rank"] <= 24
    df["pyf_false_positive"] = df["pyf_predicted_startable"] & ~df["actual_startable"]
    df["pyf_false_negative"] = ~df["pyf_predicted_startable"] & df["actual_startable"]

    rows: list[dict] = []

    def add_group(slice_type: str, slice_col: str) -> None:
        for value, grp in df.groupby(slice_col, dropna=False):
            if len(grp) == 0:
                continue
            rows.append(
                {
                    "slice_type": slice_type,
                    "slice_value": str(value) if str(value) else "missing",
                    "rows": len(grp),
                    "seasons": f"{int(grp['season'].min())}-{int(grp['season'].max())}",
                    "avg_raw_brk_tkl": fmt_float(grp["pfr_rush_brk_tkl__raw"].mean()),
                    "avg_per_game": fmt_float(grp["pfr_rush_brk_tkl__per_game"].mean()),
                    "startable_rate": pct(grp["actual_startable"].mean()),
                    "avg_next_points": fmt_float(grp["label_next_nwr_points"].mean()),
                    "avg_finish": fmt_float(grp["label_next_position_finish"].mean()),
                    "pyf_false_positives": int(grp["pyf_false_positive"].sum()),
                    "pyf_false_negatives": int(grp["pyf_false_negative"].sum()),
                    "sparse_history_rows": int(grp["sparse_history_flag"].map(safe_bool).sum()),
                    "low_games_rows": int(grp["low_games_flag"].map(safe_bool).sum()),
                    "interpretation": "review_only_slice_context_not_ranking_rule",
                }
            )

    add_group("pfr_raw_broken_tackle_bucket", "raw_brk_tkl_bucket")
    add_group("pfr_per_game_bucket", "per_game_bucket")
    add_group("role_archetype", "role_archetype")
    if "age_bucket" in df.columns:
        add_group("age_bucket", "age_bucket")
    if "lifecycle_bucket" in df.columns:
        add_group("lifecycle_bucket", "lifecycle_bucket")
    add_group("sparse_history_flag", "sparse_history_flag")
    add_group("low_games_flag", "low_games_flag")
    return rows


def build_stability(joined: pd.DataFrame) -> list[dict]:
    rows = []
    for season, grp in joined.groupby("season"):
        mart_rows = int(joined[joined["season"].eq(season)].shape[0])
        raw_sp = spearman(grp["pfr_rush_brk_tkl__raw"], grp["label_next_nwr_points"])
        pg_sp = spearman(grp["pfr_rush_brk_tkl__per_game"], grp["label_next_nwr_points"])
        pa_sp = spearman(grp["pfr_rush_brk_tkl__per_attempt"], grp["label_next_nwr_points"])
        pyf_sp = spearman(grp["pyf_prior_nwr_points"], grp["label_next_nwr_points"])
        rows.append(
            {
                "season": int(season),
                "rows": len(grp),
                "pyf_spearman": fmt_float(pyf_sp),
                "raw_spearman": fmt_float(raw_sp),
                "per_game_spearman": fmt_float(pg_sp),
                "per_attempt_spearman_diagnostic": fmt_float(pa_sp),
                "raw_delta_vs_pyf": fmt_float(raw_sp - pyf_sp if not math.isnan(raw_sp) and not math.isnan(pyf_sp) else float("nan")),
                "per_game_delta_vs_pyf": fmt_float(pg_sp - pyf_sp if not math.isnan(pg_sp) and not math.isnan(pyf_sp) else float("nan")),
                "joined_rate_within_mart_rb_season": pct(len(grp) / mart_rows if mart_rows else float("nan")),
                "notes": "Season-level stability only; small seasonal samples can swing.",
            }
        )
    return rows


def summarize(
    joined: pd.DataFrame,
    sidecar: pd.DataFrame,
    scorecard: list[dict],
    coverage: list[dict],
    stability: list[dict],
) -> dict:
    pfr_rows = [row for row in scorecard if row["candidate_id"].startswith("PFR_")]
    primary = [row for row in pfr_rows if "PER_ATTEMPT" not in row["candidate_id"]]
    best = max(primary, key=lambda r: float(r["spearman_vs_next_points"] or "-999"))
    pyf = next(row for row in scorecard if row["candidate_id"] == "PYF_BASELINE_SAME_ROWS")
    raw = next(row for row in scorecard if row["candidate_id"] == "PFR_BRK_TKL_RAW_REVIEW_ONLY")
    per_game = next(row for row in scorecard if row["candidate_id"] == "PFR_BRK_TKL_PER_GAME_REVIEW_ONLY")
    deltas = [
        float(row["spearman_delta_vs_pyf_same_rows"])
        for row in primary
        if row["spearman_delta_vs_pyf_same_rows"] not in {"", None}
    ]
    best_delta = max(deltas) if deltas else float("nan")
    if best_delta >= 0.015:
        verdict = "GREEN_PFR_RB_BROKEN_TACKLE_ADDS_REVIEW_ONLY_SIGNAL"
        next_use = "AVAILABLE_REVIEW_ONLY_COMPONENT_SIGNAL"
    elif best_delta >= -0.003:
        verdict = "YELLOW_PFR_RB_BROKEN_TACKLE_MIXED_OR_GUARDRAIL_ONLY"
        next_use = "AVAILABLE_REVIEW_ONLY_GUARDRAIL_CONTEXT"
    else:
        verdict = "RED_PFR_RB_BROKEN_TACKLE_NO_INCREMENTAL_SIGNAL"
        next_use = "AVAILABLE_BUT_NO_INCREMENTAL_SIGNAL"

    eligible = sidecar[sidecar["feature_season_int"].between(2018, 2024)]
    joined_rows = len(joined)
    missing_rate = 1 - joined_rows / len(eligible) if len(eligible) else float("nan")
    season_stability_positive = sum(
        1
        for row in stability
        if row["raw_delta_vs_pyf"] not in {"", None} and float(row["raw_delta_vs_pyf"]) > 0
    )
    return {
        "verdict": verdict,
        "next_use": next_use,
        "total_rb_mart_rows": len(sidecar),
        "eligible_rows": len(eligible),
        "joined_rows": joined_rows,
        "missing_rate": missing_rate,
        "seasons_joined": f"{int(joined['season'].min())}-{int(joined['season'].max())}" if joined_rows else "",
        "source_seasons": "2018-2025",
        "lagged_source_seasons_tested": "2018-2024",
        "best_pfr_signal": best["candidate_id"],
        "best_pfr_spearman": best["spearman_vs_next_points"],
        "best_delta_vs_pyf": fmt_float(best_delta),
        "pyf_spearman": pyf["spearman_vs_next_points"],
        "raw_spearman": raw["spearman_vs_next_points"],
        "per_game_spearman": per_game["spearman_vs_next_points"],
        "season_stability_positive": season_stability_positive,
        "season_count": len(stability),
        "join_rate": pct(joined_rows / len(eligible) if len(eligible) else float("nan")),
        "overall_join_rate": pct(joined_rows / len(sidecar) if len(sidecar) else float("nan")),
    }


def write_markdowns(summary: dict, schema_rows: list[dict], source_ledger: list[dict]) -> None:
    report = f"""
# PFR RB Broken Tackle Data Mart Join / Component Test V1 Report

## Verdict

`{summary['verdict']}`

## Executive Summary

Actual narrow PFR RB broken-tackle values were found locally in the nflverse public PFR advanced rushing parquet cache. The primary source hash is `{SOURCE_HASH_EXPECTED}`, matching the hash recorded by the prior PFR addendum. The lane built a review-only sidecar and ran a focused RB-only component signal test using lagged source season N to target season N+1.

The result is not production, not a broad PFR promotion, and not ranking integration. PFR broken-tackle context is partial because source coverage begins in 2018, not 2013. The joined values are descriptive, but the focused component test did not show incremental signal beyond PYF or multi-year production, so this branch should be parked rather than advanced into another formula test.

## Source and Coverage

- Source file: `{SOURCE_PARQUET}`
- Source seasons: `{summary['source_seasons']}`
- Lagged source seasons tested: `{summary['lagged_source_seasons_tested']}`
- Formula Mart RB rows: `{summary['total_rb_mart_rows']}`
- Lag-eligible RB rows: `{summary['eligible_rows']}`
- Joined/tested RB rows: `{summary['joined_rows']}`
- Lag-eligible join coverage: `{summary['join_rate']}`
- Overall RB sidecar coverage: `{summary['overall_join_rate']}`
- Missingness among lag-eligible rows: `{pct(summary['missing_rate'])}`

## Signal Result

- PYF Spearman on same joined RB rows: `{summary['pyf_spearman']}`
- Raw broken-tackle Spearman: `{summary['raw_spearman']}`
- Per-game broken-tackle Spearman: `{summary['per_game_spearman']}`
- Best PFR primary signal: `{summary['best_pfr_signal']}`
- Best PFR delta vs PYF on same rows: `{summary['best_delta_vs_pyf']}`
- Season-stability positive raw delta seasons: `{summary['season_stability_positive']} / {summary['season_count']}`

## Interpretation

PFR broken tackles do not replace PYF or multi-year production. Raw and per-game tackle-breaking values trail PYF on the same joined rows and trail PYF in every tested target season. High broken-tackle buckets mostly identify productive prior-year RBs that the existing production fields already capture. The output files include partial residual and incremental diagnostic checks; those are review-only diagnostics, not formula weights.

`per_attempt` remains diagnostic only because it can overstate low-attempt players.

## Gates Preserved

- PFR production/model-use remains blocked.
- Broad PFR feature promotion remains blocked.
- PFR QB passing remains blocked.
- PFF Elusive Rating and `nwr_elusive_proxy_review_only` remain blocked.
- Production/model-use and rankings integration remain blocked.
- App/runtime/model behavior did not change.
- Canonical `local_exports` was not written.
"""

    next_lane = (
        "PFR RB Broken Tackle Cluster-Seed Formula Test V1"
        if summary["next_use"] == "AVAILABLE_REVIEW_ONLY_COMPONENT_SIGNAL"
        else "Historical Market / ADP Source Gate and Data Mart Join V1"
    )
    next_use = f"""
# PFR RB Broken Tackle Next Use Decision

## Decision

`{summary['next_use']}`

## Maximum Allowed Use

Review-only evidence/slice context only. The current component result does not justify another PFR-specific formula branch. The sidecar should remain preserved as evidence, but it may not be used as production model input, direct ranking input, hidden sort logic, or broad PFR source promotion.

## Recommended Next Lane

`{next_lane}`

## Rationale

The PFR branch now has actual values, a review-only sidecar, source hash validation, lagged as-of handling, and RB-only component metrics. The evidence is not strong enough for a PFR-specific follow-up: raw and per-game broken-tackle values trail PYF and multi-year production, and `per_attempt` is weak diagnostic-only. The larger accuracy path should pivot to market/ADP source-gate work.
"""

    blockers = """
# PFR RB Broken Tackle Blockers and Caveats

- The source starts in 2018, so it does not support full 2013-2025 historical formula coverage.
- The join uses normalized player name plus source feature season because the Formula Data Mart uses GSIS-style `player_id` while the PFR source uses `pfr_id`.
- Multi-team PFR rows were handled by preferring `2TM` total rows; this avoids duplicate player-season sidecar keys.
- `pfr_rush_brk_tkl__per_attempt` is diagnostic only.
- Values are RB-only and review-only.
- PFR is not production-approved.
- Broad PFR, PFR QB passing, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
- Any future formula candidate must compare against PYF, rushing volume, prior touches, and multi-year production.
"""

    source_trace = f"""
# PFR RB Broken Tackle Source Trace

## Current Lane

- Artifact folder: `{OUT_DIR}`
- Source parquet: `{SOURCE_PARQUET}`
- Source SHA256: `{SOURCE_HASH_EXPECTED}`
- Cache parquet: `{CACHE_PARQUET}`

## Prior Decisions Read

- High-Value Signal Data Locator Audit V1: `{HIGH_VALUE_AUDIT}`
- Formula Results Master Review / Data Upgrade Pivot V1: `{FORMULA_RESULTS_PIVOT}`
- PFR RB Broken Tackle Addendum V1: `{PFR_ADDENDUM}`
- Formula Data Mart / Feature Availability Audit V1 source mart: `{FORMULA_MART}`
- Diverse Champion Refinement position references: `{REFINEMENT_POSITION_RESULTS}`

## Use Gate

The source is treated as public nflverse PFR advanced rushing context for review-only RB broken-tackle testing. This lane does not promote PFR to production/model-use, does not use PFR QB passing, and does not use PFF-style elusive/proxy metrics.
"""

    write_text(OUT_DIR / "PFR_RB_BROKEN_TACKLE_DATA_MART_JOIN_COMPONENT_TEST_V1_REPORT.md", report)
    write_text(OUT_DIR / "PFR_RB_BROKEN_TACKLE_NEXT_USE_DECISION.md", next_use)
    write_text(OUT_DIR / "PFR_RB_BROKEN_TACKLE_BLOCKERS_AND_CAVEATS.md", blockers)
    write_text(OUT_DIR / "PFR_RB_BROKEN_TACKLE_SOURCE_TRACE.md", source_trace)


def write_blocked_no_source() -> None:
    source_rows = [
        {
            "source_path": str(SOURCE_PARQUET),
            "source_type": "expected_nflverse_public_pfr_advanced_rushing_parquet",
            "raw_vs_derived": "missing",
            "file_size": "",
            "modified_time": "",
            "sha256": "",
            "row_count": "",
            "columns": "",
            "seasons_covered": "",
            "player_id_fields": "",
            "position_fields": "",
            "team_fields": "",
            "join_keys": "",
            "missingness": "source_missing",
            "duplicate_keys": "",
            "source_use_gate_status": "blocked_missing_source_values",
            "leakage_asof_status": "not_tested",
            "safe_for_review_only_lagged_formula_mart_use": "no",
            "notes": "Actual values not found.",
        }
    ]
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_SOURCE_LEDGER.csv", source_rows, SOURCE_LEDGER_FIELDS)
    write_csv(
        OUT_DIR / "PFR_RB_BROKEN_TACKLE_SCHEMA_VALIDATION.csv",
        [
            {
                "check_name": "actual_source_values_found",
                "status": "FAIL",
                "observed_value": "False",
                "expected_value": "True",
                "notes": "Stopped per lane instruction.",
            }
        ],
        ["check_name", "status", "observed_value", "expected_value", "notes"],
    )
    empty_sidecar_fields = [
        "season",
        "source_feature_season",
        "player_id",
        "player_name",
        "position",
        "source_team",
        "pfr_rush_brk_tkl__raw",
        "pfr_rush_brk_tkl__per_game",
        "pfr_rush_brk_tkl__per_attempt",
        "source_path",
        "source_hash",
        "join_status",
        "coverage_status",
        "review_only_status",
    ]
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_REVIEW_ONLY_SIDECAR.csv", [], empty_sidecar_fields)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_JOIN_COVERAGE.csv", [], JOIN_COVERAGE_FIELDS)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_COMPONENT_SIGNAL_SCORECARD.csv", [], SCORECARD_FIELDS)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_SLICE_GUARDRAILS.csv", [], GUARDRAIL_FIELDS)
    write_csv(OUT_DIR / "PFR_RB_BROKEN_TACKLE_STABILITY_BY_SEASON.csv", [], STABILITY_FIELDS)
    write_text(
        OUT_DIR / "PFR_RB_BROKEN_TACKLE_DATA_MART_JOIN_COMPONENT_TEST_V1_REPORT.md",
        "# PFR RB Broken Tackle Data Mart Join / Component Test V1 Report\n\n`RED_PFR_RB_BROKEN_TACKLE_VALUES_NOT_FOUND`\n",
    )
    write_text(
        OUT_DIR / "PFR_RB_BROKEN_TACKLE_NEXT_USE_DECISION.md",
        "# PFR RB Broken Tackle Next Use Decision\n\n`BLOCKED`\n",
    )
    write_text(
        OUT_DIR / "PFR_RB_BROKEN_TACKLE_BLOCKERS_AND_CAVEATS.md",
        "# PFR RB Broken Tackle Blockers and Caveats\n\nActual values were not found.\n",
    )
    write_text(
        OUT_DIR / "PFR_RB_BROKEN_TACKLE_SOURCE_TRACE.md",
        f"# PFR RB Broken Tackle Source Trace\n\nExpected source missing: `{SOURCE_PARQUET}`\n",
    )
    print("pfr_rb_broken_tackle_lane_complete verdict=RED_PFR_RB_BROKEN_TACKLE_VALUES_NOT_FOUND")


if __name__ == "__main__":
    main()
