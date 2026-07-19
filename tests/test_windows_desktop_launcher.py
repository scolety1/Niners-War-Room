from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.launcher import windows_desktop as launcher
from src.services.draft_day_runtime_state_service import (
    empty_runtime_state,
    load_runtime_state,
    save_runtime_state,
)


@pytest.fixture
def synthetic_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> launcher.LauncherPaths:
    monkeypatch.setenv("NWR_DATA_HOME", str(tmp_path / "profile"))
    monkeypatch.setenv("NWR_SHARED_DATA_ROOT", str(tmp_path / "missing-shared"))
    monkeypatch.delenv("NWR_DRAFT_DAY_RUNTIME_ROOT", raising=False)
    monkeypatch.delenv("NWR_DEVELOPMENT_LAB_STATE_ROOT", raising=False)
    monkeypatch.delenv("NWR_MOCK_DRAFT_ROOT", raising=False)
    monkeypatch.delenv("NWR_REFRESH_DATA_ROOT", raising=False)
    paths = launcher.launcher_paths(repo_root=Path(__file__).resolve().parents[1])
    launcher.ensure_directories(paths)
    return paths


def _save_synthetic_draft(paths: launcher.LauncherPaths, note: str) -> dict[str, object]:
    state = empty_runtime_state(mode="mock", draft_id="launcher_synthetic")
    state["notes"] = [note]
    return save_runtime_state(
        state,
        event_type="synthetic_launcher_test",
        root=paths.draft_root,
        create_backup=False,
    )


def test_state_root_environment_is_stable_outside_worktree(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    env = launcher.runtime_environment(synthetic_paths)
    assert Path(env["NWR_DATA_HOME"]) == synthetic_paths.data_home
    assert Path(env["NWR_DRAFT_DAY_RUNTIME_ROOT"]) == synthetic_paths.draft_root
    assert synthetic_paths.repo_root not in synthetic_paths.data_home.parents
    assert env["MODEL_V4_LIVE_API_ENABLED"] == "false"


def test_backup_restore_round_trip_through_draft_service(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    _save_synthetic_draft(synthetic_paths, "before")
    first = launcher.create_backup(synthetic_paths, reason="first")
    _save_synthetic_draft(synthetic_paths, "after")
    second = launcher.create_backup(synthetic_paths, reason="second")
    assert first["snapshot_id"] != second["snapshot_id"]

    plan = launcher.restore_plan(synthetic_paths, str(first["snapshot_id"]))
    assert any(row["status"] == "REPLACE" for row in plan["changes"])
    restored = launcher.restore_backup(
        synthetic_paths,
        str(first["snapshot_id"]),
        confirmation=str(first["snapshot_id"]),
    )
    assert restored["restored"] is True
    state = load_runtime_state(
        mode="mock",
        draft_id="launcher_synthetic",
        root=synthetic_paths.draft_root,
    )
    assert state["notes"] == ["before"]


def test_restore_requires_exact_confirmation(synthetic_paths: launcher.LauncherPaths) -> None:
    _save_synthetic_draft(synthetic_paths, "safe")
    backup = launcher.create_backup(synthetic_paths, reason="confirmation")
    with pytest.raises(launcher.LauncherError, match="exactly match"):
        launcher.restore_backup(
            synthetic_paths,
            str(backup["snapshot_id"]),
            confirmation="wrong",
        )


def test_corrupt_backup_is_rejected(synthetic_paths: launcher.LauncherPaths) -> None:
    _save_synthetic_draft(synthetic_paths, "safe")
    backup = launcher.create_backup(synthetic_paths, reason="corrupt")
    snapshot = synthetic_paths.backup_root / str(backup["snapshot_id"])
    payload = next((snapshot / "payload").rglob("*.json"))
    payload.write_text("{}", encoding="utf-8")
    assert launcher.validate_backup(snapshot)["valid"] is False
    with pytest.raises(launcher.LauncherError, match="Backup is invalid"):
        launcher.restore_plan(synthetic_paths, str(backup["snapshot_id"]))


def test_crash_temp_file_does_not_replace_last_valid_state(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    _save_synthetic_draft(synthetic_paths, "last-valid")
    state_path = synthetic_paths.draft_root / "state" / "launcher_synthetic__mock.json"
    original_hash = launcher.sha256(state_path)
    (state_path.parent / f".{state_path.name}.interrupted.tmp").write_text(
        '{"schema_version":', encoding="utf-8"
    )
    assert launcher.validate_state(synthetic_paths).valid is True
    assert launcher.sha256(state_path) == original_hash
    assert load_runtime_state(
        mode="mock", draft_id="launcher_synthetic", root=synthetic_paths.draft_root
    )["notes"] == ["last-valid"]


def test_worktree_replacement_retains_same_state_root(
    synthetic_paths: launcher.LauncherPaths,
    tmp_path: Path,
) -> None:
    _save_synthetic_draft(synthetic_paths, "survives-update")
    replacement = launcher.launcher_paths(repo_root=tmp_path / "replacement-worktree")
    assert replacement.data_home == synthetic_paths.data_home
    assert replacement.draft_root == synthetic_paths.draft_root
    state = load_runtime_state(
        mode="mock", draft_id="launcher_synthetic", root=replacement.draft_root
    )
    assert state["notes"] == ["survives-update"]


def test_stale_lock_with_occupied_port_fails_closed(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synthetic_paths.lock_path.write_text(
        json.dumps({"launcher_version": launcher.LAUNCHER_VERSION, "launcher_pid": 999999}),
        encoding="utf-8",
    )
    monkeypatch.setattr(launcher, "port_is_listening", lambda _host, _port: True)
    monkeypatch.setattr(launcher, "_pid_alive", lambda _pid: False)
    with pytest.raises(launcher.LauncherError, match="occupied"):
        launcher._acquire_lock(synthetic_paths)


def test_stop_never_targets_unowned_port(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(launcher, "port_is_listening", lambda _host, _port: True)
    with pytest.raises(launcher.LauncherError, match="nothing was killed"):
        launcher.request_stop(synthetic_paths)


def test_invalid_state_blocks_backup(synthetic_paths: launcher.LauncherPaths) -> None:
    state_dir = synthetic_paths.draft_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "broken.json").write_text("not-json", encoding="utf-8")
    assert launcher.validate_state(synthetic_paths).valid is False
    with pytest.raises(launcher.LauncherError, match="invalid state"):
        launcher.create_backup(synthetic_paths, reason="must-fail")


def test_invalid_legacy_receipt_blocks_migration_without_mutation(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    legacy = tmp_path / "legacy-refresh"
    legacy.mkdir()
    source = legacy / "latest_refresh_status.json"
    source.write_text("not-json", encoding="utf-8")
    before = launcher.sha256(source)
    monkeypatch.setenv("NWR_LEGACY_REFRESH_ROOT", str(legacy))
    inspected = launcher.inspect_legacy_migration(synthetic_paths)
    migrated = launcher.migrate_legacy_refresh(synthetic_paths)
    assert inspected.status == "BLOCKED_INVALID_LEGACY_STATE"
    assert migrated.status == "BLOCKED_INVALID_LEGACY_STATE"
    assert launcher.sha256(source) == before
    assert not (synthetic_paths.refresh_root / source.name).exists()


@pytest.mark.skipif(not hasattr(__import__("os").path, "isjunction"), reason="Windows only")
def test_validated_junctions_bind_repository_paths_to_stable_roots(
    synthetic_paths: launcher.LauncherPaths,
    tmp_path: Path,
) -> None:
    paths = launcher.LauncherPaths(
        **{**synthetic_paths.__dict__, "repo_root": tmp_path / "replacement"}
    )
    paths.repo_root.mkdir()
    launcher.ensure_localdata_junctions(paths)
    statuses = launcher.junction_status(paths)
    assert statuses == {"refresh_data": "VALID", "mock_drafts": "VALID"}
    assert (paths.repo_root / "local_exports" / "refresh_data").resolve() == (
        paths.refresh_root.resolve()
    )


def test_populated_non_junction_fails_closed(
    synthetic_paths: launcher.LauncherPaths,
    tmp_path: Path,
) -> None:
    paths = launcher.LauncherPaths(
        **{**synthetic_paths.__dict__, "repo_root": tmp_path / "conflict"}
    )
    conflict = paths.repo_root / "local_exports" / "refresh_data"
    conflict.mkdir(parents=True)
    (conflict / "existing.json").write_text("{}", encoding="utf-8")
    with pytest.raises(launcher.LauncherError, match="STATE_MIGRATION_CONFLICT"):
        launcher.ensure_localdata_junctions(paths)


def test_restore_oldest_at_retention_limit_and_remove_absent_state(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    _save_synthetic_draft(synthetic_paths, "original")
    oldest = launcher.create_backup(synthetic_paths, reason="retention_0")
    for index in range(1, launcher.BACKUP_RETENTION):
        _save_synthetic_draft(synthetic_paths, f"later-{index}")
        launcher.create_backup(synthetic_paths, reason=f"retention_{index}")
    extra = synthetic_paths.mock_draft_root / "extra.json"
    extra.write_text('{"schema_version": 1}\n', encoding="utf-8")

    restored = launcher.restore_backup(
        synthetic_paths,
        str(oldest["snapshot_id"]),
        confirmation=str(oldest["snapshot_id"]),
    )

    assert restored["restored"] is True
    assert not extra.exists()
    state = load_runtime_state(
        mode="mock", draft_id="launcher_synthetic", root=synthetic_paths.draft_root
    )
    assert state["notes"] == ["original"]


def test_manual_backup_requires_stopped_consistency_boundary(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    synthetic_paths.lock_path.write_text("{}", encoding="utf-8")
    with pytest.raises(launcher.LauncherError, match="requires NWR to be stopped"):
        launcher.create_manual_backup(synthetic_paths)


def test_exclusive_lock_contains_identity_before_acquire_returns(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    launcher._acquire_lock(synthetic_paths)
    record = json.loads(synthetic_paths.lock_path.read_text(encoding="utf-8"))
    assert record["state"] == "STARTING"
    assert record["launcher_pid"] > 0
    assert record["launcher_executable"]
    assert record["lock_nonce"]


def test_manual_backup_reserves_lock_for_entire_operation(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def observe_lock(_paths: launcher.LauncherPaths, **_kwargs: object) -> dict[str, str]:
        record = json.loads(synthetic_paths.lock_path.read_text(encoding="utf-8"))
        assert record["state"] == "MAINTENANCE"
        with pytest.raises(launcher.LauncherError, match="already in progress"):
            launcher._acquire_lock(synthetic_paths)
        return {"status": "OBSERVED"}

    monkeypatch.setattr(launcher, "create_backup", observe_lock)
    assert launcher.create_manual_backup(synthetic_paths) == {"status": "OBSERVED"}
    assert not synthetic_paths.lock_path.exists()


def test_empty_state_restore_failure_rolls_back_to_empty(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_synthetic_draft(synthetic_paths, "snapshot")
    backup = launcher.create_backup(synthetic_paths, reason="non_empty")
    for state_file in (synthetic_paths.draft_root / "state").glob("*.json"):
        state_file.unlink()

    original_fingerprint = launcher.state_fingerprint
    calls = 0

    def fail_once(paths: launcher.LauncherPaths) -> tuple[tuple[str, str], ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise launcher.LauncherError("injected failure")
        return original_fingerprint(paths)

    monkeypatch.setattr(launcher, "state_fingerprint", fail_once)
    snapshot_id = str(backup["snapshot_id"])
    with pytest.raises(launcher.LauncherError, match="rolled back"):
        launcher.restore_backup(
            synthetic_paths,
            snapshot_id,
            confirmation=snapshot_id,
        )

    assert list((synthetic_paths.draft_root / "state").glob("*.json")) == []
    assert not synthetic_paths.lock_path.exists()


def test_main_surfaces_readiness_runtime_error(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    surfaced: list[str] = []
    logged: list[str] = []
    monkeypatch.setattr(launcher, "launcher_paths", lambda: synthetic_paths)
    monkeypatch.setattr(
        launcher, "start", lambda _paths: (_ for _ in ()).throw(RuntimeError("not ready"))
    )
    monkeypatch.setattr(launcher, "show_error", surfaced.append)
    monkeypatch.setattr(launcher, "_append_launcher_log", lambda _paths, text: logged.append(text))

    assert launcher.main(["start"]) == 1
    assert surfaced == ["not ready"]
    assert any("not ready" in entry for entry in logged)


def test_prelaunch_backup_failure_is_logged_and_visibly_warned(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warnings: list[str] = []
    logs: list[str] = []
    monkeypatch.setattr(launcher, "verify_repository", lambda _paths: None)
    monkeypatch.setattr(launcher, "_acquire_lock", lambda _paths: None)
    monkeypatch.setattr(launcher, "port_is_listening", lambda _host, _port: False)
    monkeypatch.setattr(
        launcher,
        "migrate_legacy_refresh",
        lambda _paths: launcher.MigrationResult("NO_LEGACY_STATE"),
    )
    monkeypatch.setattr(launcher, "ensure_localdata_junctions", lambda _paths: None)
    monkeypatch.setattr(launcher, "state_fingerprint", lambda _paths: ())
    monkeypatch.setattr(
        launcher,
        "create_backup",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(launcher.LauncherError("disk full")),
    )
    monkeypatch.setattr(launcher, "show_warning", warnings.append)
    monkeypatch.setattr(launcher, "_append_launcher_log", lambda _paths, text: logs.append(text))
    monkeypatch.setattr(
        launcher,
        "find_python",
        lambda _repo: (_ for _ in ()).throw(launcher.LauncherError("stop after warning")),
    )

    with pytest.raises(launcher.LauncherError, match="stop after warning"):
        launcher.start(synthetic_paths)

    assert warnings == ["Pre-launch backup warning: disk full"]
    assert logs == ["Pre-launch backup warning: disk full"]


def test_backup_log_failure_does_not_suppress_visible_warning(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(
        launcher,
        "_append_launcher_log",
        lambda *_args: (_ for _ in ()).throw(OSError("disk remains full")),
    )
    monkeypatch.setattr(launcher, "show_warning", warnings.append)

    launcher._report_backup_warning(synthetic_paths, "Pre-launch backup warning: disk full")

    assert len(warnings) == 1
    assert "Pre-launch backup warning: disk full" in warnings[0]
    assert "Launcher log could not be written" in warnings[0]


def _write_forged_snapshot(
    paths: launcher.LauncherPaths,
    *,
    snapshot_id: str,
    family: str,
    relative: str,
    payload: str,
) -> Path:
    snapshot = paths.backup_root / snapshot_id
    target = snapshot / "payload" / family / relative
    target.parent.mkdir(parents=True)
    target.write_text(payload, encoding="utf-8")
    (snapshot / "MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "snapshot_id": snapshot_id,
                "files": [
                    {
                        "family": family,
                        "relative_path": relative,
                        "bytes": target.stat().st_size,
                        "sha256": launcher.sha256(target),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return snapshot


def test_hash_consistent_unknown_backup_family_is_rejected(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    snapshot = _write_forged_snapshot(
        synthetic_paths,
        snapshot_id="forged_unknown_family",
        family="credentials",
        relative="token.json",
        payload='{"schema_version": 1}',
    )
    result = launcher.validate_backup(snapshot)
    assert result["valid"] is False
    assert "unsupported backup family" in result["error"]


def test_hash_consistent_invalid_owner_schema_is_rejected(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    snapshot = _write_forged_snapshot(
        synthetic_paths,
        snapshot_id="forged_invalid_schema",
        family="saved_mock_drafts",
        relative="bad.json",
        payload='{"schema_version": 999}',
    )
    result = launcher.validate_backup(snapshot)
    assert result["valid"] is False
    assert "unsupported state backup schema" in result["error"]


def test_windows_rooted_relative_backup_path_is_rejected(
    synthetic_paths: launcher.LauncherPaths,
) -> None:
    snapshot = synthetic_paths.backup_root / "rooted_relative"
    snapshot.mkdir()
    (snapshot / "MANIFEST.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "snapshot_id": snapshot.name,
                "files": [
                    {
                        "family": "saved_mock_drafts",
                        "relative_path": "\\outside.json",
                        "bytes": 0,
                        "sha256": "0" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = launcher.validate_backup(snapshot)

    assert result["valid"] is False
    assert "strictly relative" in result["error"]


def test_failed_restore_removes_new_invalid_file_before_rollback(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _write_forged_snapshot(
        synthetic_paths,
        snapshot_id="forced_invalid_restore",
        family="saved_mock_drafts",
        relative="introduced.json",
        payload='{"schema_version": 999}',
    )
    monkeypatch.setattr(
        launcher,
        "validate_backup",
        lambda path: {
            "valid": True,
            "snapshot_id": path.name,
            "files": 1 if path == snapshot else 0,
        },
    )

    with pytest.raises(launcher.LauncherError, match="rolled back"):
        launcher.restore_backup(
            synthetic_paths,
            snapshot.name,
            confirmation=snapshot.name,
        )

    assert not (synthetic_paths.mock_draft_root / "introduced.json").exists()
    assert launcher.validate_state(synthetic_paths).valid is True


def test_registered_browser_cleanup_targets_only_verified_owned_tree(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    browser = tmp_path / "chrome.exe"
    browser.write_bytes(b"synthetic executable marker")
    pid = 4242
    registration = launcher._browser_registration(synthetic_paths, pid)
    launcher._atomic_json(
        registration,
        {
            "launcher_version": launcher.LAUNCHER_VERSION,
            "browser_pid": pid,
            "browser_executable": str(browser.resolve()),
            "browser_created": 123,
            "browser_profile": str(synthetic_paths.browser_profile),
            "repo_root": str(synthetic_paths.repo_root),
            "expected_browser": str(browser.resolve()),
        },
    )
    commands: list[list[str]] = []
    monkeypatch.setattr(launcher, "browser_candidates", lambda: iter((browser,)))
    monkeypatch.setattr(launcher, "_identity_matches", lambda _record, _prefix: True)
    monkeypatch.setattr(launcher, "_pid_alive", lambda _pid: False)
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda command, **_kwargs: (
            commands.append(command)
            or launcher.subprocess.CompletedProcess(command, 0, stdout="stopped")
        ),
    )

    result = launcher._shutdown_registered_browsers(synthetic_paths)

    assert commands == [["taskkill.exe", "/PID", str(pid), "/T"]]
    assert result == [
        {"pid": pid, "status": "STOPPED", "forced_cleanup": False, "initial_exit_code": 0}
    ]
    assert not registration.exists()


def test_browser_identity_failure_reaps_directly_created_process(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeProcess:
        pid = 5151

        def __init__(self) -> None:
            self.running = True
            self.terminated = False
            self.killed = False

        def poll(self) -> int | None:
            return None if self.running else 0

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, *, timeout: float) -> int:
            if not self.killed:
                raise launcher.subprocess.TimeoutExpired("browser", timeout)
            self.running = False
            return 0

        def kill(self) -> None:
            self.killed = True

    process = FakeProcess()
    monkeypatch.setattr(launcher, "_process_identity", lambda _pid: None)

    with pytest.raises(launcher.LauncherError, match="browser process identity"):
        launcher._register_browser(
            synthetic_paths,
            process,  # type: ignore[arg-type]
            tmp_path / "chrome.exe",
        )

    assert process.terminated is True
    assert process.killed is True
    assert process.running is False


def test_browser_registration_write_failure_reaps_direct_process(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeProcess:
        pid = 6161

        def __init__(self) -> None:
            self.running = True
            self.terminated = False

        def poll(self) -> int | None:
            return None if self.running else 0

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, *, timeout: float) -> int:
            del timeout
            self.running = False
            return 0

        def kill(self) -> None:
            raise AssertionError("graceful direct-process reap should have succeeded")

    process = FakeProcess()
    browser = tmp_path / "chrome.exe"
    monkeypatch.setattr(
        launcher,
        "_process_identity",
        lambda pid: {"pid": pid, "executable": str(browser), "created": 123},
    )
    monkeypatch.setattr(
        launcher,
        "_atomic_json",
        lambda *_args: (_ for _ in ()).throw(OSError("registration disk full")),
    )

    with pytest.raises(OSError, match="registration disk full"):
        launcher._register_browser(
            synthetic_paths,
            process,  # type: ignore[arg-type]
            browser,
        )

    assert process.terminated is True
    assert process.running is False


def test_malformed_browser_pid_registration_is_removed_without_targeting(
    synthetic_paths: launcher.LauncherPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registration = synthetic_paths.run_root / "browser.malformed.json"
    launcher._atomic_json(
        registration,
        {
            "launcher_version": launcher.LAUNCHER_VERSION,
            "browser_pid": "not-an-integer",
        },
    )
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("malformed registration must never target a process")
        ),
    )

    result = launcher._shutdown_registered_browsers(synthetic_paths)

    assert len(result) == 1
    assert result[0]["status"] == "INVALID_REGISTRATION_REMOVED"
    assert not registration.exists()
