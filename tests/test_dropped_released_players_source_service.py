from __future__ import annotations

import csv
from pathlib import Path

from src.services.dropped_released_players_source_service import (
    REQUIRED_COLUMNS,
    validate_dropped_released_players_source,
)

CONTRACT = Path("docs/model_v4/DROPPED_RELEASED_PLAYER_SOURCE_CONTRACT_20260609.md")
TEMPLATE = Path(
    "local_exports/model_v4/draft_prep/templates/dropped_released_players_template.csv"
)
ACTIVE_POOL = Path("local_exports/model_v4/draft_prep/latest/draftable_pool_review_rows.csv")
DECISION_BOARD = Path("app/pages/08_june15_review.py")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_source_contract_and_template_exist_with_guardrails() -> None:
    contract_text = CONTRACT.read_text(encoding="utf-8")
    template_header = TEMPLATE.read_text(encoding="utf-8").strip().split(",")

    assert list(REQUIRED_COLUMNS) == template_header
    assert "Missing dropped-player files must not be interpreted as proof" in contract_text
    assert "NWR Dynasty Score" in contract_text
    assert "final draft recommendations" in contract_text
    assert "never mutate active data packs" in contract_text
    assert len(_read_rows(TEMPLATE)) == 0


def test_validator_rejects_missing_required_columns(tmp_path: Path) -> None:
    source = tmp_path / "missing_columns.csv"
    report = tmp_path / "report.csv"
    _write_csv(source, ["player", "position"], [{"player": "", "position": "RB"}])

    result = validate_dropped_released_players_source(source, report_path=report)
    issues = _read_rows(report)

    assert result.valid is False
    assert any(row["issue_type"] == "missing_required_column" for row in issues)
    assert result.report_path == report


def test_validator_rejects_invalid_position_and_bool_values(tmp_path: Path) -> None:
    source = tmp_path / "bad_rows.csv"
    report = tmp_path / "report.csv"
    _write_csv(
        source,
        list(REQUIRED_COLUMNS),
        [
            {
                "player": "Example Only",
                "position": "EDGE",
                "nfl_team": "",
                "releasing_team_or_roster_owner": "Example Team",
                "release_status": "released",
                "source_date": "",
                "source_file": "example.csv",
                "notes": "",
                "manual_review_required": "maybe",
                "protected_status": "unknown",
                "legal_draftable": "maybe",
                "allowed_use": "legal draftable pool confirmation",
                "blocked_use": "NWR Dynasty Score; final draft recommendations",
            }
        ],
    )

    result = validate_dropped_released_players_source(source, report_path=report)
    issue_types = {row["issue_type"] for row in _read_rows(report)}

    assert result.valid is False
    assert "invalid_position" in issue_types
    assert "missing_source_date" in issue_types
    assert "invalid_legal_draftable" in issue_types
    assert "invalid_manual_review_required" in issue_types


def test_validator_accepts_shape_without_mutating_active_pool(tmp_path: Path) -> None:
    source = tmp_path / "valid_shape.csv"
    report = tmp_path / "report.csv"
    before_exists = ACTIVE_POOL.exists()
    before_text = ACTIVE_POOL.read_text(encoding="utf-8") if before_exists else ""
    _write_csv(source, list(REQUIRED_COLUMNS), [])

    result = validate_dropped_released_players_source(source, report_path=report)

    assert result.valid is True
    assert result.row_count == 0
    assert result.issue_count == 0
    assert _read_rows(report) == []
    assert ACTIVE_POOL.exists() is before_exists
    if before_exists:
        assert ACTIVE_POOL.read_text(encoding="utf-8") == before_text


def test_decision_board_not_touched_by_contract() -> None:
    decision_text = DECISION_BOARD.read_text(encoding="utf-8")

    assert "DROPPED_RELEASED_PLAYER_SOURCE_CONTRACT" not in decision_text
