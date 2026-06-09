from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.services.data_pack_admission_service import (
    admission_summary_row,
    build_data_pack_admission_report,
)
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.draft_freeze_service import DEFAULT_FREEZE_ROOT
from src.services.final_calibration_gate_service import (
    FinalCalibrationGateReport,
    build_final_calibration_gate,
)
from src.services.lve_stats_first_apply_service import (
    DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
    STATS_FIRST_APPLIED_PACK_MANIFEST_FILE,
    stats_first_applied_pack_review_rows,
)
from src.services.lve_stats_first_preview_service import (
    DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    STATS_FIRST_PREVIEW_MANIFEST_FILE,
    STATS_FIRST_PREVIEW_OUTPUT_FILE,
    stats_first_preview_review_rows,
    stats_first_preview_snapshot_rows,
)
from src.services.trust_status_service import trust_status_from_health


@dataclass(frozen=True)
class SafetyGateCheck:
    gate: str
    status: str
    severity: str
    detail: str
    next_action: str


@dataclass(frozen=True)
class SafetyGateAuditReport:
    status: str
    calibration_passed: bool
    calibration_badge: str
    final_decision_badge: str
    blocked_count: int
    review_count: int
    ready_count: int
    checks: tuple[SafetyGateCheck, ...]


def build_final_qa_safety_gate_audit(
    data_pack_path: str | Path,
    *,
    stats_first_preview_root: str | Path = DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    stats_first_applied_pack_root: str | Path = DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
    draft_freeze_root: str | Path = DEFAULT_FREEZE_ROOT,
) -> SafetyGateAuditReport:
    calibration_report = build_final_calibration_gate(
        data_pack_path,
        stats_first_preview_root=stats_first_preview_root,
    )
    checks = (
        _final_calibration_gate(calibration_report),
        _selected_pack_gate(
            data_pack_path,
            calibration_passed=calibration_report.passed,
        ),
        _stats_first_preview_gate(stats_first_preview_root),
        _stats_first_apply_gate(stats_first_applied_pack_root),
        _draft_freeze_gate(draft_freeze_root),
        _no_silent_mutation_policy_gate(),
    )
    blocked = sum(1 for check in checks if check.status == "blocked")
    review = sum(1 for check in checks if check.status == "review")
    ready = sum(1 for check in checks if check.status == "ready")
    status = "blocked" if blocked else "review" if review else "ready"
    return SafetyGateAuditReport(
        status=status,
        calibration_passed=calibration_report.passed,
        calibration_badge=calibration_report.badge,
        final_decision_badge=calibration_report.decision_badge,
        blocked_count=blocked,
        review_count=review,
        ready_count=ready,
        checks=checks,
    )


def safety_gate_audit_summary_row(report: SafetyGateAuditReport) -> dict[str, object]:
    return {
        "overall_status": report.status,
        "calibration_badge": report.calibration_badge,
        "final_decision_badge": report.final_decision_badge,
        "model_calibration_passed": report.calibration_passed,
        "blocked": report.blocked_count,
        "review": report.review_count,
        "ready": report.ready_count,
        "money_decision_gate": "pass" if report.status == "ready" else "hold",
        "next_action": _overall_next_action(report.status),
    }


def safety_gate_audit_rows(report: SafetyGateAuditReport) -> list[dict[str, object]]:
    return [
        {
            "gate": check.gate,
            "status": check.status,
            "severity": check.severity,
            "detail": check.detail,
            "next_action": check.next_action,
        }
        for check in report.checks
    ]


def _final_calibration_gate(report: FinalCalibrationGateReport) -> SafetyGateCheck:
    if report.passed:
        return SafetyGateCheck(
            gate="final_model_calibration",
            status="ready",
            severity="info",
            detail=report.badge,
            next_action="Decision-ready status may be restored if selected pack gates pass.",
        )
    return SafetyGateCheck(
        gate="final_model_calibration",
        status=report.status,
        severity="error" if report.status == "blocked" else "warning",
        detail=(
            f"{report.badge}: {report.blocked_count} blocked, "
            f"{report.review_count} review, {report.ready_count} ready."
        ),
        next_action="Open Model Lab and clear the final calibration gate checks.",
    )


def _selected_pack_gate(
    data_pack_path: str | Path,
    *,
    calibration_passed: bool,
) -> SafetyGateCheck:
    health = build_data_pack_health_report(data_pack_path)
    admission = build_data_pack_admission_report(candidate_data_pack=data_pack_path)
    trust = trust_status_from_health(health, calibration_passed=calibration_passed)
    admission_summary = admission_summary_row(admission)
    if trust.status == "decision_ready" and admission.decision == "ready":
        return SafetyGateCheck(
            gate="selected_pack_decision_readiness",
            status="ready",
            severity="info",
            detail="Selected pack is decision-ready and admitted.",
            next_action="Use this pack only after any late news is intentionally refreshed.",
        )
    if trust.status == "blocked" or admission.decision == "blocked":
        return SafetyGateCheck(
            gate="selected_pack_decision_readiness",
            status="blocked",
            severity="error",
            detail=(
                f"Trust status is {trust.status}; admission is "
                f"{admission_summary['decision']}."
            ),
            next_action="Fix blocking Import Review issues before using decision pages.",
        )
    return SafetyGateCheck(
        gate="selected_pack_decision_readiness",
        status="review",
        severity="warning",
        detail=f"Trust status is {trust.status}; admission is {admission.decision}.",
        next_action="Clear review items before money decisions or freeze as review-only.",
    )


def _stats_first_preview_gate(preview_root: str | Path) -> SafetyGateCheck:
    snapshots = stats_first_preview_snapshot_rows(preview_root)
    if not snapshots:
        return SafetyGateCheck(
            gate="stats_first_preview_boundary",
            status="review",
            severity="warning",
            detail="No stats-first preview artifacts were found.",
            next_action=(
                "Create a preview from normalized features before applying "
                "stats-first scores."
            ),
        )
    bad_manifests = []
    missing_outputs = []
    for snapshot in snapshots:
        preview_path = Path(str(snapshot.get("preview_path") or ""))
        manifest = _read_json(preview_path / STATS_FIRST_PREVIEW_MANIFEST_FILE)
        boundary = str(manifest.get("apply_boundary") or "")
        if "preview_only" not in boundary or "does not overwrite" not in boundary:
            bad_manifests.append(str(snapshot.get("preview_id") or preview_path.name))
        output_name = str(manifest.get("output_file") or STATS_FIRST_PREVIEW_OUTPUT_FILE)
        if not (preview_path / output_name).exists():
            missing_outputs.append(str(snapshot.get("preview_id") or preview_path.name))
    if bad_manifests or missing_outputs:
        return SafetyGateCheck(
            gate="stats_first_preview_boundary",
            status="blocked",
            severity="error",
            detail=(
                f"{len(bad_manifests)} manifests lack preview-only boundary; "
                f"{len(missing_outputs)} previews lack output files."
            ),
            next_action="Regenerate malformed preview artifacts before any apply step.",
        )
    review_rows = stats_first_preview_review_rows(preview_root)
    blocked_rows = sum(1 for row in review_rows if row.get("review_status") == "blocked")
    review_count = sum(1 for row in review_rows if row.get("review_status") == "review")
    if blocked_rows:
        return SafetyGateCheck(
            gate="stats_first_preview_boundary",
            status="blocked",
            severity="error",
            detail=f"{blocked_rows} preview rows are blocked.",
            next_action="Fix normalized source rows and regenerate the preview.",
        )
    if review_count:
        return SafetyGateCheck(
            gate="stats_first_preview_boundary",
            status="review",
            severity="warning",
            detail=f"{len(snapshots)} previews found; {review_count} rows need review.",
            next_action="Inspect review rows before applying any preview.",
        )
    return SafetyGateCheck(
        gate="stats_first_preview_boundary",
        status="ready",
        severity="info",
        detail=f"{len(snapshots)} previews keep the preview-only boundary intact.",
        next_action="Only apply ready rows through the explicit copied-pack workflow.",
    )


def _stats_first_apply_gate(applied_pack_root: str | Path) -> SafetyGateCheck:
    root = Path(applied_pack_root)
    if not root.exists():
        return SafetyGateCheck(
            gate="stats_first_apply_boundary",
            status="review",
            severity="warning",
            detail="No stats-first applied pack copies were found.",
            next_action="Create an applied pack copy only after preview review is clean.",
        )
    manifests = list(root.glob(f"*/{STATS_FIRST_APPLIED_PACK_MANIFEST_FILE}"))
    if not manifests:
        return SafetyGateCheck(
            gate="stats_first_apply_boundary",
            status="review",
            severity="warning",
            detail="Applied pack root exists, but no stats-first applied manifests were found.",
            next_action="Use the explicit apply workflow when a preview is ready.",
        )
    missing_boundary = []
    for manifest_path in manifests:
        manifest = _read_json(manifest_path)
        effect = str(manifest.get("scoring_effect") or "")
        if "source pack" not in effect or "not overwritten" not in effect:
            missing_boundary.append(manifest_path.parent.name)
    if missing_boundary:
        return SafetyGateCheck(
            gate="stats_first_apply_boundary",
            status="blocked",
            severity="error",
            detail=f"{len(missing_boundary)} applied manifests lack no-overwrite evidence.",
            next_action="Regenerate those applied pack copies before selecting them.",
        )
    review_rows = stats_first_applied_pack_review_rows(applied_pack_root)
    blocked = sum(1 for row in review_rows if row.get("review_status") == "blocked")
    review = sum(1 for row in review_rows if row.get("review_status") == "review")
    if blocked:
        return SafetyGateCheck(
            gate="stats_first_apply_boundary",
            status="blocked",
            severity="error",
            detail=f"{blocked} applied pack copies are blocked.",
            next_action="Do not select blocked applied packs; regenerate from ready previews.",
        )
    if review:
        return SafetyGateCheck(
            gate="stats_first_apply_boundary",
            status="review",
            severity="warning",
            detail=f"{review} applied pack copies validate with review warnings.",
            next_action="Run Import Review admission before using any applied pack.",
        )
    return SafetyGateCheck(
        gate="stats_first_apply_boundary",
        status="ready",
        severity="info",
        detail=f"{len(manifests)} applied pack copies preserve no-overwrite boundaries.",
        next_action="Select only admitted applied packs for decision pages.",
    )


def _draft_freeze_gate(draft_freeze_root: str | Path) -> SafetyGateCheck:
    root = Path(draft_freeze_root)
    if not root.exists():
        return SafetyGateCheck(
            gate="draft_freeze_gate",
            status="review",
            severity="warning",
            detail="No draft-day freezes were found.",
            next_action="Create a final freeze after the selected pack is decision-ready.",
        )
    metadata_paths = sorted(root.glob("*/model_run_metadata.json"))
    if not metadata_paths:
        return SafetyGateCheck(
            gate="draft_freeze_gate",
            status="review",
            severity="warning",
            detail="Freeze root exists, but no model_run_metadata.json files were found.",
            next_action="Create a freeze through the Draft Freeze page.",
        )
    final_ready = 0
    review_only = 0
    invalid = 0
    for metadata_path in metadata_paths:
        metadata = _read_json(metadata_path)
        no_mutation = metadata.get("no_live_mutation") is True
        refresh_locked = metadata.get("refresh_after_freeze_allowed") is False
        certificate_path = metadata_path.parent / "board_exports" / "money_decision_certificate.csv"
        if not no_mutation or not refresh_locked or not certificate_path.exists():
            invalid += 1
            continue
        if metadata.get("decision_ready") is True and metadata.get("review_snapshot") is False:
            final_ready += 1
        else:
            review_only += 1
    if invalid:
        return SafetyGateCheck(
            gate="draft_freeze_gate",
            status="blocked",
            severity="error",
            detail=f"{invalid} freezes are missing lock/no-mutation/certificate evidence.",
            next_action="Regenerate invalid freezes before using them under draft pressure.",
        )
    if final_ready:
        return SafetyGateCheck(
            gate="draft_freeze_gate",
            status="ready",
            severity="info",
            detail=f"{final_ready} final freeze(s) found; {review_only} review snapshot(s) found.",
            next_action="Use the latest final-board freeze unless late news requires a new cycle.",
        )
    return SafetyGateCheck(
        gate="draft_freeze_gate",
        status="review",
        severity="warning",
        detail=f"{review_only} freeze snapshot(s) found, but none are final boards.",
        next_action="Clear review blockers and create a decision-ready freeze.",
    )


def _no_silent_mutation_policy_gate() -> SafetyGateCheck:
    return SafetyGateCheck(
        gate="no_silent_mutation_policy",
        status="ready",
        severity="info",
        detail=(
            "Stats-first previews are isolated, apply creates copied packs, and "
            "freeze creates backups/exports only."
        ),
        next_action=(
            "Keep using explicit create/apply/freeze buttons; do not edit "
            "generated outputs."
        ),
    )


def _overall_next_action(status: str) -> str:
    if status == "ready":
        return "Safety gates are clear; use the latest final freeze for draft-day decisions."
    if status == "blocked":
        return "Fix blocked safety gates before money decisions."
    return "Review warning gates and create a final freeze only after they are acceptable."


def _read_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
