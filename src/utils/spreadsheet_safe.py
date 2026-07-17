from __future__ import annotations

from collections.abc import Iterable, Mapping

FORMULA_PREFIXES = ("=", "+", "-", "@")
SPREADSHEET_SAFE_PREFIX = "'"
# Closed, reviewable set used only to locate the first security-relevant
# character. The encoder never strips or normalizes these original characters.
SECURITY_RELEVANT_LEADING_WHITESPACE = " \t\r\n\u00a0"


def spreadsheet_safe_cell(value: object) -> object:
    """Encode formula-looking string cells as explicit spreadsheet text.

    SPACE, TAB, CR, LF, and NBSP are ignored only while locating the first
    security-relevant character. The apostrophe is prefixed at index zero before
    the complete original value, so its whitespace and Unicode remain present.
    A value whose index-zero character is already the safety apostrophe remains
    unchanged; this is the explicit behavioral-idempotence rule. Non-strings
    retain their original type so CSV writers can preserve numeric semantics.
    """

    if not isinstance(value, str) or value == "":
        return value
    if value.startswith(SPREADSHEET_SAFE_PREFIX):
        return value

    relevant_index = 0
    while (
        relevant_index < len(value)
        and value[relevant_index] in SECURITY_RELEVANT_LEADING_WHITESPACE
    ):
        relevant_index += 1
    if value[relevant_index : relevant_index + 1] in FORMULA_PREFIXES:
        return SPREADSHEET_SAFE_PREFIX + value
    return value


def spreadsheet_safe_rows(
    rows: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [
        {key: spreadsheet_safe_cell(value) for key, value in row.items()}
        for row in rows
    ]
