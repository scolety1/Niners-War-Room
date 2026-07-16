from __future__ import annotations

import csv
import io
from pathlib import Path
from unittest.mock import patch

import pytest

from app.components.development_lab import csv_download
from src.services.draft_freeze_service import _write_csv
from src.utils.spreadsheet_safe import spreadsheet_safe_cell, spreadsheet_safe_rows


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("=1+1", "'=1+1"),
        ("+SUM(A1:A2)", "'+SUM(A1:A2)"),
        ("-2+3", "'-2+3"),
        ("@SUM(1,1)", "'@SUM(1,1)"),
        ("  =1+1", "'  =1+1"),
        ("\t@SUM(1,1)", "'\t@SUM(1,1)"),
        (" \t-2+3", "' \t-2+3"),
        ("safe", "safe"),
        ("value = 1", "value = 1"),
        ("O'Brien", "O'Brien"),
        ("'=1+1", "'=1+1"),
        ("'  =1+1", "'  =1+1"),
        ("  '=1+1", "  '=1+1"),
        ("", ""),
    ),
)
def test_spreadsheet_safe_cell_string_contract(value: str, expected: str) -> None:
    assert spreadsheet_safe_cell(value) == expected
    assert spreadsheet_safe_cell(spreadsheet_safe_cell(value)) == expected


@pytest.mark.parametrize("value", (0, -3, 1.5, None, True))
def test_spreadsheet_safe_cell_preserves_non_strings(value: object) -> None:
    assert spreadsheet_safe_cell(value) is value


def test_spreadsheet_safe_rows_preserves_structure_and_unicode() -> None:
    rows = [{"name": "José 🏈", "note": "\t=1+1\nsecond line", "score": -3.5}]
    encoded = spreadsheet_safe_rows(rows)

    assert encoded == [
        {"name": "José 🏈", "note": "'\t=1+1\nsecond line", "score": -3.5}
    ]
    assert rows[0]["note"] == "\t=1+1\nsecond line"


def test_development_lab_download_encodes_strings_at_final_boundary() -> None:
    captured: dict[str, object] = {}
    rows = [
        {
            "safe": "José, Jr.",
            "formula": "  =HYPERLINK(\"https://example.invalid\",\"x\")",
            "multiline": "\t@SUM(1,1)\nsecond line",
            "already_safe": "'=1+1",
            "numeric": 7,
        }
    ]

    with patch(
        "app.components.development_lab.st.download_button",
        side_effect=lambda *args, **kwargs: captured.update(kwargs),
    ):
        csv_download("Export", rows, "development_lab.csv")

    parsed = list(csv.DictReader(io.StringIO(str(captured["data"]))))
    assert parsed == [
        {
            "safe": "José, Jr.",
            "formula": "'  =HYPERLINK(\"https://example.invalid\",\"x\")",
            "multiline": "'\t@SUM(1,1)\nsecond line",
            "already_safe": "'=1+1",
            "numeric": "7",
        }
    ]


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
def test_draft_freeze_board_writer_encodes_every_board_family(
    tmp_path: Path,
    board_name: str,
) -> None:
    path = tmp_path / f"{board_name}.csv"
    _write_csv(
        path,
        [
            {
                "name": "\t+SUM(1,1)",
                "detail": "quoted, value\nnext line",
                "already_safe": "'@safe",
                "numeric": -42,
            }
        ],
    )

    row = list(csv.DictReader(path.open(newline="", encoding="utf-8")))[0]
    assert row == {
        "name": "'\t+SUM(1,1)",
        "detail": "quoted, value\nnext line",
        "already_safe": "'@safe",
        "numeric": "-42",
    }
