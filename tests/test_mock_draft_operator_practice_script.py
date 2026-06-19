from __future__ import annotations

from pathlib import Path

import pytest

from scripts.mock_draft_operator_practice import main


def test_demo_command_runs_with_fixture_only_language(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["demo"])

    output = capsys.readouterr().out
    assert result == 0
    assert "fixture-only practice" in output
    assert "No real simulation run" in output
    assert "Manual fixture draft: fixture:rookie_a" in output
    assert "Operator session validation: GREEN" in output


def test_status_command_runs(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["status"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Current pick: 1.01" in output


def test_available_command_runs(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["available"])

    output = capsys.readouterr().out
    assert result == 0
    assert "fixture:rookie_a" in output
    assert "Fixture Rookie A" in output


def test_validate_command_runs_without_real_manifest(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["validate"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Operator session validation: GREEN" in output


def test_upcoming_command_runs(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["upcoming"])

    output = capsys.readouterr().out
    assert result == 0
    assert "NEXT: 1.02 | NWR" in output


def test_script_writes_no_files_by_default(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)

    result = main(["status"])

    assert result == 0
    assert list(tmp_path.iterdir()) == []


def test_explicit_temp_state_path_round_trip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state_path = tmp_path / "fixture_operator_state.json"

    draft_result = main(
        ["draft", "--asset-id", "fixture:rookie_a", "--state-path", str(state_path)]
    )
    history_result = main(["history", "--state-path", str(state_path)])

    assert draft_result == 0
    assert history_result == 0
    assert Path(state_path).exists()


def test_invalid_asset_command_exits_nonzero_without_traceback(
    tmp_path,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    state_path = tmp_path / "fixture_operator_state.json"

    result = main(["draft", "--asset-id", "fixture:not_real", "--state-path", str(state_path)])

    captured = capsys.readouterr()
    assert result == 1
    assert "Operator practice error:" in captured.err
    assert "not available" in captured.err
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_duplicate_draft_command_exits_nonzero_without_traceback(
    tmp_path,
    capsys,
) -> None:  # type: ignore[no-untyped-def]
    state_path = tmp_path / "fixture_operator_state.json"
    assert main(["draft", "--asset-id", "fixture:rookie_a", "--state-path", str(state_path)]) == 0
    capsys.readouterr()

    result = main(["draft", "--asset-id", "fixture:rookie_a", "--state-path", str(state_path)])

    captured = capsys.readouterr()
    assert result == 1
    assert "Operator practice error:" in captured.err
    assert "already drafted" in captured.err
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


def test_empty_undo_reports_no_drafted_pick(capsys) -> None:  # type: ignore[no-untyped-def]
    result = main(["undo"])

    output = capsys.readouterr().out
    assert result == 0
    assert "No drafted pick to undo." in output
    assert "Undid last fixture pick." not in output


def test_help_documents_state_path_persistence(capsys) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    output = capsys.readouterr().out
    assert exc_info.value.code == 0
    assert "fixture state only" in output
    assert "--state-path" in output
    assert "commands start fresh" in output
    assert "unless --state-path is supplied" in output
    assert "no real simulation" in output
