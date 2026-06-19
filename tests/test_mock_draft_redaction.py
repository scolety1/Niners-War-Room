from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_redaction import summarize_input_reference


def test_fixture_mode_can_show_fake_rows() -> None:
    summary = summarize_input_reference(
        role="rookie_input",
        path="tests/fixtures/fake.csv",
        headers=("asset_id", "player"),
        row_count=1,
        mode="fixture",
        sample_rows=({"asset_id": "fixture:a", "player": "Fixture Rookie A"},),
    )

    assert summary.rows
    assert summary.real_mode_redacted is False


def test_real_mode_hides_rows_and_full_path() -> None:
    summary = summarize_input_reference(
        role="rookie_input",
        path="C:/private/local/rookies.csv",
        headers=("asset_id", "player"),
        row_count=2,
        mode="real",
        sample_rows=({"asset_id": "real:a", "player": "Real Player"},),
    )

    assert summary.display_path == "rookies.csv"
    assert summary.rows == ()
    assert summary.real_mode_redacted is True


def test_basename_header_row_count_summary() -> None:
    summary = summarize_input_reference(
        role="market_context",
        path="C:/private/market.csv",
        headers=("asset_id", "market_adp_pick"),
        row_count=7,
        mode="real",
    )

    assert summary.role == "market_context"
    assert summary.headers == ("asset_id", "market_adp_pick")
    assert summary.row_count == 7


def test_redaction_writes_no_files(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())

    summary = summarize_input_reference(
        role="my_picks",
        path=tmp_path / "my_picks.csv",
        headers=("overall_pick",),
        row_count=0,
        mode="real",
    )

    assert summary.no_files_written is True
    assert set(tmp_path.iterdir()) == before
