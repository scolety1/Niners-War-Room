from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from src.config.settings import get_settings


def get_database_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return get_settings().database_path


@contextmanager
def connect(path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    database_path = get_database_path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
