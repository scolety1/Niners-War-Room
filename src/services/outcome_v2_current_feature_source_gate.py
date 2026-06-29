from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

SEASON_STATS_POINTER_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context"
    r"\latest_candidate.json"
)
IDENTITY_BRIDGE_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge"
    r"\outcome_v2_current_identity_bridge.csv"
)
VALIDATION_RESULTS_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended"
    r"\outcome_v2_probability_validation_results.csv"
)
OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\outcome_v2_horizon\current_feature_gate")

AUDIT_FILENAME = "outcome_v2_current_feature_source_gate_audit.csv"
MANIFEST_FILENAME = "outcome_v2_current_feature_source_gate_manifest.csv"

APPROVED_ALLOWED_USE = "outcome_v2_current_feature_source_display_only"
DISPLAY_ONLY_ALLOWED_USE = "display_stat_context_only"
SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")

IDENTITY_COLUMNS = {
    "player_id",
    "player_display_name",
    "position",
    "recent_team",
    "season",
    "season_type",
}
FIRST_DOWN_SCORING_COLUMNS = {
    "passing_yards",
    "passing_tds",
    "passing_interceptions",
    "passing_first_downs",
    "passing_2pt_conversions",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "rushing_2pt_conversions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
    "receiving_2pt_conversions",
    "rushing_fumbles_lost",
    "receiving_fumbles_lost",
    "punt_return_yards",
    "kickoff_return_yards",
    "special_teams_tds",
}
OPTIONAL_EXACTNESS_COLUMNS = {"sack_fumbles_lost", "games"}


@dataclass(frozen=True)
class CurrentFeatureSourceGateResult:
    decision: str
    output_root: Path
    audit_path: Path
    manifest_path: Path
    total_candidate_rows: int
    candidate_2025_rows: int
    veteran_bridge_rows: int
    matched_feature_rows: int
    missing_feature_rows: int
    rookie_out_of_scope_rows: int
    validated_fields: int
    blocked_fields: int


def resolve_candidate_paths(
    pointer_path: str | Path = SEASON_STATS_POINTER_PATH,
) -> tuple[Path, Path, dict[str, Any]]:
    pointer = Path(pointer_path)
    if not pointer.exists():
        raise FileNotFoundError(f"Missing season-stats pointer: {pointer}")
    metadata = json.loads(pointer.read_text(encoding="utf-8"))
    snapshot_path = Path(str(metadata.get("snapshot_path", "")))
    data_file = str(metadata.get("data_file", "player_season_stats_display_context.csv"))
    manifest_path = Path(str(metadata.get("manifest_path", "")))
    data_path = snapshot_path / data_file
    if not data_path.exists():
        raise FileNotFoundError(f"Missing season-stats candidate CSV: {data_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing season-stats manifest: {manifest_path}")
    return data_path, manifest_path, metadata


def evaluate_current_feature_source_gate(
    season_stats: pd.DataFrame,
    identity_bridge: pd.DataFrame,
    validation_results: pd.DataFrame,
    *,
    pointer_metadata: dict[str, Any],
    manifest_metadata: dict[str, Any],
) -> tuple[str, pd.DataFrame]:
    _require_columns(season_stats, IDENTITY_COLUMNS, "season_stats")
    _require_columns(
        identity_bridge,
        {
            "nwr_player_id",
            "current_board_player_name",
            "current_board_position",
            "gsis_id",
            "identity_status",
        },
        "identity_bridge",
    )
    _require_columns(validation_results, {"field_id", "validation_status"}, "validation_results")

    season_stats = season_stats.copy().fillna("")
    identity_bridge = identity_bridge.copy().fillna("")
    validation_results = validation_results.copy().fillna("")

    skill_stats = season_stats[season_stats["position"].isin(SUPPORTED_POSITIONS)].copy()
    stats_2025 = skill_stats[
        (skill_stats["season"].astype(str) == "2025")
        & (skill_stats["season_type"].astype(str) == "REG")
    ].copy()
    veteran_bridge = identity_bridge[
        identity_bridge["identity_status"].isin(["matched_exact", "matched_high_confidence"])
    ].copy()
    out_of_scope = identity_bridge[
        identity_bridge["identity_status"].eq("out_of_scope_rookie_or_prospect")
    ].copy()
    merged = veteran_bridge.merge(
        stats_2025,
        left_on="gsis_id",
        right_on="player_id",
        how="left",
        suffixes=("_bridge", "_stats"),
    )
    matched_features = int(merged["player_id"].fillna("").astype(str).str.strip().ne("").sum())
    missing_features = len(merged) - matched_features
    coverage_pct = (
        round((matched_features / len(veteran_bridge) * 100), 2)
        if len(veteran_bridge)
        else 0.0
    )

    required_columns = IDENTITY_COLUMNS | FIRST_DOWN_SCORING_COLUMNS
    required_missing = sorted(required_columns - set(season_stats.columns))
    optional_missing = sorted(OPTIONAL_EXACTNESS_COLUMNS - set(season_stats.columns))
    provenance_status = _provenance_status(manifest_metadata)
    timing_status = _timing_status(pointer_metadata, manifest_metadata, stats_2025)
    source_policy_status = _source_policy_status(pointer_metadata, manifest_metadata)
    field_status = _field_status(required_missing, optional_missing)
    identity_status = "PASS_IDENTITY_JOIN" if matched_features else "BLOCKED_IDENTITY_JOIN"
    coverage_status = (
        "PASS_USEFUL_COVERAGE"
        if len(veteran_bridge) and coverage_pct >= 75
        else "BLOCKED_INSUFFICIENT_COVERAGE"
    )
    validated_fields = int(
        validation_results["validation_status"].eq("PASS_APP_DISPLAY_VALIDATION").sum()
    )
    blocked_fields = len(validation_results) - validated_fields
    validation_status = (
        "PASS_VALIDATED_FIELDS_AVAILABLE" if validated_fields else "BLOCKED_NO_VALIDATED_FIELDS"
    )
    decision = _decision(
        provenance_status=provenance_status,
        timing_status=timing_status,
        source_policy_status=source_policy_status,
        field_status=field_status,
        identity_status=identity_status,
        coverage_status=coverage_status,
        validation_status=validation_status,
        missing_features=missing_features,
    )
    audit = pd.DataFrame(
        [
            _metric("decision", decision, "gate", "Final gate decision."),
            _metric("total_candidate_rows", len(season_stats), "data", ""),
            _metric("candidate_2025_rows", len(stats_2025), "data", "QB/RB/WR/TE 2025 REG rows."),
            _metric("source_repo", manifest_metadata.get("source_repo", ""), "provenance", ""),
            _metric("source_head", manifest_metadata.get("source_head", ""), "provenance", ""),
            _metric(
                "source_dataset",
                "|".join(_list_text(manifest_metadata.get("source_datasets"))),
                "provenance",
                "",
            ),
            _metric("provenance_status", provenance_status, "provenance", ""),
            _metric(
                "source_created_at",
                manifest_metadata.get("source_created_at", ""),
                "timing",
                "",
            ),
            _metric(
                "source_timing_class",
                "|".join(_list_text(pointer_metadata.get("source_timing_classes"))),
                "timing",
                "",
            ),
            _metric("live_use_allowed", pointer_metadata.get("live_use_allowed", ""), "timing", ""),
            _metric(
                "timing_status",
                timing_status,
                "timing",
                "2025 REG rows are complete-season facts for 2026-pre-draft use only.",
            ),
            _metric("required_missing_columns", "|".join(required_missing), "fields", ""),
            _metric("optional_missing_columns", "|".join(optional_missing), "fields", ""),
            _metric(
                "field_status",
                field_status,
                "fields",
                "Missing games prevents full feature-schema approval.",
            ),
            _metric(
                "scoring_status",
                _scoring_status(required_missing, optional_missing),
                "fields",
                "",
            ),
            _metric("availability_status", _availability_status(optional_missing), "fields", ""),
            _metric("veteran_bridge_rows", len(veteran_bridge), "identity", ""),
            _metric("matched_feature_rows", matched_features, "identity", ""),
            _metric("missing_feature_rows", missing_features, "identity", ""),
            _metric("rookie_out_of_scope_rows", len(out_of_scope), "identity", ""),
            _metric("identity_status", identity_status, "identity", ""),
            _metric("coverage_pct", coverage_pct, "coverage", ""),
            _metric("coverage_status", coverage_status, "coverage", ""),
            *_coverage_rows(merged),
            _metric("validated_fields", validated_fields, "validation", ""),
            _metric("blocked_fields", blocked_fields, "validation", ""),
            _metric("validation_status", validation_status, "validation", ""),
            _metric("source_policy_status", source_policy_status, "policy", ""),
            _metric("allowed_use_if_approved", APPROVED_ALLOWED_USE, "policy", ""),
            _metric("display_only", "true", "guardrail", ""),
            _metric("model_use_allowed", "false", "guardrail", ""),
            _metric("source_truth_allowed", "false", "guardrail", ""),
            _metric("training_allowed", "false", "guardrail", ""),
            _metric("rank_or_sort_use_allowed", "false", "guardrail", ""),
        ]
    )
    return decision, audit


def write_current_feature_source_gate_artifacts(
    *,
    output_root: str | Path = OUTPUT_ROOT,
    season_stats_pointer_path: str | Path = SEASON_STATS_POINTER_PATH,
    identity_bridge_path: str | Path = IDENTITY_BRIDGE_PATH,
    validation_results_path: str | Path = VALIDATION_RESULTS_PATH,
) -> CurrentFeatureSourceGateResult:
    stats_path, manifest_path, pointer_metadata = resolve_candidate_paths(season_stats_pointer_path)
    manifest_metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
    identity_path = Path(identity_bridge_path)
    validation_path = Path(validation_results_path)
    missing = [str(path) for path in (identity_path, validation_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing current feature source gate inputs: {missing}")

    season_stats = pd.read_csv(stats_path, dtype=str)
    identity_bridge = pd.read_csv(identity_path, dtype=str)
    validation_results = pd.read_csv(validation_path, dtype=str)
    decision, audit = evaluate_current_feature_source_gate(
        season_stats,
        identity_bridge,
        validation_results,
        pointer_metadata=pointer_metadata,
        manifest_metadata=manifest_metadata,
    )
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    audit_path = root / AUDIT_FILENAME
    manifest_out_path = root / MANIFEST_FILENAME
    audit.to_csv(audit_path, index=False)
    manifest = pd.DataFrame(
        [
            {
                "artifact": AUDIT_FILENAME,
                "path": str(audit_path),
                "rows": len(audit),
                "sha256": _sha256(audit_path),
                "created_at": datetime.now().isoformat(),
                "decision": decision,
                "source_stats_path": str(stats_path),
                "source_manifest_path": str(manifest_path),
                "identity_bridge_path": str(identity_path),
                "validation_results_path": str(validation_path),
                "display_only": "true",
                "model_use_allowed": "false",
                "source_truth_allowed": "false",
                "training_allowed": "false",
            }
        ]
    )
    manifest.to_csv(manifest_out_path, index=False)
    metrics = dict(zip(audit["metric"], audit["value"], strict=True))
    return CurrentFeatureSourceGateResult(
        decision=decision,
        output_root=root,
        audit_path=audit_path,
        manifest_path=manifest_out_path,
        total_candidate_rows=int(metrics["total_candidate_rows"]),
        candidate_2025_rows=int(metrics["candidate_2025_rows"]),
        veteran_bridge_rows=int(metrics["veteran_bridge_rows"]),
        matched_feature_rows=int(metrics["matched_feature_rows"]),
        missing_feature_rows=int(metrics["missing_feature_rows"]),
        rookie_out_of_scope_rows=int(metrics["rookie_out_of_scope_rows"]),
        validated_fields=int(metrics["validated_fields"]),
        blocked_fields=int(metrics["blocked_fields"]),
    )


def _decision(
    *,
    provenance_status: str,
    timing_status: str,
    source_policy_status: str,
    field_status: str,
    identity_status: str,
    coverage_status: str,
    validation_status: str,
    missing_features: int,
) -> str:
    if provenance_status != "PASS_PUBLIC_FACTUAL_NFLVERSE_PROVENANCE":
        return "BLOCKED_UNKNOWN_PROVENANCE"
    if timing_status == "BLOCKED_UNKNOWN_TIMING":
        return "BLOCKED_UNKNOWN_TIMING"
    if source_policy_status == "BLOCKED_SOURCE_POLICY":
        return "BLOCKED_SOURCE_POLICY"
    if field_status == "BLOCKED_FIELD_MISMATCH":
        return "BLOCKED_FIELD_MISMATCH"
    if identity_status != "PASS_IDENTITY_JOIN":
        return "BLOCKED_IDENTITY_JOIN"
    if (
        coverage_status != "PASS_USEFUL_COVERAGE"
        or validation_status != "PASS_VALIDATED_FIELDS_AVAILABLE"
    ):
        return "BLOCKED_INSUFFICIENT_COVERAGE"
    if field_status == "PARTIAL_FIELD_COMPATIBILITY" or missing_features:
        return "PARTIAL_APPROVAL_2025_FEATURE_CONTEXT_OUTCOME_V2_DISPLAY_ONLY"
    return "APPROVE_2025_FEATURE_CONTEXT_OUTCOME_V2_DISPLAY_ONLY"


def _provenance_status(manifest: dict[str, Any]) -> str:
    source_repo = str(manifest.get("source_repo", "")).lower()
    source_datasets = {item.lower() for item in _list_text(manifest.get("source_datasets"))}
    if (
        "nflverse" in source_repo
        and "nflreadpy" in source_repo
        and "season_stats" in source_datasets
    ):
        return "PASS_PUBLIC_FACTUAL_NFLVERSE_PROVENANCE"
    return "BLOCKED_UNKNOWN_PROVENANCE"


def _timing_status(
    pointer: dict[str, Any],
    manifest: dict[str, Any],
    stats_2025: pd.DataFrame,
) -> str:
    if stats_2025.empty:
        return "BLOCKED_UNKNOWN_TIMING"
    source_created_at = str(manifest.get("source_created_at", ""))
    try:
        created = datetime.fromisoformat(source_created_at.replace("Z", "+00:00"))
    except ValueError:
        return "BLOCKED_UNKNOWN_TIMING"
    if created.year < 2026:
        return "BLOCKED_UNKNOWN_TIMING"
    season_types = set(stats_2025["season_type"].astype(str))
    if season_types != {"REG"}:
        return "BLOCKED_UNKNOWN_TIMING"
    if pointer.get("live_use_allowed") is True:
        return "PASS_TIMING_EXPLICIT_LIVE_ALLOWED"
    return "PASS_NARROW_COMPLETED_2025_REG_FOR_2026_PREDRAFT"


def _source_policy_status(pointer: dict[str, Any], manifest: dict[str, Any]) -> str:
    pointer_allowed = set(_list_text(pointer.get("allowed_use")))
    manifest_allowed = set(_list_text(manifest.get("allowed_use")))
    forbidden = set(_list_text(pointer.get("forbidden_use"))) | set(
        _list_text(manifest.get("forbidden_use"))
    )
    if (
        DISPLAY_ONLY_ALLOWED_USE not in pointer_allowed
        or DISPLAY_ONLY_ALLOWED_USE not in manifest_allowed
    ):
        return "BLOCKED_SOURCE_POLICY"
    if APPROVED_ALLOWED_USE in forbidden:
        return "BLOCKED_SOURCE_POLICY"
    blocked_requirements = {"private_value", "hidden_sort", "hidden_rank", "model_training"}
    if not forbidden.intersection(blocked_requirements):
        return "BLOCKED_SOURCE_POLICY"
    return "PASS_NARROW_DISPLAY_ONLY_POLICY"


def _field_status(required_missing: list[str], optional_missing: list[str]) -> str:
    if required_missing:
        return "BLOCKED_FIELD_MISMATCH"
    if "games" in optional_missing:
        return "PARTIAL_FIELD_COMPATIBILITY"
    return "PASS_FEATURE_SCHEMA_COMPATIBLE"


def _scoring_status(required_missing: list[str], optional_missing: list[str]) -> str:
    if required_missing:
        return "BLOCKED_SCORING_FIELDS_MISSING"
    if "sack_fumbles_lost" in optional_missing:
        return "PARTIAL_EXACT_FIRST_DOWN_SCORING_MISSING_SACK_FUMBLES_LOST"
    return "PASS_EXACT_VERIFIED_FIRST_DOWN_SCORING_FIELDS"


def _availability_status(optional_missing: list[str]) -> str:
    if "games" in optional_missing:
        return "PARTIAL_AVAILABILITY_CONTEXT_MISSING_GAMES"
    return "PASS_GAMES_AVAILABLE"


def _coverage_rows(merged: pd.DataFrame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for position, group in merged.groupby("current_board_position"):
        matched = int(group["player_id"].fillna("").astype(str).str.strip().ne("").sum())
        total = len(group)
        rows.append(
            _metric(
                f"coverage_{position}",
                f"{matched}/{total}",
                "coverage",
                f"{round(matched / total * 100, 2) if total else 0.0}% matched",
            )
        )
    return rows


def _metric(metric: str, value: Any, category: str, notes: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": str(value),
        "category": category,
        "notes": notes,
    }


def _list_text(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [
        part.strip()
        for part in text.replace(";", ",").replace("|", ",").split(",")
        if part.strip()
    ]


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
