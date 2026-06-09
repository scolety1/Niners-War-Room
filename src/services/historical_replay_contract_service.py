from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_HISTORICAL_REPLAY_TEMPLATE_ROOT = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "real_data_inputs"
    / "historical_replay"
)

HISTORICAL_REPLAY_TEMPLATE_HEADERS: dict[str, tuple[str, ...]] = {
    "platform_draft_exports.csv": (
        "season",
        "overall_pick",
        "round",
        "slot",
        "team",
        "player",
        "position",
        "source",
        "source_snapshot_id",
        "imported_at",
        "notes",
    ),
    "offline_rookie_notes.csv": (
        "season",
        "rookie_pick_number",
        "team",
        "player",
        "position",
        "source",
        "confidence",
        "provenance_note",
        "needs_traded_pick_review",
        "source_snapshot_id",
        "transcribed_by",
        "transcribed_at",
        "notes",
    ),
    "model_replay_inputs.csv": (
        "season",
        "player",
        "position",
        "model_rank",
        "model_score",
        "model_recommendation",
        "model_version",
        "as_of_date",
        "input_source_snapshot_id",
        "confidence",
        "notes",
    ),
    "historical_outcomes.csv": (
        "season",
        "player",
        "position",
        "outcome_label",
        "outcome_score",
        "outcome_window",
        "outcome_source_snapshot_id",
        "evaluated_at",
        "notes",
    ),
    "replay_source_catalog.csv": (
        "source_snapshot_id",
        "source_name",
        "source_type",
        "season",
        "as_of_date",
        "captured_at",
        "local_path",
        "source_url",
        "hindsight_allowed",
        "review_status",
        "notes",
    ),
    "replay_audit_notes.csv": (
        "note_id",
        "season",
        "player",
        "note_scope",
        "note_type",
        "note_text",
        "source_snapshot_id",
        "affects_replay",
        "created_at",
    ),
}

AS_OF_FILES = {"platform_draft_exports.csv", "offline_rookie_notes.csv", "model_replay_inputs.csv"}
OUTCOME_FILES = {"historical_outcomes.csv"}
REVIEW_STATUS_VALUES = {"reviewed", "needs_review", "blocked"}
BOOL_VALUES = {"true", "false", "1", "0", "yes", "no", "y", "n"}
POSITIONS = {"QB", "RB", "WR", "TE"}


@dataclass(frozen=True)
class HistoricalReplayContractIssue:
    file_name: str
    severity: str
    issue: str
    row_number: int | None = None
    suggested_fix: str = ""


@dataclass(frozen=True)
class HistoricalReplayCoverageRow:
    file_name: str
    contract_role: str
    status: str
    row_count: int
    required_columns: int
    missing_columns: str
    next_action: str


@dataclass(frozen=True)
class HistoricalReplayContractReport:
    root: Path
    status: str
    error_count: int
    warning_count: int
    coverage_rows: tuple[HistoricalReplayCoverageRow, ...]
    issues: tuple[HistoricalReplayContractIssue, ...]


def expected_historical_replay_headers() -> dict[str, tuple[str, ...]]:
    return HISTORICAL_REPLAY_TEMPLATE_HEADERS


def build_historical_replay_contract_report(
    root: str | Path = DEFAULT_HISTORICAL_REPLAY_TEMPLATE_ROOT,
) -> HistoricalReplayContractReport:
    root_path = Path(root)
    issues: list[HistoricalReplayContractIssue] = []
    coverage_rows: list[HistoricalReplayCoverageRow] = []

    for file_name, required_columns in HISTORICAL_REPLAY_TEMPLATE_HEADERS.items():
        csv_path = root_path / file_name
        if not csv_path.exists():
            issues.append(
                HistoricalReplayContractIssue(
                    file_name=file_name,
                    severity="error",
                    issue="Historical replay contract file is missing.",
                    suggested_fix=f"Add {file_name}.",
                )
            )
            coverage_rows.append(
                _coverage_row(
                    file_name=file_name,
                    contract_role=_contract_role(file_name),
                    status="blocked",
                    row_count=0,
                    required_columns=len(required_columns),
                    missing_columns="all",
                    next_action=f"Create {file_name} from the committed template.",
                )
            )
            continue

        header, rows = _read_csv(csv_path)
        missing_columns = tuple(column for column in required_columns if column not in header)
        if missing_columns:
            issues.append(
                HistoricalReplayContractIssue(
                    file_name=file_name,
                    severity="error",
                    issue="Missing required columns: " + ", ".join(missing_columns) + ".",
                    suggested_fix="Use the historical replay template header.",
                )
            )
        issues.extend(_validate_rows(file_name, rows))
        coverage_rows.append(
            _coverage_row(
                file_name=file_name,
                contract_role=_contract_role(file_name),
                status="blocked" if missing_columns else "ready",
                row_count=len(rows),
                required_columns=len(required_columns),
                missing_columns="|".join(missing_columns),
                next_action=_next_action(file_name, len(rows), bool(missing_columns)),
            )
        )

    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    return HistoricalReplayContractReport(
        root=root_path.resolve(),
        status="blocked" if error_count else "review" if warning_count else "ready",
        error_count=error_count,
        warning_count=warning_count,
        coverage_rows=tuple(coverage_rows),
        issues=tuple(issues),
    )


def historical_replay_coverage_rows(
    report: HistoricalReplayContractReport,
) -> list[dict[str, object]]:
    return [
        {
            "file_name": row.file_name,
            "contract_role": row.contract_role,
            "status": row.status,
            "row_count": row.row_count,
            "required_columns": row.required_columns,
            "missing_columns": row.missing_columns,
            "next_action": row.next_action,
        }
        for row in report.coverage_rows
    ]


def historical_replay_issue_rows(
    report: HistoricalReplayContractReport,
) -> list[dict[str, object]]:
    return [
        {
            "file_name": issue.file_name,
            "severity": issue.severity,
            "row": issue.row_number or "",
            "issue": issue.issue,
            "fix": issue.suggested_fix,
        }
        for issue in report.issues
    ]


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [{key: value for key, value in row.items()} for row in reader]
        return tuple(reader.fieldnames or ()), rows


def _validate_rows(
    file_name: str, rows: list[dict[str, str]]
) -> tuple[HistoricalReplayContractIssue, ...]:
    issues: list[HistoricalReplayContractIssue] = []
    seen_keys: set[tuple[str, ...]] = set()
    for row_number, row in enumerate(rows, start=2):
        issues.extend(_validate_common_row(file_name, row, row_number))
        key = _unique_key(file_name, row)
        if key and key in seen_keys:
            issues.append(
                HistoricalReplayContractIssue(
                    file_name=file_name,
                    severity="error",
                    row_number=row_number,
                    issue="Duplicate historical replay row.",
                    suggested_fix="Keep one row for this season/player or season/pick key.",
                )
            )
        if key:
            seen_keys.add(key)
    return tuple(issues)


def _validate_common_row(
    file_name: str, row: dict[str, str], row_number: int
) -> list[HistoricalReplayContractIssue]:
    issues: list[HistoricalReplayContractIssue] = []
    season = _value(row, "season")
    if season and not _is_int(season):
        issues.append(_row_issue(file_name, row_number, "season must be an integer."))
    position = _value(row, "position")
    if position and position not in POSITIONS:
        issues.append(
            _row_issue(file_name, row_number, "position must be QB, RB, WR, or TE.")
        )
    for column in ("model_rank", "model_score", "outcome_score"):
        value = _value(row, column)
        if value and not _is_float(value):
            issues.append(_row_issue(file_name, row_number, f"{column} must be numeric."))
    for column in ("overall_pick", "round", "slot", "rookie_pick_number"):
        value = _value(row, column)
        if value and not _is_int(value):
            issues.append(_row_issue(file_name, row_number, f"{column} must be an integer."))
    for column in ("needs_traded_pick_review", "hindsight_allowed", "affects_replay"):
        value = _value(row, column)
        if value and value.lower() not in BOOL_VALUES:
            issues.append(
                _row_issue(file_name, row_number, f"{column} must be a boolean value.")
            )
    review_status = _value(row, "review_status")
    if review_status and review_status not in REVIEW_STATUS_VALUES:
        issues.append(
            _row_issue(
                file_name,
                row_number,
                "review_status must be reviewed, needs_review, or blocked.",
            )
        )
    if file_name in AS_OF_FILES and _value(row, "outcome_score"):
        issues.append(
            HistoricalReplayContractIssue(
                file_name=file_name,
                severity="error",
                row_number=row_number,
                issue="As-of replay files cannot contain outcome_score.",
                suggested_fix="Move hindsight outcome data to historical_outcomes.csv.",
            )
        )
    return issues


def _coverage_row(
    *,
    file_name: str,
    contract_role: str,
    status: str,
    row_count: int,
    required_columns: int,
    missing_columns: str,
    next_action: str,
) -> HistoricalReplayCoverageRow:
    return HistoricalReplayCoverageRow(
        file_name=file_name,
        contract_role=contract_role,
        status=status,
        row_count=row_count,
        required_columns=required_columns,
        missing_columns=missing_columns,
        next_action=next_action,
    )


def _contract_role(file_name: str) -> str:
    if file_name in AS_OF_FILES:
        return "as_of_input"
    if file_name in OUTCOME_FILES:
        return "hindsight_outcome"
    return "provenance"


def _next_action(file_name: str, row_count: int, has_missing_columns: bool) -> str:
    if has_missing_columns:
        return "Fix the header before loading this file."
    if row_count == 0:
        return "Fill this template when historical replay data is available."
    if file_name in AS_OF_FILES:
        return "Confirm rows use only data available at that historical draft date."
    if file_name in OUTCOME_FILES:
        return "Confirm outcomes are evaluation labels, not model inputs."
    return "Review provenance before trusting the replay package."


def _unique_key(file_name: str, row: dict[str, str]) -> tuple[str, ...] | None:
    season = _value(row, "season")
    if file_name == "offline_rookie_notes.csv":
        pick = _value(row, "rookie_pick_number")
        return (season, pick) if season and pick else None
    if file_name == "platform_draft_exports.csv":
        overall = _value(row, "overall_pick")
        return (season, overall) if season and overall else None
    player = _value(row, "player")
    if season and player:
        return (season, _match_key(player))
    source_snapshot_id = _value(row, "source_snapshot_id")
    if source_snapshot_id:
        return (source_snapshot_id,)
    note_id = _value(row, "note_id")
    if note_id:
        return (note_id,)
    return None


def _row_issue(
    file_name: str, row_number: int, issue: str
) -> HistoricalReplayContractIssue:
    return HistoricalReplayContractIssue(
        file_name=file_name,
        severity="error",
        row_number=row_number,
        issue=issue,
        suggested_fix="Correct the row value or leave it blank if optional.",
    )


def _value(row: dict[str, str], column: str) -> str:
    return (row.get(column) or "").strip()


def _match_key(player: str) -> str:
    return "".join(character.lower() for character in player if character.isalnum())


def _is_int(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True
