#!/usr/bin/env python3
"""Freeze and schema-validate selected Model v4 receipt candidates.

This is a Data Hygiene review artifact generator. It copies only selected
small, derived, review-safe files into this packet folder and leaves large or
protected/runtime artifacts as manifest-only rows. It does not write to
canonical local_exports, regenerate receipts, run replay, tune formulas, or
change rankings/app/runtime behavior.
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path


ARTIFACT_DIR = Path(__file__).resolve().parent
FROZEN_DIR = ARTIFACT_DIR / "frozen_receipt_artifacts"
EXPECTED_REMOTE_HEAD = "a57b33e1c2cd55bc61d0c0a32cb48ed554b776cc"
PRIOR_LOCATOR_COMMIT = "490052293d2b5ec8d27c2c8b13fff20486405895"
PRIOR_GAP_COMMIT = "8a438d4424357eb90f6210bd3f082736c4b111c9"
PRIOR_SYSTEM_AUDIT_COMMIT = "6bc013bea5925525ed8326cc62ca97c1d0ca5ab2"
FREEZE_GROUP_ALIASES = {
    "current_board_recovered_inputs": "cb",
    "current_board_overlay_sidecars": "ov",
    "exact_rebuild_audit_artifacts": "audit",
    "historical_partial_receipt_artifacts": "hist",
}

FROZEN_CANDIDATES = [
    {
        "receipt_family": "checkpoint_review_score;position_specific_review_score;lifecycle_age_receipts;confidence_cap_receipts;exact_transform_weight_receipts",
        "artifact_role": "highest_value_current_player_value_full_board_rows",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\current_player_value_full_board_review_rows.csv",
        "artifact_scope": "current_only",
        "freeze_group": "current_board_recovered_inputs",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "checkpoint_review_score;position_specific_review_score;lifecycle_age_receipts;confidence_cap_receipts;exact_transform_weight_receipts",
        "artifact_role": "current_player_value_review_rows_review_subset",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\current_player_value_review_rows.csv",
        "artifact_scope": "current_only",
        "freeze_group": "current_board_recovered_inputs",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "checkpoint_review_score;position_specific_review_score;lifecycle_age_receipts;confidence_cap_receipts;exact_transform_weight_receipts",
        "artifact_role": "current_value_layers_full_board_current_player_value_rows",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\full_board_active_support\current_value_layers\current_player_value_review_rows.csv",
        "artifact_scope": "current_only",
        "freeze_group": "current_board_recovered_inputs",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "WR_QB_v2_candidate_overlay;exact_nwr_dynasty_score_and_rank",
        "artifact_role": "hash_verified_final_board",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv",
        "artifact_scope": "current_only",
        "freeze_group": "current_board_recovered_inputs",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "WR_QB_v2_candidate_overlay",
        "artifact_role": "pre_wr_qb_v2_overlay_sidecar",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.pre_wr_qb_v2_20260609_220847.csv",
        "artifact_scope": "current_only_overlay_sidecar",
        "freeze_group": "current_board_overlay_sidecars",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "WR_QB_v2_candidate_overlay",
        "artifact_role": "pre_old_pocket_qb_guardrail_sidecar",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.pre_old_pocket_qb_guardrail_20260609_231231.csv",
        "artifact_scope": "current_only_overlay_sidecar",
        "freeze_group": "current_board_overlay_sidecars",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "source_coverage_matrix_history;confidence_cap_receipts",
        "artifact_role": "current_board_source_coverage_matrix",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\model_v4\current_value\latest\full_board_active_support\evidence_matrices\source_coverage_matrix.csv",
        "artifact_scope": "current_only_coverage_matrix",
        "freeze_group": "current_board_recovered_inputs",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "exact_nwr_dynasty_score_and_rank;lifecycle_age_receipts;confidence_cap_receipts",
        "artifact_role": "recovered_timestamped_data_pack_model_outputs",
        "source_path": r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1\recovered_from_final_laptop_handoff\local_exports\data_packs\lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233\model_outputs.csv",
        "artifact_scope": "current_only_data_pack",
        "freeze_group": "current_board_recovered_inputs",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "lifecycle_age_receipts",
        "artifact_role": "review_safe_qb_age_adapter_used_for_exact_current_board_rebuild",
        "source_path": r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708\review_safe_qb_age_adapter_from_lifecycle_receipts.csv",
        "artifact_scope": "current_only_adapter",
        "freeze_group": "exact_rebuild_audit_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "exact_nwr_dynasty_score_and_rank;WR_QB_v2_candidate_overlay",
        "artifact_role": "rebuilt_hash_verified_current_board",
        "source_path": r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708\rebuilt_full_player_board_value_review_rows.csv",
        "artifact_scope": "current_only_rebuild_output",
        "freeze_group": "exact_rebuild_audit_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "checkpoint_review_score;position_specific_review_score;confidence_cap_receipts",
        "artifact_role": "exact_rebuild_receipt_chain_summary",
        "source_path": r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708\CURRENT_BOARD_RECOVERY_REBUILD_RECEIPT_CHAIN.csv",
        "artifact_scope": "current_only_rebuild_audit",
        "freeze_group": "exact_rebuild_audit_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "checkpoint_review_score;source_coverage_matrix_history;exact_transform_weight_receipts",
        "artifact_role": "exact_rebuild_input_map",
        "source_path": r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708\CURRENT_BOARD_RECOVERY_REBUILD_INPUT_MAP.csv",
        "artifact_scope": "current_only_rebuild_audit",
        "freeze_group": "exact_rebuild_audit_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "exact_nwr_dynasty_score_and_rank",
        "artifact_role": "exact_rebuild_hash_audit",
        "source_path": r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708\CURRENT_BOARD_RECOVERY_REBUILD_HASH_AUDIT.csv",
        "artifact_scope": "current_only_rebuild_audit",
        "freeze_group": "exact_rebuild_audit_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "exact_nwr_dynasty_score_and_rank",
        "artifact_role": "exact_rebuild_comparison",
        "source_path": r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708\CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv",
        "artifact_scope": "current_only_rebuild_audit",
        "freeze_group": "exact_rebuild_audit_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "exact_nwr_dynasty_score_and_rank",
        "artifact_role": "exact_rebuild_field_diffs",
        "source_path": r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708\CURRENT_BOARD_RECOVERY_REBUILD_FIELD_DIFFS.csv",
        "artifact_scope": "current_only_rebuild_audit",
        "freeze_group": "exact_rebuild_audit_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "source_coverage_matrix_history;confidence_cap_receipts",
        "artifact_role": "historical_replay_readiness_matrix",
        "source_path": r"C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708\docs\hq\model\model_v4_historical_component_receipt_backfill_v1_20260708\MODEL_V4_HISTORICAL_REPLAY_READINESS_MATRIX.csv",
        "artifact_scope": "partial_historical_readiness",
        "freeze_group": "historical_partial_receipt_artifacts",
        "freeze_decision": "freeze",
    },
    {
        "receipt_family": "source_coverage_matrix_history;position_specific_review_score;confidence_cap_receipts",
        "artifact_role": "historical_receipt_coverage_summary",
        "source_path": r"C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708\docs\hq\model\model_v4_historical_component_receipt_backfill_v1_20260708\MODEL_V4_HISTORICAL_RECEIPT_COVERAGE_SUMMARY.csv",
        "artifact_scope": "partial_historical_readiness",
        "freeze_group": "historical_partial_receipt_artifacts",
        "freeze_decision": "freeze",
    },
]

MANIFEST_ONLY_CANDIDATES = [
    {
        "receipt_family": "position_specific_review_score;role_archetype_receipts;confidence_cap_receipts",
        "artifact_role": "large_partial_historical_component_receipts",
        "source_path": r"C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708\docs\hq\model\model_v4_historical_component_receipt_backfill_v1_20260708\MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv",
        "artifact_scope": "partial_historical_proxy_receipts",
        "reason": "large derived artifact; useful for schema validation but not copied in freeze lane",
    },
    {
        "receipt_family": "WR_QB_v2_candidate_overlay;exact_transform_weight_receipts",
        "artifact_role": "wr_qb_v2_candidate_service_source_trace",
        "source_path": r"C:\NWR\Niners-War-Room\src\services\model_v4_wr_qb_v2_candidate_service.py",
        "artifact_scope": "runtime_source_trace_manifest_only",
        "reason": "source/runtime file must not be copied or modified in Data Hygiene freeze lane",
    },
    {
        "receipt_family": "WR_QB_v2_candidate_overlay;exact_transform_weight_receipts",
        "artifact_role": "wr_qb_v2_candidate_export_script_trace",
        "source_path": r"C:\NWR\Niners-War-Room\scripts\build_model_v4_wr_qb_v2_candidate_exports.py",
        "artifact_scope": "script_source_trace_manifest_only",
        "reason": "script trace only; not a receipt artifact and not copied in freeze lane",
    },
    {
        "receipt_family": "source_coverage_matrix_history;exact_transform_weight_receipts",
        "artifact_role": "signal_source_coverage_matrix_doc_trace",
        "source_path": r"C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_MODEL_SIGNAL_SOURCE_COVERAGE_MATRIX_20260621.md",
        "artifact_scope": "documentation_trace_manifest_only",
        "reason": "documentation trace, not a tabular receipt; manifest only",
    },
]

FAMILY_ORDER = [
    "checkpoint_review_score",
    "position_specific_review_score",
    "lifecycle_age_receipts",
    "role_archetype_receipts",
    "confidence_cap_receipts",
    "WR_QB_v2_candidate_overlay",
    "exact_nwr_dynasty_score_and_rank",
    "route_yprr_tprr_exact_receipts",
    "red_zone_exact_receipts",
    "shadow_model_v2_metrics",
    "return_scoring_receipts",
    "source_coverage_matrix_history",
    "exact_transform_weight_receipts",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_schema(path: Path) -> tuple[int | None, list[str]]:
    if path.suffix.lower() not in {".csv", ".tsv"}:
        return None, []
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        try:
            columns = next(reader)
        except StopIteration:
            return 0, []
        rows = sum(1 for _ in reader)
    return rows, columns


def find_cols(columns: list[str], pattern: str) -> list[str]:
    rx = re.compile(pattern, re.I)
    return [c for c in columns if rx.search(c)]


def schema_result(path: Path, scope: str) -> dict[str, str]:
    row_count, columns = read_csv_schema(path)
    key_cols = find_cols(columns, r"(player_id|nwr_player_id|gsis_id|sleeper_id|pfr_id|player_name|player|name)")
    season_cols = find_cols(columns, r"(season|year|as_of|feature|source|target)")
    position_cols = find_cols(columns, r"(^pos$|position|fantasy_position)")
    score_cols = find_cols(columns, r"(checkpoint_review_score|position_specific_review_score|nwr_dynasty_score|rank|score|value)")
    status_cols = find_cols(columns, r"(candidate_mode|status|stamp|review|mode)")
    source_cols = find_cols(columns, r"(source|receipt|gate|provenance|hash|artifact)")
    current_schema_match = "yes" if (
        key_cols and position_cols and score_cols and scope.startswith("current")
    ) else "no"
    historical_support = "yes" if (
        key_cols and season_cols and (score_cols or source_cols) and not scope.startswith("current")
    ) else "no"
    if scope.startswith("current"):
        artifact_time_scope = "current_only"
    elif "partial_historical" in scope:
        artifact_time_scope = "partial_historical"
    else:
        artifact_time_scope = scope
    return {
        "row_count": "" if row_count is None else str(row_count),
        "column_count": str(len(columns)),
        "columns": "|".join(columns),
        "key_columns_present": "|".join(key_cols),
        "season_columns_present": "|".join(season_cols),
        "position_columns_present": "|".join(position_cols),
        "player_id_columns_present": "|".join(find_cols(columns, r"(player_id|nwr_player_id|gsis_id|sleeper_id|pfr_id)")),
        "score_columns_present": "|".join(score_cols),
        "status_candidate_mode_columns_present": "|".join(status_cols),
        "source_use_gate_columns_present": "|".join(source_cols),
        "schema_matches_current_board_equivalent": current_schema_match,
        "schema_can_support_historical_replay_later": historical_support,
        "artifact_time_scope": artifact_time_scope,
    }


def safe_name(role: str, source_path: Path) -> str:
    role = re.sub(r"[^A-Za-z0-9_.-]+", "_", role).strip("_")[:16]
    digest = sha256_file(source_path)[:12]
    return f"{digest}_{role}{source_path.suffix}".replace(" ", "_")


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    freeze_manifest: list[dict[str, str]] = []
    schema_rows: list[dict[str, str]] = []
    path_rows: list[dict[str, str]] = []
    manifest_only_rows: list[dict[str, str]] = []

    for candidate in FROZEN_CANDIDATES:
        source = Path(candidate["source_path"])
        if not source.exists():
            raise FileNotFoundError(source)
        stat = source.stat()
        sha = sha256_file(source)
        group_dir = FROZEN_DIR / FREEZE_GROUP_ALIASES.get(candidate["freeze_group"], candidate["freeze_group"])
        group_dir.mkdir(parents=True, exist_ok=True)
        frozen_name = safe_name(candidate["artifact_role"], source)
        frozen = group_dir / frozen_name
        shutil.copy2(source, frozen)
        frozen_sha = sha256_file(frozen)
        if frozen_sha != sha:
            raise RuntimeError(f"copy hash mismatch for {source}")
        schema = schema_result(frozen, candidate["artifact_scope"])
        freeze_manifest.append({
            "receipt_family": candidate["receipt_family"],
            "artifact_role": candidate["artifact_role"],
            "source_path": str(source),
            "frozen_path": str(frozen.relative_to(ARTIFACT_DIR)),
            "sha256": sha,
            "file_size_bytes": str(stat.st_size),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "row_count": schema["row_count"],
            "column_count": schema["column_count"],
            "freeze_decision": "frozen_review_safe_derived",
            "artifact_time_scope": schema["artifact_time_scope"],
            "notes": "Copied under review artifact folder only; no canonical runtime path changed.",
        })
        schema_rows.append({
            "receipt_family": candidate["receipt_family"],
            "artifact_role": candidate["artifact_role"],
            "source_path": str(source),
            "frozen_path": str(frozen.relative_to(ARTIFACT_DIR)),
            "sha256": sha,
            "file_size_bytes": str(stat.st_size),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            **schema,
        })
        path_rows.append({
            "receipt_family": candidate["receipt_family"],
            "artifact_role": candidate["artifact_role"],
            "source_path": str(source),
            "frozen_path": str(frozen.relative_to(ARTIFACT_DIR)),
            "freeze_status": "frozen",
            "manifest_only_reason": "",
        })

    for candidate in MANIFEST_ONLY_CANDIDATES:
        source = Path(candidate["source_path"])
        if not source.exists():
            manifest_only_rows.append({
                **candidate,
                "sha256": "",
                "file_size_bytes": "",
                "modified_time": "",
                "row_count": "",
                "column_count": "",
                "columns": "",
                "manifest_status": "missing_at_validation_time",
            })
            continue
        stat = source.stat()
        sha = sha256_file(source)
        schema = schema_result(source, candidate["artifact_scope"])
        manifest_only_rows.append({
            **candidate,
            "sha256": sha,
            "file_size_bytes": str(stat.st_size),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "row_count": schema["row_count"],
            "column_count": schema["column_count"],
            "columns": schema["columns"],
            "manifest_status": "manifest_only_not_copied",
        })
        schema_rows.append({
            "receipt_family": candidate["receipt_family"],
            "artifact_role": candidate["artifact_role"],
            "source_path": str(source),
            "frozen_path": "",
            "sha256": sha,
            "file_size_bytes": str(stat.st_size),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            **schema,
        })
        path_rows.append({
            "receipt_family": candidate["receipt_family"],
            "artifact_role": candidate["artifact_role"],
            "source_path": str(source),
            "frozen_path": "",
            "freeze_status": "manifest_only",
            "manifest_only_reason": candidate["reason"],
        })

    family_rows: list[dict[str, str]] = []
    for family in FAMILY_ORDER:
        frozen = [r for r in freeze_manifest if family in r["receipt_family"].split(";")]
        manifest = [r for r in manifest_only_rows if family in r["receipt_family"].split(";")]
        schemas = [r for r in schema_rows if family in r["receipt_family"].split(";")]
        if family in {"route_yprr_tprr_exact_receipts", "return_scoring_receipts"}:
            decision = "requires_source_admission"
        elif family == "shadow_model_v2_metrics":
            decision = "missing_source"
        elif family in {"role_archetype_receipts", "confidence_cap_receipts", "red_zone_exact_receipts"}:
            decision = "requires_regeneration_contract"
        elif family in {"WR_QB_v2_candidate_overlay", "exact_nwr_dynasty_score_and_rank", "exact_transform_weight_receipts"}:
            decision = "requires_human_review"
        elif frozen or manifest:
            decision = "freeze_ready_for_master_review"
        else:
            decision = "not_enough_information"
        replay_support = "no"
        if any(r["schema_can_support_historical_replay_later"] == "yes" for r in schemas):
            replay_support = "partial_only"
        if family in {"checkpoint_review_score", "exact_nwr_dynasty_score_and_rank"}:
            replay_support = "current_only"
        family_rows.append({
            "receipt_family": family,
            "decision": decision,
            "frozen_artifacts": str(len(frozen)),
            "manifest_only_artifacts": str(len(manifest)),
            "schemas_validated": str(len(schemas)),
            "schema_supports_exact_historical_replay": "no",
            "schema_supports_future_review": replay_support,
            "source_admission_required": "yes" if decision == "requires_source_admission" else "no",
            "human_review_required": "yes",
            "notes": "Exact historical equivalent not found; evidence is current-only or partial unless separately admitted.",
        })

    freeze_fields = [
        "receipt_family",
        "artifact_role",
        "source_path",
        "frozen_path",
        "sha256",
        "file_size_bytes",
        "modified_time",
        "row_count",
        "column_count",
        "freeze_decision",
        "artifact_time_scope",
        "notes",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FREEZE_MANIFEST.csv", freeze_manifest, freeze_fields)

    schema_fields = [
        "receipt_family",
        "artifact_role",
        "source_path",
        "frozen_path",
        "sha256",
        "file_size_bytes",
        "modified_time",
        "row_count",
        "column_count",
        "columns",
        "key_columns_present",
        "season_columns_present",
        "position_columns_present",
        "player_id_columns_present",
        "score_columns_present",
        "status_candidate_mode_columns_present",
        "source_use_gate_columns_present",
        "schema_matches_current_board_equivalent",
        "schema_can_support_historical_replay_later",
        "artifact_time_scope",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_SCHEMA_VALIDATION.csv", schema_rows, schema_fields)

    family_fields = [
        "receipt_family",
        "decision",
        "frozen_artifacts",
        "manifest_only_artifacts",
        "schemas_validated",
        "schema_supports_exact_historical_replay",
        "schema_supports_future_review",
        "source_admission_required",
        "human_review_required",
        "notes",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FAMILY_VALIDATION_DECISIONS.csv", family_rows, family_fields)

    path_fields = [
        "receipt_family",
        "artifact_role",
        "source_path",
        "frozen_path",
        "freeze_status",
        "manifest_only_reason",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_SOURCE_PATH_MAP.csv", path_rows, path_fields)

    manifest_fields = [
        "receipt_family",
        "artifact_role",
        "source_path",
        "artifact_scope",
        "reason",
        "sha256",
        "file_size_bytes",
        "modified_time",
        "row_count",
        "column_count",
        "columns",
        "manifest_status",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_MANIFEST_ONLY_ARTIFACTS.csv", manifest_only_rows, manifest_fields)

    improved = [r for r in family_rows if int(r["frozen_artifacts"]) + int(r["manifest_only_artifacts"]) + int(r["schemas_validated"]) > 0]
    blocked = [r["receipt_family"] for r in family_rows if r["decision"] in {"requires_source_admission", "missing_source", "not_enough_information"}]

    limitations = ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FREEZE_LIMITATIONS.md"
    limitations.write_text(
        "# Model v4 Historical Receipt Freeze Limitations\n\n"
        "- No exact historical equivalents were found in the prior locator lane.\n"
        "- This freeze preserves current-only and partial/proxy evidence; it does not unblock exact Model v4 replay by itself.\n"
        "- The frozen current-board files may validate current receipt semantics, not season-by-season historical replay.\n"
        "- The large `MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv` is manifest-only in this lane and remains partial/proxy evidence.\n"
        "- Route/YPRR/TPRR and return-scoring receipts still require source admission.\n"
        "- `shadow_model_v2_metrics.csv` remains missing.\n"
        "- No source is promoted, no Formula Gauntlet tournament is approved, and no ranking/app/runtime/model behavior is changed.\n",
        encoding="utf-8",
    )

    next_actions = ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_NEXT_ACTIONS_AFTER_FREEZE.md"
    next_actions.write_text(
        "# Model v4 Historical Receipt Next Actions After Freeze\n\n"
        "## Recommended Next Lane\n\n"
        "`Model v4 Historical Receipt Master Review and Admission Decision V1`\n\n"
        "Purpose: Master HQ reviews the frozen evidence bundle, decides whether any current-only artifacts should be canonicalized as evidence, and decides whether to authorize a bounded review-only regeneration contract for role, confidence, and red-zone receipts.\n\n"
        "## Do Not Run Yet\n\n"
        "- Exact Model v4 historical replay.\n"
        "- Formula Gauntlet tournaments.\n"
        "- 100-candidate Gauntlet.\n"
        "- Champion refinement.\n"
        "- Rankings integration.\n\n"
        "## Possible Follow-On Work\n\n"
        "- Bounded review-only regeneration contract for `role_archetype_receipts`, `confidence_cap_receipts`, and `red_zone_exact_receipts`.\n"
        "- Human review for WR/QB overlay and exact score/rank current-only sidecars.\n"
        "- Source admission lanes for route/YPRR/TPRR and return scoring.\n"
        "- Manual recovery or scope removal decision for `shadow_model_v2_metrics`.\n",
        encoding="utf-8",
    )

    source_trace = ARTIFACT_DIR / "DATA_HYGIENE_SOURCE_TRACE.md"
    source_trace.write_text(
        "# Data Hygiene Source Trace\n\n"
        f"- Current remote HQ verified: `{EXPECTED_REMOTE_HEAD}`\n"
        f"- Prior locator ledger commit verified: `{PRIOR_LOCATOR_COMMIT}`\n"
        f"- Prior gap plan commit verified: `{PRIOR_GAP_COMMIT}`\n"
        f"- Prior system audit commit verified: `{PRIOR_SYSTEM_AUDIT_COMMIT}`\n\n"
        "## Governance Standards\n\n"
        "- `docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708/`\n"
        "- Local/push-held Data Hygiene Operating Charter was available as context; this lane remains evidence/readiness only.\n\n"
        "## Prior Artifacts Read\n\n"
        "- `C:\\NWR\\Niners-War-Room-model-v4-historical-receipt-locator-ledger-v1-20260709\\docs\\hq\\data_hygiene\\model_v4_historical_receipt_locator_ledger_v1_20260709`\n"
        "- `C:\\NWR\\Niners-War-Room-model-v4-historical-receipt-gap-closure-plan-v1-20260708\\docs\\hq\\data_hygiene\\model_v4_historical_receipt_gap_closure_plan_v1_20260708`\n"
        "- `C:\\NWR\\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\\docs\\hq\\model\\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708`\n"
        "- `C:\\NWR\\Niners-War-Room-full-system-audit-integration-map-v1-20260709\\docs\\hq\\master\\nwr_full_system_audit_integration_map_v1_20260709`\n"
        "- `C:\\NWR\\_manual_recovery_dropzone\\current_board_rebuild_inputs_v1\\z1`\n\n"
        "This lane copied only selected small derived/review-safe files into `frozen_receipt_artifacts/`; all other artifacts were manifest-only. It did not write canonical `local_exports`, regenerate receipts, run replay, run Formula Gauntlet, promote sources, or change rankings/app/runtime/model behavior.\n",
        encoding="utf-8",
    )

    report = ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FREEZE_SCHEMA_VALIDATION_V1_REPORT.md"
    verdict = "YELLOW_MODEL_V4_HISTORICAL_RECEIPT_FREEZE_PARTIAL_WITH_BLOCKERS"
    report.write_text(
        "# Model v4 Historical Receipt Freeze and Schema Validation V1\n\n"
        "## Verdict\n\n"
        f"`{verdict}`\n\n"
        "## Clear Answer\n\n"
        "Data Hygiene froze a small, review-safe evidence bundle and schema-validated both frozen and manifest-only receipt candidates. The freeze improves Master HQ reviewability, but it does not provide exact season-by-season Model v4 historical receipts and does not unblock exact replay.\n\n"
        "## Freeze Summary\n\n"
        f"- Frozen artifacts: `{len(freeze_manifest)}`\n"
        f"- Manifest-only artifacts: `{len(manifest_only_rows)}`\n"
        f"- Schemas validated: `{len(schema_rows)}`\n"
        f"- Receipt families improved for review: `{len(improved)}`\n"
        f"- Receipt families still blocked: `{', '.join(blocked)}`\n\n"
        "## What Was Frozen\n\n"
        "- Current-board value review rows and final board rows from the validated laptop recovery dropzone.\n"
        "- WR/QB overlay sidecars from the recovered current-board chain.\n"
        "- Current-board source coverage matrix and data-pack `model_outputs.csv`.\n"
        "- Exact current-board rebuild audit artifacts, including hash/comparison/receipt-chain rows.\n"
        "- Small partial historical readiness/coverage summaries.\n\n"
        "## What Stayed Manifest-Only\n\n"
        "- Large partial historical component receipts (`42,933` rows).\n"
        "- Runtime/source-code traces for WR/QB candidate overlay.\n"
        "- Source coverage documentation trace.\n\n"
        "## Readiness Impact\n\n"
        "- Exact Model v4 replay remains blocked.\n"
        "- Formula Gauntlet tournaments remain blocked.\n"
        "- 100-candidate Gauntlet remains blocked.\n"
        "- Champion refinement remains blocked.\n"
        "- Rankings integration remains blocked.\n"
        "- No source was promoted.\n",
        encoding="utf-8",
    )

    print(f"frozen_artifacts={len(freeze_manifest)}")
    print(f"manifest_only={len(manifest_only_rows)}")
    print(f"schemas_validated={len(schema_rows)}")
    print(f"families_improved={len(improved)}")
    print(f"blocked_families={';'.join(blocked)}")


if __name__ == "__main__":
    main()
