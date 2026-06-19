from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "verify_deployment_v2_baseline_ancestry.py"
)
SPEC = importlib.util.spec_from_file_location("verify_deployment_v2_baseline_ancestry", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
baseline = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = baseline
SPEC.loader.exec_module(baseline)


def _completed(command: list[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)


def _fake_run_git(*, ancestor_returncode: int = 0, status_output: str = ""):
    def fake_run_git(_repo: Path, *args: str):
        command = ["git", *args]
        if args == ("rev-parse", "HEAD"):
            return _completed(command, stdout="abc123full\n")
        if args == ("rev-parse", "--short", "HEAD"):
            return _completed(command, stdout="abc123\n")
        if args == ("cat-file", "-e", "base123^{commit}"):
            return _completed(command)
        if args == ("merge-base", "--is-ancestor", "base123", "HEAD"):
            return _completed(command, returncode=ancestor_returncode)
        if args == ("status", "--short"):
            return _completed(command, stdout=status_output)
        raise AssertionError(f"unexpected git args: {args}")

    return fake_run_git


def test_descendant_baseline_is_green(monkeypatch) -> None:
    monkeypatch.setattr(baseline, "run_git", _fake_run_git())

    result = baseline.verify_baseline(Path("."), "base123")

    assert result.verdict == "GREEN"
    assert result.ancestor is True


def test_missing_baseline_argument_is_yellow() -> None:
    result = baseline.verify_baseline(Path("."), "")

    assert result.verdict == "YELLOW"
    assert result.reasons == ["baseline commit was not supplied"]


def test_non_ancestor_baseline_is_red(monkeypatch) -> None:
    monkeypatch.setattr(baseline, "run_git", _fake_run_git(ancestor_returncode=1))

    result = baseline.verify_baseline(Path("."), "base123")

    assert result.verdict == "RED"
    assert result.ancestor is False


def test_dirty_checkout_is_red_when_clean_required(monkeypatch) -> None:
    monkeypatch.setattr(baseline, "run_git", _fake_run_git(status_output=" M docs/example.md\n"))

    result = baseline.verify_baseline(Path("."), "base123", require_clean=True)

    assert result.verdict == "RED"
    assert result.clean_status is False
    assert "clean status required but git status is not clean" in result.reasons


def test_result_to_dict_has_json_shape(monkeypatch) -> None:
    monkeypatch.setattr(baseline, "run_git", _fake_run_git())

    output = baseline.result_to_dict(baseline.verify_baseline(Path("."), "base123"))

    assert output["verdict"] == "GREEN"
    assert output["baseline"] == "base123"
    assert output["current_head"] == {"full": "abc123full", "short": "abc123"}
    assert output["ancestor"] is True
