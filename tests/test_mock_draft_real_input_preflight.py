from __future__ import annotations

from scripts.mock_draft_real_input_preflight import main


def test_missing_manifest_reports_yellow(capsys) -> None:
    result = main(["local_exports/mock_draft/missing_manifest.local.json"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Overall readiness: YELLOW" in output
    assert "No simulations run" in output


def test_fixture_manifest_reports_green(capsys) -> None:
    result = main(["tests/fixtures/mock_draft_inputs/input_manifest_fixture.json"])

    output = capsys.readouterr().out
    assert result == 0
    assert "Overall readiness: GREEN" in output
    assert "Frozen rookie input" in output


def test_malformed_manifest_reports_red(capsys) -> None:
    result = main(["tests/fixtures/mock_draft_inputs/adversarial/malformed_manifest.json"])

    output = capsys.readouterr().out
    assert result == 1
    assert "Overall readiness: RED" in output
