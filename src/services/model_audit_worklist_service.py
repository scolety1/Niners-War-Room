from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.services.final_calibration_gate_service import build_final_calibration_gate
from src.services.model_outlier_service import (
    build_model_outlier_report,
    is_review_required_bucket,
)
from src.services.player_feature_receipts_service import DEFAULT_RECEIPT_VETERAN_MODEL_DIR
from src.services.source_coverage_audit_service import build_source_coverage_audit


@dataclass(frozen=True)
class ModelAuditWorklistReport:
    rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    issues: list[str]
    source_root: str


def build_model_audit_worklist(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> ModelAuditWorklistReport:
    source_root = (
        Path(veteran_model_dir)
        if veteran_model_dir
        else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    calibration = build_final_calibration_gate(
        data_pack_path,
        veteran_model_dir=source_root,
        identity_source_root=source_root,
    )
    coverage = build_source_coverage_audit(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    outliers = build_model_outlier_report(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    rows = [
        *_calibration_rows(calibration),
        *_coverage_rows(coverage.missing_critical_rows),
        *_outlier_rows(outliers.rows),
    ]
    rows = sorted(
        rows,
        key=lambda row: (
            int(row["priority_order"]),
            str(row["area"]),
            str(row["player"]).lower(),
            str(row["item"]),
        ),
    )
    return ModelAuditWorklistReport(
        rows=rows,
        summary_rows=_summary_rows(rows),
        issues=[*coverage.issues, *outliers.issues],
        source_root=str(source_root),
    )


def _calibration_rows(calibration: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for check in calibration.checks:
        if check.status == "ready":
            continue
        priority = "blocker" if check.status == "blocked" else "review"
        rows.append(
            _worklist_row(
                priority=priority,
                area="calibration_gate",
                item=check.gate,
                player="",
                position="",
                team="",
                detail=check.detail,
                next_action=check.next_action,
            )
        )
    return rows


def _coverage_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        _worklist_row(
            priority="blocker",
            area="source_coverage",
            item=str(row["bucket"]),
            player=str(row["player"]),
            position=str(row["position"]),
            team=str(row["team"]),
            detail=(
                f"Missing critical {row['bucket']} inputs: "
                f"{row.get('missing_features', '')}."
            ),
            next_action="Fill, import, or explicitly approve this source bucket.",
        )
        for row in rows
    ]


def _outlier_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        if not is_review_required_bucket(row["bucket"]):
            continue
        severity = str(row["severity"])
        if severity not in {"blocking", "high", "medium"}:
            continue
        output.append(
            _worklist_row(
                priority="blocker" if severity in {"blocking", "high"} else "review",
                area="ranking_outlier",
                item=str(row["outlier_type"]),
                player=str(row["player"]),
                position=str(row["position"]),
                team=str(row["team"]),
                detail=str(row["reason"]),
                next_action=str(row["suggested_review"]),
                model_rank=row.get("model_rank", ""),
                position_rank=row.get("position_rank", ""),
            )
        )
    return output


def _worklist_row(
    *,
    priority: str,
    area: str,
    item: str,
    player: str,
    position: str,
    team: str,
    detail: str,
    next_action: str,
    model_rank: object = "",
    position_rank: object = "",
) -> dict[str, object]:
    return {
        "priority": priority,
        "priority_order": 0 if priority == "blocker" else 1,
        "area": area,
        "item": item,
        "player": player,
        "position": position,
        "team": team,
        "model_rank": model_rank,
        "position_rank": position_rank,
        "detail": detail,
        "next_action": next_action,
    }


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for area in sorted({str(row["area"]) for row in rows}):
        area_rows = [row for row in rows if row["area"] == area]
        output.append(
            {
                "area": area,
                "items": len(area_rows),
                "blockers": sum(1 for row in area_rows if row["priority"] == "blocker"),
                "review": sum(1 for row in area_rows if row["priority"] == "review"),
            }
        )
    if not output:
        output.append(
            {
                "area": "all_clear",
                "items": 0,
                "blockers": 0,
                "review": 0,
            }
        )
    return output
