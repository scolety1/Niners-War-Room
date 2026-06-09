from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REQUIRED_COLUMNS: tuple[str, ...] = (
    "player",
    "position",
    "nfl_team",
    "releasing_team_or_roster_owner",
    "release_status",
    "source_date",
    "source_file",
    "notes",
    "manual_review_required",
    "protected_status",
    "legal_draftable",
    "allowed_use",
    "blocked_use",
)

VALID_POSITIONS = {"QB", "RB", "WR", "TE", "K"}
VALID_BOOLEAN_VALUES = {"true", "false", "yes", "no", "1", "0"}
DEFAULT_REPORT_PATH = Path(
    "local_exports/model_v4/draft_prep/latest/"
    "dropped_released_players_validation_report.csv"
)


@dataclass(frozen=True)
class DroppedReleasedValidationResult:
    source_path: Path
    report_path: Path
    row_count: int
    issue_count: int
    valid: bool


def validate_dropped_released_players_source(
    csv_path: str | Path,
    *,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> DroppedReleasedValidationResult:
    source = Path(csv_path)
    report = Path(report_path)
    issues: list[dict[str, object]] = []

    if not source.exists():
        issues.append(_issue(0, "", "missing_file", f"Source file not found: {source}"))
        _write_report(report, issues)
        return DroppedReleasedValidationResult(source, report, 0, len(issues), False)

    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        for column in missing_columns:
            issues.append(
                _issue(
                    0,
                    "",
                    "missing_required_column",
                    f"Missing required column: {column}",
                )
            )
        row_count = 0
        for row_number, row in enumerate(reader, start=2):
            row_count += 1
            player = _clean(row.get("player"))
            position = _clean(row.get("position")).upper()
            source_date = _clean(row.get("source_date"))
            legal_draftable = _clean(row.get("legal_draftable")).lower()
            manual_review = _clean(row.get("manual_review_required")).lower()

            if not player:
                issues.append(_issue(row_number, player, "missing_player", "Player is required."))
            if not position:
                issues.append(
                    _issue(row_number, player, "missing_position", "Position is required.")
                )
            elif position not in VALID_POSITIONS:
                issues.append(
                    _issue(
                        row_number,
                        player,
                        "invalid_position",
                        f"Position must be one of {sorted(VALID_POSITIONS)}.",
                    )
                )
            if not source_date:
                issues.append(
                    _issue(row_number, player, "missing_source_date", "Source date is required.")
                )
            if legal_draftable not in VALID_BOOLEAN_VALUES:
                issues.append(
                    _issue(
                        row_number,
                        player,
                        "invalid_legal_draftable",
                        "legal_draftable must be true/false.",
                    )
                )
            if manual_review and manual_review not in VALID_BOOLEAN_VALUES:
                issues.append(
                    _issue(
                        row_number,
                        player,
                        "invalid_manual_review_required",
                        "manual_review_required must be true/false when supplied.",
                    )
                )
            blocked_use = _clean(row.get("blocked_use")).lower()
            missing_blocked_use = (
                "nwr dynasty score" not in blocked_use
                or "final draft recommendations" not in blocked_use
            )
            if missing_blocked_use:
                issues.append(
                    _issue(
                        row_number,
                        player,
                        "blocked_use_guardrail_missing",
                        "blocked_use must forbid private value and final recommendations.",
                    )
                )

    _write_report(report, issues)
    return DroppedReleasedValidationResult(
        source_path=source,
        report_path=report,
        row_count=row_count,
        issue_count=len(issues),
        valid=not issues,
    )


def _clean(value: object) -> str:
    return str(value or "").strip()


def _issue(row_number: int, player: str, issue_type: str, message: str) -> dict[str, object]:
    return {
        "row_number": row_number,
        "player": player,
        "issue_type": issue_type,
        "severity": "error",
        "message": message,
        "mutates_active_data_pack": "false",
    }


def _write_report(path: Path, issues: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "row_number",
        "player",
        "issue_type",
        "severity",
        "message",
        "mutates_active_data_pack",
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(issues)
