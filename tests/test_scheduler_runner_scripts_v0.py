from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
RUNBOOK = REPO_ROOT / "docs" / "hq" / "parallel_lanes" / "NWR_DISABLED_SCHEDULER_V0_RUNBOOK.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_runner_scripts_exist() -> None:
    for name in (
        "run_sleeper_refresh_v0.ps1",
        "run_nflverse_refresh_v0.ps1",
        "run_nwr_data_health_v0.ps1",
    ):
        assert (SCRIPTS / name).exists()


def test_runners_call_expected_master_scripts() -> None:
    sleeper = _read(SCRIPTS / "run_sleeper_refresh_v0.ps1")
    nflverse = _read(SCRIPTS / "run_nflverse_refresh_v0.ps1")
    health = _read(SCRIPTS / "run_nwr_data_health_v0.ps1")

    assert "scripts/sleeper_scheduled_pull_v0.py" in sleeper
    assert "scripts/sleeper_normalize_snapshot_v0.py" in sleeper
    assert "scripts/nflverse_scheduled_pull_v0.py" in nflverse
    assert "scripts/nflverse_normalize_snapshot_v0.py" in nflverse
    assert "scripts/nwr_operator_status_v0.py" in health
    assert "--write-report" in health


def test_candidate_generation_is_explicit_and_latest_approved_is_not_written() -> None:
    combined = "\n".join(
        _read(SCRIPTS / name)
        for name in (
            "run_sleeper_refresh_v0.ps1",
            "run_nflverse_refresh_v0.ps1",
            "run_nwr_data_health_v0.ps1",
        )
    )

    assert "[switch]$WriteCandidates" in combined
    assert "--write-candidates" in combined
    assert "--write-approved" not in combined
    assert "latest_approved.json" not in combined


def test_nflverse_runner_uses_local_only_pythonpath_and_restores_it() -> None:
    nflverse = _read(SCRIPTS / "run_nflverse_refresh_v0.ps1")

    assert r"C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps" in nflverse
    assert "$OriginalPythonPath = $env:PYTHONPATH" in nflverse
    assert "$env:PYTHONPATH = $NflreadpyPath" in nflverse
    assert "$env:PYTHONPATH = $OriginalPythonPath" in nflverse
    assert "--seasons $Seasons" in nflverse
    assert "--datasets $Datasets" in nflverse


def test_runbook_uses_disabled_task_examples_only() -> None:
    runbook = _read(RUNBOOK)

    assert "No Windows scheduled tasks were created" in runbook
    assert "Register-ScheduledTask" in runbook
    assert "-Disabled" in runbook
    assert "Enable-ScheduledTask" in runbook
    assert "Only after Tim/Master approval" in runbook


def test_runbook_records_required_schedules_and_approval_gates() -> None:
    runbook = _read(RUNBOOK)

    assert "Monday / Wednesday / Friday" in runbook
    assert "Every 2-3 days" in runbook
    assert "After each pull or daily" in runbook
    assert "latest_approved" in runbook
    assert "Tim/Master/QA approval" in runbook
    assert "QA/Data Hygiene remains HOLD" in runbook
