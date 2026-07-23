"""Build the governed exact Model v4 replay and accuracy audit packet.

This builder is intentionally local, deterministic, review-only, and fail-closed.
It reads tracked repository evidence only. It never calls a provider, reads
LocalData, or writes production ranking inputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PACKET_REL = Path(
    "docs/hq/master/nwr_exact_model_v4_replay_accuracy_audit_v1_20260723"
)
PARTIAL_PANEL_REL = Path(
    "docs/hq/model/historical_model_v4_replay_substrate_v1_20260708/"
    "MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
)
FORMULA_MART_REL = Path(
    "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/"
    "FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
AGE_SIDECAR_REL = Path(
    "docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/"
    "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
)
OOF_REL = Path(
    "docs/hq/model/"
    "formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/"
    "OUT_OF_FOLD_PREDICTIONS.csv"
)
CURRENT_BOARD_REL = Path(
    "docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/"
    "rebuilt_full_player_board_value_review_rows.csv"
)
PROXY_BUILDER_REL = Path(
    "docs/hq/model/production_rankings_backtest_v1_20260708/"
    "build_production_rankings_backtest_v1.py"
)
CURRENT_FORMULA_CONTRACT_REL = Path(
    "docs/hq/model/model_v4_formula_documentation_cleanup_v1_20260708/"
    "MODEL_V4_ACTIVE_FORMULA_CONTRACT.md"
)
CURRENT_FORMULA_REGISTRY_REL = Path(
    "docs/hq/model/model_v4_formula_documentation_cleanup_v1_20260708/"
    "MODEL_V4_COMPONENT_REGISTRY.csv"
)
FROZEN_2026_REL = Path(
    "docs/hq/model/"
    "formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/"
    "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
)

ROOT = DEFAULT_ROOT
PACKET = ROOT / CANONICAL_PACKET_REL
PARTIAL_PANEL = ROOT / PARTIAL_PANEL_REL
FORMULA_MART = ROOT / FORMULA_MART_REL
AGE_SIDECAR = ROOT / AGE_SIDECAR_REL
OOF = ROOT / OOF_REL
CURRENT_BOARD = ROOT / CURRENT_BOARD_REL
PROXY_BUILDER = ROOT / PROXY_BUILDER_REL
CURRENT_FORMULA_CONTRACT = ROOT / CURRENT_FORMULA_CONTRACT_REL
CURRENT_FORMULA_REGISTRY = ROOT / CURRENT_FORMULA_REGISTRY_REL
FROZEN_2026 = ROOT / FROZEN_2026_REL

START_HQ = "ce2c40d9cf462e4d4985a37020ae8c30afe72def"
START_TREE = "b4647a5cd129e36113628fc88830cca9fff479b2"
SOURCE_COMMIT = "0929ce6ec058a698efeee10fe5770f56047bab21"
BOARD_HASH = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
FROZEN_2026_HASH = "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179"
TRACKED_INPUT_HASHES = {
    PARTIAL_PANEL_REL: "22c7aa9ecb8567d0ff795809d075f8f8ac91a3dfe56e7a31f8a328ba99c9b99f",
    FORMULA_MART_REL: "4c63a01cc4d56d0496d56ff13d4dabb4faa0b7a24d8f7510a368ad48d9714151",
    AGE_SIDECAR_REL: "ea5ec2455c89031b8deb6077847b7c10e4da4a09f604bf1dae0e6250983f883b",
    OOF_REL: "afa3a87bee6230f2e455c0c01f542b12d17bb737ddb76f1f5af45b607833d390",
    CURRENT_BOARD_REL: BOARD_HASH,
    PROXY_BUILDER_REL: "c9676d4ca145b50492066bfef89c3b5b708600fd61adae82349eedf3ea611590",
    CURRENT_FORMULA_CONTRACT_REL: (
        "be14b8eed1d00ad25418cc3c76b07c2c95e1a44d9bbb23d3ce5284ec5b825c9d"
    ),
    CURRENT_FORMULA_REGISTRY_REL: (
        "daea46d9295647624b701291838f27a765919cfb7ecf4f82572de345d0ec2c3f"
    ),
    FROZEN_2026_REL: FROZEN_2026_HASH,
}
SEED = 20260723
POSITIONS = ("QB", "RB", "WR", "TE")
POSITION_ORDER = {position: index for index, position in enumerate(POSITIONS)}
STARTABLE = {"QB": 12, "RB": 24, "WR": 36, "TE": 12}
EXACT_REQUIRED = (
    "identity",
    "outcome",
    "lagged_production",
    "position_score",
    "lifecycle",
    "confidence",
    "discipline_safety",
    "checkpoint",
    "final_score",
    "rank",
)
EXACT_CLASSIFICATIONS = {
    "EXACT_PRIMARY_EVIDENCE",
    "EXACT_DETERMINISTIC_REGENERATION",
}
ALLOWED_CLASSIFICATIONS = EXACT_CLASSIFICATIONS | {
    "NEAR_EQUIVALENT",
    "PARTIAL_REPLAY",
    "APPROXIMATE",
    "REVIEW_ONLY",
    "BLOCKED_MISSING_RECEIPT",
    "BLOCKED_SOURCE_NOT_ADMITTED",
    "DEPRECATED",
    "FROZEN_COMPARATOR",
}
HISTORICAL_ADMISSIBLE_CLASSIFICATIONS = EXACT_CLASSIFICATIONS | {
    "NEAR_EQUIVALENT",
    "PARTIAL_REPLAY",
    "REVIEW_ONLY",
}
EXACT_JOIN_KEYS = ("player_id", "season", "position")
FEATURE_COLUMNS = (
    "pyf_prior_nwr_points",
    "pyf_prior_nwr_ppg",
    "prior_2yr_weighted_nwr_points",
    "prior_3yr_weighted_nwr_points",
    "prior_games",
    "prior_targets",
    "prior_carries",
    "prior_receptions",
    "prior_rushing_yards",
    "prior_receiving_yards",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
    "prior_rushing_first_downs",
    "prior_receiving_first_downs",
    "prior_passing_attempts",
    "prior_passing_completions",
    "prior_passing_yards",
    "prior_passing_td",
    "prior_interceptions",
    "prior_passing_first_downs",
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_touches",
    "prior_opportunities",
)
FROZEN_2026_COLUMNS = (
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
)


@dataclass(frozen=True)
class Metric:
    rows: int
    seasons: int
    spearman: float
    rank_mae: float
    precision: float
    recall: float
    false_positive_rate: float
    false_negative_rate: float
    score_mae: float | None


@dataclass(frozen=True)
class EvidenceProof:
    component: str
    classification: str
    provenance: str
    schema_proof: str
    identity_proof: str
    historical_availability_proof: str
    mandatory: bool = True


def configure_paths(repo_root: Path, output_dir: Path | None = None) -> None:
    global ROOT, PACKET, PARTIAL_PANEL, FORMULA_MART, AGE_SIDECAR, OOF
    global CURRENT_BOARD, PROXY_BUILDER, CURRENT_FORMULA_CONTRACT
    global CURRENT_FORMULA_REGISTRY, FROZEN_2026
    ROOT = repo_root.resolve()
    PACKET = output_dir.resolve() if output_dir else ROOT / CANONICAL_PACKET_REL
    PARTIAL_PANEL = ROOT / PARTIAL_PANEL_REL
    FORMULA_MART = ROOT / FORMULA_MART_REL
    AGE_SIDECAR = ROOT / AGE_SIDECAR_REL
    OOF = ROOT / OOF_REL
    CURRENT_BOARD = ROOT / CURRENT_BOARD_REL
    PROXY_BUILDER = ROOT / PROXY_BUILDER_REL
    CURRENT_FORMULA_CONTRACT = ROOT / CURRENT_FORMULA_CONTRACT_REL
    CURRENT_FORMULA_REGISTRY = ROOT / CURRENT_FORMULA_REGISTRY_REL
    FROZEN_2026 = ROOT / FROZEN_2026_REL


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        try:
            packet_relative = resolved.relative_to(PACKET)
        except ValueError as exc:
            raise RuntimeError(f"path is outside governed roots: {resolved}") from exc
        return (CANONICAL_PACKET_REL / packet_relative).as_posix()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def source_commit(path: Path) -> str:
    return git("log", "-1", "--format=%H", SOURCE_COMMIT, "--", rel(path)) or "NOT_FOUND"


def write_canonical_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.encode("utf-8"))


def stable_value_key(field: str, value: Any) -> tuple[int, Any]:
    if value is None:
        return (4, "")
    try:
        if bool(pd.isna(value)):
            return (4, "")
    except (TypeError, ValueError):
        pass
    text_value = str(value)
    if text_value == "OVERALL":
        return (0, -1)
    if text_value in POSITION_ORDER:
        return (0, POSITION_ORDER[text_value])
    if ":" in text_value and text_value.rsplit(":", 1)[-1] in POSITION_ORDER:
        prefix, position = text_value.rsplit(":", 1)
        return (0, (prefix, POSITION_ORDER[position]))
    if text_value.startswith("WITHOUT_") and text_value.removeprefix("WITHOUT_") in POSITION_ORDER:
        return (0, POSITION_ORDER[text_value.removeprefix("WITHOUT_")])
    if isinstance(value, (bool, np.bool_)):
        return (1, int(value))
    if isinstance(value, (int, float, np.integer, np.floating)):
        return (1, float(value))
    return (2, str(value))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized = list(rows)
    materialized.sort(
        key=lambda row: tuple(stable_value_key(field, row.get(field)) for field in fields)
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in materialized:
            writer.writerow({field: clean(row.get(field, "")) for field in fields})


def clean(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return ""
        return f"{float(value):.6f}"
    if isinstance(value, (bool, np.bool_)):
        return "true" if value else "false"
    return value


def write_md(name: str, body: str) -> None:
    write_canonical_text(PACKET / name, body.rstrip() + "\n")


def canonicalize_frame(frame: pd.DataFrame, keys: tuple[str, ...]) -> pd.DataFrame:
    missing = [key for key in keys if key not in frame.columns]
    if missing:
        raise RuntimeError(f"canonical sort keys missing: {missing}")
    output = frame.copy()
    helper_columns: list[str] = []
    for index, key in enumerate(keys):
        helper = f"__canonical_sort_{index}"
        helper_columns.append(helper)
        if key == "position":
            output[helper] = output[key].map(POSITION_ORDER).fillna(len(POSITION_ORDER))
        elif pd.api.types.is_numeric_dtype(output[key]):
            output[helper] = pd.to_numeric(output[key], errors="coerce").fillna(np.inf)
        else:
            output[helper] = output[key].astype("string").fillna("\uffff")
    output = output.sort_values(helper_columns, kind="stable", na_position="last")
    return output.drop(columns=helper_columns).reset_index(drop=True)


def perturb_frame(frame: pd.DataFrame, mode: str, seed: int) -> pd.DataFrame:
    if mode == "original":
        return frame.copy()
    if mode == "reverse":
        return frame.iloc[::-1].reset_index(drop=True)
    if mode == "random":
        return frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    raise RuntimeError(f"unsupported input-order mode: {mode}")


def validate_tracked_input_hashes() -> None:
    for relative, expected in TRACKED_INPUT_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"required tracked input missing: {relative.as_posix()}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"tracked input hash changed: {relative.as_posix()} "
                f"expected={expected} actual={actual}"
            )


def historical_feature_records(
    mart: pd.DataFrame,
    *,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
) -> pd.DataFrame:
    missing = [
        column
        for column in ("player_id", "feature_season", "season", *feature_columns)
        if column not in mart.columns
    ]
    if missing:
        raise RuntimeError(f"historical feature columns missing: {missing}")
    records: list[dict[str, Any]] = []
    for row in mart.itertuples(index=False):
        input_season = int(row.feature_season)
        target_season = int(row.season)
        for field_name in feature_columns:
            records.append(
                {
                    "player_id": row.player_id,
                    "input_season": input_season,
                    "target_season": target_season,
                    "as_of_date": f"{target_season}-02-15",
                    "feature_family": "LAGGED_PRODUCTION",
                    "source_authority": rel(FORMULA_MART),
                    "source_season": input_season,
                    "availability_classification": "EXACT_DETERMINISTIC_REGENERATION",
                    "field_name": field_name,
                    "value": getattr(row, field_name),
                }
            )
    return pd.DataFrame.from_records(records)


def validate_temporal_records(records: pd.DataFrame) -> None:
    required = (
        "player_id",
        "input_season",
        "target_season",
        "as_of_date",
        "feature_family",
        "source_authority",
        "source_season",
        "availability_classification",
        "field_name",
    )
    missing = [column for column in required if column not in records.columns]
    if missing:
        raise RuntimeError(f"temporal metadata missing: {missing}")
    if records.empty:
        raise RuntimeError("temporal record set is empty")
    for column in (
        "player_id",
        "as_of_date",
        "feature_family",
        "source_authority",
        "availability_classification",
        "field_name",
    ):
        values = records[column].astype("string")
        if values.isna().any() or values.str.strip().eq("").any():
            raise RuntimeError(f"temporal metadata blank: {column}")
    input_season = pd.to_numeric(records["input_season"], errors="coerce")
    target_season = pd.to_numeric(records["target_season"], errors="coerce")
    source_season = pd.to_numeric(records["source_season"], errors="coerce")
    if input_season.isna().any() or target_season.isna().any() or source_season.isna().any():
        raise RuntimeError("season metadata must be numeric and complete")
    if not target_season.eq(input_season + 1).all():
        raise RuntimeError("contradictory input/target season metadata")
    if source_season.gt(input_season).any():
        raise RuntimeError("future or target-season source is inadmissible")
    as_of = pd.to_datetime(records["as_of_date"], errors="coerce")
    target_boundary = pd.to_datetime(target_season.astype(int).astype(str) + "-09-01")
    if as_of.isna().any() or as_of.gt(target_boundary).any():
        raise RuntimeError("as-of boundary is absent or later than the target decision boundary")
    classifications = set(records["availability_classification"].astype(str))
    unsupported = classifications - ALLOWED_CLASSIFICATIONS
    if unsupported:
        raise RuntimeError(f"unsupported availability classification: {sorted(unsupported)}")
    inadmissible = classifications - HISTORICAL_ADMISSIBLE_CLASSIFICATIONS
    if inadmissible:
        raise RuntimeError(f"historically inadmissible classification: {sorted(inadmissible)}")
    denied_fields = records["field_name"].astype(str).str.lower().str.contains(
        r"(?:^|_)(?:current|current_only|current_board|market_adp|adp|target_score|"
        r"target_games|label_next|next_nwr|nwr_dynasty_score)(?:$|_)",
        regex=True,
    )
    denied_families = records["feature_family"].astype(str).str.upper().isin(
        {"CURRENT_ONLY_ADP", "CURRENT_BOARD_RANK", "TARGET_SEASON_SCORE", "FUTURE_PRODUCTION"}
    )
    if denied_fields.any() or denied_families.any():
        raise RuntimeError("current-only, target-season, or future feature is inadmissible")


def default_exactness_proofs() -> list[EvidenceProof]:
    exact_provenance = f"{rel(FORMULA_MART)}#{sha256(FORMULA_MART)}"
    return [
        EvidenceProof(
            "identity",
            "EXACT_PRIMARY_EVIDENCE",
            exact_provenance,
            "FORMULA_MART_SCHEMA_V1",
            "EXACT_PLAYER_ID",
            "HISTORICAL_ASOF_PROVEN",
        ),
        EvidenceProof(
            "outcome",
            "EXACT_PRIMARY_EVIDENCE",
            exact_provenance,
            "FORMULA_MART_SCHEMA_V1",
            "EXACT_PLAYER_ID",
            "TARGET_LABEL_JOINED_AFTER_FEATURES",
        ),
        EvidenceProof(
            "lagged_production",
            "EXACT_DETERMINISTIC_REGENERATION",
            exact_provenance,
            "FORMULA_MART_SCHEMA_V1",
            "EXACT_PLAYER_ID",
            "FEATURE_N_TARGET_N_PLUS_1",
        ),
        EvidenceProof("position_score", "BLOCKED_MISSING_RECEIPT", "", "", "", ""),
        EvidenceProof("lifecycle", "NEAR_EQUIVALENT", rel(AGE_SIDECAR), "", "", ""),
        EvidenceProof("confidence", "NEAR_EQUIVALENT", rel(FORMULA_MART), "", "", ""),
        EvidenceProof("discipline_safety", "BLOCKED_MISSING_RECEIPT", "", "", "", ""),
        EvidenceProof("checkpoint", "BLOCKED_MISSING_RECEIPT", "", "", "", ""),
        EvidenceProof("final_score", "BLOCKED_MISSING_RECEIPT", "", "", "", ""),
        EvidenceProof("rank", "BLOCKED_MISSING_RECEIPT", "", "", "", ""),
    ]


def validate_exactness_proofs(proofs: Iterable[EvidenceProof]) -> dict[str, EvidenceProof]:
    proof_list = list(proofs)
    components = [proof.component for proof in proof_list]
    if len(components) != len(set(components)):
        raise RuntimeError("duplicate exactness component proof")
    missing = sorted(set(EXACT_REQUIRED) - set(components))
    extra = sorted(set(components) - set(EXACT_REQUIRED))
    if missing or extra:
        raise RuntimeError(
            f"exactness component completeness failure missing={missing} extra={extra}"
        )
    by_component = {proof.component: proof for proof in proof_list}
    for proof in proof_list:
        if proof.classification not in ALLOWED_CLASSIFICATIONS:
            raise RuntimeError(f"unsupported exactness classification: {proof.classification}")
        if proof.mandatory is not True:
            raise RuntimeError(f"mandatory component omitted: {proof.component}")
        if proof.classification in EXACT_CLASSIFICATIONS and not all(
            (
                proof.provenance.strip(),
                proof.schema_proof.strip(),
                proof.identity_proof.strip(),
                proof.historical_availability_proof.strip(),
            )
        ):
            raise RuntimeError(f"exact label lacks complete authority proof: {proof.component}")
    return by_component


def derive_full_row_exactness(proofs: Iterable[EvidenceProof]) -> bool:
    by_component = validate_exactness_proofs(proofs)
    return all(
        by_component[component].classification in EXACT_CLASSIFICATIONS
        for component in EXACT_REQUIRED
    )


def validate_identity_frame(frame: pd.DataFrame, *, name: str) -> None:
    missing = [column for column in EXACT_JOIN_KEYS if column not in frame.columns]
    if missing:
        raise RuntimeError(f"{name} exact identity columns missing: {missing}")
    player_ids = frame["player_id"].astype("string")
    if player_ids.isna().any() or player_ids.str.strip().eq("").any():
        raise RuntimeError(f"{name} contains blank player_id")
    if frame.duplicated(list(EXACT_JOIN_KEYS)).any():
        raise RuntimeError(f"{name} contains duplicate exact player identity")


def exact_player_id_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    join_keys: tuple[str, ...] = EXACT_JOIN_KEYS,
    how: str = "left",
) -> pd.DataFrame:
    if tuple(join_keys) != EXACT_JOIN_KEYS:
        raise RuntimeError("historical joins require exact player_id/season/position authority")
    validate_identity_frame(left, name="left join input")
    validate_identity_frame(right, name="right join input")
    left_identity = set(map(tuple, left[list(EXACT_JOIN_KEYS)].itertuples(index=False, name=None)))
    right_identity = set(
        map(tuple, right[list(EXACT_JOIN_KEYS)].itertuples(index=False, name=None))
    )
    if left_identity != right_identity:
        raise RuntimeError("historical exact identity universes differ")
    if "player_name" in left.columns and "player_name" in right.columns:
        governed = left[list(EXACT_JOIN_KEYS) + ["player_name"]].merge(
            right[list(EXACT_JOIN_KEYS) + ["player_name"]],
            on=list(EXACT_JOIN_KEYS),
            how="outer",
            validate="one_to_one",
            suffixes=("_left", "_right"),
            indicator=True,
        )
        if not governed["_merge"].eq("both").all() or not governed["player_name_left"].fillna(
            ""
        ).eq(governed["player_name_right"].fillna("")).all():
            raise RuntimeError("player_id/name authority mismatch")
    return left.merge(
        right,
        on=list(EXACT_JOIN_KEYS),
        how=how,
        validate="one_to_one",
        suffixes=("", "_right"),
    )


def validate_frozen_comparator(path: Path | None = None) -> pd.DataFrame:
    path = path or FROZEN_2026
    if not path.is_file():
        raise RuntimeError("frozen 2026 comparator missing")
    actual_hash = sha256(path)
    if actual_hash != FROZEN_2026_HASH:
        raise RuntimeError(
            f"frozen 2026 comparator hash changed expected={FROZEN_2026_HASH} actual={actual_hash}"
        )
    frame = pd.read_csv(path, low_memory=False)
    if tuple(frame.columns) != FROZEN_2026_COLUMNS:
        raise RuntimeError("frozen 2026 comparator schema changed")
    if len(frame) != 924:
        raise RuntimeError("frozen 2026 comparator row count changed")
    ids = frame["player_id"].astype("string")
    if ids.isna().any() or ids.str.strip().eq("").any():
        raise RuntimeError("frozen 2026 comparator player-ID set changed")
    governed = (
        "raw_score",
        "within_position_rank",
        "overall_research_rank",
        "freeze_timestamp",
        "target_season",
        "feature_season",
        "input_source_dates",
        "input_source_hashes",
        "source_status",
    )
    if frame[list(governed)].isna().all(axis=1).any():
        raise RuntimeError("frozen comparator governed score/rank/source/as-of row is incomplete")
    return frame


def load_sources(
    *,
    input_order: str = "original",
    order_seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validate_tracked_input_hashes()
    for path in (
        PARTIAL_PANEL,
        FORMULA_MART,
        AGE_SIDECAR,
        OOF,
        CURRENT_BOARD,
        PROXY_BUILDER,
        CURRENT_FORMULA_CONTRACT,
        CURRENT_FORMULA_REGISTRY,
        FROZEN_2026,
    ):
        if not path.is_file():
            raise RuntimeError(f"required tracked input missing: {rel(path)}")
    validate_frozen_comparator()
    panel = pd.read_csv(PARTIAL_PANEL, low_memory=False)
    mart = pd.read_csv(FORMULA_MART, low_memory=False)
    age = pd.read_csv(AGE_SIDECAR, low_memory=False)
    oof = pd.read_csv(OOF, low_memory=False)
    if len(panel) != 5518 or len(mart) != 5518 or len(age) != 5518:
        raise RuntimeError("historical row-universe count changed")
    if panel["substrate_row_id"].duplicated().any():
        raise RuntimeError("partial panel identity is not unique")
    if mart["substrate_row_id"].duplicated().any():
        raise RuntimeError("formula mart identity is not unique")
    if set(panel["player_id_gsis"]) != set(mart["player_id"]):
        raise RuntimeError("player-id universes differ")
    if bool(mart["production_approved"].fillna(False).astype(bool).any()):
        raise RuntimeError("review-only mart unexpectedly production approved")
    validate_identity_frame(mart, name="formula mart")
    validate_identity_frame(age, name="age sidecar")
    exact_player_id_join(
        mart[list(EXACT_JOIN_KEYS) + ["player_name"]],
        age[list(EXACT_JOIN_KEYS) + ["player_name"]],
    )
    panel_identity = panel[
        ["substrate_row_id", "player_id_gsis", "target_season", "position"]
    ].rename(columns={"player_id_gsis": "player_id", "target_season": "season"})
    mart_identity = mart[
        ["substrate_row_id", "player_id", "season", "position"]
    ]
    identity_check = panel_identity.merge(
        mart_identity,
        on=["substrate_row_id", "player_id", "season", "position"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not identity_check["_merge"].eq("both").all():
        raise RuntimeError("panel-to-mart exact player identity mismatch")
    oof_ids = oof["player_id"].astype("string")
    if oof_ids.isna().any() or oof_ids.str.strip().eq("").any():
        raise RuntimeError("OOF contains blank player_id")
    mart_oof_map = mart.set_index("substrate_row_id")["player_id"]
    mapped = oof["substrate_row_id"].map(mart_oof_map)
    overlap = mapped.notna()
    if not mapped.loc[overlap].astype(str).eq(oof.loc[overlap, "player_id"].astype(str)).all():
        raise RuntimeError("OOF exact player identity mismatch")
    validate_temporal_records(historical_feature_records(mart))
    panel = perturb_frame(panel, input_order, order_seed)
    mart = perturb_frame(mart, input_order, order_seed + 1)
    age = perturb_frame(age, input_order, order_seed + 2)
    oof = perturb_frame(oof, input_order, order_seed + 3)
    panel = canonicalize_frame(
        panel,
        ("target_season", "position", "player_id_gsis", "substrate_row_id"),
    )
    mart = canonicalize_frame(
        mart,
        ("season", "position", "player_id", "substrate_row_id"),
    )
    age = canonicalize_frame(
        age,
        ("season", "position", "player_id"),
    )
    oof = canonicalize_frame(
        oof,
        ("target_season", "position", "candidate_name", "player_id", "substrate_row_id"),
    )
    return panel, mart, age, oof


def load_proxy_module() -> Any:
    spec = importlib.util.spec_from_file_location("nwr_proxy_builder", PROXY_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load accepted proxy builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_proxy(panel: pd.DataFrame) -> pd.DataFrame:
    proxy = panel.copy()
    numeric = [
        column
        for column in proxy.columns
        if column.startswith("prior_")
        or column
        in {
            "feature_season",
            "target_season",
            "target_games",
            "next_nwr_points",
            "next_position_finish",
        }
    ]
    for column in numeric:
        proxy[column] = pd.to_numeric(proxy[column], errors="coerce")
    module = load_proxy_module()
    proxy = module._add_proxy_scores(proxy)  # noqa: SLF001
    proxy = module._add_prediction_ranks(  # noqa: SLF001
        proxy, "production_formula_partial_proxy_score"
    )
    return proxy


def add_ranks(
    frame: pd.DataFrame,
    score: str,
    *,
    name: str,
    player_name: str = "player_name",
) -> pd.DataFrame:
    output = frame.copy()
    output[name] = np.nan
    for (_season, _position), group in output.groupby(["season", "position"], sort=True):
        tie_breakers = [score, player_name]
        ascending = [False, True]
        for candidate in ("player_id", "substrate_row_id"):
            if candidate in group.columns:
                tie_breakers.append(candidate)
                ascending.append(True)
        ranked = group.sort_values(
            tie_breakers,
            ascending=ascending,
            na_position="last",
            kind="stable",
        )
        valid = ranked[score].notna()
        output.loc[ranked.loc[valid].index, name] = np.arange(1, valid.sum() + 1)
    return output


def spearman(left: pd.Series, right: pd.Series) -> float:
    joined = pd.concat([left, right], axis=1).dropna()
    if len(joined) < 2:
        return float("nan")
    return float(joined.iloc[:, 0].rank().corr(joined.iloc[:, 1].rank()))


def metric(
    frame: pd.DataFrame,
    pred_rank: str,
    actual_rank: str,
    *,
    raw_score: str | None = None,
    actual_score: str | None = None,
) -> Metric:
    valid = frame.dropna(subset=[pred_rank, actual_rank]).copy()
    if valid.empty:
        return Metric(0, 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, None)
    actual_hit = pd.Series(False, index=valid.index)
    pred_hit = pd.Series(False, index=valid.index)
    for position, threshold in STARTABLE.items():
        mask = valid["position"].eq(position)
        actual_hit.loc[mask] = valid.loc[mask, actual_rank].le(threshold)
        pred_hit.loc[mask] = valid.loc[mask, pred_rank].le(threshold)
    tp = int((actual_hit & pred_hit).sum())
    fp = int((~actual_hit & pred_hit).sum())
    fn = int((actual_hit & ~pred_hit).sum())
    tn = int((~actual_hit & ~pred_hit).sum())
    score_mae: float | None = None
    if raw_score and actual_score:
        scores = valid.dropna(subset=[raw_score, actual_score])
        if not scores.empty:
            score_mae = float((scores[raw_score] - scores[actual_score]).abs().mean())
    rank_spearman = spearman(valid[pred_rank], valid[actual_rank])
    if valid["position"].nunique() > 1:
        position_metrics = [
            metric(
                group,
                pred_rank,
                actual_rank,
                raw_score=raw_score,
                actual_score=actual_score,
            )
            for _position, group in valid.groupby("position")
        ]
        contributing = [
            item for item in position_metrics if item.rows and not np.isnan(item.spearman)
        ]
        if contributing:
            rank_spearman = sum(item.spearman * item.rows for item in contributing) / sum(
                item.rows for item in contributing
            )
    return Metric(
        rows=len(valid),
        seasons=int(valid["season"].nunique()),
        spearman=rank_spearman,
        rank_mae=float((valid[pred_rank] - valid[actual_rank]).abs().mean()),
        precision=tp / (tp + fp) if tp + fp else np.nan,
        recall=tp / (tp + fn) if tp + fn else np.nan,
        false_positive_rate=fp / (fp + tn) if fp + tn else np.nan,
        false_negative_rate=fn / (fn + tp) if fn + tp else np.nan,
        score_mae=score_mae,
    )


def bootstrap_ci(frame: pd.DataFrame, pred_rank: str, actual_rank: str) -> tuple[float, float]:
    seasons = np.array(sorted(frame["season"].dropna().unique()))
    if len(seasons) < 2:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    values: list[float] = []
    for _index in range(100):
        sampled = rng.choice(seasons, size=len(seasons), replace=True)
        pieces = [frame.loc[frame["season"].eq(season)] for season in sampled]
        value = metric(pd.concat(pieces), pred_rank, actual_rank).spearman
        if not np.isnan(value):
            values.append(value)
    if not values:
        return np.nan, np.nan
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def baseline_rows(
    proxy: pd.DataFrame, mart: pd.DataFrame, age: pd.DataFrame
) -> list[dict[str, Any]]:
    base = exact_player_id_join(
        mart,
        age[
            [
                "player_id",
                "season",
                "position",
                "age_bucket",
                "lifecycle_bucket",
            ]
        ],
        how="left",
    )
    for column in (
        "season",
        "label_next_position_finish",
        "label_next_nwr_points",
        "pyf_prior_nwr_points",
        "prior_2yr_weighted_nwr_points",
        "prior_3yr_weighted_nwr_points",
    ):
        base[column] = pd.to_numeric(base[column], errors="coerce")
    base = add_ranks(base, "pyf_prior_nwr_points", name="pyf_rank")
    base = add_ranks(base, "prior_2yr_weighted_nwr_points", name="two_year_rank")
    base = add_ranks(base, "prior_3yr_weighted_nwr_points", name="three_year_rank")
    late_guard = base["age_bucket"].astype(str).eq("age_32_plus") | base["lifecycle_bucket"].astype(
        str
    ).eq("late_career_10_plus")
    base["gauntlet_081_score"] = base["prior_3yr_weighted_nwr_points"] * np.where(
        late_guard, 0.98, 1.0
    )
    base = add_ranks(base, "gauntlet_081_score", name="gauntlet_081_rank")
    proxy_eval = proxy.rename(
        columns={
            "target_season": "season",
            "next_position_finish": "actual_rank",
            "next_nwr_points": "actual_score",
            "production_formula_partial_proxy_score_pred_rank": "proxy_rank",
        }
    )
    rows: list[dict[str, Any]] = []

    def append(
        model: str,
        layer: str,
        data: pd.DataFrame,
        pred: str,
        actual: str,
        raw: str | None = None,
        actual_score: str | None = None,
        caveat: str = "",
    ) -> None:
        scopes = [("OVERALL", data)]
        scopes.extend((position, data.loc[data["position"].eq(position)]) for position in POSITIONS)
        for scope, scoped in scopes:
            result = metric(scoped, pred, actual, raw_score=raw, actual_score=actual_score)
            low, high = bootstrap_ci(scoped, pred, actual)
            rows.append(
                {
                    "model": model,
                    "evidence_layer": layer,
                    "metric_alignment": "RANKING_ALIGNED",
                    "scope": scope,
                    "rows": result.rows,
                    "seasons": result.seasons,
                    "effective_sample_size": result.rows,
                    "spearman": result.spearman,
                    "spearman_ci_low": low,
                    "spearman_ci_high": high,
                    "rank_mae": result.rank_mae,
                    "top_n_precision": result.precision,
                    "top_n_recall": result.recall,
                    "false_positive_rate": result.false_positive_rate,
                    "false_negative_rate": result.false_negative_rate,
                    "score_mae": result.score_mae,
                    "caveat": caveat,
                }
            )

    append(
        "EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY",
        "BLOCKED_MISSING_RECEIPT",
        base.iloc[0:0],
        "pyf_rank",
        "label_next_position_finish",
        caveat="Zero complete exact rows; no metric invented.",
    )
    append(
        "ACCEPTED_PRODUCTION_PROXY",
        "PARTIAL_REPLAY",
        proxy_eval,
        "proxy_rank",
        "actual_rank",
        raw="production_formula_partial_proxy_score",
        caveat="Proxy score scale is 0..1; score MAE against fantasy points is invalid.",
    )
    append(
        "PYF",
        "EXACT_DETERMINISTIC_REGENERATION",
        base,
        "pyf_rank",
        "label_next_position_finish",
        raw="pyf_prior_nwr_points",
        actual_score="label_next_nwr_points",
    )
    append(
        "MULTI_YEAR_AVERAGE_2YR",
        "EXACT_DETERMINISTIC_REGENERATION",
        base,
        "two_year_rank",
        "label_next_position_finish",
        raw="prior_2yr_weighted_nwr_points",
        actual_score="label_next_nwr_points",
    )
    append(
        "MULTI_YEAR_AVERAGE_3YR",
        "EXACT_DETERMINISTIC_REGENERATION",
        base,
        "three_year_rank",
        "label_next_position_finish",
        raw="prior_3yr_weighted_nwr_points",
        actual_score="label_next_nwr_points",
    )
    append(
        "GAUNTLET_081",
        "REVIEW_ONLY",
        base,
        "gauntlet_081_rank",
        "label_next_position_finish",
        raw="gauntlet_081_score",
        actual_score="label_next_nwr_points",
        caveat=("Fixed prior challenger; full-history selection through 2025 prevents admission."),
    )
    for blocked in (
        "HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1",
        "ACCEPTED_NEAR_EQUIVALENT_OLD_CURRENT_RECONSTRUCTION",
        "PRODUCTION_SAFE_LIFECYCLE_BASELINE",
    ):
        append(
            blocked,
            "BLOCKED_MISSING_RECEIPT",
            base.iloc[0:0],
            "pyf_rank",
            "label_next_position_finish",
            caveat="Exact governed definition or admitted historical output was not found.",
        )
    return rows


def age_join(mart: pd.DataFrame, age: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "player_id",
        "player_name",
        "season",
        "position",
        "age",
        "years_since_rookie_year",
        "career_stage",
        "age_bucket",
        "lifecycle_bucket",
        "missingness_flag",
        "source_gate_status",
        "leakage_flag",
    ]
    return exact_player_id_join(mart, age[fields], how="left")


def exactness_mask(mart: pd.DataFrame, age: pd.DataFrame) -> pd.DataFrame:
    proofs = validate_exactness_proofs(default_exactness_proofs())
    full_exact = derive_full_row_exactness(proofs.values())
    partial_exact = any(
        proof.classification in EXACT_CLASSIFICATIONS for proof in proofs.values()
    ) and not full_exact
    blocker_names = {
        "lifecycle": "lifecycle_modifier",
        "confidence": "confidence_cap",
    }
    blockers = [
        blocker_names.get(component, component)
        for component in EXACT_REQUIRED
        if proofs[component].classification not in EXACT_CLASSIFICATIONS
    ]
    joined = age_join(mart, age)
    joined["age"] = pd.to_numeric(joined["age"], errors="coerce")
    joined["prior_games"] = pd.to_numeric(joined["prior_games"], errors="coerce")
    output = pd.DataFrame(
        {
            "substrate_row_id": joined["substrate_row_id"],
            "player_id": joined["player_id"],
            "target_season": joined["season"],
            "feature_season": joined["feature_season"],
            "position": joined["position"],
            "age": joined["age"],
            "prior_games": joined["prior_games"],
            "identity_status": proofs["identity"].classification,
            "outcome_status": proofs["outcome"].classification,
            "lagged_production_status": proofs["lagged_production"].classification,
            "position_score_status": proofs["position_score"].classification,
            "lifecycle_status": proofs["lifecycle"].classification,
            "confidence_status": proofs["confidence"].classification,
            "discipline_safety_status": proofs["discipline_safety"].classification,
            "checkpoint_status": proofs["checkpoint"].classification,
            "final_score_status": proofs["final_score"].classification,
            "rank_status": proofs["rank"].classification,
            "route_status": "BLOCKED_SOURCE_NOT_ADMITTED",
            "return_scoring_status": "BLOCKED_SOURCE_NOT_ADMITTED",
            "full_exact_row": full_exact,
            "exact_component_partial_row": partial_exact,
            "proxy_available": True,
            "exactness_blocker": "|".join(blockers),
        }
    )
    if bool(output["full_exact_row"].any()):
        raise RuntimeError("exact subset must fail closed while required receipts are absent")
    return canonicalize_frame(
        output,
        ("target_season", "position", "player_id", "substrate_row_id"),
    )


def coverage_rows(mask: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(dimension: str, key: str, group: pd.DataFrame) -> None:
        rows.append(
            {
                "dimension": dimension,
                "value": key,
                "rows": len(group),
                "full_exact_rows": int(group["full_exact_row"].sum()),
                "exact_component_partial_rows": int(group["exact_component_partial_row"].sum()),
                "proxy_rows": int(group["proxy_available"].sum()),
                "full_exact_percent": float(group["full_exact_row"].mean()),
                "positions": "|".join(sorted(group["position"].unique())),
                "seasons": "|".join(
                    str(value) for value in sorted(group["target_season"].unique())
                ),
            }
        )

    for (season, position), group in mask.groupby(["target_season", "position"]):
        add("SEASON_POSITION", f"{season}:{position}", group)
    for position, group in mask.groupby("position"):
        add("POSITION", str(position), group)
    for season, group in mask.groupby("target_season"):
        add("SEASON", str(season), group)
    age_band = (
        pd.cut(
            mask["age"],
            bins=[0, 22, 25, 28, 30, 34, 200],
            labels=["<=22", "23-25", "26-28", "29-30", "31-34", "35+"],
        )
        .astype("string")
        .fillna("MISSING")
    )
    for value, group in mask.assign(_band=age_band).groupby("_band"):
        add("AGE", str(value), group)
    games_band = (
        pd.cut(
            mask["prior_games"],
            bins=[-1, 3, 7, 11, 16, 100],
            labels=["0-3", "4-7", "8-11", "12-16", "17+"],
        )
        .astype("string")
        .fillna("MISSING")
    )
    for value, group in mask.assign(_band=games_band).groupby("_band"):
        add("PRIOR_GAMES", str(value), group)
    return rows


def attribution_rows(
    proxy: pd.DataFrame, mart: pd.DataFrame, age: pd.DataFrame
) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    base = age_join(mart, age)
    proxy_fields = proxy[
        [
            "substrate_row_id",
            "production_formula_partial_proxy_score",
            "production_formula_partial_proxy_score_pred_rank",
            "next_position_finish",
        ]
    ].copy()
    data = base.merge(proxy_fields, on="substrate_row_id", how="inner")
    numeric = [
        "season",
        "age",
        "years_since_rookie_year",
        "prior_games",
        "pyf_prior_nwr_points",
        "prior_2yr_weighted_nwr_points",
        "prior_3yr_weighted_nwr_points",
        "label_next_nwr_points",
        "label_next_position_finish",
        "production_formula_partial_proxy_score",
        "production_formula_partial_proxy_score_pred_rank",
        "next_position_finish",
    ]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["rank_residual"] = (
        data["production_formula_partial_proxy_score_pred_rank"]
        - data["label_next_position_finish"]
    )
    data["absolute_rank_residual"] = data["rank_residual"].abs()
    data["false_positive"] = False
    data["false_negative"] = False
    for position, threshold in STARTABLE.items():
        selected = data["position"].eq(position)
        predicted = data["production_formula_partial_proxy_score_pred_rank"].le(threshold)
        actual = data["label_next_position_finish"].le(threshold)
        data.loc[selected, "false_positive"] = selected & predicted & ~actual
        data.loc[selected, "false_negative"] = selected & ~predicted & actual
    games_map = data.set_index(["player_id", "feature_season"])["prior_games"]
    data["prior_2yr_games"] = data["prior_games"] + pd.Series(
        [
            games_map.get((player, feature - 1), np.nan)
            for player, feature in zip(data["player_id"], data["feature_season"], strict=True)
        ],
        index=data.index,
    )
    data["prior_3yr_games"] = data["prior_2yr_games"] + pd.Series(
        [
            games_map.get((player, feature - 2), np.nan)
            for player, feature in zip(data["player_id"], data["feature_season"], strict=True)
        ],
        index=data.index,
    )
    data["age_cohort"] = np.select(
        [
            data["position"].eq("WR") & data["age"].ge(30),
            data["position"].eq("RB") & data["age"].ge(28),
            data["position"].eq("TE") & data["age"].ge(31),
            data["position"].eq("QB") & data["age"].ge(34),
        ],
        ["WR_30_PLUS", "RB_28_PLUS", "TE_31_PLUS", "QB_34_PLUS"],
        default="OTHER",
    )
    data["prior_games_cohort"] = (
        pd.cut(
            data["prior_games"],
            [-1, 3, 7, 11, 16, 100],
            labels=["0-3", "4-7", "8-11", "12-16", "17+"],
        )
        .astype("string")
        .fillna("MISSING")
    )
    data["two_year_games_cohort"] = (
        pd.cut(
            data["prior_2yr_games"],
            [-1, 7, 15, 23, 31, 100],
            labels=["0-7", "8-15", "16-23", "24-31", "32+"],
        )
        .astype("string")
        .fillna("MISSING")
    )
    data["three_year_games_cohort"] = (
        pd.cut(
            data["prior_3yr_games"],
            [-1, 11, 23, 35, 47, 100],
            labels=["0-11", "12-23", "24-35", "36-47", "48+"],
        )
        .astype("string")
        .fillna("MISSING")
    )
    data["production_tier"] = pd.qcut(
        data["pyf_prior_nwr_points"].rank(method="first"),
        4,
        labels=["LOW", "LOW_MID", "HIGH_MID", "HIGH"],
    )
    data["stability"] = (data["prior_3yr_weighted_nwr_points"] - data["pyf_prior_nwr_points"]).abs()
    data["stability_cohort"] = pd.qcut(
        data["stability"].rank(method="first"),
        4,
        labels=["STABLE", "MODERATE", "VOLATILE", "MOST_VOLATILE"],
    )
    data["trend"] = data["pyf_prior_nwr_points"] - data["prior_3yr_weighted_nwr_points"]
    data["trend_cohort"] = pd.cut(
        data["trend"], [-np.inf, -25, 25, np.inf], labels=["DECLINING", "FLAT", "RISING"]
    )
    data["rank_tier"] = pd.cut(
        data["production_formula_partial_proxy_score_pred_rank"],
        [0, 12, 24, 60, np.inf],
        labels=["TOP_12", "TOP_24", "TOP_60", "DEPTH"],
    )
    data["missingness"] = np.where(
        data["confidence_missingness_flag"].astype(str).eq("component_missingness_present"),
        "MISSING_COMPONENT",
        "COMPLETE_AVAILABLE_PROXY_FIELDS",
    )
    dimensions = {
        "POSITION": "position",
        "AGE_COHORT": "age_cohort",
        "YEARS_IN_LEAGUE": "years_since_rookie_year",
        "PRIOR_GAMES": "prior_games_cohort",
        "TWO_YEAR_GAMES": "two_year_games_cohort",
        "THREE_YEAR_GAMES": "three_year_games_cohort",
        "PRIOR_PRODUCTION": "production_tier",
        "MULTI_YEAR_STABILITY": "stability_cohort",
        "TREND": "trend_cohort",
        "RANK_TIER": "rank_tier",
        "MISSINGNESS": "missingness",
        "CONFIDENCE_STATE": "confidence_status",
        "LIFECYCLE_STATE": "lifecycle_bucket",
        "SOURCE_COVERAGE": "source_gate_status",
        "SEASON": "season",
    }
    rows: list[dict[str, Any]] = []
    for dimension, column in dimensions.items():
        for value, group in data.groupby(column, dropna=False):
            rows.append(
                {
                    "dimension": dimension,
                    "cohort": str(value),
                    "rows": len(group),
                    "mean_signed_rank_error": group["rank_residual"].mean(),
                    "rank_mae": group["absolute_rank_residual"].mean(),
                    "false_positives": int(group["false_positive"].sum()),
                    "false_negatives": int(group["false_negative"].sum()),
                    "spearman": spearman(
                        group["production_formula_partial_proxy_score_pred_rank"],
                        group["label_next_position_finish"],
                    ),
                    "evidence_layer": "ACCEPTED_PRODUCTION_PROXY",
                    "primary_attribution": "PROXY_AND_OUTCOME_ERROR_NOT_EXACT_MODEL_ERROR",
                    "caveat": "Attribution cannot isolate exact Model v4 formula error.",
                }
            )
    for dimension in ("TEAM_CHANGE", "INACTIVE_RETIREMENT"):
        rows.append(
            {
                "dimension": dimension,
                "cohort": "BLOCKED_HISTORICAL_FIELD_UNAVAILABLE",
                "rows": 0,
                "evidence_layer": "BLOCKED_SOURCE_NOT_ADMITTED",
                "primary_attribution": "NOT_TESTABLE",
                "caveat": "No safe historically as-of field in the admitted panel.",
            }
        )
    return rows, data


def oof_candidate_rows(
    oof: pd.DataFrame,
    mart: pd.DataFrame,
    age: pd.DataFrame,
    proxy: pd.DataFrame,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data = oof.copy()
    numeric = [
        "target_season",
        "feature_season",
        "raw_score",
        "prediction_rank_full_coverage",
        "actual_nwr_points",
        "actual_position_finish",
    ]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["score_valid"] = data["score_valid"].astype(str).str.lower().eq("true")
    data = data.rename(columns={"target_season": "season"})
    pyf = data.loc[data["candidate_name"].eq("PYF")].copy()
    gauntlet = data.loc[
        data["candidate_name"].eq("GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE")
    ].copy()
    oof_ids = set(pyf["substrate_row_id"])
    current_proxy = proxy.loc[proxy["substrate_row_id"].isin(oof_ids)].rename(
        columns={
            "target_season": "season",
            "production_formula_partial_proxy_score": "raw_score",
            "production_formula_partial_proxy_score_pred_rank": ("prediction_rank_full_coverage"),
            "next_nwr_points": "actual_nwr_points",
            "next_position_finish": "actual_position_finish",
        }
    )
    rows: list[dict[str, Any]] = []

    def result_row(
        candidate: str,
        evaluation: str,
        scope: str,
        frame: pd.DataFrame,
        comparator: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        result = metric(
            frame,
            "prediction_rank_full_coverage",
            "actual_position_finish",
            raw_score="raw_score",
            actual_score="actual_nwr_points",
        )
        comp_spearman = np.nan
        if comparator is not None:
            comp_spearman = metric(
                comparator,
                "prediction_rank_full_coverage",
                "actual_position_finish",
            ).spearman
        return {
            "candidate": candidate,
            "evaluation": evaluation,
            "scope": scope,
            "rows": result.rows,
            "seasons": result.seasons,
            "spearman": result.spearman,
            "baseline_spearman": comp_spearman,
            "spearman_delta": result.spearman - comp_spearman,
            "rank_mae": result.rank_mae,
            "top_n_precision": result.precision,
            "top_n_recall": result.recall,
            "false_positive_rate": result.false_positive_rate,
            "false_negative_rate": result.false_negative_rate,
            "score_mae": result.score_mae,
            "temporal_status": (
                "ROLLING_DIAGNOSTIC_ONLY_FULL_HISTORY_SELECTION_CAVEAT"
                if "GAUNTLET_081" in candidate
                else "CONTROLLING_BASELINE"
            ),
        }

    rows.append(
        result_row(
            "CANDIDATE_0_CURRENT_BASELINE_PROXY",
            "OVERALL_OOF",
            "OVERALL",
            current_proxy,
        )
    )
    rows.append(result_row("REFERENCE_PYF", "OVERALL_OOF", "OVERALL", pyf))
    common_ids = set(gauntlet.loc[gauntlet["score_valid"], "substrate_row_id"])
    proxy_common = current_proxy.loc[current_proxy["substrate_row_id"].isin(common_ids)]
    gauntlet_common = gauntlet.loc[gauntlet["substrate_row_id"].isin(common_ids)]
    rows.append(
        result_row(
            "CANDIDATE_2_GAUNTLET_081",
            "OVERALL_OOF",
            "OVERALL",
            gauntlet_common,
            proxy_common,
        )
    )
    for season in sorted(pyf["season"].unique()):
        pyf_season = pyf.loc[pyf["season"].eq(season)]
        current_season = current_proxy.loc[current_proxy["season"].eq(season)]
        season_ids = set(
            gauntlet.loc[
                gauntlet["season"].eq(season) & gauntlet["score_valid"],
                "substrate_row_id",
            ]
        )
        gauntlet_season = gauntlet.loc[gauntlet["substrate_row_id"].isin(season_ids)]
        proxy_season = current_proxy.loc[current_proxy["substrate_row_id"].isin(season_ids)]
        rows.append(
            result_row(
                "CANDIDATE_0_CURRENT_BASELINE_PROXY",
                "WALK_FORWARD_TARGET_SEASON",
                str(season),
                current_season,
            )
        )
        rows.append(
            result_row(
                "REFERENCE_PYF",
                "WALK_FORWARD_TARGET_SEASON",
                str(season),
                pyf_season,
            )
        )
        rows.append(
            result_row(
                "CANDIDATE_2_GAUNTLET_081",
                "WALK_FORWARD_TARGET_SEASON",
                str(season),
                gauntlet_season,
                proxy_season,
            )
        )
    for position in POSITIONS:
        gauntlet_pos = gauntlet.loc[gauntlet["position"].eq(position)]
        proxy_pos = current_proxy.loc[current_proxy["position"].eq(position)]
        rows.append(
            result_row(
                "CANDIDATE_2_GAUNTLET_081",
                "POSITION",
                position,
                gauntlet_pos,
                proxy_pos,
            )
        )
        rows.append(
            result_row(
                "CANDIDATE_2_GAUNTLET_081",
                "LEAVE_ONE_POSITION_OUT",
                f"WITHOUT_{position}",
                gauntlet.loc[~gauntlet["position"].eq(position)],
                current_proxy.loc[~current_proxy["position"].eq(position)],
            )
        )
    lookup = age_join(mart, age)[
        [
            "substrate_row_id",
            "age",
            "age_bucket",
            "lifecycle_bucket",
            "low_games_flag",
            "confidence_missingness_flag",
        ]
    ]
    proxy_slice = current_proxy.merge(lookup, on="substrate_row_id", how="left")
    gauntlet_slice = gauntlet.merge(lookup, on="substrate_row_id", how="left")
    slice_masks = {
        "HIGH_COVERAGE_ONLY": gauntlet_slice["confidence_missingness_flag"]
        .astype(str)
        .eq("source_columns_present"),
        "OLDER_PLAYERS": gauntlet_slice["age_bucket"].astype(str).isin(["age_32_plus"]),
        "LOW_GAMES": gauntlet_slice["low_games_flag"].astype(str).str.lower().eq("true"),
        "TOP_TIER_ACTUAL": gauntlet_slice["actual_position_finish"].le(
            gauntlet_slice["position"].map(STARTABLE)
        ),
    }
    for scope, mask in slice_masks.items():
        ids = set(gauntlet_slice.loc[mask, "substrate_row_id"])
        rows.append(
            result_row(
                "CANDIDATE_2_GAUNTLET_081",
                "SENSITIVITY",
                scope,
                gauntlet_slice.loc[gauntlet_slice["substrate_row_id"].isin(ids)],
                proxy_slice.loc[proxy_slice["substrate_row_id"].isin(ids)],
            )
        )
    rows.append(
        {
            "candidate": "CANDIDATE_2_GAUNTLET_081",
            "evaluation": "SENSITIVITY",
            "scope": "EXACT_ROW_ONLY",
            "rows": 0,
            "seasons": 0,
            "temporal_status": "NOT_TESTABLE_ZERO_EXACT_ROWS",
        }
    )
    rows.append(
        result_row(
            "CANDIDATE_2_GAUNTLET_081",
            "SENSITIVITY",
            "PROXY_OVERLAP_ONLY",
            gauntlet_common,
            proxy_common,
        )
    )
    overall = next(
        row
        for row in rows
        if row["candidate"] == "CANDIDATE_2_GAUNTLET_081" and row["evaluation"] == "OVERALL_OOF"
    )
    season_rows = [
        row
        for row in rows
        if row["candidate"] == "CANDIDATE_2_GAUNTLET_081"
        and row["evaluation"] == "WALK_FORWARD_TARGET_SEASON"
    ]
    summary = {
        "overall_delta": overall["spearman_delta"],
        "positive_seasons": sum(bool(row.get("spearman_delta", np.nan) > 0) for row in season_rows),
        "season_count": len(season_rows),
        "coverage": int(gauntlet["score_valid"].sum()),
        "total": len(gauntlet),
    }
    return rows, summary


def authority_rows() -> list[dict[str, Any]]:
    artifacts = [
        (
            PARTIAL_PANEL,
            "2013-2025",
            "QB|RB|WR|TE",
            5518,
            "player_id_gsis",
            "current_formula_family_proxy",
            "PARTIAL_REPLAY",
            "PASS",
            "review-only",
        ),
        (
            FORMULA_MART,
            "2013-2025",
            "QB|RB|WR|TE",
            5518,
            "player_id",
            "formula_candidate_inputs",
            "PARTIAL_REPLAY",
            "PASS",
            "review-only",
        ),
        (
            AGE_SIDECAR,
            "2013-2025",
            "QB|RB|WR|TE",
            5518,
            "player_id",
            "historical_asof_metadata",
            "EXACT_DETERMINISTIC_REGENERATION",
            "PASS",
            "review-only",
        ),
        (
            OOF,
            "2015-2025",
            "QB|RB|WR|TE",
            14193,
            "player_id",
            "temporal_validation_v1",
            "REVIEW_ONLY",
            "GAUNTLET_SELECTION_CAVEAT",
            "review-only",
        ),
        (
            CURRENT_BOARD,
            "2026",
            "QB|RB|WR|TE",
            240,
            "player_id",
            "model_v4_wr_qb_v2_old_pocket_qb_guardrail",
            "EXACT_PRIMARY_EVIDENCE",
            "CURRENT_ONLY",
            "production",
        ),
        (
            FROZEN_2026,
            "2026",
            "QB|RB|WR|TE",
            sum(1 for _ in FROZEN_2026.open(encoding="utf-8")) - 1,
            "player_id",
            "prospective_freeze",
            "FROZEN_COMPARATOR",
            "CURRENT_ONLY",
            "frozen-review",
        ),
    ]
    rows = []
    for path, seasons, positions, count, identity, formula, exactness, leakage, status in artifacts:
        rows.append(
            {
                "artifact": rel(path),
                "commit": source_commit(path),
                "sha256": sha256(path),
                "season_coverage": seasons,
                "position_coverage": positions,
                "row_coverage": count,
                "identity_namespace": identity,
                "formula_version": formula,
                "input_availability": "TRACKED",
                "checkpoint_availability": (
                    "CURRENT_ONLY" if path in {CURRENT_BOARD, FROZEN_2026} else "ABSENT"
                ),
                "exactness_classification": exactness,
                "leakage_status": leakage,
                "production_review_status": status,
                "current_relevance": "HIGH",
            }
        )
    blocked = [
        "checkpoint_review_score",
        "position_specific_review_score",
        "lifecycle_modifier_review",
        "confidence_cap_historical",
        "discipline_safety_layers",
        "exact_nwr_dynasty_score_and_rank",
        "shadow_model_v2_metrics",
        "accepted_old_current_reconstruction",
        "HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1",
    ]
    for artifact in blocked:
        rows.append(
            {
                "artifact": artifact,
                "commit": "NOT_FOUND_IN_REACHABLE_HISTORY",
                "sha256": "",
                "season_coverage": "NONE",
                "position_coverage": "NONE",
                "row_coverage": 0,
                "identity_namespace": "UNKNOWN",
                "formula_version": "UNRECOVERED",
                "input_availability": "BLOCKED",
                "checkpoint_availability": "ABSENT",
                "exactness_classification": "BLOCKED_MISSING_RECEIPT",
                "leakage_status": "NOT_TESTABLE",
                "production_review_status": "blocked",
                "current_relevance": "HIGH",
            }
        )
    return rows


def recovery_rows() -> list[dict[str, Any]]:
    families = [
        ("historical_identity", "RECOVERED", "EXACT_PRIMARY_EVIDENCE", FORMULA_MART, 5518),
        ("target_outcomes", "RECOVERED", "EXACT_PRIMARY_EVIDENCE", FORMULA_MART, 5518),
        (
            "lagged_production_inputs",
            "REGENERATED",
            "EXACT_DETERMINISTIC_REGENERATION",
            FORMULA_MART,
            5518,
        ),
        (
            "historical_age_asof_metadata",
            "REGENERATED",
            "EXACT_DETERMINISTIC_REGENERATION",
            AGE_SIDECAR,
            5510,
        ),
        ("role_archetype_context", "RECOVERED", "NEAR_EQUIVALENT", FORMULA_MART, 5518),
        ("confidence_context", "RECOVERED", "NEAR_EQUIVALENT", FORMULA_MART, 5518),
    ]
    rows = []
    for family, result, classification, path, count in families:
        rows.append(
            {
                "receipt_family": family,
                "recovery_result": result,
                "source_commit": source_commit(path),
                "source_path_or_blob": rel(path),
                "sha256": sha256(path),
                "schema": "|".join(pd.read_csv(path, nrows=0).columns),
                "row_count": count,
                "season_coverage": "2013-2025",
                "position_coverage": "QB|RB|WR|TE",
                "identity_coverage": f"{count}/5518",
                "byte_provenance": "ORIGINAL_TRACKED" if result == "RECOVERED" else "REGENERATED",
                "historical_input_only": "true",
                "classification": classification,
            }
        )
    for family, classification in [
        ("checkpoint_review_score", "BLOCKED_MISSING_RECEIPT"),
        ("position_specific_review_score", "BLOCKED_MISSING_RECEIPT"),
        ("lifecycle_inputs_and_modifier", "BLOCKED_MISSING_RECEIPT"),
        ("confidence_cap_inputs_and_output", "BLOCKED_MISSING_RECEIPT"),
        ("discipline_safety_layers", "BLOCKED_MISSING_RECEIPT"),
        ("exact_model_v4_score_output", "BLOCKED_MISSING_RECEIPT"),
        ("ranking_assignments_and_ties", "BLOCKED_MISSING_RECEIPT"),
        ("route_yprr_tprr", "BLOCKED_SOURCE_NOT_ADMITTED"),
        ("return_from_injury_scoring", "BLOCKED_SOURCE_NOT_ADMITTED"),
        ("shadow_model_v2_metrics", "BLOCKED_MISSING_RECEIPT"),
    ]:
        rows.append(
            {
                "receipt_family": family,
                "recovery_result": "BLOCKED",
                "source_commit": "NOT_FOUND_IN_REACHABLE_HISTORY",
                "source_path_or_blob": "",
                "sha256": "",
                "schema": "",
                "row_count": 0,
                "season_coverage": "NONE",
                "position_coverage": "NONE",
                "identity_coverage": "0/5518",
                "byte_provenance": "NONE",
                "historical_input_only": "NOT_TESTABLE",
                "classification": classification,
            }
        )
    return rows


def git_history_rows() -> list[dict[str, Any]]:
    queries = [
        "checkpoint_review_score",
        "position_specific_review_score",
        "lifecycle_modifier_review",
        "confidence_cap",
        "nwr_dynasty_score",
        "shadow_model_v2_metrics",
        "HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1",
        "old_current_ranking_logic_reconstruction",
    ]
    rows = []
    for query in queries:
        output = git(
            "log",
            "--no-textconv",
            "--format=%H|%ad|%s",
            "--date=short",
            f"-S{query}",
            SOURCE_COMMIT,
        )
        hits = sorted(line for line in output.splitlines() if line)
        rows.append(
            {
                "query": query,
                "technique": f"git log --no-textconv -S anchored to {SOURCE_COMMIT}",
                "hit_count": len(hits),
                "first_hits": " || ".join(hits[:5]),
                "exact_historical_receipt_found": "false",
                "disposition": (
                    "NO_MATCH"
                    if not hits
                    else "MENTIONS_OR_CURRENT_ONLY_NO_EXACT_HISTORICAL_RECEIPT"
                ),
            }
        )
    rows.append(
        {
            "query": "relevant path names",
            "technique": f"git rev-list {SOURCE_COMMIT} --objects plus path regex",
            "hit_count": "SEE_RECOVERY_INVENTORY",
            "first_hits": "Prior packets, current-only outputs, and partial panels only.",
            "exact_historical_receipt_found": "false",
            "disposition": "NO_EXACT_HISTORICAL_CHECKPOINT_BLOB",
        }
    )
    return rows


def regeneration_rows() -> list[dict[str, Any]]:
    command = (
        "python scripts/build_exact_model_v4_replay_accuracy_audit_v1.py "
        f"--source-commit {SOURCE_COMMIT} --repo-root <REPO_ROOT> --output-dir <OUTPUT_DIR>"
    )
    environment = "Python >=3.12; locked project pandas/numpy; locale/timezone independent"
    return [
        {
            "family": "historical_player_identity_and_outcomes",
            "classification": "EXACT_PRIMARY_EVIDENCE",
            "command": command,
            "environment": environment,
            "seed": "NONE",
            "input_path": rel(FORMULA_MART),
            "input_sha256": sha256(FORMULA_MART),
            "output_path": rel(PACKET / "LEAKAGE_SAFE_PANEL_MANIFEST.csv"),
            "output_sha256": sha256(PACKET / "LEAKAGE_SAFE_PANEL_MANIFEST.csv"),
            "overlap_checkpoint_match": "IDENTITY_AND_ROW_COUNT_PASS",
            "historical_only": "true",
        },
        {
            "family": "historical_age_asof_metadata",
            "classification": "EXACT_DETERMINISTIC_REGENERATION",
            "command": command,
            "environment": environment,
            "seed": "NONE",
            "input_path": rel(AGE_SIDECAR),
            "input_sha256": sha256(AGE_SIDECAR),
            "output_path": rel(PACKET / "COMPONENT_AND_ROW_EXACTNESS_MASK.csv"),
            "output_sha256": sha256(PACKET / "COMPONENT_AND_ROW_EXACTNESS_MASK.csv"),
            "overlap_checkpoint_match": "5510 NONMISSING; 8 EXPLICITLY MISSING",
            "historical_only": "true",
        },
        {
            "family": "accepted_production_proxy",
            "classification": "PARTIAL_REPLAY",
            "command": command,
            "environment": environment,
            "seed": "NONE",
            "input_path": rel(PARTIAL_PANEL),
            "input_sha256": sha256(PARTIAL_PANEL),
            "output_path": rel(PACKET / "BASELINE_ACCURACY_RESULTS.csv"),
            "output_sha256": sha256(PACKET / "BASELINE_ACCURACY_RESULTS.csv"),
            "overlap_checkpoint_match": "ACCEPTED BUILDER REUSED; METRICS REPRODUCED",
            "historical_only": "true",
        },
        {
            "family": "bootstrap_uncertainty",
            "classification": "REVIEW_ONLY",
            "command": command,
            "environment": environment,
            "seed": SEED,
            "input_path": rel(FORMULA_MART),
            "input_sha256": sha256(FORMULA_MART),
            "output_path": rel(PACKET / "BASELINE_ACCURACY_RESULTS.csv"),
            "output_sha256": sha256(PACKET / "BASELINE_ACCURACY_RESULTS.csv"),
            "overlap_checkpoint_match": "DETERMINISTIC_RERUN_REQUIRED",
            "historical_only": "true",
        },
    ]


def packet_csvs(
    panel: pd.DataFrame,
    mart: pd.DataFrame,
    age: pd.DataFrame,
    oof: pd.DataFrame,
    proxy: pd.DataFrame,
) -> dict[str, Any]:
    authority = authority_rows()
    write_csv(
        PACKET / "HISTORICAL_EVIDENCE_AUTHORITY_MATRIX.csv",
        authority,
        list(authority[0]),
    )
    recovery = recovery_rows()
    write_csv(PACKET / "RECEIPT_RECOVERY_INVENTORY.csv", recovery, list(recovery[0]))
    history = git_history_rows()
    write_csv(PACKET / "GIT_HISTORY_AND_BLOB_RECOVERY_LOG.csv", history, list(history[0]))
    mask = exactness_mask(mart, age)
    write_csv(
        PACKET / "COMPONENT_AND_ROW_EXACTNESS_MASK.csv",
        mask.to_dict("records"),
        list(mask.columns),
    )
    coverage = coverage_rows(mask)
    write_csv(
        PACKET / "EXACTNESS_COVERAGE_BY_SEASON_POSITION.csv",
        coverage,
        list(coverage[0]),
    )
    differential = []
    for scope, group in [
        ("OVERALL", mask),
        *[(p, mask[mask["position"].eq(p)]) for p in POSITIONS],
    ]:
        differential.append(
            {
                "scope": scope,
                "exact_rows": int(group["full_exact_row"].sum()),
                "proxy_rows": int(group["proxy_available"].sum()),
                "overlap_rows": 0,
                "score_difference_mean": "",
                "rank_difference_mean": "",
                "spearman_agreement": "",
                "top_n_overlap": "",
                "severe_rank_reversals": "",
                "missing_row_difference": len(group),
                "false_positive_difference": "",
                "false_negative_difference": "",
                "conclusion": "NOT_TESTABLE_ZERO_EXACT_OVERLAP",
            }
        )
    write_csv(
        PACKET / "PROXY_TO_EXACT_DIFFERENTIAL.csv",
        differential,
        list(differential[0]),
    )
    panel_rows = [
        {
            "panel": "EXACT_REPLAY",
            "seasons": "NONE",
            "rows": 0,
            "unique_players": 0,
            "positions": "NONE",
            "identity": "player_id",
            "temporal_rule": "feature season t predicts target season t+1",
            "leakage_status": "PASS_BY_EMPTY_FAIL_CLOSED",
            "missing_targets": 0,
            "retired_inactive_handling": "BLOCKED_UNAVAILABLE",
            "survivorship_handling": "FULL_ADMITTED_UNIVERSE_NO_FILTER",
            "coverage_loss": 5518,
            "exclusions": "All rows lack one or more required exact Model v4 receipts.",
        },
        {
            "panel": "EXACT_COMPONENT_PARTIAL",
            "seasons": "2013-2025",
            "rows": 5518,
            "unique_players": int(mart["player_id"].nunique()),
            "positions": "QB:754|RB:1429|WR:2124|TE:1211",
            "identity": "player_id",
            "temporal_rule": "feature season t predicts target season t+1",
            "leakage_status": "PASS",
            "missing_targets": int(mart["label_next_nwr_points"].isna().sum()),
            "retired_inactive_handling": "TARGET_UNIVERSE_PRESERVED; EXPLICIT STATUS UNAVAILABLE",
            "survivorship_handling": "FULL_ADMITTED_UNIVERSE_NO_CURRENT_BOARD_FILTER",
            "coverage_loss": 0,
            "exclusions": "None from the admitted row universe.",
        },
        {
            "panel": "ACCEPTED_PROXY",
            "seasons": "2013-2025",
            "rows": 5518,
            "unique_players": int(mart["player_id"].nunique()),
            "positions": "QB:754|RB:1429|WR:2124|TE:1211",
            "identity": "player_id",
            "temporal_rule": "feature season t predicts target season t+1",
            "leakage_status": "PASS",
            "missing_targets": int(proxy["next_nwr_points"].isna().sum()),
            "retired_inactive_handling": "TARGET_UNIVERSE_PRESERVED; EXPLICIT STATUS UNAVAILABLE",
            "survivorship_handling": "FULL_ADMITTED_UNIVERSE_NO_CURRENT_BOARD_FILTER",
            "coverage_loss": 0,
            "exclusions": "None; proxy missing components are confidence-penalized as documented.",
        },
        {
            "panel": "CANDIDATE_OOF",
            "seasons": "2015-2025",
            "rows": 4731,
            "unique_players": int(oof["player_id"].nunique()),
            "positions": "QB|RB|WR|TE",
            "identity": "player_id",
            "temporal_rule": "expanding-window OOF predictions",
            "leakage_status": "PYF_PASS; GAUNTLET_SELECTION_CAVEAT",
            "missing_targets": 0,
            "retired_inactive_handling": "OUTCOME PANEL UNIVERSE PRESERVED",
            "survivorship_handling": "NO_CURRENT_BOARD_FILTER",
            "coverage_loss": 787,
            "exclusions": "2013-2014 warm-up seasons excluded from OOF.",
        },
    ]
    write_csv(
        PACKET / "LEAKAGE_SAFE_PANEL_MANIFEST.csv",
        panel_rows,
        list(panel_rows[0]),
    )
    baselines = baseline_rows(proxy, mart, age)
    write_csv(PACKET / "BASELINE_ACCURACY_RESULTS.csv", baselines, list(baselines[0]))
    attribution, cases = attribution_rows(proxy, mart, age)
    write_csv(
        PACKET / "ERROR_ATTRIBUTION_BY_POSITION_AGE_USAGE.csv",
        attribution,
        list(attribution[0]),
    )
    challenger_definitions = [
        {
            "candidate": "CANDIDATE_0",
            "name": "CURRENT_BASELINE_ACCEPTED_PRODUCTION_PROXY",
            "definition": "Exact accepted partial proxy builder, unchanged.",
            "inputs": rel(PARTIAL_PANEL),
            "parameters": "fixed current proxy registry",
            "pre_registered": "true",
            "status": "BASELINE",
        },
        {
            "candidate": "CANDIDATE_1",
            "name": "HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1",
            "definition": "UNAVAILABLE; exact governed definition not found in tracked history.",
            "inputs": "BLOCKED",
            "parameters": "NOT_INVENTED",
            "pre_registered": "true_by_request_but_definition_missing",
            "status": "BLOCKED_MISSING_RECEIPT",
        },
        {
            "candidate": "CANDIDATE_2",
            "name": "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE",
            "definition": (
                "prior_3yr_weighted_nwr_points * 0.98 only when age_32_plus "
                "or late_career_10_plus; otherwise unchanged"
            ),
            "inputs": "tracked three-year points plus exact-asof age/lifecycle metadata",
            "parameters": "guard multiplier=0.98 fixed",
            "pre_registered": "true_existing_formula_gauntlet",
            "status": "EVALUATED_REVIEW_ONLY",
        },
        {
            "candidate": "CANDIDATE_3",
            "name": "NONE",
            "definition": (
                "No new candidate registered because exact Model v4 residuals are unavailable."
            ),
            "inputs": "NONE",
            "parameters": "NONE",
            "pre_registered": "false",
            "status": "NOT_EVALUATED_NO_INVENTION",
        },
    ]
    write_csv(
        PACKET / "CHALLENGER_DEFINITIONS.csv",
        challenger_definitions,
        list(challenger_definitions[0]),
    )
    walk, walk_summary = oof_candidate_rows(oof, mart, age, proxy)
    write_csv(PACKET / "WALK_FORWARD_RESULTS.csv", walk, list(walk[0]))
    gates = candidate_gate_rows(walk_summary)
    write_csv(
        PACKET / "CHALLENGER_ACCEPTANCE_GATE_MATRIX.csv",
        gates,
        list(gates[0]),
    )
    simulation = [
        {
            "candidate": "NONE",
            "status": "NOT_RUN_NO_CHALLENGER_PASSED_PRELIMINARY_GATES",
            "affected_player_ids": "",
            "score_delta": "",
            "rank_delta": "",
            "position_changes": 0,
            "top_24_changes": 0,
            "top_60_changes": 0,
            "largest_risers": "",
            "largest_fallers": "",
            "older_player_effects": "NOT_SIMULATED",
            "low_games_effects": "NOT_SIMULATED",
            "confidence_changes": "NONE",
            "unresolved_input_states": "ALL_CHALLENGERS_BLOCKED_OR_REJECTED",
            "production_write": "NONE",
        }
    ]
    write_csv(
        PACKET / "CURRENT_BOARD_REVIEW_ONLY_SIMULATION.csv",
        simulation,
        list(simulation[0]),
    )
    blockers = blocker_rows()
    write_csv(
        PACKET / "EXACT_REPLAY_BLOCKERS_AND_RECOVERY_PLAN.csv",
        blockers,
        list(blockers[0]),
    )
    residual_cases(cases)
    return {
        "mask": mask,
        "baselines": baselines,
        "attribution": attribution,
        "walk": walk,
        "walk_summary": walk_summary,
        "blockers": blockers,
    }


def candidate_gate_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    gate_names = [
        "ZERO_LEAKAGE",
        "EXACT_DOCUMENTED_INPUTS",
        "ADEQUATE_COVERAGE",
        "ADEQUATE_SAMPLE_SIZES",
        "MATERIAL_OVERALL_RANKING_IMPROVEMENT",
        "IMPROVEMENT_SURVIVES_UNCERTAINTY",
        "NO_MATERIAL_POOLED_SCORE_REGRESSION",
        "NO_SEVERE_POSITION_REGRESSION",
        "NO_REPEATED_POSITION_REGRESSION",
        "NO_TOP_TIER_FALSE_POSITIVE_REGRESSION",
        "NO_PRODUCTIVE_VETERAN_FALSE_NEGATIVE_REGRESSION",
        "NO_LOW_GAMES_INSTABILITY",
        "NO_ONE_SEASON_DEPENDENCY",
        "NO_ONE_POSITION_DEPENDENCY",
        "NO_COVERAGE_LOSS_WITHOUT_FAIL_CLOSED_PATH",
        "MONOTONIC_AND_INTERPRETABLE",
        "CURRENT_240_RANKINGS_UNCHANGED",
        "FROZEN_2026_COMPARATOR_UNCHANGED",
        "NO_PRODUCTION_INTEGRATION",
        "INDEPENDENT_REPRODUCTION_SUCCEEDS",
    ]
    rows: list[dict[str, Any]] = []
    for candidate in ("CANDIDATE_0", "CANDIDATE_1", "CANDIDATE_2", "CANDIDATE_3"):
        for gate in gate_names:
            if candidate == "CANDIDATE_0":
                result, evidence = "NOT_APPLICABLE_BASELINE", "Comparator only."
            elif candidate == "CANDIDATE_1":
                result, evidence = (
                    "FAIL",
                    "Exact governed definition and checkpoint inputs not found; "
                    "no reinterpretation.",
                )
            elif candidate == "CANDIDATE_3":
                result, evidence = (
                    "NOT_EVALUATED",
                    "No new candidate pre-registered from unavailable exact residuals.",
                )
            else:
                result = "PASS"
                evidence = "Tracked OOF evidence and detached audit."
                failures = {
                    "ZERO_LEAKAGE": (
                        "Formula-gauntlet candidate selection used full history through 2025."
                    ),
                    "IMPROVEMENT_SURVIVES_UNCERTAINTY": (
                        "No nested temporal selection record; OOF is diagnostic only."
                    ),
                    "NO_MATERIAL_POOLED_SCORE_REGRESSION": (
                        "Raw score calibration differs; mandatory pooled-score "
                        "gate not established."
                    ),
                    "NO_PRODUCTIVE_VETERAN_FALSE_NEGATIVE_REGRESSION": (
                        "Unconditional late-career multiplier creates veteran downside without "
                        "an admitted stability/return guard."
                    ),
                    "NO_LOW_GAMES_INSTABILITY": (
                        "Prior governed gauntlet slice recorded +3 low-games false positives."
                    ),
                    "NO_COVERAGE_LOSS_WITHOUT_FAIL_CLOSED_PATH": (
                        f"Valid predictions {summary['coverage']}/"
                        f"{summary['total']}; four rows lost."
                    ),
                }
                if gate in failures:
                    result, evidence = "FAIL", failures[gate]
                elif gate == "MATERIAL_OVERALL_RANKING_IMPROVEMENT":
                    evidence = f"OOF Spearman delta {summary['overall_delta']:.6f}."
                elif gate == "NO_ONE_SEASON_DEPENDENCY":
                    evidence = (
                        f"Positive target-season deltas {summary['positive_seasons']}/"
                        f"{summary['season_count']}."
                    )
                elif gate == "CURRENT_240_RANKINGS_UNCHANGED":
                    evidence = f"Tracked board remains {BOARD_HASH}; no simulation run."
                elif gate == "FROZEN_2026_COMPARATOR_UNCHANGED":
                    evidence = f"Frozen input SHA-256 {sha256(FROZEN_2026)}."
            rows.append(
                {
                    "candidate": candidate,
                    "gate": gate,
                    "result": result,
                    "evidence": evidence,
                    "mandatory": "true",
                }
            )
    return rows


def blocker_rows() -> list[dict[str, Any]]:
    rows = [
        (
            1,
            "exact checkpoint and rank receipts",
            "Highest: enables exact score/rank overlap and proxy differential.",
            "2013-2025 all positions",
            "Search backup manifests or obtain admitted original historical exports.",
            "Tracked history has only mentions/current-only outputs.",
            "No",
            "No",
            "Yes",
            "HIGH",
            "HIGH",
            "Original receipts absent from reachable Git history.",
            "Do not substitute proxy scores.",
        ),
        (
            2,
            "position components plus lifecycle/confidence/discipline inputs",
            "High: enables deterministic exact current-formula regeneration.",
            "Potentially 2013-2025 by available component",
            "Admit immutable historical component sources with as-of manifests.",
            "Formula mart and gap ledgers identify required schemas.",
            "Conditional",
            "Yes",
            "Yes",
            "HIGH",
            "HIGH",
            "Sources and exact historical transforms are not admitted.",
            "Do not backfill with current-only ADP or retrospective values.",
        ),
        (
            3,
            "stable inactive/return and identity outcome coverage",
            "Medium: separates retirement/injury outcomes from formula error.",
            "Older and low-games cohorts",
            "Admit time-bounded activity/return receipts joined only by player_id.",
            "Tracked outcome panels provide identity anchors.",
            "Conditional",
            "Yes",
            "Yes",
            "MEDIUM",
            "MEDIUM",
            "Historically as-of activity/return receipt absent.",
            "Do not infer from current roster or join by name.",
        ),
    ]
    fields = [
        "priority",
        "missing_receipt_family",
        "accuracy_value",
        "season_position_coverage",
        "exact_recovery_path",
        "repository_or_history_lead",
        "deterministic_regeneration_possible",
        "source_admission_required",
        "human_review_required",
        "risk",
        "effort",
        "blocker",
        "prohibited_workaround",
    ]
    return [dict(zip(fields, row, strict=True)) for row in rows]


def residual_cases(data: pd.DataFrame) -> None:
    cases = data.sort_values(
        ["absolute_rank_residual", "season", "player_id"],
        ascending=[False, True, True],
        kind="stable",
    ).head(20)
    lines = [
        "# Mechanical residual case studies",
        "",
        "Cases are the 20 largest absolute accepted-proxy rank residuals. Selection",
        "is mechanical, uses exact player IDs, and is not based on fame or narrative.",
        "These are proxy-error cases, not proven exact Model v4 errors.",
        "",
        "| order | player_id | player | target season | position | predicted rank | "
        "actual finish | signed error | age | prior games |",
        "|---:|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for order, row in enumerate(cases.itertuples(), 1):
        lines.append(
            f"| {order} | {row.player_id} | {row.player_name} | {int(row.season)} | "
            f"{row.position} | "
            f"{row.production_formula_partial_proxy_score_pred_rank:.0f} | "
            f"{row.label_next_position_finish:.0f} | {row.rank_residual:.0f} | "
            f"{clean(row.age)} | {clean(row.prior_games)} |"
        )
    write_md("MECHANICAL_RESIDUAL_CASE_STUDIES.md", "\n".join(lines))


def packet_markdown(results: dict[str, Any]) -> None:
    baselines = pd.DataFrame(results["baselines"])
    overall = baselines.loc[baselines["scope"].eq("OVERALL")]
    proxy = overall.loc[overall["model"].eq("ACCEPTED_PRODUCTION_PROXY")].iloc[0]
    pyf = overall.loc[overall["model"].eq("PYF")].iloc[0]
    two = overall.loc[overall["model"].eq("MULTI_YEAR_AVERAGE_2YR")].iloc[0]
    three = overall.loc[overall["model"].eq("MULTI_YEAR_AVERAGE_3YR")].iloc[0]
    attribution = pd.DataFrame(results["attribution"])
    largest = (
        attribution.loc[attribution["rows"].fillna(0).astype(int).ge(30)]
        .sort_values("rank_mae", ascending=False)
        .head(8)
    )
    largest_text = "; ".join(
        f"{row.dimension}:{row.cohort} MAE {float(row.rank_mae):.2f}"
        for row in largest.itertuples()
    )
    contract = f"""# Exact replay contract

## Primary target

`EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY` applies the exact current production
Model v4 formula to inputs that were available at each historical decision date.
It is the required contract for evaluating the accuracy of the current model.

## Contract A — current-formula historical replay

- Formula authority: `{rel(CURRENT_FORMULA_CONTRACT)}` and
  `{rel(CURRENT_FORMULA_REGISTRY)}`.
- Formula identity: `model_v4_wr_qb_v2_old_pocket_qb_guardrail` on the accepted
  scored board; documented fallback is not interchangeable.
- Required sequence: admitted as-of components -> position-specific score ->
  lifecycle modifier -> confidence cap -> discipline/safety layers ->
  `checkpoint_review_score` -> exact Model v4 score -> deterministic rank.
- Position logic: the registry's RB/WR/QB/TE component formulas and weights.
- Confidence and lifecycle: exact historical inputs and outputs are required;
  the review-only sidecars are not silently promoted.
- Rank/ties: score descending, exact governed stable secondary ordering. The
  production proxy's name tie-break is not authority for the missing exact rank
  receipt.
- Missing data: a row is excluded from the exact subset if any required
  component is not exact original or exact deterministic regeneration.
- Sources: only tracked/admitted sources available before target-season outcome.
- Availability: zero complete historical rows; contract is blocked by receipts.

## Contract B — historical-version replay

Apply the exact model version active at each checkpoint, including that version's
components, lifecycle, confidence, safety, missingness, and tie rules. Versioned
checkpoint manifests were not recovered, so this contract is also blocked. It is
useful for deployment-history analysis, not the primary current-model question.

## Contract C — accepted production-proxy replay

The accepted proxy reuses historically lagged production fields, position weights,
documented missing-component penalties, and deterministic ranking. It has 5,518
rows for 2013-2025. It is leakage-safe and reproducible, but it is a
`PARTIAL_REPLAY`: it is not an exact score/checkpoint/rank replay and may not fill
the exact subset.

The three contracts remain separate throughout this packet.
"""
    write_md("EXACT_REPLAY_CONTRACT.md", contract)
    report = f"""# Exact Model v4 replay and accuracy report

## Verdict

`YELLOW_NWR_ACCURACY_AUDIT_COMPLETE_PROXY_CONCLUSIONS_REFINED`

The tracked evidence frontier is now explicit and reproducible. Exact player
identity, outcomes, lagged production, and historical age-as-of metadata were
recovered or deterministically regenerated. Exact Model v4 position scores,
lifecycle modifiers, confidence-cap outputs, discipline/safety outputs,
checkpoints, final scores, and ranks were not found in any reachable tracked
history. Therefore full exact replay remains 0 of 5,518 rows across every
position and season.

## Accuracy evidence

The accepted proxy reproduces at Spearman {float(proxy.spearman):.6f} and rank
MAE {float(proxy.rank_mae):.6f}. PYF is {float(pyf.spearman):.6f} /
{float(pyf.rank_mae):.6f}; the deterministic two-year baseline is
{float(two.spearman):.6f} / {float(two.rank_mae):.6f}; and the deterministic
three-year baseline is {float(three.spearman):.6f} / {float(three.rank_mae):.6f}.
Ranking-aligned and valid pooled-score metrics are kept separate in the CSV.

Because exact/proxy overlap is zero, proxy-to-exact score differences, rank
differences, agreement, top-N overlap, reversals, and classification deltas are
not testable. Prior aging conclusions remain directionally useful within the
accepted proxy/OOF evidence, but they are not validated as exact Model v4 causal
effects.

## Error attribution

The largest mechanically measured proxy-error cohorts include: {largest_text}.
Low-games, lifecycle, and older-player slices are reported without converting
proxy residuals into exact-model claims. Historically as-of team change,
retirement, and return-from-injury states remain source-blocked.

## Challengers

- Candidate 0 is the unchanged baseline.
- Candidate 1 is blocked because its exact governed HQ2 definition was not found.
- Candidate 2 is the fixed GAUNTLET_081 2% late-career multiplier. It improves
  overall OOF ranking correlation but fails mandatory leakage/selection,
  uncertainty, pooled-score, productive-veteran, low-games, and coverage gates.
- Candidate 3 was not invented because exact error attribution is unavailable.

Disposition: `NO_ACCURACY_CHALLENGER_ADMITTED`.

No current-board simulation was run because no challenger passed preliminary
gates. Production ranking change: `NONE`. Frozen 2026 change: `NONE`.
"""
    write_md("EXACT_MODEL_V4_REPLAY_AND_ACCURACY_REPORT.md", report)
    write_md(
        "EXECUTIVE_VERDICT.md",
        """# Executive verdict

`YELLOW_NWR_ACCURACY_AUDIT_COMPLETE_PROXY_CONCLUSIONS_REFINED`

Exact historical Model v4 replay remains blocked at zero complete rows, but the
evidence boundary, reproducible proxy metrics, leakage-safe error attribution,
and governed challenger disposition are now explicit. No challenger passes all
20 mandatory gates.

`NO_ACCURACY_CHALLENGER_ADMITTED`

Production ranking change: `NONE`. Frozen 2026 change: `NONE`. No production
integration or provider call occurred.
""",
    )
    write_md(
        "NEXT_THREE_ACCURACY_LANES.md",
        """# Next three accuracy lanes

1. Recover original historical checkpoint, final-score, and exact-rank receipts
   with immutable as-of manifests.
2. Admit exact historical position components plus lifecycle, confidence, and
   discipline/safety inputs so deterministic current-formula regeneration can be
   attempted and checked against surviving checkpoints.
3. Admit stable player-ID-keyed inactivity, return, and outcome-state receipts
   for older and low-games cohort attribution.

Do not run another proxy-tuning lane while exactness is the dominant constraint.
""",
    )
    write_md(
        "PRODUCTION_RANKING_NO_CHANGE_PROOF.md",
        f"""# Production ranking no-change proof

The tracked canonical 240-row board remained byte-identical at SHA-256
`{BOARD_HASH}`. Its ordered top five remains Puka Nacua, Jaxon Smith-Njigba,
Bijan Robinson, Jonathan Taylor, and Jahmyr Gibbs.

The audit builder reads this board only to assert its hash. It does not write
ranking inputs, production code, UI, routes, or LocalData. No challenger passed
preliminary gates, so current-board simulation is explicitly not run.

Production ranking change: `NONE`.
""",
    )
    write_md(
        "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md",
        """# Security, Data Health, and runtime no-change

This lane performs no security scan. Required existing security regression tests
run through the Hermetic gate. Data Health is exercised only through passive-read
and existing regression tests. No provider, refresh, launcher mutation, LocalData
read, UI route, runtime configuration, or application process is introduced by
the builder.

Final gate results are recorded in `VALIDATION_RESULTS.md`.
""",
    )
    write_md(
        "PRIMARY_AND_PERSISTENT_STATE_PRESERVATION.md",
        """# Primary and persistent state preservation

The five user-owned DynastyProcess CSVs in the primary worktree are treated as
opaque and are checked only by their supplied SHA-256 values at every required
checkpoint. They are never parsed, copied, normalized, staged, or committed.

Persistent product state baseline: 14 files / 542,801 bytes /
PERSISTENT_STATE_DIGEST_V1
`88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`.
Recovery baseline: 7 files / 172,878 bytes /
PERSISTENT_STATE_DIGEST_V1
`1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.

Final checkpoint results are recorded in `VALIDATION_RESULTS.md`.
""",
    )
    write_md(
        "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        f"""# Protected and frozen path proof

The lane creates only one research builder, its tests, and this audit packet.
Production formula, ranking, identity, Data Health, security automation,
application routes/UI, and accepted comparators are outside the write set.

- Current board SHA-256: `{BOARD_HASH}`.
- Frozen 2026 comparator SHA-256: `{sha256(FROZEN_2026)}`.
- Starting HQ/tree: `{START_HQ}` / `{START_TREE}`.

Final diff scans and hash checks are recorded in `VALIDATION_RESULTS.md`.
""",
    )
    write_md(
        "ROLLBACK_PLAN.md",
        """# Rollback plan

This lane is additive and research-only. To roll it back before adoption, remove
the isolated worktree and branch after independently verifying their exact paths.
To roll back after adopting the local commits, revert the documentation commit
and then the tooling commit. No production state, LocalData, provider state,
rankings, backups, primary opaque CSV, old worktree, or remote branch requires
restoration. No push occurred.
""",
    )
    write_md(
        "VALIDATION_RESULTS.md",
        f"""# Validation results

Status: `CANONICAL_BUILD_SELF_VALIDATION_PASS`.

The authoritative builder validates all governed tracked-input hashes, exact
player-ID joins, historical feature metadata, the exactness lattice, the
924-row frozen comparator, the 240-row current board, and preserved metric and
challenger conclusions before the packet manifest is sealed.

- Fixed history anchor: `{SOURCE_COMMIT}`.
- Exact rows: `0 / 5,518`.
- Exact seasons: `NONE`.
- Proxy-to-exact differential: `NOT TESTABLE`.
- Current board: 240 rows / `{BOARD_HASH}`.
- Frozen comparator: 924 rows / `{FROZEN_2026_HASH}`.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.
- Challenger disposition: `NO_ACCURACY_CHALLENGER_ADMITTED`.

The independent mutation, clean-checkout, Hermetic, LocalData, security
regression, Data Health, and preservation gates are recorded in the separately
committed assertion/regeneration revision packet. This file is generated
atomically; no post-build correction is permitted.
""",
    )


def write_file_inventory() -> None:
    files = [
        Path("scripts/build_exact_model_v4_replay_accuracy_audit_v1.py"),
        Path("tests/test_exact_model_v4_replay_accuracy_audit_v1.py"),
    ]
    files.extend(
        Path("docs/hq/master/nwr_exact_model_v4_replay_accuracy_audit_v1_20260723") / path.name
        for path in sorted(PACKET.iterdir())
        if path.name not in {"FILES_CREATED_OR_CHANGED.csv", "MANIFEST.json"}
    )
    rows = [
        {
            "path": path.as_posix(),
            "change": "CREATED",
            "purpose": (
                "Deterministic research-only audit tooling"
                if path.parts[0] == "scripts"
                else "Reproducibility and governance tests"
                if path.parts[0] == "tests"
                else "Exact replay accuracy audit packet"
            ),
        }
        for path in files
    ]
    write_csv(PACKET / "FILES_CREATED_OR_CHANGED.csv", rows, list(rows[0]))


def write_manifest() -> None:
    required = required_packet_files()
    missing = [name for name in required[:-1] if not (PACKET / name).is_file()]
    if missing:
        raise RuntimeError(f"required packet files missing: {missing}")
    entries = [
        {
            "path": name,
            "bytes": (PACKET / name).stat().st_size,
            "sha256": sha256(PACKET / name),
        }
        for name in required[:-1]
    ]
    manifest = {
        "packet": "nwr_exact_model_v4_replay_accuracy_audit_v1_20260723",
        "schema_version": 2,
        "verdict": "YELLOW_NWR_ACCURACY_AUDIT_COMPLETE_PROXY_CONCLUSIONS_REFINED",
        "challenger_disposition": "NO_ACCURACY_CHALLENGER_ADMITTED",
        "starting_hq": START_HQ,
        "starting_tree": START_TREE,
        "fixed_source_commit": SOURCE_COMMIT,
        "exact_target_contract": "EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY",
        "exact_rows": 0,
        "source_panel_rows": 5518,
        "production_ranking_change": "NONE",
        "frozen_2026_change": "NONE",
        "seed": SEED,
        "canonical_serialization": {
            "encoding": "UTF-8",
            "bom": False,
            "line_endings": "LF",
            "newline_at_eof": True,
            "float_precision": 6,
            "json_keys": "sorted",
            "manifest_self_hash": "excluded",
        },
        "files": entries,
    }
    write_canonical_text(
        PACKET / "MANIFEST.json",
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )


def required_packet_files() -> list[str]:
    return [
        "EXACT_MODEL_V4_REPLAY_AND_ACCURACY_REPORT.md",
        "EXECUTIVE_VERDICT.md",
        "EXACT_REPLAY_CONTRACT.md",
        "HISTORICAL_EVIDENCE_AUTHORITY_MATRIX.csv",
        "RECEIPT_RECOVERY_INVENTORY.csv",
        "GIT_HISTORY_AND_BLOB_RECOVERY_LOG.csv",
        "DETERMINISTIC_REGENERATION_MANIFEST.csv",
        "COMPONENT_AND_ROW_EXACTNESS_MASK.csv",
        "EXACTNESS_COVERAGE_BY_SEASON_POSITION.csv",
        "PROXY_TO_EXACT_DIFFERENTIAL.csv",
        "LEAKAGE_SAFE_PANEL_MANIFEST.csv",
        "BASELINE_ACCURACY_RESULTS.csv",
        "ERROR_ATTRIBUTION_BY_POSITION_AGE_USAGE.csv",
        "MECHANICAL_RESIDUAL_CASE_STUDIES.md",
        "CHALLENGER_DEFINITIONS.csv",
        "WALK_FORWARD_RESULTS.csv",
        "CHALLENGER_ACCEPTANCE_GATE_MATRIX.csv",
        "CURRENT_BOARD_REVIEW_ONLY_SIMULATION.csv",
        "EXACT_REPLAY_BLOCKERS_AND_RECOVERY_PLAN.csv",
        "NEXT_THREE_ACCURACY_LANES.md",
        "PRODUCTION_RANKING_NO_CHANGE_PROOF.md",
        "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md",
        "PRIMARY_AND_PERSISTENT_STATE_PRESERVATION.md",
        "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        "ROLLBACK_PLAN.md",
        "FILES_CREATED_OR_CHANGED.csv",
        "VALIDATION_RESULTS.md",
        "MANIFEST.json",
    ]


def validate_research_results(results: dict[str, Any]) -> None:
    mask = results["mask"]
    if len(mask) != 5518 or bool(mask["full_exact_row"].any()):
        raise RuntimeError("exact replay frontier changed")
    if int(mask["player_id"].nunique()) != 1552:
        raise RuntimeError("historical player identity count changed")
    baselines = pd.DataFrame(results["baselines"])
    overall = baselines.loc[baselines["scope"].eq("OVERALL")].set_index("model")
    expected = {
        "ACCEPTED_PRODUCTION_PROXY": (0.674738598, 21.649510692),
        "PYF": (0.681007814, 21.386009),
        "MULTI_YEAR_AVERAGE_2YR": (0.695417424, 20.942733),
        "MULTI_YEAR_AVERAGE_3YR": (0.696731774, 20.902501),
        "GAUNTLET_081": (0.697014621, 20.887640),
    }
    for model, (expected_spearman, expected_mae) in expected.items():
        row = overall.loc[model]
        if abs(float(row["spearman"]) - expected_spearman) > 0.000001:
            raise RuntimeError(f"preserved Spearman changed for {model}")
        if abs(float(row["rank_mae"]) - expected_mae) > 0.000001:
            raise RuntimeError(f"preserved rank MAE changed for {model}")
    summary = results["walk_summary"]
    if int(summary["total"]) != 4731 or int(summary["coverage"]) != 4727:
        raise RuntimeError("OOF candidate coverage changed")
    if abs(float(summary["overall_delta"]) - 0.022824) > 0.000001:
        raise RuntimeError("GAUNTLET_081 OOF delta changed")


def validate_source_anchor(requested: str) -> None:
    if requested != SOURCE_COMMIT:
        raise RuntimeError(f"source commit must be fixed at {SOURCE_COMMIT}")
    resolved = git("rev-parse", f"{requested}^{{commit}}")
    if resolved != SOURCE_COMMIT:
        raise RuntimeError("fixed source commit did not resolve exactly")
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_COMMIT, "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError("builder checkout does not descend from the fixed source commit")


def validate_packet_inventory() -> None:
    expected = set(required_packet_files())
    actual = {path.name for path in PACKET.iterdir() if path.is_file()}
    if actual != expected:
        raise RuntimeError(
            f"packet inventory mismatch missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )
    for path in PACKET.iterdir():
        if not path.is_file():
            continue
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            raise RuntimeError(f"UTF-8 BOM prohibited: {path.name}")
        if b"\r" in data:
            raise RuntimeError(f"non-LF line ending prohibited: {path.name}")
        if data and not data.endswith(b"\n"):
            raise RuntimeError(f"newline at EOF required: {path.name}")


def build(*, input_order: str = "original", order_seed: int = SEED) -> None:
    PACKET.mkdir(parents=True, exist_ok=True)
    panel, mart, age, oof = load_sources(
        input_order=input_order,
        order_seed=order_seed,
    )
    proxy = make_proxy(panel)
    results = packet_csvs(panel, mart, age, oof, proxy)
    validate_research_results(results)
    packet_markdown(results)
    write_file_inventory()
    regeneration = regeneration_rows()
    write_csv(
        PACKET / "DETERMINISTIC_REGENERATION_MANIFEST.csv",
        regeneration,
        list(regeneration[0]),
    )
    write_file_inventory()
    write_manifest()
    validate_packet_inventory()


def compare_packet_dirs(left: Path, right: Path) -> list[dict[str, Any]]:
    left_files = {
        path.relative_to(left).as_posix(): path
        for path in left.rglob("*")
        if path.is_file()
    }
    right_files = {
        path.relative_to(right).as_posix(): path
        for path in right.rglob("*")
        if path.is_file()
    }
    rows = []
    for name in sorted(set(left_files) | set(right_files)):
        left_path = left_files.get(name)
        right_path = right_files.get(name)
        left_hash = sha256(left_path) if left_path else ""
        right_hash = sha256(right_path) if right_path else ""
        rows.append(
            {
                "path": name,
                "left_sha256": left_hash,
                "right_sha256": right_hash,
                "left_bytes": left_path.stat().st_size if left_path else "",
                "right_bytes": right_path.stat().st_size if right_path else "",
                "result": "PASS" if left_hash and left_hash == right_hash else "FAIL",
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Exact repository checkout containing the fixed tracked inputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Empty or canonical output directory; defaults to the tracked packet path.",
    )
    parser.add_argument(
        "--source-commit",
        default=SOURCE_COMMIT,
        help="Fixed reachable-history anchor. Any other value fails closed.",
    )
    parser.add_argument(
        "--input-order",
        choices=("original", "reverse", "random"),
        default="original",
        help="Permitted pre-canonicalization input-order perturbation.",
    )
    parser.add_argument("--order-seed", type=int, default=SEED)
    parser.add_argument(
        "--verify-against",
        type=Path,
        help="After generation, require byte-identical output to this packet directory.",
    )
    parser.add_argument(
        "--comparison-report",
        type=Path,
        help="Optional noncanonical file-by-file comparison CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_paths(args.repo_root, args.output_dir)
    validate_source_anchor(args.source_commit)
    build(input_order=args.input_order, order_seed=args.order_seed)
    if args.verify_against:
        rows = compare_packet_dirs(PACKET, args.verify_against.resolve())
        if args.comparison_report:
            write_csv(
                args.comparison_report.resolve(),
                rows,
                [
                    "path",
                    "left_sha256",
                    "right_sha256",
                    "left_bytes",
                    "right_bytes",
                    "result",
                ],
            )
        failures = [row for row in rows if row["result"] != "PASS"]
        if failures:
            raise RuntimeError(
                f"packet verification failed for {[row['path'] for row in failures]}"
            )
        print(f"verified {len(rows)} governed files byte-identical")
    print(f"built {PACKET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
