from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.command_board_service import build_team_command_board, build_war_board
from src.services.data_pack_admission_service import (
    admission_reason_rows,
    admission_summary_row,
    build_data_pack_admission_report,
)
from src.services.data_pack_health_service import (
    build_data_pack_health_report,
    coverage_report_rows,
    health_check_rows,
    readiness_status_rows,
)
from src.services.draft_service import build_draft_room
from src.services.final_calibration_gate_service import (
    build_final_calibration_gate,
    final_calibration_gate_rows,
    final_calibration_gate_summary_row,
)
from src.services.league_service import build_league_intel
from src.services.lve_stats_first_apply_service import (
    DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
    STATS_FIRST_APPLIED_PACK_MANIFEST_FILE,
)
from src.services.lve_stats_first_preview_service import (
    DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    STATS_FIRST_PREVIEW_MANIFEST_FILE,
)
from src.services.model_recalibration_service import rankings_are_review_only
from src.services.trust_status_service import trust_status_row

DEFAULT_FREEZE_ROOT = Path("local_exports/draft_freezes")


@dataclass(frozen=True)
class DraftFreezeResult:
    freeze_id: str
    freeze_dir: Path
    data_pack_backup_dir: Path
    export_files: dict[str, Path]
    metadata_path: Path
    checklist_path: Path
    summary_path: Path


def freeze_draft_pack(
    data_pack_path: str | Path,
    *,
    output_root: str | Path = DEFAULT_FREEZE_ROOT,
    freeze_id: str | None = None,
    allow_review_snapshot: bool = False,
    stats_first_preview_root: str | Path = DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    stats_first_applied_pack_root: str | Path = DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
) -> DraftFreezeResult:
    source_pack = Path(data_pack_path).resolve()
    validated = validate_data_pack(source_pack)
    health = build_data_pack_health_report(source_pack)
    admission = build_data_pack_admission_report(candidate_data_pack=source_pack)
    calibration_report = build_final_calibration_gate(
        source_pack,
        stats_first_preview_root=stats_first_preview_root,
    )
    calibration_passed = calibration_report.passed
    if (
        admission.decision != "ready"
        or rankings_are_review_only(calibration_passed=calibration_passed)
        or not calibration_passed
    ) and not allow_review_snapshot:
        raise ValueError(
            "Active pack is not admitted or calibrated for final draft-day freeze. "
            "Use Import Review or freeze it explicitly as a review snapshot."
        )
    freeze_name = freeze_id or _freeze_id(validated.data_pack_name)
    freeze_dir = Path(output_root).resolve() / freeze_name
    if freeze_dir.exists():
        raise FileExistsError(
            f"Freeze already exists: {freeze_dir}. Choose a new freeze ID."
        )

    data_pack_backup = freeze_dir / "data_pack_backup"
    boards_dir = freeze_dir / "board_exports"
    model_backup_dir = freeze_dir / "model_output_backup"
    stats_first_backup_dir = freeze_dir / "stats_first_backup"
    boards_dir.mkdir(parents=True)
    shutil.copytree(source_pack, data_pack_backup)
    model_backup_dir.mkdir()
    model_output = source_pack / "model_outputs.csv"
    if model_output.exists():
        shutil.copy2(model_output, model_backup_dir / "model_outputs.csv")
    stats_first_backup = _backup_stats_first_artifacts(
        stats_first_backup_dir,
        stats_first_preview_root,
        stats_first_applied_pack_root,
    )

    export_files = _export_boards(source_pack, boards_dir)
    checklist_path = boards_dir / "decision_readiness_checklist.csv"
    _write_csv(
        checklist_path,
        readiness_status_rows(health, calibration_passed=calibration_passed),
    )
    export_files["decision_readiness_checklist"] = checklist_path
    health_checks_path = boards_dir / "pack_health_checks.csv"
    _write_csv(health_checks_path, health_check_rows(health))
    export_files["pack_health_checks"] = health_checks_path
    coverage_path = boards_dir / "pack_coverage_report.csv"
    _write_csv(coverage_path, coverage_report_rows(health))
    export_files["pack_coverage_report"] = coverage_path
    trust_path = boards_dir / "trust_status.csv"
    _write_csv(trust_path, [trust_status_row(health, calibration_passed=calibration_passed)])
    export_files["trust_status"] = trust_path
    calibration_path = boards_dir / "final_calibration_gate.csv"
    _write_csv(calibration_path, final_calibration_gate_rows(calibration_report))
    export_files["final_calibration_gate"] = calibration_path
    admission_path = boards_dir / "admission_reasons.csv"
    _write_csv(admission_path, admission_reason_rows(admission))
    export_files["admission_reasons"] = admission_path

    metadata = _metadata_rows(
        validated.rows_by_table,
        health,
        source_pack,
        freeze_name,
        admission_summary_row(admission),
        allow_review_snapshot,
        stats_first_backup,
        final_calibration_gate_summary_row(calibration_report),
    )
    certificate_path = boards_dir / "money_decision_certificate.csv"
    _write_csv(certificate_path, [_money_decision_certificate_row(metadata)])
    export_files["money_decision_certificate"] = certificate_path
    metadata_path = freeze_dir / "model_run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    summary_path = freeze_dir / "DRAFT_DAY_README.txt"
    summary_path.write_text(_draft_day_readme(metadata), encoding="utf-8")
    (freeze_dir / "FREEZE_LOCK.txt").write_text(
        "Draft-day freeze. Do not refresh, rebuild, or edit files inside this folder.\n",
        encoding="utf-8",
    )

    return DraftFreezeResult(
        freeze_id=freeze_name,
        freeze_dir=freeze_dir,
        data_pack_backup_dir=data_pack_backup,
        export_files=export_files,
        metadata_path=metadata_path,
        checklist_path=checklist_path,
        summary_path=summary_path,
    )


def _export_boards(source_pack: Path, boards_dir: Path) -> dict[str, Path]:
    war = build_war_board(source_pack)
    team = build_team_command_board(source_pack)
    draft = build_draft_room(source_pack)
    league = build_league_intel(source_pack)
    exports = {
        "war_board": boards_dir / "war_board.csv",
        "team_roster": boards_dir / "team_roster.csv",
        "team_top_five": boards_dir / "team_top_five.csv",
        "team_forced_release": boards_dir / "team_forced_release.csv",
        "draft_assets": boards_dir / "draft_assets.csv",
        "draft_picks": boards_dir / "draft_picks.csv",
        "draft_release_targets": boards_dir / "draft_release_targets.csv",
        "league_pressure": boards_dir / "league_pressure.csv",
        "league_default_releases": boards_dir / "league_default_releases.csv",
    }
    _write_csv(exports["war_board"], war.rows)
    _write_csv(exports["team_roster"], team.roster_rows)
    _write_csv(exports["team_top_five"], team.top_five_rows)
    _write_csv(exports["team_forced_release"], team.forced_release_rows)
    _write_csv(exports["draft_assets"], draft.asset_rows)
    _write_csv(exports["draft_picks"], draft.pick_rows)
    _write_csv(exports["draft_release_targets"], draft.release_target_rows)
    _write_csv(exports["league_pressure"], league.pressure_rows)
    _write_csv(exports["league_default_releases"], league.default_release_rows)
    return exports


def _metadata_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
    health,
    source_pack: Path,
    freeze_id: str,
    admission_summary: dict[str, object],
    allow_review_snapshot: bool,
    stats_first_backup: dict[str, object],
    calibration_summary: dict[str, object],
) -> dict[str, object]:
    model_rows = rows_by_table.get("model_outputs", [])
    model_versions = sorted(
        {str(row.get("model_version")) for row in model_rows if row.get("model_version")}
    )
    computed_at_values = sorted(
        {str(row.get("computed_at")) for row in model_rows if row.get("computed_at")}
    )
    return {
        "freeze_id": freeze_id,
        "frozen_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_data_pack": str(source_pack),
        "snapshot_date": health.snapshot_date,
        "data_pack_name": health.data_pack_name,
        "readiness": health.readiness,
        "error_count": health.error_count,
        "warning_count": health.warning_count,
        "roster_count": health.roster_count,
        "pick_count": health.pick_count,
        "league_rank_coverage_pct": round(health.league_rank_coverage_pct, 1),
        "placeholder_model_output_count": health.placeholder_model_output_count,
        "trust_status": trust_status_row(
            health,
            calibration_passed=bool(calibration_summary["model_calibration_passed"]),
        )["trust_status"],
        "trust_next_action": trust_status_row(
            health,
            calibration_passed=bool(calibration_summary["model_calibration_passed"]),
        )["next_action"],
        "admission_decision": admission_summary["decision"],
        "admission_health": admission_summary["health"],
        "admission_diff_changes": admission_summary["diff_changes"],
        "model_recalibration_active": rankings_are_review_only(
            calibration_passed=bool(calibration_summary["model_calibration_passed"])
        ),
        "model_calibration_passed": calibration_summary["model_calibration_passed"],
        "model_calibration_status": calibration_summary["calibration_status"],
        "model_calibration_badge": calibration_summary["calibration_badge"],
        "final_decision_badge": calibration_summary["final_decision_badge"],
        "model_calibration_blocked": calibration_summary["blocked"],
        "model_calibration_review": calibration_summary["review"],
        "decision_ready": health.readiness == "ready"
        and health.placeholder_model_output_count == 0
        and health.error_count == 0
        and admission_summary["decision"] == "ready"
        and bool(calibration_summary["model_calibration_passed"])
        and not rankings_are_review_only(
            calibration_passed=bool(calibration_summary["model_calibration_passed"])
        ),
        "review_snapshot": allow_review_snapshot,
        "model_versions": model_versions,
        "computed_at_values": computed_at_values,
        "exported_boards": [
            "war_board",
            "team_roster",
            "team_top_five",
            "team_forced_release",
            "draft_assets",
            "draft_picks",
            "draft_release_targets",
            "league_pressure",
            "league_default_releases",
            "decision_readiness_checklist",
            "pack_health_checks",
            "pack_coverage_report",
            "trust_status",
            "admission_reasons",
            "final_calibration_gate",
            "money_decision_certificate",
        ],
        "stats_first_backup": stats_first_backup,
        "no_live_mutation": True,
        "refresh_after_freeze_allowed": False,
    }


def _backup_stats_first_artifacts(
    target_root: Path,
    preview_root: str | Path,
    applied_pack_root: str | Path,
) -> dict[str, object]:
    target_root.mkdir(parents=True, exist_ok=True)
    preview_backup = target_root / "previews"
    applied_backup = target_root / "applied_packs"
    preview_count = _copy_manifest_directories(
        Path(preview_root),
        preview_backup,
        STATS_FIRST_PREVIEW_MANIFEST_FILE,
    )
    applied_count = _copy_manifest_directories(
        Path(applied_pack_root),
        applied_backup,
        STATS_FIRST_APPLIED_PACK_MANIFEST_FILE,
    )
    return {
        "preview_source_root": str(Path(preview_root)),
        "applied_pack_source_root": str(Path(applied_pack_root)),
        "preview_backup_dir": str(preview_backup),
        "applied_pack_backup_dir": str(applied_backup),
        "preview_count": preview_count,
        "applied_pack_count": applied_count,
        "scoring_effect": "backup only; freeze does not apply or mutate stats-first outputs",
    }


def _copy_manifest_directories(source_root: Path, target_root: Path, manifest_file: str) -> int:
    target_root.mkdir(parents=True, exist_ok=True)
    if not source_root.exists():
        return 0
    copied = 0
    for child in sorted(source_root.iterdir()):
        if not child.is_dir() or not (child / manifest_file).exists():
            continue
        shutil.copytree(child, target_root / child.name)
        copied += 1
    return copied


def _draft_day_readme(metadata: dict[str, object]) -> str:
    decision_ready = "yes" if metadata["decision_ready"] else "no"
    artifact_type = (
        "FINAL DECISION BOARD"
        if metadata["decision_ready"] and not metadata["review_snapshot"]
        else "REVIEW SNAPSHOT - NOT A FINAL BOARD"
    )
    use_policy = (
        "This freeze can be used as the draft-day board."
        if metadata["decision_ready"] and not metadata["review_snapshot"]
        else (
            "This freeze is for review/history only. Do not use it as the "
            "draft-day board until a later freeze is decision-ready."
        )
    )
    return "\n".join(
        [
            "LVE Draft-Day Freeze",
            "",
            f"Artifact type: {artifact_type}",
            f"Freeze ID: {metadata['freeze_id']}",
            f"Frozen at: {metadata['frozen_at']}",
            f"Source data pack: {metadata['source_data_pack']}",
            f"Snapshot: {metadata['snapshot_date']}",
            f"Trust status: {metadata['trust_status']}",
            f"Admission decision: {metadata['admission_decision']}",
            f"Model calibration: {metadata['model_calibration_badge']}",
            f"Final decision badge: {metadata['final_decision_badge']}",
            f"Review snapshot: {'yes' if metadata['review_snapshot'] else 'no'}",
            f"Decision ready at freeze: {decision_ready}",
            f"Next action at freeze: {metadata['trust_next_action']}",
            f"Use policy: {use_policy}",
            "",
            "Contents:",
            "- data_pack_backup/: exact selected data pack copy",
            "- model_output_backup/: model_outputs.csv copy when present",
            "- stats_first_backup/: stats-first previews/applied-pack evidence when present",
            "- board_exports/: CSV exports for draft-day review",
            "- board_exports/admission_reasons.csv: why this freeze was ready/review/blocked",
            "- board_exports/money_decision_certificate.csv: one-row final use verdict",
            "- model_run_metadata.json: machine-readable freeze metadata",
            "- FREEZE_LOCK.txt: no-mutation marker",
            "",
            "Policy:",
            "Do not refresh Sleeper, rebuild the pack, or edit files inside this freeze.",
            "Create a new freeze ID if late news forces a new review cycle.",
            "",
        ]
    )


def _money_decision_certificate_row(metadata: dict[str, object]) -> dict[str, object]:
    decision_ready = bool(metadata["decision_ready"]) and not bool(
        metadata["review_snapshot"]
    )
    return {
        "freeze_id": metadata["freeze_id"],
        "money_decision_status": "final_board" if decision_ready else "review_only",
        "can_use_for_money_decisions": decision_ready,
        "artifact_type": (
            "FINAL DECISION BOARD"
            if decision_ready
            else "REVIEW SNAPSHOT - NOT A FINAL BOARD"
        ),
        "trust_status": metadata["trust_status"],
        "admission_decision": metadata["admission_decision"],
        "model_calibration_status": metadata["model_calibration_status"],
        "model_calibration_badge": metadata["model_calibration_badge"],
        "final_decision_badge": metadata["final_decision_badge"],
        "model_calibration_passed": metadata["model_calibration_passed"],
        "review_snapshot": metadata["review_snapshot"],
        "decision_ready": metadata["decision_ready"],
        "next_action": "Use War Board as the primary decision surface."
        if decision_ready
        else "Do not use this freeze as the final board; clear review blockers and freeze again.",
        "source_data_pack": metadata["source_data_pack"],
    }


def _freeze_id(data_pack_name: str) -> str:
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(
        character if character.isalnum() or character in {"_", "-"} else "_"
        for character in data_pack_name.lower()
    )
    return f"{stamp}_{safe_name}"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
