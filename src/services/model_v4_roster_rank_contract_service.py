from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

OFFICIAL_NINERS_ROSTER_RANK_PATH = Path(
    "docs/model_v4/official_inputs/NINERS_ROSTER_RANKS_20260331.csv"
)
EXPECTED_HEADER = (
    "roster_team",
    "roster_rank",
    "player_name",
    "position",
    "nfl_team",
    "league_rank",
    "source_title",
    "source_date",
    "ranking_source",
)
EXPECTED_NINERS_ROSTER_COUNT = 24
EXPECTED_NINERS_TOP_FIVE = (
    "De'Von Achane",
    "Lamar Jackson",
    "Chase Brown",
    "Luther Burden",
    "Brian Thomas",
)
LEAGUE_RANK_USAGE_POLICY = "rule_context_only"


@dataclass(frozen=True)
class OfficialRosterRankRow:
    roster_team: str
    roster_rank: int
    player_name: str
    position: str
    nfl_team: str
    league_rank: int
    source_title: str
    source_date: str
    ranking_source: str


@dataclass(frozen=True)
class OfficialRosterRankIssue:
    severity: str
    row_number: int | None
    field: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class OfficialRosterRankContractReport:
    status: str
    roster_team: str
    row_count: int
    top_five_names: tuple[str, ...]
    rows: tuple[OfficialRosterRankRow, ...]
    issues: tuple[OfficialRosterRankIssue, ...]
    league_rank_usage_policy: str = LEAGUE_RANK_USAGE_POLICY
    league_rank_allowed_in_dynasty_asset_value: bool = False


def validate_official_roster_rank_contract(
    path: str | Path = OFFICIAL_NINERS_ROSTER_RANK_PATH,
    *,
    roster_team: str = "Niners",
    expected_roster_count: int = EXPECTED_NINERS_ROSTER_COUNT,
    expected_top_five: tuple[str, ...] = EXPECTED_NINERS_TOP_FIVE,
) -> OfficialRosterRankContractReport:
    csv_path = Path(path)
    issues: list[OfficialRosterRankIssue] = []
    rows: list[OfficialRosterRankRow] = []

    if not csv_path.exists():
        issue = OfficialRosterRankIssue(
            severity="error",
            row_number=None,
            field="path",
            issue=f"Official roster-rank input does not exist: {csv_path}",
            suggested_fix="Regenerate or restore the locked March 31 roster-rank CSV.",
        )
        return OfficialRosterRankContractReport(
            status="blocked",
            roster_team=roster_team,
            row_count=0,
            top_five_names=(),
            rows=(),
            issues=(issue,),
        )

    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != EXPECTED_HEADER:
            issues.append(
                OfficialRosterRankIssue(
                    severity="error",
                    row_number=1,
                    field="header",
                    issue="Official roster-rank CSV header does not match the v4 lock.",
                    suggested_fix=f"Use exact header: {','.join(EXPECTED_HEADER)}",
                )
            )
        raw_rows = list(reader)

    for row_number, raw_row in enumerate(raw_rows, start=2):
        if str(raw_row.get("roster_team") or "").strip() != roster_team:
            continue
        roster_rank = _required_int(
            raw_row.get("roster_rank"),
            issues,
            row_number=row_number,
            field="roster_rank",
        )
        league_rank = _required_int(
            raw_row.get("league_rank"),
            issues,
            row_number=row_number,
            field="league_rank",
        )
        if roster_rank is None or league_rank is None:
            continue
        player_name = str(raw_row.get("player_name") or "").strip()
        if not player_name:
            issues.append(
                OfficialRosterRankIssue(
                    severity="error",
                    row_number=row_number,
                    field="player_name",
                    issue="Official roster-rank row is missing player_name.",
                    suggested_fix="Fill player_name from the locked March 31 ranking sheet.",
                )
            )
            continue
        rows.append(
            OfficialRosterRankRow(
                roster_team=roster_team,
                roster_rank=roster_rank,
                player_name=player_name,
                position=str(raw_row.get("position") or "").strip(),
                nfl_team=str(raw_row.get("nfl_team") or "").strip(),
                league_rank=league_rank,
                source_title=str(raw_row.get("source_title") or "").strip(),
                source_date=str(raw_row.get("source_date") or "").strip(),
                ranking_source=str(raw_row.get("ranking_source") or "").strip(),
            )
        )

    _validate_roster_shape(
        rows,
        issues,
        roster_team=roster_team,
        expected_roster_count=expected_roster_count,
    )
    top_five_names = roster_league_rank_top_five_names(rows)
    if top_five_names != expected_top_five:
        issues.append(
            OfficialRosterRankIssue(
                severity="error",
                row_number=None,
                field="league_rank",
                issue=(
                    f"{roster_team} roster's league-rank top five is "
                    f"{top_five_names}, expected {expected_top_five}."
                ),
                suggested_fix=(
                    "Verify the locked March 31 ranking sheet and do not infer "
                    "top-five status from model value."
                ),
            )
        )

    status = "blocked" if any(issue.severity == "error" for issue in issues) else "ready"
    return OfficialRosterRankContractReport(
        status=status,
        roster_team=roster_team,
        row_count=len(rows),
        top_five_names=top_five_names,
        rows=tuple(rows),
        issues=tuple(issues),
    )


def roster_league_rank_top_five_names(
    rows: tuple[OfficialRosterRankRow, ...] | list[OfficialRosterRankRow],
) -> tuple[str, ...]:
    return tuple(row.player_name for row in roster_league_rank_top_five_rows(rows))


def roster_league_rank_top_five_rows(
    rows: tuple[OfficialRosterRankRow, ...] | list[OfficialRosterRankRow],
) -> tuple[OfficialRosterRankRow, ...]:
    return tuple(sorted(rows, key=lambda row: (row.league_rank, row.player_name))[:5])


def _validate_roster_shape(
    rows: list[OfficialRosterRankRow],
    issues: list[OfficialRosterRankIssue],
    *,
    roster_team: str,
    expected_roster_count: int,
) -> None:
    if len(rows) != expected_roster_count:
        issues.append(
            OfficialRosterRankIssue(
                severity="error",
                row_number=None,
                field="roster_team",
                issue=(
                    f"{roster_team} has {len(rows)} locked roster-rank rows; "
                    f"expected {expected_roster_count}."
                ),
                suggested_fix="Restore the complete 24-player Niners roster from March 31.",
            )
        )

    roster_ranks = [row.roster_rank for row in rows]
    expected_ranks = set(range(1, expected_roster_count + 1))
    if set(roster_ranks) != expected_ranks or len(roster_ranks) != len(set(roster_ranks)):
        issues.append(
            OfficialRosterRankIssue(
                severity="error",
                row_number=None,
                field="roster_rank",
                issue=(
                    f"{roster_team} roster_rank values must be exactly "
                    f"1-{expected_roster_count} with no duplicates."
                ),
                suggested_fix="Use the locked roster order from the official input CSV.",
            )
        )

    player_names = [row.player_name for row in rows]
    duplicate_names = sorted(
        {
            player_name
            for player_name in player_names
            if player_names.count(player_name) > 1
        }
    )
    if duplicate_names:
        issues.append(
            OfficialRosterRankIssue(
                severity="error",
                row_number=None,
                field="player_name",
                issue=f"Duplicate player names in official roster-rank CSV: {duplicate_names}",
                suggested_fix="Resolve duplicate official-input rows before using the contract.",
            )
        )


def _required_int(
    value: object,
    issues: list[OfficialRosterRankIssue],
    *,
    row_number: int,
    field: str,
) -> int | None:
    text = str(value or "").strip()
    if not text:
        issues.append(
            OfficialRosterRankIssue(
                severity="error",
                row_number=row_number,
                field=field,
                issue=f"{field} is required.",
                suggested_fix=f"Fill {field} from the locked March 31 ranking sheet.",
            )
        )
        return None
    try:
        return int(text)
    except ValueError:
        issues.append(
            OfficialRosterRankIssue(
                severity="error",
                row_number=row_number,
                field=field,
                issue=f"{field} must be numeric; got {text!r}.",
                suggested_fix=f"Use the numeric {field} from the official input CSV.",
            )
        )
        return None
