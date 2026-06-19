from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_deployment_v2_readiness_checks.py"
)
SPEC = importlib.util.spec_from_file_location("run_deployment_v2_readiness_checks", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _completed(command: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)


def _fake_run_command(
    *,
    status_output: str = "",
    guard_returncode: int = 0,
    guard_output: str = (
        "Deployment V2 local-only surface guard passed: no deploy surfaces detected.\n"
    ),
    guard_report: dict[str, object] | None = None,
):
    report = guard_report or {
        "verdict": "GREEN",
        "blocked_surface_count": 0,
        "violations": [],
    }

    def fake_run_command(_repo: Path, command: list[str]):
        if command[:3] == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="work/deployment-v2-discovery\n")
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return _completed(command, stdout="abc123full\n")
        if command[:3] == ["git", "rev-parse", "--short"]:
            return _completed(command, stdout="abc123\n")
        if command[:4] == ["git", "log", "-1", "--pretty=%s"]:
            return _completed(command, stdout="Readiness test fixture\n")
        if command[:3] == ["git", "status", "--short"]:
            return _completed(command, stdout=status_output)
        if command[:3] == ["git", "diff", "--check"]:
            return _completed(command)
        if command[-2:] == ["scripts/validate_local_only_surface_guard.py", "--report"]:
            return _completed(command, stdout=json.dumps(report))
        if command[-1:] == ["scripts/validate_local_only_surface_guard.py"]:
            return _completed(command, returncode=guard_returncode, stdout=guard_output)
        raise AssertionError(f"unexpected command: {command}")

    return fake_run_command


def test_readiness_runner_clean_path_is_green(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    results = runner.run_readiness_checks(Path("."), sys.executable)

    assert runner.overall_verdict(results) == "GREEN"
    statuses = {result.name: result.status for result in results}
    assert statuses["import_report_comparison"] == "SKIPPED"


def test_readiness_runner_dirty_status_is_not_green(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command(status_output=" M file.txt\n"))

    results = runner.run_readiness_checks(Path("."), sys.executable)

    assert runner.overall_verdict(results) == "RED"
    assert {result.name: result.status for result in results}["status"] == "RED"


def test_readiness_runner_missing_optional_import_zip_does_not_crash() -> None:
    result = runner.check_import_report(Path("."), sys.executable, import_zip=None)

    assert result.status == "SKIPPED"
    assert result.detail == "no import zip supplied"


def test_readiness_runner_local_guard_failure_propagates(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "run_command",
        _fake_run_command(guard_returncode=1, guard_output="blocked surface fixture\n"),
    )

    results = runner.run_readiness_checks(Path("."), sys.executable)

    assert runner.overall_verdict(results) == "RED"
    assert {result.name: result.status for result in results}["local_only_guard"] == "RED"


def test_readiness_runner_json_report_output_is_parseable(capsys) -> None:
    results = [
        runner.CheckResult("branch", "GREEN", "work/deployment-v2-discovery"),
        runner.CheckResult("import_report_comparison", "SKIPPED", "no import zip supplied"),
    ]

    runner.print_json_report(results)
    output = json.loads(capsys.readouterr().out)

    assert output["verdict"] == "GREEN"
    assert output["checks"][0]["name"] == "branch"
    assert output["checks"][1]["status"] == "SKIPPED"
