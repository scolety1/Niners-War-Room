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

    monkeypatch.setattr(
        launcher,
        "state_fingerprint",
        lambda _paths: (_ for _ in ()).throw(launcher.LauncherError("injected failure")),
    )
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
