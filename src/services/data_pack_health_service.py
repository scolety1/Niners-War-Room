from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.csv_schemas import REQUIRED_V1_FILES
from src.data.validators import ImportIssue, validate_data_pack
from src.services.model_recalibration_service import rankings_are_review_only


@dataclass(frozen=True)
class HealthCheck:
    check_name: str
    status: str
    severity: str
    value: str
    detail: str


@dataclass(frozen=True)
class CoverageRow:
    coverage_area: str
    status: str
    covered: str
    expected: str
    coverage_pct: float
    decision_blocking: bool
    detail: str
    next_action: str


@dataclass(frozen=True)
class DataPackHealthReport:
    data_pack_path: Path
    data_pack_name: str
    snapshot_date: str | None
    readiness: str
    error_count: int
    warning_count: int
    roster_count: int
    pick_count: int
    league_rank_coverage_pct: float
    placeholder_model_output_count: int
    coverage_rows: tuple[CoverageRow, ...]
    checks: tuple[HealthCheck, ...]
    issues: tuple[ImportIssue, ...]


def build_data_pack_health_report(
    data_pack_path: str | Path,
    *,
    roster_limit: int = 24,
) -> DataPackHealthReport:
    validated = validate_data_pack(data_pack_path, roster_limit=roster_limit)
    roster_rows = validated.rows_by_table.get("rosters", [])
    ranking_rows = validated.rows_by_table.get("official_rankings", [])
    pick_rows = validated.rows_by_table.get("future_picks", [])
    model_rows = validated.rows_by_table.get("model_outputs", [])
    metadata_rows = validated.rows_by_table.get("metadata_sources", [])
    error_count = sum(1 for issue in validated.issues if issue.severity == "error")
    warning_count = sum(1 for issue in validated.issues if issue.severity == "warning")
    rankings_by_player = _rows_by_player(ranking_rows)
    ranked_count = sum(
        1
        for row in roster_rows
        if _league_rank_value(
            row,
            rankings_by_player.get(str(row.get("player_id") or "")),
        )
        is not None
    )
    rank_coverage = _pct(ranked_count, len(roster_rows))
    placeholder_count = _placeholder_model_outputs(model_rows)
    coverage_rows = _coverage_rows(
        data_pack_path=Path(data_pack_path),
        roster_rows=roster_rows,
        ranking_rows=ranking_rows,
        pick_rows=pick_rows,
        model_rows=model_rows,
        metadata_rows=metadata_rows,
        roster_limit=roster_limit,
        ranked_count=ranked_count,
        rank_coverage=rank_coverage,
        placeholder_count=placeholder_count,
    )
    checks = (
        _schema_check(error_count, warning_count),
        _roster_check(roster_rows, roster_limit),
        _rank_coverage_check(ranked_count, len(roster_rows), rank_coverage),
        _pick_check(pick_rows),
        _model_output_check(model_rows, placeholder_count),
        _source_review_check(metadata_rows),
    )
    readiness = _readiness(checks)
    return DataPackHealthReport(
        data_pack_path=Path(data_pack_path).resolve(),
        data_pack_name=validated.data_pack_name,
        snapshot_date=validated.snapshot_date,
        readiness=readiness,
        error_count=error_count,
        warning_count=warning_count,
        roster_count=len(roster_rows),
        pick_count=len(pick_rows),
        league_rank_coverage_pct=rank_coverage,
        placeholder_model_output_count=placeholder_count,
        coverage_rows=coverage_rows,
        checks=checks,
        issues=validated.issues,
    )


def health_check_rows(report: DataPackHealthReport) -> list[dict[str, object]]:
    return [
        {
            "check": check.check_name,
            "status": check.status,
            "severity": check.severity,
            "value": check.value,
            "detail": check.detail,
        }
        for check in report.checks
    ]


def health_issue_rows(report: DataPackHealthReport) -> list[dict[str, object]]:
    return [
        {
            "severity": issue.severity,
            "file": issue.file_name or "",
            "row": issue.row_number or "",
            "entity": issue.entity_name or "",
            "issue": issue.issue,
            "fix": issue.suggested_fix or "",
        }
        for issue in report.issues
    ]


def coverage_report_rows(report: DataPackHealthReport) -> list[dict[str, object]]:
    return [
        {
            "coverage_area": row.coverage_area,
            "status": row.status,
            "covered": row.covered,
            "expected": row.expected,
            "coverage_pct": round(row.coverage_pct, 1),
            "decision_blocking": row.decision_blocking,
            "detail": row.detail,
            "next_action": row.next_action,
        }
        for row in report.coverage_rows
    ]


def health_summary_row(report: DataPackHealthReport) -> dict[str, object]:
    return {
        "data_pack": report.data_pack_name,
        "readiness": report.readiness,
        "snapshot": report.snapshot_date or "",
        "errors": report.error_count,
        "warnings": report.warning_count,
        "rosters": report.roster_count,
        "picks": report.pick_count,
        "league_rank_coverage_pct": round(report.league_rank_coverage_pct, 1),
        "placeholder_model_outputs": report.placeholder_model_output_count,
        "path": str(report.data_pack_path),
    }


def readiness_status_rows(
    report: DataPackHealthReport,
    *,
    calibration_passed: bool = False,
) -> list[dict[str, object]]:
    data_ready = (
        report.error_count == 0
        and report.roster_count > 0
        and report.league_rank_coverage_pct > 0
    )
    model_ready = (
        report.placeholder_model_output_count == 0
        and _check_status(report, "model_outputs") == "ready"
    )
    recalibrating = rankings_are_review_only(calibration_passed=calibration_passed)
    decision_ready = (
        data_ready
        and model_ready
        and report.readiness == "ready"
        and not recalibrating
    )
    return [
        {
            "status_area": "data_ready",
            "status": "ready" if data_ready else "needs_review",
            "what_it_means": "Rosters, picks, and league-rank inputs can be inspected.",
            "next_action": "Use Team and League Intel for rule inventory."
            if data_ready
            else "Fix import errors or merge league ranks before top-five review.",
        },
        {
            "status_area": "model_ready",
            "status": "under_recalibration"
            if model_ready and recalibrating
            else "ready"
            if model_ready
            else "needs_scores",
            "what_it_means": "Keeper, drop, trade, and forced-release strategy scores are real.",
            "next_action": (
                "Scores exist, but rankings are review-only until model audit passes."
                if model_ready and recalibrating
                else "Use War Board, Trade Central, and strategy tables."
                if model_ready
                else "Load real veteran model outputs before trusting recommendations."
            ),
        },
        {
            "status_area": "decision_ready",
            "status": "ready" if decision_ready else "review_only",
            "what_it_means": (
                "The selected pack is ready for draft-pressure decisions."
                if decision_ready
                else (
                    "The selected pack can be inspected, but rankings and actions "
                    "are not final calls yet."
                )
            ),
            "next_action": (
                "Use War Board as the primary decision surface."
                if decision_ready
                else "Treat visible tables as review aids, not final calls."
            ),
        },
    ]


def _schema_check(error_count: int, warning_count: int) -> HealthCheck:
    if error_count:
        return HealthCheck(
            "schema_validation",
            "blocked",
            "error",
            f"{error_count} errors",
            "Required CSV shape or cross-file rules have blocking errors.",
        )
    if warning_count:
        return HealthCheck(
            "schema_validation",
            "review",
            "warning",
            f"{warning_count} warnings",
            "Data pack loads, but warnings need review before money decisions.",
        )
    return HealthCheck("schema_validation", "ready", "info", "clean", "No import issues.")


def _roster_check(rows: list[dict[str, object]], roster_limit: int) -> HealthCheck:
    team_count = len({str(row.get("team_id")) for row in rows if row.get("team_id")})
    expected_rows = team_count * roster_limit
    if not rows:
        return HealthCheck(
            "roster_coverage",
            "blocked",
            "error",
            "0 roster rows",
            "No rosters are available for command-board decisions.",
        )
    if expected_rows and len(rows) != expected_rows:
        return HealthCheck(
            "roster_coverage",
            "review",
            "warning",
            f"{len(rows)} of {expected_rows}",
            "Roster count does not match the configured declaration roster limit.",
        )
    return HealthCheck(
        "roster_coverage",
        "ready",
        "info",
        f"{len(rows)} rows",
        "Roster table is populated for every discovered team.",
    )


def _rank_coverage_check(
    ranked_count: int,
    roster_count: int,
    coverage_pct: float,
) -> HealthCheck:
    if roster_count == 0:
        return HealthCheck(
            "league_rank_coverage",
            "blocked",
            "error",
            "no rosters",
            "Cannot evaluate league-rank coverage without roster rows.",
        )
    if ranked_count == 0:
        return HealthCheck(
            "league_rank_coverage",
            "blocked",
            "error",
            "0.0%",
            (
                "No league ranks are present; Required Top-Five Release Slot "
                "logic is unsafe."
            ),
        )
    if coverage_pct < 95:
        return HealthCheck(
            "league_rank_coverage",
            "review",
            "warning",
            f"{coverage_pct:.1f}%",
            "Some rostered players are missing league ranks.",
        )
    return HealthCheck(
        "league_rank_coverage",
        "ready",
        "info",
        f"{coverage_pct:.1f}%",
        "League-rank coverage is sufficient for summer/declaration review.",
    )


def _pick_check(rows: list[dict[str, object]]) -> HealthCheck:
    if not rows:
        return HealthCheck(
            "future_pick_coverage",
            "review",
            "warning",
            "0 picks",
            "Draft Board will not show pick value paths until future picks exist.",
        )
    current_years = sorted({str(row.get("pick_year")) for row in rows if row.get("pick_year")})
    return HealthCheck(
        "future_pick_coverage",
        "ready",
        "info",
        f"{len(rows)} picks",
        f"Future pick table covers years: {', '.join(current_years)}.",
    )


def _model_output_check(
    rows: list[dict[str, object]],
    placeholder_count: int,
) -> HealthCheck:
    if not rows:
        return HealthCheck(
            "model_outputs",
            "blocked",
            "error",
            "0 outputs",
            "Command boards need model output rows, even if they are placeholders.",
        )
    if placeholder_count:
        return HealthCheck(
            "model_outputs",
            "review",
            "warning",
            f"{placeholder_count} placeholders",
            "Neutral generated scores are present; do not trust keeper/drop calls yet.",
        )
    return HealthCheck(
        "model_outputs",
        "ready",
        "info",
        f"{len(rows)} outputs",
        "Model outputs are populated without Phase 10 neutral placeholders.",
    )


def _source_review_check(rows: list[dict[str, object]]) -> HealthCheck:
    if not rows:
        return HealthCheck(
            "source_review",
            "review",
            "warning",
            "0 sources",
            "No metadata rows explain where this data pack came from.",
        )
    needs_review = [
        row for row in rows if str(row.get("review_status") or "") != "reviewed"
    ]
    if needs_review:
        return HealthCheck(
            "source_review",
            "review",
            "warning",
            f"{len(needs_review)} unreviewed",
            "At least one source row still needs human review.",
        )
    return HealthCheck(
        "source_review",
        "ready",
        "info",
        f"{len(rows)} reviewed",
        "All source rows are marked reviewed.",
    )


def _readiness(checks: tuple[HealthCheck, ...]) -> str:
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    if any(check.status == "review" for check in checks):
        return "review"
    return "ready"


def _coverage_rows(
    *,
    data_pack_path: Path,
    roster_rows: list[dict[str, object]],
    ranking_rows: list[dict[str, object]],
    pick_rows: list[dict[str, object]],
    model_rows: list[dict[str, object]],
    metadata_rows: list[dict[str, object]],
    roster_limit: int,
    ranked_count: int,
    rank_coverage: float,
    placeholder_count: int,
) -> tuple[CoverageRow, ...]:
    team_count = len({str(row.get("team_id")) for row in roster_rows if row.get("team_id")})
    expected_roster_rows = team_count * roster_limit
    expected_model_rows = len(roster_rows)
    reviewed_source_count = sum(
        1 for row in metadata_rows if str(row.get("review_status") or "") == "reviewed"
    )
    required_file_count = len(REQUIRED_V1_FILES)
    present_file_count = sum(
        1 for file_name in REQUIRED_V1_FILES if (data_pack_path / file_name).exists()
    )
    real_model_count = max(0, len(model_rows) - placeholder_count)

    rows = [
        _coverage_row(
            coverage_area="required_files",
            covered=present_file_count,
            expected=required_file_count,
            status="ready" if present_file_count == required_file_count else "blocked",
            decision_blocking=present_file_count != required_file_count,
            detail="All required V1 CSV files are present."
            if present_file_count == required_file_count
            else "One or more required V1 CSV files are missing.",
            next_action="Continue to row and model coverage."
            if present_file_count == required_file_count
            else "Add missing required files before using this pack.",
        ),
        _coverage_row(
            coverage_area="roster_rows",
            covered=len(roster_rows),
            expected=expected_roster_rows or len(roster_rows),
            status=_roster_coverage_status(roster_rows, expected_roster_rows),
            decision_blocking=not roster_rows,
            detail="Roster rows match the configured declaration roster limit."
            if roster_rows and len(roster_rows) == expected_roster_rows
            else "Roster row count needs review against the configured roster limit.",
            next_action="Use Team and League Intel for roster review."
            if roster_rows
            else "Load roster rows before using any board.",
        ),
        _coverage_row(
            coverage_area="league_rank_rows",
            covered=ranked_count,
            expected=len(roster_rows),
            status=_rank_coverage_status(ranked_count, len(roster_rows), rank_coverage),
            decision_blocking=len(roster_rows) == 0 or ranked_count == 0,
            coverage_pct=rank_coverage,
            detail=(
                "League rank is covered for rostered players, using ranking-table fallback "
                "where needed."
            )
            if rank_coverage >= 95
            else "Some rostered players lack league rank coverage.",
            next_action="Top-five forced-release review is available."
            if rank_coverage >= 95
            else (
                "Merge or fill league ranks before trusting Required Top-Five "
                "Release Slot logic."
            ),
        ),
        _coverage_row(
            coverage_area="future_picks",
            covered=len(pick_rows),
            expected="at least 1",
            status="ready" if pick_rows else "review",
            decision_blocking=False,
            coverage_pct=100.0 if pick_rows else 0.0,
            detail="Future pick table is populated."
            if pick_rows
            else "Draft Board can load, but pick paths are incomplete.",
            next_action="Review traded-pick ownership before draft decisions."
            if pick_rows
            else "Import future picks before using pick-value tools.",
        ),
        _coverage_row(
            coverage_area="model_outputs",
            covered=real_model_count,
            expected=expected_model_rows or len(model_rows),
            status=_model_coverage_status(model_rows, placeholder_count, expected_model_rows),
            decision_blocking=not model_rows,
            detail=_model_coverage_detail(model_rows, placeholder_count, expected_model_rows),
            next_action="Model recommendations can be reviewed."
            if model_rows and placeholder_count == 0 and len(model_rows) >= expected_model_rows
            else "Generate real model outputs before trusting keeper/drop recommendations.",
        ),
        _coverage_row(
            coverage_area="source_review",
            covered=reviewed_source_count,
            expected=len(metadata_rows),
            status=_source_coverage_status(reviewed_source_count, len(metadata_rows)),
            decision_blocking=False,
            detail="All source metadata rows are reviewed."
            if metadata_rows and reviewed_source_count == len(metadata_rows)
            else "One or more source metadata rows need review.",
            next_action="Proceed with source provenance already reviewed."
            if metadata_rows and reviewed_source_count == len(metadata_rows)
            else "Review metadata source rows before treating the pack as decision-ready.",
        ),
    ]
    return tuple(rows)


def _coverage_row(
    *,
    coverage_area: str,
    covered: int,
    expected: int | str,
    status: str,
    decision_blocking: bool,
    detail: str,
    next_action: str,
    coverage_pct: float | None = None,
) -> CoverageRow:
    if coverage_pct is None:
        coverage_pct = _pct(covered, expected if isinstance(expected, int) else 0)
    return CoverageRow(
        coverage_area=coverage_area,
        status=status,
        covered=str(covered),
        expected=str(expected),
        coverage_pct=coverage_pct,
        decision_blocking=decision_blocking,
        detail=detail,
        next_action=next_action,
    )


def _roster_coverage_status(
    roster_rows: list[dict[str, object]], expected_roster_rows: int
) -> str:
    if not roster_rows:
        return "blocked"
    if expected_roster_rows and len(roster_rows) != expected_roster_rows:
        return "review"
    return "ready"


def _rank_coverage_status(
    ranked_count: int, roster_count: int, coverage_pct: float
) -> str:
    if roster_count == 0 or ranked_count == 0:
        return "blocked"
    if coverage_pct < 95:
        return "review"
    return "ready"


def _model_coverage_status(
    model_rows: list[dict[str, object]],
    placeholder_count: int,
    expected_model_rows: int,
) -> str:
    if not model_rows:
        return "blocked"
    if placeholder_count or (expected_model_rows and len(model_rows) < expected_model_rows):
        return "review"
    return "ready"


def _model_coverage_detail(
    model_rows: list[dict[str, object]],
    placeholder_count: int,
    expected_model_rows: int,
) -> str:
    if not model_rows:
        return "No model output rows are available."
    if placeholder_count:
        return f"{placeholder_count} neutral placeholder model output rows remain."
    if expected_model_rows and len(model_rows) < expected_model_rows:
        return "Model outputs do not cover every rostered player."
    return "Model outputs cover rostered players without neutral placeholders."


def _source_coverage_status(reviewed_source_count: int, source_count: int) -> str:
    if source_count == 0:
        return "review"
    if reviewed_source_count != source_count:
        return "review"
    return "ready"


def _placeholder_model_outputs(rows: list[dict[str, object]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("risk_level") == "needs_model"
        or "Neutral placeholder" in str(row.get("notes") or "")
    )


def _rows_by_player(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        str(row.get("player_id")): row
        for row in rows
        if row.get("player_id") is not None
    }


def _league_rank_value(
    row: dict[str, object],
    fallback_row: dict[str, object] | None = None,
) -> object:
    for key in ("league_rank", "official_rank"):
        value = row.get(key)
        if value is not None and value != "":
            return value
        if fallback_row is not None:
            fallback_value = fallback_row.get(key)
            if fallback_value is not None and fallback_value != "":
                return fallback_value
    return None


def _pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100


def _check_status(report: DataPackHealthReport, check_name: str) -> str:
    for check in report.checks:
        if check.check_name == check_name:
            return check.status
    return "blocked"
