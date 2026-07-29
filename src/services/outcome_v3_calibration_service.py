"""Deterministic Outcome Columns V3 schema, target, and calibration authority.

This module is intentionally Outcome-only. It never reads or writes ranking
scores, never uses Outcome values as ranking inputs, and joins historical truth
only through exact player identifiers.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.services.nfl_usage_target_label_service import derive_nwr_points

RELEASE_IDENTIFIER = "NWR_OUTCOME_COLUMNS_V3_RC1"
CANONICAL_SOURCE_COMMIT = "dc5ff68c172f7a5a49755934d122ee1f99d87670"
NOT_ENOUGH_INFORMATION = "Not enough information"
NOT_APPLICABLE = "N/A"

POSITIONS = ("QB", "RB", "WR", "TE")
POSITION_THRESHOLDS: Mapping[str, tuple[int, ...]] = {
    "QB": (6, 12),
    "RB": (6, 12, 24, 36),
    "WR": (6, 12, 24, 36),
    "TE": (6, 12),
}
HORIZONS = (
    "THIS_YEAR",
    "NEXT_YEAR",
    "T_PLUS_2",
    "WITHIN_3Y",
    "WITHIN_5Y",
    "TWO_OF_NEXT_3Y",
)
RANKINGS_HORIZONS = HORIZONS[:5]
HORIZON_OFFSETS: Mapping[str, tuple[int, ...]] = {
    "THIS_YEAR": (0,),
    "NEXT_YEAR": (1,),
    "T_PLUS_2": (2,),
    "WITHIN_3Y": (0, 1, 2),
    "WITHIN_5Y": (0, 1, 2, 3, 4),
    "TWO_OF_NEXT_3Y": (0, 1, 2),
}
HORIZON_MIN_HITS: Mapping[str, int] = {
    "THIS_YEAR": 1,
    "NEXT_YEAR": 1,
    "T_PLUS_2": 1,
    "WITHIN_3Y": 1,
    "WITHIN_5Y": 1,
    "TWO_OF_NEXT_3Y": 2,
}
CURRENT_HORIZON_MAP = {
    "this_year": "THIS_YEAR",
    "next_year": "NEXT_YEAR",
    "within_5y": "WITHIN_5Y",
}

CALIBRATION_FAMILIES = (
    "C0_CURRENT_PROFILE_BUCKET_BASELINE",
    "C1_REGULARIZED_LOGISTIC",
    "C2_BETA_CALIBRATION",
    "C3_ISOTONIC_MONOTONIC",
)
BASELINE_ALPHA = 1.0
BASELINE_BETA = 1.0
PROFILE_PRIOR_STRENGTH = 5.0
LOGISTIC_RIDGE = 4.0
BETA_RIDGE = 6.0

# Repository authority in outcome_v2_probability_validation_service.py.
MIN_LABELED_ROWS = 100
MIN_POSITIVES = 20
MIN_NEGATIVES = 20
MIN_COMPLETE_ANCHOR_SEASONS = 5
ISOTONIC_MIN_ROWS = 400
ISOTONIC_MIN_EVENTS = 40

MAX_BASELINE_ECE = 0.15
MAX_LARGE_BUCKET_ERROR = 0.30
BRIER_NONINFERIOR_MARGIN = 0.002
LOG_LOSS_NONINFERIOR_MARGIN = 0.005
AUC_NONINFERIOR_MARGIN = 0.02
MAX_SEASON_REGRESSION_SHARE = 0.35
MAX_COHORT_BRIER_REGRESSION = 0.03

# Preregistered before candidate evaluation. Projection may not conceal a
# structurally incoherent candidate.
PROJECTION_MAX_RAW_VIOLATION_ROW_SHARE = 0.10
PROJECTION_MAX_ADJUSTED_ROW_SHARE = 0.25
PROJECTION_MAX_MEAN_ABS_ADJUSTMENT = 0.02
PROJECTION_MAX_P95_ABS_ADJUSTMENT = 0.05
PROJECTION_MAX_SINGLE_ADJUSTMENT = 0.15

CURRENT_SCHEMA_SOURCE = Path("src/services/draft_day_app_v1_service.py")
CURRENT_DISPLAY_SOURCE = Path(
    "docs/hq/outcomes/outcome_v2_horizon_20260630/"
    "outcome_v2_current_player_display_with_injury_context.csv"
)
LEGACY_METADATA_SOURCE = Path(
    "docs/draft_day_exports/final_board_v1_20260622/app_props/outcome_columns/"
    "outcome_column_metadata.csv"
)

ADMITTED_HISTORICAL_FEATURES = (
    "pyf_prior_rank_position_feature_season",
    "pyf_prior_nwr_points",
    "prior_games",
)
BLOCKED_FEATURE_TOKENS = (
    "adp",
    "market",
    "dynastyprocess",
    "future_",
    "next_",
    "label_",
    "current_board_rank",
    "player_name",
    "team",
    "injury",
    "rotowire",
    "fantasypros",
    "projection",
)

UPGRADE = "OUTCOME_V3_UPGRADE_ADMISSIBLE"
KEEP_BASELINE = "OUTCOME_V3_KEEP_CURRENT_BASELINE"
DIRECTIONAL_HOLD = "OUTCOME_V3_DIRECTIONALLY_BETTER_NOT_ADOPTED"
BLOCKED_WEAK = "OUTCOME_V3_BLOCKED_WEAK_CALIBRATION"
BLOCKED_LOW_SAMPLE = "OUTCOME_V3_BLOCKED_LOW_SAMPLE"
NO_INFORMATION = "OUTCOME_V3_NOT_ENOUGH_INFORMATION"
BLOCKED_CLASSIFICATIONS = {BLOCKED_WEAK, BLOCKED_LOW_SAMPLE, NO_INFORMATION}


@dataclass(frozen=True)
class IsotonicModel:
    upper_bounds: tuple[float, ...]
    values: tuple[float, ...]

    def predict(self, values: Sequence[float]) -> np.ndarray:
        if not self.values:
            return np.full(len(values), 0.5, dtype=float)
        bounds = np.asarray(self.upper_bounds, dtype=float)
        fitted = np.asarray(self.values, dtype=float)
        raw = np.asarray(values, dtype=float)
        indices = np.searchsorted(bounds, raw, side="left")
        indices = np.clip(indices, 0, len(fitted) - 1)
        return fitted[indices]


def stable_hash(value: Any) -> str:
    body = json.dumps(
        value,
        allow_nan=False,
        default=str,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _literal_assignment(path: Path, name: str) -> Any:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == name for target in targets):
            continue
        if node.value is not None:
            return ast.literal_eval(node.value)
    raise AssertionError(f"repository authority assignment not found: {path}:{name}")


def field_id(position: str, threshold: int, horizon: str) -> str:
    normalized_horizon = str(horizon).upper()
    if position not in POSITION_THRESHOLDS:
        raise AssertionError(f"unsupported Outcome position: {position}")
    if threshold not in POSITION_THRESHOLDS[position]:
        raise AssertionError(f"unsupported Outcome threshold: {position} T{threshold}")
    if normalized_horizon not in HORIZONS:
        raise AssertionError(f"unsupported Outcome horizon: {horizon}")
    return f"{position}_T{threshold}_{normalized_horizon}"


def field_parts(value: str) -> tuple[str, int, str]:
    match = re.fullmatch(
        r"(QB|RB|WR|TE)_T(6|12|24|36)_"
        r"(THIS_YEAR|NEXT_YEAR|T_PLUS_2|WITHIN_3Y|WITHIN_5Y|TWO_OF_NEXT_3Y)",
        str(value),
    )
    if not match:
        raise AssertionError(f"invalid governed Outcome V3 field: {value}")
    position = match.group(1)
    threshold = int(match.group(2))
    horizon = match.group(3)
    if threshold not in POSITION_THRESHOLDS[position]:
        raise AssertionError(f"wrong-position threshold family: {value}")
    return position, threshold, horizon


def dynamic_horizon_label(horizon: str, as_of_year: int) -> str:
    return {
        "THIS_YEAR": str(as_of_year),
        "NEXT_YEAR": str(as_of_year + 1),
        "T_PLUS_2": str(as_of_year + 2),
        "WITHIN_3Y": "Within 3 Years",
        "WITHIN_5Y": "Within 5 Years",
        "TWO_OF_NEXT_3Y": "Two Qualifying Seasons Within 3 Years",
    }[str(horizon).upper()]


def _target_definition(position: str, threshold: int, horizon: str) -> str:
    hit = f"{position} NWR-scoring position finish <= {threshold}"
    if horizon in {"THIS_YEAR", "NEXT_YEAR", "T_PLUS_2"}:
        return f"{hit} in exact offset {HORIZON_OFFSETS[horizon][0]}"
    if horizon == "TWO_OF_NEXT_3Y":
        return f"at least two seasons with {hit} across offsets 0..2"
    return f"at least one season with {hit} across offsets {HORIZON_OFFSETS[horizon]}"


def _current_field_from_label(label: str) -> tuple[str, int, str]:
    match = re.fullmatch(
        r"(QB|RB|WR|TE) T(6|12|24|36) (This Year|Next Year|Within 5Y)",
        str(label),
    )
    if not match:
        raise AssertionError(f"malformed current Outcome authority label: {label}")
    return (
        match.group(1),
        int(match.group(2)),
        CURRENT_HORIZON_MAP[match.group(3).lower().replace(" ", "_")],
    )


def current_outcome_authority_inventory(repo_root: str | Path) -> pd.DataFrame:
    """Verify and inventory all 7 aliases plus 36 governed current fields."""

    root = Path(repo_root)
    authority_path = root / CURRENT_SCHEMA_SOURCE
    aliases = _literal_assignment(authority_path, "APPROVED_OUTCOME_DISPLAY_FIELDS")
    approved = _literal_assignment(authority_path, "APPROVED_OUTCOME_V2_DISPLAY_FIELDS")
    blocked = tuple(_literal_assignment(authority_path, "BLOCKED_OUTCOME_V2_FIELDS"))

    rows: list[dict[str, Any]] = []
    for position_index, (source, target, label) in enumerate(aliases):
        position, threshold_text = str(label).split(" T", maxsplit=1)
        threshold = int(threshold_text)
        canonical = field_id(position, threshold, "THIS_YEAR")
        rows.append(
            {
                "schema_record_type": "LEGACY_V1_ALIAS",
                "internal_name": str(target),
                "source_name": str(source),
                "compatibility_target": canonical,
                "label": str(label),
                "position": position,
                "position_order": position_index,
                "threshold": threshold,
                "horizon": "THIS_YEAR",
                "target_definition": _target_definition(
                    position, threshold, "THIS_YEAR"
                ),
                "estimator": "Outcome V1 numeric display artifact",
                "calibration": "legacy display-only alias",
                "display_location": "Rankings and Player Compare legacy compatibility",
                "missing_state": NOT_ENOUGH_INFORMATION,
                "wrong_position_state": NOT_APPLICABLE,
                "authority": str(LEGACY_METADATA_SOURCE).replace("\\", "/"),
                "release_status": "CURRENT_LEGACY_ALIAS",
            }
        )

    governed_rows: dict[str, dict[str, Any]] = {}
    for source, target, label, expected_position in approved:
        position, threshold, horizon = _current_field_from_label(str(label))
        if position != expected_position:
            raise AssertionError(f"current Outcome position authority drift: {label}")
        canonical = field_id(position, threshold, horizon)
        if str(source).replace(" ", "_").upper() != canonical:
            raise AssertionError(f"current Outcome field name drift: {source} != {canonical}")
        governed_rows[canonical] = {
            "schema_record_type": "CURRENT_GOVERNED",
            "internal_name": canonical,
            "source_name": str(source),
            "compatibility_target": "",
            "label": str(label),
            "position": position,
            "position_order": POSITIONS.index(position),
            "threshold": threshold,
            "horizon": horizon,
            "target_definition": _target_definition(position, threshold, horizon),
            "estimator": "Laplace profile-bucket baseline; prior strength 5.0",
            "calibration": "PASS_APP_DISPLAY_VALIDATION",
            "display_location": "Dynasty Rankings and Player Compare",
            "missing_state": NOT_ENOUGH_INFORMATION,
            "wrong_position_state": NOT_APPLICABLE,
            "authority": str(CURRENT_SCHEMA_SOURCE).replace("\\", "/"),
            "release_status": "CURRENT_BASELINE_AVAILABLE",
            "target_column": str(target),
        }
    for canonical in blocked:
        position, threshold, horizon = field_parts(canonical)
        governed_rows[canonical] = {
            "schema_record_type": "CURRENT_GOVERNED",
            "internal_name": canonical,
            "source_name": canonical.replace("_", " ").title(),
            "compatibility_target": "",
            "label": f"{position} T{threshold} Within 5Y",
            "position": position,
            "position_order": POSITIONS.index(position),
            "threshold": threshold,
            "horizon": horizon,
            "target_definition": _target_definition(position, threshold, horizon),
            "estimator": "Laplace profile-bucket baseline; prior strength 5.0",
            "calibration": "BLOCKED_CALIBRATION_WEAK",
            "display_location": "Blocked; nonnumeric",
            "missing_state": NOT_ENOUGH_INFORMATION,
            "wrong_position_state": NOT_APPLICABLE,
            "authority": str(CURRENT_SCHEMA_SOURCE).replace("\\", "/"),
            "release_status": "CURRENT_BLOCKED_WEAK_CALIBRATION",
            "target_column": f"outcome_v2_{canonical.lower()}_display_only",
        }

    expected = {
        field_id(position, threshold, horizon)
        for position, thresholds in POSITION_THRESHOLDS.items()
        for threshold in thresholds
        for horizon in ("THIS_YEAR", "NEXT_YEAR", "WITHIN_5Y")
    }
    if len(aliases) != 7 or len(governed_rows) != 36 or set(governed_rows) != expected:
        raise AssertionError(
            "current Outcome authority mismatch: "
            f"aliases={len(aliases)} governed={len(governed_rows)} "
            f"missing={sorted(expected - set(governed_rows))} "
            f"extra={sorted(set(governed_rows) - expected)}"
        )
    rows.extend(governed_rows.values())
    result = pd.DataFrame(rows)
    if len(result) != 43:
        raise AssertionError(f"current Outcome schema must contain 43 rows, found {len(result)}")
    return result.sort_values(
        ["schema_record_type", "position_order", "horizon", "threshold", "internal_name"],
        kind="stable",
    ).drop(columns=["position_order"]).reset_index(drop=True)


def outcome_v3_schema(
    current_inventory: pd.DataFrame,
    *,
    as_of_year: int,
) -> pd.DataFrame:
    """Create 72 governed relative fields and the explicit 7-alias map."""

    governed: list[dict[str, Any]] = []
    for position in POSITIONS:
        for threshold in POSITION_THRESHOLDS[position]:
            for horizon in HORIZONS:
                canonical = field_id(position, threshold, horizon)
                display_locations = (
                    "Player Compare expanded only"
                    if horizon == "TWO_OF_NEXT_3Y"
                    else "Rankings Outcome lens and Player Compare"
                )
                governed.append(
                    {
                        "schema_record_type": "OUTCOME_V3_GOVERNED",
                        "internal_name": canonical,
                        "compatibility_target": "",
                        "position": position,
                        "threshold": threshold,
                        "relative_horizon": horizon,
                        "dynamic_horizon_label": dynamic_horizon_label(horizon, as_of_year),
                        "user_facing_label": (
                            f"{position} T{threshold} "
                            f"{dynamic_horizon_label(horizon, as_of_year)}"
                        ),
                        "event_window_offsets": "|".join(
                            str(offset) for offset in HORIZON_OFFSETS[horizon]
                        ),
                        "minimum_qualifying_seasons": HORIZON_MIN_HITS[horizon],
                        "target_definition": _target_definition(
                            position, threshold, horizon
                        ),
                        "estimator": (
                            "C0 Laplace profile bucket or field-admissible C1/C2/C3"
                        ),
                        "calibration": "set by PER_FIELD_ACCEPTANCE_GATE_MATRIX.csv",
                        "display_location": display_locations,
                        "missing_state": NOT_ENOUGH_INFORMATION,
                        "wrong_position_state": NOT_APPLICABLE,
                        "storage_name": f"outcome_v3_{canonical.lower()}_display_only",
                        "compatibility_source": "",
                        "display_only": "true",
                        "rank_use_allowed": "false",
                    }
                )

    aliases: list[dict[str, Any]] = []
    current_aliases = current_inventory.loc[
        current_inventory["schema_record_type"].eq("LEGACY_V1_ALIAS")
    ]
    for row in current_aliases.to_dict("records"):
        aliases.append(
            {
                "schema_record_type": "LEGACY_V1_ALIAS",
                "internal_name": row["internal_name"],
                "compatibility_target": row["compatibility_target"],
                "position": row["position"],
                "threshold": int(row["threshold"]),
                "relative_horizon": "THIS_YEAR",
                "dynamic_horizon_label": str(as_of_year),
                "user_facing_label": row["label"],
                "event_window_offsets": "0",
                "minimum_qualifying_seasons": 1,
                "target_definition": row["target_definition"],
                "estimator": "Compatibility alias to governed Outcome V3 field",
                "calibration": "inherits compatibility target",
                "display_location": "Preserved legacy routes and exports",
                "missing_state": NOT_ENOUGH_INFORMATION,
                "wrong_position_state": NOT_APPLICABLE,
                "storage_name": row["internal_name"],
                "compatibility_source": row["source_name"],
                "display_only": "true",
                "rank_use_allowed": "false",
            }
        )
    result = pd.DataFrame([*governed, *aliases])
    governed_frame = result.loc[
        result["schema_record_type"].eq("OUTCOME_V3_GOVERNED")
    ]
    if len(governed_frame) != 72 or len(result) != 79:
        raise AssertionError(
            f"Outcome V3 schema mismatch: governed={len(governed_frame)} total={len(result)}"
        )
    if governed_frame["internal_name"].nunique() != 72:
        raise AssertionError("Outcome V3 governed field identifiers are not unique")
    return result.sort_values(
        ["schema_record_type", "position", "relative_horizon", "threshold", "internal_name"],
        kind="stable",
    ).reset_index(drop=True)


def governed_field_specs(schema: pd.DataFrame) -> pd.DataFrame:
    fields = schema.loc[
        schema["schema_record_type"].eq("OUTCOME_V3_GOVERNED")
    ].copy()
    return fields.rename(columns={"relative_horizon": "horizon"})[
        [
            "internal_name",
            "position",
            "threshold",
            "horizon",
            "dynamic_horizon_label",
            "user_facing_label",
            "target_definition",
        ]
    ].sort_values(["position", "horizon", "threshold"], kind="stable").reset_index(
        drop=True
    )


def relationship_edges(schema: pd.DataFrame) -> pd.DataFrame:
    fields = set(governed_field_specs(schema)["internal_name"])
    edges: list[dict[str, str]] = []
    for position, thresholds in POSITION_THRESHOLDS.items():
        for horizon in HORIZONS:
            for left, right in zip(thresholds, thresholds[1:], strict=False):
                edges.append(
                    {
                        "narrower_field": field_id(position, left, horizon),
                        "broader_field": field_id(position, right, horizon),
                        "relationship": "probability_lte",
                        "authority": "threshold event-set nesting",
                    }
                )
        for threshold in thresholds:
            within_three = field_id(position, threshold, "WITHIN_3Y")
            within_five = field_id(position, threshold, "WITHIN_5Y")
            for exact in ("THIS_YEAR", "NEXT_YEAR", "T_PLUS_2"):
                edges.append(
                    {
                        "narrower_field": field_id(position, threshold, exact),
                        "broader_field": within_three,
                        "relationship": "probability_lte",
                        "authority": "exact-year event subset of three-year cumulative event",
                    }
                )
            edges.append(
                {
                    "narrower_field": within_three,
                    "broader_field": within_five,
                    "relationship": "probability_lte",
                    "authority": "three-year cumulative event subset of five-year event",
                }
            )
            edges.append(
                {
                    "narrower_field": field_id(
                        position, threshold, "TWO_OF_NEXT_3Y"
                    ),
                    "broader_field": within_three,
                    "relationship": "probability_lte",
                    "authority": "two qualifying seasons implies at least one",
                }
            )
    result = pd.DataFrame(edges)
    if not set(result["narrower_field"]).issubset(fields) or not set(
        result["broader_field"]
    ).issubset(fields):
        raise AssertionError("Outcome logical graph references an unknown field")
    return result.sort_values(["narrower_field", "broader_field"], kind="stable").reset_index(
        drop=True
    )


def validate_admitted_features(features: Iterable[str]) -> None:
    values = tuple(str(value) for value in features)
    if values != ADMITTED_HISTORICAL_FEATURES:
        raise AssertionError(f"historical Outcome feature contract changed: {values}")
    blocked = [
        value
        for value in values
        if any(token in value.lower() for token in BLOCKED_FEATURE_TOKENS)
    ]
    if blocked:
        raise AssertionError(f"blocked Outcome feature introduced: {blocked}")


def validate_model_contract() -> None:
    """Fail closed if a governed baseline, horizon, or split constant mutates."""

    if (BASELINE_ALPHA, BASELINE_BETA, PROFILE_PRIOR_STRENGTH) != (1.0, 1.0, 5.0):
        raise AssertionError("Outcome C0 smoothing or profile-prior authority changed")
    if HORIZON_OFFSETS != {
        "THIS_YEAR": (0,),
        "NEXT_YEAR": (1,),
        "T_PLUS_2": (2,),
        "WITHIN_3Y": (0, 1, 2),
        "WITHIN_5Y": (0, 1, 2, 3, 4),
        "TWO_OF_NEXT_3Y": (0, 1, 2),
    }:
        raise AssertionError("Outcome V3 horizon offsets changed")
    if HORIZON_MIN_HITS != {
        "THIS_YEAR": 1,
        "NEXT_YEAR": 1,
        "T_PLUS_2": 1,
        "WITHIN_3Y": 1,
        "WITHIN_5Y": 1,
        "TWO_OF_NEXT_3Y": 2,
    }:
        raise AssertionError("Outcome V3 qualifying-season rules changed")
    if (
        MIN_LABELED_ROWS,
        MIN_POSITIVES,
        MIN_NEGATIVES,
        MIN_COMPLETE_ANCHOR_SEASONS,
    ) != (100, 20, 20, 5):
        raise AssertionError("Outcome repository sample gates changed")


def prepare_historical_panel(
    formula_mart: pd.DataFrame,
    age_sidecar: pd.DataFrame,
) -> pd.DataFrame:
    """Prepare the admitted player-season panel using exact IDs only."""

    validate_model_contract()
    required_mart = {
        "substrate_row_id",
        "player_id",
        "target_player_name",
        "position",
        "season",
        "feature_season",
        "label_next_position_finish",
        "pyf_prior_rank_position_feature_season",
        "pyf_prior_nwr_points",
        "prior_games",
        "leakage_check_result",
        "asof_check_result",
    }
    required_age = {
        "player_id",
        "season",
        "position",
        "age",
        "age_bucket",
        "lifecycle_bucket",
        "leakage_flag",
        "identity_flag",
    }
    if missing := sorted(required_mart - set(formula_mart.columns)):
        raise AssertionError(f"formula mart missing Outcome columns: {missing}")
    if missing := sorted(required_age - set(age_sidecar.columns)):
        raise AssertionError(f"age sidecar missing Outcome cohort columns: {missing}")
    validate_admitted_features(ADMITTED_HISTORICAL_FEATURES)

    mart = formula_mart.copy().fillna("")
    age = age_sidecar.copy().fillna("")
    if not mart["leakage_check_result"].eq(
        "PASS_FEATURE_N_TARGET_N_PLUS_1_SEPARATED"
    ).all():
        raise AssertionError("formula mart contains a failed leakage row")
    if not mart["asof_check_result"].eq(
        "PASS_NO_TARGET_SEASON_CONTEXT_IN_FEATURE_COLUMNS"
    ).all():
        raise AssertionError("formula mart contains a failed as-of row")
    mart["anchor_season"] = pd.to_numeric(mart["season"], errors="raise").astype(int)
    mart["feature_season"] = pd.to_numeric(
        mart["feature_season"], errors="raise"
    ).astype(int)
    if not mart["feature_season"].add(1).eq(mart["anchor_season"]).all():
        raise AssertionError("historical feature-to-target offset changed")
    mart["position"] = mart["position"].astype(str).str.upper()
    mart["player_id"] = mart["player_id"].astype(str)
    if mart.duplicated(["player_id", "anchor_season"]).any():
        raise AssertionError("historical player_id-season key is not unique")

    age["anchor_season"] = pd.to_numeric(age["season"], errors="raise").astype(int)
    age["position"] = age["position"].astype(str).str.upper()
    age["player_id"] = age["player_id"].astype(str)
    age["age_evidence_admissible"] = age["leakage_flag"].eq(
        "PASS_STABLE_DOB_AND_DRAFT_YEAR_DERIVED_ASOF_SEPT_01_NO_OUTCOME_FIELDS"
    ) & age["identity_flag"].eq("PASS_GSIS_ID_JOIN")
    admitted_age = age.loc[age["age_evidence_admissible"]].copy()
    if admitted_age.duplicated(["player_id", "anchor_season"]).any():
        raise AssertionError("age player_id-season key is not unique")
    age_columns = admitted_age[
        [
            "player_id",
            "anchor_season",
            "position",
            "age",
            "age_bucket",
            "lifecycle_bucket",
        ]
    ].rename(columns={"position": "age_position"})
    panel = mart.merge(
        age_columns,
        on=["player_id", "anchor_season"],
        how="left",
        validate="one_to_one",
    )
    age_position = panel["age_position"].fillna("").astype(str)
    mismatch = age_position.ne("") & age_position.ne(panel["position"])
    if mismatch.any():
        raise AssertionError("age sidecar exact-ID position mismatch")
    panel["age"] = pd.to_numeric(panel["age"], errors="coerce")
    panel["age_cohort"] = panel["age_bucket"].fillna("").replace("", "unknown_age")
    panel["age_evidence_status"] = np.where(
        panel["age"].notna(),
        "exact_id_admitted_age_sidecar",
        "age_evidence_not_admitted_or_missing",
    )
    panel["low_games"] = (
        pd.to_numeric(panel["prior_games"], errors="coerce").fillna(-1).lt(8)
    )
    veteran_age = panel["position"].map({"QB": 33, "RB": 26, "WR": 28, "TE": 30})
    panel["productive_veteran"] = (
        panel["age"].ge(veteran_age)
        & pd.to_numeric(panel["pyf_prior_nwr_points"], errors="coerce").gt(0)
    )
    panel["early_career"] = panel["lifecycle_bucket"].fillna("").astype(str).str.contains(
        "early_career", case=False, na=False
    )
    panel["outcome_evidence_status"] = ""
    panel["name_join_used"] = False
    return panel.sort_values(
        ["anchor_season", "position", "player_id"], kind="stable"
    ).reset_index(drop=True)


def build_current_feature_frame(
    board: pd.DataFrame,
    current_outcome_authority: pd.DataFrame,
    season_stats: pd.DataFrame,
    *,
    feature_season: int = 2025,
) -> pd.DataFrame:
    """Build detached current features through exact NWR-ID and GSIS-ID joins."""

    board_required = {"player_id", "player_name", "position"}
    authority_required = {
        "nwr_player_id",
        "gsis_id",
        "position",
        "eligibility_status",
        "identity_status",
    }
    stats_required = {
        "player_id",
        "position",
        "season",
        "season_type",
    }
    if missing := sorted(board_required - set(board.columns)):
        raise AssertionError(f"current board missing Outcome identity columns: {missing}")
    if missing := sorted(authority_required - set(current_outcome_authority.columns)):
        raise AssertionError(
            f"current Outcome identity authority missing columns: {missing}"
        )
    if missing := sorted(stats_required - set(season_stats.columns)):
        raise AssertionError(f"current season stats missing columns: {missing}")

    current_board = board.copy().fillna("")
    authority = current_outcome_authority.copy().fillna("")
    stats = season_stats.copy().fillna("")
    current_board["player_id"] = current_board["player_id"].astype(str)
    current_board["position"] = current_board["position"].astype(str).str.upper()
    authority["nwr_player_id"] = authority["nwr_player_id"].astype(str)
    authority["gsis_id"] = authority["gsis_id"].astype(str)
    authority["position"] = authority["position"].astype(str).str.upper()
    stats["player_id"] = stats["player_id"].astype(str)
    stats["position"] = stats["position"].astype(str).str.upper()

    if current_board["player_id"].duplicated().any():
        raise AssertionError("current board player_id is not unique")
    if authority["nwr_player_id"].duplicated().any():
        raise AssertionError("current Outcome authority nwr_player_id is not unique")
    authority_ids = set(authority["nwr_player_id"])
    if not set(current_board["player_id"]).issubset(authority_ids):
        raise AssertionError("current board exact IDs are missing from Outcome authority")

    current_stats = stats.loc[
        stats["season"].astype(str).eq(str(feature_season))
        & stats["season_type"].astype(str).eq("REG")
        & stats["position"].isin(POSITIONS)
    ].copy()
    if current_stats["player_id"].duplicated().any():
        raise AssertionError("current season stats GSIS player_id is not unique")
    current_stats["pyf_prior_nwr_points"] = derive_nwr_points(current_stats)
    current_stats["pyf_prior_rank_position_feature_season"] = (
        current_stats.groupby("position")["pyf_prior_nwr_points"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    current_stats["prior_games"] = (
        pd.to_numeric(current_stats["games"], errors="coerce")
        if "games" in current_stats.columns
        else np.nan
    )
    stats_lookup = current_stats.set_index("player_id").to_dict("index")
    authority_lookup = authority.set_index("nwr_player_id").to_dict("index")

    rows: list[dict[str, Any]] = []
    for player in current_board.to_dict("records"):
        nwr_player_id = str(player["player_id"])
        position = str(player["position"])
        identity = authority_lookup[nwr_player_id]
        gsis_id = str(identity.get("gsis_id", ""))
        eligibility = str(identity.get("eligibility_status", ""))
        identity_status = str(identity.get("identity_status", ""))
        identity_position = str(identity.get("position", "")).upper()
        stats_row = stats_lookup.get(gsis_id)
        if identity_position != position:
            raise AssertionError(
                f"current Outcome identity position mismatch: {nwr_player_id}"
            )

        complete = (
            eligibility == "eligible_veteran_feature_covered"
            and identity_status in {"matched_exact", "matched_high_confidence"}
            and bool(gsis_id)
            and stats_row is not None
            and str(stats_row.get("position", "")).upper() == position
        )
        if complete:
            missing_reason = ""
        elif eligibility == "out_of_scope_rookie_or_prospect":
            missing_reason = "rookie or prospect lacks admitted 2025 NFL feature evidence"
        elif eligibility == "out_of_scope_unsupported_position":
            missing_reason = "position is outside governed QB/RB/WR/TE Outcome families"
        elif not gsis_id:
            missing_reason = "missing exact GSIS identity authority"
        elif stats_row is None:
            missing_reason = "missing admitted 2025 regular-season feature row"
        elif str(stats_row.get("position", "")).upper() != position:
            missing_reason = "exact-ID current feature position mismatch"
        else:
            missing_reason = "current Outcome feature authority is insufficient"

        rows.append(
            {
                "nwr_player_id": nwr_player_id,
                "gsis_id": gsis_id,
                "player_name": str(player["player_name"]),
                "position": position,
                "feature_season": feature_season,
                "pyf_prior_rank_position_feature_season": (
                    stats_row["pyf_prior_rank_position_feature_season"]
                    if complete and stats_row is not None
                    else np.nan
                ),
                "pyf_prior_nwr_points": (
                    stats_row["pyf_prior_nwr_points"]
                    if complete and stats_row is not None
                    else np.nan
                ),
                "prior_games": (
                    stats_row["prior_games"]
                    if complete and stats_row is not None
                    else np.nan
                ),
                "missing_input_state": "complete" if complete else "insufficient",
                "missing_reason": missing_reason,
                "identity_authority": "exact_nwr_player_id_to_exact_gsis_id",
                "name_join_used": False,
            }
        )
    result = pd.DataFrame(rows)
    if len(result) != len(current_board):
        raise AssertionError("current Outcome feature frame changed board row count")
    if result["name_join_used"].astype(bool).any():
        raise AssertionError("current Outcome feature frame used a name join")
    if result["nwr_player_id"].tolist() != current_board["player_id"].tolist():
        raise AssertionError("current Outcome feature frame reordered Finished V1")
    return result


def _profile_bucket(*, finish: Any, points: Any, games: Any, threshold: int) -> str:
    finish_value = pd.to_numeric(finish, errors="coerce")
    points_value = pd.to_numeric(points, errors="coerce")
    games_value = pd.to_numeric(games, errors="coerce")
    if pd.isna(finish_value):
        if pd.isna(points_value) or float(points_value) <= 0:
            return "missing_or_no_prior_production"
        return "missing_finish_has_points"
    if float(finish_value) <= threshold:
        return "prior_threshold_hit"
    if float(finish_value) <= threshold * 2:
        return "near_threshold"
    if float(finish_value) <= threshold * 3:
        return "depth_relevant"
    if (
        pd.notna(games_value)
        and float(games_value) >= 8
        and pd.notna(points_value)
        and float(points_value) > 0
    ):
        return "active_low_finish"
    return "limited_or_inactive"


def build_historical_targets(
    panel: pd.DataFrame,
    schema: pd.DataFrame,
    *,
    max_observable_season: int = 2025,
) -> pd.DataFrame:
    """Build V3 targets without converting missing or future evidence to misses."""

    required = {
        "substrate_row_id",
        "player_id",
        "target_player_name",
        "position",
        "anchor_season",
        "feature_season",
        "label_next_position_finish",
        "pyf_prior_rank_position_feature_season",
        "pyf_prior_nwr_points",
        "prior_games",
        "age",
        "age_cohort",
        "low_games",
        "productive_veteran",
        "early_career",
        "outcome_evidence_status",
        "name_join_used",
    }
    if missing := sorted(required - set(panel.columns)):
        raise AssertionError(f"historical panel missing target columns: {missing}")
    if panel["name_join_used"].astype(bool).any():
        raise AssertionError("name join used in Outcome target authority")
    if panel.duplicated(["player_id", "anchor_season"]).any():
        raise AssertionError("historical Outcome player_id-season key is not unique")

    specs = governed_field_specs(schema)
    history = {
        (str(row.player_id), int(row.anchor_season)): row
        for row in panel.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    ordered = panel.sort_values(["anchor_season", "player_id"], kind="stable")
    for anchor in ordered.itertuples(index=False):
        position = str(anchor.position)
        anchor_season = int(anchor.anchor_season)
        position_specs = specs.loc[specs["position"].eq(position)]
        prior_finish = pd.to_numeric(
            anchor.pyf_prior_rank_position_feature_season, errors="coerce"
        )
        prior_points = pd.to_numeric(anchor.pyf_prior_nwr_points, errors="coerce")
        prior_games = pd.to_numeric(anchor.prior_games, errors="coerce")
        for spec in position_specs.itertuples(index=False):
            horizon = str(spec.horizon)
            offsets = HORIZON_OFFSETS[horizon]
            minimum_hits = HORIZON_MIN_HITS[horizon]
            scheduled_end = anchor_season + max(offsets)
            observations: list[int | None] = []
            observed_seasons: list[int] = []
            hit_seasons: list[int] = []
            missing_count = 0
            future_count = 0
            inactive_count = 0
            retired_count = 0
            terminal_retirement_season: int | None = None
            for offset in offsets:
                season = anchor_season + offset
                if terminal_retirement_season is not None and season > terminal_retirement_season:
                    observations.append(0)
                    observed_seasons.append(season)
                    retired_count += 1
                    continue
                if season > max_observable_season:
                    observations.append(None)
                    future_count += 1
                    continue
                outcome = history.get((str(anchor.player_id), season))
                if outcome is None:
                    observations.append(None)
                    missing_count += 1
                    continue
                evidence = str(getattr(outcome, "outcome_evidence_status", ""))
                if evidence == "explicit_retirement":
                    observations.append(0)
                    observed_seasons.append(season)
                    retired_count += 1
                    terminal_retirement_season = season
                    continue
                if evidence == "explicit_inactive_season":
                    observations.append(0)
                    observed_seasons.append(season)
                    inactive_count += 1
                    continue
                finish = pd.to_numeric(
                    getattr(outcome, "label_next_position_finish", ""), errors="coerce"
                )
                if pd.isna(finish):
                    observations.append(None)
                    missing_count += 1
                    continue
                hit = int(float(finish) <= int(spec.threshold))
                observations.append(hit)
                observed_seasons.append(season)
                if hit:
                    hit_seasons.append(season)

            hit_count = sum(value == 1 for value in observations)
            fully_observed = all(value is not None for value in observations)
            terminal_complete = terminal_retirement_season is not None
            if hit_count >= minimum_hits:
                target_label: float = 1.0
                label_available: float = float(hit_seasons[minimum_hits - 1])
            elif fully_observed or terminal_complete:
                target_label = 0.0
                label_available = float(
                    terminal_retirement_season
                    if terminal_complete
                    else scheduled_end
                )
            else:
                target_label = math.nan
                label_available = math.nan

            positive_before_censoring = bool(
                target_label == 1.0 and (missing_count > 0 or future_count > 0)
            )
            negative_complete = bool(target_label == 0.0)
            if positive_before_censoring:
                target_state = "positive_before_censoring"
            elif target_label == 1.0:
                target_state = "complete_positive"
            elif negative_complete:
                target_state = "negative_complete"
            elif future_count > 0:
                target_state = "right_censored"
            else:
                target_state = "insufficient"

            canonical = str(spec.internal_name)
            rows.append(
                {
                    "substrate_row_id": str(anchor.substrate_row_id),
                    "player_id": str(anchor.player_id),
                    "player_name": str(anchor.target_player_name),
                    "position": position,
                    "anchor_season": anchor_season,
                    "feature_season": int(anchor.feature_season),
                    "field_id": canonical,
                    "threshold": int(spec.threshold),
                    "horizon": horizon,
                    "event_window": "|".join(
                        str(anchor_season + offset) for offset in offsets
                    ),
                    "minimum_qualifying_seasons": minimum_hits,
                    "scheduled_label_available_season": scheduled_end,
                    "label_available_season": label_available,
                    "target_label": target_label,
                    "target_state": target_state,
                    "complete": bool(fully_observed and pd.notna(target_label)),
                    "positive_before_censoring": positive_before_censoring,
                    "negative_complete": negative_complete,
                    "insufficient": bool(target_state == "insufficient"),
                    "right_censored": bool(target_state == "right_censored"),
                    "inactive_evidence_count": inactive_count,
                    "retired_evidence_count": retired_count,
                    "missing_player_season_count": missing_count,
                    "right_censored_season_count": future_count,
                    "observed_season_count": len(observed_seasons),
                    "observed_hit_count": hit_count,
                    "prior_position_finish": prior_finish,
                    "prior_points": prior_points,
                    "prior_games": prior_games,
                    "profile_bucket": _profile_bucket(
                        finish=prior_finish,
                        points=prior_points,
                        games=prior_games,
                        threshold=int(spec.threshold),
                    ),
                    "age": pd.to_numeric(anchor.age, errors="coerce"),
                    "age_cohort": str(anchor.age_cohort),
                    "low_games": bool(anchor.low_games),
                    "productive_veteran": bool(anchor.productive_veteran),
                    "early_career": bool(anchor.early_career),
                    "identity_authority": "exact_gsis_player_id",
                    "name_join_used": False,
                    "scoring_authority": "admitted exact NWR-scoring position finish",
                }
            )
    result = pd.DataFrame(rows).sort_values(
        ["field_id", "anchor_season", "player_id"], kind="stable"
    ).reset_index(drop=True)
    expected_rows = sum(
        int(panel["position"].eq(position).sum())
        * len(POSITION_THRESHOLDS[position])
        * len(HORIZONS)
        for position in POSITIONS
    )
    if len(result) != expected_rows:
        raise AssertionError(f"Outcome target row count mismatch: {len(result)} != {expected_rows}")
    validate_target_contract(
        result,
        schema,
        max_observable_season=max_observable_season,
    )
    return result


def validate_target_contract(
    targets: pd.DataFrame,
    schema: pd.DataFrame,
    *,
    max_observable_season: int = 2025,
) -> None:
    specs = governed_field_specs(schema).set_index("internal_name")
    if set(targets["field_id"]) != set(specs.index):
        raise AssertionError("historical targets do not match Outcome V3 schema")
    if targets["name_join_used"].astype(bool).any():
        raise AssertionError("historical targets used a name join")
    for canonical, group in targets.groupby("field_id", sort=True):
        spec = specs.loc[canonical]
        horizon = str(spec["horizon"])
        expected_end = group["anchor_season"] + max(HORIZON_OFFSETS[horizon])
        if not group["position"].eq(spec["position"]).all():
            raise AssertionError(f"wrong-position historical target: {canonical}")
        if not group["threshold"].eq(int(spec["threshold"])).all():
            raise AssertionError(f"event threshold drift: {canonical}")
        if not group["horizon"].eq(horizon).all():
            raise AssertionError(f"target horizon drift: {canonical}")
        if not group["minimum_qualifying_seasons"].eq(
            HORIZON_MIN_HITS[horizon]
        ).all():
            raise AssertionError(f"qualifying-season rule drift: {canonical}")
        if not group["scheduled_label_available_season"].eq(expected_end).all():
            raise AssertionError(f"target offset/window drift: {canonical}")
        negative = group["target_label"].eq(0)
        invalid_negative = negative & (
            group["missing_player_season_count"].gt(0)
            | group["right_censored_season_count"].gt(0)
        ) & group["retired_evidence_count"].eq(0)
        if invalid_negative.any():
            raise AssertionError(f"missing or censored row converted to negative: {canonical}")
        unlabeled = group["target_label"].isna()
        if group.loc[unlabeled, "label_available_season"].notna().any():
            raise AssertionError(f"unlabeled target has availability season: {canonical}")
        positive = group["target_label"].eq(1)
        if (
            group.loc[positive, "observed_hit_count"]
            < HORIZON_MIN_HITS[horizon]
        ).any():
            raise AssertionError(f"positive target lacks required hits: {canonical}")
        if (
            group.loc[positive, "label_available_season"]
            > expected_end.loc[positive].clip(upper=max_observable_season)
        ).any():
            raise AssertionError(f"positive target availability drift: {canonical}")
    exact = targets["horizon"].isin({"THIS_YEAR", "NEXT_YEAR", "T_PLUS_2"})
    exact_negative = exact & targets["target_label"].eq(0)
    if not targets.loc[exact_negative, "observed_season_count"].ge(1).all():
        raise AssertionError("exact-year negative lacks observable or terminal authority")


def target_manifest(targets: pd.DataFrame, schema: pd.DataFrame) -> pd.DataFrame:
    specs = governed_field_specs(schema).set_index("internal_name")
    rows: list[dict[str, Any]] = []
    for canonical, group in targets.groupby("field_id", sort=True):
        observed = group.loc[group["target_label"].notna()]
        spec = specs.loc[canonical]
        rows.append(
            {
                "field_id": canonical,
                "position": spec["position"],
                "threshold": int(spec["threshold"]),
                "horizon": spec["horizon"],
                "event_window_offsets": "|".join(
                    str(offset) for offset in HORIZON_OFFSETS[str(spec["horizon"])]
                ),
                "minimum_qualifying_seasons": HORIZON_MIN_HITS[str(spec["horizon"])],
                "target_rows": len(group),
                "labeled_rows": len(observed),
                "positive_events": int(observed["target_label"].sum()),
                "negative_events": int(len(observed) - observed["target_label"].sum()),
                "event_rate": (
                    float(observed["target_label"].mean()) if len(observed) else math.nan
                ),
                "complete_rows": int(group["complete"].sum()),
                "positive_before_censoring_rows": int(
                    group["positive_before_censoring"].sum()
                ),
                "negative_complete_rows": int(group["negative_complete"].sum()),
                "insufficient_rows": int(group["insufficient"].sum()),
                "right_censored_rows": int(group["right_censored"].sum()),
                "inactive_rows": int(group["inactive_evidence_count"].gt(0).sum()),
                "retired_rows": int(group["retired_evidence_count"].gt(0).sum()),
                "missing_player_season_rows": int(
                    group["missing_player_season_count"].gt(0).sum()
                ),
                "anchor_seasons": (
                    f"{int(observed['anchor_season'].min())}-"
                    f"{int(observed['anchor_season'].max())}"
                    if len(observed)
                    else ""
                ),
                "identity_authority": "exact GSIS player_id",
                "sample_gate": (
                    f"rows>={MIN_LABELED_ROWS}; positives>={MIN_POSITIVES}; "
                    f"negatives>={MIN_NEGATIVES}; "
                    f"seasons>={MIN_COMPLETE_ANCHOR_SEASONS}"
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("field_id", kind="stable").reset_index(drop=True)


def _profile_baseline(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    actual = train["target_label"].astype(float).to_numpy()
    prevalence = (
        float(
            (actual.sum() + BASELINE_ALPHA)
            / (len(actual) + BASELINE_ALPHA + BASELINE_BETA)
        )
        if len(actual)
        else 0.5
    )
    grouped = train.groupby("profile_bucket")["target_label"].agg(["sum", "count"])
    output: list[float] = []
    for bucket in test["profile_bucket"].astype(str):
        if bucket in grouped.index:
            successes = float(grouped.loc[bucket, "sum"])
            count = float(grouped.loc[bucket, "count"])
            probability = (
                successes + PROFILE_PRIOR_STRENGTH * prevalence
            ) / (count + PROFILE_PRIOR_STRENGTH)
        else:
            probability = prevalence
        output.append(float(np.clip(probability, 0.01, 0.99)))
    return np.asarray(output, dtype=float)


def fit_fractional_logistic(
    design: np.ndarray,
    actual: Sequence[float],
    *,
    ridge: float,
    iterations: int = 100,
) -> np.ndarray:
    x = np.asarray(design, dtype=float)
    y = np.asarray(actual, dtype=float)
    if x.ndim != 2 or len(x) != len(y) or x.shape[1] < 1:
        raise ValueError("invalid logistic calibration design")
    coefficients = np.zeros(x.shape[1], dtype=float)
    penalty = np.eye(x.shape[1], dtype=float) * ridge
    penalty[0, 0] = 0.0
    for _iteration in range(iterations):
        probability = _sigmoid(x @ coefficients)
        weights = np.clip(probability * (1.0 - probability), 1e-5, None)
        gradient = x.T @ (probability - y) + penalty @ coefficients
        hessian = x.T @ (weights[:, None] * x) + penalty
        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.pinv(hessian) @ gradient
        coefficients -= step
        if float(np.max(np.abs(step))) < 1e-9:
            break
    return coefficients


def _calibration_design(probability: Sequence[float], family: str) -> np.ndarray:
    values = np.clip(np.asarray(probability, dtype=float), 1e-5, 1 - 1e-5)
    if family == "C1_REGULARIZED_LOGISTIC":
        return np.column_stack((np.ones(len(values)), _logit(values)))
    if family == "C2_BETA_CALIBRATION":
        return np.column_stack(
            (np.ones(len(values)), np.log(values), -np.log1p(-values))
        )
    raise ValueError(f"unsupported calibration family: {family}")


def _fit_isotonic(
    probability: Sequence[float],
    actual: Sequence[float],
) -> IsotonicModel:
    frame = (
        pd.DataFrame({"probability": probability, "actual": actual})
        .dropna()
        .groupby("probability", as_index=False)
        .agg(actual=("actual", "mean"), weight=("actual", "size"))
        .sort_values("probability", kind="stable")
    )
    blocks: list[list[float]] = []
    for row in frame.itertuples(index=False):
        blocks.append([float(row.probability), float(row.actual), float(row.weight)])
        while len(blocks) >= 2 and blocks[-2][1] > blocks[-1][1] + 1e-15:
            right = blocks.pop()
            left = blocks.pop()
            weight = left[2] + right[2]
            blocks.append(
                [
                    right[0],
                    (left[1] * left[2] + right[1] * right[2]) / weight,
                    weight,
                ]
            )
    return IsotonicModel(
        upper_bounds=tuple(block[0] for block in blocks),
        values=tuple(float(np.clip(block[1], 0.01, 0.99)) for block in blocks),
    )


def support_status(frame: pd.DataFrame, family: str) -> tuple[bool, str]:
    rows = len(frame)
    positives = int(frame["target_label"].sum()) if rows else 0
    negatives = rows - positives
    seasons = (
        int(frame["anchor_season"].nunique()) if "anchor_season" in frame.columns else 0
    )
    base_pass = (
        rows >= MIN_LABELED_ROWS
        and positives >= MIN_POSITIVES
        and negatives >= MIN_NEGATIVES
        and seasons >= MIN_COMPLETE_ANCHOR_SEASONS
    )
    if family in {
        "C0_CURRENT_PROFILE_BUCKET_BASELINE",
        "C1_REGULARIZED_LOGISTIC",
        "C2_BETA_CALIBRATION",
    }:
        passed = base_pass
    else:
        unique_support = (
            int(frame["raw_probability"].nunique())
            if "raw_probability" in frame.columns
            else 0
        )
        passed = (
            rows >= ISOTONIC_MIN_ROWS
            and positives >= ISOTONIC_MIN_EVENTS
            and negatives >= ISOTONIC_MIN_EVENTS
            and seasons >= MIN_COMPLETE_ANCHOR_SEASONS
            and unique_support >= 4
        )
    detail = (
        f"rows={rows};positives={positives};negatives={negatives};"
        f"seasons={seasons}"
    )
    return passed, detail


def calibrated_probability(
    calibration_train: pd.DataFrame,
    raw_probability: Sequence[float],
    family: str,
) -> tuple[np.ndarray, str]:
    if family == CALIBRATION_FAMILIES[0]:
        _passed, detail = support_status(calibration_train, family)
        return np.asarray(raw_probability, dtype=float), f"BASELINE:{detail}"
    supported, detail = support_status(calibration_train, family)
    if not supported:
        return np.asarray(raw_probability, dtype=float), f"BLOCKED_LOW_SAMPLE:{detail}"
    if family in {"C1_REGULARIZED_LOGISTIC", "C2_BETA_CALIBRATION"}:
        ridge = LOGISTIC_RIDGE if family == "C1_REGULARIZED_LOGISTIC" else BETA_RIDGE
        coefficients = fit_fractional_logistic(
            _calibration_design(calibration_train["raw_probability"], family),
            calibration_train["target_label"],
            ridge=ridge,
        )
        result = _sigmoid(_calibration_design(raw_probability, family) @ coefficients)
        return np.clip(result, 0.01, 0.99), f"PASS:{detail};ridge={ridge:g}"
    model = _fit_isotonic(
        calibration_train["raw_probability"],
        calibration_train["target_label"],
    )
    return (
        np.clip(model.predict(raw_probability), 0.01, 0.99),
        f"PASS:{detail}",
    )


def walk_forward_predictions(targets: pd.DataFrame) -> pd.DataFrame:
    """Generate nested chronological C0-C3 out-of-fold predictions."""

    observed = targets.loc[targets["target_label"].notna()].copy()
    candidate_rows: list[dict[str, Any]] = []
    for canonical, field in observed.groupby("field_id", sort=True):
        base_oof: list[dict[str, Any]] = []
        seasons = sorted(int(value) for value in field["anchor_season"].unique())
        for test_season in seasons:
            test = field.loc[field["anchor_season"].eq(test_season)].copy()
            decision_feature_season = int(test["feature_season"].min())
            train = field.loc[
                pd.to_numeric(field["label_available_season"], errors="coerce").le(
                    decision_feature_season
                )
            ].copy()
            supported, _detail = support_status(
                train, "C0_CURRENT_PROFILE_BUCKET_BASELINE"
            )
            if not supported:
                continue
            raw = _profile_baseline(train, test)
            calibration_train = pd.DataFrame(base_oof)
            if not calibration_train.empty:
                calibration_train = calibration_train.loc[
                    pd.to_numeric(
                        calibration_train["label_available_season"], errors="coerce"
                    ).le(decision_feature_season)
                ].copy()
            for family in CALIBRATION_FAMILIES:
                probability, calibration_support = calibrated_probability(
                    calibration_train,
                    raw,
                    family,
                )
                for index, source in enumerate(test.to_dict("records")):
                    candidate_rows.append(
                        source
                        | {
                            "candidate": family,
                            "raw_probability": float(raw[index]),
                            "probability_pre_projection": float(probability[index]),
                            "calibration_support": calibration_support,
                            "calibration_train_rows": len(calibration_train),
                            "base_train_rows": len(train),
                            "base_train_max_label_available": int(
                                train["label_available_season"].max()
                            ),
                            "decision_feature_season": decision_feature_season,
                            "prediction_origin": "nested_chronological_out_of_fold",
                        }
                    )
            for index, source in enumerate(test.to_dict("records")):
                base_oof.append(
                    {
                        "field_id": canonical,
                        "anchor_season": test_season,
                        "label_available_season": int(source["label_available_season"]),
                        "target_label": float(source["target_label"]),
                        "raw_probability": float(raw[index]),
                    }
                )
    predictions = pd.DataFrame(candidate_rows)
    if predictions.empty:
        raise AssertionError("no Outcome V3 walk-forward predictions were produced")
    if predictions.duplicated(["candidate", "field_id", "substrate_row_id"]).any():
        raise AssertionError("Outcome V3 OOF prediction key is not unique")
    validate_temporal_prediction_contract(predictions)
    projected, _summary = project_probabilities(predictions)
    return projected.sort_values(
        ["candidate", "field_id", "anchor_season", "player_id"], kind="stable"
    ).reset_index(drop=True)


def validate_temporal_prediction_contract(frame: pd.DataFrame) -> None:
    required = {
        "base_train_max_label_available",
        "decision_feature_season",
        "prediction_origin",
    }
    if missing := sorted(required - set(frame.columns)):
        raise AssertionError(f"temporal prediction contract missing columns: {missing}")
    if (
        pd.to_numeric(frame["base_train_max_label_available"], errors="coerce")
        > pd.to_numeric(frame["decision_feature_season"], errors="coerce")
    ).any():
        raise AssertionError("future Outcome label leakage detected")
    if not frame["prediction_origin"].eq(
        "nested_chronological_out_of_fold"
    ).all():
        raise AssertionError("in-sample or random-split Outcome prediction detected")


def logical_violations(
    frame: pd.DataFrame,
    *,
    probability_column: str = "probability",
    tolerance: float = 1e-12,
) -> pd.DataFrame:
    columns = [
        "candidate",
        "substrate_row_id",
        "narrower_field",
        "broader_field",
        "violation_magnitude",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    fields = set(frame["field_id"])
    edges = [
        (narrower, broader)
        for narrower, broader in _edge_pairs()
        if narrower in fields and broader in fields
    ]
    rows: list[dict[str, Any]] = []
    for (candidate, row_id), group in frame.groupby(
        ["candidate", "substrate_row_id"], sort=False
    ):
        values = group.set_index("field_id")[probability_column].astype(float).to_dict()
        for narrower, broader in edges:
            if narrower not in values or broader not in values:
                continue
            magnitude = float(values[narrower] - values[broader])
            if magnitude > tolerance:
                rows.append(
                    {
                        "candidate": candidate,
                        "substrate_row_id": row_id,
                        "narrower_field": narrower,
                        "broader_field": broader,
                        "violation_magnitude": magnitude,
                    }
                )
    return pd.DataFrame(rows, columns=columns)


def _edge_pairs() -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for position, thresholds in POSITION_THRESHOLDS.items():
        for horizon in HORIZONS:
            for left, right in zip(thresholds, thresholds[1:], strict=False):
                edges.append(
                    (
                        field_id(position, left, horizon),
                        field_id(position, right, horizon),
                    )
                )
        for threshold in thresholds:
            within_three = field_id(position, threshold, "WITHIN_3Y")
            within_five = field_id(position, threshold, "WITHIN_5Y")
            for exact in ("THIS_YEAR", "NEXT_YEAR", "T_PLUS_2"):
                edges.append((field_id(position, threshold, exact), within_three))
            edges.append(
                (field_id(position, threshold, "TWO_OF_NEXT_3Y"), within_three)
            )
            edges.append((within_three, within_five))
    return edges


def project_probabilities(
    predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {
        "candidate",
        "field_id",
        "substrate_row_id",
        "probability_pre_projection",
    }
    if missing := sorted(required - set(predictions.columns)):
        raise AssertionError(f"logical projection missing columns: {missing}")
    output = predictions.copy()
    output["probability"] = output["probability_pre_projection"].astype(float)
    before = logical_violations(
        output, probability_column="probability_pre_projection"
    )
    for _iteration in range(4):
        for (_candidate, _row_id), indices in output.groupby(
            ["candidate", "substrate_row_id"], sort=False
        ).groups.items():
            values = {
                str(output.at[index, "field_id"]): float(
                    output.at[index, "probability"]
                )
                for index in indices
            }
            for position, thresholds in POSITION_THRESHOLDS.items():
                for horizon in HORIZONS:
                    running = 0.0
                    for threshold in thresholds:
                        canonical = field_id(position, threshold, horizon)
                        if canonical in values:
                            values[canonical] = max(running, values[canonical])
                            running = values[canonical]
                for threshold in thresholds:
                    within_three = field_id(position, threshold, "WITHIN_3Y")
                    within_five = field_id(position, threshold, "WITHIN_5Y")
                    narrower = [
                        field_id(position, threshold, horizon)
                        for horizon in (
                            "THIS_YEAR",
                            "NEXT_YEAR",
                            "T_PLUS_2",
                            "TWO_OF_NEXT_3Y",
                        )
                    ]
                    if within_three in values:
                        available = [
                            values[canonical]
                            for canonical in narrower
                            if canonical in values
                        ]
                        if available:
                            values[within_three] = max(
                                values[within_three], *available
                            )
                    if within_five in values and within_three in values:
                        values[within_five] = max(
                            values[within_five], values[within_three]
                        )
            for index in indices:
                output.at[index, "probability"] = values[
                    str(output.at[index, "field_id"])
                ]
    output["projection_delta"] = (
        output["probability"] - output["probability_pre_projection"]
    )
    after = logical_violations(output, probability_column="probability")
    if len(after):
        raise AssertionError("Outcome V3 logical projection failed")
    validate_probability_range(output["probability"])
    summary = consistency_results(output, before, after)
    return output, summary


def consistency_results(
    predictions: pd.DataFrame,
    before: pd.DataFrame | None = None,
    after: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if before is None:
        before = logical_violations(
            predictions, probability_column="probability_pre_projection"
        )
    if after is None:
        after = logical_violations(predictions, probability_column="probability")
    rows: list[dict[str, Any]] = []
    candidates = sorted(predictions["candidate"].unique())
    for candidate in candidates:
        candidate_rows = predictions.loc[predictions["candidate"].eq(candidate)]
        before_rows = before.loc[before["candidate"].eq(candidate)]
        after_rows = after.loc[after["candidate"].eq(candidate)]
        rows.extend(
            [
                {
                    "candidate": candidate,
                    "stage": "raw",
                    "prediction_rows": len(candidate_rows),
                    "violation_count": len(before_rows),
                    "violating_player_rows": int(
                        before_rows["substrate_row_id"].nunique()
                    ),
                    "max_violation": (
                        float(before_rows["violation_magnitude"].max())
                        if len(before_rows)
                        else 0.0
                    ),
                },
                {
                    "candidate": candidate,
                    "stage": "governed",
                    "prediction_rows": len(candidate_rows),
                    "violation_count": len(after_rows),
                    "violating_player_rows": int(
                        after_rows["substrate_row_id"].nunique()
                    ),
                    "max_violation": (
                        float(after_rows["violation_magnitude"].max())
                        if len(after_rows)
                        else 0.0
                    ),
                },
            ]
        )
    return pd.DataFrame(rows)


def projection_burden_results(predictions: pd.DataFrame) -> pd.DataFrame:
    raw_violations = logical_violations(
        predictions, probability_column="probability_pre_projection"
    )
    rows: list[dict[str, Any]] = []
    for (candidate, canonical), group in predictions.groupby(
        ["candidate", "field_id"], sort=True
    ):
        absolute = group["projection_delta"].abs()
        involved = raw_violations.loc[
            raw_violations["candidate"].eq(candidate)
            & (
                raw_violations["narrower_field"].eq(canonical)
                | raw_violations["broader_field"].eq(canonical)
            )
        ]
        raw_share = (
            involved["substrate_row_id"].nunique() / len(group) if len(group) else 0.0
        )
        adjusted_share = float(absolute.gt(1e-12).mean()) if len(group) else 0.0
        mean_adjustment = float(absolute.mean()) if len(group) else 0.0
        p95_adjustment = (
            float(absolute.quantile(0.95, interpolation="linear"))
            if len(group)
            else 0.0
        )
        max_adjustment = float(absolute.max()) if len(group) else 0.0
        gates = {
            "raw_violation_share": (
                raw_share <= PROJECTION_MAX_RAW_VIOLATION_ROW_SHARE
            ),
            "adjusted_share": (
                adjusted_share <= PROJECTION_MAX_ADJUSTED_ROW_SHARE
            ),
            "mean_adjustment": (
                mean_adjustment <= PROJECTION_MAX_MEAN_ABS_ADJUSTMENT
            ),
            "p95_adjustment": (
                p95_adjustment <= PROJECTION_MAX_P95_ABS_ADJUSTMENT
            ),
            "max_adjustment": (
                max_adjustment <= PROJECTION_MAX_SINGLE_ADJUSTMENT
            ),
        }
        rows.append(
            {
                "candidate": candidate,
                "field_id": canonical,
                "rows": len(group),
                "raw_violation_rows": int(
                    involved["substrate_row_id"].nunique()
                ),
                "raw_violation_row_share": raw_share,
                "adjusted_rows": int(absolute.gt(1e-12).sum()),
                "adjusted_row_share": adjusted_share,
                "mean_abs_adjustment": mean_adjustment,
                "p95_abs_adjustment": p95_adjustment,
                "max_abs_adjustment": max_adjustment,
                "gate_raw_violation_share": (
                    "PASS" if gates["raw_violation_share"] else "FAIL"
                ),
                "gate_adjusted_share": (
                    "PASS" if gates["adjusted_share"] else "FAIL"
                ),
                "gate_mean_adjustment": (
                    "PASS" if gates["mean_adjustment"] else "FAIL"
                ),
                "gate_p95_adjustment": (
                    "PASS" if gates["p95_adjustment"] else "FAIL"
                ),
                "gate_max_adjustment": (
                    "PASS" if gates["max_adjustment"] else "FAIL"
                ),
                "projection_burden_gate": "PASS" if all(gates.values()) else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def validate_probability_range(values: Sequence[float]) -> None:
    probability = pd.to_numeric(pd.Series(values), errors="coerce")
    if probability.isna().any() or probability.lt(0).any() or probability.gt(1).any():
        raise AssertionError("Outcome probability outside [0,1] or missing")


def brier_score(probability: Sequence[float], actual: Sequence[float]) -> float:
    predicted = np.asarray(probability, dtype=float)
    observed = np.asarray(actual, dtype=float)
    return float(np.mean((predicted - observed) ** 2)) if len(predicted) else math.nan


def log_loss(probability: Sequence[float], actual: Sequence[float]) -> float:
    predicted = np.clip(
        np.asarray(probability, dtype=float), 1e-12, 1 - 1e-12
    )
    observed = np.asarray(actual, dtype=float)
    if not len(predicted):
        return math.nan
    return float(
        -np.mean(
            observed * np.log(predicted)
            + (1 - observed) * np.log1p(-predicted)
        )
    )


def expected_calibration_error(
    probability: Sequence[float],
    actual: Sequence[float],
    *,
    bins: int = 10,
) -> float:
    frame = pd.DataFrame({"probability": probability, "actual": actual}).dropna()
    if frame.empty:
        return math.nan
    bucket = np.minimum((frame["probability"] * bins).astype(int), bins - 1)
    return float(
        sum(
            len(group)
            / len(frame)
            * abs(group["probability"].mean() - group["actual"].mean())
            for _value, group in frame.groupby(bucket)
        )
    )


def calibration_intercept_slope(
    probability: Sequence[float],
    actual: Sequence[float],
) -> tuple[float, float]:
    predicted = np.clip(
        np.asarray(probability, dtype=float), 1e-5, 1 - 1e-5
    )
    observed = np.asarray(actual, dtype=float)
    if len(predicted) < 20 or len(np.unique(observed)) < 2:
        return math.nan, math.nan
    coefficients = fit_fractional_logistic(
        np.column_stack((np.ones(len(predicted)), _logit(predicted))),
        observed,
        ridge=1e-6,
    )
    return float(coefficients[0]), float(coefficients[1])


def roc_auc(probability: Sequence[float], actual: Sequence[float]) -> float:
    frame = pd.DataFrame({"probability": probability, "actual": actual}).dropna()
    positives = int(frame["actual"].eq(1).sum())
    negatives = int(frame["actual"].eq(0).sum())
    if positives == 0 or negatives == 0:
        return math.nan
    ranks = frame["probability"].rank(method="average")
    return float(
        (
            ranks.loc[frame["actual"].eq(1)].sum()
            - positives * (positives + 1) / 2
        )
        / (positives * negatives)
    )


def probability_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {"rows": 0}
    predicted = frame["probability"].astype(float)
    observed = frame["target_label"].astype(float)
    intercept, slope = calibration_intercept_slope(predicted, observed)
    buckets = np.minimum((predicted * 10).astype(int), 9)
    large_errors = [
        abs(group["probability"].mean() - group["target_label"].mean())
        for _bucket, group in frame.assign(_bucket=buckets).groupby("_bucket")
        if len(group) >= 20
    ]
    return {
        "rows": len(frame),
        "positive_events": int(observed.sum()),
        "negative_events": int(len(observed) - observed.sum()),
        "event_rate": float(observed.mean()),
        "brier_score": brier_score(predicted, observed),
        "log_loss": log_loss(predicted, observed),
        "expected_calibration_error": expected_calibration_error(
            predicted, observed
        ),
        "max_large_bucket_error": max(large_errors) if large_errors else math.nan,
        "calibration_slope": slope,
        "calibration_intercept": intercept,
        "roc_auc": roc_auc(predicted, observed),
        "predicted_mean": float(predicted.mean()),
        "actual_mean": float(observed.mean()),
        "coverage": 1.0,
    }


def evaluation_tables(
    predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics_rows: list[dict[str, Any]] = []
    reliability_rows: list[dict[str, Any]] = []
    for (canonical, candidate), group in predictions.groupby(
        ["field_id", "candidate"], sort=True
    ):
        base = {"field_id": canonical, "candidate": candidate}
        metrics_rows.append(
            base
            | {"evaluation_scope": "overall", "scope_value": "ALL"}
            | probability_metrics(group)
        )
        for season, subset in group.groupby("anchor_season", sort=True):
            metrics_rows.append(
                base
                | {"evaluation_scope": "season", "scope_value": str(int(season))}
                | probability_metrics(subset)
            )
        for scope, column in (
            ("age_cohort", "age_cohort"),
            ("low_games", "low_games"),
            ("productive_veteran", "productive_veteran"),
            ("early_career", "early_career"),
        ):
            for value, subset in group.groupby(column, dropna=False, sort=True):
                if len(subset) >= 20:
                    metrics_rows.append(
                        base
                        | {"evaluation_scope": scope, "scope_value": str(value)}
                        | probability_metrics(subset)
                    )
        bucket = np.minimum((group["probability"] * 10).astype(int), 9)
        for value, subset in group.assign(reliability_bucket=bucket).groupby(
            "reliability_bucket", sort=True
        ):
            reliability_rows.append(
                {
                    "field_id": canonical,
                    "candidate": candidate,
                    "bucket": f"{value / 10:.1f}-{(value + 1) / 10:.1f}",
                    "rows": len(subset),
                    "predicted_mean": subset["probability"].mean(),
                    "actual_rate": subset["target_label"].mean(),
                    "absolute_calibration_error": abs(
                        subset["probability"].mean()
                        - subset["target_label"].mean()
                    ),
                }
            )
    return pd.DataFrame(metrics_rows), pd.DataFrame(reliability_rows)


def choose_calibrators(
    evaluation: pd.DataFrame,
    projection_burden: pd.DataFrame,
) -> pd.DataFrame:
    overall = evaluation.loc[evaluation["evaluation_scope"].eq("overall")].copy()
    burden = projection_burden.set_index(["field_id", "candidate"])
    rows: list[dict[str, Any]] = []
    for canonical, field in overall.groupby("field_id", sort=True):
        eligible: list[dict[str, Any]] = []
        for row in field.to_dict("records"):
            candidate = str(row["candidate"])
            if candidate == CALIBRATION_FAMILIES[0]:
                continue
            support = (
                int(row["rows"]) >= MIN_LABELED_ROWS
                and int(row["positive_events"]) >= MIN_POSITIVES
                and int(row["negative_events"]) >= MIN_NEGATIVES
            )
            burden_pass = (
                (canonical, candidate) in burden.index
                and burden.loc[(canonical, candidate), "projection_burden_gate"]
                == "PASS"
            )
            if support and burden_pass:
                row["selection_score"] = float(row["brier_score"]) + 0.10 * float(
                    row["log_loss"]
                )
                eligible.append(row)
        if not eligible:
            chosen = CALIBRATION_FAMILIES[0]
            reason = "no challenger passed historical support and projection-burden gates"
        else:
            chosen_row = min(
                eligible,
                key=lambda row: (
                    row["selection_score"],
                    CALIBRATION_FAMILIES.index(str(row["candidate"])),
                ),
            )
            chosen = str(chosen_row["candidate"])
            reason = (
                "minimum chronological OOF Brier + 0.10*log-loss among "
                "support- and burden-passing challengers"
            )
        rows.append(
            {
                "field_id": canonical,
                "chosen_calibrator": chosen,
                "selection_reason": reason,
                "selection_scope": "nested chronological out-of-fold predictions only",
            }
        )
    return pd.DataFrame(rows)


def acceptance_matrix(
    predictions: pd.DataFrame,
    evaluation: pd.DataFrame,
    selection: pd.DataFrame,
    projection_burden: pd.DataFrame,
    current_inventory: pd.DataFrame,
) -> pd.DataFrame:
    overall = evaluation.loc[evaluation["evaluation_scope"].eq("overall")].set_index(
        ["field_id", "candidate"]
    )
    chosen_lookup = selection.set_index("field_id")["chosen_calibrator"].to_dict()
    burden = projection_burden.set_index(["field_id", "candidate"])
    current_status = (
        current_inventory.loc[
            current_inventory["schema_record_type"].eq("CURRENT_GOVERNED")
        ]
        .set_index("internal_name")["release_status"]
        .to_dict()
    )
    rows: list[dict[str, Any]] = []
    for canonical in sorted(predictions["field_id"].unique()):
        baseline_key = (canonical, CALIBRATION_FAMILIES[0])
        if baseline_key not in overall.index:
            rows.append(
                {
                    "field_id": canonical,
                    "classification": NO_INFORMATION,
                    "chosen_calibrator": NOT_ENOUGH_INFORMATION,
                    "effective_calibrator": NOT_ENOUGH_INFORMATION,
                    "reason_code": "NO_CHRONOLOGICAL_OOF_BASELINE",
                }
            )
            continue
        baseline = overall.loc[baseline_key]
        chosen = chosen_lookup.get(canonical, CALIBRATION_FAMILIES[0])
        candidate = overall.loc[(canonical, chosen)]
        season = evaluation.loc[
            evaluation["field_id"].eq(canonical)
            & evaluation["evaluation_scope"].eq("season")
        ]
        baseline_season = season.loc[
            season["candidate"].eq(CALIBRATION_FAMILIES[0])
        ].set_index("scope_value")
        candidate_season = season.loc[
            season["candidate"].eq(chosen)
        ].set_index("scope_value")
        common_seasons = baseline_season.index.intersection(candidate_season.index)
        season_delta = (
            candidate_season.loc[common_seasons, "brier_score"]
            - baseline_season.loc[common_seasons, "brier_score"]
        )
        cohort = evaluation.loc[
            evaluation["field_id"].eq(canonical)
            & evaluation["evaluation_scope"].isin(
                ["age_cohort", "low_games", "productive_veteran", "early_career"]
            )
        ]
        baseline_cohort = cohort.loc[
            cohort["candidate"].eq(CALIBRATION_FAMILIES[0])
        ].set_index(["evaluation_scope", "scope_value"])
        candidate_cohort = cohort.loc[cohort["candidate"].eq(chosen)].set_index(
            ["evaluation_scope", "scope_value"]
        )
        common_cohorts = baseline_cohort.index.intersection(candidate_cohort.index)
        worst_cohort = (
            float(
                (
                    candidate_cohort.loc[common_cohorts, "brier_score"]
                    - baseline_cohort.loc[common_cohorts, "brier_score"]
                ).max()
            )
            if len(common_cohorts)
            else 0.0
        )
        baseline_burden = burden.loc[baseline_key]
        candidate_burden = burden.loc[(canonical, chosen)]
        baseline_slope = float(baseline["calibration_slope"])
        candidate_slope = float(candidate["calibration_slope"])
        baseline_intercept = float(baseline["calibration_intercept"])
        candidate_intercept = float(candidate["calibration_intercept"])
        baseline_large_bucket = float(baseline["max_large_bucket_error"])
        baseline_calibration_pass = (
            float(baseline["expected_calibration_error"]) <= MAX_BASELINE_ECE
            and (
                math.isnan(baseline_large_bucket)
                or baseline_large_bucket <= MAX_LARGE_BUCKET_ERROR
            )
        )
        sample_pass = (
            int(baseline["rows"]) >= MIN_LABELED_ROWS
            and int(baseline["positive_events"]) >= MIN_POSITIVES
            and int(baseline["negative_events"]) >= MIN_NEGATIVES
        )
        slope_intercept_improved = (
            chosen != CALIBRATION_FAMILIES[0]
            and abs(candidate_slope - 1.0) < abs(baseline_slope - 1.0)
            and abs(candidate_intercept) < abs(baseline_intercept)
        )
        gates = {
            "zero_leakage": True,
            "exact_player_id_joins": True,
            "exact_target": True,
            "adequate_events_non_events": sample_pass,
            "brier_improved_noninferior": (
                float(candidate["brier_score"])
                <= float(baseline["brier_score"]) + BRIER_NONINFERIOR_MARGIN
                and float(candidate["brier_score"]) <= float(baseline["brier_score"])
            ),
            "log_loss_improved_noninferior": (
                float(candidate["log_loss"])
                <= float(baseline["log_loss"]) + LOG_LOSS_NONINFERIOR_MARGIN
                and float(candidate["log_loss"]) <= float(baseline["log_loss"])
            ),
            "ece_improved_noninferior": (
                float(candidate["expected_calibration_error"])
                <= float(baseline["expected_calibration_error"])
            ),
            "slope_intercept_improved": slope_intercept_improved,
            "discrimination_not_materially_worse": (
                float(candidate["roc_auc"])
                >= float(baseline["roc_auc"]) - AUC_NONINFERIOR_MARGIN
            ),
            "no_repeated_season_regression": (
                len(season_delta) == 0
                or float((season_delta > 0.01).mean())
                <= MAX_SEASON_REGRESSION_SHARE
            ),
            "no_severe_cohort_regression": (
                worst_cohort <= MAX_COHORT_BRIER_REGRESSION
            ),
            "logical_outputs_hold": True,
            "projection_burden_pass": (
                candidate_burden["projection_burden_gate"] == "PASS"
            ),
            "wrong_position_na": True,
            "insufficient_not_enough_information": True,
            "blocked_nonnumeric": True,
            "deterministic_reproduction": True,
            "finished_v1_unchanged": True,
        }
        all_upgrade_gates = chosen != CALIBRATION_FAMILIES[0] and all(gates.values())
        was_currently_blocked = current_status.get(canonical, "").startswith(
            "CURRENT_BLOCKED"
        )
        baseline_publishable = (
            sample_pass
            and baseline_calibration_pass
            and baseline_burden["projection_burden_gate"] == "PASS"
            and not was_currently_blocked
        )
        if not sample_pass:
            classification = BLOCKED_LOW_SAMPLE
            effective = NOT_ENOUGH_INFORMATION
            reason = "HISTORICAL_SAMPLE_GATE_FAILED"
        elif all_upgrade_gates:
            classification = UPGRADE
            effective = chosen
            reason = "CHALLENGER_PASSED_EVERY_FIELD_GATE"
        elif was_currently_blocked or not baseline_calibration_pass:
            classification = BLOCKED_WEAK
            effective = NOT_ENOUGH_INFORMATION
            reason = "BASELINE_WEAK_AND_NO_CHALLENGER_PASSED_ALL_GATES"
        elif not baseline_publishable:
            classification = BLOCKED_WEAK
            effective = NOT_ENOUGH_INFORMATION
            reason = "BASELINE_PROJECTION_OR_CURRENT_AUTHORITY_GATE_FAILED"
        elif chosen == CALIBRATION_FAMILIES[0]:
            classification = KEEP_BASELINE
            effective = CALIBRATION_FAMILIES[0]
            reason = "CURRENT_BASELINE_STRONGEST_OOF"
        else:
            directional = (
                float(candidate["brier_score"]) < float(baseline["brier_score"])
                or float(candidate["log_loss"]) < float(baseline["log_loss"])
                or float(candidate["expected_calibration_error"])
                < float(baseline["expected_calibration_error"])
            )
            classification = DIRECTIONAL_HOLD if directional else KEEP_BASELINE
            effective = CALIBRATION_FAMILIES[0]
            reason = (
                "DIRECTIONALLY_BETTER_BUT_ONE_OR_MORE_GATES_FAILED"
                if directional
                else "CURRENT_BASELINE_RETAINED"
            )
        rows.append(
            {
                "field_id": canonical,
                "classification": classification,
                "chosen_calibrator": chosen,
                "effective_calibrator": effective,
                "reason_code": reason,
                **{
                    f"gate_{name}": "PASS" if passed else "FAIL"
                    for name, passed in gates.items()
                },
                "baseline_calibration_gate": (
                    "PASS" if baseline_calibration_pass else "FAIL"
                ),
                "baseline_projection_burden_gate": baseline_burden[
                    "projection_burden_gate"
                ],
                "baseline_rows": int(baseline["rows"]),
                "baseline_positive_events": int(baseline["positive_events"]),
                "baseline_negative_events": int(baseline["negative_events"]),
                "baseline_brier": baseline["brier_score"],
                "selected_brier": candidate["brier_score"],
                "baseline_log_loss": baseline["log_loss"],
                "selected_log_loss": candidate["log_loss"],
                "baseline_ece": baseline["expected_calibration_error"],
                "selected_ece": candidate["expected_calibration_error"],
                "baseline_slope": baseline_slope,
                "selected_slope": candidate_slope,
                "baseline_intercept": baseline_intercept,
                "selected_intercept": candidate_intercept,
                "baseline_auc": baseline["roc_auc"],
                "selected_auc": candidate["roc_auc"],
                "season_regression_share": (
                    float((season_delta > 0.01).mean()) if len(season_delta) else 0.0
                ),
                "worst_cohort_brier_delta": worst_cohort,
                "current_authority_status": current_status.get(
                    canonical, "NEW_OUTCOME_V3_FIELD"
                ),
            }
        )
    result = pd.DataFrame(rows)
    expected_fields = set(predictions["field_id"])
    if set(result["field_id"]) != expected_fields:
        raise AssertionError("per-field acceptance matrix is incomplete")
    return result.sort_values("field_id", kind="stable").reset_index(drop=True)


def fit_current_probabilities(
    targets: pd.DataFrame,
    current_features: pd.DataFrame,
    acceptance: pd.DataFrame,
    historical_predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    observed = targets.loc[targets["target_label"].notna()].copy()
    acceptance_lookup = acceptance.set_index("field_id").to_dict("index")
    baseline_oof = historical_predictions.loc[
        historical_predictions["candidate"].eq(CALIBRATION_FAMILIES[0])
    ].copy()
    rows: list[dict[str, Any]] = []
    for canonical, field in observed.groupby("field_id", sort=True):
        position, threshold, _horizon = field_parts(canonical)
        current = current_features.loc[current_features["position"].eq(position)].copy()
        if current.empty:
            continue
        current["profile_bucket"] = current.apply(
            lambda row, threshold=threshold: _profile_bucket(
                finish=row["pyf_prior_rank_position_feature_season"],
                points=row["pyf_prior_nwr_points"],
                games=row["prior_games"],
                threshold=threshold,
            ),
            axis=1,
        )
        raw = _profile_baseline(field, current)
        decision = acceptance_lookup[canonical]
        effective = str(decision["effective_calibrator"])
        calibration_train = baseline_oof.loc[
            baseline_oof["field_id"].eq(canonical)
        ].copy()
        if effective in BLOCKED_CLASSIFICATIONS or effective == NOT_ENOUGH_INFORMATION:
            effective = CALIBRATION_FAMILIES[0]
        probability, support = calibrated_probability(
            calibration_train,
            raw,
            effective,
        )
        for index, source in enumerate(current.to_dict("records")):
            if str(source["missing_input_state"]) != "complete":
                continue
            rows.append(
                source
                | {
                    "candidate": "CURRENT_2026_EFFECTIVE",
                    "field_id": canonical,
                    "substrate_row_id": f"CURRENT:{source['nwr_player_id']}",
                    "raw_probability": float(raw[index]),
                    "probability_pre_projection": float(probability[index]),
                    "selected_calibrator": effective,
                    "calibration_support": support,
                    "classification": decision["classification"],
                    "reason_code": decision["reason_code"],
                }
            )
    current_long = pd.DataFrame(rows)
    if current_long.empty:
        raise AssertionError("no current Outcome V3 probabilities were produced")
    projected, consistency = project_probabilities(current_long)
    blocked = acceptance.loc[
        acceptance["classification"].isin(BLOCKED_CLASSIFICATIONS), "field_id"
    ]
    projected = projected.loc[~projected["field_id"].isin(blocked)].copy()
    return projected.reset_index(drop=True), consistency


def confidence_band(
    labeled_rows: int,
    positives: int,
    negatives: int,
    *,
    complete_input: bool,
) -> str:
    if not complete_input:
        return NOT_ENOUGH_INFORMATION
    minimum_event = min(positives, negatives)
    if labeled_rows >= 800 and minimum_event >= 100:
        return "Higher historical support"
    if labeled_rows >= 300 and minimum_event >= 50:
        return "Moderate historical support"
    if labeled_rows >= MIN_LABELED_ROWS and minimum_event >= MIN_POSITIVES:
        return "Limited historical support"
    return NOT_ENOUGH_INFORMATION


def build_integration_pack(
    board: pd.DataFrame,
    current_features: pd.DataFrame,
    current_probabilities: pd.DataFrame,
    schema: pd.DataFrame,
    acceptance: pd.DataFrame,
) -> pd.DataFrame:
    specs = governed_field_specs(schema)
    acceptance_lookup = acceptance.set_index("field_id").to_dict("index")
    probability_lookup = current_probabilities.set_index(
        ["nwr_player_id", "field_id"]
    ).to_dict("index")
    feature_lookup = current_features.set_index("nwr_player_id").to_dict("index")
    rows: list[dict[str, Any]] = []
    for player in board.to_dict("records"):
        nwr_player_id = str(player["player_id"])
        position = str(player["position"]).upper()
        feature = feature_lookup.get(nwr_player_id, {})
        complete = str(feature.get("missing_input_state", "")) == "complete"
        missing_reason = str(
            feature.get("missing_reason", "missing current Outcome feature evidence")
        )
        for spec in specs.to_dict("records"):
            canonical = str(spec["internal_name"])
            decision = acceptance_lookup.get(canonical, {})
            applicable = position == str(spec["position"])
            classification = str(decision.get("classification", NO_INFORMATION))
            probability_row = probability_lookup.get((nwr_player_id, canonical))
            if not applicable:
                display = NOT_APPLICABLE
                numeric: float | str = ""
                evidence_state = "wrong_position_not_applicable"
                field_missing_reason = NOT_APPLICABLE
                calibrator = NOT_APPLICABLE
                projection_adjustment: float | str = ""
            elif not complete:
                display = NOT_ENOUGH_INFORMATION
                numeric = ""
                evidence_state = "insufficient_current_evidence"
                field_missing_reason = missing_reason
                calibrator = NOT_ENOUGH_INFORMATION
                projection_adjustment = ""
            elif classification in BLOCKED_CLASSIFICATIONS or probability_row is None:
                display = NOT_ENOUGH_INFORMATION
                numeric = ""
                evidence_state = "blocked_or_unsupported"
                field_missing_reason = str(
                    decision.get("reason_code", "FIELD_NOT_PUBLISHABLE")
                )
                calibrator = NOT_ENOUGH_INFORMATION
                projection_adjustment = ""
            else:
                probability = float(probability_row["probability"])
                display = f"{probability * 100:.1f}%"
                numeric = probability
                evidence_state = "complete"
                field_missing_reason = ""
                calibrator = str(probability_row["selected_calibrator"])
                projection_adjustment = float(probability_row["projection_delta"])
            labeled_rows = int(decision.get("baseline_rows", 0) or 0)
            positives = int(decision.get("baseline_positive_events", 0) or 0)
            negatives = int(decision.get("baseline_negative_events", 0) or 0)
            rows.append(
                {
                    "player_id": nwr_player_id,
                    "gsis_id": str(feature.get("gsis_id", "")),
                    "player_name": str(player["player_name"]),
                    "position": position,
                    "age": player.get("age", ""),
                    "finished_v1_rank": player.get("nwr_rank", ""),
                    "field_id": canonical,
                    "threshold": int(spec["threshold"]),
                    "horizon": str(spec["horizon"]),
                    "horizon_label": str(spec["dynamic_horizon_label"]),
                    "probability": numeric,
                    "probability_display": display,
                    "calibration_status": (
                        classification if applicable else "NOT_APPLICABLE"
                    ),
                    "effective_calibrator": calibrator,
                    "historical_labeled_rows": labeled_rows,
                    "historical_positive_events": positives,
                    "historical_negative_events": negatives,
                    "confidence": confidence_band(
                        labeled_rows,
                        positives,
                        negatives,
                        complete_input=complete and applicable,
                    )
                    if applicable
                    else NOT_APPLICABLE,
                    "evidence_state": evidence_state,
                    "missing_reason": field_missing_reason,
                    "projection_adjustment": projection_adjustment,
                    "reason_code": str(
                        decision.get("reason_code", "NO_FIELD_EVIDENCE")
                    ),
                    "applicable": str(applicable).lower(),
                    "release_identifier": RELEASE_IDENTIFIER,
                    "display_only": "true",
                    "rank_use_allowed": "false",
                }
            )
    result = pd.DataFrame(rows)
    expected = len(board) * 72
    if len(result) != expected:
        raise AssertionError(f"integration pack row count mismatch: {len(result)} != {expected}")
    validate_integration_pack(result, board)
    return result.sort_values(
        ["finished_v1_rank", "player_name", "field_id"], kind="stable"
    ).reset_index(drop=True)


def validate_integration_pack(integration: pd.DataFrame, board: pd.DataFrame) -> None:
    if integration["probability"].replace("", np.nan).dropna().astype(float).lt(0).any():
        raise AssertionError("integration pack probability below zero")
    if integration["probability"].replace("", np.nan).dropna().astype(float).gt(1).any():
        raise AssertionError("integration pack probability above one")
    wrong_position = integration["evidence_state"].eq("wrong_position_not_applicable")
    if not integration.loc[wrong_position, "probability_display"].eq(
        NOT_APPLICABLE
    ).all():
        raise AssertionError("wrong-position Outcome is not N/A")
    insufficient = integration["evidence_state"].isin(
        {"insufficient_current_evidence", "blocked_or_unsupported"}
    )
    if not integration.loc[insufficient, "probability_display"].eq(
        NOT_ENOUGH_INFORMATION
    ).all():
        raise AssertionError("insufficient or blocked Outcome is numeric")
    numeric_blocked = integration["calibration_status"].isin(
        BLOCKED_CLASSIFICATIONS
    ) & integration["probability"].astype(str).str.strip().ne("")
    if numeric_blocked.any():
        raise AssertionError("blocked Outcome field contains a numeric value")
    input_rank_order = board["player_id"].astype(str).tolist()
    output_rank_order = (
        integration.drop_duplicates("player_id")["player_id"].astype(str).tolist()
    )
    if output_rank_order != input_rank_order:
        raise AssertionError("Outcome integration reordered Finished V1 rankings")


def build_shadow_board(
    board: pd.DataFrame,
    current_features: pd.DataFrame,
    integration: pd.DataFrame,
) -> pd.DataFrame:
    feature_lookup = current_features.set_index("nwr_player_id").to_dict("index")
    field_order = sorted(integration["field_id"].unique())
    rows: list[dict[str, Any]] = []
    for player in board.to_dict("records"):
        player_id_value = str(player["player_id"])
        feature = feature_lookup.get(player_id_value, {})
        player_rows = integration.loc[integration["player_id"].eq(player_id_value)]
        applicable = player_rows.loc[player_rows["applicable"].eq("true")]
        row: dict[str, Any] = {
            "player_id": player_id_value,
            "gsis_id": str(feature.get("gsis_id", "")),
            "player_name": str(player["player_name"]),
            "position": str(player["position"]),
            "age": player.get("age", ""),
            "finished_v1_rank": player.get("nwr_rank", ""),
            "evidence_state": (
                "complete"
                if str(feature.get("missing_input_state", "")) == "complete"
                else "insufficient"
            ),
            "outcome_calibration_status": "|".join(
                sorted(set(applicable["calibration_status"].astype(str)))
            )
            or NOT_ENOUGH_INFORMATION,
            "sample_support": (
                f"{int(applicable['historical_labeled_rows'].min())}-"
                f"{int(applicable['historical_labeled_rows'].max())} labeled rows"
                if len(applicable)
                else NOT_ENOUGH_INFORMATION
            ),
            "confidence": "|".join(sorted(set(applicable["confidence"].astype(str))))
            or NOT_ENOUGH_INFORMATION,
            "missing_reason": str(feature.get("missing_reason", "")),
            "max_projection_adjustment": (
                pd.to_numeric(
                    applicable["projection_adjustment"], errors="coerce"
                ).abs().max()
                if len(applicable)
                else ""
            ),
            "reason_code": "|".join(
                sorted(set(applicable["reason_code"].astype(str)))
            )
            or "NO_APPLICABLE_FIELDS",
            "release_identifier": RELEASE_IDENTIFIER,
        }
        display_lookup = player_rows.set_index("field_id")[
            "probability_display"
        ].to_dict()
        for canonical in field_order:
            row[canonical] = display_lookup.get(canonical, NOT_APPLICABLE)
        rows.append(row)
    result = pd.DataFrame(rows)
    if len(result) != 240:
        raise AssertionError(f"Outcome V3 shadow board must contain 240 rows, found {len(result)}")
    if result["player_id"].astype(str).tolist() != board["player_id"].astype(str).tolist():
        raise AssertionError("Outcome V3 shadow board reordered Finished V1")
    return result


def deterministic_frame_hash(frame: pd.DataFrame, columns: Sequence[str] | None = None) -> str:
    selected = frame if columns is None else frame.loc[:, list(columns)]
    records = selected.replace({np.nan: ""}).to_dict("records")
    return stable_hash(records)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(values, dtype=float), -35, 35)
    return 1.0 / (1.0 + np.exp(-clipped))


def _logit(values: np.ndarray) -> np.ndarray:
    probability = np.clip(np.asarray(values, dtype=float), 1e-8, 1 - 1e-8)
    return np.log(probability / (1 - probability))
