from __future__ import annotations

import sqlite3

from src.data.migrations import INDEX_STATEMENTS, SCHEMA_STATEMENTS, initialize_database


def test_initialize_database_creates_expected_tables() -> None:
    connection = sqlite3.connect(":memory:")
    initialize_database(connection)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }

    assert {
        "players",
        "teams",
        "owners",
        "rosters",
        "official_rankings",
        "future_picks",
        "pick_values",
        "market_values",
        "player_features",
        "model_outputs",
        "owner_notes",
        "metadata_sources",
        "import_errors",
    }.issubset(tables)


def test_schema_and_index_statements_are_defined() -> None:
    assert len(SCHEMA_STATEMENTS) >= 13
    assert len(INDEX_STATEMENTS) >= 11
