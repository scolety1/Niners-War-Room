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
        if command[-1:] == ["scripts/audit_deployment_v2_docs_consistency.py"]:
            return _completed(command, stdout="Deployment V2 docs consistency verdict: GREEN\n")
        if "scripts/verify_deployment_v2_baseline_ancestry.py" in command:
            return _completed(
                command,
                stdout="Deployment V2 baseline ancestry verdict: GREEN\n",
            )
        raise AssertionError(f"unexpected command: {command}")

    return fake_run_command


def test_readiness_runner_clean_path_is_green(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    results = runner.run_readiness_checks(Path("."), sys.executable)

    assert runner.overall_verdict(results) == "GREEN"
    statuses = {result.name: result.status for result in results}
    assert statuses["import_report_comparison"] == "SKIPPED"
    assert statuses["baseline_ancestry"] == "SKIPPED"


def test_readiness_runner_dirty_status_is_not_green(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command(status_output=" M file.txt\n"))

    results = runner.run_readiness_checks(Path("."), sys.executable)

    assert runner.overall_verdict(results) == "RED"
    assert {result.name: result.status for result in results}["status"] == "RED"


def test_readiness_runner_missing_optional_import_zip_does_not_crash() -> None:
    result = runner.check_import_report(Path("."), sys.executable, import_zip=None)

    assert result.status == "SKIPPED"
    assert result.detail == "no import zip supplied"


def test_readiness_runner_missing_optional_baseline_does_not_crash() -> None:
    result = runner.check_baseline_ancestry(Path("."), sys.executable, baseline=None)

    assert result.status == "SKIPPED"
    assert result.detail == "no baseline supplied"


def test_readiness_runner_baseline_check_runs_when_supplied(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    results = runner.run_readiness_checks(Path("."), sys.executable, baseline="base123")

    assert {result.name: result.status for result in results}["baseline_ancestry"] == "GREEN"


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


def test_readiness_json_report_has_required_keys(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    results = runner.run_readiness_checks(Path("."), sys.executable)
    output = runner.readiness_json_report(results)

    assert {
        "verdict",
        "branch",
        "head",
        "clean_status",
        "diff_check",
        "local_only_guard",
        "guard_report",
        "import_report",
        "baseline_ancestry",
        "docs_audit",
        "schema_smoke_tests",
        "skipped_checks",
        "blockers",
        "violations",
        "checks",
    } <= set(output)
    assert output["verdict"] == "GREEN"
    assert output["branch"]["status"] == "GREEN"
    assert output["clean_status"]["detail"] == "clean"
    assert output["docs_audit"]["status"] == "GREEN"
    assert output["schema_smoke_tests"]["status"] == "SKIPPED"


def test_readiness_json_report_includes_non_green_checks(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command(status_output=" M file.txt\n"))

    results = runner.run_readiness_checks(Path("."), sys.executable)
    output = runner.readiness_json_report(results)

    assert output["verdict"] == "RED"
    assert output["clean_status"]["status"] == "RED"
    assert output["blockers"] == ["M file.txt"]
    assert output["violations"] == [
        {
            "check": "status",
            "status": "RED",
            "detail": "M file.txt",
        }
    ]


def test_readiness_json_report_tracks_skipped_import_report(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    results = runner.run_readiness_checks(Path("."), sys.executable)
    output = runner.readiness_json_report(results)

    assert output["import_report"]["status"] == "SKIPPED"
    assert output["skipped_checks"] == ["import_report_comparison", "baseline_ancestry"]


def test_readiness_runner_human_output_still_works(capsys) -> None:
    results = [
        runner.CheckResult("branch", "GREEN", "work/deployment-v2-discovery"),
        runner.CheckResult("status", "GREEN", "clean"),
    ]

    runner.print_human_report(results)
    output = capsys.readouterr().out

    assert "Deployment V2 readiness verdict: GREEN" in output
    assert "- branch: GREEN - work/deployment-v2-discovery" in output


def test_readiness_all_checks_adds_schema_smoke_tests(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    def fake_schema_smoke(_repo: Path, _python: str):
        return runner.CheckResult("schema_smoke_tests", "GREEN", "schema tests passed")

    monkeypatch.setattr(runner, "check_schema_smoke_tests", fake_schema_smoke)

    results = runner.run_readiness_checks(Path("."), sys.executable, all_checks=True)

    assert {result.name: result.status for result in results}["schema_smoke_tests"] == "GREEN"


def test_readiness_all_checks_failure_makes_final_non_green(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    def fake_schema_smoke(_repo: Path, _python: str):
        return runner.CheckResult("schema_smoke_tests", "RED", "schema tests failed")

    monkeypatch.setattr(runner, "check_schema_smoke_tests", fake_schema_smoke)

    results = runner.run_readiness_checks(Path("."), sys.executable, all_checks=True)

    assert runner.overall_verdict(results) == "RED"
    assert {result.name: result.status for result in results}["schema_smoke_tests"] == "RED"


def test_readiness_all_checks_json_includes_schema_and_optional_skips(monkeypatch) -> None:
    monkeypatch.setattr(runner, "run_command", _fake_run_command())

    def fake_schema_smoke(_repo: Path, _python: str):
        return runner.CheckResult("schema_smoke_tests", "GREEN", "schema tests passed")

    monkeypatch.setattr(runner, "check_schema_smoke_tests", fake_schema_smoke)

    output = runner.readiness_json_report(
        runner.run_readiness_checks(Path("."), sys.executable, all_checks=True)
    )

    assert output["schema_smoke_tests"]["status"] == "GREEN"
    assert output["import_report"]["status"] == "SKIPPED"
    assert output["baseline_ancestry"]["status"] == "SKIPPED"
    assert output["skipped_checks"] == ["import_report_comparison", "baseline_ancestry"]
