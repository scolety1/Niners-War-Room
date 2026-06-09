from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES

PICK_LABEL_PATTERN = re.compile(r"^(?:\d{4}\s+)?(?P<round>[1-9]\d*)\.(?P<slot>\d{2})$")
DEFAULT_ROSTER_LIMIT = 24


@dataclass(frozen=True)
class ImportIssue:
    severity: str
    file_name: str | None
    issue: str
    row_number: int | None = None
    entity_type: str | None = None
    entity_name: str | None = None
    suggested_fix: str | None = None


@dataclass(frozen=True)
class ValidatedDataPack:
    data_pack_path: Path
    data_pack_name: str
    snapshot_date: str | None
    rows_by_table: dict[str, list[dict[str, object]]]
    issues: tuple[ImportIssue, ...]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


def validate_data_pack(
    path: str | Path, roster_limit: int = DEFAULT_ROSTER_LIMIT
) -> ValidatedDataPack:
    data_pack_path = Path(path).resolve()
    data_pack_name = data_pack_path.name
    rows_by_table: dict[str, list[dict[str, object]]] = {}
    issues: list[ImportIssue] = []

    for file_name in REQUIRED_V1_FILES:
        csv_path = data_pack_path / file_name
        schema = CSV_SCHEMAS[file_name]
        if not csv_path.exists():
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name=file_name,
                    issue="Required CSV file is missing.",
                    suggested_fix=f"Add {file_name} to the data pack.",
                )
            )
            continue

        frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        missing_columns = [
            column for column in schema.required_columns if column not in frame.columns
        ]
        if missing_columns:
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name=file_name,
                    issue=f"Missing required columns: {', '.join(missing_columns)}.",
                    suggested_fix="Add the missing columns or update the CSV schema.",
                )
            )
            continue

        valid_rows: list[dict[str, object]] = []
        for row_offset, (_, raw_row) in enumerate(frame.iterrows(), start=2):
            row_number = row_offset
            row = {column: _clean_value(raw_row.get(column, "")) for column in schema.all_columns}
            row_errors = _validate_required_values(file_name, row, row_number)
            row_errors.extend(_validate_numeric_values(file_name, row, row_number))
            row_errors.extend(_validate_player_identity(file_name, row, row_number))
            row_errors.extend(_validate_pick_label(file_name, row, row_number))
            issues.extend(row_errors)
            if not any(issue.severity == "error" for issue in row_errors):
                valid_rows.append(_coerce_row(file_name, row))

        rows_by_table[schema.table_name] = valid_rows

    issues.extend(_validate_cross_file_rules(rows_by_table, roster_limit))
    snapshot_date = _first_snapshot_date(rows_by_table)
    return ValidatedDataPack(
        data_pack_path=data_pack_path,
        data_pack_name=data_pack_name,
        snapshot_date=snapshot_date,
        rows_by_table=rows_by_table,
        issues=tuple(issues),
    )


def _clean_value(value: object) -> str | None:
    text = str(value).strip()
    return text or None


def _validate_required_values(
    file_name: str, row: dict[str, object], row_number: int
) -> list[ImportIssue]:
    schema = CSV_SCHEMAS[file_name]
    issues: list[ImportIssue] = []
    for column in schema.required_columns:
        if row.get(column) in (None, ""):
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name=file_name,
                    row_number=row_number,
                    entity_type=schema.table_name,
                    entity_name=_entity_name(row),
                    issue=f"Missing required value for {column}.",
                    suggested_fix=f"Populate {column}.",
                )
            )
    return issues


def _validate_numeric_values(
    file_name: str, row: dict[str, object], row_number: int
) -> list[ImportIssue]:
    schema = CSV_SCHEMAS[file_name]
    issues: list[ImportIssue] = []
    for column in schema.integer_columns:
        value = row.get(column)
        if value is not None and not _is_int(value):
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name=file_name,
                    row_number=row_number,
                    entity_type=schema.table_name,
                    entity_name=_entity_name(row),
                    issue=f"{column} must be an integer.",
                    suggested_fix=f"Replace {column} with a whole number.",
                )
            )
    for column in schema.float_columns:
        value = row.get(column)
        if value is not None and not _is_float(value):
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name=file_name,
                    row_number=row_number,
                    entity_type=schema.table_name,
                    entity_name=_entity_name(row),
                    issue=f"{column} must be numeric.",
                    suggested_fix=f"Replace {column} with a number.",
                )
            )
    return issues


def _validate_player_identity(
    file_name: str, row: dict[str, object], row_number: int
) -> list[ImportIssue]:
    if "player_id" not in row and "player_name" not in row:
        return []
    if row.get("player_id") or row.get("player_name"):
        return []
    return [
        ImportIssue(
            severity="error",
            file_name=file_name,
            row_number=row_number,
            entity_type=CSV_SCHEMAS[file_name].table_name,
            issue="Missing player identity.",
            suggested_fix="Provide player_id or player_name.",
        )
    ]


def _validate_pick_label(
    file_name: str, row: dict[str, object], row_number: int
) -> list[ImportIssue]:
    if "pick_label" not in row:
        return []
    label = row.get("pick_label")
    if label is None:
        return []

    match = PICK_LABEL_PATTERN.match(str(label))
    if match is None:
        return [
            ImportIssue(
                severity="error",
                file_name=file_name,
                row_number=row_number,
                entity_type=CSV_SCHEMAS[file_name].table_name,
                entity_name=str(label),
                issue="Invalid pick label.",
                suggested_fix="Use labels like 2026 1.01 or 1.01.",
            )
        ]

    issues: list[ImportIssue] = []
    row_round = row.get("round")
    row_slot = row.get("slot")
    if (
        row_round is not None
        and _is_int(row_round)
        and int(str(row_round)) != int(match.group("round"))
    ):
        issues.append(
            ImportIssue(
                severity="error",
                file_name=file_name,
                row_number=row_number,
                entity_type=CSV_SCHEMAS[file_name].table_name,
                entity_name=str(label),
                issue="Pick label round does not match round column.",
                suggested_fix="Make pick_label and round consistent.",
            )
        )
    if (
        row_slot is not None
        and _is_int(row_slot)
        and int(str(row_slot)) != int(match.group("slot"))
    ):
        issues.append(
            ImportIssue(
                severity="error",
                file_name=file_name,
                row_number=row_number,
                entity_type=CSV_SCHEMAS[file_name].table_name,
                entity_name=str(label),
                issue="Pick label slot does not match slot column.",
                suggested_fix="Make pick_label and slot consistent.",
            )
        )
    return issues


def _validate_cross_file_rules(
    rows_by_table: dict[str, list[dict[str, object]]], roster_limit: int
) -> list[ImportIssue]:
    issues: list[ImportIssue] = []
    roster_rows = rows_by_table.get("rosters", [])
    ranking_rows = rows_by_table.get("official_rankings", [])
    future_pick_rows = rows_by_table.get("future_picks", [])

    player_teams: dict[str, set[str]] = defaultdict(set)
    player_names: dict[str, str] = {}
    team_ids: set[str] = set()
    roster_counts: Counter[str] = Counter()
    for row in roster_rows:
        player_id = str(row.get("player_id") or "")
        team_id = str(row.get("team_id") or "")
        if team_id:
            team_ids.add(team_id)
            roster_counts[team_id] += 1
        else:
            issues.append(_unknown_team_issue("fact_rosters.csv", row))
        if player_id and team_id:
            player_teams[player_id].add(team_id)
            player_names[player_id] = str(row.get("player_name") or player_id)

    for player_id, teams in player_teams.items():
        if len(teams) > 1:
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name="fact_rosters.csv",
                    entity_type="player",
                    entity_name=player_names[player_id],
                    issue="Player appears on multiple teams.",
                    suggested_fix="Keep the player on only one roster for this snapshot.",
                )
            )

    for team_id, count in roster_counts.items():
        if count != roster_limit:
            issues.append(
                ImportIssue(
                    severity="warning",
                    file_name="fact_rosters.csv",
                    entity_type="team",
                    entity_name=team_id,
                    issue=f"Roster count is {count}; expected {roster_limit}.",
                    suggested_fix=(
                        "Confirm this is a partial sample or update the configured roster limit."
                    ),
                )
            )

    ranked_player_ids = {
        str(row.get("player_id"))
        for row in ranking_rows
        if row.get("player_id") and _league_rank_value(row) is not None
    }
    ranking_by_player = {
        str(row.get("player_id")): row
        for row in ranking_rows
        if row.get("player_id") is not None
    }
    for row in roster_rows:
        player_id = str(row.get("player_id") or "")
        league_rank = _league_rank_value(row, ranking_by_player.get(player_id))
        if league_rank is None:
            issues.append(
                ImportIssue(
                    severity="warning",
                    file_name="fact_rosters.csv",
                    entity_type="player",
                    entity_name=str(row.get("player_name") or player_id),
                    issue="Roster row is missing a league rank.",
                    suggested_fix="Populate league rank or confirm this player is unranked.",
                )
            )
        if league_rank == 400 and not _is_rank_placeholder(
            row,
            ranking_by_player.get(player_id),
        ):
            issues.append(
                ImportIssue(
                    severity="warning",
                    file_name="fact_rosters.csv",
                    entity_type="player",
                    entity_name=str(row.get("player_name") or player_id),
                    issue="League rank is 400.",
                    suggested_fix="Confirm this is the intended placeholder or trailing rank.",
                )
            )
        if player_id and player_id not in ranked_player_ids:
            issues.append(
                ImportIssue(
                    severity="warning",
                    file_name="fact_official_rankings.csv",
                    entity_type="player",
                    entity_name=str(row.get("player_name") or player_id),
                    issue="Roster player is missing a league rank.",
                    suggested_fix=(
                        "Add the player to fact_official_rankings.csv or confirm unranked status."
                    ),
                )
            )

    for row in ranking_rows:
        league_rank = _league_rank_value(row)
        if league_rank is None:
            issues.append(
                ImportIssue(
                    severity="warning",
                    file_name="fact_official_rankings.csv",
                    entity_type="player",
                    entity_name=str(row.get("player_name") or row.get("player_id") or ""),
                    issue="League ranking row is missing a league rank.",
                    suggested_fix="Populate league rank or confirm this player is unranked.",
                )
            )
        if league_rank == 400 and not _is_rank_placeholder(row):
            issues.append(
                ImportIssue(
                    severity="warning",
                    file_name="fact_official_rankings.csv",
                    entity_type="player",
                    entity_name=str(row.get("player_name") or row.get("player_id") or ""),
                    issue="League rank is 400.",
                    suggested_fix="Confirm this is the intended placeholder or trailing rank.",
                )
            )

    pick_keys = [_pick_key(row) for row in future_pick_rows]
    for pick_key, count in Counter(pick_keys).items():
        if pick_key and count > 1:
            issues.append(
                ImportIssue(
                    severity="error",
                    file_name="fact_future_picks.csv",
                    entity_type="draft_pick",
                    entity_name=" ".join(str(part) for part in pick_key),
                    issue="Duplicate draft pick.",
                    suggested_fix="Keep only one current owner row for each pick.",
                )
            )

    for row in future_pick_rows:
        issues.extend(_validate_pick_team("original", row, team_ids))
        issues.extend(_validate_pick_team("current", row, team_ids))

    return issues


def _validate_pick_team(
    prefix: str, row: dict[str, object], known_team_ids: set[str]
) -> list[ImportIssue]:
    team_id = row.get(f"{prefix}_team_id")
    if team_id is None:
        return []
    if str(team_id) in known_team_ids:
        return []
    return [
        ImportIssue(
            severity="warning",
            file_name="fact_future_picks.csv",
            entity_type="team",
            entity_name=str(team_id),
            issue="Unknown team.",
            suggested_fix=(
                "Use a team_id that appears in fact_rosters.csv or confirm this team exists."
            ),
        )
    ]


def _unknown_team_issue(file_name: str, row: dict[str, object]) -> ImportIssue:
    return ImportIssue(
        severity="warning",
        file_name=file_name,
        entity_type="team",
        entity_name=str(row.get("team_name") or ""),
        issue="Unknown team.",
        suggested_fix="Provide a stable team_id and team_name.",
    )


def _pick_key(row: dict[str, object]) -> tuple[object, object, object] | None:
    if row.get("pick_year") is None or row.get("round") is None:
        return None
    if row.get("slot") is not None:
        return (row.get("pick_year"), row.get("round"), row.get("slot"))
    label = row.get("pick_label")
    if label is not None:
        match = PICK_LABEL_PATTERN.match(str(label))
        if match is not None:
            return (row.get("pick_year"), row.get("round"), int(match.group("slot")))
    return (row.get("pick_year"), row.get("round"), row.get("pick_label"))


def _coerce_row(file_name: str, row: dict[str, object]) -> dict[str, object]:
    schema = CSV_SCHEMAS[file_name]
    coerced = dict(row)
    for column in schema.integer_columns:
        if coerced.get(column) is not None:
            coerced[column] = int(str(coerced[column]))
    for column in schema.float_columns:
        if coerced.get(column) is not None:
            coerced[column] = float(str(coerced[column]))
    return coerced


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


def _is_rank_placeholder(
    row: dict[str, object],
    fallback_row: dict[str, object] | None = None,
) -> bool:
    for candidate in (row, fallback_row):
        if candidate is None:
            continue
        value = candidate.get("is_rank_placeholder")
        if str(value or "").strip().lower() in {"1", "true", "yes"}:
            return True
    return False


def _first_snapshot_date(rows_by_table: dict[str, list[dict[str, object]]]) -> str | None:
    for rows in rows_by_table.values():
        for row in rows:
            value = row.get("snapshot_date")
            if value is not None:
                return str(value)
    return None


def _entity_name(row: dict[str, object]) -> str | None:
    for column in ("player_name", "pick_label", "team_name", "file_name", "player_id"):
        value = row.get(column)
        if value is not None:
            return str(value)
    return None


def _is_int(value: object) -> bool:
    try:
        int(str(value))
    except ValueError:
        return False
    return True


def _is_float(value: object) -> bool:
    try:
        float(str(value))
    except ValueError:
        return False
    return True


def summarize_issues(issues: Iterable[ImportIssue]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0}
    for issue in issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    return counts
