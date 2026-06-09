from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.services.data_pack_diff_service import (
    DataPackDiffReport,
    build_data_pack_diff_report,
)
from src.services.data_pack_health_service import (
    DataPackHealthReport,
    build_data_pack_health_report,
)

MODEL_APPLIED_PACK_MANIFEST_FILE = "model_applied_pack_manifest.json"


@dataclass(frozen=True)
class AdmissionReason:
    severity: str
    area: str
    reason: str
    action: str


@dataclass(frozen=True)
class DataPackAdmissionReport:
    candidate_path: Path
    baseline_path: Path | None
    decision: str
    health_readiness: str
    diff_change_count: int
    reasons: tuple[AdmissionReason, ...]


def build_data_pack_admission_report(
    *,
    candidate_data_pack: str | Path,
    baseline_data_pack: str | Path | None = None,
    roster_limit: int = 24,
) -> DataPackAdmissionReport:
    health = build_data_pack_health_report(candidate_data_pack, roster_limit=roster_limit)
    diff = (
        build_data_pack_diff_report(
            baseline_data_pack=baseline_data_pack,
            candidate_data_pack=candidate_data_pack,
        )
        if baseline_data_pack
        else None
    )
    reasons = tuple(_admission_reasons(health, diff))
    decision = _admission_decision(reasons)
    return DataPackAdmissionReport(
        candidate_path=Path(candidate_data_pack).resolve(),
        baseline_path=Path(baseline_data_pack).resolve() if baseline_data_pack else None,
        decision=decision,
        health_readiness=health.readiness,
        diff_change_count=_diff_change_count(diff),
        reasons=reasons,
    )


def admission_summary_row(report: DataPackAdmissionReport) -> dict[str, object]:
    return {
        "decision": report.decision,
        "health": report.health_readiness,
        "diff_changes": report.diff_change_count,
        "candidate_path": str(report.candidate_path),
        "baseline_path": str(report.baseline_path) if report.baseline_path else "",
    }


def admission_reason_rows(report: DataPackAdmissionReport) -> list[dict[str, object]]:
    return [
        {
            "severity": reason.severity,
            "area": reason.area,
            "reason": reason.reason,
            "action": reason.action,
        }
        for reason in report.reasons
    ]


def _admission_reasons(
    health: DataPackHealthReport,
    diff: DataPackDiffReport | None,
) -> list[AdmissionReason]:
    reasons: list[AdmissionReason] = []
    applied_reason = _applied_pack_admission_reason(health)
    if applied_reason is not None:
        reasons.append(applied_reason)
    if health.error_count:
        reasons.append(
            AdmissionReason(
                "blocked",
                "schema",
                f"{health.error_count} validation errors are present.",
                "Fix blocking CSV validation errors before using this pack.",
            )
        )
    if health.league_rank_coverage_pct == 0:
        reasons.append(
            AdmissionReason(
                "blocked",
                "league_rank",
                "No league ranks are present.",
                "Merge the league-rank PDF/text before trusting release-rule views.",
            )
        )
    elif health.league_rank_coverage_pct < 95:
        reasons.append(
            AdmissionReason(
                "review",
                "league_rank",
                f"League-rank coverage is {health.league_rank_coverage_pct:.1f}%.",
                (
                    "Review missing league-rank rows before Required Top-Five "
                    "Release Slot decisions."
                ),
            )
        )
    if health.placeholder_model_output_count:
        reasons.append(
            AdmissionReason(
                "review",
                "model_outputs",
                f"{health.placeholder_model_output_count} neutral placeholders are present.",
                "Replace placeholder model outputs before trusting keeper/drop scores.",
            )
        )
    if health.warning_count and not reasons:
        reasons.append(
            AdmissionReason(
                "review",
                "validation",
                f"{health.warning_count} validation warnings are present.",
                "Review warning rows before final use.",
            )
        )
    if diff is not None:
        reasons.extend(_diff_reasons(diff))
    if not reasons:
        reasons.append(
            AdmissionReason(
                "ready",
                "admission",
                "Pack health and comparison checks are clear.",
                "This pack is admitted for local draft-room use.",
            )
        )
    return reasons


def _applied_pack_admission_reason(
    health: DataPackHealthReport,
) -> AdmissionReason | None:
    manifest_path = health.data_pack_path / MODEL_APPLIED_PACK_MANIFEST_FILE
    if not manifest_path.exists():
        return None
    manifest = _read_manifest(manifest_path)
    applied_row_count = _int_or_zero(manifest.get("applied_row_count", 0))
    if health.error_count:
        return AdmissionReason(
            "blocked",
            "generated_applied_pack",
            "Generated applied pack has validation errors.",
            "Regenerate or fix the applied pack before using it.",
        )
    if _health_check_status(health, "model_outputs") == "blocked":
        return AdmissionReason(
            "blocked",
            "generated_applied_pack",
            "Generated applied pack has no usable model output rows.",
            "Regenerate the applied pack from ready promotion candidates.",
        )
    if applied_row_count <= 0:
        return AdmissionReason(
            "blocked",
            "generated_applied_pack",
            "Generated applied pack reports zero applied model rows.",
            "Regenerate the applied pack from ready promotion candidates.",
        )
    if health.readiness != "ready":
        return AdmissionReason(
            "review",
            "generated_applied_pack",
            "Generated applied pack exists, but pack health still needs review.",
            "Review Import Review warnings before using this generated pack.",
        )
    return AdmissionReason(
        "ready",
        "generated_applied_pack",
        "Generated applied pack passed manifest and health admission checks.",
        "Use this pack only after this Import Review decision stays ready.",
    )


def _diff_reasons(diff: DataPackDiffReport) -> list[AdmissionReason]:
    reasons: list[AdmissionReason] = []
    roster_change_count = (
        len(diff.roster_added) + len(diff.roster_removed) + len(diff.roster_moved)
    )
    if roster_change_count:
        reasons.append(
            AdmissionReason(
                "review",
                "rosters",
                f"{roster_change_count} roster changes versus baseline.",
                "Review roster changes before using keeper or trade boards.",
            )
        )
    if diff.league_rank_changed:
        reasons.append(
            AdmissionReason(
                "review",
                "league_rank",
                f"{len(diff.league_rank_changed)} league-rank changes versus baseline.",
                (
                    "Review league-rank changes before relying on Required "
                    "Top-Five Release Slot pressure."
                ),
            )
        )
    if diff.pick_owner_changed:
        reasons.append(
            AdmissionReason(
                "review",
                "future_picks",
                f"{len(diff.pick_owner_changed)} pick-owner changes versus baseline.",
                "Review pick ownership before trade or draft-room decisions.",
            )
        )
    return reasons


def _admission_decision(reasons: tuple[AdmissionReason, ...]) -> str:
    if any(reason.severity == "blocked" for reason in reasons):
        return "blocked"
    if any(reason.severity == "review" for reason in reasons):
        return "review"
    return "ready"


def _diff_change_count(diff: DataPackDiffReport | None) -> int:
    if diff is None:
        return 0
    return (
        len(diff.roster_added)
        + len(diff.roster_removed)
        + len(diff.roster_moved)
        + len(diff.league_rank_changed)
        + len(diff.pick_owner_changed)
    )


def _health_check_status(health: DataPackHealthReport, check_name: str) -> str:
    for check in health.checks:
        if check.check_name == check_name:
            return check.status
    return ""


def _read_manifest(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _int_or_zero(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
