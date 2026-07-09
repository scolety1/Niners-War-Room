from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ARTIFACT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
CONTROL_REPO_ROOT = Path(r"C:\NWR\Niners-War-Room")
CONTROL_BOARD = (
    CONTROL_REPO_ROOT
    / "local_exports"
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv"
)

EXPECTED_BOARD_HASH = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    board_rows = _read_rows(CONTROL_BOARD) if CONTROL_BOARD.exists() else []
    board_hash = _file_hash(CONTROL_BOARD) if CONTROL_BOARD.exists() else ""
    build_id = hashlib.sha256(
        f"model_v4_component_receipt_backfill_v1|{board_hash}|{len(board_rows)}".encode()
    ).hexdigest()
    _write_csv(
        ARTIFACT_DIR / "MODEL_V4_COMPONENT_RECEIPT_INVENTORY.csv",
        RECEIPT_INVENTORY_HEADER,
        _receipt_inventory_rows(board_hash, board_rows),
    )
    _write_csv(
        ARTIFACT_DIR / "MODEL_V4_COMPONENT_RECEIPTS_CURRENT_BOARD.csv",
        CURRENT_BOARD_RECEIPT_HEADER,
        _current_board_receipt_rows(board_rows, board_hash, build_id),
    )
    _write_csv(
        ARTIFACT_DIR / "MODEL_V4_SOURCE_ADMISSION_READINESS_MATRIX.csv",
        SOURCE_ADMISSION_HEADER,
        SOURCE_ADMISSION_ROWS,
    )
    _write_csv(
        ARTIFACT_DIR / "MODEL_V4_HISTORICAL_REPLAY_RECEIPT_READINESS.csv",
        HISTORICAL_READINESS_HEADER,
        HISTORICAL_READINESS_ROWS,
    )


RECEIPT_INVENTORY_HEADER = (
    "receipt_id",
    "component_or_layer",
    "expected_artifact",
    "source_file_function",
    "needed_for",
    "exists_in_fresh_worktree",
    "exists_in_control_runtime",
    "safe_to_backfill_this_lane",
    "receipt_status",
    "blocker",
    "notes",
)

EXPECTED_RECEIPTS = (
    (
        "final_candidate_board",
        "candidate board final artifact",
        "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv",
        "src/services/draft_day_app_v1_service.py::load_dynasty_rankings",
        "app-visible board hash pinning and observed final fields",
        "yes_observed_field_receipts_only",
    ),
    (
        "candidate_output_board",
        "WR/QB v2 candidate output",
        "local_exports/model_v4/current_value/candidates/wr_qb_v2/full_player_board_value_review_rows.csv",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::write_wr_qb_v2_candidate_exports",
        "candidate overlay rebuild and reason-code source",
        "no",
    ),
    (
        "candidate_reason_codes",
        "WR/QB v2 candidate reason-code report",
        "local_exports/model_v4/current_value/candidates/wr_qb_v2/candidate_scoring_component_reason_codes.csv",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::write_wr_qb_v2_candidate_exports",
        "candidate overlay component explanation",
        "no",
    ),
    (
        "candidate_guardrails",
        "WR/QB v2 candidate guardrail report",
        "local_exports/model_v4/current_value/candidates/wr_qb_v2/candidate_guardrail_contamination_report.csv",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::write_wr_qb_v2_candidate_exports",
        "candidate overlay guardrail proof",
        "no",
    ),
    (
        "base_full_board",
        "base full player board before candidate overlay",
        "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv",
        "src/services/full_player_board_value_service.py::build_full_player_board_value_rows",
        "base_nwr_dynasty_score and upstream checkpoint pointer",
        "no",
    ),
    (
        "checkpoint_review_rows",
        "current value checkpoint review rows",
        "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv",
        "src/services/model_v4_current_value_checkpoint_service.py::build_current_value_checkpoint",
        "checkpoint_review_score",
        "no",
    ),
    (
        "checkpoint_component_rows",
        "current value checkpoint component rows",
        "local_exports/model_v4/current_value/latest/current_player_value_component_rows.csv",
        "src/services/model_v4_current_value_checkpoint_service.py::build_current_value_checkpoint",
        "checkpoint contribution reconciliation",
        "no",
    ),
    (
        "checkpoint_receipts",
        "current value checkpoint receipts",
        "local_exports/model_v4/current_value/latest/current_player_value_receipts.csv",
        "src/services/model_v4_current_value_checkpoint_service.py::build_current_value_checkpoint",
        "checkpoint source trace",
        "no",
    ),
    (
        "rb_wr_value_rows",
        "RB/WR current value review rows",
        "local_exports/model_v4/current_value/latest/rb_wr_current_value_review_rows.csv",
        "src/services/model_v4_rb_wr_current_value_service.py::build_rb_wr_current_value",
        "RB/WR position_specific_review_score",
        "no",
    ),
    (
        "rb_wr_component_rows",
        "RB/WR current value component rows",
        "local_exports/model_v4/current_value/latest/rb_wr_current_value_component_rows.csv",
        "src/services/model_v4_rb_wr_current_value_service.py::build_rb_wr_current_value",
        "RB/WR component values weights and contributions",
        "no",
    ),
    (
        "rb_wr_receipts",
        "RB/WR current value receipts",
        "local_exports/model_v4/current_value/latest/rb_wr_current_value_receipts.csv",
        "src/services/model_v4_rb_wr_current_value_service.py::build_rb_wr_current_value",
        "RB/WR source trace",
        "no",
    ),
    (
        "qb_te_value_rows",
        "QB/TE current value review rows",
        "local_exports/model_v4/current_value/latest/qb_te_current_value_review_rows.csv",
        "src/services/model_v4_qb_te_current_value_service.py::build_qb_te_current_value",
        "QB/TE position_specific_review_score",
        "no",
    ),
    (
        "qb_te_component_rows",
        "QB/TE current value component rows",
        "local_exports/model_v4/current_value/latest/qb_te_current_value_component_rows.csv",
        "src/services/model_v4_qb_te_current_value_service.py::build_qb_te_current_value",
        "QB/TE component values weights discipline and contributions",
        "no",
    ),
    (
        "qb_te_receipts",
        "QB/TE current value receipts",
        "local_exports/model_v4/current_value/latest/qb_te_current_value_receipts.csv",
        "src/services/model_v4_qb_te_current_value_service.py::build_qb_te_current_value",
        "QB/TE source trace",
        "no",
    ),
    (
        "replacement_vorp_players",
        "replacement/VORP player rows",
        "local_exports/model_v4/replacement_vorp/latest/player_vorp_review_rows.csv",
        "src/services/model_v4_replacement_vorp_core_service.py::build_replacement_vorp_core",
        "positive_vorp_points review_scoring_points first-down points",
        "no",
    ),
    (
        "replacement_vorp_components",
        "replacement/VORP component rows",
        "local_exports/model_v4/replacement_vorp/latest/replacement_vorp_component_rows.csv",
        "src/services/model_v4_replacement_vorp_core_service.py::build_replacement_vorp_core",
        "replacement/VORP component explanation",
        "no",
    ),
    (
        "replacement_vorp_receipts",
        "replacement/VORP receipts",
        "local_exports/model_v4/replacement_vorp/latest/replacement_vorp_receipts.csv",
        "src/services/model_v4_replacement_vorp_core_service.py::build_replacement_vorp_core",
        "replacement/VORP source trace",
        "no",
    ),
    (
        "lifecycle_rows",
        "lifecycle archetype rows",
        "local_exports/model_v4/current_value/latest/lifecycle_archetype_review_rows.csv",
        "src/services/model_v4_lifecycle_archetype_service.py::build_lifecycle_archetype_layer",
        "lifecycle_modifier_review",
        "no",
    ),
    (
        "lifecycle_components",
        "lifecycle component rows",
        "local_exports/model_v4/current_value/latest/lifecycle_archetype_component_rows.csv",
        "src/services/model_v4_lifecycle_archetype_service.py::build_lifecycle_archetype_layer",
        "lifecycle source explanation",
        "no",
    ),
    (
        "lifecycle_receipts",
        "lifecycle receipts",
        "local_exports/model_v4/current_value/latest/lifecycle_archetype_receipts.csv",
        "src/services/model_v4_lifecycle_archetype_service.py::build_lifecycle_archetype_layer",
        "lifecycle source trace",
        "no",
    ),
    (
        "confidence_rows",
        "confidence missingness rows",
        "local_exports/model_v4/current_value/latest/confidence_missingness_review_rows.csv",
        "src/services/model_v4_confidence_missingness_service.py::build_confidence_missingness_layer",
        "confidence_cap",
        "no",
    ),
    (
        "confidence_receipts",
        "confidence missingness receipts",
        "local_exports/model_v4/current_value/latest/confidence_missingness_receipts.csv",
        "src/services/model_v4_confidence_missingness_service.py::build_confidence_missingness_layer",
        "confidence cap source trace",
        "no",
    ),
    (
        "nfl_evidence_matrix",
        "NFL current evidence matrix",
        "local_exports/model_v4/evidence_matrices/latest/nfl_player_current_evidence_matrix.csv",
        "src/services/model_v4_formula_contract_service.py::NFL_MATRIX",
        "base factual and derived component inputs",
        "no",
    ),
    (
        "source_coverage_matrix",
        "source coverage matrix",
        "local_exports/model_v4/evidence_matrices/latest/source_coverage_matrix.csv",
        "src/services/model_v4_confidence_missingness_service.py::build_confidence_missingness_layer",
        "confidence cap coverage inputs",
        "no",
    ),
    (
        "warning_matrix",
        "warning matrix",
        "local_exports/model_v4/evidence_matrices/latest/warning_matrix.csv",
        "src/services/model_v4_confidence_missingness_service.py::build_confidence_missingness_layer",
        "warning/missingness inputs",
        "no",
    ),
    (
        "admitted_rushing_first_downs",
        "admitted rushing first downs",
        "local_exports/model_v4/first_downs/latest/admitted_rushing_first_downs.csv",
        "src/services/model_v4_replacement_vorp_core_service.py::build_replacement_vorp_core",
        "first-down scoring and VORP",
        "no",
    ),
    (
        "admitted_receiving_first_downs",
        "admitted receiving first downs",
        "local_exports/model_v4/first_downs/latest/admitted_receiving_first_downs.csv",
        "src/services/model_v4_replacement_vorp_core_service.py::build_replacement_vorp_core",
        "first-down scoring and VORP",
        "no",
    ),
    (
        "admitted_return_scoring",
        "admitted return scoring",
        "local_exports/model_v4/returns/latest/admitted_return_scoring_evidence.csv",
        "src/services/model_v4_replacement_vorp_core_service.py::build_replacement_vorp_core",
        "review scoring points",
        "no",
    ),
    (
        "candidate_age_rows",
        "candidate age rows",
        "local_exports/active_veteran_model_public_sources/veteran_player_inputs.csv",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::build_wr_qb_v2_candidate",
        "old QB horizon overlay age gates",
        "no",
    ),
    (
        "candidate_historical_metrics",
        "candidate historical metrics",
        "local_exports/model_v4/model_edge/latest/shadow_model_v2_metrics.csv",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::build_wr_qb_v2_candidate",
        "candidate guardrail metrics",
        "no",
    ),
)


CURRENT_BOARD_RECEIPT_HEADER = (
    "board_version",
    "candidate_mode",
    "player_id",
    "player_name",
    "position",
    "component_name",
    "receipt_class",
    "raw_value",
    "normalized_value",
    "weight_transformation",
    "source_file_function",
    "source_data_artifact",
    "source_gate_status",
    "production_review_display_blocked_classification",
    "identity_caveat_flags",
    "leakage_caveat_flags",
    "missingness_flag",
    "receipt_hash_or_build_id",
    "receipt_status",
    "caveat",
)

OBSERVED_FIELDS = (
    (
        "allowed_use_policy_stamp",
        "allowed_use",
        "row-level policy stamp",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
    ),
    (
        "candidate_mode_stamp",
        "candidate_mode",
        "row-level candidate mode stamp",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
    ),
    (
        "candidate_nwr_rank",
        "nwr_rank",
        "candidate rank assigned after candidate score sort",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_assign_candidate_ranks",
    ),
    (
        "candidate_nwr_dynasty_score",
        "nwr_dynasty_score",
        "observed final candidate score",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
    ),
    (
        "base_nwr_rank",
        "base_nwr_rank",
        "observed base rank copied into final candidate board",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
    ),
    (
        "base_nwr_dynasty_score",
        "base_nwr_dynasty_score",
        "observed base score copied into final candidate board",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
    ),
    (
        "candidate_adjustment",
        "candidate_adjustment",
        "observed score delta equals candidate score minus base score",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
    ),
    (
        "candidate_reason_codes",
        "candidate_reason_codes",
        "observed candidate reason code string",
        "src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
    ),
    (
        "upstream_checkpoint_pointer",
        "upstream_source_path",
        "observed upstream checkpoint file pointer",
        "src/services/full_player_board_value_service.py::_full_board_row",
    ),
)


SOURCE_ADMISSION_HEADER = (
    "component",
    "current_status",
    "blocker",
    "required_gate",
    "human_review_needed",
    "production_eligible_now",
    "notes",
)

SOURCE_ADMISSION_ROWS = (
    {
        "component": "current candidate board final artifact",
        "current_status": "candidate_review_only_not_active_rankings",
        "blocker": "policy stamp blocks production use",
        "required_gate": "human label/promotion review plus receipt reconciliation",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "hash-pinned observable board only",
    },
    {
        "component": "nwr_dynasty_score",
        "current_status": "candidate_review_only",
        "blocker": "upstream checkpoint/component receipts absent",
        "required_gate": "component receipt reconciliation and source-admission review",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "final score observable but not reconstructable",
    },
    {
        "component": "checkpoint_review_score",
        "current_status": "review_only_missing_receipt",
        "blocker": "current_player_value_review_rows.csv absent",
        "required_gate": "current value checkpoint receipt backfill",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "formula is position_specific_review_score * lifecycle_modifier_review * confidence_cap",
    },
    {
        "component": "RB/WR current value",
        "current_status": "review_only_missing_receipt",
        "blocker": "RB/WR value/component/receipt rows absent",
        "required_gate": "RB/WR component source gate and deterministic rebuild",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "weights are source-traced in code but row values are missing",
    },
    {
        "component": "QB/TE current value",
        "current_status": "review_only_missing_receipt",
        "blocker": "QB/TE value/component/receipt rows absent",
        "required_gate": "QB/TE component source gate and deterministic rebuild",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "discipline multipliers require row receipts",
    },
    {
        "component": "replacement/VORP",
        "current_status": "review_only_missing_receipt",
        "blocker": "replacement/VORP player/component/receipt rows absent",
        "required_gate": "replacement/VORP source-admission and receipt rebuild",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "depends on first-down and return scoring evidence",
    },
    {
        "component": "first-down scoring inputs",
        "current_status": "source-gated but current receipt missing",
        "blocker": "admitted first-down artifacts absent in clean worktree/control runtime",
        "required_gate": "first-down receipt integrity gate",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "must stay matched/admitted; no inferred values",
    },
    {
        "component": "lifecycle modifier",
        "current_status": "review_only_missing_receipt",
        "blocker": "lifecycle rows/component/receipts absent",
        "required_gate": "decision-date lifecycle source gate",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "current age/role context is leakage-risk for history",
    },
    {
        "component": "confidence cap",
        "current_status": "review_only_missing_receipt",
        "blocker": "confidence rows/receipts absent",
        "required_gate": "source coverage and warning matrix gate",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "missingness semantics must be preserved",
    },
    {
        "component": "WR/QB v2 candidate overlay",
        "current_status": "candidate_review_only",
        "blocker": "candidate output folder/reason/guardrail reports absent",
        "required_gate": "candidate overlay human review and guardrail report",
        "human_review_needed": "yes",
        "production_eligible_now": "no",
        "notes": "explicitly not active rankings",
    },
)


HISTORICAL_READINESS_HEADER = (
    "component",
    "current_receipt_status",
    "historical_replay_status",
    "decision_date_safety",
    "identity_risk",
    "source_gate_status",
    "blocker",
    "next_requirement",
)

HISTORICAL_READINESS_ROWS = (
    {
        "component": "current candidate board final artifact",
        "current_receipt_status": "observable hash-pinned final artifact",
        "historical_replay_status": "not replay-ready",
        "decision_date_safety": "current-only artifact",
        "identity_risk": "not revalidated historically",
        "source_gate_status": "candidate_review_only",
        "blocker": "not a season-by-season decision-date receipt",
        "next_requirement": "historical candidate target selection and receipt schema",
    },
    {
        "component": "nwr_dynasty_score",
        "current_receipt_status": "final field observed only",
        "historical_replay_status": "blocked",
        "decision_date_safety": "unsafe without season-specific receipts",
        "identity_risk": "medium",
        "source_gate_status": "candidate_review_only",
        "blocker": "underlying checkpoint and candidate receipts missing",
        "next_requirement": "reconcile current score before historical replay",
    },
    {
        "component": "checkpoint_review_score",
        "current_receipt_status": "missing",
        "historical_replay_status": "blocked",
        "decision_date_safety": "not proven",
        "identity_risk": "medium",
        "source_gate_status": "review_only_current_value_checkpoint",
        "blocker": "current checkpoint rows/component/receipts absent",
        "next_requirement": "current and historical checkpoint receipt backfill",
    },
    {
        "component": "RB/WR current value",
        "current_receipt_status": "missing",
        "historical_replay_status": "partial only",
        "decision_date_safety": "partial proxy only",
        "identity_risk": "medium",
        "source_gate_status": "review_only",
        "blocker": "component row receipts absent; route/proxy evidence incomplete",
        "next_requirement": "source-gated season-by-season RB/WR component receipts",
    },
    {
        "component": "QB/TE current value",
        "current_receipt_status": "missing",
        "historical_replay_status": "partial only",
        "decision_date_safety": "partial proxy only",
        "identity_risk": "medium",
        "source_gate_status": "review_only",
        "blocker": "component row receipts absent; discipline context not historically receipted",
        "next_requirement": "source-gated season-by-season QB/TE component receipts",
    },
    {
        "component": "replacement/VORP",
        "current_receipt_status": "missing",
        "historical_replay_status": "partial proxy only",
        "decision_date_safety": "requires lagged labels/source proof",
        "identity_risk": "medium",
        "source_gate_status": "review_only",
        "blocker": "player VORP and first-down/return receipts absent",
        "next_requirement": "replacement/VORP current receipt rebuild, then historical partition",
    },
    {
        "component": "first-down scoring inputs",
        "current_receipt_status": "missing in runtime",
        "historical_replay_status": "partial availability",
        "decision_date_safety": "must be season-lagged and matched-only",
        "identity_risk": "medium",
        "source_gate_status": "matched/admitted only",
        "blocker": "exact current receipt absent",
        "next_requirement": "first-down source-admission receipt lane",
    },
    {
        "component": "lifecycle modifier",
        "current_receipt_status": "missing",
        "historical_replay_status": "blocked",
        "decision_date_safety": "current role/age context leakage risk",
        "identity_risk": "medium",
        "source_gate_status": "review_only",
        "blocker": "no decision-date lifecycle receipts",
        "next_requirement": "historical lifecycle receipt design",
    },
    {
        "component": "confidence cap",
        "current_receipt_status": "missing",
        "historical_replay_status": "blocked",
        "decision_date_safety": "not proven",
        "identity_risk": "medium",
        "source_gate_status": "review_only",
        "blocker": "source coverage/warning matrices absent",
        "next_requirement": "confidence/missingness receipt rebuild",
    },
    {
        "component": "WR/QB v2 candidate overlay",
        "current_receipt_status": "final fields observed; reason/guardrail reports missing",
        "historical_replay_status": "blocked",
        "decision_date_safety": "not proven",
        "identity_risk": "medium",
        "source_gate_status": "candidate_review_only",
        "blocker": "candidate input files and historical metrics absent",
        "next_requirement": "candidate overlay source receipt lane if selected as target",
    },
)


def _receipt_inventory_rows(board_hash: str, board_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for receipt_id, layer, rel_path, source_fn, needed_for, safe in EXPECTED_RECEIPTS:
        fresh_path = REPO_ROOT / rel_path
        control_path = CONTROL_REPO_ROOT / rel_path
        exists_fresh = fresh_path.exists()
        exists_control = control_path.exists()
        status = "present_observable" if exists_control or exists_fresh else "missing"
        blocker = "" if status == "present_observable" else "artifact_absent"
        notes = ""
        if receipt_id == "final_candidate_board" and exists_control:
            status = "present_hash_verified" if board_hash.lower() == EXPECTED_BOARD_HASH else "present_hash_mismatch"
            notes = f"rows={len(board_rows)} hash={board_hash}"
        rows.append(
            {
                "receipt_id": receipt_id,
                "component_or_layer": layer,
                "expected_artifact": rel_path,
                "source_file_function": source_fn,
                "needed_for": needed_for,
                "exists_in_fresh_worktree": str(exists_fresh).lower(),
                "exists_in_control_runtime": str(exists_control).lower(),
                "safe_to_backfill_this_lane": safe,
                "receipt_status": status,
                "blocker": blocker,
                "notes": notes,
            }
        )
    return rows


def _current_board_receipt_rows(
    board_rows: list[dict[str, str]],
    board_hash: str,
    build_id: str,
) -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    for row in board_rows:
        for component_name, field, transform, source_fn in OBSERVED_FIELDS:
            raw = str(row.get(field, "") or "")
            if raw == "":
                continue
            digest = hashlib.sha256(
                f"{board_hash}|{row.get('player_id','')}|{component_name}|{raw}".encode()
            ).hexdigest()
            receipts.append(
                {
                    "board_version": row.get("full_board_version", ""),
                    "candidate_mode": row.get("candidate_mode", ""),
                    "player_id": row.get("player_id", ""),
                    "player_name": row.get("player_name", ""),
                    "position": row.get("position", ""),
                    "component_name": component_name,
                    "receipt_class": "observed_final_board_field_not_upstream_component",
                    "raw_value": raw,
                    "normalized_value": raw,
                    "weight_transformation": transform,
                    "source_file_function": source_fn,
                    "source_data_artifact": str(CONTROL_BOARD),
                    "source_gate_status": row.get("allowed_use", ""),
                    "production_review_display_blocked_classification": (
                        "candidate_review_only_not_active_rankings"
                    ),
                    "identity_caveat_flags": "identity_not_revalidated_in_this_lane",
                    "leakage_caveat_flags": "current_only_not_historical_replay_safe",
                    "missingness_flag": "value_present",
                    "receipt_hash_or_build_id": f"{build_id}:{digest}",
                    "receipt_status": "observed_only",
                    "caveat": (
                        "This records a value already present in the final board; it does "
                        "not reconstruct checkpoint/component math."
                    ),
                }
            )
    return receipts


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(path: Path, header: tuple[str, ...], rows: list[dict[str, object]] | tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})


if __name__ == "__main__":
    main()
