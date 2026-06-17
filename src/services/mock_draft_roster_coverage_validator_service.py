from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.services.mock_draft_input_schema_validator_service import SCHEMA_COLUMNS

ROSTER_REQUIRED_COLUMNS = SCHEMA_COLUMNS["post_drop_rosters"]
TEAM_MANAGER_REQUIRED_COLUMNS = SCHEMA_COLUMNS["team_managers"]


@dataclass(frozen=True)
class RosterCoverageIssue:
    issue_type: str
    status: str
    count: int
    review_flag: str
    message: str


@dataclass(frozen=True)
class TeamRosterSummary:
    team_name: str
    manager: str
    player_rows: int
    position_counts: dict[str, int]


@dataclass(frozen=True)
class RosterCoverageResult:
    review_only: bool
    expected_team_count: int
    full_simulation_ready: bool
    team_summaries: tuple[TeamRosterSummary, ...]
    issues: tuple[RosterCoverageIssue, ...]
    summary: dict[str, object]


def validate_roster_coverage(
    roster_path: str | Path,
    *,
    team_managers_path: str | Path | None = None,
    expected_team_count: int = 10,
) -> RosterCoverageResult:
    roster_file = Path(roster_path)
    manager_file = Path(team_managers_path) if team_managers_path else None
    issues: list[RosterCoverageIssue] = []

    if not roster_file.exists():
        issues.append(
            RosterCoverageIssue(
                issue_type="missing_roster_file",
                status="RED",
                count=1,
                review_flag="post_drop_rosters_missing",
                message="Required post-drop roster file is missing.",
            )
        )
        return _build_result(expected_team_count, (), issues)

    roster_rows = _read_csv(roster_file)
    roster_columns = set(roster_rows[0]) if roster_rows else set()
    missing_roster_columns = tuple(sorted(ROSTER_REQUIRED_COLUMNS - roster_columns))
    if missing_roster_columns:
        issues.append(
            RosterCoverageIssue(
                issue_type="missing_roster_columns",
                status="RED",
                count=len(missing_roster_columns),
                review_flag="post_drop_rosters_schema_review_required",
                message="Post-drop roster file is missing required columns.",
            )
        )

    manager_rows: list[dict[str, str]] = []
    if manager_file and manager_file.exists():
        manager_rows = _read_csv(manager_file)
        manager_columns = set(manager_rows[0]) if manager_rows else set()
        missing_manager_columns = tuple(
            sorted(TEAM_MANAGER_REQUIRED_COLUMNS - manager_columns)
        )
        if missing_manager_columns:
            issues.append(
                RosterCoverageIssue(
                    issue_type="missing_team_manager_columns",
                    status="RED",
                    count=len(missing_manager_columns),
                    review_flag="team_manager_schema_review_required",
                    message="Team/manager file is missing required columns.",
                )
            )

    roster_team_names = {
        row.get("team_name", "").strip()
        for row in roster_rows
        if row.get("team_name", "").strip()
    }
    manager_team_names = {
        row.get("team_name", "").strip()
        for row in manager_rows
        if row.get("team_name", "").strip()
    }
    expected_team_names = manager_team_names or roster_team_names

    if len(expected_team_names) != expected_team_count:
        issues.append(
            RosterCoverageIssue(
                issue_type="team_count",
                status="YELLOW",
                count=len(expected_team_names),
                review_flag="ten_team_roster_coverage_review_required",
                message="Roster coverage does not yet prove exactly 10 teams.",
            )
        )

    teams_missing_rosters = sorted(expected_team_names - roster_team_names)
    if teams_missing_rosters:
        issues.append(
            RosterCoverageIssue(
                issue_type="teams_missing_rosters",
                status="YELLOW",
                count=len(teams_missing_rosters),
                review_flag="team_roster_rows_missing_review_required",
                message="One or more teams have manager rows but no roster rows.",
            )
        )

    missing_player_identity = sum(
        1
        for row in roster_rows
        if not row.get("player_name", "").strip() or not row.get("position", "").strip()
    )
    if missing_player_identity:
        issues.append(
            RosterCoverageIssue(
                issue_type="missing_player_identity",
                status="YELLOW",
                count=missing_player_identity,
                review_flag="player_identity_review_required",
                message="Roster rows with missing player name or position need review.",
            )
        )

    duplicate_players = _duplicate_player_count(roster_rows)
    if duplicate_players:
        issues.append(
            RosterCoverageIssue(
                issue_type="duplicate_player_rows",
                status="YELLOW",
                count=duplicate_players,
                review_flag="duplicate_player_review_required",
                message="Duplicate player rows are preserved and require review.",
            )
        )

    missing_manager = sum(1 for row in roster_rows if not row.get("manager", "").strip())
    if missing_manager:
        issues.append(
            RosterCoverageIssue(
                issue_type="missing_manager",
                status="YELLOW",
                count=missing_manager,
                review_flag="team_manager_review_required",
                message="Roster rows with blank manager need review.",
            )
        )

    missing_lineage = sum(
        1 for row in roster_rows if not row.get("input_status", "").strip()
    )
    if missing_lineage:
        issues.append(
            RosterCoverageIssue(
                issue_type="missing_lineage",
                status="YELLOW",
                count=missing_lineage,
                review_flag="input_lineage_review_required",
                message="Roster rows with blank input_status need source review.",
            )
        )

    summaries = _team_summaries(roster_rows)
    return _build_result(expected_team_count, summaries, issues, len(roster_rows))


def roster_coverage_issues_as_dicts(
    result: RosterCoverageResult,
) -> list[dict[str, object]]:
    return [
        {
            "issue_type": issue.issue_type,
            "status": issue.status,
            "count": issue.count,
            "review_flag": issue.review_flag,
            "message": issue.message,
        }
        for issue in result.issues
    ]


def roster_team_summaries_as_dicts(
    result: RosterCoverageResult,
) -> list[dict[str, object]]:
    return [
        {
            "team_name": summary.team_name,
            "manager": summary.manager,
            "player_rows": summary.player_rows,
            "position_counts": "|".join(
                f"{position}:{count}"
                for position, count in sorted(summary.position_counts.items())
            ),
        }
        for summary in result.team_summaries
    ]


def _build_result(
    expected_team_count: int,
    summaries: tuple[TeamRosterSummary, ...],
    issues: list[RosterCoverageIssue],
    roster_row_count: int = 0,
) -> RosterCoverageResult:
    full_ready = bool(summaries) and len(summaries) == expected_team_count and all(
        issue.status == "GREEN" for issue in issues
    )
    return RosterCoverageResult(
        review_only=True,
        expected_team_count=expected_team_count,
        full_simulation_ready=full_ready,
        team_summaries=summaries,
        issues=tuple(issues),
        summary={
            "review_only": True,
            "roster_rows": roster_row_count,
            "team_count": len(summaries),
            "expected_team_count": expected_team_count,
            "full_simulation_ready": full_ready,
            "green_issues": sum(1 for issue in issues if issue.status == "GREEN"),
            "yellow_issues": sum(1 for issue in issues if issue.status == "YELLOW"),
            "red_issues": sum(1 for issue in issues if issue.status == "RED"),
            "market_policy": "Roster coverage does not read or apply ADP/market.",
            "nwr_score_policy": "Roster coverage does not invent numeric NWR scores.",
        },
    )


def _team_summaries(rows: list[dict[str, str]]) -> tuple[TeamRosterSummary, ...]:
    by_team: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        team_name = row.get("team_name", "").strip()
        if not team_name:
            continue
        by_team.setdefault(team_name, []).append(row)

    summaries: list[TeamRosterSummary] = []
    for team_name, team_rows in sorted(by_team.items()):
        manager = next(
            (row.get("manager", "").strip() for row in team_rows if row.get("manager")),
            "",
        )
        position_counts = Counter(
            row.get("position", "").strip() or "UNKNOWN" for row in team_rows
        )
        summaries.append(
            TeamRosterSummary(
                team_name=team_name,
                manager=manager,
                player_rows=len(team_rows),
                position_counts=dict(position_counts),
            )
        )
    return tuple(summaries)


def _duplicate_player_count(rows: list[dict[str, str]]) -> int:
    identities = [
        (
            row.get("player_name", "").strip().casefold(),
            row.get("position", "").strip().casefold(),
        )
        for row in rows
        if row.get("player_name", "").strip()
    ]
    return sum(count - 1 for count in Counter(identities).values() if count > 1)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
