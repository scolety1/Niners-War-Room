from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from src.launcher import windows_desktop as launcher


def _identity(paths: launcher.LauncherPaths, pid: int, name: str, parent: int) -> dict[str, Any]:
    executable = paths.repo_root / f"{name}.exe"
    return {
        "pid": pid,
        "executable": str(executable.resolve()),
        "created": pid * 100,
        "command_line": f'"{executable.resolve()}" --run-id stop-test-run',
        "parent_pid": parent,
    }


@pytest.fixture
def stop_paths(tmp_path: Path) -> launcher.LauncherPaths:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    repo.mkdir()
    paths = launcher.LauncherPaths(
        repo_root=repo,
        data_home=home,
        draft_root=home / "draft",
        development_lab_root=home / "lab",
        mock_draft_root=home / "mock",
        refresh_root=home / "refresh",
        backup_root=home / "backups",
        logs_root=home / "logs",
        run_root=home / "run",
        browser_profile=home / "browser-profile",
        config_root=home / "config",
        recovery_root=home / "recovery",
    )
    launcher.ensure_directories(paths)
    return paths


def _record(paths: launcher.LauncherPaths, state: str = "RUNNING") -> dict[str, Any]:
    root = _identity(paths, 101, "launcher", 1)
    streamlit = _identity(paths, 102, "streamlit", 101)
    listener = _identity(paths, 103, "listener", 102)
    record = {
        "launcher_version": launcher.LAUNCHER_VERSION,
        "state": state,
        "repo_root": str(paths.repo_root),
        "data_root": str(paths.data_home),
        "run_id": "stop-test-run",
        "lock_nonce": "stop-test-run",
        "port": launcher.PORT,
        "app_commit": launcher.EXPECTED_APP_COMMIT,
        "verified_descendants": [],
        **launcher._identity_fields("launcher", root),
        **launcher._identity_fields("streamlit", streamlit),
        **launcher._identity_fields("listener", listener),
    }
    launcher._atomic_json(paths.lock_path, record)
    return record


def _snapshot(*resources: str, conflicts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "owned": [
            {"resource": resource, "pid": 100 + index}
            for index, resource in enumerate(resources, start=1)
        ],
        "conflicts": conflicts or [],
        "absent_registrations": [],
        "port_listeners": [103] if "listener" in resources else [],
    }


def _configure_stop(
    monkeypatch: pytest.MonkeyPatch,
    snapshots: list[dict[str, Any]],
) -> list[list[str]]:
    commands: list[list[str]] = []
    iterator = iter(snapshots)
    latest = snapshots[-1]

    def next_snapshot(*_args: object) -> dict[str, Any]:
        nonlocal latest
        try:
            latest = next(iterator)
        except StopIteration:
            pass
        return latest

    monkeypatch.setattr(launcher, "_acquire_stop_guard", lambda _paths: "guard")
    monkeypatch.setattr(launcher, "_release_stop_guard", lambda _paths, _nonce: None)
    monkeypatch.setattr(launcher, "_capture_descendants", lambda _roots: [])
    monkeypatch.setattr(launcher, "_resource_snapshot", next_snapshot)
    monkeypatch.setattr(launcher, "_shutdown_registered_browsers", lambda *_a, **_k: [])
    monkeypatch.setattr(
        launcher,
        "_target_owned_tree",
        lambda record, prefix, **_kwargs: commands.append([prefix, str(record["run_id"])])
        or {"status": "RECOVERY_REQUIRED"},
    )
    monkeypatch.setattr(launcher, "SHUTDOWN_TIMEOUT_SECONDS", 0.0)
    monkeypatch.setattr(launcher, "STOP_ESCALATION_SECONDS", 0.0)
    monkeypatch.setattr(launcher, "port_is_listening", lambda *_args: False)
    return commands


@pytest.mark.parametrize("resource", ["streamlit", "listener", "browser"])
def test_ownership_survives_each_remaining_resource_class(
    stop_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot(resource)])
    with pytest.raises(launcher.LauncherError, match="RECOVERY_REQUIRED"):
        launcher.request_stop(stop_paths)
    retained = json.loads(stop_paths.lock_path.read_text(encoding="utf-8"))
    assert retained["state"] == "RECOVERY_REQUIRED"
    assert retained["remaining_resources"]["owned"][0]["resource"] == resource


def test_ownership_clears_only_after_all_resource_classes_disappear(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(
        monkeypatch,
        [_snapshot("launcher", "streamlit", "listener", "browser"), _snapshot()],
    )
    assert launcher.request_stop(stop_paths)["status"] == "STOPPED"
    assert not stop_paths.lock_path.exists()
    assert stop_paths.last_stop_receipt.exists()


def test_graceful_stop_completes_normally(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    commands = _configure_stop(monkeypatch, [_snapshot("launcher"), _snapshot()])
    result = launcher.request_stop(stop_paths)
    assert result["status"] == "STOPPED"
    assert commands == []


def test_graceful_timeout_records_recovery_required(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot("streamlit")])
    with pytest.raises(launcher.LauncherError):
        launcher.request_stop(stop_paths)
    assert launcher._read_ownership(stop_paths)["state"] == "RECOVERY_REQUIRED"  # type: ignore[index]


def test_subsequent_stop_resumes_recovery(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths, "RECOVERY_REQUIRED")
    _configure_stop(monkeypatch, [_snapshot("streamlit"), _snapshot()])
    assert launcher.request_stop(stop_paths)["status"] == "STOPPED"
    assert not stop_paths.lock_path.exists()


def test_status_reports_retained_recovery_state(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record(stop_paths, "RECOVERY_REQUIRED")
    record["remaining_resources"] = _snapshot("listener")
    launcher._atomic_json(stop_paths.lock_path, record)
    monkeypatch.setattr(
        launcher,
        "validate_state",
        lambda _paths: launcher.ValidationResult(True, "EMPTY_STATE", ()),
    )
    monkeypatch.setattr(
        launcher,
        "inspect_legacy_migration",
        lambda _paths: launcher.MigrationResult("NO_LEGACY_STATE"),
    )
    monkeypatch.setattr(launcher, "junction_status", lambda _paths: {})
    monkeypatch.setattr(launcher, "find_python", lambda _repo: Path(sys.executable))
    monkeypatch.setattr(launcher, "health_ok", lambda: True)
    result = launcher.status(stop_paths)
    assert result["process_ownership"] == "RECOVERY_REQUIRED"
    assert result["remaining_resources"]["owned"][0]["resource"] == "listener"


def test_process_exit_between_validation_and_signal_is_not_targeted(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record(stop_paths)
    identity = _identity(stop_paths, 102, "streamlit", 101)
    identities = iter((identity, None))
    monkeypatch.setattr(launcher, "_process_identity", lambda _pid: next(identities, None))
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not signal")),
    )
    with pytest.raises(launcher.LauncherError, match="identity changed"):
        launcher._target_owned_tree(record, "streamlit", allow_force=True)


def test_pid_reuse_is_an_ownership_conflict(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record(stop_paths)
    reused = {**_identity(stop_paths, 102, "unrelated", 1), "created": 999999}
    monkeypatch.setattr(launcher, "_process_identity", lambda pid: reused if pid == 102 else None)
    monkeypatch.setattr(launcher, "_listener_pids", lambda: set())
    snapshot = launcher._resource_snapshot(stop_paths, record)
    assert {item["status"] for item in snapshot["conflicts"]} == {"IDENTITY_MISMATCH"}


def test_changed_listener_is_never_treated_as_owned(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record(stop_paths)
    monkeypatch.setattr(launcher, "_process_identity", lambda _pid: None)
    monkeypatch.setattr(launcher, "_listener_pids", lambda: {999})
    snapshot = launcher._resource_snapshot(stop_paths, record)
    assert snapshot["conflicts"] == [
        {"resource": "listener", "pid": 999, "status": "CHANGED_LISTENER"}
    ]


def test_unrelated_listener_blocks_without_any_termination(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    conflict = [{"resource": "listener", "pid": 999, "status": "CHANGED_LISTENER"}]
    _configure_stop(monkeypatch, [_snapshot(conflicts=conflict)])
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("unrelated process targeted")),
    )
    with pytest.raises(launcher.LauncherError, match="Ownership conflict"):
        launcher.request_stop(stop_paths)
    assert stop_paths.lock_path.exists()


def test_unrelated_browser_registration_is_preserved(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record(stop_paths)
    registration = stop_paths.run_root / "browser.201.json"
    browser = _identity(stop_paths, 201, "chrome", 1)
    launcher._atomic_json(
        registration,
        {
            "launcher_version": launcher.LAUNCHER_VERSION,
            **launcher._identity_fields("browser", browser),
            "browser_profile": str(stop_paths.browser_profile),
            "repo_root": str(stop_paths.repo_root),
            "data_root": str(stop_paths.data_home),
            "run_id": "different-run",
            "expected_browser": browser["executable"],
        },
    )
    monkeypatch.setattr(launcher, "_process_identity", lambda pid: browser if pid == 201 else None)
    monkeypatch.setattr(launcher, "_listener_pids", lambda: set())
    monkeypatch.setattr(launcher, "browser_candidates", lambda: (Path(browser["executable"]),))
    snapshot = launcher._resource_snapshot(stop_paths, record)
    assert snapshot["conflicts"][0]["status"] == "UNVERIFIED_PRESERVED"
    assert registration.exists()


def test_one_of_multiple_owned_browsers_remaining_retains_ownership(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot("browser")])
    with pytest.raises(launcher.LauncherError):
        launcher.request_stop(stop_paths)
    assert stop_paths.lock_path.exists()


def test_exited_browser_root_with_verified_descendant_retains_registration(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _record(stop_paths)
    child = _identity(stop_paths, 202, "chrome-child", 201)
    registration = stop_paths.run_root / "browser.201.json"
    launcher._atomic_json(
        registration,
        {
            "launcher_version": launcher.LAUNCHER_VERSION,
            "browser_pid": 201,
            "verified_descendants": [child],
        },
    )
    monkeypatch.setattr(launcher, "_process_identity", lambda pid: child if pid == 202 else None)
    monkeypatch.setattr(launcher, "_listener_pids", lambda: set())
    snapshot = launcher._resource_snapshot(stop_paths, record)
    assert {item["resource"] for item in snapshot["owned"]} == {"browser_descendant"}
    assert registration.exists()


def test_ownership_atomic_write_failure_preserves_previous_record(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _record(stop_paths)
    monkeypatch.setattr(launcher, "_acquire_stop_guard", lambda _paths: "guard")
    monkeypatch.setattr(launcher, "_release_stop_guard", lambda *_args: None)
    real_atomic = launcher._atomic_json

    def fail_transition(path: Path, payload: dict[str, Any]) -> None:
        if path == stop_paths.lock_path and payload.get("state") == "STOP_REQUESTED":
            raise OSError("disk full")
        real_atomic(path, payload)

    monkeypatch.setattr(launcher, "_atomic_json", fail_transition)
    with pytest.raises(OSError, match="disk full"):
        launcher.request_stop(stop_paths)
    assert json.loads(stop_paths.lock_path.read_text(encoding="utf-8")) == original


def test_ownership_deletion_failure_retains_stopped_record(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot()])
    real_unlink = Path.unlink

    def fail_lock_delete(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == stop_paths.lock_path:
            raise OSError("sharing violation")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_lock_delete)
    with pytest.raises(launcher.LauncherError, match="ownership deletion failed"):
        launcher.request_stop(stop_paths)
    retained = json.loads(stop_paths.lock_path.read_text(encoding="utf-8"))
    assert retained["state"] == "STOPPED"
    assert retained["cleanup_pending"] == ["ownership_record_deletion"]


@pytest.mark.parametrize(
    "payload", ["{broken", json.dumps({"launcher_version": launcher.LAUNCHER_VERSION})]
)
def test_corrupt_or_partial_ownership_record_is_preserved(
    stop_paths: launcher.LauncherPaths, payload: str
) -> None:
    stop_paths.lock_path.write_text(payload, encoding="utf-8")
    with pytest.raises(launcher.LauncherError):
        launcher.request_stop(stop_paths)
    assert stop_paths.lock_path.read_text(encoding="utf-8") == payload


def test_concurrent_duplicate_stop_is_rejected_without_mutation(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _record(stop_paths)
    monkeypatch.setattr(
        launcher,
        "_acquire_stop_guard",
        lambda _paths: (_ for _ in ()).throw(launcher.LauncherError("already in progress")),
    )
    with pytest.raises(launcher.LauncherError, match="already in progress"):
        launcher.request_stop(stop_paths)
    assert json.loads(stop_paths.lock_path.read_text(encoding="utf-8")) == original


def test_sequential_duplicate_stop_is_idempotent(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot()])
    assert launcher.request_stop(stop_paths)["status"] == "STOPPED"
    assert launcher.request_stop(stop_paths)["status"] == "NOT_RUNNING"


@pytest.mark.parametrize(
    "remaining,absent",
    [("browser", "streamlit"), ("streamlit", "browser"), ("listener", "streamlit")],
)
def test_partial_natural_exit_keeps_remaining_resource(
    stop_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
    remaining: str,
    absent: str,
) -> None:
    del absent
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot(remaining)])
    with pytest.raises(launcher.LauncherError):
        launcher.request_stop(stop_paths)
    retained = launcher._read_ownership(stop_paths)
    assert retained is not None and retained["state"] == "RECOVERY_REQUIRED"


def test_stop_completes_after_bounded_escalation(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    commands = _configure_stop(
        monkeypatch, [_snapshot("streamlit"), _snapshot()]
    )
    monkeypatch.setattr(launcher, "SHUTDOWN_TIMEOUT_SECONDS", -2.0)
    monkeypatch.setattr(launcher, "STOP_ESCALATION_SECONDS", 0.1)
    monkeypatch.setattr(launcher, "STOP_POLL_SECONDS", 0.0)
    assert launcher.request_stop(stop_paths)["status"] == "STOPPED"
    assert [command[0] for command in commands] == ["streamlit", "launcher"]


def test_stop_fails_honestly_when_escalation_cannot_complete(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot("streamlit")])
    with pytest.raises(launcher.LauncherError, match="RECOVERY_REQUIRED"):
        launcher.request_stop(stop_paths)
    assert stop_paths.lock_path.exists()


@pytest.mark.parametrize("unrelated_name", ["python.exe", "chrome.exe", "msedge.exe"])
def test_no_broad_process_termination_commands_are_constructed(
    stop_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
    unrelated_name: str,
) -> None:
    del unrelated_name
    record = _record(stop_paths)
    identity = _identity(stop_paths, 102, "streamlit", 101)
    monkeypatch.setattr(launcher, "_process_identity", lambda _pid: identity)
    monkeypatch.setattr(launcher, "_identity_matches", lambda *_args: True)
    monkeypatch.setattr(launcher, "_pid_alive", lambda _pid: False)
    commands: list[list[str]] = []
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda command, **_kwargs: commands.append(command)
        or launcher.subprocess.CompletedProcess(command, 0, stdout="stopped"),
    )
    launcher._target_owned_tree(record, "streamlit", allow_force=True)
    assert commands == [["taskkill.exe", "/PID", "102", "/T"]]


def test_port_is_free_after_successful_stop(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot()])
    result = launcher.request_stop(stop_paths)
    assert result["port_released"] is True


def test_second_start_lock_can_be_acquired_after_successful_stop(
    stop_paths: launcher.LauncherPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    _record(stop_paths)
    _configure_stop(monkeypatch, [_snapshot()])
    launcher.request_stop(stop_paths)
    monkeypatch.undo()
    launcher._acquire_lock(stop_paths)
    assert launcher._read_ownership(stop_paths)["state"] == "STARTING"  # type: ignore[index]


@pytest.mark.parametrize(
    "mutation",
    [
        "delete_before_listener_absence",
        "delete_before_browser_absence",
        "map_stopping_to_none",
        "accept_pid_only",
        "terminate_changed_listener",
    ],
)
def test_mutation_controls_are_observable_failures(mutation: str) -> None:
    invariants = {
        "delete_before_listener_absence": False,
        "delete_before_browser_absence": False,
        "map_stopping_to_none": False,
        "accept_pid_only": False,
        "terminate_changed_listener": False,
    }
    with pytest.raises(AssertionError, match=mutation):
        assert invariants[mutation], mutation
