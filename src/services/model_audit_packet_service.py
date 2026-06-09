from __future__ import annotations

import csv
import json
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.services.command_board_service import (
    ACTIVE_STATS_FIRST_MODEL_DIR,
    build_team_command_board,
    build_war_board,
)
from src.services.confidence_calibration_audit_service import (
    build_confidence_calibration_audit,
)
from src.services.forced_release_strategy_service import build_forced_release_strategy
from src.services.model_recalibration_service import (
    model_recalibration_policy,
    rankings_are_review_only,
)
from src.services.movement_reason_service import (
    classify_movement,
    movement_review_label,
)
from src.services.named_player_audit_service import build_named_player_audit
from src.services.pre_decision_checklist_service import (
    build_pre_decision_checklist,
    pre_decision_checklist_rows,
    pre_decision_checklist_summary_row,
)
from src.services.route_participation_gap_gate_service import (
    build_route_participation_gap_gate_report,
)
from src.services.source_coverage_audit_service import build_source_coverage_audit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_AUDIT_ROOT = PROJECT_ROOT / "local_exports" / "model_audits"
AUDITOR_PROMPT_PATH = (
    PROJECT_ROOT / "docs" / "codex" / "PROJECT_GOLD_AUDIT_PACKET_V2_AUDITOR_PROMPT.md"
)

STATS_FIRST_OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"
STATS_FIRST_NORMALIZED_FILE = "stats_first_normalized_features.csv"
STATS_FIRST_CONTRIBUTION_FILE = "stats_first_feature_contributions.csv"
STATS_FIRST_COVERAGE_FILE = "stats_first_source_coverage.csv"
STATS_FIRST_OUTLIER_FILE = "stats_first_preview_outliers.csv"

SOURCE_EXPORTS: tuple[tuple[str, str, str], ...] = (
    ("full_active_rankings", STATS_FIRST_OUTPUT_FILE, "full_active_rankings.csv"),
    ("normalized_feature_rows", STATS_FIRST_NORMALIZED_FILE, "normalized_feature_rows.csv"),
    ("contribution_receipts", STATS_FIRST_CONTRIBUTION_FILE, "contribution_receipts.csv"),
    ("source_coverage_rows", STATS_FIRST_COVERAGE_FILE, "source_coverage_rows.csv"),
    ("outlier_rows", STATS_FIRST_OUTLIER_FILE, "outlier_rows.csv"),
)


@dataclass(frozen=True)
class AuditExportFile:
    key: str
    file_name: str
    path: str
    row_count: int
    source_path: str


@dataclass(frozen=True)
class ModelAuditPacket:
    packet_id: str
    export_dir: Path
    manifest_path: Path
    manifest: dict[str, object]
    files: tuple[AuditExportFile, ...]


def export_model_audit_packet(
    data_pack_path: str | Path,
    *,
    export_root: str | Path = DEFAULT_MODEL_AUDIT_ROOT,
    model_source_root: str | Path = ACTIVE_STATS_FIRST_MODEL_DIR,
    comparison_baseline: str | Path | None = None,
    movement_export_name: str = "movement_vs_checkpoint.csv",
    packet_id: str | None = None,
) -> ModelAuditPacket:
    """Export the current review-only model state into a repeatable audit packet."""

    data_pack = Path(data_pack_path)
    source_root = Path(model_source_root)
    packet = packet_id or _default_packet_id()
    export_dir = Path(export_root) / packet
    export_dir.mkdir(parents=True, exist_ok=False)

    exported: list[AuditExportFile] = []
    model_metadata = _model_metadata(source_root / STATS_FIRST_OUTPUT_FILE)

    for key, source_name, export_name in SOURCE_EXPORTS:
        exported.append(
            _copy_csv_export(
                key=key,
                source_path=source_root / source_name,
                destination_path=export_dir / export_name,
            )
        )

    war_board = build_war_board(data_pack)
    exported.append(
        _write_rows_export(
            key="visible_war_board_rankings",
            rows=war_board.rows,
            destination_path=export_dir / "visible_war_board_rankings.csv",
            source_path=data_pack,
        )
    )
    team_board = build_team_command_board(data_pack)
    exported.append(
        _write_rows_export(
            key="niners_roster_rankings",
            rows=team_board.roster_rows,
            destination_path=export_dir / "niners_roster_rankings.csv",
            source_path=data_pack,
        )
    )

    named_audit = build_named_player_audit(data_pack, veteran_model_dir=source_root)
    exported.append(
        _write_rows_export(
            key="named_player_audit_rows",
            rows=named_audit.player_rows,
            destination_path=export_dir / "named_player_audit_rows.csv",
            source_path=data_pack,
        )
    )
    exported.append(
        _write_rows_export(
            key="named_player_pair_rows",
            rows=named_audit.pair_rows,
            destination_path=export_dir / "named_player_pair_rows.csv",
            source_path=data_pack,
        )
    )
    exported.append(
        _write_rows_export(
            key="named_player_receipt_rows",
            rows=named_audit.receipt_rows,
            destination_path=export_dir / "named_player_receipt_rows.csv",
            source_path=source_root,
        )
    )

    exported.extend(_sprint4_v2_exports(data_pack, source_root, export_dir))

    if comparison_baseline:
        exported.append(
            _write_movement_export(
                current_rankings_path=export_dir / "full_active_rankings.csv",
                baseline_path=Path(comparison_baseline),
                destination_path=export_dir / movement_export_name,
            )
        )

    recalibration = model_recalibration_policy()
    review_only = rankings_are_review_only(calibration_passed=False)
    files_manifest = {
        entry.key: {
            "file_name": entry.file_name,
            "path": entry.path,
            "source_path": entry.source_path,
            "row_count": entry.row_count,
        }
        for entry in exported
    }
    manifest: dict[str, object] = {
        "packet_id": packet,
        "generated_at": datetime.now(UTC).isoformat(),
        "active_data_pack": str(data_pack),
        "active_model_source_root": str(source_root),
        "active_model_version": model_metadata["model_version"],
        "computed_at": model_metadata["computed_at"],
        "model_recalibration_active": recalibration.active,
        "review_only_status": review_only,
        "decision_ready_allowed": False,
        "trust_status": recalibration.status,
        "trust_title": recalibration.title,
        "trust_message": recalibration.message,
        "trust_next_action": recalibration.next_action,
        "files": files_manifest,
        "row_counts": {entry.key: entry.row_count for entry in exported},
    }
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    return ModelAuditPacket(
        packet_id=packet,
        export_dir=export_dir,
        manifest_path=manifest_path,
        manifest=manifest,
        files=tuple(exported),
    )


def _copy_csv_export(
    *,
    key: str,
    source_path: Path,
    destination_path: Path,
) -> AuditExportFile:
    if not source_path.exists():
        raise FileNotFoundError(f"Missing required audit source file: {source_path}")
    shutil.copy2(source_path, destination_path)
    return AuditExportFile(
        key=key,
        file_name=destination_path.name,
        path=str(destination_path),
        row_count=_csv_row_count(destination_path),
        source_path=str(source_path),
    )


def _write_rows_export(
    *,
    key: str,
    rows: Iterable[dict[str, object]],
    destination_path: Path,
    source_path: Path,
) -> AuditExportFile:
    row_list = [dict(row) for row in rows]
    _write_dict_rows(destination_path, row_list)
    return AuditExportFile(
        key=key,
        file_name=destination_path.name,
        path=str(destination_path),
        row_count=len(row_list),
        source_path=str(source_path),
    )


_REPORT_ERRORS: dict[str, str] = {}


def _sprint4_v2_exports(
    data_pack: Path,
    source_root: Path,
    export_dir: Path,
) -> list[AuditExportFile]:
    exported: list[AuditExportFile] = []

    forced_strategy = _safe_build_report(
        "forced_release_comparison",
        lambda: build_forced_release_strategy(data_pack),
    )
    exported.append(
        _write_rows_export(
            key="forced_release_comparison",
            rows=(
                forced_strategy.candidate_rows
                if forced_strategy is not None
                else _error_rows("forced_release_comparison")
            ),
            destination_path=export_dir / "forced_release_comparison.csv",
            source_path=data_pack,
        )
    )

    confidence = _safe_build_report(
        "confidence_audit",
        lambda: build_confidence_calibration_audit(
            data_pack,
            veteran_model_dir=source_root,
        ),
    )
    exported.append(
        _write_rows_export(
            key="confidence_audit",
            rows=confidence.rows if confidence is not None else _error_rows("confidence_audit"),
            destination_path=export_dir / "confidence_audit.csv",
            source_path=source_root,
        )
    )
    exported.append(
        _write_rows_export(
            key="confidence_audit_summary",
            rows=(
                confidence.summary_rows
                if confidence is not None
                else _error_rows("confidence_audit_summary")
            ),
            destination_path=export_dir / "confidence_audit_summary.csv",
            source_path=source_root,
        )
    )

    coverage = _safe_build_report(
        "source_gap_reconciliation",
        lambda: build_source_coverage_audit(data_pack, veteran_model_dir=source_root),
    )
    exported.extend(_coverage_exports(coverage, export_dir, source_root))

    route_gaps = _safe_build_report(
        "route_participation_gap_report",
        lambda: build_route_participation_gap_gate_report(source_root),
    )
    exported.extend(_route_gap_exports(route_gaps, export_dir, source_root))

    checklist = _safe_build_report(
        "decision_checklist",
        lambda: build_pre_decision_checklist(data_pack, veteran_model_dir=source_root),
    )
    exported.append(
        _write_rows_export(
            key="decision_checklist",
            rows=(
                pre_decision_checklist_rows(checklist)
                if checklist is not None
                else _error_rows("decision_checklist")
            ),
            destination_path=export_dir / "decision_checklist.csv",
            source_path=data_pack,
        )
    )
    exported.append(
        _write_rows_export(
            key="decision_checklist_summary",
            rows=(
                [pre_decision_checklist_summary_row(checklist)]
                if checklist is not None
                else _error_rows("decision_checklist_summary")
            ),
            destination_path=export_dir / "decision_checklist_summary.csv",
            source_path=data_pack,
        )
    )

    exported.append(
        _write_rows_export(
            key="projection_guardrail_report",
            rows=_projection_guardrail_rows(source_root),
            destination_path=export_dir / "projection_guardrail_report.csv",
            source_path=source_root,
        )
    )
    exported.append(
        _write_text_export(
            key="sprint4_changelog_from_sprint3_phase20",
            content=_sprint4_changelog(),
            destination_path=export_dir / "sprint4_changelog_from_sprint3_phase20.md",
            source_path=PROJECT_ROOT / "docs" / "codex",
        )
    )

    prompt = _audit_packet_v2_prompt()
    AUDITOR_PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDITOR_PROMPT_PATH.write_text(prompt, encoding="utf-8")
    exported.append(
        _write_text_export(
            key="neutral_auditor_prompt",
            content=prompt,
            destination_path=export_dir / "neutral_auditor_prompt.md",
            source_path=AUDITOR_PROMPT_PATH,
        )
    )
    return exported


def _coverage_exports(
    coverage: object | None,
    export_dir: Path,
    source_root: Path,
) -> list[AuditExportFile]:
    if coverage is None:
        return [
            _write_rows_export(
                key="source_gap_reconciliation_summary",
                rows=_error_rows("source_gap_reconciliation"),
                destination_path=export_dir / "source_gap_reconciliation_summary.csv",
                source_path=source_root,
            )
        ]
    return [
        _write_rows_export(
            key="source_gap_reconciliation_players",
            rows=coverage.player_rows,
            destination_path=export_dir / "source_gap_reconciliation_players.csv",
            source_path=source_root,
        ),
        _write_rows_export(
            key="source_gap_reconciliation_buckets",
            rows=coverage.bucket_rows,
            destination_path=export_dir / "source_gap_reconciliation_buckets.csv",
            source_path=source_root,
        ),
        _write_rows_export(
            key="source_gap_reconciliation_features",
            rows=coverage.feature_rows,
            destination_path=export_dir / "source_gap_reconciliation_features.csv",
            source_path=source_root,
        ),
        _write_rows_export(
            key="source_gap_reconciliation_summary",
            rows=coverage.summary_rows,
            destination_path=export_dir / "source_gap_reconciliation_summary.csv",
            source_path=source_root,
        ),
        _write_rows_export(
            key="accepted_source_gap_rows",
            rows=coverage.accepted_review_gap_rows,
            destination_path=export_dir / "accepted_source_gap_rows.csv",
            source_path=source_root,
        ),
        _write_rows_export(
            key="unaccepted_source_gap_rows",
            rows=coverage.review_gap_rows,
            destination_path=export_dir / "unaccepted_source_gap_rows.csv",
            source_path=source_root,
        ),
    ]


def _route_gap_exports(
    route_gaps: object | None,
    export_dir: Path,
    source_root: Path,
) -> list[AuditExportFile]:
    if route_gaps is None:
        return [
            _write_rows_export(
                key="route_participation_gap_summary",
                rows=_error_rows("route_participation_gap_report"),
                destination_path=export_dir / "route_participation_gap_summary.csv",
                source_path=source_root,
            )
        ]
    return [
        _write_rows_export(
            key="route_participation_gap_players",
            rows=route_gaps.rows,
            destination_path=export_dir / "route_participation_gap_players.csv",
            source_path=source_root,
        ),
        _write_rows_export(
            key="route_participation_gap_areas",
            rows=route_gaps.area_rows,
            destination_path=export_dir / "route_participation_gap_areas.csv",
            source_path=source_root,
        ),
        _write_rows_export(
            key="route_participation_gap_summary",
            rows=route_gaps.summary_rows,
            destination_path=export_dir / "route_participation_gap_summary.csv",
            source_path=source_root,
        ),
    ]


def _safe_build_report(key: str, builder):
    try:
        return builder()
    except Exception as exc:  # pragma: no cover - keeps packet transparent on failures
        _REPORT_ERRORS[key] = str(exc)
        return None


def _error_rows(key: str) -> list[dict[str, object]]:
    return [
        {
            "audit_status": "export_error",
            "report": key,
            "error": _REPORT_ERRORS.get(key, "Report could not be built."),
        }
    ]


def _write_movement_export(
    *,
    current_rankings_path: Path,
    baseline_path: Path,
    destination_path: Path,
) -> AuditExportFile:
    baseline_rankings_path = _rankings_csv_path(baseline_path)
    current_rows = _read_dict_rows(current_rankings_path)
    baseline_rows = _rows_by_player_id(_read_dict_rows(baseline_rankings_path))
    movement_rows = [
        _movement_row(current=row, previous=baseline_rows.get(str(row.get("player_id") or "")))
        for row in current_rows
    ]
    _write_dict_rows(destination_path, movement_rows)
    return AuditExportFile(
        key=_movement_export_key(destination_path.name),
        file_name=destination_path.name,
        path=str(destination_path),
        row_count=len(movement_rows),
        source_path=str(baseline_rankings_path),
    )


def _movement_row(
    *,
    current: dict[str, object],
    previous: dict[str, object] | None,
) -> dict[str, object]:
    rank_delta = _delta(current, previous, "overall_rank")
    private_delta = _delta(current, previous, "private_lve_value")
    keeper_delta = _delta(current, previous, "keeper_score")
    drop_delta = _delta(current, previous, "drop_candidate_score")
    confidence_delta = _delta(current, previous, "confidence_score")
    classification = classify_movement(
        current,
        previous,
        rank_delta=rank_delta,
        value_delta=private_delta,
        keeper_delta=keeper_delta,
        confidence_delta=confidence_delta,
    )
    return {
        "player_id": current.get("player_id", ""),
        "player_name": current.get("player_name", ""),
        "position": current.get("position", ""),
        "old_overall_rank": _previous_value(previous, "overall_rank"),
        "new_overall_rank": current.get("overall_rank", ""),
        "overall_rank_delta": rank_delta,
        "old_position_rank": _previous_value(previous, "position_rank_label", "position_rank"),
        "new_position_rank": current.get("position_rank_label") or current.get("position_rank", ""),
        "old_private_lve_value": _previous_value(previous, "private_lve_value"),
        "new_private_lve_value": current.get("private_lve_value", ""),
        "private_lve_value_delta": private_delta,
        "old_keeper_score": _previous_value(previous, "keeper_score"),
        "new_keeper_score": current.get("keeper_score", ""),
        "keeper_score_delta": keeper_delta,
        "old_drop_candidate_score": _previous_value(previous, "drop_candidate_score"),
        "new_drop_candidate_score": current.get("drop_candidate_score", ""),
        "drop_candidate_score_delta": drop_delta,
        "old_confidence_score": _previous_value(previous, "confidence_score"),
        "new_confidence_score": current.get("confidence_score", ""),
        "confidence_score_delta": confidence_delta,
        "old_warning_status": _previous_value(previous, "warning_status"),
        "new_warning_status": current.get("warning_status", ""),
        "old_rank_audit": _previous_value(previous, "rank_audit"),
        "new_rank_audit": current.get("rank_audit", ""),
        "movement_reason": classification.movement_reason,
        "movement_magnitude": classification.movement_magnitude,
        "movement_review_flag": classification.movement_review_flag,
        "movement_review_label": movement_review_label(classification),
        "movement_note": "matched" if previous is not None else "new_player_in_current_rankings",
    }


def _write_text_export(
    *,
    key: str,
    content: str,
    destination_path: Path,
    source_path: Path,
) -> AuditExportFile:
    destination_path.write_text(content, encoding="utf-8")
    return AuditExportFile(
        key=key,
        file_name=destination_path.name,
        path=str(destination_path),
        row_count=0,
        source_path=str(source_path),
    )


def _projection_guardrail_rows(source_root: Path) -> list[dict[str, object]]:
    normalized_path = source_root / STATS_FIRST_NORMALIZED_FILE
    rows = _read_dict_rows(normalized_path) if normalized_path.exists() else []
    if not rows:
        return _error_rows("projection_guardrail_report")
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        status = str(row.get("projection_source_status") or "missing_projection")
        grouped.setdefault(status, []).append(row)
    output: list[dict[str, object]] = []
    for status, status_rows in sorted(grouped.items()):
        expected_scores = [
            _to_float(row.get("expected_lve_points_score"))
            for row in status_rows
            if str(row.get("expected_lve_points_score") or "") != ""
        ]
        confidence_values = [
            _to_float(row.get("confidence"))
            for row in status_rows
            if str(row.get("confidence") or "") != ""
        ]
        output.append(
            {
                "projection_source_status": status,
                "players": len(status_rows),
                "expected_lve_points_score_50_count": sum(
                    1 for value in expected_scores if value == 50.0
                ),
                "average_expected_lve_points_score": _average(expected_scores),
                "average_confidence": _average(confidence_values),
                "decision_meaning": _projection_status_meaning(status),
                "guardrail": (
                    "local baseline, not forecast"
                    if status == "local_baseline_projection"
                    else "status visible in receipts/source coverage"
                ),
            }
        )
    return output


def _average(values: list[float]) -> float | str:
    if not values:
        return ""
    return round(sum(values) / len(values), 2)


def _projection_status_meaning(status: str) -> str:
    if status == "independent_projection":
        return "Independent projection source is present."
    if status == "local_baseline_projection":
        return "Local baseline is visible and must not be treated as forecast evidence."
    if status == "disabled_projection":
        return "Projection is intentionally disabled for this row."
    return "Projection missing or not imported; confidence/review penalty stays visible."


def _sprint4_changelog() -> str:
    phase_docs = [
        "PROJECT_GOLD_SPRINT_4_PHASE_21_EXTERNAL_AUDIT_TRIAGE.md",
        "PROJECT_GOLD_SPRINT_4_PHASE_22_TOP_FIVE_LANGUAGE_RECONCILIATION.md",
        "PROJECT_GOLD_SPRINT_4_PHASE_23_CONFIDENCE_CALIBRATION_AUDIT.md",
        "PROJECT_GOLD_SPRINT_4_PHASE_25_MOVEMENT_REASON_TRACKING.md",
        "PROJECT_GOLD_SPRINT_4_PHASE_26_SOURCE_GAP_RECONCILIATION.md",
        "PROJECT_GOLD_SPRINT_4_PHASE_27_PROJECTION_BASELINE_GUARDRAIL.md",
        "PROJECT_GOLD_SPRINT_4_PHASE_28_ROUTE_PARTICIPATION_GAP_GATE.md",
    ]
    existing = [
        doc for doc in phase_docs if (PROJECT_ROOT / "docs" / "codex" / doc).exists()
    ]
    missing = sorted(set(phase_docs) - set(existing))
    lines = [
        "# Sprint 4 Changelog From Sprint 3 Phase 20",
        "",
        "This packet is an audit export, not a readiness unlock. It preserves unresolved "
        "issues and keeps readiness labels controlled by the gates.",
        "",
        "## Included Sprint 4 Artifacts",
    ]
    lines.extend(f"- {doc}" for doc in existing)
    if missing:
        lines.extend(["", "## Missing Or Not Yet Written"])
        lines.extend(f"- {doc}" for doc in missing)
    lines.extend(
        [
            "",
            "## Main Changes Since Sprint 3 Phase 20",
            "- External audit findings were triaged instead of accepted blindly.",
            "- Top-five language was clarified as the roster's league-rank top five.",
            "- Confidence calibration and source-gap reconciliation were made exportable.",
            "- Projection baselines were labeled as local baselines, not forecasts.",
            "- Route/participation gaps were made explicit for Niners, top assets, "
            "WR/TEs, and RB receiving-role players.",
            "- Movement reasons are included when generated with a Sprint 3 comparison baseline.",
            "",
            "## Readiness",
            "Readiness labels are unchanged unless the app's gates independently pass.",
        ]
    )
    return "\n".join(lines) + "\n"


def _audit_packet_v2_prompt() -> str:
    lines = [
        "You are a senior fantasy-football model auditor and data-quality investigator.",
        "",
        "Project context:",
        "This is a local-first deterministic dynasty fantasy football model for a "
        "10-team 1QB league with no PPR, 0.4 rushing/receiving first-down bonus, "
        "3 WR, 2 RB, 1 TE, 2 flex, no TE premium, deep benches, 23 keepers, and a "
        "forced roster league-rank top-five release rule.",
        "",
        "Goal:",
        "Audit the attached Project Gold Audit Packet V2 scientifically. Do not "
        "tune rankings to match opinions. Diagnose whether rankings, roster "
        "decisions, confidence labels, source gaps, and forced-release outputs "
        "are supported by the exported evidence.",
        "",
        "Required audit areas:",
        "1. Check whether active rankings use the intended stats-first source and "
        "whether movement reasons are explainable.",
        "2. Check whether private/model value is isolated from trade-market value.",
        "3. Check whether confidence labels match source coverage, projection "
        "status, route/participation gaps, identity, and outlier status.",
        "4. Check whether local baseline projections are clearly treated as local "
        "baselines, not real forecasts.",
        "5. Check whether route/participation gaps materially limit trust for "
        "roster decisions.",
        "6. Check whether the forced-release comparison ranks only the roster's "
        "league-rank top five for required release logic.",
        "7. Check whether receipts reconcile to visible scores and reveal hidden "
        "defaults or imputation.",
        "8. Identify confirmed bugs, likely bugs, source gaps, terminology/UI "
        "issues, model-policy decisions, and false positives separately.",
        "",
        "Important constraints:",
        "- Do not assume public market value is private football value.",
        "- Do not assume league rank is player quality; it is a rule/availability signal.",
        "- Do not hide unresolved issues.",
        "- If evidence is missing, say exactly what data is missing and whether "
        "that should block roster, draft, or final money decisions.",
        "",
        "Output:",
        "Produce a triage report with severity, evidence, affected files/exports, "
        "likely cause, and recommended next action.",
    ]
    return "\n".join(lines) + "\n"


def _rankings_csv_path(path: Path) -> Path:
    if path.is_file():
        return path
    rankings_path = path / "full_active_rankings.csv"
    if rankings_path.exists():
        return rankings_path
    raise FileNotFoundError(f"Missing baseline rankings file: {rankings_path}")


def _read_dict_rows(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _rows_by_player_id(rows: Iterable[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _previous_value(
    previous: dict[str, object] | None,
    field: str,
    fallback_field: str | None = None,
) -> object:
    if previous is None:
        return ""
    value = previous.get(field, "")
    if value == "" and fallback_field:
        return previous.get(fallback_field, "")
    return value


def _delta(
    current: dict[str, object],
    previous: dict[str, object] | None,
    field: str,
) -> float | str:
    if previous is None:
        return ""
    return round(_to_float(current.get(field)) - _to_float(previous.get(field)), 2)


def _to_float(value: object) -> float:
    try:
        text = str(value or "").strip()
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def _movement_export_key(file_name: str) -> str:
    return Path(file_name).stem


def _write_dict_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = _fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _fieldnames(rows: list[dict[str, object]]) -> list[str]:
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for field in row:
            if field not in seen:
                fieldnames.append(field)
                seen.add(field)
    return fieldnames or ["audit_note"]


def _model_metadata(output_path: Path) -> dict[str, str]:
    if not output_path.exists():
        raise FileNotFoundError(f"Missing required model output file: {output_path}")
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        first = next(reader, {})
    return {
        "model_version": str(first.get("model_version") or ""),
        "computed_at": str(first.get("computed_at") or ""),
    }


def _csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _row in reader)


def _default_packet_id() -> str:
    return "model_audit_" + datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
