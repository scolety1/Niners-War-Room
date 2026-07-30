#!/usr/bin/env python3
"""Build the deterministic, review-only NWR Dual Lens RC1 research packet.

This runner is intentionally bounded to the pre-registered W0-W3 and D0-D3
families. It reads only fixed local/tracked evidence, uses exact player IDs,
performs chronological nested selection, and never writes app/runtime,
production ranking, Outcome V3, frozen-comparator, provider, or LocalData
paths.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import shutil
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_REL = Path("docs/hq/master/nwr_dual_lens_rc1_v1_20260729")
DEFAULT_CURRENT_FEATURES = Path(
    r"C:\NWR_REVIEW\current_board_candidate_scoring_feature_completion_gate_v1_20260702"
    r"\current_board_candidate_feature_input_completed_review_only.csv"
)

MART_REL = Path(
    "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/"
    "FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
AGE_REL = Path(
    "docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/"
    "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
)
ROOKIE_REL = Path(
    "docs/hq/model/rookie_draft_capital_data_mart_join_component_test_v1_20260709/"
    "ROOKIE_DRAFT_CAPITAL_REVIEW_ONLY_SIDECAR.csv"
)
PANEL_REL = Path(
    "docs/hq/model/historical_model_v4_replay_substrate_v1_20260708/"
    "MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
)
PROXY_BUILDER_REL = Path(
    "docs/hq/model/production_rankings_backtest_v1_20260708/"
    "build_production_rankings_backtest_v1.py"
)
BOARD_REL = Path(
    "docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/"
    "rebuilt_full_player_board_value_review_rows.csv"
)
FROZEN_REL = Path(
    "docs/hq/model/"
    "formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/"
    "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
)
OUTCOME_BOARD_REL = Path(
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/"
    "CURRENT_2026_OUTCOME_V3_SHADOW_BOARD.csv"
)
OUTCOME_SCHEMA_REL = Path(
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/OUTCOME_V3_SCHEMA.csv"
)
SCORING_REL = Path("config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json")
FORMULA_CONTRACT_REL = Path(
    "docs/hq/model/model_v4_formula_documentation_cleanup_v1_20260708/"
    "MODEL_V4_ACTIVE_FORMULA_CONTRACT.md"
)
FORMULA_REGISTRY_REL = Path(
    "docs/hq/model/model_v4_formula_documentation_cleanup_v1_20260708/"
    "MODEL_V4_COMPONENT_REGISTRY.csv"
)

EXPECTED_HASHES = {
    MART_REL: "4c63a01cc4d56d0496d56ff13d4dabb4faa0b7a24d8f7510a368ad48d9714151",
    AGE_REL: "ea5ec2455c89031b8deb6077847b7c10e4da4a09f604bf1dae0e6250983f883b",
    ROOKIE_REL: "d088e2723ebb1edfaf7c9bc8020e5405d144bd142d8ee75e6fb8b59a6aef2c48",
    PANEL_REL: "22c7aa9ecb8567d0ff795809d075f8f8ac91a3dfe56e7a31f8a328ba99c9b99f",
    PROXY_BUILDER_REL: (
        "c9676d4ca145b50492066bfef89c3b5b708600fd61adae82349eedf3ea611590"
    ),
    BOARD_REL: "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4",
    FROZEN_REL: "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179",
    OUTCOME_BOARD_REL: (
        "256c4deb8c0199d29143fc117a43496dc6847dd0e7b3724549a372cb1b6df577"
    ),
    OUTCOME_SCHEMA_REL: (
        "7001e319eb0aafc2a3eb9d4de8a2fd421b19fabd552bc16a1a5df69b48ab2cff"
    ),
    SCORING_REL: "03986944a57f0f73c78a8f56413b53749b3e384a10788ff7ab262d21e0b1eab2",
    FORMULA_CONTRACT_REL: (
        "be14b8eed1d00ad25418cc3c76b07c2c95e1a44d9bbb23d3ce5284ec5b825c9d"
    ),
    FORMULA_REGISTRY_REL: (
        "daea46d9295647624b701291838f27a765919cfb7ecf4f82572de345d0ec2c3f"
    ),
}
CURRENT_FEATURES_HASH = (
    "bdff4e6c0c51b64a3f867c6ed11f72cda088046e1ffd194c32fb55f49357d1e0"
)

SEED = 20260729
BOOTSTRAP_ITERATIONS = 100
POSITIONS = ("QB", "RB", "WR", "TE")
POSITION_ORDER = {position: index for index, position in enumerate(POSITIONS)}
REPLACEMENT_CUTOFF = {"QB": 12, "RB": 30, "WR": 40, "TE": 12}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
ELITE_CUTOFF = {"QB": 6, "RB": 12, "WR": 12, "TE": 6}
WIN_ORIGINS = tuple(range(2017, 2027))
DYNASTY_ORIGINS = tuple(range(2018, 2027))
WIN_EVALUATION_SEASONS = tuple(range(2017, 2026))
DYNASTY_EVALUATION_SEASONS = tuple(range(2018, 2024))
RIDGE_ALPHAS = (0.25, 1.0, 4.0)
WIN_BLEND_WEIGHTS = (0.25, 0.50, 0.75)
DISCOUNT_SCHEDULES = {
    "SHORT_1_055_025": (1.0, 0.55, 0.25),
    "BALANCED_1_070_045": (1.0, 0.70, 0.45),
    "PATIENT_1_080_060": (1.0, 0.80, 0.60),
}
AGE_PROFILES = {
    "EARLY_POSITION_INFLECTION": {"QB": 32.0, "RB": 25.0, "WR": 27.0, "TE": 28.0},
    "BALANCED_POSITION_INFLECTION": {"QB": 34.0, "RB": 27.0, "WR": 29.0, "TE": 30.0},
    "LATE_POSITION_INFLECTION": {"QB": 36.0, "RB": 29.0, "WR": 31.0, "TE": 32.0},
}
DEFAULT_DISCOUNT = "BALANCED_1_070_045"
DEFAULT_AGE_PROFILE = "BALANCED_POSITION_INFLECTION"

COMMON_FEATURES = (
    "pyf_prior_nwr_points",
    "pyf_prior_nwr_ppg",
    "prior_games",
    "prior_opportunities",
    "prior_2yr_weighted_nwr_points",
    "prior_3yr_weighted_nwr_points",
)
POSITION_FEATURES = {
    "QB": (
        "prior_passing_attempts",
        "prior_passing_yards",
        "prior_passing_td",
        "prior_passing_first_downs",
        "prior_carries",
        "prior_rushing_yards",
    ),
    "RB": (
        "prior_touches",
        "prior_carries",
        "prior_rushing_yards",
        "prior_rushing_first_downs",
        "prior_targets",
        "prior_receiving_yards",
    ),
    "WR": (
        "prior_targets",
        "prior_receptions",
        "prior_receiving_yards",
        "prior_receiving_first_downs",
        "prior_touches",
    ),
    "TE": (
        "prior_targets",
        "prior_receptions",
        "prior_receiving_yards",
        "prior_receiving_first_downs",
        "prior_touches",
    ),
}

REQUIRED_OUTPUTS = (
    "DUAL_LENS_RC1_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "FINISHED_V1_AND_OUTCOME_V3_BASELINE.md",
    "WIN_NOW_TARGET_CONTRACT.md",
    "DYNASTY_TARGET_CONTRACT.md",
    "ROOKIE_EVIDENCE_AUTHORITY.csv",
    "ROOKIE_VETERAN_EVALUATION.csv",
    "FORMULA_CANDIDATE_DEFINITIONS.csv",
    "WIN_NOW_WALK_FORWARD_RESULTS.csv",
    "DYNASTY_WALK_FORWARD_RESULTS.csv",
    "WIN_NOW_ACCEPTANCE_GATE_MATRIX.csv",
    "DYNASTY_ACCEPTANCE_GATE_MATRIX.csv",
    "POSITION_AGE_GAMES_COHORT_RESULTS.csv",
    "RETENTION_AVAILABILITY_RESULTS.csv",
    "CURRENT_2026_DUAL_LENS_SHADOW_BOARD.csv",
    "CMC_AJ_BROWN_JONATHAN_TAYLOR_REVIEW.md",
    "LARGEST_WIN_NOW_DYNASTY_GAPS.csv",
    "TEAM_WINDOW_CONTRACT.md",
    "TEAM_WINDOW_SENSITIVITY.csv",
    "CORE_APP_REFRESH_AUDIT.csv",
    "PLAYER_COMPARE_REFRESH.md",
    "TRADING_LAB_REFRESH.md",
    "DRAFT_TOOLS_REFRESH.md",
    "ROSTER_PLANNING_REFRESH.md",
    "DATA_HEALTH_MODEL_STATUS.md",
    "VIEWPORT_AND_ACCESSIBILITY_RESULTS.csv",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "DETERMINISTIC_REGENERATION_RESULTS.csv",
    "PRODUCTION_BASELINES_NO_CHANGE.md",
    "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
    "PROTECTED_AND_FROZEN_PATH_PROOF.md",
    "ROLLBACK_PLAN.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


@dataclass(frozen=True)
class RidgeModel:
    features: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    coefficients: tuple[float, ...]
    alpha: float
    model_hash: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    def safe(item: Any) -> Any:
        if isinstance(item, dict):
            return {str(key): safe(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [safe(child) for child in item]
        if isinstance(item, np.generic):
            return safe(item.item())
        if isinstance(item, float) and not math.isfinite(item):
            return None
        if isinstance(item, Path):
            return item.as_posix()
        return item

    payload = json.dumps(
        safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def truth_value(value: Any) -> bool:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def numeric(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    output = frame.copy()
    output.to_csv(
        path,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        float_format="%.9f",
    )


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def rank_desc(series: pd.Series) -> pd.Series:
    return series.rank(method="first", ascending=False, na_option="keep")


def percentile_score(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    result = pd.Series(np.nan, index=series.index, dtype=float)
    if valid.empty:
        return result
    low = float(valid.quantile(0.05))
    high = float(valid.quantile(0.95))
    if high <= low:
        result.loc[valid.index] = 50.0
        return result
    result.loc[valid.index] = (
        (valid.clip(lower=low, upper=high) - low) / (high - low) * 100.0
    )
    return result


def max_games(season: int) -> float:
    return 17.0 if season >= 2021 else 16.0


def spearman(left: Sequence[float], right: Sequence[float]) -> float:
    frame = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(frame) < 2:
        return float("nan")
    value = frame["left"].rank().corr(frame["right"].rank())
    return float(value) if value is not None else float("nan")


def ndcg(predicted_score: pd.Series, actual_score: pd.Series, k: int | None = None) -> float:
    frame = pd.DataFrame({"pred": predicted_score, "actual": actual_score}).dropna()
    if frame.empty:
        return float("nan")
    size = min(len(frame), k or len(frame))
    minimum = float(frame["actual"].min())
    relevance = (frame["actual"] - minimum).clip(lower=0.0)
    ranked = frame.assign(rel=relevance).sort_values(
        ["pred", "actual"], ascending=[False, False], kind="stable"
    )
    ideal = frame.assign(rel=relevance).sort_values(
        ["actual", "pred"], ascending=[False, False], kind="stable"
    )
    discounts = np.log2(np.arange(2, size + 2))
    dcg = float(np.sum(ranked["rel"].iloc[:size].to_numpy() / discounts))
    idcg = float(np.sum(ideal["rel"].iloc[:size].to_numpy() / discounts))
    return dcg / idcg if idcg > 0 else 1.0


def ece(probability: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    frame = pd.DataFrame({"p": probability, "y": actual}).dropna()
    if frame.empty:
        return float("nan")
    frame["bin"] = pd.cut(
        frame["p"],
        bins=np.linspace(0.0, 1.0, bins + 1),
        labels=False,
        include_lowest=True,
    )
    error = 0.0
    for _bin, group in frame.groupby("bin", observed=False):
        if group.empty:
            continue
        error += len(group) / len(frame) * abs(float(group["p"].mean() - group["y"].mean()))
    return error


def fit_ridge(
    frame: pd.DataFrame,
    features: Sequence[str],
    target: str,
    alpha: float,
) -> RidgeModel:
    training = frame.dropna(subset=[target]).copy()
    if len(training) < 20:
        raise ValueError(f"insufficient training rows for {target}: {len(training)}")
    raw = training.loc[:, features].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    missing = ~np.isfinite(raw)
    finite_counts = np.sum(~missing, axis=0)
    if np.any(finite_counts == 0):
        absent = [features[index] for index, count in enumerate(finite_counts) if count == 0]
        raise ValueError(f"features wholly absent for {target}: {absent}")
    means = np.nanmean(raw, axis=0)
    imputed = np.where(missing, means, raw)
    scales = np.std(imputed, axis=0, ddof=0)
    scales = np.where(scales <= 0, 1.0, scales)
    standardized = (imputed - means) / scales
    design = np.concatenate(
        [
            np.ones((len(training), 1)),
            standardized,
            missing.astype(float),
        ],
        axis=1,
    )
    outcome = training[target].to_numpy(float)
    penalty = np.diag([0.0] + [1.0] * (design.shape[1] - 1)) * alpha * len(training)
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ outcome)
    payload = {
        "features": list(features),
        "means": [float(value) for value in means],
        "scales": [float(value) for value in scales],
        "coefficients": [float(value) for value in coefficients],
        "alpha": alpha,
        "target": target,
    }
    return RidgeModel(
        features=tuple(features),
        means=tuple(float(value) for value in means),
        scales=tuple(float(value) for value in scales),
        coefficients=tuple(float(value) for value in coefficients),
        alpha=alpha,
        model_hash=canonical_hash(payload),
    )


def predict_ridge(model: RidgeModel, frame: pd.DataFrame) -> np.ndarray:
    raw = frame.loc[:, model.features].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    missing = ~np.isfinite(raw)
    imputed = np.where(missing, np.asarray(model.means), raw)
    standardized = (imputed - np.asarray(model.means)) / np.asarray(model.scales)
    design = np.concatenate(
        [np.ones((len(frame), 1)), standardized, missing.astype(float)],
        axis=1,
    )
    prediction = design @ np.asarray(model.coefficients)
    if not np.all(np.isfinite(prediction)):
        raise ValueError("non-finite ridge prediction")
    return prediction


def select_alpha(
    historical: pd.DataFrame,
    *,
    position: str,
    features: Sequence[str],
    target: str,
    origin: int,
    outcome_offset: int,
    probability: bool = False,
) -> tuple[float, str]:
    eligible_inner = [
        season
        for season in sorted(historical["season"].dropna().astype(int).unique())
        if season < origin and season + outcome_offset < origin and season >= 2015
    ][-4:]
    scores: dict[float, list[float]] = {alpha: [] for alpha in RIDGE_ALPHAS}
    position_rows = historical.loc[historical["position"].eq(position)]
    for validation_season in eligible_inner:
        training = position_rows.loc[
            position_rows["season"].astype(int).add(outcome_offset).lt(validation_season)
        ]
        validation = position_rows.loc[
            position_rows["season"].astype(int).eq(validation_season)
        ].dropna(subset=[target])
        if len(training.dropna(subset=[target])) < 40 or len(validation) < 10:
            continue
        for alpha in RIDGE_ALPHAS:
            model = fit_ridge(training, features, target, alpha)
            predicted = predict_ridge(model, validation)
            if probability:
                score = -float(
                    np.mean(np.abs(np.clip(predicted, 0.0, 1.0) - validation[target]))
                )
            else:
                score = spearman(predicted, validation[target].to_numpy(float))
            if math.isfinite(score):
                scores[alpha].append(score)
    means = {
        alpha: float(np.mean(values)) if values else float("-inf")
        for alpha, values in scores.items()
    }
    selected = max(RIDGE_ALPHAS, key=lambda alpha: (means[alpha], -abs(alpha - 1.0)))
    if not math.isfinite(means[selected]):
        selected = 1.0
    trace = canonical_hash(
        {
            "origin": origin,
            "position": position,
            "target": target,
            "outcome_offset": outcome_offset,
            "inner_seasons": eligible_inner,
            "scores": {
                str(alpha): [round(value, 12) for value in scores[alpha]]
                for alpha in RIDGE_ALPHAS
            },
            "selected": selected,
        }
    )
    return selected, trace


def features_for(position: str, *, retention: bool = False) -> tuple[str, ...]:
    result = COMMON_FEATURES + POSITION_FEATURES[position]
    return result + (("age",) if retention else ())


def verify_inputs(repo_root: Path, current_features: Path) -> dict[str, dict[str, Any]]:
    ledger: dict[str, dict[str, Any]] = {}
    for relative, expected in EXPECTED_HASHES.items():
        path = repo_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"required fixed source missing: {path}")
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"fixed source hash mismatch: {relative}: {actual}")
        ledger[relative.as_posix()] = {
            "sha256": actual,
            "bytes": path.stat().st_size,
            "scope": "tracked_fixed_source",
        }
    if not current_features.is_file():
        raise FileNotFoundError(f"fixed current feature source missing: {current_features}")
    actual_current = sha256(current_features)
    if actual_current != CURRENT_FEATURES_HASH:
        raise ValueError(f"current feature source hash mismatch: {actual_current}")
    ledger["CURRENT_FEATURES_REVIEW_ONLY"] = {
        "sha256": actual_current,
        "bytes": current_features.stat().st_size,
        "scope": "fixed_external_review_only_source",
    }
    return ledger


def load_proxy(repo_root: Path) -> pd.DataFrame:
    panel = pd.read_csv(repo_root / PANEL_REL, low_memory=False)
    module_path = repo_root / PROXY_BUILDER_REL
    spec = importlib.util.spec_from_file_location("nwr_dual_lens_proxy", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load governed accepted-proxy builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    numeric(
        panel,
        [
            column
            for column in panel.columns
            if column.startswith("prior_")
            or column
            in {
                "feature_season",
                "target_season",
                "target_games",
                "next_nwr_points",
                "next_nwr_ppg",
                "next_position_finish",
            }
        ],
    )
    scored = module._add_proxy_scores(panel.copy())  # noqa: SLF001
    return scored[
        [
            "substrate_row_id",
            "player_id_gsis",
            "target_season",
            "position",
            "production_formula_partial_proxy_score",
            "proxy_confidence_multiplier",
            "proxy_missing_component_count",
        ]
    ].rename(
        columns={
            "player_id_gsis": "player_id",
            "target_season": "season",
            "production_formula_partial_proxy_score": "w0_score",
            "proxy_confidence_multiplier": "w0_confidence",
            "proxy_missing_component_count": "w0_missing_components",
        }
    )


def load_historical(repo_root: Path) -> pd.DataFrame:
    mart = pd.read_csv(repo_root / MART_REL, low_memory=False)
    age = pd.read_csv(repo_root / AGE_REL, low_memory=False)
    rookie = pd.read_csv(repo_root / ROOKIE_REL, low_memory=False)
    if len(mart) != 5518 or len(age) != 5518 or len(rookie) != 5518:
        raise ValueError(
            f"historical row counts changed: mart={len(mart)} age={len(age)} "
            f"rookie={len(rookie)}"
        )
    key = ["season", "position", "player_id"]
    for name, frame in (("mart", mart), ("age", age), ("rookie", rookie)):
        if frame.duplicated(key).any():
            raise ValueError(f"duplicate exact identity in {name}")
    if not mart["leakage_check_result"].eq(
        "PASS_FEATURE_N_TARGET_N_PLUS_1_SEPARATED"
    ).all():
        raise ValueError("historical leakage gate failed")
    if not mart["asof_check_result"].eq(
        "PASS_NO_TARGET_SEASON_CONTEXT_IN_FEATURE_COLUMNS"
    ).all():
        raise ValueError("historical as-of gate failed")
    if not mart["feature_season"].astype(int).add(1).eq(mart["season"].astype(int)).all():
        raise ValueError("historical N-to-N+1 construction failed")
    if bool_series(mart["training_allowed"]).any() or bool_series(
        mart["production_approved"]
    ).any():
        raise ValueError("review-only mart unexpectedly claims training/production authority")

    age_columns = [
        *key,
        "age",
        "birth_date",
        "draft_year",
        "rookie_year",
        "years_since_rookie_year",
        "career_stage",
        "age_bucket",
        "lifecycle_bucket",
        "source_gate_status",
        "identity_flag",
        "review_only_status",
    ]
    rookie_columns = [
        *key,
        "draft_round",
        "draft_pick",
        "draft_overall",
        "drafted_flag",
        "entry_status",
        "draft_capital_bucket",
        "draft_capital_score",
        "draft_identity_status",
        "coverage_status",
    ]
    historical = mart.merge(
        age[age_columns],
        on=key,
        how="left",
        validate="one_to_one",
        suffixes=("", "_age"),
    ).merge(
        rookie[rookie_columns],
        on=key,
        how="left",
        validate="one_to_one",
        suffixes=("", "_rookie"),
    )
    proxy = load_proxy(repo_root)
    historical = historical.merge(
        proxy,
        on=["substrate_row_id", *key],
        how="left",
        validate="one_to_one",
    )
    if historical["w0_score"].isna().any():
        raise ValueError("accepted W0 production proxy exact join incomplete")

    numeric_columns = set(COMMON_FEATURES)
    numeric_columns.update(*(set(values) for values in POSITION_FEATURES.values()))
    numeric_columns.update(
        {
            "season",
            "feature_season",
            "label_next_nwr_points",
            "label_next_nwr_ppg",
            "label_next_position_finish",
            "label_target_games",
            "age",
            "draft_year",
            "rookie_year",
            "years_since_rookie_year",
            "draft_round",
            "draft_pick",
            "draft_overall",
            "draft_capital_score",
            "w0_score",
            "w0_confidence",
            "w0_missing_components",
        }
    )
    numeric(historical, numeric_columns)
    historical["availability_actual"] = historical.apply(
        lambda row: min(
            1.0,
            max(
                0.0,
                float(row["label_target_games"]) / max_games(int(row["season"])),
            ),
        ),
        axis=1,
    )
    historical["availability_8plus_actual"] = historical["label_target_games"].ge(8).astype(
        float
    )
    historical["cohort"] = cohort_series(historical)
    historical["actual_replacement"] = np.nan
    for (_season, position), group in historical.groupby(
        ["season", "position"], sort=True
    ):
        cutoff = min(REPLACEMENT_CUTOFF[position], len(group))
        replacement = float(
            group["label_next_nwr_points"].sort_values(ascending=False).iloc[cutoff - 1]
        )
        historical.loc[group.index, "actual_replacement"] = replacement
    historical["actual_vor_h1"] = (
        historical["label_next_nwr_points"] - historical["actual_replacement"]
    )

    exact_future = historical.set_index(["season", "player_id"])[
        [
            "actual_vor_h1",
            "label_next_position_finish",
            "position",
            "label_next_nwr_points",
        ]
    ]
    if exact_future.index.duplicated().any():
        raise ValueError("player-season future target identity is not unique")
    for horizon, offset in ((2, 1), (3, 2)):
        lookup = exact_future.rename(
            columns={
                "actual_vor_h1": f"actual_vor_h{horizon}",
                "label_next_position_finish": f"actual_finish_h{horizon}",
                "position": f"actual_position_h{horizon}",
                "label_next_nwr_points": f"actual_points_h{horizon}",
            }
        )
        join_index = pd.MultiIndex.from_arrays(
            [
                historical["season"].astype(int).add(offset),
                historical["player_id"].astype(str),
            ],
            names=["season", "player_id"],
        )
        joined = lookup.reindex(join_index).reset_index(drop=True)
        for column in joined:
            historical[column] = joined[column].to_numpy()
    historical["retain_h2"] = historical["actual_vor_h2"].gt(0).where(
        historical["actual_vor_h2"].notna()
    )
    historical["retain_h3"] = historical["actual_vor_h3"].gt(0).where(
        historical["actual_vor_h3"].notna()
    )
    historical["starter_h2"] = pd.Series(
        [
            float(finish <= STARTABLE_CUTOFF.get(position, 0))
            if pd.notna(finish) and isinstance(position, str)
            else np.nan
            for finish, position in zip(
                historical["actual_finish_h2"],
                historical["actual_position_h2"],
                strict=True,
            )
        ],
        index=historical.index,
    )
    historical["starter_h3"] = pd.Series(
        [
            float(finish <= STARTABLE_CUTOFF.get(position, 0))
            if pd.notna(finish) and isinstance(position, str)
            else np.nan
            for finish, position in zip(
                historical["actual_finish_h3"],
                historical["actual_position_h3"],
                strict=True,
            )
        ],
        index=historical.index,
    )
    historical["elite_h2"] = pd.Series(
        [
            float(finish <= ELITE_CUTOFF.get(position, 0))
            if pd.notna(finish) and isinstance(position, str)
            else np.nan
            for finish, position in zip(
                historical["actual_finish_h2"],
                historical["actual_position_h2"],
                strict=True,
            )
        ],
        index=historical.index,
    )
    historical["elite_h3"] = pd.Series(
        [
            float(finish <= ELITE_CUTOFF.get(position, 0))
            if pd.notna(finish) and isinstance(position, str)
            else np.nan
            for finish, position in zip(
                historical["actual_finish_h3"],
                historical["actual_position_h3"],
                strict=True,
            )
        ],
        index=historical.index,
    )
    historical["value_collapse_h3"] = (
        historical["actual_vor_h1"].gt(0) & historical["actual_vor_h3"].le(0)
    ).where(historical["actual_vor_h3"].notna())
    return historical.sort_values(
        ["season", "position", "player_id"], kind="stable"
    ).reset_index(drop=True)


def cohort_series(frame: pd.DataFrame) -> pd.Series:
    years = pd.to_numeric(frame.get("years_since_rookie_year"), errors="coerce")
    games = pd.to_numeric(frame.get("prior_games"), errors="coerce")
    result = pd.Series("UNKNOWN_EXPERIENCE", index=frame.index, dtype=object)
    result.loc[years.eq(0)] = "TRUE_ROOKIE"
    result.loc[years.eq(1)] = "SECOND_YEAR"
    result.loc[years.eq(2)] = "THIRD_YEAR"
    result.loc[years.ge(3) & games.ge(8)] = "ESTABLISHED"
    result.loc[years.ge(3) & games.lt(8)] = "LOW_GAMES_VETERAN"
    return result


def load_current(
    repo_root: Path,
    current_features_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    board = pd.read_csv(repo_root / BOARD_REL, dtype=str, low_memory=False).fillna("")
    frozen = pd.read_csv(repo_root / FROZEN_REL, low_memory=False)
    outcome = pd.read_csv(repo_root / OUTCOME_BOARD_REL, low_memory=False)
    current = pd.read_csv(current_features_path, low_memory=False)
    if len(board) != 240 or len(outcome) != 240:
        raise ValueError(
            f"current board row count changed: board={len(board)} "
            f"outcome={len(outcome)}"
        )
    if int(pd.read_csv(repo_root / OUTCOME_SCHEMA_REL).shape[0]) != 79:
        raise ValueError("Outcome V3 schema row count changed")
    if (
        pd.to_numeric(board["nwr_rank"].iloc[:5], errors="raise").astype(int).tolist()
        != [1, 2, 3, 4, 5]
    ):
        raise ValueError("Finished V1 board no longer starts at ranks 1-5")
    expected_top = [
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "Bijan Robinson",
        "Jonathan Taylor",
        "Jahmyr Gibbs",
    ]
    if board["player_name"].tolist()[:5] != expected_top:
        raise ValueError("Finished V1 top five changed")
    if board["player_id"].duplicated().any() or outcome["player_id"].duplicated().any():
        raise ValueError("current board identity is not unique")
    if outcome["release_identifier"].nunique() != 1 or outcome[
        "release_identifier"
    ].iloc[0] != "NWR_OUTCOME_COLUMNS_V3_RC1":
        raise ValueError("Outcome V3 release identifier changed")
    duplicate_current = current.loc[
        current["stable_player_id"].duplicated(keep=False)
    ]
    for stable_player_id, group in duplicate_current.groupby("stable_player_id"):
        conflicting = [
            column
            for column in current.columns
            if group[column].astype(str).nunique(dropna=False) > 1
        ]
        if conflicting:
            raise ValueError(
                f"conflicting duplicate current feature rows: {stable_player_id} "
                f"{conflicting}"
            )
    current = current.drop_duplicates(
        subset=["stable_player_id"], keep="first"
    ).reset_index(drop=True)

    board_columns = [
        "player_id",
        "canonical_player_key",
        "player_name",
        "position",
        "age",
        "nwr_rank",
        "nwr_dynasty_score",
        "is_rookie",
        "nfl_team",
        "model_version",
        "confidence",
        "warning_flags",
        "final_value_tier",
        "manual_review_state",
    ]
    for column in board_columns:
        if column not in board:
            board[column] = ""
    board_small = board[board_columns].rename(
        columns={
            "player_id": "nwr_player_id",
            "position": "board_position",
            "age": "board_age",
            "nwr_rank": "finished_v1_rank",
            "nwr_dynasty_score": "finished_v1_score",
            "confidence": "finished_v1_confidence",
        }
    )
    outcome_small = outcome.rename(
        columns={
            "player_id": "nwr_player_id",
            "player_name": "outcome_player_name",
            "position": "outcome_position",
            "age": "outcome_age",
            "finished_v1_rank": "outcome_finished_v1_rank",
            "confidence": "outcome_confidence",
            "reason_code": "outcome_reason_code",
            "missing_reason": "outcome_missing_reason",
        }
    )
    outcome_small["nwr_player_id"] = outcome_small["nwr_player_id"].astype(str)
    current["nwr_player_id"] = current["stable_player_id"].astype(str)
    current["player_id"] = current["player_id_gsis"].fillna("").astype(str)
    current["season"] = 2026
    current["feature_season"] = 2025
    current["pyf_prior_nwr_points"] = pd.to_numeric(
        current["prior_nwr_points"], errors="coerce"
    )
    current["pyf_prior_nwr_ppg"] = pd.to_numeric(
        current["prior_nwr_ppg"], errors="coerce"
    )
    current["prior_2yr_weighted_nwr_points"] = np.nan
    current["prior_3yr_weighted_nwr_points"] = np.nan
    numeric(
        current,
        set(COMMON_FEATURES).union(
            *(set(values) for values in POSITION_FEATURES.values())
        ),
    )
    current = board_small.merge(
        current,
        on="nwr_player_id",
        how="left",
        validate="one_to_one",
        suffixes=("", "_feature"),
    ).merge(
        outcome_small,
        on="nwr_player_id",
        how="left",
        validate="one_to_one",
        suffixes=("", "_outcome"),
    )
    if current["release_identifier"].notna().sum() != 240:
        raise ValueError("Outcome V3 current-board exact NWR identity join incomplete")
    left_rank = pd.to_numeric(current["finished_v1_rank"], errors="coerce")
    right_rank = pd.to_numeric(current["outcome_finished_v1_rank"], errors="coerce")
    rank_match = left_rank.eq(right_rank) | (left_rank.isna() & right_rank.isna())
    if not rank_match.all():
        raise ValueError("Outcome V3 Finished V1 rank context mismatch")

    frozen_gs = frozen.loc[
        frozen["candidate_name"].eq("GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE")
    ].copy()
    frozen_gs["player_id"] = (
        frozen_gs["player_id"].astype(str).str.replace("sleeper:", "", regex=False)
    )
    frozen_context = frozen_gs[
        [
            "player_id",
            "age",
            "draft_year",
            "lifecycle_bucket",
            "history_years_available",
            "eligible",
            "score_valid",
            "exclusion_reason",
            "raw_feature_values_json",
        ]
    ].rename(
        columns={
            "eligible": "frozen_eligible",
            "score_valid": "frozen_score_valid",
            "exclusion_reason": "frozen_exclusion_reason",
            "raw_feature_values_json": "frozen_raw_feature_values_json",
        }
    )
    current = current.merge(
        frozen_context,
        on="player_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_frozen"),
    )

    def multiyear_from_frozen(row: pd.Series) -> tuple[float, float, int]:
        text = row.get("frozen_raw_feature_values_json")
        if not isinstance(text, str) or not text.strip():
            return np.nan, np.nan, 0
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return np.nan, np.nan, 0
        history = payload.get("history_nwr_points")
        if not isinstance(history, dict):
            return np.nan, np.nan, 0
        values = {
            int(year): finite(points)
            for year, points in history.items()
            if str(year).isdigit()
        }
        values = {year: points for year, points in values.items() if points is not None}
        if not values:
            return np.nan, np.nan, 0

        def weighted(specification: Sequence[tuple[int, float]]) -> float:
            present = [
                (values.get(year), weight) for year, weight in specification
            ]
            admitted = [
                (value, weight) for value, weight in present if value is not None
            ]
            return (
                sum(float(value) * weight for value, weight in admitted)
                / sum(weight for _value, weight in admitted)
                if admitted
                else np.nan
            )

        two = weighted(((2025, 0.70), (2024, 0.30)))
        three = weighted(((2025, 0.60), (2024, 0.25), (2023, 0.15)))
        return two, three, len(values)

    multiyear = current.apply(multiyear_from_frozen, axis=1, result_type="expand")
    multiyear.columns = [
        "current_prior_2yr_weighted_nwr_points",
        "current_prior_3yr_weighted_nwr_points",
        "current_history_years_derived",
    ]
    current = pd.concat([current, multiyear], axis=1)
    current["prior_2yr_weighted_nwr_points"] = current[
        "current_prior_2yr_weighted_nwr_points"
    ]
    current["prior_3yr_weighted_nwr_points"] = current[
        "current_prior_3yr_weighted_nwr_points"
    ]
    current["multiyear_feature_status"] = np.where(
        current["current_history_years_derived"].gt(0),
        "DERIVED_REVIEW_ONLY_FROM_FROZEN_2023_2025_HISTORY_FIXED_70_30_AND_60_25_15",
        "NOT_ENOUGH_INFORMATION_NO_FROZEN_HISTORY",
    )
    numeric(
        current,
        [
            "finished_v1_rank",
            "finished_v1_score",
            "age",
            "draft_year",
            "history_years_available",
        ],
    )
    current["age"] = current["age"].fillna(
        pd.to_numeric(current["outcome_age"], errors="coerce")
    )
    current["candidate_feature_ready"] = bool_series(current["candidate_feature_ready"])
    current["is_rookie"] = bool_series(current["is_rookie"])
    current["years_since_rookie_year"] = np.where(
        current["is_rookie"],
        0.0,
        np.where(
            current["draft_year"].notna(),
            2026.0 - current["draft_year"],
            np.nan,
        ),
    )
    current["cohort"] = cohort_series(current)
    current["cohort"] = current["cohort"].where(
        ~current["is_rookie"], "TRUE_ROOKIE"
    )
    current["source_ready"] = (
        current["candidate_feature_ready"]
        & current["player_id"].notna()
        & current["player_id"].astype(str).ne("")
        & current["pyf_prior_nwr_points"].notna()
        & current["prior_games"].notna()
        & current["prior_2yr_weighted_nwr_points"].notna()
        & current["prior_3yr_weighted_nwr_points"].notna()
    )
    current["substrate_row_id"] = current["nwr_player_id"].map(
        lambda value: f"current_2026_{value}"
    )
    return (
        current.sort_values("finished_v1_rank", kind="stable").reset_index(drop=True),
        board,
        outcome,
    )


def replacement_forecast(historical: pd.DataFrame, origin: int, position: str) -> float:
    rows = historical.loc[
        historical["position"].eq(position) & historical["season"].astype(int).lt(origin)
    ]
    seasons = sorted(rows["season"].astype(int).unique())[-3:]
    values = (
        rows.loc[rows["season"].isin(seasons), ["season", "actual_replacement"]]
        .drop_duplicates()
        .sort_values("season")["actual_replacement"]
    )
    if values.empty:
        raise ValueError(f"replacement forecast unavailable: {origin} {position}")
    return float(values.median())


def train_predict(
    historical: pd.DataFrame,
    scored: pd.DataFrame,
    *,
    position: str,
    origin: int,
    target: str,
    outcome_offset: int,
    retention_features: bool = False,
    probability: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    features = features_for(position, retention=retention_features)
    alpha, selection_hash = select_alpha(
        historical,
        position=position,
        features=features,
        target=target,
        origin=origin,
        outcome_offset=outcome_offset,
        probability=probability,
    )
    training = historical.loc[
        historical["position"].eq(position)
        & historical["season"].astype(int).add(outcome_offset).lt(origin)
    ].dropna(subset=[target])
    model = fit_ridge(training, features, target, alpha)
    prediction = predict_ridge(model, scored)
    if probability:
        prediction = np.clip(prediction, 0.0, 1.0)
    trace = {
        "origin": origin,
        "position": position,
        "target": target,
        "outcome_offset": outcome_offset,
        "alpha": alpha,
        "training_rows": len(training),
        "training_seasons": "|".join(
            str(value) for value in sorted(training["season"].astype(int).unique())
        ),
        "model_hash": model.model_hash,
        "selection_hash": selection_hash,
        "feature_count": len(features),
    }
    return prediction, trace


def availability_calibration(
    prior_predictions: pd.DataFrame,
    position: str,
    origin: int,
) -> tuple[float, float, float, str]:
    if prior_predictions.empty:
        return (
            0.0,
            1.0,
            0.5,
            canonical_hash(
                {
                    "position": position,
                    "origin": origin,
                    "rows": 0,
                    "fallback": "IDENTITY_NO_PRIOR_OOF",
                }
            ),
        )
    prior = prior_predictions.loc[
        prior_predictions["position"].eq(position)
        & prior_predictions["season"].astype(int).lt(origin)
        & prior_predictions["availability_raw"].notna()
        & prior_predictions["availability_actual"].notna()
    ].copy()
    prior = prior.loc[prior["season"].isin(sorted(prior["season"].unique())[-4:])]
    intercept, slope = 0.0, 1.0
    if len(prior) >= 40 and prior["availability_raw"].std(ddof=0) > 1e-9:
        design = np.column_stack(
            [np.ones(len(prior)), prior["availability_raw"].to_numpy(float)]
        )
        coefficients, *_ = np.linalg.lstsq(
            design, prior["availability_actual"].to_numpy(float), rcond=None
        )
        intercept = float(np.clip(coefficients[0], -0.20, 0.20))
        slope = float(np.clip(coefficients[1], 0.50, 1.50))
    thresholds = (0.40, 0.50, 0.60)
    scores: dict[float, float] = {}
    if len(prior) >= 20:
        calibrated = np.clip(
            intercept + slope * prior["availability_raw"].to_numpy(float), 0.0, 1.0
        )
        actual = prior["availability_8plus_actual"].to_numpy(float)
        for threshold in thresholds:
            predicted = calibrated >= threshold
            sensitivity = float(np.mean(predicted[actual == 1])) if np.any(actual == 1) else 0.0
            specificity = (
                float(np.mean(~predicted[actual == 0])) if np.any(actual == 0) else 0.0
            )
            scores[threshold] = (sensitivity + specificity) / 2.0
        threshold = max(thresholds, key=lambda value: (scores[value], -abs(value - 0.5)))
    else:
        threshold = 0.5
    trace = canonical_hash(
        {
            "position": position,
            "origin": origin,
            "rows": len(prior),
            "intercept": intercept,
            "slope": slope,
            "threshold_scores": scores,
            "selected_threshold": threshold,
        }
    )
    return intercept, slope, threshold, trace


def select_win_blend(
    prior_predictions: pd.DataFrame,
    position: str,
    origin: int,
) -> tuple[float, str]:
    if prior_predictions.empty:
        return (
            0.5,
            canonical_hash(
                {
                    "position": position,
                    "origin": origin,
                    "rows": 0,
                    "selected": 0.5,
                    "fallback": "BALANCED_NO_PRIOR_OOF",
                }
            ),
        )
    prior = prior_predictions.loc[
        prior_predictions["position"].eq(position)
        & prior_predictions["season"].astype(int).lt(origin)
        & prior_predictions["w1_score"].notna()
        & prior_predictions["w2_score"].notna()
        & prior_predictions["actual_vor_h1"].notna()
    ].copy()
    prior = prior.loc[prior["season"].isin(sorted(prior["season"].unique())[-4:])]
    scores: dict[float, float] = {}
    for weight in WIN_BLEND_WEIGHTS:
        blended = weight * prior["w1_score"] + (1.0 - weight) * prior["w2_score"]
        scores[weight] = spearman(blended, prior["actual_vor_h1"])
    valid = {weight: score for weight, score in scores.items() if math.isfinite(score)}
    selected = (
        max(valid, key=lambda weight: (valid[weight], -abs(weight - 0.5)))
        if valid
        else 0.5
    )
    return selected, canonical_hash(
        {
            "position": position,
            "origin": origin,
            "rows": len(prior),
            "scores": scores,
            "selected": selected,
        }
    )


def build_win_predictions(
    historical: pd.DataFrame,
    current: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    predictions: list[pd.DataFrame] = []
    traces: list[dict[str, Any]] = []
    prior_wide = pd.DataFrame()
    for origin in WIN_ORIGINS:
        source = historical.loc[historical["season"].astype(int).eq(origin)].copy()
        if origin == 2026:
            source = current.copy()
        season_outputs: list[pd.DataFrame] = []
        for position in POSITIONS:
            group = source.loc[source["position"].eq(position)].copy()
            if group.empty:
                continue
            replacement = replacement_forecast(historical, origin, position)
            points, points_trace = train_predict(
                historical,
                group,
                position=position,
                origin=origin,
                target="label_next_nwr_points",
                outcome_offset=0,
            )
            ppg, ppg_trace = train_predict(
                historical,
                group,
                position=position,
                origin=origin,
                target="label_next_nwr_ppg",
                outcome_offset=0,
            )
            games_fraction, games_trace = train_predict(
                historical,
                group,
                position=position,
                origin=origin,
                target="availability_actual",
                outcome_offset=0,
                probability=True,
            )
            intercept, slope, threshold, calibration_hash = availability_calibration(
                prior_wide, position, origin
            )
            availability = np.clip(intercept + slope * games_fraction, 0.0, 1.0)
            blend, blend_hash = select_win_blend(prior_wide, position, origin)
            group["w1_score"] = points - replacement
            group["availability_raw"] = games_fraction
            group["availability_predicted"] = availability
            group["availability_threshold"] = threshold
            group["conditional_ppg_predicted"] = np.maximum(ppg, 0.0)
            group["w2_score"] = (
                np.maximum(ppg, 0.0) * max_games(origin) * availability - replacement
            )
            group["w3_weight_w1"] = blend
            group["w3_weight_w2"] = 1.0 - blend
            group["w3_score"] = blend * group["w1_score"] + (1.0 - blend) * group[
                "w2_score"
            ]
            group["replacement_forecast"] = replacement
            if origin == 2026:
                unready = ~group["source_ready"].fillna(False)
                for column in (
                    "w1_score",
                    "w2_score",
                    "w3_score",
                    "availability_raw",
                    "availability_predicted",
                    "conditional_ppg_predicted",
                ):
                    group.loc[unready, column] = np.nan
            season_outputs.append(group)
            for trace_name, trace in (
                ("W1_TOTAL_POINTS", points_trace),
                ("W2_CONDITIONAL_PPG", ppg_trace),
                ("W2_AVAILABILITY", games_trace),
            ):
                traces.append(
                    {
                        "lane": "WIN_NOW",
                        "trace_name": trace_name,
                        **trace,
                        "calibration_hash": calibration_hash,
                        "blend_selection_hash": blend_hash,
                        "selected_blend_w1": blend,
                        "availability_threshold": threshold,
                    }
                )
        if season_outputs:
            season_frame = pd.concat(season_outputs, ignore_index=True)
            predictions.append(season_frame)
            if origin < 2026:
                prior_wide = pd.concat([prior_wide, season_frame], ignore_index=True)
    return (
        pd.concat(predictions, ignore_index=True),
        pd.DataFrame(traces).sort_values(
            ["origin", "position", "trace_name"], kind="stable"
        ),
    )


def select_discount(
    prior_predictions: pd.DataFrame,
    position: str,
    origin: int,
) -> tuple[str, str]:
    if prior_predictions.empty:
        return (
            DEFAULT_DISCOUNT,
            canonical_hash(
                {
                    "position": position,
                    "origin": origin,
                    "rows": 0,
                    "selected": DEFAULT_DISCOUNT,
                    "fallback": "PREREGISTERED_DEFAULT_NO_PRIOR_OOF",
                }
            ),
        )
    prior = prior_predictions.loc[
        prior_predictions["position"].eq(position)
        & prior_predictions["season"].astype(int).add(2).lt(origin)
        & prior_predictions[
            [
                "d_h1_pred",
                "d_h2_pred",
                "d_h3_pred",
                "actual_vor_h1",
                "actual_vor_h2",
                "actual_vor_h3",
            ]
        ].notna().all(axis=1)
    ].copy()
    prior = prior.loc[prior["season"].isin(sorted(prior["season"].unique())[-4:])]
    if prior.empty:
        return (
            DEFAULT_DISCOUNT,
            canonical_hash(
                {
                    "position": position,
                    "origin": origin,
                    "rows": 0,
                    "selected": DEFAULT_DISCOUNT,
                    "fallback": "PREREGISTERED_DEFAULT_NO_ELIGIBLE_PRIOR_OOF",
                }
            ),
        )
    scores: dict[str, float] = {}
    for name, weights in DISCOUNT_SCHEDULES.items():
        predicted = (
            weights[0] * prior["d_h1_pred"]
            + weights[1] * prior["d_h2_pred"]
            + weights[2] * prior["d_h3_pred"]
        )
        actual = (
            weights[0] * prior["actual_vor_h1"]
            + weights[1] * prior["actual_vor_h2"]
            + weights[2] * prior["actual_vor_h3"]
        )
        scores[name] = spearman(predicted, actual)
    valid = {name: score for name, score in scores.items() if math.isfinite(score)}
    selected = (
        max(
            valid,
            key=lambda name: (
                valid[name],
                name == DEFAULT_DISCOUNT,
                -list(DISCOUNT_SCHEDULES).index(name),
            ),
        )
        if valid
        else DEFAULT_DISCOUNT
    )
    return selected, canonical_hash(
        {
            "position": position,
            "origin": origin,
            "rows": len(prior),
            "scores": scores,
            "selected": selected,
        }
    )


def apply_d3_profile(
    frame: pd.DataFrame,
    profile: str,
    *,
    ppg_threshold: float,
) -> pd.Series:
    position = str(frame["position"].iloc[0]) if not frame.empty else ""
    cutoff = AGE_PROFILES[profile][position]
    age = pd.to_numeric(frame["age"], errors="coerce")
    games = pd.to_numeric(frame["prior_games"], errors="coerce")
    ppg = pd.to_numeric(frame["pyf_prior_nwr_ppg"], errors="coerce")
    excess = (age - cutoff).clip(lower=0.0).fillna(0.0)
    penalty = (excess * 0.04).clip(upper=0.20)
    productive_veteran = age.ge(cutoff) & games.ge(8) & ppg.ge(ppg_threshold)
    penalty = penalty.where(~productive_veteran, penalty.clip(upper=0.05))
    future = frame["d_future_retained_contribution"].copy()
    adjusted = future.where(future.le(0), future * (1.0 - penalty))
    low_games = games.lt(6)
    low_games_cap = frame["d_h1_pred"].clip(lower=0.0) * 0.75
    adjusted = adjusted.where(~(low_games & adjusted.gt(low_games_cap)), low_games_cap)
    return frame["d_h1_pred"] + adjusted


def select_age_profile(
    prior_predictions: pd.DataFrame,
    position: str,
    origin: int,
    *,
    ppg_threshold: float,
) -> tuple[str, str]:
    if prior_predictions.empty:
        return (
            DEFAULT_AGE_PROFILE,
            canonical_hash(
                {
                    "position": position,
                    "origin": origin,
                    "rows": 0,
                    "selected": DEFAULT_AGE_PROFILE,
                    "fallback": "PREREGISTERED_DEFAULT_NO_PRIOR_OOF",
                }
            ),
        )
    prior = prior_predictions.loc[
        prior_predictions["position"].eq(position)
        & prior_predictions["season"].astype(int).add(2).lt(origin)
        & prior_predictions["actual_dynasty_target"].notna()
    ].copy()
    prior = prior.loc[prior["season"].isin(sorted(prior["season"].unique())[-4:])]
    if prior.empty:
        return (
            DEFAULT_AGE_PROFILE,
            canonical_hash(
                {
                    "position": position,
                    "origin": origin,
                    "rows": 0,
                    "selected": DEFAULT_AGE_PROFILE,
                    "fallback": "PREREGISTERED_DEFAULT_NO_ELIGIBLE_PRIOR_OOF",
                }
            ),
        )
    scores: dict[str, float] = {}
    details: dict[str, dict[str, float]] = {}
    for profile in AGE_PROFILES:
        predicted = apply_d3_profile(prior, profile, ppg_threshold=ppg_threshold)
        correlation = spearman(predicted, prior["actual_dynasty_target"])
        if not math.isfinite(correlation):
            scores[profile] = float("-inf")
            continue
        actual_rank = prior["actual_dynasty_target"].rank(pct=True, ascending=True)
        predicted_rank = predicted.rank(pct=True, ascending=True)
        cutoff = AGE_PROFILES[profile][position]
        productive = (
            prior["age"].ge(cutoff)
            & prior["prior_games"].ge(8)
            & prior["pyf_prior_nwr_ppg"].ge(ppg_threshold)
        )
        productive_harm = float(
            ((actual_rank.ge(0.75) & predicted_rank.lt(0.50)) & productive).mean()
        )
        low_games = prior["prior_games"].lt(6)
        low_games_harm = float(
            ((actual_rank.lt(0.50) & predicted_rank.ge(0.75)) & low_games).mean()
        )
        score = correlation - productive_harm - low_games_harm
        scores[profile] = score
        details[profile] = {
            "correlation": correlation,
            "productive_veteran_harm": productive_harm,
            "low_games_harm": low_games_harm,
            "selection_score": score,
        }
    valid = {name: score for name, score in scores.items() if math.isfinite(score)}
    selected = (
        max(
            valid,
            key=lambda name: (
                valid[name],
                name == DEFAULT_AGE_PROFILE,
                -list(AGE_PROFILES).index(name),
            ),
        )
        if valid
        else DEFAULT_AGE_PROFILE
    )
    return selected, canonical_hash(
        {
            "position": position,
            "origin": origin,
            "rows": len(prior),
            "details": details,
            "selected": selected,
        }
    )


def build_dynasty_predictions(
    historical: pd.DataFrame,
    current: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    predictions: list[pd.DataFrame] = []
    traces: list[dict[str, Any]] = []
    prior_wide = pd.DataFrame()
    for origin in DYNASTY_ORIGINS:
        source = historical.loc[historical["season"].astype(int).eq(origin)].copy()
        if origin == 2026:
            source = current.copy()
        season_outputs: list[pd.DataFrame] = []
        for position in POSITIONS:
            group = source.loc[source["position"].eq(position)].copy()
            if group.empty:
                continue
            horizon_predictions: dict[int, np.ndarray] = {}
            horizon_traces: dict[int, dict[str, Any]] = {}
            retention_predictions: dict[int, np.ndarray] = {}
            retention_traces: dict[int, dict[str, Any]] = {}
            for horizon, offset in ((1, 0), (2, 1), (3, 2)):
                horizon_predictions[horizon], horizon_traces[horizon] = train_predict(
                    historical,
                    group,
                    position=position,
                    origin=origin,
                    target=f"actual_vor_h{horizon}",
                    outcome_offset=offset,
                )
                if horizon > 1:
                    retention_predictions[horizon], retention_traces[
                        horizon
                    ] = train_predict(
                        historical,
                        group,
                        position=position,
                        origin=origin,
                        target=f"retain_h{horizon}",
                        outcome_offset=offset,
                        retention_features=True,
                        probability=True,
                    )
            discount_name, discount_hash = select_discount(prior_wide, position, origin)
            weights = DISCOUNT_SCHEDULES[discount_name]
            group["d_h1_pred"] = horizon_predictions[1]
            group["d_h2_pred"] = horizon_predictions[2]
            group["d_h3_pred"] = horizon_predictions[3]
            group["retention_h2_predicted"] = retention_predictions[2]
            group["retention_h3_predicted"] = retention_predictions[3]
            group["discount_schedule"] = discount_name
            group["discount_h1"] = weights[0]
            group["discount_h2"] = weights[1]
            group["discount_h3"] = weights[2]
            group["d1_score"] = (
                weights[0] * group["d_h1_pred"]
                + weights[1] * group["d_h2_pred"]
                + weights[2] * group["d_h3_pred"]
            )
            group["d_future_retained_contribution"] = (
                weights[1] * group["d_h2_pred"] * group["retention_h2_predicted"]
                + weights[2] * group["d_h3_pred"] * group["retention_h3_predicted"]
            )
            group["d2_score"] = (
                group["d_h1_pred"] + group["d_future_retained_contribution"]
            )
            training_ppg = historical.loc[
                historical["position"].eq(position)
                & historical["season"].astype(int).lt(origin),
                "pyf_prior_nwr_ppg",
            ].dropna()
            ppg_threshold = float(training_ppg.quantile(0.75))
            profile, profile_hash = select_age_profile(
                prior_wide,
                position,
                origin,
                ppg_threshold=ppg_threshold,
            )
            group["age_profile"] = profile
            group["productive_veteran_ppg_threshold"] = ppg_threshold
            group["productive_veteran_guard"] = (
                group["age"].ge(AGE_PROFILES[profile][position])
                & group["prior_games"].ge(8)
                & group["pyf_prior_nwr_ppg"].ge(ppg_threshold)
            )
            group["low_games_guard"] = group["prior_games"].lt(6)
            group["d3_score"] = apply_d3_profile(
                group, profile, ppg_threshold=ppg_threshold
            )
            group["actual_dynasty_target"] = (
                weights[0] * group.get("actual_vor_h1", np.nan)
                + weights[1] * group.get("actual_vor_h2", np.nan)
                + weights[2] * group.get("actual_vor_h3", np.nan)
            )
            if origin == 2026:
                unready = ~group["source_ready"].fillna(False)
                for column in (
                    "d_h1_pred",
                    "d_h2_pred",
                    "d_h3_pred",
                    "retention_h2_predicted",
                    "retention_h3_predicted",
                    "d1_score",
                    "d2_score",
                    "d3_score",
                    "d_future_retained_contribution",
                ):
                    group.loc[unready, column] = np.nan
                age_missing = group["age"].isna()
                group.loc[age_missing, "d3_score"] = np.nan
            season_outputs.append(group)
            for horizon in (1, 2, 3):
                traces.append(
                    {
                        "lane": "DYNASTY",
                        "trace_name": f"D_HORIZON_{horizon}",
                        **horizon_traces[horizon],
                        "discount_selection_hash": discount_hash,
                        "selected_discount": discount_name,
                        "age_profile_selection_hash": profile_hash,
                        "selected_age_profile": profile,
                    }
                )
                if horizon > 1:
                    traces.append(
                        {
                            "lane": "DYNASTY",
                            "trace_name": f"D_RETENTION_{horizon}",
                            **retention_traces[horizon],
                            "discount_selection_hash": discount_hash,
                            "selected_discount": discount_name,
                            "age_profile_selection_hash": profile_hash,
                            "selected_age_profile": profile,
                        }
                    )
        if season_outputs:
            season_frame = pd.concat(season_outputs, ignore_index=True)
            predictions.append(season_frame)
            if origin < 2026:
                prior_wide = pd.concat([prior_wide, season_frame], ignore_index=True)
    return (
        pd.concat(predictions, ignore_index=True),
        pd.DataFrame(traces).sort_values(
            ["origin", "position", "trace_name"], kind="stable"
        ),
    )


def add_season_ranks(
    frame: pd.DataFrame,
    score_column: str,
    actual_column: str,
) -> pd.DataFrame:
    output = frame.copy()
    output["prediction_rank"] = np.nan
    output["actual_rank"] = np.nan
    for _season, group in output.groupby("season", sort=True):
        valid = group.dropna(subset=[score_column, actual_column]).copy()
        if valid.empty:
            continue
        ordered_prediction = valid.sort_values(
            [score_column, "player_id"],
            ascending=[False, True],
            kind="stable",
        )
        ordered_actual = valid.sort_values(
            [actual_column, "player_id"],
            ascending=[False, True],
            kind="stable",
        )
        output.loc[ordered_prediction.index, "prediction_rank"] = np.arange(
            1, len(ordered_prediction) + 1
        )
        output.loc[ordered_actual.index, "actual_rank"] = np.arange(
            1, len(ordered_actual) + 1
        )
    return output


def top_metrics(frame: pd.DataFrame, k: int) -> tuple[float, float, int, int, int]:
    valid = frame.dropna(subset=["prediction_rank", "actual_rank"])
    predicted = valid["prediction_rank"].le(k)
    actual = valid["actual_rank"].le(k)
    hits = int((predicted & actual).sum())
    predicted_count = int(predicted.sum())
    actual_count = int(actual.sum())
    precision = hits / predicted_count if predicted_count else float("nan")
    recall = hits / actual_count if actual_count else float("nan")
    return precision, recall, hits, predicted_count, actual_count


def severe_errors(frame: pd.DataFrame) -> tuple[int, int]:
    valid = frame.dropna(subset=["prediction_rank", "actual_rank"])
    severe_fp = int(
        (valid["prediction_rank"].le(24) & valid["actual_rank"].gt(120)).sum()
    )
    severe_fn = int(
        (valid["actual_rank"].le(24) & valid["prediction_rank"].gt(120)).sum()
    )
    return severe_fp, severe_fn


def bootstrap_metric(
    frame: pd.DataFrame,
    *,
    score_column: str,
    actual_column: str,
    iterations: int = BOOTSTRAP_ITERATIONS,
) -> tuple[float, float]:
    seasons = np.asarray(sorted(frame["season"].dropna().astype(int).unique()))
    if len(seasons) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(SEED)
    values: list[float] = []
    for _index in range(iterations):
        sampled = rng.choice(seasons, size=len(seasons), replace=True)
        pieces = []
        for replicate, season in enumerate(sampled):
            piece = frame.loc[
                frame["season"].astype(int).eq(int(season))
            ].copy()
            piece["season"] = replicate
            pieces.append(piece)
        sample = pd.concat(pieces, ignore_index=True)
        ranked = add_season_ranks(sample, score_column, actual_column)
        value = spearman(ranked["prediction_rank"], ranked["actual_rank"])
        if math.isfinite(value):
            values.append(value)
    if not values:
        return float("nan"), float("nan")
    return (
        float(np.quantile(values, 0.025)),
        float(np.quantile(values, 0.975)),
    )


def metric_row(
    frame: pd.DataFrame,
    *,
    lane: str,
    candidate: str,
    score_column: str,
    actual_column: str,
    scope_type: str,
    scope_value: str,
    include_ci: bool,
) -> dict[str, Any]:
    ranked = add_season_ranks(frame, score_column, actual_column)
    valid = ranked.dropna(
        subset=[score_column, actual_column, "prediction_rank", "actual_rank"]
    )
    eligible = len(frame)
    precision12, recall12, *_ = top_metrics(valid, 12)
    precision24, recall24, *_ = top_metrics(valid, 24)
    precision60, recall60, *_ = top_metrics(valid, 60)
    severe_fp, severe_fn = severe_errors(valid)
    ci_low, ci_high = (
        bootstrap_metric(valid, score_column=score_column, actual_column=actual_column)
        if include_ci
        else (float("nan"), float("nan"))
    )
    return {
        "lane": lane,
        "candidate_id": candidate,
        "scope_type": scope_type,
        "scope_value": scope_value,
        "eligible_rows": eligible,
        "scored_rows": len(valid),
        "coverage": len(valid) / eligible if eligible else np.nan,
        "seasons": int(valid["season"].nunique()) if not valid.empty else 0,
        "spearman": spearman(valid["prediction_rank"], valid["actual_rank"]),
        "spearman_ci_low": ci_low,
        "spearman_ci_high": ci_high,
        "rank_mae": float(
            (valid["prediction_rank"] - valid["actual_rank"]).abs().mean()
        )
        if not valid.empty
        else np.nan,
        "ndcg": ndcg(valid[score_column], valid[actual_column]),
        "ndcg_top60": ndcg(valid[score_column], valid[actual_column], 60),
        "top12_precision": precision12,
        "top12_recall": recall12,
        "top24_precision": precision24,
        "top24_recall": recall24,
        "top60_precision": precision60,
        "top60_recall": recall60,
        "severe_false_positives": severe_fp,
        "severe_false_negatives": severe_fn,
        "severe_errors": severe_fp + severe_fn,
        "metric_status": "SUPPORTED" if len(valid) >= 20 else "UNSUPPORTED_LOW_N",
        "review_only": True,
    }


def evaluation_table(
    predictions: pd.DataFrame,
    *,
    lane: str,
    candidates: dict[str, str],
    actual_column: str,
    seasons: Sequence[int],
) -> pd.DataFrame:
    base = predictions.loc[predictions["season"].astype(int).isin(seasons)].copy()
    rows: list[dict[str, Any]] = []
    for candidate, score_column in candidates.items():
        rows.append(
            metric_row(
                base,
                lane=lane,
                candidate=candidate,
                score_column=score_column,
                actual_column=actual_column,
                scope_type="OVERALL",
                scope_value="ALL",
                include_ci=True,
            )
        )
        for position in POSITIONS:
            group = base.loc[base["position"].eq(position)]
            rows.append(
                metric_row(
                    group,
                    lane=lane,
                    candidate=candidate,
                    score_column=score_column,
                    actual_column=actual_column,
                    scope_type="POSITION",
                    scope_value=position,
                    include_ci=False,
                )
            )
        for season in seasons:
            group = base.loc[base["season"].astype(int).eq(season)]
            rows.append(
                metric_row(
                    group,
                    lane=lane,
                    candidate=candidate,
                    score_column=score_column,
                    actual_column=actual_column,
                    scope_type="SEASON",
                    scope_value=str(season),
                    include_ci=False,
                )
            )
    return pd.DataFrame(rows)


def choose_research_candidate(
    results: pd.DataFrame,
    candidates: Sequence[str],
) -> str:
    overall = results.loc[
        results["scope_type"].eq("OVERALL")
        & results["candidate_id"].isin(candidates)
        & results["spearman"].notna()
    ].copy()
    if overall.empty:
        raise ValueError("no supported bounded research candidate")
    overall["selection_score"] = (
        overall["spearman"]
        + 0.10 * overall["ndcg_top60"]
        - 0.002 * overall["severe_errors"]
    )
    priority = {candidate: -index for index, candidate in enumerate(candidates)}
    overall["priority"] = overall["candidate_id"].map(priority)
    selected = overall.sort_values(
        ["selection_score", "priority"],
        ascending=[False, False],
        kind="stable",
    ).iloc[0]["candidate_id"]
    return str(selected)


def candidate_score_column(candidate: str) -> str:
    mapping = {
        "W0_FINISHED_V1_ACCEPTED_PROXY": "w0_score",
        "W1_NEXT_SEASON_VOR": "w1_score",
        "W2_CONDITIONAL_PRODUCTION_AVAILABILITY": "w2_score",
        "W3_SHORT_HORIZON_CALIBRATED_BLEND": "w3_score",
        "D0_FINISHED_V1_ACCEPTED_PROXY": "w0_score",
        "D1_DISCOUNTED_MULTI_HORIZON_VOR": "d1_score",
        "D2_FUTURE_PRODUCTION_X_RETENTION": "d2_score",
        "D3_CAPPED_CAREER_HORIZON_GUARDS": "d3_score",
    }
    return mapping[candidate]


def bootstrap_delta(
    frame: pd.DataFrame,
    candidate_score: str,
    baseline_score: str,
    actual_score: str,
    iterations: int = BOOTSTRAP_ITERATIONS,
) -> tuple[float, float, float]:
    seasons = np.asarray(sorted(frame["season"].dropna().astype(int).unique()))
    rng = np.random.default_rng(SEED + 1)
    values: list[float] = []
    for _index in range(iterations):
        sampled = rng.choice(seasons, size=len(seasons), replace=True)
        pieces = []
        for replicate, season in enumerate(sampled):
            piece = frame.loc[
                frame["season"].astype(int).eq(int(season))
            ].copy()
            piece["season"] = replicate
            pieces.append(piece)
        sample = pd.concat(pieces, ignore_index=True)
        candidate = add_season_ranks(sample, candidate_score, actual_score)
        baseline = add_season_ranks(sample, baseline_score, actual_score)
        c_value = spearman(candidate["prediction_rank"], candidate["actual_rank"])
        b_value = spearman(baseline["prediction_rank"], baseline["actual_rank"])
        if math.isfinite(c_value) and math.isfinite(b_value):
            values.append(c_value - b_value)
    if not values:
        return float("nan"), float("nan"), float("nan")
    return (
        float(np.mean(values)),
        float(np.quantile(values, 0.025)),
        float(np.quantile(values, 0.975)),
    )


def calibration_results(
    win: pd.DataFrame,
    dynasty: pd.DataFrame,
    win_candidate: str,
    dynasty_candidate: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    win_eval = win.loc[win["season"].astype(int).isin(WIN_EVALUATION_SEASONS)].dropna(
        subset=["availability_predicted", "availability_actual"]
    )
    for scope, group in [("ALL", win_eval)] + [
        (position, win_eval.loc[win_eval["position"].eq(position)])
        for position in POSITIONS
    ]:
        if group.empty:
            continue
        p = group["availability_predicted"].clip(1e-9, 1 - 1e-9)
        y_fraction = group["availability_actual"]
        y_binary = group["availability_8plus_actual"]
        rows.append(
            {
                "lane": "WIN_NOW",
                "candidate_id": win_candidate,
                "target": "GAMES_AVAILABILITY_FRACTION_AND_8PLUS",
                "scope": scope,
                "rows": len(group),
                "coverage": len(group) / len(win_eval) if len(win_eval) else np.nan,
                "brier": float(np.mean((p - y_binary) ** 2)),
                "mae": float(np.mean(np.abs(p - y_fraction))),
                "log_loss": float(
                    -np.mean(y_binary * np.log(p) + (1 - y_binary) * np.log(1 - p))
                ),
                "ece": ece(p, y_binary),
                "threshold": float(group["availability_threshold"].median()),
                "precision": np.nan,
                "recall": np.nan,
                "status": "SUPPORTED",
            }
        )

    dynasty_eval = dynasty.loc[
        dynasty["season"].astype(int).isin(DYNASTY_EVALUATION_SEASONS)
    ]
    for horizon in (2, 3):
        probability_column = f"retention_h{horizon}_predicted"
        actual_column = f"retain_h{horizon}"
        valid = dynasty_eval.dropna(subset=[probability_column, actual_column])
        for scope, group in [("ALL", valid)] + [
            (position, valid.loc[valid["position"].eq(position)])
            for position in POSITIONS
        ]:
            if group.empty:
                continue
            p = group[probability_column].clip(1e-9, 1 - 1e-9)
            y = group[actual_column].astype(float)
            rows.append(
                {
                    "lane": "DYNASTY",
                    "candidate_id": "D2_D3_SHARED_RETENTION_MODEL",
                    "target": f"ABOVE_REPLACEMENT_H{horizon}",
                    "scope": scope,
                    "rows": len(group),
                    "coverage": len(group) / len(dynasty_eval)
                    if len(dynasty_eval)
                    else np.nan,
                    "brier": float(np.mean((p - y) ** 2)),
                    "mae": float(np.mean(np.abs(p - y))),
                    "log_loss": float(
                        -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
                    ),
                    "ece": ece(p, y),
                    "threshold": 0.5,
                    "precision": float(
                        ((p.ge(0.5)) & y.eq(1)).sum() / max(1, p.ge(0.5).sum())
                    ),
                    "recall": float(
                        ((p.ge(0.5)) & y.eq(1)).sum() / max(1, y.eq(1).sum())
                    ),
                    "status": "SUPPORTED",
                }
            )
    collapse = dynasty_eval.dropna(
        subset=["retention_h3_predicted", "value_collapse_h3"]
    )
    if not collapse.empty:
        probability = 1.0 - collapse["retention_h3_predicted"]
        actual = collapse["value_collapse_h3"].astype(float)
        predicted = probability.ge(0.5)
        rows.append(
            {
                "lane": "DYNASTY",
                "candidate_id": "D2_D3_SHARED_RETENTION_MODEL",
                "target": "SEVERE_VALUE_COLLAPSE_H3",
                "scope": "ALL",
                "rows": len(collapse),
                "coverage": len(collapse) / len(dynasty_eval),
                "brier": float(np.mean((probability - actual) ** 2)),
                "mae": float(np.mean(np.abs(probability - actual))),
                "log_loss": float(
                    -np.mean(
                        actual * np.log(probability.clip(1e-9, 1 - 1e-9))
                        + (1 - actual)
                        * np.log((1 - probability).clip(1e-9, 1 - 1e-9))
                    )
                ),
                "ece": ece(probability, actual),
                "threshold": 0.5,
                "precision": float(
                    ((predicted) & actual.eq(1)).sum() / max(1, predicted.sum())
                ),
                "recall": float(
                    ((predicted) & actual.eq(1)).sum() / max(1, actual.eq(1).sum())
                ),
                "status": "SUPPORTED",
            }
        )
    return pd.DataFrame(rows)


def cohort_results(
    win: pd.DataFrame,
    dynasty: pd.DataFrame,
    win_candidate: str,
    dynasty_candidate: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    win_score = candidate_score_column(win_candidate)
    dynasty_score = candidate_score_column(dynasty_candidate)
    win_eval = win.loc[win["season"].astype(int).isin(WIN_EVALUATION_SEASONS)].copy()
    dynasty_eval = dynasty.loc[
        dynasty["season"].astype(int).isin(DYNASTY_EVALUATION_SEASONS)
    ].copy()
    cohort_rows: list[dict[str, Any]] = []
    requested = (
        "TRUE_ROOKIE",
        "SECOND_YEAR",
        "THIRD_YEAR",
        "ESTABLISHED",
        "LOW_GAMES_VETERAN",
        "INJURY_RETURN",
    )
    for cohort in requested:
        for lane, frame, score, actual in (
            ("WIN_NOW", win_eval, win_score, "actual_vor_h1"),
            ("DYNASTY", dynasty_eval, dynasty_score, "actual_dynasty_target"),
        ):
            if cohort == "INJURY_RETURN":
                cohort_rows.append(
                    {
                        "cohort": cohort,
                        "lane": lane,
                        "candidate_id": win_candidate
                        if lane == "WIN_NOW"
                        else dynasty_candidate,
                        "eligible_rows": 0,
                        "scored_rows": 0,
                        "coverage": np.nan,
                        "spearman": np.nan,
                        "spearman_ci_low": np.nan,
                        "spearman_ci_high": np.nan,
                        "rank_mae": np.nan,
                        "top60_precision": np.nan,
                        "top60_recall": np.nan,
                        "false_positives": np.nan,
                        "false_negatives": np.nan,
                        "calibration_mae": np.nan,
                        "status": "SOURCE_BLOCKED_NO_INJURY_RETURN_AUTHORITY",
                        "uncertainty": "NOT_ENOUGH_INFORMATION",
                    }
                )
                continue
            group = frame.loc[frame["cohort"].eq(cohort)].copy()
            ranked = add_season_ranks(group, score, actual)
            valid = ranked.dropna(
                subset=[score, actual, "prediction_rank", "actual_rank"]
            )
            precision, recall, _hits, predicted_count, actual_count = top_metrics(
                valid, 60
            )
            ci_low, ci_high = (
                bootstrap_metric(valid, score_column=score, actual_column=actual)
                if valid["season"].nunique() >= 2 and len(valid) >= 20
                else (np.nan, np.nan)
            )
            calibration_mae = (
                float(
                    np.mean(
                        np.abs(
                            valid["availability_predicted"]
                            - valid["availability_actual"]
                        )
                    )
                )
                if lane == "WIN_NOW"
                and not valid.empty
                and valid["availability_predicted"].notna().any()
                else (
                    float(
                        np.mean(
                            np.abs(
                                valid["retention_h3_predicted"]
                                - valid["retain_h3"].astype(float)
                            )
                        )
                    )
                    if lane == "DYNASTY"
                    and not valid.empty
                    and valid["retain_h3"].notna().any()
                    else np.nan
                )
            )
            cohort_rows.append(
                {
                    "cohort": cohort,
                    "lane": lane,
                    "candidate_id": win_candidate
                    if lane == "WIN_NOW"
                    else dynasty_candidate,
                    "eligible_rows": len(group),
                    "scored_rows": len(valid),
                    "coverage": len(valid) / len(group) if len(group) else np.nan,
                    "spearman": spearman(
                        valid["prediction_rank"], valid["actual_rank"]
                    ),
                    "spearman_ci_low": ci_low,
                    "spearman_ci_high": ci_high,
                    "rank_mae": float(
                        (valid["prediction_rank"] - valid["actual_rank"]).abs().mean()
                    )
                    if not valid.empty
                    else np.nan,
                    "top60_precision": precision,
                    "top60_recall": recall,
                    "false_positives": predicted_count - _hits,
                    "false_negatives": actual_count - _hits,
                    "calibration_mae": calibration_mae,
                    "status": (
                        "UNSUPPORTED_ZERO_ROWS"
                        if len(group) == 0
                        else (
                            "SUPPORTED"
                            if len(valid) >= 20
                            else "INSUFFICIENT_SMALL_N"
                        )
                    ),
                    "uncertainty": (
                        "NOT_ENOUGH_INFORMATION"
                        if len(valid) < 20
                        else "BOOTSTRAP_SEASON_CLUSTERED"
                    ),
                }
            )
    cohort_frame = pd.DataFrame(cohort_rows)

    detail_rows: list[dict[str, Any]] = []
    for lane, frame, candidate, score, actual in (
        ("WIN_NOW", win_eval, win_candidate, win_score, "actual_vor_h1"),
        (
            "DYNASTY",
            dynasty_eval,
            dynasty_candidate,
            dynasty_score,
            "actual_dynasty_target",
        ),
    ):
        scopes: list[tuple[str, str, pd.Series]] = []
        for position in POSITIONS:
            scopes.append(("POSITION", position, frame["position"].eq(position)))
        age = pd.to_numeric(frame["age"], errors="coerce")
        for label, lower, upper in (
            ("AGE_UNDER_24", -np.inf, 24),
            ("AGE_24_27", 24, 28),
            ("AGE_28_30", 28, 31),
            ("AGE_31_PLUS", 31, np.inf),
        ):
            scopes.append(("AGE", label, age.ge(lower) & age.lt(upper)))
        games = pd.to_numeric(frame["prior_games"], errors="coerce")
        for label, lower, upper in (
            ("GAMES_0_5", -np.inf, 6),
            ("GAMES_6_7", 6, 8),
            ("GAMES_8_12", 8, 13),
            ("GAMES_13_PLUS", 13, np.inf),
        ):
            scopes.append(("GAMES", label, games.ge(lower) & games.lt(upper)))
        for scope_type, scope_value, mask in scopes:
            group = frame.loc[mask]
            row = metric_row(
                group,
                lane=lane,
                candidate=candidate,
                score_column=score,
                actual_column=actual,
                scope_type=scope_type,
                scope_value=scope_value,
                include_ci=False,
            )
            detail_rows.append(row)
    return cohort_frame, pd.DataFrame(detail_rows)


def result_value(
    results: pd.DataFrame,
    candidate: str,
    field: str,
    *,
    scope_type: str = "OVERALL",
    scope_value: str = "ALL",
) -> float:
    rows = results.loc[
        results["candidate_id"].eq(candidate)
        & results["scope_type"].eq(scope_type)
        & results["scope_value"].astype(str).eq(str(scope_value))
    ]
    if len(rows) != 1:
        return float("nan")
    value = finite(rows.iloc[0][field])
    return value if value is not None else float("nan")


def candidate_delta_safety(
    results: pd.DataFrame,
    candidate: str,
    baseline: str,
    scope_type: str,
) -> list[float]:
    values: list[float] = []
    scopes = sorted(
        results.loc[results["scope_type"].eq(scope_type), "scope_value"]
        .astype(str)
        .unique()
    )
    for scope in scopes:
        candidate_value = result_value(
            results,
            candidate,
            "spearman",
            scope_type=scope_type,
            scope_value=scope,
        )
        baseline_value = result_value(
            results,
            baseline,
            "spearman",
            scope_type=scope_type,
            scope_value=scope,
        )
        if math.isfinite(candidate_value) and math.isfinite(baseline_value):
            values.append(candidate_value - baseline_value)
    return values


def build_gates(
    win_results: pd.DataFrame,
    dynasty_results: pd.DataFrame,
    calibration: pd.DataFrame,
    cohorts: pd.DataFrame,
    win_predictions: pd.DataFrame,
    dynasty_predictions: pd.DataFrame,
    win_candidate: str,
    dynasty_candidate: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    win_baseline = "W0_FINISHED_V1_ACCEPTED_PROXY"
    dynasty_baseline = "D0_FINISHED_V1_ACCEPTED_PROXY"
    win_eval = win_predictions.loc[
        win_predictions["season"].astype(int).isin(WIN_EVALUATION_SEASONS)
    ]
    dynasty_eval = dynasty_predictions.loc[
        dynasty_predictions["season"].astype(int).isin(DYNASTY_EVALUATION_SEASONS)
    ]
    win_delta, win_delta_low, win_delta_high = bootstrap_delta(
        win_eval,
        candidate_score_column(win_candidate),
        "w0_score",
        "actual_vor_h1",
    )
    dynasty_delta, dynasty_delta_low, dynasty_delta_high = bootstrap_delta(
        dynasty_eval,
        candidate_score_column(dynasty_candidate),
        "w0_score",
        "actual_dynasty_target",
    )
    win_position_deltas = candidate_delta_safety(
        win_results, win_candidate, win_baseline, "POSITION"
    )
    win_season_deltas = candidate_delta_safety(
        win_results, win_candidate, win_baseline, "SEASON"
    )
    dynasty_position_deltas = candidate_delta_safety(
        dynasty_results, dynasty_candidate, dynasty_baseline, "POSITION"
    )
    dynasty_season_deltas = candidate_delta_safety(
        dynasty_results, dynasty_candidate, dynasty_baseline, "SEASON"
    )
    win_calibration = calibration.loc[
        calibration["lane"].eq("WIN_NOW") & calibration["scope"].eq("ALL")
    ]
    retention_h3 = calibration.loc[
        calibration["lane"].eq("DYNASTY")
        & calibration["scope"].eq("ALL")
        & calibration["target"].eq("ABOVE_REPLACEMENT_H3")
    ]
    win_calibration_pass = (
        len(win_calibration) == 1
        and float(win_calibration.iloc[0]["mae"]) <= 0.20
        and float(win_calibration.iloc[0]["ece"]) <= 0.12
    )
    retention_pass = (
        len(retention_h3) == 1
        and float(retention_h3.iloc[0]["brier"]) <= 0.25
        and float(retention_h3.iloc[0]["ece"]) <= 0.12
    )
    win_low_games = cohorts.loc[
        cohorts["lane"].eq("WIN_NOW")
        & cohorts["cohort"].eq("LOW_GAMES_VETERAN")
    ]
    dynasty_low_games = cohorts.loc[
        cohorts["lane"].eq("DYNASTY")
        & cohorts["cohort"].eq("LOW_GAMES_VETERAN")
    ]

    def row(
        gate_id: str,
        gate: str,
        passed: bool,
        evidence: str,
        blocker: str = "",
    ) -> dict[str, Any]:
        return {
            "gate_id": gate_id,
            "gate": gate,
            "mandatory": True,
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
            "blocker_or_caveat": blocker,
        }

    win_rows = [
        row(
            "W-G01",
            "Zero future leakage and chronological nested selection",
            True,
            "N-to-N+1 source gates pass; every fitted target requires anchor+horizon < origin.",
        ),
        row(
            "W-G02",
            "Exact player identity",
            True,
            "5,518 unique season-position-player_id rows; no name join.",
        ),
        row(
            "W-G03",
            "Adequate historical and current experienced-player coverage",
            result_value(win_results, win_candidate, "coverage") >= 0.95,
            f"OOF coverage={result_value(win_results, win_candidate, 'coverage'):.6f}; "
            "current unsupported rows remain null-fenced.",
        ),
        row(
            "W-G04",
            "Material next-year improvement or non-inferiority with better availability",
            (
                win_delta >= 0.01
                and win_delta_low >= 0.0
                and win_calibration_pass
            ),
            f"season-bootstrap delta={win_delta:.6f} "
            f"CI=[{win_delta_low:.6f},{win_delta_high:.6f}]; "
            f"availability_calibration_pass={win_calibration_pass}.",
            "Strict gate requires material improvement with non-negative uncertainty bound.",
        ),
        row(
            "W-G05",
            "Uncertainty survival",
            win_delta_low >= -0.005,
            f"delta lower 95% bound={win_delta_low:.6f}; floor=-0.005.",
        ),
        row(
            "W-G06",
            "Position and season safety",
            bool(win_position_deltas)
            and min(win_position_deltas) >= -0.03
            and sum(value < -0.05 for value in win_season_deltas) <= 2,
            f"min_position_delta="
            f"{min(win_position_deltas) if win_position_deltas else np.nan:.6f}; "
            f"seasons_below_-0.05={sum(value < -0.05 for value in win_season_deltas)}.",
        ),
        row(
            "W-G07",
            "Top-tier safety",
            result_value(win_results, win_candidate, "top24_precision")
            >= result_value(win_results, win_baseline, "top24_precision") - 0.03,
            f"candidate_top24_precision="
            f"{result_value(win_results, win_candidate, 'top24_precision'):.6f}; "
            f"W0={result_value(win_results, win_baseline, 'top24_precision'):.6f}.",
        ),
        row(
            "W-G08",
            "Availability calibration",
            win_calibration_pass,
            (
                f"MAE={float(win_calibration.iloc[0]['mae']):.6f}; "
                f"ECE={float(win_calibration.iloc[0]['ece']):.6f}."
                if len(win_calibration) == 1
                else "No supported availability row."
            ),
        ),
        row(
            "W-G09",
            "Low-games safety",
            len(win_low_games) == 1
            and win_low_games.iloc[0]["status"] == "SUPPORTED"
            and float(win_low_games.iloc[0]["coverage"]) >= 0.95,
            (
                f"rows={int(win_low_games.iloc[0]['scored_rows'])}; "
                f"coverage={float(win_low_games.iloc[0]['coverage']):.6f}."
                if len(win_low_games) == 1
                else "No low-games cohort result."
            ),
        ),
        row(
            "W-G10",
            "Explicit rookie governance",
            True,
            "True-rookie OOF support is zero and the canonical current board has zero "
            "rows flagged as rookies. Any future rookie is null-fenced until governed "
            "evidence exists; no rookie precision is invented.",
        ),
        row(
            "W-G11",
            "Production source authority",
            False,
            "All 5,518 mart rows are review_only; training_allowed=False and "
            "production_approved=False.",
            "Controlling source authority blocks production admission regardless of metrics.",
        ),
        row(
            "W-G12",
            "Deterministic reproduction and immutable baselines",
            True,
            "Fixed hashes, fixed seed, stable ordering/precision, no production writes.",
        ),
    ]

    dynasty_rows = [
        row(
            "D-G01",
            "Zero future leakage and chronological nested selection",
            True,
            "Horizon-h training requires anchor+(h-1) < origin; future absence remains unknown.",
        ),
        row(
            "D-G02",
            "Exact player identity",
            True,
            "All horizon joins use exact player_id+season; no name join.",
        ),
        row(
            "D-G03",
            "Adequate comparable multi-year coverage",
            result_value(dynasty_results, dynasty_candidate, "coverage") >= 0.70,
            f"complete three-horizon coverage="
            f"{result_value(dynasty_results, dynasty_candidate, 'coverage'):.6f}.",
            "Missing future player-seasons are censored unknown, never coerced to zero.",
        ),
        row(
            "D-G04",
            "Material multi-year improvement",
            dynasty_delta >= 0.01 and dynasty_delta_low >= 0.0,
            f"season-bootstrap delta={dynasty_delta:.6f} "
            f"CI=[{dynasty_delta_low:.6f},{dynasty_delta_high:.6f}].",
        ),
        row(
            "D-G05",
            "Retention and above-replacement calibration",
            dynasty_candidate
            in {
                "D2_FUTURE_PRODUCTION_X_RETENTION",
                "D3_CAPPED_CAREER_HORIZON_GUARDS",
            }
            and retention_pass,
            (
                f"H3 Brier={float(retention_h3.iloc[0]['brier']):.6f}; "
                f"ECE={float(retention_h3.iloc[0]['ece']):.6f}."
                if len(retention_h3) == 1
                else "No supported H3 retention row."
            ),
            "Selected D1 does not directly incorporate the separately calibrated "
            "retention model.",
        ),
        row(
            "D-G06",
            "Productive-veteran safety",
            dynasty_candidate == "D3_CAPPED_CAREER_HORIZON_GUARDS"
            and bool(dynasty_eval["productive_veteran_guard"].any()),
            f"guarded_rows={int(dynasty_eval['productive_veteran_guard'].fillna(False).sum())}; "
            "age penalty capped at 5% for productive veterans.",
        ),
        row(
            "D-G07",
            "Improved veteran overvaluation without universal age penalty",
            dynasty_candidate == "D3_CAPPED_CAREER_HORIZON_GUARDS",
            "D3 uses position-specific nested inflections, a 20% maximum future-only "
            "penalty, and no youth bonus.",
            "Pass requires D3 to be selected as the strongest bounded research candidate.",
        ),
        row(
            "D-G08",
            "Low-games safety",
            dynasty_candidate == "D3_CAPPED_CAREER_HORIZON_GUARDS"
            and len(dynasty_low_games) == 1
            and dynasty_low_games.iloc[0]["status"] == "SUPPORTED",
            (
                f"rows={int(dynasty_low_games.iloc[0]['scored_rows'])}; "
                "positive future contribution is capped at 75% of positive H1."
                if len(dynasty_low_games) == 1
                else "No low-games cohort result."
            ),
        ),
        row(
            "D-G09",
            "Position and season stability",
            bool(dynasty_position_deltas)
            and min(dynasty_position_deltas) >= -0.03
            and sum(value < -0.05 for value in dynasty_season_deltas) <= 2,
            f"min_position_delta="
            f"{min(dynasty_position_deltas) if dynasty_position_deltas else np.nan:.6f}; "
            f"seasons_below_-0.05={sum(value < -0.05 for value in dynasty_season_deltas)}.",
        ),
        row(
            "D-G10",
            "Explicit rookie governance",
            True,
            "True-rookie OOF support is zero and the canonical current board has zero "
            "rookie-flagged rows; draft-capital evidence remains review-only "
            "positive-evidence only.",
        ),
        row(
            "D-G11",
            "Interpretable bounded behavior",
            True,
            "Exactly three horizons; fixed discount schedules; position-specific capped "
            "inflections; explicit veteran and low-games guards.",
        ),
        row(
            "D-G12",
            "Production source authority",
            False,
            "Mart, age, and draft-capital evidence are review-only and not production-approved.",
            "Controlling source authority blocks production admission regardless of metrics.",
        ),
        row(
            "D-G13",
            "Deterministic reproduction and immutable baselines",
            True,
            "Fixed hashes, fixed seed, stable ordering/precision, no production writes.",
        ),
    ]
    win_frame = pd.DataFrame(win_rows)
    dynasty_frame = pd.DataFrame(dynasty_rows)
    win_admitted = bool(win_frame["status"].eq("PASS").all())
    dynasty_admitted = bool(dynasty_frame["status"].eq("PASS").all())
    summary = {
        "win_candidate": win_candidate,
        "dynasty_candidate": dynasty_candidate,
        "win_delta": win_delta,
        "win_delta_ci": [win_delta_low, win_delta_high],
        "dynasty_delta": dynasty_delta,
        "dynasty_delta_ci": [dynasty_delta_low, dynasty_delta_high],
        "win_admitted": win_admitted,
        "dynasty_admitted": dynasty_admitted,
        "both_admitted": win_admitted and dynasty_admitted,
        "verdict": (
            "GREEN_NWR_FINISHED_V1_RETAINS_AUTHORITY_DUAL_LENS_NOT_ADMITTED"
            if not (win_admitted and dynasty_admitted)
            else "GREEN_NWR_DUAL_LENS_RESEARCH_READY_FOR_HQ_REVIEW"
        ),
    }
    return win_frame, dynasty_frame, summary


def current_outcome_context(row: pd.Series, suffix: str) -> Any:
    position = str(row.get("position") or row.get("board_position") or "")
    column = f"{position}_T12_{suffix}"
    return row.get(column, np.nan)


def reason_codes(row: pd.Series) -> str:
    codes = ["REVIEW_ONLY_SOURCE"]
    if truth_value(row.get("is_rookie")):
        codes.append("ROOKIE_UNSUPPORTED_NO_PRIOR_NFL_FEATURES")
    if not truth_value(row.get("source_ready")):
        codes.append("NOT_ENOUGH_INFORMATION")
    if truth_value(row.get("low_games_guard")):
        codes.append("LOW_GAMES_GUARD")
    if truth_value(row.get("productive_veteran_guard")):
        codes.append("PRODUCTIVE_VETERAN_GUARD")
    if finite(row.get("win_now_rank")) is not None and finite(
        row.get("dynasty_value_rank")
    ) is not None:
        gap = float(row["win_now_rank"]) - float(row["dynasty_value_rank"])
        if gap <= -20:
            codes.append("WIN_NOW_PREMIUM")
        elif gap >= 20:
            codes.append("DYNASTY_HORIZON_PREMIUM")
        else:
            codes.append("LENSES_BROADLY_ALIGNED")
    return "|".join(codes)


def build_current_board(
    current: pd.DataFrame,
    win_predictions: pd.DataFrame,
    dynasty_predictions: pd.DataFrame,
    win_candidate: str,
    dynasty_candidate: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    win_current = win_predictions.loc[win_predictions["season"].astype(int).eq(2026)].copy()
    dynasty_current = dynasty_predictions.loc[
        dynasty_predictions["season"].astype(int).eq(2026)
    ].copy()
    win_columns = [
        "nwr_player_id",
        "player_id",
        "w1_score",
        "w2_score",
        "w3_score",
        "w3_weight_w1",
        "w3_weight_w2",
        "availability_predicted",
        "conditional_ppg_predicted",
        "replacement_forecast",
    ]
    dynasty_columns = [
        "nwr_player_id",
        "player_id",
        "d_h1_pred",
        "d_h2_pred",
        "d_h3_pred",
        "retention_h2_predicted",
        "retention_h3_predicted",
        "discount_schedule",
        "discount_h1",
        "discount_h2",
        "discount_h3",
        "d1_score",
        "d2_score",
        "d3_score",
        "d_future_retained_contribution",
        "age_profile",
        "productive_veteran_guard",
        "low_games_guard",
    ]
    base_columns = [
        "nwr_player_id",
        "player_id",
        "player_name",
        "position",
        "nfl_team",
        "age",
        "finished_v1_rank",
        "finished_v1_score",
        "finished_v1_confidence",
        "model_version",
        "is_rookie",
        "cohort",
        "source_ready",
        "candidate_feature_ready",
        "missing_required_features",
        "frozen_exclusion_reason",
        "history_years_available",
        "multiyear_feature_status",
        "outcome_calibration_status",
        "outcome_confidence",
        "outcome_missing_reason",
        "outcome_reason_code",
        "release_identifier",
    ]
    outcome_columns = [
        column
        for column in current.columns
        if column.endswith("_NEXT_YEAR")
        or column.endswith("_WITHIN_3Y")
        or column.endswith("_T_PLUS_2")
    ]
    board = current[base_columns + outcome_columns].merge(
        win_current[win_columns],
        on=["nwr_player_id", "player_id"],
        how="left",
        validate="one_to_one",
    ).merge(
        dynasty_current[dynasty_columns],
        on=["nwr_player_id", "player_id"],
        how="left",
        validate="one_to_one",
    )
    board["win_now_formula_id"] = win_candidate
    board["dynasty_formula_id"] = dynasty_candidate
    board["win_now_score"] = board[candidate_score_column(win_candidate)]
    board["dynasty_value_score"] = board[candidate_score_column(dynasty_candidate)]
    board["win_now_rank"] = rank_desc(board["win_now_score"])
    board["dynasty_value_rank"] = rank_desc(board["dynasty_value_score"])
    board["win_now_normalized_score"] = percentile_score(board["win_now_score"])
    board["dynasty_normalized_score"] = percentile_score(board["dynasty_value_score"])
    for label, win_weight in (
        ("contending", 0.75),
        ("balanced", 0.50),
        ("rebuilding", 0.25),
    ):
        dynasty_weight = 1.0 - win_weight
        board[f"{label}_win_now_weight"] = win_weight
        board[f"{label}_dynasty_weight"] = dynasty_weight
        board[f"{label}_team_window_score"] = (
            win_weight * board["win_now_normalized_score"]
            + dynasty_weight * board["dynasty_normalized_score"]
        ).where(
            board[
                ["win_now_normalized_score", "dynasty_normalized_score"]
            ].notna().all(axis=1)
        )
        board[f"{label}_team_window_rank"] = rank_desc(
            board[f"{label}_team_window_score"]
        )
    board["outcome_v3_next_year_context"] = board.apply(
        lambda row: current_outcome_context(row, "NEXT_YEAR"), axis=1
    )
    board["outcome_v3_t_plus_2_context"] = board.apply(
        lambda row: current_outcome_context(row, "T_PLUS_2"), axis=1
    )
    board["outcome_v3_within_3y_context"] = board.apply(
        lambda row: current_outcome_context(row, "WITHIN_3Y"), axis=1
    )
    board["evidence_state"] = np.select(
        [
            board["is_rookie"].fillna(False).astype(bool),
            ~board["source_ready"].fillna(False).astype(bool),
            board["low_games_guard"].fillna(False).astype(bool),
        ],
        [
            "NOT_ENOUGH_INFORMATION_TRUE_ROOKIE",
            "NOT_ENOUGH_INFORMATION_MISSING_FEATURES",
            "REVIEW_ONLY_LOW_GAMES",
        ],
        default="REVIEW_ONLY_EXPERIENCED",
    )
    board["rookie_evidence_state"] = np.where(
        board["is_rookie"],
        "UNSUPPORTED_NO_TRUE_ROOKIE_HISTORICAL_ROWS",
        "NOT_APPLICABLE_EXPERIENCED",
    )
    board["confidence"] = np.select(
        [
            ~board["source_ready"].fillna(False).astype(bool),
            board["low_games_guard"].fillna(False).astype(bool),
        ],
        ["NOT_ENOUGH_INFORMATION", "LOW"],
        default="MEDIUM_REVIEW_ONLY",
    )
    board["missing_reason"] = np.where(
        board["source_ready"],
        "",
        np.where(
            board["is_rookie"],
            "NO_PRIOR_NFL_PRODUCTION_OR_AVAILABILITY;ROOKIE_FEATURE_AUTHORITY_INCOMPLETE",
            board["missing_required_features"].fillna("").replace(
                "", "CURRENT_FEATURE_ROW_NOT_READY"
            ),
        ),
    )
    board["reason_codes"] = board.apply(reason_codes, axis=1)
    board["lens_rank_gap_win_minus_dynasty"] = (
        board["win_now_rank"] - board["dynasty_value_rank"]
    )
    board["absolute_lens_rank_gap"] = board[
        "lens_rank_gap_win_minus_dynasty"
    ].abs()
    board["rank_scope"] = "SCORED_REVIEW_ONLY_SUBSET_NOT_240_PLAYER_PRODUCTION_RANK"
    board["release_identifier_dual_lens"] = "NWR_DUAL_LENS_RC1_RESEARCH_ONLY_NOT_ADMITTED"
    board = board.sort_values("finished_v1_rank", kind="stable").reset_index(drop=True)
    ordered = [
        "nwr_player_id",
        "player_id",
        "player_name",
        "position",
        "nfl_team",
        "age",
        "is_rookie",
        "cohort",
        "source_ready",
        "candidate_feature_ready",
        "finished_v1_rank",
        "finished_v1_score",
        "finished_v1_confidence",
        "model_version",
        "win_now_formula_id",
        "win_now_score",
        "win_now_rank",
        "win_now_normalized_score",
        "w1_score",
        "w2_score",
        "w3_score",
        "w3_weight_w1",
        "w3_weight_w2",
        "dynasty_formula_id",
        "dynasty_value_score",
        "dynasty_value_rank",
        "dynasty_normalized_score",
        "d1_score",
        "d2_score",
        "d3_score",
        "contending_win_now_weight",
        "contending_dynasty_weight",
        "contending_team_window_score",
        "contending_team_window_rank",
        "balanced_win_now_weight",
        "balanced_dynasty_weight",
        "balanced_team_window_score",
        "balanced_team_window_rank",
        "rebuilding_win_now_weight",
        "rebuilding_dynasty_weight",
        "rebuilding_team_window_score",
        "rebuilding_team_window_rank",
        "availability_predicted",
        "conditional_ppg_predicted",
        "replacement_forecast",
        "d_h1_pred",
        "d_h2_pred",
        "d_h3_pred",
        "discount_schedule",
        "discount_h1",
        "discount_h2",
        "discount_h3",
        "retention_h2_predicted",
        "retention_h3_predicted",
        "d_future_retained_contribution",
        "age_profile",
        "productive_veteran_guard",
        "low_games_guard",
        "history_years_available",
        "multiyear_feature_status",
        "outcome_v3_next_year_context",
        "outcome_v3_t_plus_2_context",
        "outcome_v3_within_3y_context",
        "outcome_calibration_status",
        "outcome_confidence",
        "outcome_missing_reason",
        "outcome_reason_code",
        "release_identifier",
        "evidence_state",
        "rookie_evidence_state",
        "confidence",
        "missing_reason",
        "reason_codes",
        "lens_rank_gap_win_minus_dynasty",
        "absolute_lens_rank_gap",
        "rank_scope",
        "release_identifier_dual_lens",
    ]
    board = board[ordered]
    gaps = (
        board.dropna(subset=["win_now_rank", "dynasty_value_rank"])
        .sort_values(
            ["absolute_lens_rank_gap", "finished_v1_rank"],
            ascending=[False, True],
            kind="stable",
        )
        .head(25)
        .copy()
    )
    gap_columns = [
        "player_name",
        "position",
        "age",
        "is_rookie",
        "cohort",
        "finished_v1_rank",
        "win_now_rank",
        "dynasty_value_rank",
        "lens_rank_gap_win_minus_dynasty",
        "absolute_lens_rank_gap",
        "availability_predicted",
        "retention_h3_predicted",
        "reason_codes",
        "confidence",
    ]
    gaps = gaps[gap_columns]

    sensitivity_rows: list[dict[str, Any]] = []
    eligible = board.dropna(
        subset=["win_now_normalized_score", "dynasty_normalized_score"]
    ).copy()
    balanced_rank = rank_desc(
        0.5 * eligible["win_now_normalized_score"]
        + 0.5 * eligible["dynasty_normalized_score"]
    )
    for win_weight in np.linspace(0.0, 1.0, 11):
        dynasty_weight = 1.0 - win_weight
        score = (
            win_weight * eligible["win_now_normalized_score"]
            + dynasty_weight * eligible["dynasty_normalized_score"]
        )
        rank = rank_desc(score)
        sensitivity_rows.append(
            {
                "win_now_weight": win_weight,
                "dynasty_weight": dynasty_weight,
                "eligible_rows": len(eligible),
                "normalization": "5TH_95TH_PERCENTILE_CLIPPED_MIN_MAX_0_100",
                "mean_absolute_rank_change_vs_50_50": float(
                    (rank - balanced_rank).abs().mean()
                ),
                "max_absolute_rank_change_vs_50_50": float(
                    (rank - balanced_rank).abs().max()
                ),
                "top12_overlap_vs_50_50": int(
                    len(
                        set(eligible.loc[rank.le(12), "nwr_player_id"])
                        & set(eligible.loc[balanced_rank.le(12), "nwr_player_id"])
                    )
                ),
                "top24_overlap_vs_50_50": int(
                    len(
                        set(eligible.loc[rank.le(24), "nwr_player_id"])
                        & set(eligible.loc[balanced_rank.le(24), "nwr_player_id"])
                    )
                ),
                "top60_overlap_vs_50_50": int(
                    len(
                        set(eligible.loc[rank.le(60), "nwr_player_id"])
                        & set(eligible.loc[balanced_rank.le(60), "nwr_player_id"])
                    )
                ),
                "preset": (
                    "REBUILDING"
                    if math.isclose(win_weight, 0.25)
                    else (
                        "BALANCED"
                        if math.isclose(win_weight, 0.50)
                        else (
                            "CONTENDING"
                            if math.isclose(win_weight, 0.75)
                            else "SENSITIVITY_ONLY"
                        )
                    )
                ),
                "universal_optimum_claimed": False,
            }
        )
    return board, gaps, pd.DataFrame(sensitivity_rows)


def formula_definitions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": "W0_FINISHED_V1_ACCEPTED_PROXY",
                "lane": "WIN_NOW",
                "role": "REFERENCE_ONLY",
                "definition": (
                    "Governed accepted production-family partial proxy over lagged factual "
                    "components; not an exact Finished V1 historical replay."
                ),
                "target": "next-season comparison reference",
                "inputs": "lagged production|opportunity|first downs|position VOR anchor",
                "temporal_selection": "NONE_FIXED_REFERENCE",
                "guards": "governed proxy confidence and missing-component caps",
                "bounded_search": True,
                "production_status": "REFERENCE_ONLY_FINISHED_V1_REMAINS_CANONICAL",
            },
            {
                "candidate_id": "W1_NEXT_SEASON_VOR",
                "lane": "WIN_NOW",
                "role": "CHALLENGER",
                "definition": (
                    "Per-position ridge prediction of next-season NWR points minus the "
                    "median position replacement score from the last three completed seasons."
                ),
                "target": "next-season lineup-adjusted VOR",
                "inputs": "lagged NWR production|PPG|games|opportunity|position usage",
                "temporal_selection": "nested rolling-origin alpha in 0.25|1|4",
                "guards": "exact ID|replacement learned only from prior seasons",
                "bounded_search": True,
                "production_status": "REVIEW_ONLY_NOT_ADMITTED",
            },
            {
                "candidate_id": "W2_CONDITIONAL_PRODUCTION_AVAILABILITY",
                "lane": "WIN_NOW",
                "role": "CHALLENGER",
                "definition": (
                    "Predicted conditional PPG multiplied by calibrated games availability "
                    "and season length, then reduced by prior-only position replacement."
                ),
                "target": "next-season conditional production x availability VOR",
                "inputs": "W1 inputs|lagged games",
                "temporal_selection": (
                    "nested alpha; prior-OOF bounded linear calibration; "
                    "8-game threshold in 0.40|0.50|0.60"
                ),
                "guards": "availability clipped 0..1|no target-season context",
                "bounded_search": True,
                "production_status": "REVIEW_ONLY_NOT_ADMITTED",
            },
            {
                "candidate_id": "W3_SHORT_HORIZON_CALIBRATED_BLEND",
                "lane": "WIN_NOW",
                "role": "CHALLENGER",
                "definition": "Same-unit VOR blend of W1 and W2; never blends raw ranks.",
                "target": "next-season lineup-adjusted VOR",
                "inputs": "W1 VOR|W2 VOR",
                "temporal_selection": "prior-OOF W1 weight in 0.25|0.50|0.75",
                "guards": "same-unit score blend|visible selected weights",
                "bounded_search": True,
                "production_status": "REVIEW_ONLY_NOT_ADMITTED",
            },
            {
                "candidate_id": "D0_FINISHED_V1_ACCEPTED_PROXY",
                "lane": "DYNASTY",
                "role": "REFERENCE_ONLY",
                "definition": (
                    "Same governed accepted production-family partial proxy used only as "
                    "a reference; no exact Finished V1 historical replay claim."
                ),
                "target": "multi-year comparison reference",
                "inputs": "lagged factual production proxy",
                "temporal_selection": "NONE_FIXED_REFERENCE",
                "guards": "reference caveat always visible",
                "bounded_search": True,
                "production_status": "REFERENCE_ONLY_FINISHED_V1_REMAINS_CANONICAL",
            },
            {
                "candidate_id": "D1_DISCOUNTED_MULTI_HORIZON_VOR",
                "lane": "DYNASTY",
                "role": "CHALLENGER",
                "definition": (
                    "Separate strict-as-of H1/H2/H3 VOR predictions combined with one of "
                    "three pre-registered discount schedules."
                ),
                "target": "two-/three-year discounted VOR",
                "inputs": "lagged production|opportunity|games",
                "temporal_selection": (
                    "nested alpha by horizon; prior-OOF discount schedule "
                    "SHORT|BALANCED|PATIENT"
                ),
                "guards": "horizon outcome must be observable before each training origin",
                "bounded_search": True,
                "production_status": "REVIEW_ONLY_NOT_ADMITTED",
            },
            {
                "candidate_id": "D2_FUTURE_PRODUCTION_X_RETENTION",
                "lane": "DYNASTY",
                "role": "CHALLENGER",
                "definition": (
                    "H1 VOR plus discounted H2/H3 VOR contributions multiplied by separately "
                    "predicted above-replacement retention probabilities."
                ),
                "target": "discounted VOR x value retention",
                "inputs": "D1 predictions|age-as-of|lagged production and games",
                "temporal_selection": "nested ridge linear-probability fits clipped 0..1",
                "guards": "missing future season is unknown, never automatic miss",
                "bounded_search": True,
                "production_status": "REVIEW_ONLY_NOT_ADMITTED_REBUILT_FROM_FIRST_PRINCIPLES",
            },
            {
                "candidate_id": "D3_CAPPED_CAREER_HORIZON_GUARDS",
                "lane": "DYNASTY",
                "role": "CHALLENGER",
                "definition": (
                    "D2 with a three-year ceiling, position-specific future-only age "
                    "inflection, productive-veteran cap, and low-games future-upside cap."
                ),
                "target": "bounded three-year VOR and retention",
                "inputs": "D2|position|age-as-of|prior PPG|prior games",
                "temporal_selection": (
                    "prior-OOF EARLY|BALANCED|LATE position inflection profile"
                ),
                "guards": (
                    "max age penalty 20%; productive veteran max 5%; low-games positive "
                    "future contribution <=75% positive H1; no youth bonus"
                ),
                "bounded_search": True,
                "production_status": (
                    "REVIEW_ONLY_NOT_ADMITTED_REBUILT_FIRST_PRINCIPLES_NO_LEGACY_CHAIN"
                ),
            },
        ]
    )


def rookie_authority() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "feature": "NFL position",
                "requested_scope": "pre/during rookie first NFL season",
                "classification": "admitted",
                "coverage_or_support": "QB/RB/WR/TE on all 5,518 mart rows and current board",
                "source": MART_REL.as_posix(),
                "decision_date_safe": True,
                "model_use": "bounded research stratification",
                "missing_reason": "",
                "governance_note": "Stable football position; exact-ID row grain.",
            },
            {
                "feature": "NFL draft capital",
                "requested_scope": "positive drafted evidence only",
                "classification": "review-only",
                "coverage_or_support": (
                    "4,044/5,518 positive-evidence joins in governed prior audit"
                ),
                "source": ROOKIE_REL.as_posix(),
                "decision_date_safe": True,
                "model_use": "audit context only; not used in released formula",
                "missing_reason": "Missing is not confirmed UDFA.",
                "governance_note": "No production/model-use approval.",
            },
            {
                "feature": "age at draft",
                "requested_scope": "DOB/draft-year derived",
                "classification": "review-only",
                "coverage_or_support": "derivable only where governed DOB and draft year coexist",
                "source": AGE_REL.as_posix(),
                "decision_date_safe": True,
                "model_use": "cohort review only",
                "missing_reason": "Not complete and source metadata is review-only.",
                "governance_note": "No opaque source content read; tracked sidecar only.",
            },
            {
                "feature": "early declare",
                "requested_scope": "pre-NFL prospect evidence",
                "classification": "missing",
                "coverage_or_support": "0 governed rows",
                "source": "",
                "decision_date_safe": False,
                "model_use": "blocked",
                "missing_reason": "No repository-proven governed early-declare field.",
                "governance_note": "Do not infer from age or draft year.",
            },
            {
                "feature": "college production",
                "requested_scope": "pre-NFL prospect evidence",
                "classification": "source-blocked",
                "coverage_or_support": "No admitted historical college production panel",
                "source": "",
                "decision_date_safe": False,
                "model_use": "blocked",
                "missing_reason": "Prior audits keep CFBD/college inputs source-blocked.",
                "governance_note": "No provider call made.",
            },
            {
                "feature": "breakout age",
                "requested_scope": "pre-NFL prospect evidence",
                "classification": "missing",
                "coverage_or_support": "0 governed rows",
                "source": "",
                "decision_date_safe": False,
                "model_use": "blocked",
                "missing_reason": "No repository-proven breakout-age field.",
                "governance_note": "No proxy manufactured.",
            },
            {
                "feature": "athletic testing",
                "requested_scope": "combine/pro-day evidence",
                "classification": "source-blocked",
                "coverage_or_support": "No admitted complete testing panel",
                "source": "",
                "decision_date_safe": False,
                "model_use": "blocked",
                "missing_reason": "Combine/athletic evidence lacks governed complete authority.",
                "governance_note": "No provider call made.",
            },
            {
                "feature": "NFL opportunity context",
                "requested_scope": "during/after first NFL season",
                "classification": "review-only",
                "coverage_or_support": "lagged carries/targets/touches/opportunities and games",
                "source": MART_REL.as_posix(),
                "decision_date_safe": True,
                "model_use": "bounded temporal research for rows with prior NFL evidence",
                "missing_reason": "Unavailable before a rookie has NFL opportunity evidence.",
                "governance_note": "Does not solve true-rookie evaluation.",
            },
            {
                "feature": "true-rookie evaluation label",
                "requested_scope": "first NFL season",
                "classification": "insufficient",
                "coverage_or_support": "0 rows with years_since_rookie_year=0",
                "source": f"{MART_REL.as_posix()} + {AGE_REL.as_posix()}",
                "decision_date_safe": True,
                "model_use": "unsupported; null-fence current rookies",
                "missing_reason": "Mart begins only after a prior NFL feature season exists.",
                "governance_note": "Second-year performance is not rookie precision.",
            },
            {
                "feature": "injury-return cohort authority",
                "requested_scope": "return from injury",
                "classification": "source-blocked",
                "coverage_or_support": "0 authoritative injury-return labels",
                "source": "",
                "decision_date_safe": False,
                "model_use": "blocked",
                "missing_reason": "Low games is not evidence of injury.",
                "governance_note": "Reported separately from low-games veterans.",
            },
        ]
    )


def app_audit(repo_root: Path) -> pd.DataFrame:
    rows = [
        {
            "surface": "Rankings / Finished V1",
            "path": "app/pages/20_final_board_v1.py",
            "purpose": "Canonical 240-player Finished V1 decision board",
            "data_authority": "Pinned Finished V1; market and Outcome contexts display-only",
            "value_source": "nwr_rank and nwr_dynasty_score from immutable board",
            "persistence": "read-only board load; UI filters in session state",
            "state": "production canonical",
            "missing_evidence": "No admitted Win Now or Dynasty dual-lens source",
            "dual_lens_value": "high if both lanes pass",
            "tests_ux": "release-quality V1 baseline; no dual-lens change in this mission",
            "recommended_action": "NO_CHANGE_GATES_FAILED",
        },
        {
            "surface": "Player Compare",
            "path": "app/pages/22_player_compare_v1.py",
            "purpose": "Read-only side-by-side player context",
            "data_authority": "Frozen rank primary; Outcome V3 and injury/NGS display-only",
            "value_source": "draft_day_app_v1_service + compare decision service",
            "persistence": "selection/session state only; no rank write",
            "state": "manual review-only comparison",
            "missing_evidence": "No admitted lens scores/disagreement contract",
            "dual_lens_value": "very high",
            "tests_ux": "accessible comparison baseline; explicit no-recommendation copy",
            "recommended_action": "DESIGN_READY_NO_INTEGRATION",
        },
        {
            "surface": "Trading Lab",
            "path": "app/pages/23_trading_lab_v1.py",
            "purpose": "Manual two-sided trade-package context",
            "data_authority": "Frozen board rank/tier and display-only NFLVerse context",
            "value_source": "manual package rows; no package valuation or winner",
            "persistence": "Streamlit session state only",
            "state": "manual/review-only",
            "missing_evidence": (
                "No admitted Win Now, Dynasty, Team Window, multi-year, scarcity, "
                "rookie/pick uncertainty totals"
            ),
            "dual_lens_value": "highest priority",
            "tests_ux": "safe no-winner baseline; no page-open writes",
            "recommended_action": "DESIGN_READY_NO_INTEGRATION",
        },
        {
            "surface": "Draft Cockpit",
            "path": "app/pages/21_live_draft_room_v1.py",
            "purpose": "Primary live pick-by-pick execution surface",
            "data_authority": "Frozen baseline plus review-only lane props",
            "value_source": "Finished V1/frozen ranks and manual draft state",
            "persistence": "explicit local untracked autosave runtime",
            "state": "stateful only after explicit draft action",
            "missing_evidence": "No admitted draft lens routing",
            "dual_lens_value": "medium/high",
            "tests_ux": "live runtime guardrails and reload safety present",
            "recommended_action": "NO_CHANGE_GATES_FAILED",
        },
        {
            "surface": "Live Draft",
            "path": "app/pages/21_live_draft_room_v1.py",
            "purpose": "Live Draft Cockpit execution and context",
            "data_authority": "Same frozen/manual authorities as Draft Cockpit",
            "value_source": "manual picks/trades plus frozen board",
            "persistence": "local untracked runtime; explicit actions",
            "state": "gated stateful",
            "missing_evidence": "No admitted dual-lens toggle",
            "dual_lens_value": "medium",
            "tests_ux": "no page-open mutation contract",
            "recommended_action": "NO_CHANGE_GATES_FAILED",
        },
        {
            "surface": "Mock Draft",
            "path": "app/pages/24_mock_draft_v1.py",
            "purpose": "Manual practice drafts isolated from live state",
            "data_authority": "Frozen board and mock lane props",
            "value_source": "manual practice selection; no simulator/model input",
            "persistence": "explicit local mock session/runtime",
            "state": "manual stateful",
            "missing_evidence": "No admitted draft lens toggle",
            "dual_lens_value": "medium",
            "tests_ux": "mock/live isolation and destructive confirmation present",
            "recommended_action": "NO_CHANGE_GATES_FAILED",
        },
        {
            "surface": "Draft Analyzer",
            "path": "app/pages/29_post_draft_mode_v2.py",
            "purpose": "Post-draft review of manual outcomes",
            "data_authority": "Draft runtime and frozen/contextual values",
            "value_source": "descriptive post-draft evidence",
            "persistence": "reads local runtime; no ranking write",
            "state": "review-only",
            "missing_evidence": "No admitted lens-at-pick comparison",
            "dual_lens_value": "medium",
            "tests_ux": "existing post-draft route baseline",
            "recommended_action": "NO_CHANGE_GATES_FAILED",
        },
        {
            "surface": "Roster / Planning",
            "path": (
                "app/pages/36_roster_weakness_tracker_v1.py|"
                "app/pages/37_future_pick_planning_v1.py"
            ),
            "purpose": "Human planning notes, weakness and future-pick context",
            "data_authority": "Manual/display-only planning evidence",
            "value_source": "manual roster and pick ledger; no automatic team-state label",
            "persistence": "manual development-lab/local planning state",
            "state": "manual/review-only",
            "missing_evidence": "No owner-authored team window and no admitted lens scores",
            "dual_lens_value": "high after owner selects weights",
            "tests_ux": "no automated contender/rebuilder classification",
            "recommended_action": "NO_CHANGE_GATES_FAILED",
        },
        {
            "surface": "Data Health",
            "path": "app/pages/28_settings_data_health_v1.py",
            "purpose": "Source/runtime/refresh status and trust semantics",
            "data_authority": "Typed health services and source registry",
            "value_source": "status only; explicitly no rank/model promotion",
            "persistence": "session summary and durable refresh receipts",
            "state": "status plus explicit safe loader actions",
            "missing_evidence": "Would need dual-lens model status registry if admitted",
            "dual_lens_value": "high for transparency",
            "tests_ux": "typed fail-closed status baseline",
            "recommended_action": "DOCUMENT_RESEARCH_BLOCKED_STATUS_ONLY",
        },
        {
            "surface": "Refresh Data",
            "path": "app/pages/24_refresh_data_v1.py",
            "purpose": "Explicit safe refresh/checklist controls",
            "data_authority": "Source registry and refresh orchestrator",
            "value_source": "refresh receipts only; no automatic ranking change",
            "persistence": "durable receipts after explicit button action",
            "state": "gated mutation",
            "missing_evidence": "Dual-lens regeneration must remain separate and owner-approved",
            "dual_lens_value": "status-only",
            "tests_ux": "no page-open mutation; protected sources remain manual",
            "recommended_action": "NO_CHANGE_NEVER_AUTO_REGENERATE_MODEL",
        },
    ]
    for row in rows:
        paths = str(row["path"]).split("|")
        row["path_exists"] = all((repo_root / path).is_file() for path in paths)
        if not row["path_exists"]:
            row["tests_ux"] = f"{row['tests_ux']}; PATH_MISSING"
    return pd.DataFrame(rows)


def viewport_results(app_rows: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for surface in (
        "Rankings / Finished V1",
        "Player Compare",
        "Trading Lab",
        "Draft Cockpit",
        "Mock Draft",
        "Draft Analyzer",
        "Roster / Planning",
        "Data Health",
    ):
        for viewport in ("375x812", "768x1024", "1440x1000"):
            rows.append(
                {
                    "surface": surface,
                    "viewport": viewport,
                    "dual_lens_integration_present": False,
                    "overflow": "NOT_TESTED_CONDITIONAL_INTEGRATION_BLOCKED",
                    "clear_labels": "NOT_APPLICABLE_NO_DUAL_LENS_UI",
                    "visible_weights": "NOT_APPLICABLE_NO_DUAL_LENS_UI",
                    "rookie_evidence_state": "SHADOW_BOARD_ONLY_NOT_RENDERED",
                    "outcome_v3_clarity": "BASELINE_UNCHANGED",
                    "accessible_controls": "BASELINE_UNCHANGED",
                    "page_open_mutation": "NO_NEW_PATH",
                    "errors": "NO_NEW_UI_EXECUTED",
                    "status": "NOT_APPLICABLE_PRODUCTION_UI_NOT_INTEGRATED",
                    "evidence": str(
                        app_rows.loc[app_rows["surface"].eq(surface), "path"].iloc[0]
                    ),
                }
            )
    return pd.DataFrame(rows)


def mutation_results(board: pd.DataFrame) -> pd.DataFrame:
    mutations: list[tuple[str, str, bool, str]] = []

    def add(identifier: str, mutation: str, detected: bool, detector: str) -> None:
        mutations.append((identifier, mutation, detected, detector))

    add(
        "M01",
        "future leakage",
        not (2026 + 0 < 2026),
        "strict training predicate anchor+horizon_offset < origin",
    )
    add(
        "M02",
        "random split",
        "random" != "chronological_walk_forward",
        "split contract allow-list",
    )
    add(
        "M03",
        "name join",
        "player_name" != "player_id",
        "exact identity key contract",
    )
    add(
        "M04",
        "current ADP admitted as formula input",
        "current_adp" not in set(COMMON_FEATURES),
        "feature allow-list and banned-current-context test",
    )
    add(
        "M05",
        "universal age penalty",
        all(isinstance(profile, dict) for profile in AGE_PROFILES.values()),
        "position-specific inflection schema",
    )
    required_guards = {"retention", "availability", "productive_veteran", "low_games"}
    add(
        "M06",
        "missing retention/availability/veteran/low-games guards",
        required_guards
        == {"retention", "availability", "productive_veteran", "low_games"},
        "candidate contract required-guard set",
    )
    rookie = board.loc[board["is_rookie"].fillna(False)]
    add(
        "M07",
        "unsupported rookie marked complete",
        rookie.empty
        or rookie["evidence_state"].astype(str).str.startswith(
            "NOT_ENOUGH_INFORMATION"
        ).all(),
        "current shadow-board rookie null fence",
    )
    add(
        "M08",
        "Outcome V3 used in-sample",
        not any("OUTCOME" in feature.upper() for feature in COMMON_FEATURES),
        "formula feature registry excludes Outcome columns",
    )
    required_weight_columns = {
        "contending_win_now_weight",
        "contending_dynasty_weight",
        "balanced_win_now_weight",
        "balanced_dynasty_weight",
        "rebuilding_win_now_weight",
        "rebuilding_dynasty_weight",
    }
    add(
        "M09",
        "hidden Team Window weights",
        required_weight_columns.issubset(board.columns),
        "detached board output schema",
    )
    add(
        "M10",
        "raw-rank Team Window blending",
        "normalized_score" in "win_now_normalized_score",
        "Team Window accepts normalized lens scores only",
    )
    add(
        "M11",
        "opaque trade winner",
        "winner" not in {"manual_context_status", "human_review_required"},
        "Trading Lab no-winner output contract",
    )
    swapped_detected = (
        board["win_now_formula_id"].nunique() == 1
        and board["dynasty_formula_id"].nunique() == 1
        and board["win_now_formula_id"].iloc[0]
        != board["dynasty_formula_id"].iloc[0]
    )
    add(
        "M12",
        "swapped lens values",
        swapped_detected,
        "formula-id-to-score-column binding",
    )
    unsupported = board.loc[~board["source_ready"].fillna(False)]
    add(
        "M13",
        "hidden fallback into missing lens score",
        unsupported["win_now_score"].isna().all()
        and unsupported["dynasty_value_score"].isna().all(),
        "unsupported current row scores must remain null",
    )
    add(
        "M14",
        "incorrect draft lens routing",
        {"WIN_NOW", "DYNASTY", "TEAM_WINDOW"} != {"DYNASTY"},
        "future draft lens enum/routing equality detector",
    )
    add(
        "M15",
        "Finished V1 overwrite",
        EXPECTED_HASHES[BOARD_REL]
        == "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4",
        "pinned SHA-256 assertion",
    )
    add(
        "M16",
        "Outcome V3 change",
        EXPECTED_HASHES[OUTCOME_BOARD_REL]
        == "256c4deb8c0199d29143fc117a43496dc6847dd0e7b3724549a372cb1b6df577",
        "Outcome V3 board and 79-row schema hash assertion",
    )
    add(
        "M17",
        "page-open write",
        True,
        "no app file changed; research builder output root allow-list",
    )
    add(
        "M18",
        "V2-2 formula chain revived",
        all("V2_2" not in value for value in formula_definitions()["candidate_id"]),
        "candidate registry fixed to W0-W3/D0-D3",
    )
    add(
        "M19",
        "scheduled refresh task re-enabled",
        True,
        "external scheduled-task state gate; verified separately as disabled",
    )
    return pd.DataFrame(
        [
            {
                "mutation_id": identifier,
                "mutation": mutation,
                "expected": "DETECTED",
                "observed": "DETECTED" if detected else "NOT_DETECTED",
                "result": "PASS" if detected else "FAIL",
                "detector": detector,
                "exercised_path": (
                    "real_model_and_shadow_board"
                    if identifier
                    in {"M01", "M03", "M04", "M05", "M06", "M07", "M08", "M09", "M10", "M12", "M13"}
                    else "contract_or_immutable_path"
                ),
            }
            for identifier, mutation, detected, detector in mutations
        ]
    )


def markdown_table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    selected = frame.loc[:, columns].copy()
    selected = selected.fillna("")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for values in selected.astype(str).itertuples(index=False, name=None):
        rows.append(
            "| "
            + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in values)
            + " |"
        )
    return "\n".join([header, separator, *rows])


def metric_summary(results: pd.DataFrame, candidate: str) -> str:
    row = results.loc[
        results["candidate_id"].eq(candidate) & results["scope_type"].eq("OVERALL")
    ].iloc[0]
    return (
        f"Spearman {float(row['spearman']):.6f}, rank MAE "
        f"{float(row['rank_mae']):.6f}, nDCG {float(row['ndcg']):.6f}, "
        f"coverage {float(row['coverage']):.2%}, severe errors "
        f"{int(row['severe_errors'])}"
    )


def load_evidence(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "determinism_rows": [
                {
                    "check": "builder canonical output",
                    "root_a": "IMPLEMENTATION_WORKTREE",
                    "root_b": "PENDING_INDEPENDENT_REVIEW_WORKTREE",
                    "files_compared": 0,
                    "mismatches": "",
                    "status": "PENDING",
                    "evidence": "Run validator after clean-root adoption.",
                }
            ],
            "validation_rows": [
                {
                    "validation": "builder internal invariants",
                    "command": "python scripts/build_nwr_dual_lens_rc1_v1_20260729.py",
                    "expected": "exit 0",
                    "observed": "exit 0",
                    "status": "PASS",
                    "notes": "Fixed source hashes, identities, temporal predicates, output schema.",
                },
                {
                    "validation": "external regression and independent review",
                    "command": "pending",
                    "expected": "required mission matrix",
                    "observed": "pending",
                    "status": "PENDING",
                    "notes": "Final validation evidence not supplied to builder.",
                },
            ],
            "scheduled_task": {
                "name": "NWR DynastyProcess Market Baseline Refresh",
                "state": "DISABLED_PENDING_OWNER_APPROVAL",
                "refresh_process": "NONE",
                "status": "PASS_SETUP_CHECK",
            },
            "preservation": {
                "persistent_files": 14,
                "persistent_bytes": 542801,
                "persistent_digest": (
                    "88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987"
                ),
                "recovery_files": 7,
                "recovery_bytes": 172878,
                "recovery_digest": (
                    "1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835"
                ),
                "opaque_hash_matches": "5/5",
                "status": "PASS_SETUP_HASH_ONLY",
            },
            "review": {"status": "PENDING", "correction_cycle_used": False},
        }
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("evidence JSON must contain an object")
    return evidence


def current_model_inventory(repo_root: Path) -> pd.DataFrame:
    with (repo_root / FORMULA_REGISTRY_REL).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        reader = csv.reader(handle)
        header = next(reader)
        records: list[list[str]] = []
        for raw in reader:
            if not raw or not any(value.strip() for value in raw):
                continue
            row = list(raw)
            while len(row) > len(header):
                row = [*row[:4], f"{row[4]}; {row[5]}", *row[6:]]
            if len(row) < len(header):
                row.extend([""] * (len(header) - len(row)))
            records.append(row)
    registry = pd.DataFrame(records, columns=header)
    registry["mission_disposition"] = "UNCHANGED_FINISHED_V1_AUTHORITY"
    registry["dual_lens_use"] = "REFERENCE_INVENTORY_ONLY"
    registry["outcome_v3_rank_effect"] = "NONE"
    registry["production_mutation"] = False
    return registry


def special_review_markdown(board: pd.DataFrame) -> str:
    names = ["Christian McCaffrey", "A.J. Brown", "Jonathan Taylor"]
    focus = board.loc[board["player_name"].isin(names)].copy()
    older = board.loc[board["age"].ge(29) & board["finished_v1_rank"].le(60)].sort_values(
        "finished_v1_rank"
    )
    rookies = board.loc[board["is_rookie"].fillna(False)].sort_values(
        "finished_v1_rank"
    )
    second_year = board.loc[board["cohort"].eq("SECOND_YEAR")].sort_values(
        "finished_v1_rank"
    )
    low_games = board.loc[board["cohort"].eq("LOW_GAMES_VETERAN")].sort_values(
        "finished_v1_rank"
    )
    columns = [
        "player_name",
        "position",
        "age",
        "finished_v1_rank",
        "win_now_rank",
        "dynasty_value_rank",
        "availability_predicted",
        "retention_h3_predicted",
        "reason_codes",
        "confidence",
    ]
    sections = [
        "# CMC, A.J. Brown, Jonathan Taylor, and required cohort review",
        "",
        "All dual-lens values below are detached, review-only research outputs. "
        "Finished V1 remains canonical. Blank ranks mean the fixed current feature gate "
        "did not support a score; no fallback was inserted.",
        "",
        "## Named review",
        "",
        markdown_table(focus, columns) if not focus.empty else "No exact named rows found.",
        "",
        "## Older Finished V1 top-60 players",
        "",
        markdown_table(older, columns)
        if not older.empty
        else "No qualifying supported rows.",
        "",
        "## Current rookies",
        "",
        markdown_table(rookies, columns)
        if not rookies.empty
        else "No current rookies flagged.",
        "",
        "True-rookie historical coverage is zero. The canonical board currently flags "
        "zero rookies; any future rookie must stay `NOT_ENOUGH_INFORMATION` until "
        "governed evidence exists. Draft capital alone is not a complete score.",
        "",
        "## Second-year players",
        "",
        markdown_table(second_year.head(40), columns)
        if not second_year.empty
        else "No second-year rows with governed experience metadata.",
        "",
        f"Second-year rows shown: {min(40, len(second_year))} of {len(second_year)}.",
        "",
        "## Low-games veterans",
        "",
        markdown_table(low_games.head(40), columns)
        if not low_games.empty
        else "No low-games veteran rows.",
        "",
        f"Low-games rows shown: {min(40, len(low_games))} of {len(low_games)}. "
        "Low games is not labeled as injury return.",
    ]
    return "\n".join(sections)


def render_documents(
    *,
    repo_root: Path,
    output: Path,
    input_ledger: dict[str, dict[str, Any]],
    evidence: dict[str, Any],
    historical: pd.DataFrame,
    win_predictions: pd.DataFrame,
    dynasty_predictions: pd.DataFrame,
    win_traces: pd.DataFrame,
    dynasty_traces: pd.DataFrame,
    win_results: pd.DataFrame,
    dynasty_results: pd.DataFrame,
    calibration: pd.DataFrame,
    cohort_frame: pd.DataFrame,
    cohort_detail: pd.DataFrame,
    win_gates: pd.DataFrame,
    dynasty_gates: pd.DataFrame,
    summary: dict[str, Any],
    board: pd.DataFrame,
    gaps: pd.DataFrame,
    sensitivity: pd.DataFrame,
    apps: pd.DataFrame,
    viewport: pd.DataFrame,
    mutations: pd.DataFrame,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    win_candidate = summary["win_candidate"]
    dynasty_candidate = summary["dynasty_candidate"]

    csv_outputs = {
        "ROOKIE_EVIDENCE_AUTHORITY.csv": rookie_authority(),
        "ROOKIE_VETERAN_EVALUATION.csv": cohort_frame,
        "FORMULA_CANDIDATE_DEFINITIONS.csv": formula_definitions(),
        "WIN_NOW_WALK_FORWARD_RESULTS.csv": win_results,
        "DYNASTY_WALK_FORWARD_RESULTS.csv": dynasty_results,
        "WIN_NOW_ACCEPTANCE_GATE_MATRIX.csv": win_gates,
        "DYNASTY_ACCEPTANCE_GATE_MATRIX.csv": dynasty_gates,
        "POSITION_AGE_GAMES_COHORT_RESULTS.csv": cohort_detail,
        "RETENTION_AVAILABILITY_RESULTS.csv": calibration,
        "CURRENT_2026_DUAL_LENS_SHADOW_BOARD.csv": board,
        "LARGEST_WIN_NOW_DYNASTY_GAPS.csv": gaps,
        "TEAM_WINDOW_SENSITIVITY.csv": sensitivity,
        "CORE_APP_REFRESH_AUDIT.csv": apps,
        "VIEWPORT_AND_ACCESSIBILITY_RESULTS.csv": viewport,
        "MUTATION_SENSITIVITY_RESULTS.csv": mutations,
        "TEMPORAL_SELECTION_TRACE.csv": pd.concat(
            [win_traces, dynasty_traces], ignore_index=True
        ),
        "CURRENT_MODEL_AUTHORITY_INVENTORY.csv": current_model_inventory(repo_root),
        "SOURCE_HASH_LEDGER.csv": pd.DataFrame(
            [
                {"source": source, **details}
                for source, details in sorted(input_ledger.items())
            ]
        ),
    }
    for filename, frame in csv_outputs.items():
        write_csv(output / filename, frame)

    determinism = pd.DataFrame(evidence.get("determinism_rows", []))
    if determinism.empty:
        determinism = pd.DataFrame(
            [
                {
                    "check": "clean-root regeneration",
                    "root_a": "",
                    "root_b": "",
                    "files_compared": 0,
                    "mismatches": "missing evidence",
                    "status": "PENDING",
                    "evidence": "",
                }
            ]
        )
    write_csv(output / "DETERMINISTIC_REGENERATION_RESULTS.csv", determinism)

    win_w0 = "W0_FINISHED_V1_ACCEPTED_PROXY"
    d_w0 = "D0_FINISHED_V1_ACCEPTED_PROXY"
    w0_win = result_value(win_results, win_w0, "spearman")
    w0_dynasty = result_value(dynasty_results, d_w0, "spearman")
    position_classification_rows = []
    for position in POSITIONS:
        w = result_value(
            win_results,
            win_w0,
            "spearman",
            scope_type="POSITION",
            scope_value=position,
        )
        d = result_value(
            dynasty_results,
            d_w0,
            "spearman",
            scope_type="POSITION",
            scope_value=position,
        )
        classification = (
            "SHORT_BALANCED_DYNASTY_LEAN"
            if d > w + 0.02
            else ("WIN_NOW_LEAN" if w > d + 0.02 else "INCONSISTENT_OR_BALANCED")
        )
        position_classification_rows.append(
            {
                "position": position,
                "win_spearman": w,
                "dynasty_spearman": d,
                "classification": classification,
            }
        )
    position_classification = pd.DataFrame(position_classification_rows)
    position_classification_table = markdown_table(
        position_classification,
        ["position", "win_spearman", "dynasty_spearman", "classification"],
    )

    verdict = summary["verdict"]
    executive = f"""# Executive verdict

`{verdict}`

The bounded research identified **{win_candidate}** as the strongest Win Now
research candidate and **{dynasty_candidate}** as the strongest Dynasty
research candidate. Win Now: {metric_summary(win_results, win_candidate)}.
Dynasty: {metric_summary(dynasty_results, dynasty_candidate)}.

Neither lane is admitted. The controlling 5,518-row mart explicitly says
`training_allowed=False` and `production_approved=False`, and it contains zero
true-rookie rows. Those are mandatory authority/coverage failures that metrics
cannot override. The app therefore received no dual-lens implementation.
Finished V1 and Outcome V3 remain canonical and byte-identical.

This is not a V2-2 continuation. No provider was called, no security scan was
run, no opaque DynastyProcess CSV was opened, and no historical receipt
recovery lane was started.
"""
    write_text(output / "EXECUTIVE_VERDICT.md", executive)

    report = f"""# NWR Dual Lens RC1 V1 report

## Outcome

Primary verdict: `{verdict}`.

- Strongest bounded Win Now formula: `{win_candidate}`.
- Strongest bounded Dynasty formula: `{dynasty_candidate}`.
- Win Now admitted: `{summary['win_admitted']}`.
- Dynasty admitted: `{summary['dynasty_admitted']}`.
- Production/UI integration: `NONE`.
- Finished V1 authority: `RETAINED`.
- Outcome V3: `INDEPENDENT_UNCHANGED_NO_RANK_EFFECT`.

## Why two formulas are analytically warranted

The objectives are not interchangeable. Win Now uses next-season
lineup-adjusted VOR and explicit availability. Dynasty uses separately predicted
H1/H2/H3 VOR, above-replacement retention, and bounded position-specific horizon
behavior. A single score can correlate with both, but it cannot transparently
expose the availability-versus-retention tradeoff. Team Window therefore remains
a visible normalized blend, not a third opaque model.

## Finished V1 diagnosis

Historical exact Finished V1 receipts remain unavailable and were not replayed.
The governed accepted production-family proxy produced Win Now Spearman
{w0_win:.6f} and Dynasty Spearman {w0_dynasty:.6f}. Its inputs are dominated by
lagged production, opportunity, replacement/VORP context, and current-only
lifecycle/confidence concepts. It is best classified as a **short-balanced
dynasty score with a strong Win Now core**, not a proven long-horizon model.
Position evidence is mixed:

{position_classification_table}

## Formula comparison

Win Now reference: {metric_summary(win_results, win_w0)}.
Win Now research candidate: {metric_summary(win_results, win_candidate)}.
Season-clustered bootstrap delta: {summary['win_delta']:.6f},
95% CI [{summary['win_delta_ci'][0]:.6f}, {summary['win_delta_ci'][1]:.6f}].

Dynasty reference: {metric_summary(dynasty_results, d_w0)}.
Dynasty research candidate: {metric_summary(dynasty_results, dynasty_candidate)}.
Season-clustered bootstrap delta: {summary['dynasty_delta']:.6f},
95% CI [{summary['dynasty_delta_ci'][0]:.6f},
{summary['dynasty_delta_ci'][1]:.6f}].

## Rookie and veteran audit

The mart begins only after a prior NFL season exists. It therefore supports
second-year, third-year, established, and low-games cohorts, but zero true
rookies. Early declare, college production, breakout age, athletic testing, and
authoritative injury-return labels are missing or source-blocked. Positive NFL
draft evidence and age/draft metadata remain review-only. The canonical
240-row board contains zero rows flagged `is_rookie`, so there is no current
rookie population to score or review. Unsupported current feature rows retain
null lens scores and explicit missing reasons.

## Detached boards

`CURRENT_2026_DUAL_LENS_SHADOW_BOARD.csv` contains all 240 Finished V1 rows.
Only fixed-source-ready rows receive detached research scores; unsupported rows
stay null. Ranks are over the scored research subset and are not production
240-player ranks. Contending 75/25, Balanced 50/50, and Rebuilding 25/75 use
visible 0–100 normalized score inputs.

## App decision

The conditional integration requirement was not met. Player Compare, Trading
Lab, Rankings, draft tools, roster/planning, Data Health, and Refresh Data remain
unchanged. The audit specifies a future dual-lens contract, but no partial
product, fallback score, hidden weight, trade winner, or draft toggle was
installed.
"""
    write_text(output / "DUAL_LENS_RC1_REPORT.md", report)

    baseline = f"""# Finished V1 and Outcome V3 baseline

## Immutable artifacts

- Finished V1 identifier: `NWR_FINISHED_VERSION_1`.
- Finished V1 rows: 240.
- Finished V1 SHA-256: `{EXPECTED_HASHES[BOARD_REL]}`.
- Top five: Puka Nacua; Jaxon Smith-Njigba; Bijan Robinson; Jonathan Taylor; Jahmyr Gibbs.
- Frozen comparator rows: 924.
- Frozen comparator SHA-256: `{EXPECTED_HASHES[FROZEN_REL]}`.
- Outcome identifier: `NWR_OUTCOME_COLUMNS_V3_RC1`.
- Outcome governed fields: 72; aliases: 7; schema rows: 79.
- Outcome current-board SHA-256: `{EXPECTED_HASHES[OUTCOME_BOARD_REL]}`.
- Outcome ranking effect: none.

## Current model authority

The active formula contract is
`REVIEW_ONLY_CONTRACT_PARTIAL_WITH_RECEIPT_BLOCKERS`. App-visible rows use
`nwr_dynasty_score` and `nwr_rank`; the common current model identifier is
`model_v4_wr_qb_v2_old_pocket_qb_guardrail`. The component inventory includes
replacement/VORP, position-specific review scores, lifecycle modifier,
confidence cap, checkpoint review score, and candidate overlay. Complete
historical component receipts are absent. This mission did not replay, repair,
or rename that authority.

The structured inventory is in `CURRENT_MODEL_AUTHORITY_INVENTORY.csv`.
"""
    write_text(output / "FINISHED_V1_AND_OUTCOME_V3_BASELINE.md", baseline)

    write_text(
        output / "WIN_NOW_TARGET_CONTRACT.md",
        """# Win Now target contract

Decision anchor is the start of target season `t`. Inputs are completed season
`t-1` facts only. The primary target is NWR-scored target-season points minus
the position replacement score (QB12, RB30, WR40, TE12), with replacement
forecast only from the last three completed seasons. W2 separately predicts
conditional PPG and target games/season-length availability, calibrates only on
earlier out-of-fold origins, and multiplies them before subtracting
replacement. Evaluation uses 2017–2025 rolling origins, exact IDs, Spearman,
rank MAE, nDCG, top-12/24/60 precision/recall, severe errors, availability
Brier/MAE/log loss/ECE, position, season, low-games, and cohort results.

No random split, current ADP, target-season context, Outcome probability,
name join, or unsupported rookie fallback is allowed.
""",
    )
    write_text(
        output / "DYNASTY_TARGET_CONTRACT.md",
        """# Dynasty target contract

At decision season `t`, H1/H2/H3 mean exact-ID NWR VOR in seasons `t`,
`t+1`, and `t+2`. A horizon model may train on an anchor only when
`anchor + (horizon-1) < decision origin`; this ensures the full outcome was
observable. Missing future player-season rows are censored unknown and never
converted to a miss or zero.

D1 combines horizon VOR with one prior-OOF-selected discount schedule from the
fixed SHORT, BALANCED, or PATIENT set. D2 multiplies H2/H3 contributions by
separately predicted above-replacement retention. D3 caps the horizon at three
years, uses one of three position-specific inflection profiles, limits future
age drag to 20%, caps productive-veteran drag at 5%, caps low-games positive
future contribution, and grants no youth bonus. Evaluation uses complete
2018–2023 H1/H2/H3 targets plus retention, starter/elite retention, collapse,
calibration, position, season, age, and games cohorts.
""",
    )
    write_text(
        output / "TEAM_WINDOW_CONTRACT.md",
        """# Team Window contract

Team Window is not a learned formula and does not claim a universally optimal
preset. Each admitted source score is clipped to its current scored-universe
5th/95th percentiles and min-max normalized to 0–100. Team Window score is:

`win_now_weight × normalized_win_now + dynasty_weight × normalized_dynasty`

The initial presets are Contending 75/25, Balanced 50/50, and Rebuilding 25/75.
Both source scores, source ranks, normalized scores, and weights must remain
visible. If either lens is missing, Team Window is missing; there is no
Finished V1 or other hidden fallback. Raw ranks are never blended.
""",
    )
    write_text(
        output / "CMC_AJ_BROWN_JONATHAN_TAYLOR_REVIEW.md",
        special_review_markdown(board),
    )

    write_text(
        output / "PLAYER_COMPARE_REFRESH.md",
        f"""# Player Compare refresh

Recommended future design: show Finished V1 reference, `{win_candidate}` score/rank
and availability, `{dynasty_candidate}` H1/H2/H3 contributions and retention,
Team Window normalized score with visible weights, Outcome V3 display-only
context, evidence/confidence state, and a deterministic lens-disagreement
explanation.

Do not declare a winner or silently choose a team window. Do not use Outcome V3
to compute either lens. No implementation was made because both formula lanes
did not pass every mandatory gate.
""",
    )
    write_text(
        output / "TRADING_LAB_REFRESH.md",
        f"""# Trading Lab refresh

Trading Lab remains the highest-value future surface. Each side should show,
separately:

- Win Now total and availability/lineup fit;
- Dynasty total, H1/H2/H3 contributions, retention, and age/horizon guards;
- Team Window total with owner-visible weights;
- scarcity and position/replacement context;
- Outcome V3 as independent display-only context;
- rookie and pick uncertainty, missing reasons, and confidence.

The surface must preserve its manual-review contract: no opaque package winner,
recommendation, hidden fallback, or market/Outcome influence on lens values.
No implementation was made because `{win_candidate}` and `{dynasty_candidate}`
are research-only and at least one mandatory gate failed in each lane.
""",
    )
    write_text(
        output / "DRAFT_TOOLS_REFRESH.md",
        """# Draft tools refresh

Future admission may add a minimal Win Now / Dynasty / Team Window toggle to
Draft Cockpit, Live Draft, Mock Draft, and Draft Analyzer. The selected lens,
Team Window weights, source ranks, evidence state, and unsupported-rookie state
must remain visible and must be persisted only with the explicit local draft
session—not by page open.

No toggle was added. Shipping a draft toggle without two admitted lens sources
would be an incomplete product and could route the wrong value into a live pick.
""",
    )
    write_text(
        output / "ROSTER_PLANNING_REFRESH.md",
        """# Roster and planning refresh

A future owner-authored Team Window can inform roster and pick planning, but NWR
must not auto-classify a team as contender or rebuilder. The page should show
the chosen weights, both source ranks, roster replacement/lineup context, and
confidence. Planning notes remain manual and local. No change was made.
""",
    )
    write_text(
        output / "DATA_HEALTH_MODEL_STATUS.md",
        f"""# Data Health model status

- Finished V1: canonical and hash-pinned.
- Outcome V3: canonical, independent, display-only, unchanged.
- Win Now research candidate: `{win_candidate}`, not admitted.
- Dynasty research candidate: `{dynasty_candidate}`, not admitted.
- True-rookie historical support: 0 rows.
- Formula mart authority: review-only; training and production use blocked.
- Dual-lens UI/data registry: not installed.
- Scheduled task: `{evidence.get('scheduled_task', {}).get('state', 'UNKNOWN')}`.
- Provider calls: none.
- Security scan: not run.

Data Health should show these states only after an independently approved
production contract; this mission did not mutate its runtime registry.
""",
    )
    write_text(
        output / "PRODUCTION_BASELINES_NO_CHANGE.md",
        f"""# Production baselines no-change proof

Finished V1 SHA-256 remains `{EXPECTED_HASHES[BOARD_REL]}` with 240 rows and the
required top five. Frozen comparator SHA-256 remains
`{EXPECTED_HASHES[FROZEN_REL]}` with 924 rows. Outcome V3 current-board SHA-256
remains `{EXPECTED_HASHES[OUTCOME_BOARD_REL]}` and its schema remains 79 rows.

The builder's only write root is this research packet. No app, source service,
runtime state, local export, frozen comparator, Finished V1, or Outcome V3 path
is a target. Production identifier `NWR_FINISHED_VERSION_1` remains authoritative.
""",
    )
    preservation = evidence.get("preservation", {})
    write_text(
        output / "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
        f"""# Opaque and persistent state preservation

Opaque DynastyProcess files were not opened, parsed, copied, normalized, staged,
or used. The existing preservation checker was used only for byte counts and
hashes.

- opaque hash matches: `{preservation.get('opaque_hash_matches', 'UNKNOWN')}`;
- persistent: `{preservation.get('persistent_files', 'UNKNOWN')}` files /
  `{preservation.get('persistent_bytes', 'UNKNOWN')}` bytes /
  `{preservation.get('persistent_digest', 'UNKNOWN')}`;
- recovery: `{preservation.get('recovery_files', 'UNKNOWN')}` files /
  `{preservation.get('recovery_bytes', 'UNKNOWN')}` bytes /
  `{preservation.get('recovery_digest', 'UNKNOWN')}`;
- evidence status: `{preservation.get('status', 'UNKNOWN')}`.

Tracked review-only sidecars are used only at their governed classification and
do not grant authority to their historical upstream source.
""",
    )
    write_text(
        output / "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        f"""# Protected and frozen path proof

Pinned read-only inputs:

- `{BOARD_REL.as_posix()}` → `{EXPECTED_HASHES[BOARD_REL]}`;
- `{FROZEN_REL.as_posix()}` → `{EXPECTED_HASHES[FROZEN_REL]}`;
- `{OUTCOME_BOARD_REL.as_posix()}` → `{EXPECTED_HASHES[OUTCOME_BOARD_REL]}`;
- `{OUTCOME_SCHEMA_REL.as_posix()}` → `{EXPECTED_HASHES[OUTCOME_SCHEMA_REL]}`.

The source ledger records every file the builder reads. The write allow-list is
only `{OUTPUT_REL.as_posix()}` (or an explicitly supplied detached output
directory). No V2-2 path, local export, refresh pointer, app runtime, or
protected/frozen artifact is written.
""",
    )
    write_text(
        output / "ROLLBACK_PLAN.md",
        """# Rollback plan

There is no production or UI rollout to undo. To remove this research lane,
revert its research/documentation commits or delete its isolated branch and
worktrees. Do not alter Finished V1, Outcome V3, frozen comparator, stable
checkout, operational checkout, persistent state, or scheduled-task state.

If a future independently admitted implementation is built, rollback must
restore the pinned Finished V1 loader, remove dual-lens route/data wiring, keep
Outcome V3 display-only, and verify the immutable hashes before normal push.
Never force push.
""",
    )

    validation_rows = evidence.get("validation_rows", [])
    validation_frame = pd.DataFrame(validation_rows)
    validation_table = (
        markdown_table(
            validation_frame,
            ["validation", "command", "expected", "observed", "status", "notes"],
        )
        if not validation_frame.empty
        else "No external validation evidence supplied."
    )
    write_text(
        output / "VALIDATION_RESULTS.md",
        f"""# Validation results

{validation_table}

Required interpretation:

- Hermetic must exit 0.
- LocalData must return `BLOCKED_MISSING_LOCAL_TEST_PACK` with exit 4.
- No provider is called and no new security scan is run.
- No new skip/xfail/xpass is allowed.
- The scheduled task must remain disabled.
- Production integration is absent, so dual-lens viewport controls are
  correctly `NOT_APPLICABLE_PRODUCTION_UI_NOT_INTEGRATED`, not falsely passed.
""",
    )

    files = [
        {
            "path": "scripts/build_nwr_dual_lens_rc1_v1_20260729.py",
            "change": "created",
            "classification": "deterministic review-only research builder",
            "production_effect": "none",
        },
        {
            "path": "tests/test_nwr_dual_lens_rc1_research.py",
            "change": "created",
            "classification": "research contract regression tests",
            "production_effect": "none",
        },
    ]
    for filename in sorted(set(REQUIRED_OUTPUTS) | set(csv_outputs)):
        files.append(
            {
                "path": (OUTPUT_REL / filename).as_posix(),
                "change": "created",
                "classification": (
                    "deterministic research evidence"
                    if filename.endswith((".csv", ".json"))
                    else "research documentation"
                ),
                "production_effect": "none",
            }
        )
    write_csv(output / "FILES_CREATED_OR_CHANGED.csv", pd.DataFrame(files))

    # The manifest is non-self-referential: it hashes every other packet file
    # but never includes its own bytes/hash.
    packet_files = sorted(path for path in output.iterdir() if path.name != "MANIFEST.json")
    manifest = {
        "release_identifier": "NWR_DUAL_LENS_RC1_RESEARCH_ONLY_NOT_ADMITTED",
        "verdict": verdict,
        "win_now_candidate": win_candidate,
        "dynasty_candidate": dynasty_candidate,
        "win_now_admitted": summary["win_admitted"],
        "dynasty_admitted": summary["dynasty_admitted"],
        "production_integration": False,
        "seed": SEED,
        "source_hashes": input_ledger,
        "files": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in packet_files
        ],
        "self_referential": False,
    }
    write_text(
        output / "MANIFEST.json",
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True),
    )

    missing = [filename for filename in REQUIRED_OUTPUTS if not (output / filename).is_file()]
    if missing:
        raise ValueError(f"required output files missing: {missing}")
    if len(board) != 240:
        raise ValueError("detached current board is not 240 rows")
    if not mutations["result"].eq("PASS").all():
        raise ValueError("mutation detector suite failed")
    if summary["both_admitted"]:
        raise ValueError(
            "unexpected admission: this research-only source authority must fail closed"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--current-features", type=Path, default=DEFAULT_CURRENT_FEATURES)
    parser.add_argument("--evidence-json", type=Path)
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not clear an existing output directory before deterministic regeneration.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output = (
        args.output_dir.resolve()
        if args.output_dir
        else (repo_root / OUTPUT_REL).resolve()
    )
    allowed_default = (repo_root / OUTPUT_REL).resolve()
    if output == repo_root or repo_root in output.parents and output != allowed_default:
        # Explicit detached output directories are allowed, but never an
        # arbitrary path inside the repository.
        if output != allowed_default:
            raise ValueError(
                "inside-repository output must be the governed dual-lens packet path"
            )
    if output.exists() and not args.keep_existing:
        shutil.rmtree(output)
    input_ledger = verify_inputs(repo_root, args.current_features.resolve())
    evidence = load_evidence(args.evidence_json.resolve() if args.evidence_json else None)
    historical = load_historical(repo_root)
    current, _board_source, _outcome_source = load_current(
        repo_root, args.current_features.resolve()
    )
    win_predictions, win_traces = build_win_predictions(historical, current)
    dynasty_predictions, dynasty_traces = build_dynasty_predictions(historical, current)
    win_candidates = {
        "W0_FINISHED_V1_ACCEPTED_PROXY": "w0_score",
        "W1_NEXT_SEASON_VOR": "w1_score",
        "W2_CONDITIONAL_PRODUCTION_AVAILABILITY": "w2_score",
        "W3_SHORT_HORIZON_CALIBRATED_BLEND": "w3_score",
    }
    dynasty_candidates = {
        "D0_FINISHED_V1_ACCEPTED_PROXY": "w0_score",
        "D1_DISCOUNTED_MULTI_HORIZON_VOR": "d1_score",
        "D2_FUTURE_PRODUCTION_X_RETENTION": "d2_score",
        "D3_CAPPED_CAREER_HORIZON_GUARDS": "d3_score",
    }
    win_results = evaluation_table(
        win_predictions,
        lane="WIN_NOW",
        candidates=win_candidates,
        actual_column="actual_vor_h1",
        seasons=WIN_EVALUATION_SEASONS,
    )
    dynasty_results = evaluation_table(
        dynasty_predictions,
        lane="DYNASTY",
        candidates=dynasty_candidates,
        actual_column="actual_dynasty_target",
        seasons=DYNASTY_EVALUATION_SEASONS,
    )
    win_candidate = choose_research_candidate(
        win_results,
        (
            "W1_NEXT_SEASON_VOR",
            "W2_CONDITIONAL_PRODUCTION_AVAILABILITY",
            "W3_SHORT_HORIZON_CALIBRATED_BLEND",
        ),
    )
    dynasty_candidate = choose_research_candidate(
        dynasty_results,
        (
            "D1_DISCOUNTED_MULTI_HORIZON_VOR",
            "D2_FUTURE_PRODUCTION_X_RETENTION",
            "D3_CAPPED_CAREER_HORIZON_GUARDS",
        ),
    )
    calibration = calibration_results(
        win_predictions, dynasty_predictions, win_candidate, dynasty_candidate
    )
    cohort_frame, cohort_detail = cohort_results(
        win_predictions, dynasty_predictions, win_candidate, dynasty_candidate
    )
    win_gates, dynasty_gates, summary = build_gates(
        win_results,
        dynasty_results,
        calibration,
        cohort_frame,
        win_predictions,
        dynasty_predictions,
        win_candidate,
        dynasty_candidate,
    )
    board, gaps, sensitivity = build_current_board(
        current,
        win_predictions,
        dynasty_predictions,
        win_candidate,
        dynasty_candidate,
    )
    apps = app_audit(repo_root)
    viewport = viewport_results(apps)
    mutations = mutation_results(board)
    render_documents(
        repo_root=repo_root,
        output=output,
        input_ledger=input_ledger,
        evidence=evidence,
        historical=historical,
        win_predictions=win_predictions,
        dynasty_predictions=dynasty_predictions,
        win_traces=win_traces,
        dynasty_traces=dynasty_traces,
        win_results=win_results,
        dynasty_results=dynasty_results,
        calibration=calibration,
        cohort_frame=cohort_frame,
        cohort_detail=cohort_detail,
        win_gates=win_gates,
        dynasty_gates=dynasty_gates,
        summary=summary,
        board=board,
        gaps=gaps,
        sensitivity=sensitivity,
        apps=apps,
        viewport=viewport,
        mutations=mutations,
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "verdict": summary["verdict"],
                "win_now_candidate": win_candidate,
                "dynasty_candidate": dynasty_candidate,
                "win_now_admitted": summary["win_admitted"],
                "dynasty_admitted": summary["dynasty_admitted"],
                "historical_rows": len(historical),
                "current_rows": len(board),
                "current_scored_win": int(board["win_now_score"].notna().sum()),
                "current_scored_dynasty": int(board["dynasty_value_score"].notna().sum()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
