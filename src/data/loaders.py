from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.data.db import connect
from src.data.migrations import initialize_database
from src.data.validators import (
    ImportIssue,
    ValidatedDataPack,
    summarize_issues,
    validate_data_pack,
)
from src.utils.text import merge_name


def resolve_data_pack(path: str | Path) -> Path:
    return Path(path).resolve()


@dataclass(frozen=True)
class LoadResult:
    data_pack_name: str
    database_path: Path | None
    inserted_rows: dict[str, int]
    issue_counts: dict[str, int]


LOAD_ORDER = (
    "players",
    "teams",
    "rosters",
    "official_rankings",
    "future_picks",
    "pick_values",
    "model_outputs",
    "metadata_sources",
)

REPLACE_TABLES = (
    "rosters",
    "official_rankings",
    "future_picks",
    "pick_values",
    "model_outputs",
    "metadata_sources",
)


def load_data_pack(path: str | Path, database_path: str | Path | None = None) -> LoadResult:
    validated = validate_data_pack(resolve_data_pack(path))
    with connect(database_path) as connection:
        initialize_database(connection)
        _replace_loaded_tables(connection)
        _insert_import_issues(connection, validated)

        inserted_rows: dict[str, int] = {}
        rows_by_table = dict(validated.rows_by_table)
        rows_by_table["players"] = _prepare_players(rows_by_table.get("players", []))
        rows_by_table["teams"] = _derive_teams(rows_by_table)
        for table_name in LOAD_ORDER:
            rows = rows_by_table.get(table_name, [])
            inserted_rows[table_name] = _insert_rows(connection, table_name, rows)

    return LoadResult(
        data_pack_name=validated.data_pack_name,
        database_path=Path(database_path) if database_path is not None else None,
        inserted_rows=inserted_rows,
        issue_counts=summarize_issues(validated.issues),
    )


def _replace_loaded_tables(connection: sqlite3.Connection) -> None:
    for table_name in reversed(REPLACE_TABLES):
        connection.execute(f"DELETE FROM {table_name}")


def _prepare_players(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    prepared: list[dict[str, object]] = []
    for row in rows:
        next_row = dict(row)
        if next_row.get("merge_name") is None and next_row.get("player_name") is not None:
            next_row["merge_name"] = merge_name(str(next_row["player_name"]))
        if next_row.get("active_flag") is None:
            next_row["active_flag"] = 1
        prepared.append(next_row)
    return prepared


def _derive_teams(rows_by_table: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    teams: dict[str, dict[str, object]] = {}
    for row in rows_by_table.get("rosters", []):
        _add_team(teams, row.get("team_id"), row.get("team_name"), row.get("owner_name"))
    for row in rows_by_table.get("future_picks", []):
        _add_team(teams, row.get("original_team_id"), row.get("original_team_name"), None)
        _add_team(
            teams,
            row.get("current_team_id"),
            row.get("current_team_name"),
            row.get("current_owner_name"),
        )
    return list(teams.values())


def _add_team(
    teams: dict[str, dict[str, object]],
    team_id: object,
    team_name: object,
    owner_name: object,
) -> None:
    if team_id is None:
        return
    team_id_text = str(team_id)
    if team_id_text in teams:
        return
    teams[team_id_text] = {
        "team_id": team_id_text,
        "team_name": str(team_name or team_id_text),
        "owner_name": owner_name,
        "active_flag": 1,
    }


def _insert_rows(
    connection: sqlite3.Connection, table_name: str, rows: list[dict[str, object]]
) -> int:
    if not rows:
        return 0
    columns = tuple(rows[0].keys())
    placeholders = ", ".join("?" for _ in columns)
    column_names = ", ".join(columns)
    sql = _insert_sql(table_name, columns, column_names, placeholders)
    values = [tuple(row.get(column) for column in columns) for row in rows]
    connection.executemany(sql, values)
    return len(rows)


def _insert_sql(
    table_name: str, columns: tuple[str, ...], column_names: str, placeholders: str
) -> str:
    conflict_column = {"players": "player_id", "teams": "team_id"}.get(table_name)
    if conflict_column is None:
        return f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    update_columns = [column for column in columns if column != conflict_column]
    update_clause = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
    return (
        f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders}) "
        f"ON CONFLICT({conflict_column}) DO UPDATE SET {update_clause}"
    )


def _insert_import_issues(
    connection: sqlite3.Connection, validated: ValidatedDataPack
) -> None:
    connection.execute(
        "DELETE FROM import_errors WHERE data_pack_name = ?",
        (validated.data_pack_name,),
    )
    rows = [
        _issue_to_row(issue, validated.snapshot_date, validated.data_pack_name)
        for issue in validated.issues
    ]
    _insert_rows(connection, "import_errors", rows)


def _issue_to_row(
    issue: ImportIssue, snapshot_date: str | None, data_pack_name: str
) -> dict[str, object]:
    return {
        "snapshot_date": snapshot_date,
        "data_pack_name": data_pack_name,
        "severity": issue.severity,
        "file_name": issue.file_name,
        "row_number": issue.row_number,
        "entity_type": issue.entity_type,
        "entity_name": issue.entity_name,
        "issue": issue.issue,
        "suggested_fix": issue.suggested_fix,
        "status": "open",
    }
