from __future__ import annotations

from pathlib import Path

from scripts.mock_draft_closeout_status import build_closeout_status, main


def test_closeout_status_prints_green_and_yellow(capsys) -> None:
    result = main([])

    output = capsys.readouterr().out
    assert result == 0
    assert "Infrastructure readiness: GREEN" in output
    assert "Actual draft-use readiness: YELLOW" in output


def test_closeout_status_prints_no_simulation_language() -> None:
    output = build_closeout_status()

    assert "No simulations run: yes" in output
    assert "No files written: yes" in output


def test_closeout_status_writes_no_files(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())

    build_closeout_status(manifest_path=str(tmp_path / "missing.local.json"))

    assert set(tmp_path.iterdir()) == before


def test_closeout_status_does_not_require_real_manifest() -> None:
    output = build_closeout_status(
        manifest_path="local_exports/mock_draft/missing_manifest.local.json"
    )

    assert "Manifest readiness: YELLOW" in output
