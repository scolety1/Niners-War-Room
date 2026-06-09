from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.models.rookie_scores import FEATURES_BY_POSITION, ModelMode, Position

PROSPECT_FILE = "rookie_prospect_inputs.csv"
REGISTRY_FILE = "rookie_feature_registry.csv"
BENCHMARK_FILE = "veteran_opportunity_benchmarks.csv"
PLAYER_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
SOURCE_CONFIDENCE_VALUES = {"verified", "derived", "manual", "estimated", "unknown"}


@dataclass(frozen=True)
class RookieIntakeIssue:
    severity: str
    player_id: str
    player_name: str
    field_name: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class RookieIntakeRow:
    player_id: str
    player_name: str
    position: str
    model_mode: str
    readiness: str
    model_output_allowed: bool
    missing_core_features: int
    missing_feature_sources: int
    invalid_feature_values: int
    source_snapshot_id: str
    source_name: str
    source_date: str


@dataclass(frozen=True)
class RookieIntakeReport:
    data_dir: Path
    rows: tuple[RookieIntakeRow, ...]
    issues: tuple[RookieIntakeIssue, ...]
    required_files: tuple[str, ...]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    @property
    def ready_count(self) -> int:
        return sum(1 for row in self.rows if row.readiness == "ready")

    @property
    def blocked_count(self) -> int:
        return sum(1 for row in self.rows if row.readiness == "blocked")


def build_rookie_intake_report(data_dir: str | Path) -> RookieIntakeReport:
    root = Path(data_dir)
    required_files = (PROSPECT_FILE, REGISTRY_FILE, BENCHMARK_FILE)
    file_issues = _validate_required_files(root, required_files)
    if file_issues:
        return RookieIntakeReport(root, (), tuple(file_issues), required_files)

    prospect_rows = _read_csv(root / PROSPECT_FILE)
    player_id_counts = Counter(row.get("player_id", "") for row in prospect_rows)
    intake_rows: list[RookieIntakeRow] = []
    issues: list[RookieIntakeIssue] = []
    for row in prospect_rows:
        player_issues = _validate_row(row, player_id_counts)
        issues.extend(player_issues)
        intake_rows.append(_intake_row(row, player_issues))

    return RookieIntakeReport(
        data_dir=root,
        rows=tuple(intake_rows),
        issues=tuple(issues),
        required_files=required_files,
    )


def _validate_required_files(
    root: Path,
    required_files: tuple[str, ...],
) -> list[RookieIntakeIssue]:
    issues: list[RookieIntakeIssue] = []
    for file_name in required_files:
        if not (root / file_name).exists():
            issues.append(
                RookieIntakeIssue(
                    severity="error",
                    player_id="",
                    player_name="",
                    field_name=file_name,
                    issue="Required rookie source file is missing.",
                    suggested_fix=f"Add {file_name} to the rookie data directory.",
                )
            )
    return issues


def _validate_row(
    row: dict[str, str],
    player_id_counts: Counter[str],
) -> list[RookieIntakeIssue]:
    issues: list[RookieIntakeIssue] = []
    player_id = row.get("player_id", "")
    position_text = row.get("position", "")
    mode_text = row.get("model_mode", "")

    for column in (
        "player_id",
        "player_name",
        "position",
        "class_year",
        "model_mode",
        "source_snapshot_id",
        "source_name",
        "source_date",
        "data_completeness_status",
    ):
        if not row.get(column):
            issues.append(
                _issue(
                    row,
                    "error",
                    column,
                    "Missing required value.",
                    f"Populate {column}.",
                )
            )

    if player_id and not PLAYER_ID_PATTERN.match(player_id):
        issues.append(
            _issue(
                row,
                "error",
                "player_id",
                "player_id must be a stable lowercase slug.",
                "Use only lowercase letters, numbers, and underscores.",
            )
        )
    if player_id and player_id_counts[player_id] > 1:
        issues.append(
            _issue(
                row,
                "error",
                "player_id",
                "Duplicate player_id.",
                "Keep one source row per rookie player_id.",
            )
        )

    try:
        position = Position(position_text)
    except ValueError:
        issues.append(
            _issue(
                row,
                "error",
                "position",
                "Unsupported rookie position.",
                "Use QB, RB, WR, or TE.",
            )
        )
        return issues

    try:
        ModelMode(mode_text)
    except ValueError:
        issues.append(
            _issue(
                row,
                "error",
                "model_mode",
                "Unsupported model mode.",
                "Use pre_draft or post_draft.",
            )
        )

    if not _is_int(row.get("class_year", "")):
        issues.append(
            _issue(
                row,
                "error",
                "class_year",
                "class_year must be an integer.",
                "Use a four-digit year.",
            )
        )

    for feature_name in FEATURES_BY_POSITION[position]:
        value = row.get(feature_name, "")
        if value == "":
            issues.append(
                _issue(
                    row,
                    "warning",
                    feature_name,
                    "Missing core rookie feature.",
                    "Enter a normalized 0-100 score or accept lower confidence.",
                )
            )
            continue
        if not _is_score(value):
            issues.append(
                _issue(
                    row,
                    "error",
                    feature_name,
                    "Normalized feature score must be 0-100.",
                    "Replace this value with a number between 0 and 100.",
                )
            )
        if not _feature_has_source(row, feature_name):
            issues.append(
                _issue(
                    row,
                    "warning",
                    f"{feature_name}_source_key",
                    "Feature score is missing provenance.",
                    "Add a feature-specific source key or row-level source metadata.",
                )
            )
        confidence = row.get(f"{feature_name}_source_confidence", "")
        if confidence and confidence not in SOURCE_CONFIDENCE_VALUES:
            issues.append(
                _issue(
                    row,
                    "error",
                    f"{feature_name}_source_confidence",
                    "Unsupported source confidence.",
                    "Use verified, derived, manual, estimated, or unknown.",
                )
            )

    if row.get("model_mode") == "post_draft" and row.get("rookie_opportunity_score") == "":
        issues.append(
            _issue(
                row,
                "warning",
                "rookie_opportunity_score",
                "Post-draft row is missing rookie opportunity score.",
                "Enter a 0-100 post-draft opportunity score or switch to pre_draft.",
            )
        )
    if row.get("rookie_opportunity_score") and not _is_score(row["rookie_opportunity_score"]):
        issues.append(
            _issue(
                row,
                "error",
                "rookie_opportunity_score",
                "rookie_opportunity_score must be 0-100.",
                "Replace this value with a number between 0 and 100.",
            )
        )

    return issues


def _intake_row(
    row: dict[str, str],
    issues: list[RookieIntakeIssue],
) -> RookieIntakeRow:
    missing_core = sum(
        1 for issue in issues if issue.issue == "Missing core rookie feature."
    )
    source_missing = sum(
        1 for issue in issues if issue.issue == "Feature score is missing provenance."
    )
    invalid_values = sum(
        1 for issue in issues if issue.issue == "Normalized feature score must be 0-100."
    )
    has_error = any(issue.severity == "error" for issue in issues)
    if has_error or missing_core >= 3:
        readiness = "blocked"
    elif missing_core:
        readiness = "scored_with_confidence_penalty"
    else:
        readiness = "ready"
    return RookieIntakeRow(
        player_id=row.get("player_id", ""),
        player_name=row.get("player_name", ""),
        position=row.get("position", ""),
        model_mode=row.get("model_mode", ""),
        readiness=readiness,
        model_output_allowed=not has_error and missing_core < 3,
        missing_core_features=missing_core,
        missing_feature_sources=source_missing,
        invalid_feature_values=invalid_values,
        source_snapshot_id=row.get("source_snapshot_id", ""),
        source_name=row.get("source_name", ""),
        source_date=row.get("source_date", ""),
    )


def _issue(
    row: dict[str, str],
    severity: str,
    field_name: str,
    issue: str,
    suggested_fix: str,
) -> RookieIntakeIssue:
    return RookieIntakeIssue(
        severity=severity,
        player_id=row.get("player_id", ""),
        player_name=row.get("player_name", ""),
        field_name=field_name,
        issue=issue,
        suggested_fix=suggested_fix,
    )


def _feature_has_source(row: dict[str, str], feature_name: str) -> bool:
    return bool(
        row.get(f"{feature_name}_source_key")
        or (row.get("source_snapshot_id") and row.get("source_name") and row.get("source_date"))
    )


def _is_int(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def _is_score(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return 0 <= number <= 100


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
