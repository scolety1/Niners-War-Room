from __future__ import annotations

from collections.abc import Iterable, Mapping

FORMULA_PREFIXES = ("=", "+", "-", "@")


def spreadsheet_safe_cell(value: object) -> object:
    """Encode formula-looking string cells as explicit spreadsheet text.

    Spaces and tabs are ignored only while locating the first relevant character.
    The apostrophe is prefixed before the original value so its whitespace and
    Unicode bytes remain present. A value already prefixed with an apostrophe is
    left unchanged, which makes repeated export idempotent. Non-strings retain
    their original type so CSV writers can preserve numeric semantics.
    """

    if not isinstance(value, str) or value.startswith("'"):
        return value
    relevant = value.lstrip(" \t")
    if relevant.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def spreadsheet_safe_rows(
    rows: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [
        {key: spreadsheet_safe_cell(value) for key, value in row.items()}
        for row in rows
    ]
