from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.services.dynastyprocess_generation_service import (
    CURRENT_POINTER_FILENAME,
    OUTPUT_FILE_NAMES,
    GenerationResolutionError,
    PublicationCommittedError,
    PublicationError,
    PublicationState,
    expected_safe_root,
    inspect_recovery_state,
    publish_generation,
    resolve_current_generation,
)


class InjectedFailure(RuntimeError):
    pass


def _repo_and_root(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo, expected_safe_root(repo)


def _payloads(marker: str) -> dict[str, bytes]:
    return {
        name: f"file_name,marker\n{name},{marker}\n".encode()
        for name in OUTPUT_FILE_NAMES
    }


def _publish(
    repo: Path,
    root: Path,
    marker: str,
    sequence: int,
    **kwargs: object,
):
    return publish_generation(
        _payloads(marker),
        safe_root=root,
        repo_root=repo,
        run_id=f"run-{sequence}",
        generation_id=f"run-{sequence}-generation",
        **kwargs,
    )


def _assert_current_marker(repo: Path, root: Path, marker: str) -> str:
    snapshot = resolve_current_generation(root, repo_root=repo)
    assert set(snapshot.payloads) == set(OUTPUT_FILE_NAMES)
    assert all(
        f",{marker}\n".encode() in snapshot.payloads[name]
        for name in OUTPUT_FILE_NAMES
    )
    return snapshot.generation_id


PRE_POINTER_FAULTS = (
    "before_staging_creation",
    "after_staging_creation",
    *(f"after_file_write:{name}" for name in OUTPUT_FILE_NAMES),
    *(f"during_file_flush:{name}" for name in OUTPUT_FILE_NAMES),
    "before_generation_manifest_creation",
    "during_generation_manifest_write",
    "after_generation_manifest_write",
    "before_generation_rename",
    "during_generation_rename",
    "after_generation_rename_before_pointer_write",
    "during_pointer_temporary_file_write",
    "during_pointer_flush",
    "during_atomic_pointer_replacement",
)


def test_generation_publication_has_one_atomic_pointer_commit(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)

    result = _publish(repo, root, "new", 1)
    snapshot = resolve_current_generation(root, repo_root=repo)

    assert result.state == PublicationState.PUBLISHED
    assert result.pointer_path == root / CURRENT_POINTER_FILENAME
    assert snapshot.generation_id == result.generation_id
    assert set(snapshot.manifest["inventory"][0]) == {
        "bytes",
        "file_name",
        "sha256",
    }
    assert _assert_current_marker(repo, root, "new") == result.generation_id
    assert not any((root / ".staging").iterdir())


@pytest.mark.parametrize("event", PRE_POINTER_FAULTS)
def test_every_pre_pointer_fault_preserves_one_complete_old_generation(
    tmp_path: Path,
    event: str,
) -> None:
    repo, root = _repo_and_root(tmp_path)
    old = _publish(repo, root, "old", 1)
    pointer_before = (root / CURRENT_POINTER_FILENAME).read_bytes()

    def inject(observed: str) -> None:
        if observed == event:
            raise InjectedFailure(event)

    with pytest.raises(PublicationError) as caught:
        _publish(repo, root, "new", 2, fault_injector=inject)

    assert caught.value.state == PublicationState.FAILED_UNPUBLISHED
    assert (root / CURRENT_POINTER_FILENAME).read_bytes() == pointer_before
    assert _assert_current_marker(repo, root, "old") == old.generation_id


def test_crash_immediately_after_pointer_replacement_keeps_new_generation_current(
    tmp_path: Path,
) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)

    def inject(event: str) -> None:
        if event == "after_pointer_replacement":
            raise InjectedFailure(event)

    with pytest.raises(PublicationCommittedError) as caught:
        _publish(repo, root, "new", 2, fault_injector=inject)

    assert caught.value.state == PublicationState.PUBLISHED
    assert _assert_current_marker(repo, root, "new") == "run-2-generation"


@pytest.mark.parametrize(
    "event",
    ("during_old_generation_cleanup", "during_stale_staging_cleanup"),
)
def test_cleanup_failure_does_not_invalidate_publication(
    tmp_path: Path,
    event: str,
) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)

    def inject(observed: str) -> None:
        if observed == event:
            raise InjectedFailure(event)

    result = _publish(repo, root, "new", 2, fault_injector=inject)

    assert result.state == PublicationState.CLEANUP_PENDING
    assert result.cleanup_errors
    assert _assert_current_marker(repo, root, "new") == result.generation_id


def test_incomplete_staging_is_ignored_by_reader(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    old = _publish(repo, root, "old", 1)
    incomplete = root / ".staging" / "incomplete-generation"
    incomplete.mkdir()
    (incomplete / OUTPUT_FILE_NAMES[0]).write_bytes(b"partial")

    assert _assert_current_marker(repo, root, "old") == old.generation_id


def test_orphan_generation_is_identified_without_becoming_current(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    old = _publish(repo, root, "old", 1)

    def inject(event: str) -> None:
        if event == "after_generation_rename_before_pointer_write":
            raise InjectedFailure(event)

    with pytest.raises(PublicationError):
        _publish(repo, root, "orphan", 2, fault_injector=inject)

    recovery = inspect_recovery_state(root, repo_root=repo)
    assert recovery.current_generation_id == old.generation_id
    assert recovery.orphan_generation_ids == ("run-2-generation",)


def test_retry_creates_a_new_generation_without_mutating_orphan(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)

    def inject(event: str) -> None:
        if event == "after_generation_rename_before_pointer_write":
            raise InjectedFailure(event)

    with pytest.raises(PublicationError):
        _publish(repo, root, "orphan", 2, fault_injector=inject)
    orphan = root / "generations" / "run-2-generation"
    orphan_manifest_before = (orphan / "generation_manifest.json").read_bytes()

    result = _publish(repo, root, "new", 3)

    assert result.generation_id == "run-3-generation"
    assert (orphan / "generation_manifest.json").read_bytes() == orphan_manifest_before
    assert _assert_current_marker(repo, root, "new") == result.generation_id


def test_reader_fails_closed_for_missing_pointer(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    (root / CURRENT_POINTER_FILENAME).unlink()

    with pytest.raises((FileNotFoundError, GenerationResolutionError)):
        resolve_current_generation(root, repo_root=repo)


def test_reader_fails_closed_for_malformed_pointer(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    (root / CURRENT_POINTER_FILENAME).write_text("{malformed", encoding="utf-8")

    with pytest.raises(GenerationResolutionError, match="Malformed"):
        resolve_current_generation(root, repo_root=repo)


def test_reader_rejects_manifest_tampering(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    result = _publish(repo, root, "old", 1)
    result.manifest_path.write_bytes(result.manifest_path.read_bytes() + b" ")

    with pytest.raises(GenerationResolutionError, match="manifest hash"):
        resolve_current_generation(root, repo_root=repo)


def test_reader_rejects_missing_generation_file(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    result = _publish(repo, root, "old", 1)
    result.files[OUTPUT_FILE_NAMES[-1]].unlink()

    with pytest.raises((FileNotFoundError, GenerationResolutionError)):
        resolve_current_generation(root, repo_root=repo)


def test_legacy_second_replace_failure_reproduces_partial_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = tmp_path / "legacy-latest"
    staged = tmp_path / "legacy-staged"
    legacy.mkdir()
    staged.mkdir()
    for name in OUTPUT_FILE_NAMES:
        (legacy / name).write_text(f"{name},old\n", encoding="utf-8")
        (staged / name).write_text(f"{name},new\n", encoding="utf-8")

    original_replace = os.replace
    replace_calls = 0

    def fail_second_replace(source: Path, destination: Path) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("synthetic second replacement failure")
        original_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_second_replace)
    with pytest.raises(OSError, match="second replacement"):
        for name in OUTPUT_FILE_NAMES:
            os.replace(staged / name, legacy / name)

    current_markers = {
        name: (legacy / name).read_text(encoding="utf-8").split(",")[-1].strip()
        for name in OUTPUT_FILE_NAMES
    }
    assert list(current_markers.values()).count("new") == 1
    assert list(current_markers.values()).count("old") == 4


def test_second_legacy_replace_is_not_a_transactional_commit_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    replace_calls = 0

    def forbidden_legacy_replace(*_args: object, **_kwargs: object) -> None:
        nonlocal replace_calls
        replace_calls += 1
        raise OSError("legacy replacement unexpectedly called")

    monkeypatch.setattr(os, "replace", forbidden_legacy_replace)

    def inject(event: str) -> None:
        if event == "during_atomic_pointer_replacement":
            raise InjectedFailure("candidate pointer replacement failed")

    with pytest.raises(PublicationError):
        _publish(repo, root, "new", 2, fault_injector=inject)

    assert replace_calls == 0
    assert _assert_current_marker(repo, root, "old") == "run-1-generation"
