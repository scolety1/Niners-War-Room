#!/usr/bin/env python3
"""Deterministic rolling-origin Formula Temporal Validation V1.

This runner implements PRE_REGISTRATION_LOCK.md exactly.  It intentionally
keeps target-season labels outside scored feature records until a canonical
prediction hash has been recorded for each origin/position/candidate.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np


PACKET_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKET_DIR.parents[3]

MART = REPO_ROOT / "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/FORMULA_DATA_MART_REVIEW_ONLY.csv"
AGE = REPO_ROOT / "docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
GAUNTLET_RUNNER = REPO_ROOT / "docs/hq/model/full_review_only_formula_gauntlet_candidate_arena_v1_20260709/run_full_review_only_formula_gauntlet_candidate_arena_v1.py"
MART_BUILDER = REPO_ROOT / "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/build_formula_data_mart_feature_availability_audit_v1.py"
SEVERE_RUNNER = REPO_ROOT / "docs/hq/model/formula_miss_taxonomy_red_team_review_v1_20260709/build_formula_miss_taxonomy_red_team_review_v1.py"
CURRENT_FEATURES = Path(r"C:\NWR_REVIEW\current_board_candidate_scoring_feature_completion_gate_v1_20260702\current_board_candidate_feature_input_completed_review_only.csv")
RAW_PLAYER_STATS = Path(r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630\player_stats_weekly.csv")
DYNASTY_PROCESS = Path(r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\data_packs\lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233\draft_pool_downloads\dynastyprocess_db_playerids.csv")
CURRENT_BOARD = REPO_ROOT / "docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/rebuilt_full_player_board_value_review_rows.csv"
SCORING_CONFIG = REPO_ROOT / "config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json"

LOCK = PACKET_DIR / "PRE_REGISTRATION_LOCK.md"
LOCK_HASH = "1b8cfac3807613c453588a60b24b6303e8bcaac35d03639c1927ec8d81735e28"
FREEZE_TIMESTAMP = "2026-07-10T22:34:06Z"
SCORING_SEASONS = tuple(range(2015, 2026))
POSITIONS = ("QB", "RB", "WR", "TE")

PYF = "PYF"
LEGACY = "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE"
RIDGE = "POSITION_SPECIFIC_RIDGE_ALPHA_1_V1"
CURRENT_BOARD_COMPARATOR = "CURRENT_APP_VISIBLE_REVIEW_BOARD_COMPARATOR_2026_PRE_DRAFT"
CANDIDATES = (PYF, LEGACY, RIDGE)

COMMON_FEATURES = (
    "pyf_prior_nwr_points",
    "pyf_prior_nwr_ppg",
    "prior_opportunities",
    "prior_games",
    "age",
)
POSITION_FEATURES = {
    "QB": ("prior_passing_attempts", "prior_passing_yards", "prior_passing_td", "prior_passing_first_downs"),
    "RB": ("prior_touches", "prior_carries", "prior_rushing_yards", "prior_rushing_first_downs"),
    "WR": ("prior_targets", "prior_receptions", "prior_receiving_yards", "prior_receiving_first_downs"),
    "TE": ("prior_targets", "prior_receptions", "prior_receiving_yards", "prior_receiving_first_downs"),
}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
TOP_K = {"QB": (12,), "RB": (12, 24), "WR": (12, 24, 36), "TE": (12,)}

EXPECTED_HASHES = {
    MART: "4c63a01cc4d56d0496d56ff13d4dabb4faa0b7a24d8f7510a368ad48d9714151",
    AGE: "ea5ec2455c89031b8deb6077847b7c10e4da4a09f604bf1dae0e6250983f883b",
    GAUNTLET_RUNNER: "791f22187d98cd58e11be34a474f63688001887affd583fb1fd5d2c392231038",
    MART_BUILDER: "bbaec148c2edd1c57ace89d371357180228e65ba5e1d15ca8e04bb9c9f054e34",
    SEVERE_RUNNER: "eb8066a38bb05cded46719bc532b7c1467215cdd29e0bcb3ad869fecbf2ff75e",
    CURRENT_FEATURES: "bdff4e6c0c51b64a3f867c6ed11f72cda088046e1ffd194c32fb55f49357d1e0",
    RAW_PLAYER_STATS: "a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba",
    DYNASTY_PROCESS: "8b3f5d19e29163363dce579b61574277ea138c7b6f292b899f9ecfe672cd6cc1",
    CURRENT_BOARD: "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4",
    SCORING_CONFIG: "03986944a57f0f73c78a8f56413b53749b3e384a10788ff7ab262d21e0b1eab2",
}


@dataclass(frozen=True)
class RidgeFit:
    feature_names: tuple[str, ...]
    means: tuple[float, ...]
    stds: tuple[float, ...]
    missing_counts: tuple[int, ...]
    coefficients: tuple[float, ...]
    coefficient_hash: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_csv_exclusive(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_text_exclusive(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def assert_fresh_freeze_targets() -> None:
    targets = (
        PACKET_DIR / "PROSPECTIVE_2026_BASELINE_FREEZE.csv",
        PACKET_DIR / "PROSPECTIVE_2026_CHALLENGER_FREEZE.csv",
        PACKET_DIR / "PROSPECTIVE_2026_FREEZE_MANIFEST.json",
    )
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise RuntimeError(f"Immutable V1 freeze target already exists; refusing rewrite: {existing}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fnum(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() in {"NA", "N/A", "NULL", "NONE"}:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def truthy(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def fmt(value: float | None, digits: int = 9) -> str:
    return "" if value is None else f"{value:.{digits}f}"


def mean(values: Iterable[float | None]) -> float | None:
    valid = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return sum(valid) / len(valid) if valid else None


def strict_mean(values: Iterable[float | None]) -> float | None:
    materialized = list(values)
    if not materialized or any(value is None or not math.isfinite(float(value)) for value in materialized):
        return None
    return sum(float(value) for value in materialized) / len(materialized)


def rank_values(values: list[float]) -> list[float]:
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(ordered):
        end = cursor + 1
        while end < len(ordered) and ordered[end][0] == ordered[cursor][0]:
            end += 1
        average = (cursor + 1 + end) / 2.0
        for _, original in ordered[cursor:end]:
            ranks[original] = average
        cursor = end
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if dx <= 0 or dy <= 0:
        return None
    return numerator / math.sqrt(dx * dy)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    return pearson(rank_values(xs), rank_values(ys))


def kendall_tau_a(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    concordant = 0
    discordant = 0
    for i in range(len(xs) - 1):
        for j in range(i + 1, len(xs)):
            product = (xs[i] - xs[j]) * (ys[i] - ys[j])
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    denominator = len(xs) * (len(xs) - 1) / 2
    return (concordant - discordant) / denominator if denominator else None


def ordinal_rank(records: list[dict[str, Any]], score_field: str = "raw_score") -> list[dict[str, Any]]:
    ranked = [dict(record) for record in records]
    ranked.sort(
        key=lambda row: (
            float(row[score_field]),
            str(row.get("player_id", "")),
            str(row.get("substrate_row_id", "")),
        ),
        reverse=True,
    )
    for index, row in enumerate(ranked, 1):
        row["prediction_rank"] = index
    return ranked


def metrics(records: list[dict[str, Any]]) -> dict[str, float | int | None]:
    if len(records) < 20:
        return {"n": len(records), "spearman": None, "kendall": None}
    predicted = [float(row["prediction_rank"]) for row in records]
    actual = [float(row["actual_position_finish"]) for row in records]
    return {
        "n": len(records),
        "spearman": spearman(predicted, actual),
        "kendall": kendall_tau_a(predicted, actual),
    }


def feature_names(position: str) -> tuple[str, ...]:
    return COMMON_FEATURES + POSITION_FEATURES[position]


def assert_preregistration() -> None:
    actual = sha256(LOCK)
    if actual != LOCK_HASH:
        raise RuntimeError(f"Preregistration hash mismatch: expected {LOCK_HASH}, got {actual}")


def verify_sources() -> dict[str, str]:
    verified: dict[str, str] = {}
    for path, expected in EXPECTED_HASHES.items():
        if not path.is_file():
            raise RuntimeError(f"Required source missing: {path}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"Source hash mismatch for {path}: expected {expected}, got {actual}")
        verified[str(path)] = actual
    return verified


def load_historical() -> tuple[
    list[dict[str, Any]],
    dict[tuple[int, str, str], dict[str, float]],
    dict[tuple[int, str, str], dict[str, str]],
    bool,
]:
    """Return feature-only records, isolated labels, and age-sidecar rows."""
    mart_rows = read_csv(MART)
    age_rows = read_csv(AGE)
    if len(mart_rows) != 5518 or len(age_rows) != 5518:
        raise RuntimeError(f"Unexpected historical row counts: mart={len(mart_rows)} age={len(age_rows)}")

    age_index: dict[tuple[int, str, str], dict[str, str]] = {}
    for row in age_rows:
        key = (int(row["season"]), row["position"], row["player_id"])
        if key in age_index:
            raise RuntimeError(f"Duplicate age-sidecar key: {key}")
        age_index[key] = row

    features: list[dict[str, Any]] = []
    labels: dict[tuple[int, str, str], dict[str, float]] = {}
    seen: set[tuple[int, str, str]] = set()
    for source in mart_rows:
        season = int(source["season"])
        position = source["position"]
        player_id = source["player_id"]
        key = (season, position, player_id)
        if key in seen:
            raise RuntimeError(f"Duplicate Formula Mart identity key: {key}")
        seen.add(key)
        if position not in POSITIONS:
            continue
        if int(source["feature_season"]) != season - 1:
            raise RuntimeError(f"N-to-N+1 construction failure: {key}")
        if source.get("leakage_check_result") != "PASS_FEATURE_N_TARGET_N_PLUS_1_SEPARATED":
            raise RuntimeError(f"Leakage gate failure: {key}")
        if source.get("asof_check_result") != "PASS_NO_TARGET_SEASON_CONTEXT_IN_FEATURE_COLUMNS":
            raise RuntimeError(f"As-of gate failure: {key}")
        actual_points = fnum(source.get("label_next_nwr_points"))
        actual_finish = fnum(source.get("label_next_position_finish"))
        if actual_points is None or actual_finish is None:
            raise RuntimeError(f"Missing historical outcome label: {key}")
        labels[key] = {
            "actual_nwr_points": actual_points,
            "actual_position_finish": actual_finish,
        }
        age_row = age_index.get(key)
        if age_row is None:
            raise RuntimeError(f"Missing age-sidecar identity: {key}")
        age_safe = (
            age_row.get("source_gate_status") == "review_only_stable_identity_dob_candidate_not_production_model_use"
            and age_row.get("decision_date_safe") == "PASS_STABLE_IDENTITY_METADATA_ASOF_DERIVED_FOR_TARGET_SEASON_START"
            and age_row.get("leakage_flag") == "PASS_STABLE_DOB_AND_DRAFT_YEAR_DERIVED_ASOF_SEPT_01_NO_OUTCOME_FIELDS"
            and age_row.get("identity_flag") == "PASS_GSIS_ID_JOIN"
            and age_row.get("missingness_flag") == "source_columns_present"
            and age_row.get("review_only_status") == "review_only_age_lifecycle_context_not_formula_weight_not_ranking_input"
        )
        record: dict[str, Any] = {
            "target_season": season,
            "feature_season": int(source["feature_season"]),
            "position": position,
            "player_id": player_id,
            "substrate_row_id": source["substrate_row_id"],
            "player_name": source.get("target_player_name") or source.get("player_name") or "",
            "legacy_base": fnum(source.get("prior_3yr_weighted_nwr_points")),
            "age_bucket": age_row.get("age_bucket", "") if age_safe else "missing_source_gate",
            "lifecycle_bucket": age_row.get("lifecycle_bucket", "") if age_safe else "missing_source_gate",
            "age_source_gate_status": "PASS" if age_safe else "INVALID_AGE_VALUE_NULL_FENCED",
            "source_gate_status": "PASS_REVIEW_ONLY_N_TO_N_PLUS_1_WITH_UNSAFE_AGE_VALUES_NULL_FENCED",
        }
        for name in set(COMMON_FEATURES).union(*POSITION_FEATURES.values()):
            record[name] = fnum(age_row.get("age")) if name == "age" and age_safe else (None if name == "age" else fnum(source.get(name)))
        features.append(record)

    if len(features) != 5518:
        raise RuntimeError(f"Unexpected admitted historical universe: {len(features)}")
    historical_age_gate_enforced = all(
        (row["age_source_gate_status"] == "PASS" and row.get("age") is not None)
        or (
            row["age_source_gate_status"] == "INVALID_AGE_VALUE_NULL_FENCED"
            and row.get("age") is None
            and str(row.get("age_bucket", "")).startswith("missing_")
            and str(row.get("lifecycle_bucket", "")).startswith("missing_")
        )
        for row in features
    )
    if not historical_age_gate_enforced:
        raise RuntimeError("Historical age source gate was not enforced deterministically")
    return features, labels, age_index, historical_age_gate_enforced


def fit_ridge(
    training: list[dict[str, Any]],
    labels: dict[tuple[int, str, str], dict[str, float]],
    position: str,
    scope: str,
) -> RidgeFit:
    names = feature_names(position)
    if len(training) < 100:
        raise RuntimeError(f"Ridge minimum training rows failed: {scope} {position} n={len(training)}")
    seasons = {int(row["target_season"]) for row in training}
    if len(seasons) < 2:
        raise RuntimeError(f"Ridge minimum training seasons failed: {scope} {position}")

    raw = np.array(
        [[np.nan if row.get(name) is None else float(row[name]) for name in names] for row in training],
        dtype=float,
    )
    missing = ~np.isfinite(raw)
    finite_counts = np.sum(~missing, axis=0)
    if np.any(finite_counts == 0):
        absent = [names[index] for index, count in enumerate(finite_counts) if count == 0]
        raise RuntimeError(f"Ridge feature has no finite training values: {scope} {position} {absent}")
    means = np.nanmean(raw, axis=0)
    imputed = np.where(missing, means, raw)
    stds = np.std(imputed, axis=0, ddof=0)
    stds = np.where(stds == 0.0, 1.0, stds)
    standardized = (imputed - means) / stds
    x = np.concatenate([standardized, missing.astype(float)], axis=1)
    design = np.concatenate([np.ones((len(training), 1)), x], axis=1)
    y = np.array(
        [
            labels[(int(row["target_season"]), str(row["position"]), str(row["player_id"]))]["actual_nwr_points"]
            for row in training
        ],
        dtype=float,
    )
    penalty = np.diag([0.0] + [1.0] * (design.shape[1] - 1)) * len(training)
    try:
        beta = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    except np.linalg.LinAlgError as error:
        raise RuntimeError(f"Exact NumPy ridge solve failed: {scope} {position}: {error}") from error
    if not np.all(np.isfinite(beta)):
        raise RuntimeError(f"Non-finite ridge coefficients: {scope} {position}")

    payload = {
        "candidate": RIDGE,
        "scope": scope,
        "position": position,
        "objective": "(1/n)||y-Xb||^2+1.0||b_nonintercept||^2",
        "feature_names": list(names),
        "means": [float(value) for value in means],
        "stds": [float(value) for value in stds],
        "missing_counts": [int(value) for value in np.sum(missing, axis=0)],
        "coefficient_names": ["intercept"] + [f"z_{name}" for name in names] + [f"missing_{name}" for name in names],
        "coefficients": [float(value) for value in beta],
    }
    return RidgeFit(
        feature_names=names,
        means=tuple(float(value) for value in means),
        stds=tuple(float(value) for value in stds),
        missing_counts=tuple(int(value) for value in np.sum(missing, axis=0)),
        coefficients=tuple(float(value) for value in beta),
        coefficient_hash=canonical_hash(payload),
    )


def score_ridge(row: dict[str, Any], fit: RidgeFit) -> tuple[float, dict[str, float], dict[str, int]]:
    raw_values = np.array(
        [np.nan if row.get(name) is None else float(row[name]) for name in fit.feature_names], dtype=float
    )
    missing = ~np.isfinite(raw_values)
    imputed = np.where(missing, np.array(fit.means), raw_values)
    standardized = (imputed - np.array(fit.means)) / np.array(fit.stds)
    x = np.concatenate([standardized, missing.astype(float)])
    design = np.concatenate([[1.0], x])
    score = float(design @ np.array(fit.coefficients))
    if not math.isfinite(score):
        raise RuntimeError(f"Non-finite ridge prediction for {row.get('player_id')}")
    imputed_values = {name: float(value) for name, value in zip(fit.feature_names, imputed)}
    missing_values = {name: int(value) for name, value in zip(fit.feature_names, missing)}
    return score, imputed_values, missing_values


def coefficient_ledger_rows(fit: RidgeFit, scope: str, target_season: str, position: str, training_rows: int) -> list[dict[str, Any]]:
    names = list(fit.feature_names)
    coefficient_names = ["intercept"] + [f"z_{name}" for name in names] + [f"missing_{name}" for name in names]
    rows: list[dict[str, Any]] = []
    for index, (name, coefficient) in enumerate(zip(coefficient_names, fit.coefficients)):
        source_name = "" if name == "intercept" else name.removeprefix("z_").removeprefix("missing_")
        source_index = names.index(source_name) if source_name else None
        rows.append(
            {
                "candidate_name": RIDGE,
                "fit_scope": scope,
                "target_season": target_season,
                "position": position,
                "training_rows": training_rows,
                "alpha": "1.000000",
                "coefficient_order": index,
                "coefficient_name": name,
                "source_feature": source_name,
                "training_mean": "" if source_index is None else fmt(fit.means[source_index], 12),
                "training_population_std": "" if source_index is None else fmt(fit.stds[source_index], 12),
                "training_missing_count": "" if source_index is None else fit.missing_counts[source_index],
                "coefficient": fmt(coefficient, 12),
                "coefficient_hash": fit.coefficient_hash,
                "preprocessing": "train_mean_impute_then_population_zscore;missing_indicators_unscaled;intercept_unpenalized",
            }
        )
    return rows


def prediction_payload(records: list[dict[str, Any]], candidate: str, season: int, position: str) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for row in sorted(records, key=lambda item: (str(item["player_id"]), str(item["substrate_row_id"]))):
        payload.append(
            {
                "candidate_name": candidate,
                "target_season": season,
                "position": position,
                "player_id": row["player_id"],
                "substrate_row_id": row["substrate_row_id"],
                "score_valid": bool(row["score_valid"]),
                "score_exclusion_reason": row.get("score_exclusion_reason", ""),
                "raw_score": None if not row["score_valid"] else float(row["raw_score"]),
                "prediction_rank_full_coverage": row.get("prediction_rank"),
            }
        )
    return payload


def build_historical_predictions(
    features: list[dict[str, Any]],
    labels: dict[tuple[int, str, str], dict[str, float]],
) -> tuple[
    dict[tuple[str, int, str], list[dict[str, Any]]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    by_group: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in features:
        by_group[(int(row["target_season"]), str(row["position"]))].append(row)

    predictions: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    origin_registry: list[dict[str, Any]] = []
    coefficient_rows: list[dict[str, Any]] = []

    for season in SCORING_SEASONS:
        for position in POSITIONS:
            scored_features = by_group[(season, position)]
            if len(scored_features) < 20:
                raise RuntimeError(f"Scored origin below minimum group rows: {season} {position}")
            training = [
                row
                for row in features
                if str(row["position"]) == position and int(row["target_season"]) < season
            ]
            training_seasons = sorted({int(row["target_season"]) for row in training})

            fit = fit_ridge(training, labels, position, f"ROLLING_ORIGIN_{season}")
            coefficient_rows.extend(coefficient_ledger_rows(fit, "ROLLING_ORIGIN", str(season), position, len(training)))

            for candidate in CANDIDATES:
                raw_records: list[dict[str, Any]] = []
                for row in scored_features:
                    raw_score: float | None = None
                    exclusion = ""
                    coefficient_hash = "NOT_APPLICABLE"
                    feature_missing_count: int | str = "NOT_APPLICABLE"
                    if candidate == PYF:
                        raw_score = row.get("pyf_prior_nwr_points")
                        if raw_score is None:
                            exclusion = "MISSING_PYF_PRIOR_NWR_POINTS"
                    elif candidate == LEGACY:
                        base = row.get("legacy_base")
                        if base is None:
                            exclusion = "MISSING_PRIOR_3YR_WEIGHTED_NWR_POINTS"
                        elif row.get("age_source_gate_status") != "PASS" or row.get("age") is None or str(row.get("age_bucket", "")).startswith("missing_") or str(row.get("lifecycle_bucket", "")).startswith("missing_"):
                            exclusion = "MISSING_EXACT_AGE_LIFECYCLE_JOIN"
                        else:
                            guarded = row["age_bucket"] == "age_32_plus" or row["lifecycle_bucket"] == "late_career_10_plus"
                            raw_score = float(base) * (0.98 if guarded else 1.0)
                    else:
                        raw_score, _, missing_values = score_ridge(row, fit)
                        coefficient_hash = fit.coefficient_hash
                        feature_missing_count = sum(missing_values.values())
                    valid = raw_score is not None and math.isfinite(float(raw_score))
                    if not valid and not exclusion:
                        exclusion = "NONFINITE_SCORE"
                    raw_records.append(
                        {
                            "target_season": season,
                            "feature_season": season - 1,
                            "position": position,
                            "player_id": row["player_id"],
                            "substrate_row_id": row["substrate_row_id"],
                            "player_name": row["player_name"],
                            "candidate_name": candidate,
                            "candidate_role": {
                                PYF: "CONTROLLING_BASELINE",
                                LEGACY: "LOCKED_LEGACY_RESEARCH_REFERENCE",
                                RIDGE: "SOLE_NEW_CHALLENGER_CANDIDATE",
                            }[candidate],
                            "score_valid": valid,
                            "score_exclusion_reason": exclusion,
                            "raw_score": None if not valid else float(raw_score),
                            "coefficient_hash": coefficient_hash,
                            "feature_missing_count": feature_missing_count,
                            "source_gate_status": row["source_gate_status"],
                            "review_only": True,
                        }
                    )
                valid_records = ordinal_rank([row for row in raw_records if row["score_valid"]])
                rank_by_key = {
                    (row["player_id"], row["substrate_row_id"]): row["prediction_rank"] for row in valid_records
                }
                for record in raw_records:
                    record["prediction_rank"] = rank_by_key.get((record["player_id"], record["substrate_row_id"]))
                pred_hash = canonical_hash(prediction_payload(raw_records, candidate, season, position))
                for record in raw_records:
                    record["pre_outcome_prediction_hash"] = pred_hash
                    record["outcome_joined_after_prediction_hash"] = True
                predictions[(candidate, season, position)] = raw_records

                origin_registry.append(
                    {
                        "candidate_name": candidate,
                        "candidate_role": {
                            PYF: "CONTROLLING_BASELINE",
                            LEGACY: "LOCKED_LEGACY_RESEARCH_REFERENCE",
                            RIDGE: "SOLE_NEW_CHALLENGER_CANDIDATE",
                        }[candidate],
                        "position": position,
                        "training_target_seasons": "|".join(str(value) for value in training_seasons) if candidate == RIDGE else "NOT_APPLICABLE_FIXED_FORMULA",
                        "scored_target_season": season,
                        "training_row_count": len(training) if candidate == RIDGE else 0,
                        "scored_universe_row_count": len(scored_features),
                        "scored_valid_row_count": sum(1 for row in raw_records if row["score_valid"]),
                        "feature_cutoff": f"{season - 1}-season-complete",
                        "source_cutoff": f"feature_season_{season - 1}_only",
                        "preprocessing_fit_status": "PASS_TRAINING_ROWS_ONLY" if candidate == RIDGE else "NOT_APPLICABLE_FIXED_FORMULA",
                        "coefficient_hash": fit.coefficient_hash if candidate == RIDGE else "NOT_APPLICABLE",
                        "prediction_hash": pred_hash,
                        "outcome_join_status": "JOINED_ONLY_AFTER_PREDICTION_HASH",
                        "identity_gate_status": "PASS_EXACT_GSIS_SEASON_POSITION_UNIQUE",
                        "source_gate_status": "PASS_REVIEW_ONLY_TEMPORAL_VALIDATION_WITH_ROW_LEVEL_SOURCE_NULL_FENCES",
                        "gate_status": "PASS_ORIGIN_EXECUTED_AS_PREREGISTERED",
                    }
                )

    # Only after every origin/candidate prediction hash exists do target outcomes enter records.
    for records in predictions.values():
        for record in records:
            key = (int(record["target_season"]), str(record["position"]), str(record["player_id"]))
            label = labels[key]
            record["actual_nwr_points"] = label["actual_nwr_points"]
            record["actual_position_finish"] = label["actual_position_finish"]
            record["actual_startable"] = label["actual_position_finish"] <= STARTABLE_CUTOFF[str(record["position"])]

    return predictions, origin_registry, coefficient_rows


def exclusion_summary(records: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for row in records:
        if not row["score_valid"]:
            counts[row.get("score_exclusion_reason") or "UNSPECIFIED"] += 1
    return "|".join(f"{reason}:{counts[reason]}" for reason in sorted(counts)) or "none"


def severe_counts(records: list[dict[str, Any]], position: str) -> dict[str, int | str | None]:
    if len(records) < 20:
        return {
            "false_positives": None,
            "severe_false_positives": None,
            "false_negatives": None,
            "severe_false_negatives": None,
            "net_severe_misses": None,
            "metric_status": "UNSUPPORTED",
            "unsupported_reason": "POPULATION_BELOW_MINIMUM_20_ROWS",
        }
    cutoff = STARTABLE_CUTOFF[position]
    fp = severe_fp = fn = severe_fn = 0
    for row in records:
        predicted = float(row["prediction_rank"])
        actual = float(row["actual_position_finish"])
        if predicted <= cutoff and actual > cutoff:
            fp += 1
        if predicted <= cutoff / 2 and actual > 1.5 * cutoff:
            severe_fp += 1
        if predicted > cutoff and actual <= cutoff:
            fn += 1
        if predicted > 1.5 * cutoff and actual <= cutoff / 2:
            severe_fn += 1
    return {
        "false_positives": fp,
        "severe_false_positives": severe_fp,
        "false_negatives": fn,
        "severe_false_negatives": severe_fn,
        "net_severe_misses": severe_fp + severe_fn,
        "metric_status": "SUPPORTED",
        "unsupported_reason": "",
    }


def top_k_counts(records: list[dict[str, Any]], k: int) -> dict[str, int | float | None]:
    minimum = max(20, k)
    if len(records) < minimum:
        return {
            "hits": None,
            "predicted_top_k": None,
            "actual_top_k": None,
            "precision": None,
            "recall": None,
            "metric_status": "UNSUPPORTED",
            "unsupported_reason": f"POPULATION_BELOW_REQUIRED_{minimum}_ROWS",
        }
    hits = sum(
        1
        for row in records
        if float(row["prediction_rank"]) <= k and float(row["actual_position_finish"]) <= k
    )
    predicted = sum(1 for row in records if float(row["prediction_rank"]) <= k)
    actual = sum(1 for row in records if float(row["actual_position_finish"]) <= k)
    return {
        "hits": hits,
        "predicted_top_k": predicted,
        "actual_top_k": actual,
        "precision": hits / predicted if predicted else None,
        "recall": hits / actual if actual else None,
        "metric_status": "SUPPORTED",
        "unsupported_reason": "",
    }


def evaluate_historical(
    predictions: dict[tuple[str, int, str], list[dict[str, Any]]]
) -> dict[str, Any]:
    season_position_rows: list[dict[str, Any]] = []
    shared_scoreboard: list[dict[str, Any]] = []
    full_scoreboard: list[dict[str, Any]] = []
    top_severe_rows: list[dict[str, Any]] = []
    shared_detail: dict[tuple[str, int, str], dict[str, Any]] = {}
    full_detail: dict[tuple[str, int, str], dict[str, Any]] = {}

    # Candidate-complete populations remain wholly separate from paired comparisons.
    for candidate in CANDIDATES:
        all_ranked: list[dict[str, Any]] = []
        group_metrics: list[dict[str, Any]] = []
        total_universe = total_valid = 0
        for season in SCORING_SEASONS:
            for position in POSITIONS:
                records = predictions[(candidate, season, position)]
                valid = ordinal_rank([row for row in records if row["score_valid"]])
                result = metrics(valid)
                all_ranked.extend(valid)
                total_universe += len(records)
                total_valid += len(valid)
                detail = {"records": valid, **result}
                full_detail[(candidate, season, position)] = detail
                group_metrics.append(detail)
                missing_count = sum(int(row["feature_missing_count"]) for row in records) if candidate == RIDGE else 0
                season_position_rows.append(
                    {
                        "evaluation_scope": "FULL_COVERAGE",
                        "comparison_candidate": "",
                        "evaluation_subject": candidate,
                        "target_season": season,
                        "position": position,
                        "row_count": result["n"],
                        "minimum_row_gate": "PASS" if result["n"] >= 20 else "FAIL",
                        "spearman": fmt(result["spearman"]),
                        "kendall_tau_a": fmt(result["kendall"]),
                    }
                )
                full_scoreboard.append(
                    {
                        "summary_level": "SEASON_POSITION",
                        "candidate_name": candidate,
                        "target_season": season,
                        "position": position,
                        "eligible_universe_rows": len(records),
                        "valid_score_rows": len(valid),
                        "invalid_score_rows": len(records) - len(valid),
                        "coverage": fmt(len(valid) / len(records) if records else None),
                        "raw_feature_missing_cells": missing_count if candidate == RIDGE else "NOT_APPLICABLE",
                        "exclusion_reasons": exclusion_summary(records),
                        "spearman": fmt(result["spearman"]),
                        "kendall_tau_a": fmt(result["kendall"]),
                        "pooled_within_position_rank_spearman_secondary": "",
                    }
                )
                severe = severe_counts(valid, position)
                top_severe_rows.append(
                    {
                        "evaluation_scope": "FULL_COVERAGE",
                        "comparison_candidate": "",
                        "evaluation_subject": candidate,
                        "target_season": season,
                        "position": position,
                        "record_type": "SEVERE_MISS",
                        "top_k": "",
                        "population_rows": len(valid),
                        "hits": "",
                        "predicted_top_k": "",
                        "actual_top_k": "",
                        "precision": "",
                        "recall": "",
                        **severe,
                        "canonical_definition": "C_QB10_RB30_WR40_TE12;SFP=rank<=C/2&finish>1.5C;SFN=rank>1.5C&finish<=C/2",
                    }
                )
                for k in TOP_K[position]:
                    top = top_k_counts(valid, k)
                    top_severe_rows.append(
                        {
                            "evaluation_scope": "FULL_COVERAGE",
                            "comparison_candidate": "",
                            "evaluation_subject": candidate,
                            "target_season": season,
                            "position": position,
                            "record_type": "TOP_K",
                            "top_k": k,
                            "population_rows": len(valid),
                            "hits": top["hits"],
                            "predicted_top_k": top["predicted_top_k"],
                            "actual_top_k": top["actual_top_k"],
                            "precision": fmt(top["precision"]),
                            "recall": fmt(top["recall"]),
                            "false_positives": "",
                            "severe_false_positives": "",
                            "false_negatives": "",
                            "severe_false_negatives": "",
                            "net_severe_misses": "",
                            "metric_status": top["metric_status"],
                            "unsupported_reason": top["unsupported_reason"],
                            "canonical_definition": f"{position}_TOP_{k}",
                        }
                    )
        macro_sp = strict_mean(item["spearman"] for item in group_metrics)
        macro_ke = strict_mean(item["kendall"] for item in group_metrics)
        pooled_sp = spearman(
            [float(row["prediction_rank"]) for row in all_ranked],
            [float(row["actual_position_finish"]) for row in all_ranked],
        )
        full_scoreboard.append(
            {
                "summary_level": "ALL_GROUPS",
                "candidate_name": candidate,
                "target_season": "ALL_2015_2025",
                "position": "ALL_EQUAL_WEIGHT_GROUPS",
                "eligible_universe_rows": total_universe,
                "valid_score_rows": total_valid,
                "invalid_score_rows": total_universe - total_valid,
                "coverage": fmt(total_valid / total_universe if total_universe else None),
                "raw_feature_missing_cells": "SEE_MODEL_FEATURE_AND_COEFFICIENT_LEDGER" if candidate == RIDGE else "NOT_APPLICABLE",
                "exclusion_reasons": "see season-position rows",
                "spearman": fmt(macro_sp),
                "kendall_tau_a": fmt(macro_ke),
                "pooled_within_position_rank_spearman_secondary": fmt(pooled_sp),
            }
        )

    # Exact shared populations against PYF, with both ranks recomputed on each intersection.
    for candidate in (LEGACY, RIDGE):
        all_candidate_ranked: list[dict[str, Any]] = []
        all_pyf_ranked: list[dict[str, Any]] = []
        for season in SCORING_SEASONS:
            for position in POSITIONS:
                candidate_records = predictions[(candidate, season, position)]
                pyf_records = predictions[(PYF, season, position)]
                candidate_valid = {str(row["player_id"]): row for row in candidate_records if row["score_valid"]}
                pyf_valid = {str(row["player_id"]): row for row in pyf_records if row["score_valid"]}
                if len(candidate_valid) != sum(1 for row in candidate_records if row["score_valid"]):
                    raise RuntimeError(f"Duplicate candidate shared identity key: {candidate} {season} {position}")
                if len(pyf_valid) != sum(1 for row in pyf_records if row["score_valid"]):
                    raise RuntimeError(f"Duplicate PYF shared identity key: {season} {position}")
                shared_keys = sorted(set(candidate_valid).intersection(pyf_valid))
                for player_id in shared_keys:
                    if candidate_valid[player_id]["substrate_row_id"] != pyf_valid[player_id]["substrate_row_id"]:
                        raise RuntimeError(f"Substrate provenance mismatch for shared identity: {season} {position} {player_id}")
                candidate_shared = ordinal_rank([candidate_valid[key] for key in shared_keys])
                pyf_shared = ordinal_rank([pyf_valid[key] for key in shared_keys])
                candidate_metric = metrics(candidate_shared)
                pyf_metric = metrics(pyf_shared)
                all_candidate_ranked.extend(candidate_shared)
                all_pyf_ranked.extend(pyf_shared)
                shared_detail[(candidate, season, position)] = {
                    "candidate_records": candidate_shared,
                    "pyf_records": pyf_shared,
                    "candidate_spearman": candidate_metric["spearman"],
                    "pyf_spearman": pyf_metric["spearman"],
                    "candidate_kendall": candidate_metric["kendall"],
                    "pyf_kendall": pyf_metric["kendall"],
                    "spearman_delta": None
                    if candidate_metric["spearman"] is None or pyf_metric["spearman"] is None
                    else float(candidate_metric["spearman"]) - float(pyf_metric["spearman"]),
                    "kendall_delta": None
                    if candidate_metric["kendall"] is None or pyf_metric["kendall"] is None
                    else float(candidate_metric["kendall"]) - float(pyf_metric["kendall"]),
                }
                lost_by_pyf = sorted(set(candidate_valid) - set(pyf_valid))
                lost_by_candidate = sorted(set(pyf_valid) - set(candidate_valid))
                shared_scoreboard.append(
                    {
                        "summary_level": "SEASON_POSITION",
                        "candidate_name": candidate,
                        "baseline_name": PYF,
                        "target_season": season,
                        "position": position,
                        "eligible_universe_rows": len(candidate_records),
                        "pyf_valid_rows": len(pyf_valid),
                        "candidate_valid_rows": len(candidate_valid),
                        "shared_rows": len(shared_keys),
                        "rows_lost_by_pyf": len(lost_by_pyf),
                        "rows_lost_by_candidate": len(lost_by_candidate),
                        "shared_coverage_of_eligible_universe": fmt(len(shared_keys) / len(candidate_records) if candidate_records else None),
                        "shared_fraction_of_pyf_valid": fmt(len(shared_keys) / len(pyf_valid) if pyf_valid else None),
                        "shared_fraction_of_candidate_valid": fmt(len(shared_keys) / len(candidate_valid) if candidate_valid else None),
                        "pyf_exclusion_reasons": exclusion_summary(pyf_records),
                        "candidate_exclusion_reasons": exclusion_summary(candidate_records),
                        "pyf_spearman": fmt(pyf_metric["spearman"]),
                        "candidate_spearman": fmt(candidate_metric["spearman"]),
                        "candidate_minus_pyf_spearman": fmt(shared_detail[(candidate, season, position)]["spearman_delta"]),
                        "pyf_kendall_tau_a": fmt(pyf_metric["kendall"]),
                        "candidate_kendall_tau_a": fmt(candidate_metric["kendall"]),
                        "candidate_minus_pyf_kendall": fmt(shared_detail[(candidate, season, position)]["kendall_delta"]),
                        "pooled_within_position_rank_spearman_secondary_pyf": "",
                        "pooled_within_position_rank_spearman_secondary_candidate": "",
                    }
                )
                for subject, records, result in (
                    (candidate, candidate_shared, candidate_metric),
                    (PYF, pyf_shared, pyf_metric),
                ):
                    season_position_rows.append(
                        {
                            "evaluation_scope": "SHARED_WITH_PYF",
                            "comparison_candidate": candidate,
                            "evaluation_subject": subject,
                            "target_season": season,
                            "position": position,
                            "row_count": result["n"],
                            "minimum_row_gate": "PASS" if result["n"] >= 20 else "FAIL",
                            "spearman": fmt(result["spearman"]),
                            "kendall_tau_a": fmt(result["kendall"]),
                        }
                    )
                    severe = severe_counts(records, position)
                    top_severe_rows.append(
                        {
                            "evaluation_scope": "SHARED_WITH_PYF",
                            "comparison_candidate": candidate,
                            "evaluation_subject": subject,
                            "target_season": season,
                            "position": position,
                            "record_type": "SEVERE_MISS",
                            "top_k": "",
                            "population_rows": len(records),
                            "hits": "",
                            "predicted_top_k": "",
                            "actual_top_k": "",
                            "precision": "",
                            "recall": "",
                            **severe,
                            "canonical_definition": "C_QB10_RB30_WR40_TE12;SFP=rank<=C/2&finish>1.5C;SFN=rank>1.5C&finish<=C/2",
                        }
                    )
                    for k in TOP_K[position]:
                        top = top_k_counts(records, k)
                        top_severe_rows.append(
                            {
                                "evaluation_scope": "SHARED_WITH_PYF",
                                "comparison_candidate": candidate,
                                "evaluation_subject": subject,
                                "target_season": season,
                                "position": position,
                                "record_type": "TOP_K",
                                "top_k": k,
                                "population_rows": len(records),
                                "hits": top["hits"],
                                "predicted_top_k": top["predicted_top_k"],
                                "actual_top_k": top["actual_top_k"],
                                "precision": fmt(top["precision"]),
                                "recall": fmt(top["recall"]),
                                "false_positives": "",
                                "severe_false_positives": "",
                                "false_negatives": "",
                                "severe_false_negatives": "",
                                "net_severe_misses": "",
                                "metric_status": top["metric_status"],
                                "unsupported_reason": top["unsupported_reason"],
                                "canonical_definition": f"{position}_TOP_{k}",
                            }
                        )

        candidate_macro = strict_mean(shared_detail[(candidate, season, position)]["candidate_spearman"] for season in SCORING_SEASONS for position in POSITIONS)
        pyf_macro = strict_mean(shared_detail[(candidate, season, position)]["pyf_spearman"] for season in SCORING_SEASONS for position in POSITIONS)
        candidate_k_macro = strict_mean(shared_detail[(candidate, season, position)]["candidate_kendall"] for season in SCORING_SEASONS for position in POSITIONS)
        pyf_k_macro = strict_mean(shared_detail[(candidate, season, position)]["pyf_kendall"] for season in SCORING_SEASONS for position in POSITIONS)
        candidate_micro = spearman(
            [float(row["prediction_rank"]) for row in all_candidate_ranked],
            [float(row["actual_position_finish"]) for row in all_candidate_ranked],
        )
        pyf_micro = spearman(
            [float(row["prediction_rank"]) for row in all_pyf_ranked],
            [float(row["actual_position_finish"]) for row in all_pyf_ranked],
        )
        shared_scoreboard.append(
            {
                "summary_level": "ALL_GROUPS",
                "candidate_name": candidate,
                "baseline_name": PYF,
                "target_season": "ALL_2015_2025",
                "position": "ALL_EQUAL_WEIGHT_GROUPS",
                "eligible_universe_rows": sum(len(predictions[(candidate, season, position)]) for season in SCORING_SEASONS for position in POSITIONS),
                "pyf_valid_rows": sum(1 for season in SCORING_SEASONS for position in POSITIONS for row in predictions[(PYF, season, position)] if row["score_valid"]),
                "candidate_valid_rows": sum(1 for season in SCORING_SEASONS for position in POSITIONS for row in predictions[(candidate, season, position)] if row["score_valid"]),
                "shared_rows": len(all_candidate_ranked),
                "rows_lost_by_pyf": sum(max(0, len(full_detail[(candidate, season, position)]["records"]) - len(shared_detail[(candidate, season, position)]["candidate_records"])) for season in SCORING_SEASONS for position in POSITIONS),
                "rows_lost_by_candidate": sum(max(0, len(full_detail[(PYF, season, position)]["records"]) - len(shared_detail[(candidate, season, position)]["pyf_records"])) for season in SCORING_SEASONS for position in POSITIONS),
                "shared_coverage_of_eligible_universe": fmt(len(all_candidate_ranked) / sum(len(predictions[(candidate, season, position)]) for season in SCORING_SEASONS for position in POSITIONS)),
                "shared_fraction_of_pyf_valid": fmt(len(all_candidate_ranked) / sum(1 for season in SCORING_SEASONS for position in POSITIONS for row in predictions[(PYF, season, position)] if row["score_valid"])),
                "shared_fraction_of_candidate_valid": fmt(len(all_candidate_ranked) / sum(1 for season in SCORING_SEASONS for position in POSITIONS for row in predictions[(candidate, season, position)] if row["score_valid"])),
                "pyf_exclusion_reasons": "see season-position rows",
                "candidate_exclusion_reasons": "see season-position rows",
                "pyf_spearman": fmt(pyf_macro),
                "candidate_spearman": fmt(candidate_macro),
                "candidate_minus_pyf_spearman": fmt(None if candidate_macro is None or pyf_macro is None else candidate_macro - pyf_macro),
                "pyf_kendall_tau_a": fmt(pyf_k_macro),
                "candidate_kendall_tau_a": fmt(candidate_k_macro),
                "candidate_minus_pyf_kendall": fmt(None if candidate_k_macro is None or pyf_k_macro is None else candidate_k_macro - pyf_k_macro),
                "pooled_within_position_rank_spearman_secondary_pyf": fmt(pyf_micro),
                "pooled_within_position_rank_spearman_secondary_candidate": fmt(candidate_micro),
            }
        )

    return {
        "season_position_rows": season_position_rows,
        "shared_scoreboard": shared_scoreboard,
        "full_scoreboard": full_scoreboard,
        "top_severe_rows": top_severe_rows,
        "shared_detail": shared_detail,
        "full_detail": full_detail,
    }


def balanced_and_gate(
    evaluation: dict[str, Any],
    origin_rows: list[dict[str, Any]],
    source_identity_precheck_pass: bool,
) -> dict[str, Any]:
    detail = evaluation["shared_detail"]
    position_rows: list[dict[str, Any]] = []
    season_rows: list[dict[str, Any]] = []
    delta_rows: list[dict[str, Any]] = []
    candidate_summaries: dict[str, dict[str, Any]] = {}

    for candidate in (LEGACY, RIDGE):
        for season in SCORING_SEASONS:
            for position in POSITIONS:
                item = detail.get((candidate, season, position))
                if item is None:
                    raise RuntimeError(f"Missing required shared metric group: {candidate} {season} {position}")
                if len(item["candidate_records"]) < 20 or len(item["pyf_records"]) < 20:
                    raise RuntimeError(f"Required shared metric group below minimum 20 rows: {candidate} {season} {position}")
                required = ("candidate_spearman", "pyf_spearman", "candidate_kendall", "pyf_kendall")
                if any(item[name] is None or not math.isfinite(float(item[name])) for name in required):
                    raise RuntimeError(f"Undefined required shared correlation: {candidate} {season} {position}")

    expected_origin_keys = {
        (candidate, season, position) for candidate in CANDIDATES for season in SCORING_SEASONS for position in POSITIONS
    }
    actual_origin_keys = {
        (str(row["candidate_name"]), int(row["scored_target_season"]), str(row["position"])) for row in origin_rows
    }
    origin_gate_pass = (
        len(origin_rows) == len(expected_origin_keys)
        and actual_origin_keys == expected_origin_keys
        and all(row["gate_status"] == "PASS_ORIGIN_EXECUTED_AS_PREREGISTERED" for row in origin_rows)
        and all(row["identity_gate_status"] == "PASS_EXACT_GSIS_SEASON_POSITION_UNIQUE" for row in origin_rows)
        and all(row["source_gate_status"] == "PASS_REVIEW_ONLY_TEMPORAL_VALIDATION_WITH_ROW_LEVEL_SOURCE_NULL_FENCES" for row in origin_rows)
        and all(row["outcome_join_status"] == "JOINED_ONLY_AFTER_PREDICTION_HASH" for row in origin_rows)
        and all(len(str(row["prediction_hash"])) == 64 for row in origin_rows)
        and all(
            row["candidate_name"] != RIDGE or len(str(row["coefficient_hash"])) == 64 for row in origin_rows
        )
    )
    source_leakage_identity_runtime_pass = bool(source_identity_precheck_pass and origin_gate_pass)

    for candidate in (LEGACY, RIDGE):
        position_deltas: dict[str, float] = {}
        season_deltas: dict[int, float] = {}
        for position in POSITIONS:
            candidate_sp = mean(detail[(candidate, season, position)]["candidate_spearman"] for season in SCORING_SEASONS)
            pyf_sp = mean(detail[(candidate, season, position)]["pyf_spearman"] for season in SCORING_SEASONS)
            candidate_ke = mean(detail[(candidate, season, position)]["candidate_kendall"] for season in SCORING_SEASONS)
            pyf_ke = mean(detail[(candidate, season, position)]["pyf_kendall"] for season in SCORING_SEASONS)
            delta = float(candidate_sp) - float(pyf_sp)
            position_deltas[position] = delta
            position_rows.append(
                {
                    "summary_level": "POSITION",
                    "candidate_name": candidate,
                    "baseline_name": PYF,
                    "position": position,
                    "independent_target_seasons": len(SCORING_SEASONS),
                    "candidate_mean_spearman": fmt(candidate_sp),
                    "pyf_mean_spearman": fmt(pyf_sp),
                    "candidate_minus_pyf_spearman": fmt(delta),
                    "candidate_mean_kendall_tau_a": fmt(candidate_ke),
                    "pyf_mean_kendall_tau_a": fmt(pyf_ke),
                    "candidate_minus_pyf_kendall": fmt(float(candidate_ke) - float(pyf_ke)),
                }
            )
            delta_rows.append(
                {
                    "candidate_name": candidate,
                    "delta_level": "POSITION",
                    "target_season": "ALL_2015_2025",
                    "position": position,
                    "omitted_season": "",
                    "candidate_spearman": fmt(candidate_sp),
                    "pyf_spearman": fmt(pyf_sp),
                    "candidate_minus_pyf_spearman": fmt(delta),
                }
            )
        position_balanced_candidate = mean(
            mean(detail[(candidate, season, position)]["candidate_spearman"] for season in SCORING_SEASONS)
            for position in POSITIONS
        )
        position_balanced_pyf = mean(
            mean(detail[(candidate, season, position)]["pyf_spearman"] for season in SCORING_SEASONS)
            for position in POSITIONS
        )
        position_balanced_delta = float(position_balanced_candidate) - float(position_balanced_pyf)
        position_rows.append(
            {
                "summary_level": "POSITION_BALANCED_HEADLINE",
                "candidate_name": candidate,
                "baseline_name": PYF,
                "position": "ALL_EQUAL_WEIGHT_POSITIONS",
                "independent_target_seasons": len(SCORING_SEASONS),
                "candidate_mean_spearman": fmt(position_balanced_candidate),
                "pyf_mean_spearman": fmt(position_balanced_pyf),
                "candidate_minus_pyf_spearman": fmt(position_balanced_delta),
                "candidate_mean_kendall_tau_a": fmt(mean(mean(detail[(candidate, season, position)]["candidate_kendall"] for season in SCORING_SEASONS) for position in POSITIONS)),
                "pyf_mean_kendall_tau_a": fmt(mean(mean(detail[(candidate, season, position)]["pyf_kendall"] for season in SCORING_SEASONS) for position in POSITIONS)),
                "candidate_minus_pyf_kendall": fmt(mean(mean(detail[(candidate, season, position)]["kendall_delta"] for season in SCORING_SEASONS) for position in POSITIONS)),
            }
        )

        for season in SCORING_SEASONS:
            candidate_sp = mean(detail[(candidate, season, position)]["candidate_spearman"] for position in POSITIONS)
            pyf_sp = mean(detail[(candidate, season, position)]["pyf_spearman"] for position in POSITIONS)
            candidate_ke = mean(detail[(candidate, season, position)]["candidate_kendall"] for position in POSITIONS)
            pyf_ke = mean(detail[(candidate, season, position)]["pyf_kendall"] for position in POSITIONS)
            delta = float(candidate_sp) - float(pyf_sp)
            season_deltas[season] = delta
            season_rows.append(
                {
                    "summary_level": "SEASON",
                    "candidate_name": candidate,
                    "baseline_name": PYF,
                    "target_season": season,
                    "positions_included": 4,
                    "candidate_mean_spearman": fmt(candidate_sp),
                    "pyf_mean_spearman": fmt(pyf_sp),
                    "candidate_minus_pyf_spearman": fmt(delta),
                    "candidate_mean_kendall_tau_a": fmt(candidate_ke),
                    "pyf_mean_kendall_tau_a": fmt(pyf_ke),
                    "candidate_minus_pyf_kendall": fmt(float(candidate_ke) - float(pyf_ke)),
                }
            )
            delta_rows.append(
                {
                    "candidate_name": candidate,
                    "delta_level": "SEASON",
                    "target_season": season,
                    "position": "ALL_EQUAL_WEIGHT_POSITIONS",
                    "omitted_season": "",
                    "candidate_spearman": fmt(candidate_sp),
                    "pyf_spearman": fmt(pyf_sp),
                    "candidate_minus_pyf_spearman": fmt(delta),
                }
            )
            for position in POSITIONS:
                item = detail[(candidate, season, position)]
                delta_rows.append(
                    {
                        "candidate_name": candidate,
                        "delta_level": "SEASON_POSITION",
                        "target_season": season,
                        "position": position,
                        "omitted_season": "",
                        "candidate_spearman": fmt(item["candidate_spearman"]),
                        "pyf_spearman": fmt(item["pyf_spearman"]),
                        "candidate_minus_pyf_spearman": fmt(item["spearman_delta"]),
                    }
                )

        season_balanced_candidate = mean(
            mean(detail[(candidate, season, position)]["candidate_spearman"] for position in POSITIONS)
            for season in SCORING_SEASONS
        )
        season_balanced_pyf = mean(
            mean(detail[(candidate, season, position)]["pyf_spearman"] for position in POSITIONS)
            for season in SCORING_SEASONS
        )
        season_balanced_delta = float(season_balanced_candidate) - float(season_balanced_pyf)
        season_rows.append(
            {
                "summary_level": "SEASON_BALANCED_HEADLINE",
                "candidate_name": candidate,
                "baseline_name": PYF,
                "target_season": "ALL_EQUAL_WEIGHT_SEASONS",
                "positions_included": 4,
                "candidate_mean_spearman": fmt(season_balanced_candidate),
                "pyf_mean_spearman": fmt(season_balanced_pyf),
                "candidate_minus_pyf_spearman": fmt(season_balanced_delta),
                "candidate_mean_kendall_tau_a": fmt(mean(mean(detail[(candidate, season, position)]["candidate_kendall"] for position in POSITIONS) for season in SCORING_SEASONS)),
                "pyf_mean_kendall_tau_a": fmt(mean(mean(detail[(candidate, season, position)]["pyf_kendall"] for position in POSITIONS) for season in SCORING_SEASONS)),
                "candidate_minus_pyf_kendall": fmt(mean(mean(detail[(candidate, season, position)]["kendall_delta"] for position in POSITIONS) for season in SCORING_SEASONS)),
            }
        )

        loso_position: dict[int, float] = {}
        loso_season: dict[int, float] = {}
        for omitted in SCORING_SEASONS:
            remaining = [season for season in SCORING_SEASONS if season != omitted]
            pos_value = mean(
                mean(detail[(candidate, season, position)]["spearman_delta"] for season in remaining)
                for position in POSITIONS
            )
            season_value = mean(
                mean(detail[(candidate, season, position)]["spearman_delta"] for position in POSITIONS)
                for season in remaining
            )
            loso_position[omitted] = float(pos_value)
            loso_season[omitted] = float(season_value)
            for level, value in (("LOSO_POSITION_BALANCED", pos_value), ("LOSO_SEASON_BALANCED", season_value)):
                delta_rows.append(
                    {
                        "candidate_name": candidate,
                        "delta_level": level,
                        "target_season": "ALL_EXCEPT_OMITTED",
                        "position": "ALL_EQUAL_WEIGHT",
                        "omitted_season": omitted,
                        "candidate_spearman": "",
                        "pyf_spearman": "",
                        "candidate_minus_pyf_spearman": fmt(value),
                    }
                )

        rng = np.random.default_rng(20260710)
        season_position_matrix = np.array(
            [[float(detail[(candidate, season, position)]["spearman_delta"]) for position in POSITIONS] for season in SCORING_SEASONS],
            dtype=float,
        )
        position_draws = np.empty(10000, dtype=float)
        season_draws = np.empty(10000, dtype=float)
        for index in range(10000):
            sampled_indices = rng.integers(0, len(SCORING_SEASONS), size=len(SCORING_SEASONS))
            sampled = season_position_matrix[sampled_indices, :]
            position_draws[index] = float(np.mean(np.mean(sampled, axis=0)))
            season_draws[index] = float(np.mean(np.mean(sampled, axis=1)))
        position_ci_lower, position_ci_upper = (float(value) for value in np.percentile(position_draws, [2.5, 97.5]))
        season_ci_lower, season_ci_upper = (float(value) for value in np.percentile(season_draws, [2.5, 97.5]))

        severe_by_position: dict[str, dict[str, int]] = {}
        severe_overall = {
            "candidate_sfp": 0,
            "pyf_sfp": 0,
            "candidate_sfn": 0,
            "pyf_sfn": 0,
        }
        for position in POSITIONS:
            c_counts = {"severe_false_positives": 0, "severe_false_negatives": 0}
            p_counts = {"severe_false_positives": 0, "severe_false_negatives": 0}
            for season in SCORING_SEASONS:
                c = severe_counts(detail[(candidate, season, position)]["candidate_records"], position)
                p = severe_counts(detail[(candidate, season, position)]["pyf_records"], position)
                for key in c_counts:
                    c_counts[key] += c[key]
                    p_counts[key] += p[key]
            severe_by_position[position] = {
                "candidate_sfp": c_counts["severe_false_positives"],
                "pyf_sfp": p_counts["severe_false_positives"],
                "candidate_sfn": c_counts["severe_false_negatives"],
                "pyf_sfn": p_counts["severe_false_negatives"],
            }
            severe_overall["candidate_sfp"] += c_counts["severe_false_positives"]
            severe_overall["pyf_sfp"] += p_counts["severe_false_positives"]
            severe_overall["candidate_sfn"] += c_counts["severe_false_negatives"]
            severe_overall["pyf_sfn"] += p_counts["severe_false_negatives"]

        coverage_lost: dict[tuple[int, str], int] = {}
        total_candidate_valid = total_pyf_valid = 0
        for season in SCORING_SEASONS:
            for position in POSITIONS:
                candidate_records = evaluation["full_detail"][(candidate, season, position)]["records"]
                pyf_records = evaluation["full_detail"][(PYF, season, position)]["records"]
                candidate_keys = {str(row["player_id"]) for row in candidate_records}
                pyf_keys = {str(row["player_id"]) for row in pyf_records}
                candidate_provenance = {str(row["player_id"]): str(row["substrate_row_id"]) for row in candidate_records}
                pyf_provenance = {str(row["player_id"]): str(row["substrate_row_id"]) for row in pyf_records}
                if len(candidate_keys) != len(candidate_records) or len(pyf_keys) != len(pyf_records):
                    raise RuntimeError(f"Duplicate full-coverage identity key: {candidate} {season} {position}")
                for player_id in candidate_keys.intersection(pyf_keys):
                    if candidate_provenance[player_id] != pyf_provenance[player_id]:
                        raise RuntimeError(f"Coverage substrate mismatch: {candidate} {season} {position} {player_id}")
                coverage_lost[(season, position)] = len(pyf_keys - candidate_keys)
                total_candidate_valid += len(candidate_keys)
                total_pyf_valid += len(pyf_keys)
        # Use full-scoreboard group rows for the true eligible-universe denominator.
        universe_rows = sum(
            int(row["eligible_universe_rows"])
            for row in evaluation["full_scoreboard"]
            if row["summary_level"] == "SEASON_POSITION" and row["candidate_name"] == candidate
        )
        candidate_coverage = total_candidate_valid / universe_rows
        pyf_universe = sum(
            int(row["eligible_universe_rows"])
            for row in evaluation["full_scoreboard"]
            if row["summary_level"] == "SEASON_POSITION" and row["candidate_name"] == PYF
        )
        pyf_coverage = total_pyf_valid / pyf_universe

        candidate_summaries[candidate] = {
            "position_balanced_candidate": position_balanced_candidate,
            "position_balanced_pyf": position_balanced_pyf,
            "position_balanced_delta": position_balanced_delta,
            "season_balanced_candidate": season_balanced_candidate,
            "season_balanced_pyf": season_balanced_pyf,
            "season_balanced_delta": season_balanced_delta,
            "position_deltas": position_deltas,
            "season_deltas": season_deltas,
            "loso_position": loso_position,
            "loso_season": loso_season,
            "position_ci_lower": position_ci_lower,
            "position_ci_upper": position_ci_upper,
            "season_ci_lower": season_ci_lower,
            "season_ci_upper": season_ci_upper,
            "severe_by_position": severe_by_position,
            "severe_overall": severe_overall,
            "coverage_lost": coverage_lost,
            "candidate_coverage": candidate_coverage,
            "pyf_coverage": pyf_coverage,
            "candidate_valid_rows": total_candidate_valid,
            "pyf_valid_rows": total_pyf_valid,
            "eligible_universe_rows": universe_rows,
        }

    ridge = candidate_summaries[RIDGE]
    gate_results = {
        "headline_improvement": ridge["position_balanced_delta"] > 0 and ridge["season_balanced_delta"] > 0,
        "not_isolated": sum(1 for value in ridge["season_deltas"].values() if value > 0) >= 2
        and all(value > 0 for value in ridge["loso_position"].values())
        and all(value > 0 for value in ridge["loso_season"].values()),
        "no_repeated_position_regression": all(
            sum(1 for season in SCORING_SEASONS if detail[(RIDGE, season, position)]["spearman_delta"] < -0.005) < 2
            and ridge["position_deltas"][position] >= -0.005
            for position in POSITIONS
        ),
        "no_severe_fp_increase": ridge["severe_overall"]["candidate_sfp"] <= ridge["severe_overall"]["pyf_sfp"]
        and all(
            ridge["severe_by_position"][position]["candidate_sfp"]
            <= ridge["severe_by_position"][position]["pyf_sfp"]
            for position in POSITIONS
        ),
        "no_favorable_coverage_reduction": all(value == 0 for value in ridge["coverage_lost"].values())
        and ridge["candidate_coverage"] >= ridge["pyf_coverage"],
        "uncertainty_review": len(SCORING_SEASONS) >= 5
        and ridge["position_ci_lower"] > 0
        and ridge["season_ci_lower"] > 0
        and min(ridge["loso_position"].values()) > 0
        and min(ridge["loso_season"].values()) > 0,
        "source_leakage_identity_runtime": source_leakage_identity_runtime_pass,
    }
    gate_pass = all(gate_results.values())
    verdict = "GREEN_PROSPECTIVE_2026_REVIEW_ONLY_CHALLENGER_FROZEN" if gate_pass else "RED_REGULARIZED_CHALLENGER_FAILED_TEMPORAL_VALIDATION"
    return {
        "position_rows": position_rows,
        "season_rows": season_rows,
        "delta_rows": delta_rows,
        "candidate_summaries": candidate_summaries,
        "gate_results": gate_results,
        "gate_pass": gate_pass,
        "verdict": verdict,
    }


def deduplicate_2026_universe() -> list[dict[str, str]]:
    rows = [row for row in read_csv(CURRENT_FEATURES) if row.get("position") in POSITIONS]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["stable_player_id"]].append(row)
    collapsed: list[dict[str, str]] = []
    for stable_id, group in sorted(grouped.items()):
        first = group[0]
        if any(row != first for row in group[1:]):
            raise RuntimeError(f"Non-exact 2026 completed-feature duplicate: {stable_id}")
        collapsed.append(first)
    if len(collapsed) != 342:
        raise RuntimeError(f"Unexpected 2026 controlled source universe: {len(collapsed)}")
    if sum(truthy(row.get("candidate_feature_ready")) for row in collapsed) != 231:
        raise RuntimeError("Unexpected 2026 ready-row count after exact duplicate collapse")
    admitted: dict[tuple[str, str], str] = {}
    for row in collapsed:
        gsis = row.get("player_id_gsis", "").strip()
        if not gsis:
            continue
        key = (gsis, row["position"])
        if key in admitted:
            raise RuntimeError(
                f"Duplicate admitted 2026 GSIS-position identity across stable IDs: {key} {admitted[key]} {row['stable_player_id']}"
            )
        admitted[key] = row["stable_player_id"]
    return collapsed


def build_dp_index() -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(DYNASTY_PROCESS):
        gsis = row.get("gsis_id", "").strip()
        if gsis and gsis.upper() != "NA":
            index[gsis].append(row)
    return index


def choose_dp_row(index: dict[str, list[dict[str, str]]], gsis: str, position: str) -> dict[str, str]:
    options = index.get(gsis, [])
    if not options:
        raise RuntimeError(f"Missing exact DynastyProcess GSIS join: {gsis}")
    # The birthdate is textual; explicitly detect conflicting usable ISO dates.
    births = {row.get("birthdate", "").strip() for row in options if row.get("birthdate", "").strip() not in {"", "NA"}}
    if len(births) > 1:
        raise RuntimeError(f"Conflicting DynastyProcess birthdates: {gsis} {sorted(births)}")
    ranked = sorted(
        options,
        key=lambda row: (
            row.get("position") == position,
            row.get("birthdate", "").strip() not in {"", "NA"},
            fnum(row.get("draft_year")) is not None,
            json.dumps(row, sort_keys=True),
        ),
        reverse=True,
    )
    return ranked[0]


def age_lifecycle_2026(dp: dict[str, str]) -> tuple[float, str, str, str, int]:
    birth_text = dp.get("birthdate", "").strip()
    if not birth_text or birth_text == "NA":
        raise RuntimeError(f"Missing 2026 birthdate for {dp.get('gsis_id')}")
    born = date.fromisoformat(birth_text)
    anchor = date(2026, 9, 1)
    age = round((anchor - born).days / 365.2425, 3)
    if age < 23:
        age_bucket = "under_23"
    elif age < 26:
        age_bucket = "age_23_to_25"
    elif age < 29:
        age_bucket = "age_26_to_28"
    elif age < 32:
        age_bucket = "age_29_to_31"
    else:
        age_bucket = "age_32_plus"
    draft_value = fnum(dp.get("draft_year"))
    if draft_value is None:
        raise RuntimeError(f"Missing 2026 draft year for {dp.get('gsis_id')}")
    draft_year = int(draft_value)
    years = 2026 - draft_year
    if years <= 0:
        lifecycle = "rookie_year"
    elif years <= 3:
        lifecycle = "early_career_1_to_3"
    elif years <= 6:
        lifecycle = "prime_window_4_to_6"
    elif years <= 9:
        lifecycle = "veteran_7_to_9"
    else:
        lifecycle = "late_career_10_plus"
    return age, age_bucket, lifecycle, birth_text, draft_year


def verify_2026_identity_precheck() -> bool:
    universe = deduplicate_2026_universe()
    dp_index = build_dp_index()
    checked = 0
    for row in universe:
        if not truthy(row.get("candidate_feature_ready")):
            continue
        gsis = row.get("player_id_gsis", "").strip()
        if not gsis:
            raise RuntimeError(f"Ready 2026 row missing admitted GSIS identity: {row['stable_player_id']}")
        selected = choose_dp_row(dp_index, gsis, row["position"])
        age_lifecycle_2026(selected)
        checked += 1
    if checked != 231:
        raise RuntimeError(f"Unexpected exact 2026 identity/age precheck count: {checked}")
    return True


def current_feature_map(source: dict[str, str], age: float | None) -> dict[str, Any]:
    mapping: dict[str, Any] = {
        "pyf_prior_nwr_points": fnum(source.get("prior_nwr_points")),
        "pyf_prior_nwr_ppg": fnum(source.get("prior_nwr_ppg")),
        "age": age,
    }
    for name in set(COMMON_FEATURES).union(*POSITION_FEATURES.values()):
        if name not in mapping:
            mapping[name] = fnum(source.get(name))
    return mapping


def normalized_present_history(
    source: dict[str, str], historical_index: dict[tuple[int, str, str], dict[str, Any]]
) -> tuple[float | None, int, dict[str, float | None]]:
    gsis = source.get("player_id_gsis", "")
    position = source["position"]
    values: dict[str, float | None] = {
        "2025": fnum(source.get("prior_nwr_points")),
        "2024": None,
        "2023": None,
    }
    row_2025 = historical_index.get((2025, position, gsis))
    row_2024 = historical_index.get((2024, position, gsis))
    if row_2025:
        values["2024"] = row_2025.get("pyf_prior_nwr_points")
    if row_2024:
        values["2023"] = row_2024.get("pyf_prior_nwr_points")
    if values["2025"] is None:
        return None, 0, values
    weights = {"2025": 0.60, "2024": 0.25, "2023": 0.15}
    present = [(float(values[year]), weights[year]) for year in ("2025", "2024", "2023") if values[year] is not None]
    score = sum(value * weight for value, weight in present) / sum(weight for _, weight in present)
    return score, len(present), values


FREEZE_FIELDS = [
    "freeze_timestamp",
    "target_season",
    "feature_season",
    "candidate_name",
    "candidate_role",
    "player_id",
    "identity_namespace",
    "canonical_player_key",
    "player_name",
    "position",
    "source_population",
    "eligible",
    "score_valid",
    "exclusion_reason",
    "raw_score",
    "within_position_rank",
    "overall_research_rank",
    "model_or_formula_version",
    "coefficient_hash",
    "input_source_dates",
    "input_source_hashes",
    "formula_mart_hash",
    "sidecar_hashes",
    "age",
    "birth_date",
    "draft_year",
    "lifecycle_bucket",
    "history_years_available",
    "raw_feature_values_json",
    "imputed_feature_values_json",
    "missingness_json",
    "source_status",
    "review_only",
    "production_comparator_caveat",
    "prediction_record_hash",
]


def assign_freeze_ranks(records: list[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        if row["score_valid"]:
            groups[(row["candidate_name"], row["position"])].append(row)
    for (candidate, _), group in groups.items():
        if candidate == CURRENT_BOARD_COMPARATOR:
            group.sort(key=lambda row: (float(row["overall_research_rank"]), str(row["player_id"])))
        else:
            group.sort(key=lambda row: (float(row["raw_score"]), str(row["player_id"])), reverse=True)
        for index, row in enumerate(group, 1):
            row["within_position_rank"] = index
    for row in records:
        payload = {field: row.get(field, "") for field in FREEZE_FIELDS if field != "prediction_record_hash"}
        row["prediction_record_hash"] = canonical_hash(payload)


def build_2026_freezes(
    historical_features: list[dict[str, Any]],
    labels: dict[tuple[int, str, str], dict[str, float]],
    gate_pass: bool,
    coefficient_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]] | None, list[dict[str, Any]]]:
    universe = deduplicate_2026_universe()
    dp_index = build_dp_index()
    historical_index = {
        (int(row["target_season"]), str(row["position"]), str(row["player_id"])): row for row in historical_features
    }
    baseline_rows: list[dict[str, Any]] = []
    prepared: list[tuple[dict[str, str], dict[str, Any], dict[str, Any]]] = []

    for source in universe:
        ready = truthy(source.get("candidate_feature_ready"))
        gsis = source.get("player_id_gsis", "").strip()
        age = None
        age_bucket = lifecycle = birth_date = ""
        draft_year: int | str = ""
        if ready:
            if not gsis:
                raise RuntimeError(f"Ready 2026 row missing GSIS identity: {source['stable_player_id']}")
            dp = choose_dp_row(dp_index, gsis, source["position"])
            age, age_bucket, lifecycle, birth_date, draft_year = age_lifecycle_2026(dp)
        features = current_feature_map(source, age)
        context = {
            "ready": ready,
            "gsis": gsis,
            "age": age,
            "age_bucket": age_bucket,
            "lifecycle": lifecycle,
            "birth_date": birth_date,
            "draft_year": draft_year,
        }
        prepared.append((source, features, context))

        for candidate in (PYF, LEGACY):
            valid = ready
            reason = ""
            raw_score: float | None = None
            history_years: int | str = ""
            raw_values: dict[str, Any]
            missingness: dict[str, Any]
            if not ready:
                reason = "NOT_CANDIDATE_FEATURE_READY:" + (source.get("missing_required_features") or source.get("scoring_missing_reason") or "SOURCE_NULL_FENCE")
                raw_values = {"prior_nwr_points": fnum(source.get("prior_nwr_points"))}
                missingness = {"source_ready": False, "prior_nwr_points": raw_values["prior_nwr_points"] is None}
            elif candidate == PYF:
                raw_score = features["pyf_prior_nwr_points"]
                valid = raw_score is not None
                reason = "" if valid else "MISSING_PYF_PRIOR_NWR_POINTS"
                raw_values = {"prior_nwr_points": raw_score}
                missingness = {"source_ready": True, "prior_nwr_points": raw_score is None}
                history_years = 1 if valid else 0
            else:
                base, history_years, history = normalized_present_history(source, historical_index)
                valid = base is not None and bool(age_bucket) and bool(lifecycle)
                guarded = age_bucket == "age_32_plus" or lifecycle == "late_career_10_plus"
                raw_score = None if base is None else base * (0.98 if guarded else 1.0)
                reason = "" if valid else "MISSING_LEGACY_BASE_OR_AGE_LIFECYCLE"
                raw_values = {
                    "history_nwr_points": history,
                    "normalized_present_weights": {"2025": 0.60, "2024": 0.25, "2023": 0.15},
                    "late_guard_applied": guarded,
                    "age_bucket": age_bucket,
                    "lifecycle_bucket": lifecycle,
                }
                missingness = {
                    "source_ready": True,
                    "history_2025_missing": history["2025"] is None,
                    "history_2024_missing": history["2024"] is None,
                    "history_2023_missing": history["2023"] is None,
                    "age_missing": age is None,
                    "lifecycle_missing": not bool(lifecycle),
                }
            player_id = gsis if gsis else f"sleeper:{source['stable_player_id']}"
            baseline_rows.append(
                {
                    "freeze_timestamp": FREEZE_TIMESTAMP,
                    "target_season": 2026,
                    "feature_season": 2025,
                    "candidate_name": candidate,
                    "candidate_role": "FROZEN_2026_CONTROLLING_BASELINE" if candidate == PYF else "FROZEN_2026_LOCKED_LEGACY_REFERENCE",
                    "player_id": player_id,
                    "identity_namespace": "GSIS" if gsis else "SLEEPER_ONLY_NULL_FENCED",
                    "canonical_player_key": f"gsis:{gsis}" if gsis else f"sleeper:{source['stable_player_id']}:{source['position']}",
                    "player_name": source.get("player_name", ""),
                    "position": source["position"],
                    "source_population": "CONTROLLED_COMPLETED_FEATURE_UNIVERSE_342",
                    "eligible": ready,
                    "score_valid": valid and raw_score is not None and math.isfinite(float(raw_score)),
                    "exclusion_reason": reason,
                    "raw_score": fmt(raw_score, 12),
                    "within_position_rank": "",
                    "overall_research_rank": "",
                    "model_or_formula_version": "PYF_PRIOR_NWR_POINTS_V1" if candidate == PYF else "GAUNTLET_081_ACCEPTED_FIELD_EXECUTION_V1",
                    "coefficient_hash": "NOT_APPLICABLE",
                    "input_source_dates": "feature_gate=2026-07-02;raw_stats_created=2026-07-01T01:35:45.256663Z;age_asof=2026-09-01",
                    "input_source_hashes": f"completed_features={EXPECTED_HASHES[CURRENT_FEATURES]};raw_player_stats={EXPECTED_HASHES[RAW_PLAYER_STATS]};dynastyprocess={EXPECTED_HASHES[DYNASTY_PROCESS]};scoring_config={EXPECTED_HASHES[SCORING_CONFIG]}",
                    "formula_mart_hash": EXPECTED_HASHES[MART],
                    "sidecar_hashes": f"historical_age={EXPECTED_HASHES[AGE]};dynastyprocess={EXPECTED_HASHES[DYNASTY_PROCESS]}",
                    "age": fmt(age, 3),
                    "birth_date": birth_date,
                    "draft_year": draft_year,
                    "lifecycle_bucket": lifecycle,
                    "history_years_available": history_years,
                    "raw_feature_values_json": json.dumps(raw_values, sort_keys=True, separators=(",", ":")),
                    "imputed_feature_values_json": "{}",
                    "missingness_json": json.dumps(missingness, sort_keys=True, separators=(",", ":")),
                    "source_status": "REVIEW_ONLY_RECEIPT_SAFE_NOT_SOURCE_TRUTH_OR_PRODUCTION",
                    "review_only": True,
                    "production_comparator_caveat": "",
                }
            )

    # Preserve the exact current board; do not approximate or rebuild it.
    current_rows = read_csv(CURRENT_BOARD)
    if len(current_rows) != 240:
        raise RuntimeError(f"Unexpected exact current-board row count: {len(current_rows)}")
    for source in current_rows:
        score = fnum(source.get("nwr_dynasty_score"))
        overall_rank = fnum(source.get("nwr_rank"))
        valid = score is not None and overall_rank is not None
        baseline_rows.append(
            {
                "freeze_timestamp": FREEZE_TIMESTAMP,
                "target_season": 2026,
                "feature_season": "MIXED_CURRENT_INFORMATION",
                "candidate_name": CURRENT_BOARD_COMPARATOR,
                "candidate_role": "SEPARATELY_CAVEATED_CURRENT_BOARD_COMPARATOR",
                "player_id": source.get("player_id", ""),
                "identity_namespace": "NATIVE_CURRENT_BOARD_PLAYER_ID",
                "canonical_player_key": source.get("canonical_player_key", ""),
                "player_name": source.get("player_name", ""),
                "position": source.get("position", ""),
                "source_population": "EXACT_CURRENT_APP_VISIBLE_REVIEW_BOARD_240",
                "eligible": valid,
                "score_valid": valid,
                "exclusion_reason": "" if valid else "MISSING_NATIVE_BOARD_SCORE_OR_RANK",
                "raw_score": fmt(score, 12),
                "within_position_rank": "",
                "overall_research_rank": "" if overall_rank is None else int(overall_rank),
                "model_or_formula_version": source.get("candidate_model_version") or source.get("model_version") or "",
                "coefficient_hash": "NOT_AVAILABLE_NATIVE_CURRENT_BOARD_COMPARATOR",
                "input_source_dates": f"native_score_as_of={source.get('score_as_of_date','')};deterministic_rebuild=2026-07-08",
                "input_source_hashes": f"exact_current_board={EXPECTED_HASHES[CURRENT_BOARD]}",
                "formula_mart_hash": "NOT_APPLICABLE_CURRENT_INFORMATION_COMPARATOR",
                "sidecar_hashes": "NATIVE_CURRENT_BOARD_LINEAGE_ONLY",
                "age": source.get("age", ""),
                "birth_date": "",
                "draft_year": "",
                "lifecycle_bucket": "",
                "history_years_available": "",
                "raw_feature_values_json": json.dumps(
                    {
                        "native_nwr_rank": overall_rank,
                        "native_nwr_dynasty_score": score,
                        "score_as_of_date": source.get("score_as_of_date", ""),
                        "allowed_use": source.get("allowed_use", ""),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "imputed_feature_values_json": "{}",
                "missingness_json": "{}",
                "source_status": source.get("allowed_use", "candidate_review_only_not_active_rankings"),
                "review_only": True,
                "production_comparator_caveat": "Exact app-visible/current-board review artifact with current-information and proprietary-component advantage; not equivalent to a receipt-safe historical model and not production-approved.",
            }
        )

    assign_freeze_ranks(baseline_rows)

    challenger_rows: list[dict[str, Any]] | None = None
    final_coefficient_rows: list[dict[str, Any]] = []
    if gate_pass:
        challenger_rows = []
        fits: dict[str, RidgeFit] = {}
        for position in POSITIONS:
            training = [row for row in historical_features if row["position"] == position]
            fits[position] = fit_ridge(training, labels, position, "PROSPECTIVE_2026_FINAL")
            final_coefficient_rows.extend(
                coefficient_ledger_rows(fits[position], "PROSPECTIVE_2026_FINAL", "2026", position, len(training))
            )
        for source, features, context in prepared:
            ready = bool(context["ready"])
            valid = ready
            reason = ""
            score: float | None = None
            imputed: dict[str, float] = {}
            missing: dict[str, int] = {}
            fit = fits[source["position"]]
            if ready:
                score, imputed, missing = score_ridge(features, fit)
            else:
                valid = False
                reason = "NOT_CANDIDATE_FEATURE_READY:" + (source.get("missing_required_features") or source.get("scoring_missing_reason") or "SOURCE_NULL_FENCE")
            gsis = context["gsis"]
            raw_values = {name: features.get(name) for name in feature_names(source["position"])}
            challenger_rows.append(
                {
                    "freeze_timestamp": FREEZE_TIMESTAMP,
                    "target_season": 2026,
                    "feature_season": 2025,
                    "candidate_name": RIDGE,
                    "candidate_role": "PROSPECTIVE_2026_REVIEW_ONLY_CHALLENGER",
                    "player_id": gsis if gsis else f"sleeper:{source['stable_player_id']}",
                    "identity_namespace": "GSIS" if gsis else "SLEEPER_ONLY_NULL_FENCED",
                    "canonical_player_key": f"gsis:{gsis}" if gsis else f"sleeper:{source['stable_player_id']}:{source['position']}",
                    "player_name": source.get("player_name", ""),
                    "position": source["position"],
                    "source_population": "CONTROLLED_COMPLETED_FEATURE_UNIVERSE_342",
                    "eligible": ready,
                    "score_valid": valid and score is not None,
                    "exclusion_reason": reason,
                    "raw_score": fmt(score, 12),
                    "within_position_rank": "",
                    "overall_research_rank": "",
                    "model_or_formula_version": RIDGE,
                    "coefficient_hash": fit.coefficient_hash,
                    "input_source_dates": "feature_gate=2026-07-02;raw_stats_created=2026-07-01T01:35:45.256663Z;age_asof=2026-09-01",
                    "input_source_hashes": f"completed_features={EXPECTED_HASHES[CURRENT_FEATURES]};raw_player_stats={EXPECTED_HASHES[RAW_PLAYER_STATS]};dynastyprocess={EXPECTED_HASHES[DYNASTY_PROCESS]};scoring_config={EXPECTED_HASHES[SCORING_CONFIG]}",
                    "formula_mart_hash": EXPECTED_HASHES[MART],
                    "sidecar_hashes": f"historical_age={EXPECTED_HASHES[AGE]};dynastyprocess={EXPECTED_HASHES[DYNASTY_PROCESS]}",
                    "age": fmt(context["age"], 3),
                    "birth_date": context["birth_date"],
                    "draft_year": context["draft_year"],
                    "lifecycle_bucket": context["lifecycle"],
                    "history_years_available": "",
                    "raw_feature_values_json": json.dumps(raw_values, sort_keys=True, separators=(",", ":")),
                    "imputed_feature_values_json": json.dumps(imputed, sort_keys=True, separators=(",", ":")),
                    "missingness_json": json.dumps(missing, sort_keys=True, separators=(",", ":")),
                    "source_status": "REVIEW_ONLY_RECEIPT_SAFE_NOT_SOURCE_TRUTH_OR_PRODUCTION",
                    "review_only": True,
                    "production_comparator_caveat": "",
                }
            )
        assign_freeze_ranks(challenger_rows)

    coefficient_rows.extend(final_coefficient_rows)
    return baseline_rows, challenger_rows, final_coefficient_rows


def candidate_registry_rows() -> list[dict[str, Any]]:
    return [
        {
            "candidate_name": PYF,
            "role": "CONTROLLING_BASELINE",
            "historical_definition": "Formula Mart pyf_prior_nwr_points",
            "fit_method": "NONE_FIXED_FORMULA",
            "feature_list": "pyf_prior_nwr_points",
            "alpha": "NOT_APPLICABLE",
            "intercept": "NOT_APPLICABLE",
            "eligible_for_new_challenger_label": False,
            "prior_selection_caveat": "Controlling baseline",
            "supported_positions": "QB|RB|WR|TE",
            "status": "LOCKED",
        },
        {
            "candidate_name": LEGACY,
            "role": "LOCKED_LEGACY_RESEARCH_REFERENCE",
            "historical_definition": "prior_3yr_weighted_nwr_points * (0.98 when age_32_plus or late_career_10_plus else 1.00); legacy alias mismatch disclosed",
            "fit_method": "NONE_FIXED_FORMULA",
            "feature_list": "prior_3yr_weighted_nwr_points|age_bucket|lifecycle_bucket",
            "alpha": "NOT_APPLICABLE",
            "intercept": "NOT_APPLICABLE",
            "eligible_for_new_challenger_label": False,
            "prior_selection_caveat": "Selected using full-history evidence through 2025; rolling results are stability diagnostics only",
            "supported_positions": "QB|RB|WR|TE",
            "status": "LOCKED",
        },
        {
            "candidate_name": RIDGE,
            "role": "SOLE_NEW_CHALLENGER_CANDIDATE",
            "historical_definition": "Position-specific ridge; train-only mean imputation and population z-score; one indicator per numeric feature",
            "fit_method": "NumPy solve(X'X+n*diag(0,1,...),X'y); normalized alpha=1.0",
            "feature_list": "common=" + "|".join(COMMON_FEATURES) + ";QB=" + "|".join(POSITION_FEATURES["QB"]) + ";RB=" + "|".join(POSITION_FEATURES["RB"]) + ";WR_TE=" + "|".join(POSITION_FEATURES["WR"]),
            "alpha": "1.000000",
            "intercept": "YES_UNPENALIZED",
            "eligible_for_new_challenger_label": True,
            "prior_selection_caveat": "One preregistered architecture screened retrospectively; cannot prove production superiority",
            "supported_positions": "QB|RB|WR|TE",
            "status": "LOCKED",
        },
    ]


def source_ledger_rows() -> list[dict[str, Any]]:
    definitions = [
        ("SRC-001", "FORMULA_DATA_MART", MART, 5518, "2013-2025 target seasons", "PASS_REVIEW_ONLY_TEMPORAL_FEATURE_AND_LABEL_SUBSTRATE", "training_allowed/model_use_allowed/source_truth_allowed/production_approved remain false"),
        ("SRC-002", "AGE_LIFECYCLE_SIDECAR", AGE, 5518, "target-season September 1 age", "PASS_REVIEW_ONLY_EXACT_GSIS_SEASON_POSITION_JOIN", "review-only formula-family context; no production approval"),
        ("SRC-003", "ACCEPTED_GAUNTLET_RUNNER", GAUNTLET_RUNNER, "NOT_TABULAR", "2026-07-09 repository artifact", "PASS_FIXED_LEGACY_EXECUTION_LINEAGE", "legacy alias mismatch disclosed"),
        ("SRC-004", "FORMULA_MART_BUILDER", MART_BUILDER, "NOT_TABULAR", "2026-07-09 repository artifact", "PASS_NORMALIZED_PRESENT_WEIGHT_LINEAGE", "0.60/0.25/0.15 actual builder semantics"),
        ("SRC-005", "CANONICAL_SEVERE_MISS_RUNNER", SEVERE_RUNNER, "NOT_TABULAR", "2026-07-09 repository artifact", "PASS_CANONICAL_TOP_K_AND_SEVERE_TAXONOMY", "earlier diagnostic severe counts are non-comparable"),
        ("SRC-006", "2026_COMPLETED_FEATURE_INPUT", CURRENT_FEATURES, 370, "feature season 2025; gate 2026-07-02", "PASS_REVIEW_ONLY_342_DISTINCT_231_SCOREABLE_AFTER_EXACT_DUPLICATE_COLLAPSE", "111 controlled QB/RB/WR/TE rows remain null-fenced"),
        ("SRC-007", "RAW_PLAYER_STATS_RECEIPT", RAW_PLAYER_STATS, 76804, "created 2026-07-01T01:35:45.256663Z; 2025 REG facts", "PASS_REVIEW_ONLY_SOURCE_RECEIPT", "not source-truth or production approved"),
        ("SRC-008", "DYNASTYPROCESS_ID_DOB_DRAFT", DYNASTY_PROCESS, 12440, "stable identity metadata; age as of 2026-09-01", "PASS_231_OF_231_EXACT_GSIS_DOB_JOIN_ZERO_CONFLICTS", "review-only stable identity metadata"),
        ("SRC-009", "EXACT_CURRENT_BOARD_COMPARATOR", CURRENT_BOARD, 240, "native score_as_of_date=2026-pre-draft; rebuilt 2026-07-08", "PASS_EXACT_HASH_PRESERVED_SEPARATE_COMPARATOR", "candidate_review_only_not_active_rankings; current-information advantage"),
        ("SRC-010", "NWR_1QB_NONPPR_FIRST_DOWN_SCORING_CONFIG", SCORING_CONFIG, "JSON_CONTRACT", "repository scoring contract", "PASS_EXACT_SCORING_CONTRACT_HASH", "unchanged by this lane"),
    ]
    rows: list[dict[str, Any]] = []
    for source_id, name, path, count, asof, gate, caveat in definitions:
        rows.append(
            {
                "source_id": source_id,
                "source_name": name,
                "path": str(path),
                "sha256": EXPECTED_HASHES[path],
                "physical_rows_or_type": count,
                "source_asof": asof,
                "identity_grain": "(target_season,position,GSIS player_id)" if name in {"FORMULA_DATA_MART", "AGE_LIFECYCLE_SIDECAR"} else "source-specific exact identity",
                "gate_status": gate,
                "allowed_use": "REVIEW_ONLY_TEMPORAL_VALIDATION_AND_2026_TRACKING",
                "blocked_use": "PRODUCTION|RANKINGS_INTEGRATION|APP_RUNTIME|SOURCE_PROMOTION",
                "caveat": caveat,
            }
        )
    return rows


def flatten_oof(predictions: dict[tuple[str, int, str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(predictions):
        for record in sorted(predictions[key], key=lambda row: (str(row["player_id"]), str(row["substrate_row_id"]))):
            rows.append(
                {
                    "target_season": record["target_season"],
                    "feature_season": record["feature_season"],
                    "position": record["position"],
                    "player_id": record["player_id"],
                    "substrate_row_id": record["substrate_row_id"],
                    "player_name": record["player_name"],
                    "candidate_name": record["candidate_name"],
                    "candidate_role": record["candidate_role"],
                    "score_valid": record["score_valid"],
                    "score_exclusion_reason": record["score_exclusion_reason"],
                    "raw_score": fmt(record["raw_score"], 12),
                    "prediction_rank_full_coverage": record["prediction_rank"] or "",
                    "actual_nwr_points": fmt(record["actual_nwr_points"], 9),
                    "actual_position_finish": fmt(record["actual_position_finish"], 0),
                    "actual_startable_canonical": record["actual_startable"],
                    "coefficient_hash": record["coefficient_hash"],
                    "pre_outcome_prediction_hash": record["pre_outcome_prediction_hash"],
                    "outcome_joined_after_prediction_hash": record["outcome_joined_after_prediction_hash"],
                    "source_gate_status": record["source_gate_status"],
                    "review_only": record["review_only"],
                }
            )
    return rows


def write_core_csvs(
    predictions: dict[tuple[str, int, str], list[dict[str, Any]]],
    origin_rows: list[dict[str, Any]],
    coefficient_rows: list[dict[str, Any]],
    evaluation: dict[str, Any],
    balance: dict[str, Any],
    baseline_rows: list[dict[str, Any]],
    challenger_rows: list[dict[str, Any]] | None,
) -> None:
    write_csv(PACKET_DIR / "SOURCE_HASH_LEDGER.csv", source_ledger_rows(), [
        "source_id", "source_name", "path", "sha256", "physical_rows_or_type", "source_asof", "identity_grain", "gate_status", "allowed_use", "blocked_use", "caveat"
    ])
    write_csv(PACKET_DIR / "CANDIDATE_REGISTRY.csv", candidate_registry_rows(), [
        "candidate_name", "role", "historical_definition", "fit_method", "feature_list", "alpha", "intercept", "eligible_for_new_challenger_label", "prior_selection_caveat", "supported_positions", "status"
    ])
    write_csv(PACKET_DIR / "ROLLING_ORIGIN_REGISTRY.csv", origin_rows, [
        "candidate_name", "candidate_role", "position", "training_target_seasons", "scored_target_season", "training_row_count", "scored_universe_row_count", "scored_valid_row_count", "feature_cutoff", "source_cutoff", "preprocessing_fit_status", "coefficient_hash", "prediction_hash", "outcome_join_status", "identity_gate_status", "source_gate_status", "gate_status"
    ])
    write_csv(PACKET_DIR / "MODEL_FEATURE_AND_COEFFICIENT_LEDGER.csv", coefficient_rows, [
        "candidate_name", "fit_scope", "target_season", "position", "training_rows", "alpha", "coefficient_order", "coefficient_name", "source_feature", "training_mean", "training_population_std", "training_missing_count", "coefficient", "coefficient_hash", "preprocessing"
    ])
    write_csv(PACKET_DIR / "OUT_OF_FOLD_PREDICTIONS.csv", flatten_oof(predictions), [
        "target_season", "feature_season", "position", "player_id", "substrate_row_id", "player_name", "candidate_name", "candidate_role", "score_valid", "score_exclusion_reason", "raw_score", "prediction_rank_full_coverage", "actual_nwr_points", "actual_position_finish", "actual_startable_canonical", "coefficient_hash", "pre_outcome_prediction_hash", "outcome_joined_after_prediction_hash", "source_gate_status", "review_only"
    ])
    write_csv(PACKET_DIR / "SEASON_POSITION_METRICS.csv", evaluation["season_position_rows"], [
        "evaluation_scope", "comparison_candidate", "evaluation_subject", "target_season", "position", "row_count", "minimum_row_gate", "spearman", "kendall_tau_a"
    ])
    write_csv(PACKET_DIR / "SHARED_ROW_COMPARISON_SCOREBOARD.csv", evaluation["shared_scoreboard"], [
        "summary_level", "candidate_name", "baseline_name", "target_season", "position", "eligible_universe_rows", "pyf_valid_rows", "candidate_valid_rows", "shared_rows", "rows_lost_by_pyf", "rows_lost_by_candidate", "shared_coverage_of_eligible_universe", "shared_fraction_of_pyf_valid", "shared_fraction_of_candidate_valid", "pyf_exclusion_reasons", "candidate_exclusion_reasons", "pyf_spearman", "candidate_spearman", "candidate_minus_pyf_spearman", "pyf_kendall_tau_a", "candidate_kendall_tau_a", "candidate_minus_pyf_kendall", "pooled_within_position_rank_spearman_secondary_pyf", "pooled_within_position_rank_spearman_secondary_candidate"
    ])
    write_csv(PACKET_DIR / "FULL_COVERAGE_SCOREBOARD.csv", evaluation["full_scoreboard"], [
        "summary_level", "candidate_name", "target_season", "position", "eligible_universe_rows", "valid_score_rows", "invalid_score_rows", "coverage", "raw_feature_missing_cells", "exclusion_reasons", "spearman", "kendall_tau_a", "pooled_within_position_rank_spearman_secondary"
    ])
    write_csv(PACKET_DIR / "POSITION_BALANCED_SCOREBOARD.csv", balance["position_rows"], [
        "summary_level", "candidate_name", "baseline_name", "position", "independent_target_seasons", "candidate_mean_spearman", "pyf_mean_spearman", "candidate_minus_pyf_spearman", "candidate_mean_kendall_tau_a", "pyf_mean_kendall_tau_a", "candidate_minus_pyf_kendall"
    ])
    write_csv(PACKET_DIR / "SEASON_BALANCED_SCOREBOARD.csv", balance["season_rows"], [
        "summary_level", "candidate_name", "baseline_name", "target_season", "positions_included", "candidate_mean_spearman", "pyf_mean_spearman", "candidate_minus_pyf_spearman", "candidate_mean_kendall_tau_a", "pyf_mean_kendall_tau_a", "candidate_minus_pyf_kendall"
    ])
    write_csv(PACKET_DIR / "TOP_K_AND_SEVERE_MISS_REVIEW.csv", evaluation["top_severe_rows"], [
        "evaluation_scope", "comparison_candidate", "evaluation_subject", "target_season", "position", "record_type", "top_k", "population_rows", "hits", "predicted_top_k", "actual_top_k", "precision", "recall", "false_positives", "severe_false_positives", "false_negatives", "severe_false_negatives", "net_severe_misses", "metric_status", "unsupported_reason", "canonical_definition"
    ])
    write_csv(PACKET_DIR / "CANDIDATE_MINUS_PYF_DELTAS.csv", balance["delta_rows"], [
        "candidate_name", "delta_level", "target_season", "position", "omitted_season", "candidate_spearman", "pyf_spearman", "candidate_minus_pyf_spearman"
    ])
    write_csv_exclusive(PACKET_DIR / "PROSPECTIVE_2026_BASELINE_FREEZE.csv", baseline_rows, FREEZE_FIELDS)
    challenger_path = PACKET_DIR / "PROSPECTIVE_2026_CHALLENGER_FREEZE.csv"
    if challenger_rows is not None:
        write_csv_exclusive(challenger_path, challenger_rows, FREEZE_FIELDS)
    elif challenger_path.exists():
        raise RuntimeError("A challenger freeze exists even though the mechanical gate failed; V1 will not overwrite or delete it")


def gate_mark(value: bool) -> str:
    return "PASS" if value else "FAIL"


def write_narrative_artifacts(
    balance: dict[str, Any],
    baseline_rows: list[dict[str, Any]],
    challenger_rows: list[dict[str, Any]] | None,
) -> None:
    ridge = balance["candidate_summaries"][RIDGE]
    legacy = balance["candidate_summaries"][LEGACY]
    gates = balance["gate_results"]
    verdict = balance["verdict"]
    worst_position, worst_position_delta = min(ridge["position_deltas"].items(), key=lambda item: item[1])
    worst_season, worst_season_delta = min(ridge["season_deltas"].items(), key=lambda item: item[1])
    positive_seasons = sum(1 for value in ridge["season_deltas"].values() if value > 0)
    failed_gates = [name for name, passed in gates.items() if not passed]
    baseline_counts = {
        candidate: sum(1 for row in baseline_rows if row["candidate_name"] == candidate and row["score_valid"])
        for candidate in (PYF, LEGACY, CURRENT_BOARD_COMPARATOR)
    }

    source_gate = f"""# Source and Receipt Gate

## Decision

`PASS_FOR_REVIEW_ONLY_TEMPORAL_VALIDATION_AND_2026_BASELINE_FREEZE_WITH_CAVEATS`

The historical Formula Mart and age sidecar each contain 5,518 exact, duplicate-free `(target season, position, GSIS player_id)` rows. The Mart's N→N+1 leakage and as-of gates pass. Its production-related stamps remain false; this lane is an expressly authorized review-only evaluation, not source promotion or production training approval.

The age sidecar contains eight rows with missing DOB/draft identity and three rows flagged for duplicate-GSIS DOB conflict. Those 11 age values are deterministically null-fenced: the ridge applies its preregistered training-only imputation and missingness indicator, while exact GAUNTLET_081 marks those candidate rows invalid. No unsafe age value enters a score.

The 2026 completed-feature file contains 342 distinct QB/RB/WR/TE players after exact duplicate collapse: 231 scoreable and 111 null-fenced. Every scoreable row has an exact GSIS identity, and all 231 join to a single nonconflicting DynastyProcess DOB. No normalized-name identity fallback is used.

## Verified controlling hashes

- Formula Mart: `{EXPECTED_HASHES[MART]}`
- Historical age/lifecycle sidecar: `{EXPECTED_HASHES[AGE]}`
- Accepted Gauntlet runner: `{EXPECTED_HASHES[GAUNTLET_RUNNER]}`
- Mart builder: `{EXPECTED_HASHES[MART_BUILDER]}`
- Canonical severe-miss runner: `{EXPECTED_HASHES[SEVERE_RUNNER]}`
- 2026 completed features: `{EXPECTED_HASHES[CURRENT_FEATURES]}`
- Raw player-stat receipt: `{EXPECTED_HASHES[RAW_PLAYER_STATS]}`
- DynastyProcess identity/DOB/draft source: `{EXPECTED_HASHES[DYNASTY_PROCESS]}`
- Exact current-board comparator: `{EXPECTED_HASHES[CURRENT_BOARD]}`
- NWR scoring contract: `{EXPECTED_HASHES[SCORING_CONFIG]}`

## Caveats and blocked uses

- Formula Mart rows are `review_only`; `training_allowed`, `model_use_allowed`, `source_truth_allowed`, `production_approved`, and rankings integration remain false.
- The exact current-board artifact is `candidate_review_only_not_active_rankings`. It is frozen as the exact app-visible/current-board comparator, not relabeled as human-approved production-active ranks.
- Production/model use, rankings integration, app/runtime changes, and source promotion remain blocked.
"""
    write_text(PACKET_DIR / "SOURCE_AND_RECEIPT_GATE.md", source_gate)

    report = f"""# Formula Temporal Validation Framework V1 Report

## Verdict

`{verdict}`

The preregistered rolling-origin evaluation completed across **11 independent target seasons (2015–2025)** and all four supported positions. Every scored origin used only earlier target seasons for fitting and only feature-season T-1 facts for target season T. Predictions were hashed before each scored origin's outcomes were joined.

All historical evidence is `RETROSPECTIVE_TEMPORAL_VALIDATION_WITH_PRIOR_SELECTION_CAVEATS`. It is candidate-screening evidence, not fresh or untouched proof and not a production superiority claim.

## Controlling reconciliation preserved

The accepted audit at `dce5131d77f9fb671bdf6141650677d2a3444641` was not rerun or altered. Its controlling values remain PYF `0.741285` ranking-aligned / `0.693350` pooled and exact GAUNTLET_081 `0.754604` ranking-aligned / `0.708315` pooled. The retired 70/20/10 proxy remains retired. The present rolling-origin scoreboards answer a new temporal-stability question and do not replace those audit values.

## Shared-row headline results

| Candidate | Position-balanced Spearman | PYF on same rows | Delta | Season-balanced Spearman | PYF on same rows | Delta |
|---|---:|---:|---:|---:|---:|---:|
| Exact legacy GAUNTLET_081 | {legacy['position_balanced_candidate']:.6f} | {legacy['position_balanced_pyf']:.6f} | {legacy['position_balanced_delta']:+.6f} | {legacy['season_balanced_candidate']:.6f} | {legacy['season_balanced_pyf']:.6f} | {legacy['season_balanced_delta']:+.6f} |
| Position-specific ridge | {ridge['position_balanced_candidate']:.6f} | {ridge['position_balanced_pyf']:.6f} | {ridge['position_balanced_delta']:+.6f} | {ridge['season_balanced_candidate']:.6f} | {ridge['season_balanced_pyf']:.6f} | {ridge['season_balanced_delta']:+.6f} |

With the complete 11×4 season-position grid, macro, position-balanced, and season-balanced arithmetic means are algebraically equal. They are still reported separately to preserve the preregistered weighting contracts.

The ridge's worst position was **{worst_position}** at `{worst_position_delta:+.6f}` versus PYF. Its worst season was **{worst_season}** at `{worst_season_delta:+.6f}`. It improved in `{positive_seasons}` of 11 season-balanced comparisons.

## Severe misses and coverage

On ridge/PYF shared rows, severe false positives were `{ridge['severe_overall']['candidate_sfp']}` for ridge versus `{ridge['severe_overall']['pyf_sfp']}` for PYF. Severe false negatives were `{ridge['severe_overall']['candidate_sfn']}` versus `{ridge['severe_overall']['pyf_sfn']}`. Net severe misses were `{ridge['severe_overall']['candidate_sfp'] + ridge['severe_overall']['candidate_sfn']}` versus `{ridge['severe_overall']['pyf_sfp'] + ridge['severe_overall']['pyf_sfn']}`.

Ridge full historical coverage was `{ridge['candidate_valid_rows']}/{ridge['eligible_universe_rows']}` (`{ridge['candidate_coverage']:.6f}`), versus PYF `{ridge['pyf_valid_rows']}/{ridge['eligible_universe_rows']}` (`{ridge['pyf_coverage']:.6f}`). Shared-row and full-coverage evaluations remain separate in their dedicated scoreboards.

## Uncertainty

The paired season-cluster bootstrap used 10,000 draws and seed `20260710`. The position-balanced 95% interval is `[{ridge['position_ci_lower']:+.6f}, {ridge['position_ci_upper']:+.6f}]`; the season-balanced interval is `[{ridge['season_ci_lower']:+.6f}, {ridge['season_ci_upper']:+.6f}]`. The inference unit is season, never player. Eleven seasons support a stability review but not a claim of formal certainty or production proof.

## Mechanical gate

| Gate | Result |
|---|---|
| Headline improvement | {gate_mark(gates['headline_improvement'])} |
| Not isolated to one season | {gate_mark(gates['not_isolated'])} |
| No material repeated position regression | {gate_mark(gates['no_repeated_position_regression'])} |
| No severe-FP increase overall or by position | {gate_mark(gates['no_severe_fp_increase'])} |
| No favorable coverage reduction | {gate_mark(gates['no_favorable_coverage_reduction'])} |
| Season-cluster uncertainty review | {gate_mark(gates['uncertainty_review'])} |
| Source, leakage, identity, and runtime | {gate_mark(gates['source_leakage_identity_runtime'])} |

Failed gates: `{('|'.join(failed_gates) if failed_gates else 'none')}`.

## Prospective 2026 freeze

- PYF frozen: **yes**, `{baseline_counts[PYF]}` valid scores on the controlled population.
- Exact GAUNTLET_081 frozen: **yes**, `{baseline_counts[LEGACY]}` valid scores.
- Exact current-board comparator frozen: **yes**, `{baseline_counts[CURRENT_BOARD_COMPARATOR]}` native valid rows, separately caveated.
- Ridge passed every historical gate: **{'yes' if balance['gate_pass'] else 'no'}**.
- New review-only challenger frozen: **{'yes' if challenger_rows is not None else 'no'}**.

The common freeze timestamp is `{FREEZE_TIMESTAMP}`. The snapshots are review-only tracking artifacts. They do not change rankings, production formulas, the app, runtime behavior, or source status.
"""
    write_text(PACKET_DIR / "FORMULA_TEMPORAL_VALIDATION_FRAMEWORK_V1_REPORT.md", report)

    executive = f"""# Executive Verdict

`{verdict}`

The deterministic 2015–2025 rolling-origin evaluation used 11 independent target seasons. The ridge's position-balanced and season-balanced Spearman results were `{ridge['position_balanced_candidate']:.6f}` and `{ridge['season_balanced_candidate']:.6f}`, each versus PYF `{ridge['position_balanced_pyf']:.6f}`, for deltas of `{ridge['position_balanced_delta']:+.6f}` and `{ridge['season_balanced_delta']:+.6f}`.

Worst position: `{worst_position}` (`{worst_position_delta:+.6f}`). Worst season: `{worst_season}` (`{worst_season_delta:+.6f}`). Severe FP: ridge `{ridge['severe_overall']['candidate_sfp']}` vs PYF `{ridge['severe_overall']['pyf_sfp']}`. Historical coverage: ridge `{ridge['candidate_valid_rows']}/{ridge['eligible_universe_rows']}` vs PYF `{ridge['pyf_valid_rows']}/{ridge['eligible_universe_rows']}`. Position-balanced 95% interval: `[{ridge['position_ci_lower']:+.6f}, {ridge['position_ci_upper']:+.6f}]`; season-balanced: `[{ridge['season_ci_lower']:+.6f}, {ridge['season_ci_upper']:+.6f}]`.

PYF, exact GAUNTLET_081, and the exact separately caveated current-board comparator were frozen for prospective 2026 tracking. The regularized challenger **{'passed and was frozen' if balance['gate_pass'] else 'did not pass and was not frozen'}**.

The accepted formula-accuracy reconciliation did not change. All historical results remain retrospective with prior-selection caveats. Production/model use, rankings integration, app/runtime changes, and source promotion remain blocked. No push is authorized.
"""
    write_text(PACKET_DIR / "EXECUTIVE_VERDICT.md", executive)

    uncertainty = f"""# Uncertainty and Stability Review

## Independent information

The evaluation has **11 independent target seasons**, 2015–2025. Player rows are not treated as independent seasons. The complete grid contains 44 season-position groups.

## Frozen method

Paired ridge-minus-PYF season deltas were constructed by equally averaging the four position deltas within each season. A deterministic season-cluster bootstrap sampled the 11 seasons with replacement for 10,000 draws using NumPy seed `20260710`. The two-sided percentile interval uses the 2.5th and 97.5th percentiles.

## Result

- Point estimate, position-balanced: `{ridge['position_balanced_delta']:+.6f}`.
- Point estimate, season-balanced: `{ridge['season_balanced_delta']:+.6f}`.
- Position-balanced 95% season-cluster interval: `[{ridge['position_ci_lower']:+.6f}, {ridge['position_ci_upper']:+.6f}]`.
- Season-balanced 95% season-cluster interval: `[{ridge['season_ci_lower']:+.6f}, {ridge['season_ci_upper']:+.6f}]`.
- Minimum leave-one-season-out position-balanced delta: `{min(ridge['loso_position'].values()):+.6f}`.
- Minimum leave-one-season-out season-balanced delta: `{min(ridge['loso_season'].values()):+.6f}`.
- Positive season deltas: `{positive_seasons}/11`.
- Mechanical uncertainty gate: `{gate_mark(gates['uncertainty_review'])}`.

Position-balanced and season-balanced values coincide because every one of the 11 seasons has all four positions with equal weights. Leave-one-season-out results are aggregation sensitivity checks over frozen out-of-fold predictions, not model refits.

Eleven seasons are materially more informative than two, but still a limited number of independent units. The interval is a stability diagnostic; it does not establish formal certainty, causality, or production superiority.
"""
    write_text(PACKET_DIR / "UNCERTAINTY_AND_STABILITY_REVIEW.md", uncertainty)

    gate_lines = "\n".join(f"- `{name}`: `{gate_mark(value)}`" for name, value in gates.items())
    gate_doc = f"""# Challenger Gate Decision

## Decision

`{verdict}`

`{RIDGE}` **{'passes every preregistered historical stability gate and is eligible for a prospective review-only freeze' if balance['gate_pass'] else 'fails one or more preregistered historical stability gates and is not eligible for a prospective challenger freeze'}**.

## Mechanical results

{gate_lines}

Failed gates: `{('|'.join(failed_gates) if failed_gates else 'none')}`.

No aggregate improvement can compensate for a failed repeated-position, severe-FP, coverage, leakage, identity, source, runtime, or uncertainty gate. Exact GAUNTLET_081 remains a locked legacy research reference and is never eligible for the new-challenger label.

`PROSPECTIVE_2026_CHALLENGER_FREEZE.csv` is **{'present because all gates passed' if challenger_rows is not None else 'intentionally absent because the ridge did not pass every gate'}**.
"""
    write_text(PACKET_DIR / "CHALLENGER_GATE_DECISION.md", gate_doc)

    future_contract = f"""# Future 2026 Outcome Evaluation Contract

## Purpose

Actual future 2026 outcomes are required before any final accuracy or production claim. This contract evaluates immutable predictions frozen at `{FREEZE_TIMESTAMP}` without rewriting them after outcomes begin.

## Frozen comparators

1. PYF frozen baseline.
2. Exact `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE` legacy reference.
3. `{RIDGE}` only if `PROSPECTIVE_2026_CHALLENGER_FREEZE.csv` exists and its hash matches the freeze manifest.
4. Exact current app-visible/current-board review ranks as a separately caveated comparator with current-information and proprietary-component advantages.

## Outcome join

- Join actual 2026 results only by admitted exact player identity and position.
- Preserve the original frozen files and hashes.
- Never match by normalized player name alone.
- Resolve a correction only in a new version while retaining V1.
- Record missing outcomes and changed eligibility explicitly; do not silently exclude them.

## Required evaluation

- Spearman and Kendall by position.
- Equal-position headline average.
- Pooled within-position-rank Spearman as secondary only.
- Canonical QB12, RB12/24, WR12/24/36, and TE12 top-K precision/recall.
- Canonical severe false positives and false negatives using QB10/RB30/WR40/TE12 startable cutoffs.
- Full coverage, shared-row comparisons, missingness, and every material exclusion.
- Severe misses and top-K decisions at the player level for review.
- The current-board comparator reported separately, never as an equivalent receipt-safe formula.

## Decision boundary

The 2026 evaluation may inform a later human review. It does not automatically authorize production/model use, rankings integration, app/runtime changes, source promotion, recommendations, or sort logic. Those remain blocked until separately approved.
"""
    write_text(PACKET_DIR / "FUTURE_2026_OUTCOME_EVALUATION_CONTRACT.md", future_contract)


def write_freeze_manifest(
    baseline_rows: list[dict[str, Any]], challenger_rows: list[dict[str, Any]] | None, verdict: str
) -> None:
    baseline_path = PACKET_DIR / "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
    challenger_path = PACKET_DIR / "PROSPECTIVE_2026_CHALLENGER_FREEZE.csv"
    manifest = {
        "schema_version": "formula_temporal_validation_prospective_freeze_v1",
        "freeze_timestamp": FREEZE_TIMESTAMP,
        "target_season": 2026,
        "feature_season": 2025,
        "verdict": verdict,
        "immutable": True,
        "review_only": True,
        "production_model_use_allowed": False,
        "rankings_integration_allowed": False,
        "app_runtime_change_allowed": False,
        "source_promotion_allowed": False,
        "baseline_freeze": {
            "path": baseline_path.name,
            "sha256": sha256(baseline_path),
            "rows": len(baseline_rows),
            "valid_rows_by_candidate": {
                candidate: sum(1 for row in baseline_rows if row["candidate_name"] == candidate and row["score_valid"])
                for candidate in (PYF, LEGACY, CURRENT_BOARD_COMPARATOR)
            },
        },
        "challenger_freeze": {
            "applicable": challenger_rows is not None,
            "path": challenger_path.name if challenger_rows is not None else None,
            "sha256": sha256(challenger_path) if challenger_rows is not None else None,
            "rows": len(challenger_rows) if challenger_rows is not None else 0,
            "absence_reason": None if challenger_rows is not None else "REGULARIZED_CHALLENGER_DID_NOT_PASS_EVERY_PREREGISTERED_HISTORICAL_STABILITY_GATE",
        },
        "inputs": [
            {"name": row["source_name"], "path": row["path"], "sha256": row["sha256"], "source_asof": row["source_asof"]}
            for row in source_ledger_rows()
        ],
        "current_board_comparator_caveat": "Exact current app-visible/current-board review artifact; candidate_review_only_not_active_rankings; current-information and proprietary-component advantage; not equivalent to controlled receipt-safe formulas.",
        "correction_policy": "Never rewrite V1. Retain V1 and create a separately versioned snapshot.",
    }
    write_text_exclusive(PACKET_DIR / "PROSPECTIVE_2026_FREEZE_MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True))


def main() -> None:
    assert_preregistration()
    assert_fresh_freeze_targets()
    verified = verify_sources()
    identity_precheck = verify_2026_identity_precheck()
    historical_features, labels, _, historical_age_gate = load_historical()
    predictions, origin_rows, coefficient_rows = build_historical_predictions(historical_features, labels)
    evaluation = evaluate_historical(predictions)
    balance = balanced_and_gate(
        evaluation,
        origin_rows,
        bool(verified) and identity_precheck and historical_age_gate,
    )
    baseline_rows, challenger_rows, _ = build_2026_freezes(
        historical_features, labels, balance["gate_pass"], coefficient_rows
    )
    write_core_csvs(
        predictions,
        origin_rows,
        coefficient_rows,
        evaluation,
        balance,
        baseline_rows,
        challenger_rows,
    )
    write_narrative_artifacts(balance, baseline_rows, challenger_rows)
    write_freeze_manifest(baseline_rows, challenger_rows, balance["verdict"])

    ridge = balance["candidate_summaries"][RIDGE]
    result = {
        "verdict": balance["verdict"],
        "verified_sources": len(verified),
        "independent_target_seasons": len(SCORING_SEASONS),
        "position_balanced_candidate": ridge["position_balanced_candidate"],
        "position_balanced_pyf": ridge["position_balanced_pyf"],
        "position_balanced_delta": ridge["position_balanced_delta"],
        "season_balanced_candidate": ridge["season_balanced_candidate"],
        "season_balanced_pyf": ridge["season_balanced_pyf"],
        "season_balanced_delta": ridge["season_balanced_delta"],
        "worst_position": min(ridge["position_deltas"], key=ridge["position_deltas"].get),
        "worst_position_delta": min(ridge["position_deltas"].values()),
        "worst_season": min(ridge["season_deltas"], key=ridge["season_deltas"].get),
        "worst_season_delta": min(ridge["season_deltas"].values()),
        "severe_false_positives_candidate": ridge["severe_overall"]["candidate_sfp"],
        "severe_false_positives_pyf": ridge["severe_overall"]["pyf_sfp"],
        "coverage_candidate": ridge["candidate_coverage"],
        "coverage_pyf": ridge["pyf_coverage"],
        "position_balanced_uncertainty_ci": [ridge["position_ci_lower"], ridge["position_ci_upper"]],
        "season_balanced_uncertainty_ci": [ridge["season_ci_lower"], ridge["season_ci_upper"]],
        "gate_results": balance["gate_results"],
        "pyf_frozen": True,
        "legacy_frozen": True,
        "current_board_comparator_frozen": True,
        "regularized_challenger_frozen": challenger_rows is not None,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
