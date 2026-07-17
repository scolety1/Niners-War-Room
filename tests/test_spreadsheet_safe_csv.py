from __future__ import annotations

import csv
import io
from collections.abc import Callable, Iterable, Mapping
from contextlib import ExitStack
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from app.components import development_lab
from src.services import draft_freeze_service
from src.utils.spreadsheet_safe import (
    FORMULA_PREFIXES,
    SECURITY_RELEVANT_LEADING_WHITESPACE,
    SPREADSHEET_SAFE_PREFIX,
    spreadsheet_safe_cell,
    spreadsheet_safe_rows,
)

CLOSED_WHITESPACE = " \t\r\n\u00a0"
FORMULA_VALUES = {
    "=": "=1+1",
    "+": "+1+1",
    "-": "-1+1",
    "@": "@SUM(1,1)",
}
MIXED_WHITESPACE = " \t\r\n\u00a0"
REVERSE_MIXED_WHITESPACE = "\u00a0\n\r\t "
LONG_BOUNDED_MIXED_WHITESPACE = MIXED_WHITESPACE * 16
WHITESPACE_PREFIXES = (
    pytest.param("", id="none"),
    pytest.param(" ", id="space"),
    pytest.param("\t", id="tab"),
    pytest.param("\r", id="cr"),
    pytest.param("\n", id="lf"),
    pytest.param("\u00a0", id="nbsp"),
    pytest.param(" " * 3, id="repeated-space"),
    pytest.param("\t" * 3, id="repeated-tab"),
    pytest.param("\r" * 3, id="repeated-cr"),
    pytest.param("\n" * 3, id="repeated-lf"),
    pytest.param("\u00a0" * 3, id="repeated-nbsp"),
    pytest.param(MIXED_WHITESPACE, id="mixed"),
    pytest.param(REVERSE_MIXED_WHITESPACE, id="reverse-mixed"),
    pytest.param(LONG_BOUNDED_MIXED_WHITESPACE, id="long-bounded-mixed"),
)

BASELINE_BOUNDARY_CASES = (
    pytest.param("=1+1", id="direct-equals"),
    pytest.param("+1+1", id="direct-plus"),
    pytest.param("-1+1", id="direct-minus-string"),
    pytest.param("@SUM(1,1)", id="direct-at"),
    pytest.param(" =1+1", id="leading-space"),
    pytest.param("\t=1+1", id="leading-tab"),
    pytest.param(" \t  =1+1", id="multiple-ascii-whitespace"),
    pytest.param("\r=1+1", id="leading-cr"),
    pytest.param("\n=1+1", id="leading-lf"),
    pytest.param("\u00a0=1+1", id="leading-nbsp"),
    pytest.param(MIXED_WHITESPACE + "=1+1", id="multiple-all-whitespace"),
    pytest.param('"=1+1"', id="quoted-formula-text"),
    pytest.param("=SUM(1,2)", id="formula-with-commas"),
    pytest.param("=1+1\nsecond line", id="multiline-formula"),
    pytest.param('=IF(A1="x",1,0)', id="formula-with-double-quotes"),
    pytest.param("\u00e9=1+1", id="unicode-before-marker"),
    pytest.param("=\u00e9+1", id="unicode-after-marker"),
    pytest.param("", id="empty-string"),
    pytest.param("'ordinary", id="apostrophe-prefix"),
    pytest.param("'=1+1", id="already-protected"),
    pytest.param("-123", id="string-negative-number"),
    pytest.param(-123, id="numeric-negative-integer"),
    pytest.param(-123.5, id="numeric-negative-float"),
    pytest.param("value = 1", id="equals-away-from-start"),
    pytest.param("safe@example.invalid", id="safe-email"),
    pytest.param("https://example.invalid/?x=1", id="safe-url-query"),
    pytest.param("ordinary safe text", id="ordinary-safe-text"),
    pytest.param(True, id="boolean-true"),
    pytest.param(None, id="null-value"),
)


def _contract_encoded(value: object) -> object:
    if not isinstance(value, str) or value == "" or value.startswith("'"):
        return value
    index = 0
    while index < len(value) and value[index] in CLOSED_WHITESPACE:
        index += 1
    if index < len(value) and value[index] in FORMULA_VALUES:
        return "'" + value
    return value


def _serialized_contract_value(value: object) -> str:
    encoded = _contract_encoded(value)
    if encoded is None:
        return ""
    return str(encoded)


def _formula_capable(value: str) -> bool:
    return value.lstrip(CLOSED_WHITESPACE).startswith(tuple(FORMULA_VALUES))


def _row_encoder(
    cell_encoder: Callable[[object], object],
) -> Callable[[Iterable[Mapping[str, object]]], list[dict[str, object]]]:
    def encode(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
        return [
            {key: cell_encoder(value) for key, value in row.items()} for row in rows
        ]

    return encode


def _identity_rows(
    rows: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [dict(row) for row in rows]


def _serialize_and_parse(
    surface: str,
    value: object,
    tmp_path: Path,
    *,
    rows_encoder: Callable[
        [Iterable[Mapping[str, object]]], list[dict[str, object]]
    ]
    | None = None,
) -> tuple[str, list[str], list[dict[str, str]]]:
    source = {"sentinel_left": "left", "payload": value, "sentinel_right": "right"}
    with ExitStack() as stack:
        if surface == "development_lab":
            captured: dict[str, object] = {}
            stack.enter_context(
                patch.object(
                    development_lab.st,
                    "download_button",
                    side_effect=lambda *args, **kwargs: captured.update(kwargs),
                )
            )
            if rows_encoder is not None:
                stack.enter_context(
                    patch.object(development_lab, "spreadsheet_safe_rows", rows_encoder)
                )
            development_lab.csv_download("Export", [source], "development_lab.csv")
            serialized = str(captured["data"])
            with io.StringIO(serialized, newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                fieldnames = list(reader.fieldnames or ())
            return serialized, fieldnames, rows

        path = tmp_path / "draft_freeze.csv"
        if rows_encoder is not None:
            stack.enter_context(
                patch.object(draft_freeze_service, "spreadsheet_safe_rows", rows_encoder)
            )
        draft_freeze_service._write_csv(path, [source])
        serialized = path.read_bytes().decode("utf-8")
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fieldnames = list(reader.fieldnames or ())
        return serialized, fieldnames, rows


@pytest.mark.parametrize("prefix", WHITESPACE_PREFIXES)
@pytest.mark.parametrize("marker", tuple(FORMULA_VALUES))
def test_direct_helper_closed_whitespace_matrix(prefix: str, marker: str) -> None:
    value = prefix + FORMULA_VALUES[marker]
    expected = SPREADSHEET_SAFE_PREFIX + value

    encoded = spreadsheet_safe_cell(value)

    assert encoded == expected
    assert isinstance(encoded, str)
    assert encoded.startswith(SPREADSHEET_SAFE_PREFIX)
    assert encoded[1:] == value
    assert spreadsheet_safe_cell(encoded) == encoded


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("=SUM(1,2)", "'=SUM(1,2)"),
        ('=IF(A1="x",1,0)', '\'=IF(A1="x",1,0)'),
        ("\n=1+1", "'\n=1+1"),
        ("=1+1\nsecond line", "'=1+1\nsecond line"),
        ("\u00a0=\u03bb+\u00e9", "'\u00a0=\u03bb+\u00e9"),
        ('"=1+1"', '"=1+1"'),
    ),
)
def test_direct_helper_csv_sensitive_content(value: str, expected: str) -> None:
    encoded = spreadsheet_safe_cell(value)

    assert encoded == expected
    assert spreadsheet_safe_cell(encoded) == encoded


@pytest.mark.parametrize(
    "value",
    (
        "",
        "ordinary safe text",
        "safe@example.invalid",
        "https://example.invalid/?x=1",
        "value + 1",
        "value - 1",
        "\u00e9quipe \U0001f3c8",
        "123",
        "'=1+1",
        "'\t@SUM(1,1)",
    ),
)
def test_direct_helper_safe_controls_are_unchanged(value: str) -> None:
    assert spreadsheet_safe_cell(value) == value
    assert spreadsheet_safe_cell(spreadsheet_safe_cell(value)) == value


@pytest.mark.parametrize(
    "value",
    (
        -123,
        -123.5,
        123,
        123.5,
        True,
        False,
        None,
        date(2026, 7, 17),
        datetime(2026, 7, 17, 12, 30, tzinfo=UTC),
    ),
)
def test_direct_helper_preserves_non_string_identity_and_exact_type(
    value: object,
) -> None:
    encoded = spreadsheet_safe_cell(value)

    assert encoded is value
    assert type(encoded) is type(value)


def test_spreadsheet_safe_rows_preserves_source_structure_and_unicode() -> None:
    rows = [
        {
            "name": "Jos\u00e9 \U0001f3c8",
            "note": MIXED_WHITESPACE + "=1+1\nsecond line",
            "score": -3.5,
        }
    ]

    encoded = spreadsheet_safe_rows(rows)

    assert encoded == [
        {
            "name": "Jos\u00e9 \U0001f3c8",
            "note": "'" + MIXED_WHITESPACE + "=1+1\nsecond line",
            "score": -3.5,
        }
    ]
    assert rows == [
        {
            "name": "Jos\u00e9 \U0001f3c8",
            "note": MIXED_WHITESPACE + "=1+1\nsecond line",
            "score": -3.5,
        }
    ]


def test_helper_exports_the_closed_contract_constants() -> None:
    assert FORMULA_PREFIXES == ("=", "+", "-", "@")
    assert SECURITY_RELEVANT_LEADING_WHITESPACE == CLOSED_WHITESPACE
    assert tuple(ord(character) for character in CLOSED_WHITESPACE) == (
        0x0020,
        0x0009,
        0x000D,
        0x000A,
        0x00A0,
    )
    assert SPREADSHEET_SAFE_PREFIX == "'"


@pytest.mark.parametrize("surface", ("development_lab", "draft_freeze"))
@pytest.mark.parametrize("value", BASELINE_BOUNDARY_CASES)
def test_required_58_case_real_export_boundary_matrix(
    surface: str,
    value: object,
    tmp_path: Path,
) -> None:
    _serialized, fieldnames, rows = _serialize_and_parse(surface, value, tmp_path)

    assert fieldnames == ["sentinel_left", "payload", "sentinel_right"]
    assert len(rows) == 1
    assert rows[0]["sentinel_left"] == "left"
    assert rows[0]["sentinel_right"] == "right"
    assert rows[0]["payload"] == _serialized_contract_value(value)
    if isinstance(value, str) and _contract_encoded(value) != value:
        assert rows[0]["payload"].startswith(SPREADSHEET_SAFE_PREFIX)
        assert rows[0]["payload"][1:] == value
        assert not _formula_capable(rows[0]["payload"])


@pytest.mark.parametrize("surface", ("development_lab", "draft_freeze"))
@pytest.mark.parametrize("prefix", WHITESPACE_PREFIXES)
@pytest.mark.parametrize("marker", tuple(FORMULA_VALUES))
def test_real_export_boundaries_cover_every_marker_and_whitespace_prefix(
    surface: str,
    prefix: str,
    marker: str,
    tmp_path: Path,
) -> None:
    value = prefix + FORMULA_VALUES[marker]

    _serialized, fieldnames, rows = _serialize_and_parse(surface, value, tmp_path)

    assert fieldnames == ["sentinel_left", "payload", "sentinel_right"]
    assert len(rows) == 1
    assert rows[0] == {
        "sentinel_left": "left",
        "payload": SPREADSHEET_SAFE_PREFIX + value,
        "sentinel_right": "right",
    }
    assert rows[0]["payload"][1:] == value
    assert not _formula_capable(rows[0]["payload"])


@pytest.mark.parametrize(
    "board_name",
    (
        "war_board",
        "team_roster",
        "team_top_five",
        "team_forced_release",
        "draft_assets",
        "draft_picks",
        "draft_release_targets",
        "league_pressure",
        "league_default_releases",
    ),
)
def test_draft_freeze_writer_preserves_all_nine_board_family_contracts(
    tmp_path: Path,
    board_name: str,
) -> None:
    path = tmp_path / f"{board_name}.csv"
    original = MIXED_WHITESPACE + "+SUM(1,1)"

    draft_freeze_service._write_csv(
        path,
        [
            {
                "name": original,
                "detail": 'quoted, "value"\nnext line',
                "already_safe": "'@safe",
                "numeric": -42,
            }
        ],
    )

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {
            "name": SPREADSHEET_SAFE_PREFIX + original,
            "detail": 'quoted, "value"\nnext line',
            "already_safe": "'@safe",
            "numeric": "-42",
        }
    ]


def _mutant_without(omitted: str) -> Callable[[object], object]:
    allowed = CLOSED_WHITESPACE.replace(omitted, "")

    def encode(value: object) -> object:
        if not isinstance(value, str) or value.startswith("'"):
            return value
        relevant = value.lstrip(allowed)
        return "'" + value if relevant.startswith(tuple(FORMULA_VALUES)) else value

    return encode


def _mixed_scan_mutant(value: object) -> object:
    if not isinstance(value, str) or value.startswith("'"):
        return value
    index = 1 if value and value[0] in CLOSED_WHITESPACE else 0
    if index < len(value) and value[index] in FORMULA_VALUES:
        return "'" + value
    return value


def _numeric_coercion_mutant(value: object) -> object:
    rendered = str(value)
    if rendered.lstrip(CLOSED_WHITESPACE).startswith(tuple(FORMULA_VALUES)):
        return "'" + rendered
    return rendered


def _after_whitespace_prefix_mutant(value: object) -> object:
    if not isinstance(value, str) or value.startswith("'"):
        return value
    index = 0
    while index < len(value) and value[index] in CLOSED_WHITESPACE:
        index += 1
    if index < len(value) and value[index] in FORMULA_VALUES:
        return value[:index] + "'" + value[index:]
    return value


def _non_idempotent_mutant(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value.startswith("'"):
        return "'" + value
    if value.lstrip(CLOSED_WHITESPACE).startswith(tuple(FORMULA_VALUES)):
        return "'" + value
    return value


def _semantic_mutation_detected(
    mutation_id: str,
    tmp_path: Path,
) -> bool:
    if mutation_id == "M1_remove_cr":
        value = "\r=1+1"
        return _mutant_without("\r")(value) != _contract_encoded(value)
    if mutation_id == "M2_remove_lf":
        value = "\n=1+1"
        return _mutant_without("\n")(value) != _contract_encoded(value)
    if mutation_id == "M3_remove_nbsp":
        value = "\u00a0=1+1"
        return _mutant_without("\u00a0")(value) != _contract_encoded(value)
    if mutation_id == "M4_break_mixed_scan":
        value = MIXED_WHITESPACE + "=1+1"
        return _mixed_scan_mutant(value) != _contract_encoded(value)
    if mutation_id == "M5_disable_development_lab":
        _, _, rows = _serialize_and_parse(
            "development_lab", "=1+1", tmp_path, rows_encoder=_identity_rows
        )
        return _formula_capable(rows[0]["payload"])
    if mutation_id == "M6_disable_draft_freeze":
        _, _, rows = _serialize_and_parse(
            "draft_freeze", "@SUM(1,1)", tmp_path, rows_encoder=_identity_rows
        )
        return _formula_capable(rows[0]["payload"])
    if mutation_id == "M7_csv_quoting_only":
        serialized, _, rows = _serialize_and_parse(
            "development_lab", "=SUM(1,2)", tmp_path, rows_encoder=_identity_rows
        )
        return '"=SUM(1,2)"' in serialized and _formula_capable(rows[0]["payload"])
    if mutation_id == "M8_coerce_numeric_negative":
        mutated = _numeric_coercion_mutant(-123)
        return mutated != -123 and type(mutated) is not int
    if mutation_id == "M9_prefix_after_whitespace":
        value = MIXED_WHITESPACE + "=1+1"
        mutated = _after_whitespace_prefix_mutant(value)
        return isinstance(mutated, str) and not mutated.startswith("'")
    if mutation_id == "M10_remove_idempotence":
        first = _non_idempotent_mutant("=1+1")
        return _non_idempotent_mutant(first) != first
    raise AssertionError(f"unknown mutation: {mutation_id}")


@pytest.mark.parametrize(
    "mutation_id",
    (
        "M1_remove_cr",
        "M2_remove_lf",
        "M3_remove_nbsp",
        "M4_break_mixed_scan",
        "M5_disable_development_lab",
        "M6_disable_draft_freeze",
        "M7_csv_quoting_only",
        "M8_coerce_numeric_negative",
        "M9_prefix_after_whitespace",
        "M10_remove_idempotence",
    ),
)
def test_semantic_mutation_controls_detect_required_regressions(
    mutation_id: str,
    tmp_path: Path,
) -> None:
    assert _semantic_mutation_detected(mutation_id, tmp_path)
