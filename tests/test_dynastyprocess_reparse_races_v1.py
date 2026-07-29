from __future__ import annotations

import ctypes
import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

import src.services.dynastyprocess_generation_service as generation_service
from src.services.dynastyprocess_generation_service import (
    CURRENT_POINTER_FILENAME,
    OUTPUT_FILE_NAMES,
    GenerationResolutionError,
    PublicationError,
    expected_safe_root,
    publish_generation,
    resolve_current_generation,
)


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


def _current_marker(repo: Path, root: Path) -> str:
    snapshot = resolve_current_generation(root, repo_root=repo)
    markers = {
        body.decode().splitlines()[1].rsplit(",", 1)[-1]
        for body in snapshot.payloads.values()
    }
    assert len(markers) == 1
    return markers.pop()


def _make_junction(link: Path, target: Path) -> None:
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


class SwapAttempt:
    def __init__(self, target: Path, outside: Path) -> None:
        self.target = target
        self.outside = outside
        self.moved = target.with_name(f"{target.name}.identity-before")
        self.swap_completed = False

    def __call__(self) -> None:
        os.replace(self.target, self.moved)
        _make_junction(self.target, self.outside)
        self.swap_completed = True

    def restore(self) -> None:
        if not self.swap_completed:
            return
        os.rmdir(self.target)
        os.replace(self.moved, self.target)


@pytest.mark.parametrize(
    ("event", "target_selector", "label"),
    (
        (
            "after_initial_identity_validation",
            lambda root: root,
            "safe root after initial validation",
        ),
        (
            "after_generation_identity_validation",
            lambda root: root / "generations",
            "generations parent after validation",
        ),
        (
            "after_pointer_identity_validation",
            lambda root: root,
            "pointer parent after validation",
        ),
        (
            "after_initial_identity_validation",
            lambda root: root / ".staging",
            "staging parent reparse replacement",
        ),
        (
            "after_generation_identity_validation",
            lambda root: root.parent,
            "ancestor between generation validation and rename",
        ),
        (
            "after_pointer_identity_validation",
            lambda root: root.parent,
            "ancestor between pointer validation and commit",
        ),
    ),
)
def test_governed_directory_swap_attempts_fail_before_pointer_change(
    tmp_path: Path,
    event: str,
    target_selector,
    label: str,
) -> None:
    repo, root = _repo_and_root(tmp_path)
    old = _publish(repo, root, "old", 1)
    pointer_before = (root / CURRENT_POINTER_FILENAME).read_bytes()
    outside = tmp_path / f"outside-{old.generation_id}-{event}"
    outside.mkdir()
    swap = SwapAttempt(target_selector(root), outside)

    def inject(observed: str) -> None:
        if observed == event:
            swap()

    try:
        with pytest.raises(PublicationError):
            _publish(repo, root, "new", 2, fault_injector=inject)
    finally:
        swap.restore()

    assert (root / CURRENT_POINTER_FILENAME).read_bytes() == pointer_before, label
    assert _current_marker(repo, root) == "old"


def test_post_validation_pointer_destination_reparse_swap_fails_closed(
    tmp_path: Path,
) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    pointer = root / CURRENT_POINTER_FILENAME
    pointer_before = pointer.read_bytes()
    pointer_backup = root / "pointer-before-reparse-swap.json"
    outside = tmp_path / "pointer-reparse-target"
    outside.mkdir()
    swapped = False

    def inject(event: str) -> None:
        nonlocal swapped
        if event != "after_pointer_identity_validation":
            return
        os.replace(pointer, pointer_backup)
        _make_junction(pointer, outside)
        swapped = True

    try:
        with pytest.raises(PublicationError):
            _publish(repo, root, "new", 2, fault_injector=inject)
    finally:
        if swapped:
            os.rmdir(pointer)
            os.replace(pointer_backup, pointer)

    assert pointer.read_bytes() == pointer_before
    assert _current_marker(repo, root) == "old"


@pytest.mark.parametrize("identity_field", ("volume_serial", "file_id"))
def test_changed_volume_or_file_id_at_same_text_path_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    identity_field: str,
) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    pointer_before = (root / CURRENT_POINTER_FILENAME).read_bytes()
    original_capture = generation_service._capture_path_identity
    mutate_identity = False

    def capture(path: Path):
        observed = original_capture(path)
        if mutate_identity and path == root:
            return replace(
                observed,
                **{identity_field: getattr(observed, identity_field) + 1},
            )
        return observed

    def inject(event: str) -> None:
        nonlocal mutate_identity
        if event == "after_initial_identity_validation":
            mutate_identity = True

    monkeypatch.setattr(generation_service, "_capture_path_identity", capture)
    with pytest.raises(PublicationError):
        _publish(repo, root, "new", 2, fault_injector=inject)

    monkeypatch.setattr(
        generation_service,
        "_capture_path_identity",
        original_capture,
    )
    assert (root / CURRENT_POINTER_FILENAME).read_bytes() == pointer_before
    assert _current_marker(repo, root) == "old"


def test_case_alias_is_rejected_before_pointer_change(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    pointer_before = (root / CURRENT_POINTER_FILENAME).read_bytes()

    with pytest.raises((GenerationResolutionError, PublicationError)):
        publish_generation(
            _payloads("new"),
            safe_root=Path(str(root).swapcase()),
            repo_root=repo,
            run_id="run-2",
            generation_id="run-2-generation",
        )

    assert (root / CURRENT_POINTER_FILENAME).read_bytes() == pointer_before


def _short_path(path: Path) -> Path:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    required = kernel32.GetShortPathNameW(str(path), None, 0)
    assert required > 0, ctypes.FormatError(ctypes.get_last_error())
    buffer = ctypes.create_unicode_buffer(required + 1)
    written = kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
    assert written > 0, ctypes.FormatError(ctypes.get_last_error())
    return Path(buffer.value)


def test_short_name_alias_is_rejected_before_pointer_change(tmp_path: Path) -> None:
    assert os.name == "nt"
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    short_root = _short_path(root)
    assert str(short_root) != str(root)
    pointer_before = (root / CURRENT_POINTER_FILENAME).read_bytes()

    with pytest.raises((GenerationResolutionError, PublicationError)):
        publish_generation(
            _payloads("new"),
            safe_root=short_root,
            repo_root=repo,
            run_id="run-2",
            generation_id="run-2-generation",
        )

    assert (root / CURRENT_POINTER_FILENAME).read_bytes() == pointer_before


def test_mount_point_alias_is_rejected_before_pointer_change(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    real_root = root.with_name(f"{root.name}.real")
    os.replace(root, real_root)
    _make_junction(root, real_root)
    pointer_before = (real_root / CURRENT_POINTER_FILENAME).read_bytes()
    try:
        with pytest.raises((GenerationResolutionError, PublicationError)):
            _publish(repo, root, "new", 2)
    finally:
        os.rmdir(root)
        os.replace(real_root, root)

    assert (root / CURRENT_POINTER_FILENAME).read_bytes() == pointer_before
    assert _current_marker(repo, root) == "old"


def test_device_path_alias_is_rejected_before_pointer_change(tmp_path: Path) -> None:
    repo, root = _repo_and_root(tmp_path)
    _publish(repo, root, "old", 1)
    pointer_before = (root / CURRENT_POINTER_FILENAME).read_bytes()
    device_alias = Path("\\\\?\\" + str(root))

    with pytest.raises((GenerationResolutionError, PublicationError)):
        publish_generation(
            _payloads("new"),
            safe_root=device_alias,
            repo_root=repo,
            run_id="run-2",
            generation_id="run-2-generation",
        )

    assert (root / CURRENT_POINTER_FILENAME).read_bytes() == pointer_before
