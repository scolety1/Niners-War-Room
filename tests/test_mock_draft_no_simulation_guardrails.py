from __future__ import annotations

from pathlib import Path

from scripts.mock_draft_input_readiness_check import main

FORBIDDEN_COMMAND_NAMES = ("run_simulation", "simulate_draft", "start_mock_draft")


def test_readiness_scripts_do_not_expose_simulation_commands() -> None:
    script_paths = (
        Path("scripts/mock_draft_state_smoke.py"),
        Path("scripts/mock_draft_input_readiness_check.py"),
    )

    for path in script_paths:
        text = path.read_text(encoding="utf-8").lower()
        for command_name in FORBIDDEN_COMMAND_NAMES:
            assert f"def {command_name}" not in text
            assert f" {command_name}(" not in text


def test_readiness_script_reports_no_simulation_language(capsys) -> None:
    result = main()

    captured = capsys.readouterr().out
    assert result == 0
    assert "No simulations run" in captured
    assert "No files are written" in captured


def test_docs_contain_no_simulation_gate() -> None:
    docs = (
        Path("docs/hq/parallel_lanes/MOCK_DRAFT_INPUT_READINESS_CONTRACT.md"),
        Path("docs/hq/parallel_lanes/MOCK_DRAFT_SIMULATOR_SERVICE_CONTRACT.md"),
        Path("docs/hq/parallel_lanes/MOCK_DRAFT_DRAFT_DAY_SAFETY_RUNBOOK.md"),
    )

    for path in docs:
        assert "simulation" in path.read_text(encoding="utf-8").lower()


def test_no_app_wiring_file_is_required() -> None:
    assert not Path("app/pages/mock_draft.py").exists()
    assert not Path("streamlit_app.py").exists()
