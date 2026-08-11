"""Transactional publication for the five DynastyProcess refresh artifacts.

The authoritative commit point is ``current_generation.json``.  Every pointer
target is an immutable, complete generation whose manifest and five payloads
are verified before it can become current.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import stat
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

OUTPUT_FILE_NAMES = (
    "dp_freshness_report.csv",
    "dp_market_baseline_context.csv",
    "dp_nwr_join_coverage.csv",
    "dp_pick_value_context.csv",
    "dp_playerid_crosswalk_audit.csv",
)
OUTPUT_FILE_SET = frozenset(OUTPUT_FILE_NAMES)
CURRENT_POINTER_FILENAME = "current_generation.json"
GENERATION_MANIFEST_FILENAME = "generation_manifest.json"
GENERATION_MANIFEST_SCHEMA = "nwr-dynastyprocess-generation-manifest-v1"
CURRENT_POINTER_SCHEMA = "nwr-dynastyprocess-current-generation-pointer-v1"
OUTPUT_SCHEMA_VERSION = "nwr-dynastyprocess-market-baseline-v1"

_SAFE_ROOT_PARTS = (
    "local_exports",
    "refresh_data",
    "dynastyprocess_market_baseline",
)
_GENERATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_DEVICE_PREFIXES = ("\\\\?\\", "\\\\.\\", "\\??\\", "\\device\\")
_FILE_ATTRIBUTE_DIRECTORY = 0x10
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400

FaultInjector = Callable[[str], None]


class PublicationState(StrEnum):
    STAGING = "STAGING"
    STAGED_COMPLETE = "STAGED_COMPLETE"
    GENERATION_IMMUTABLE = "GENERATION_IMMUTABLE"
    COMMITTING_POINTER = "COMMITTING_POINTER"
    PUBLISHED = "PUBLISHED"
    CLEANUP_PENDING = "CLEANUP_PENDING"
    FAILED_UNPUBLISHED = "FAILED_UNPUBLISHED"


class GenerationResolutionError(ValueError):
    """The current pointer or referenced generation is not trustworthy."""


class PublicationError(RuntimeError):
    """Publication failed before its pointer became authoritative."""

    def __init__(self, message: str, *, state: PublicationState) -> None:
        super().__init__(message)
        self.state = state


class PublicationCommittedError(PublicationError):
    """A simulated crash occurred after the pointer commit completed."""


@dataclass(frozen=True)
class PathIdentity:
    requested_path: Path
    final_path: str
    volume_serial: int
    file_id: int
    file_attributes: int

    @property
    def is_reparse_point(self) -> bool:
        return bool(self.file_attributes & _FILE_ATTRIBUTE_REPARSE_POINT)


@dataclass(frozen=True)
class GenerationSnapshot:
    generation_id: str
    pointer: Mapping[str, Any]
    manifest: Mapping[str, Any]
    files: Mapping[str, Path]
    payloads: Mapping[str, bytes]


@dataclass(frozen=True)
class PublicationResult:
    run_id: str
    generation_id: str
    state: PublicationState
    pointer_path: Path
    manifest_path: Path
    files: Mapping[str, Path]
    cleanup_errors: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryInventory:
    current_generation_id: str
    orphan_generation_ids: tuple[str, ...]
    stale_staging_ids: tuple[str, ...]


def expected_safe_root(repo_root: Path) -> Path:
    return Path(repo_root).joinpath(*_SAFE_ROOT_PARTS)


def make_generation_id(run_id: str | None = None) -> str:
    normalized_run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    if not _GENERATION_ID_RE.fullmatch(normalized_run_id):
        raise ValueError(f"Invalid run ID: {normalized_run_id!r}")
    return f"{normalized_run_id}-{uuid.uuid4().hex}"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def _path_text(path: Path) -> str:
    return os.path.normpath(os.path.abspath(os.fspath(path)))


def _strip_extended_prefix(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def _same_exact_path(left: str | Path, right: str | Path) -> bool:
    return _path_text(Path(left)) == _path_text(Path(right))


def _validate_requested_safe_root(
    safe_root: Path,
    repo_root: Path,
    *,
    expected_root: Path | None = None,
) -> Path:
    raw = os.fspath(safe_root)
    lowered = raw.casefold()
    if any(lowered.startswith(prefix) for prefix in _DEVICE_PREFIXES):
        raise GenerationResolutionError("Device and extended-length path aliases are rejected.")
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise GenerationResolutionError("The safe refresh root must be absolute.")
    if ".." in candidate.parts or "." in candidate.parts:
        raise GenerationResolutionError("Traversal aliases are rejected.")
    expected = expected_root or expected_safe_root(Path(repo_root))
    if not Path(expected).is_absolute():
        raise GenerationResolutionError("The trusted refresh root must be absolute.")
    if not _same_exact_path(candidate, expected):
        raise GenerationResolutionError(
            f"Safe root must use the canonical path spelling: {expected}"
        )
    return Path(_path_text(candidate))


if os.name == "nt":
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _GENERIC_READ = 0x80000000
    _DELETE = 0x00010000
    _SYNCHRONIZE = 0x00100000
    _FILE_LIST_DIRECTORY = 0x0001
    _FILE_READ_ATTRIBUTES = 0x0080
    _FILE_SHARE_READ = 0x00000001
    _FILE_SHARE_WRITE = 0x00000002
    _FILE_SHARE_DELETE = 0x00000004
    _OPEN_EXISTING = 3
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000
    _FILE_RENAME_INFO_CLASS = 3
    _FILE_RENAME_INFORMATION_CLASS = 10

    class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    _kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION),
    ]
    _kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    _kernel32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    _kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    _kernel32.ReadFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    _kernel32.ReadFile.restype = wintypes.BOOL
    _kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    _kernel32.FlushFileBuffers.restype = wintypes.BOOL
    _kernel32.SetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    _kernel32.SetFileInformationByHandle.restype = wintypes.BOOL

    class _IO_STATUS_UNION(ctypes.Union):
        _fields_ = [
            ("Status", wintypes.LONG),
            ("Pointer", wintypes.LPVOID),
        ]

    class _IO_STATUS_BLOCK(ctypes.Structure):
        _anonymous_ = ("result",)
        _fields_ = [
            ("result", _IO_STATUS_UNION),
            ("Information", ctypes.c_size_t),
        ]

    _ntdll.NtSetInformationFile.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_IO_STATUS_BLOCK),
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.c_int,
    ]
    _ntdll.NtSetInformationFile.restype = wintypes.LONG
    _ntdll.RtlNtStatusToDosError.argtypes = [wintypes.LONG]
    _ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG


def _raise_last_windows_error(context: str) -> None:
    error = ctypes.get_last_error()
    raise OSError(error, f"{context}: {ctypes.FormatError(error).strip()}")


def _native_open(
    path: Path,
    *,
    access: int,
    directory: bool,
    share_delete: bool,
) -> int:
    share = _FILE_SHARE_READ | _FILE_SHARE_WRITE
    if share_delete:
        share |= _FILE_SHARE_DELETE
    flags = _FILE_FLAG_OPEN_REPARSE_POINT
    if directory:
        flags |= _FILE_FLAG_BACKUP_SEMANTICS
    else:
        flags |= _FILE_FLAG_SEQUENTIAL_SCAN
    handle = _kernel32.CreateFileW(
        os.fspath(path),
        access,
        share,
        None,
        _OPEN_EXISTING,
        flags,
        None,
    )
    if handle == _INVALID_HANDLE_VALUE:
        _raise_last_windows_error(f"Cannot open governed path {path}")
    return int(handle)


def _native_identity(handle: int, requested_path: Path) -> PathIdentity:
    information = _BY_HANDLE_FILE_INFORMATION()
    if not _kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        _raise_last_windows_error(f"Cannot identify governed path {requested_path}")
    required = _kernel32.GetFinalPathNameByHandleW(handle, None, 0, 0)
    if required == 0:
        _raise_last_windows_error(f"Cannot normalize governed path {requested_path}")
    buffer = ctypes.create_unicode_buffer(required + 1)
    written = _kernel32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    if written == 0 or written >= len(buffer):
        _raise_last_windows_error(f"Cannot normalize governed path {requested_path}")
    return PathIdentity(
        requested_path=requested_path,
        final_path=_path_text(Path(_strip_extended_prefix(buffer.value))),
        volume_serial=int(information.dwVolumeSerialNumber),
        file_id=(int(information.nFileIndexHigh) << 32)
        | int(information.nFileIndexLow),
        file_attributes=int(information.dwFileAttributes),
    )


class _DirectoryHandle:
    def __init__(self, path: Path, *, share_delete: bool = False) -> None:
        self.path = path
        self._closed = False
        if os.name == "nt":
            self.raw = _native_open(
                path,
                access=_FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                directory=True,
                share_delete=share_delete,
            )
            self.identity = _native_identity(self.raw, path)
        else:
            flags = os.O_RDONLY
            flags |= getattr(os, "O_DIRECTORY", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            self.raw = os.open(path, flags)
            metadata = os.fstat(self.raw)
            self.identity = PathIdentity(
                requested_path=path,
                final_path=_path_text(path),
                volume_serial=int(metadata.st_dev),
                file_id=int(metadata.st_ino),
                file_attributes=(
                    _FILE_ATTRIBUTE_DIRECTORY
                    | (
                        _FILE_ATTRIBUTE_REPARSE_POINT
                        if stat.S_ISLNK(metadata.st_mode)
                        else 0
                    )
                ),
            )
        if not self.identity.file_attributes & _FILE_ATTRIBUTE_DIRECTORY:
            self.close()
            raise GenerationResolutionError(f"Governed directory is not a directory: {path}")
        if self.identity.is_reparse_point:
            self.close()
            raise GenerationResolutionError(f"Reparse point rejected: {path}")
        if not _same_exact_path(self.identity.final_path, path):
            self.close()
            raise GenerationResolutionError(
                f"Alias path rejected for {path}; handle resolved to {self.identity.final_path}"
            )

    def flush_metadata(self) -> None:
        if os.name == "nt":
            if not _kernel32.FlushFileBuffers(self.raw):
                error = ctypes.get_last_error()
                if error not in {1, 5, 6, 50}:
                    _raise_last_windows_error(f"Cannot flush directory metadata {self.path}")
        else:
            os.fsync(self.raw)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if os.name == "nt":
            _kernel32.CloseHandle(self.raw)
        else:
            os.close(self.raw)

    def __enter__(self) -> _DirectoryHandle:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def _capture_path_identity(path: Path) -> PathIdentity:
    with _DirectoryHandle(path, share_delete=True) as handle:
        return handle.identity


class _AuthenticatedLayout:
    def __init__(self, handles: list[_DirectoryHandle]) -> None:
        self.handles = handles
        self.by_path = {_path_text(handle.path): handle for handle in handles}
        self._original = {
            key: handle.identity for key, handle in self.by_path.items()
        }

    def handle_for(self, path: Path) -> _DirectoryHandle:
        try:
            return self.by_path[_path_text(path)]
        except KeyError as exc:
            raise GenerationResolutionError(f"Directory is not authenticated: {path}") from exc

    def revalidate(self) -> None:
        for expected in self._original.values():
            observed = _capture_path_identity(expected.requested_path)
            if (
                observed.final_path != expected.final_path
                or observed.volume_serial != expected.volume_serial
                or observed.file_id != expected.file_id
                or observed.is_reparse_point
            ):
                raise GenerationResolutionError(
                    f"Governed directory identity changed: {expected.requested_path}"
                )

    def close(self) -> None:
        for handle in reversed(self.handles):
            handle.close()

    def __enter__(self) -> _AuthenticatedLayout:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def _path_chain(path: Path) -> tuple[Path, ...]:
    absolute = Path(_path_text(path))
    anchor = Path(absolute.anchor)
    chain = [anchor]
    current = anchor
    for part in absolute.parts[1:]:
        current = current / part
        chain.append(current)
    return tuple(chain)


def _authenticate_layout(
    safe_root: Path,
    repo_root: Path,
    *,
    create: bool,
    include_staging: bool,
    expected_root: Path | None = None,
    required_children: tuple[str, ...] | None = None,
) -> _AuthenticatedLayout:
    root = _validate_requested_safe_root(
        safe_root,
        repo_root,
        expected_root=expected_root,
    )
    repo = Path(_path_text(repo_root))
    if not repo.is_dir():
        raise GenerationResolutionError(f"Repository root is missing: {repo}")
    handles: list[_DirectoryHandle] = []
    volume_serial: int | None = None
    try:
        for component in _path_chain(root):
            if not component.exists():
                if not create:
                    raise GenerationResolutionError(
                        f"Safe publication directory is missing: {component}"
                    )
                try:
                    component.relative_to(repo)
                except ValueError as exc:
                    raise GenerationResolutionError(
                        f"Refusing to create a directory outside the repository: {component}"
                    ) from exc
                component.mkdir()
            handle = _DirectoryHandle(component)
            if volume_serial is None:
                volume_serial = handle.identity.volume_serial
            elif handle.identity.volume_serial != volume_serial:
                handle.close()
                raise GenerationResolutionError(
                    f"Volume transition or mount point rejected: {component}"
                )
            handles.append(handle)

        child_names = list(required_children or ("generations",))
        if include_staging and ".staging" not in child_names:
            child_names.insert(0, ".staging")
        for name in child_names:
            child = root / name
            if not child.exists():
                if not create:
                    raise GenerationResolutionError(
                        f"Publication directory is missing: {child}"
                    )
                child.mkdir()
            handle = _DirectoryHandle(child)
            if handle.identity.volume_serial != volume_serial:
                handle.close()
                raise GenerationResolutionError(
                    f"Volume transition or mount point rejected: {child}"
                )
            handles.append(handle)
        return _AuthenticatedLayout(handles)
    except Exception:
        for handle in reversed(handles):
            handle.close()
        raise


def _read_file_no_reparse(path: Path) -> bytes:
    if os.name == "nt":
        handle = _native_open(
            path,
            access=_GENERIC_READ | _FILE_READ_ATTRIBUTES,
            directory=False,
            share_delete=True,
        )
        try:
            identity = _native_identity(handle, path)
            if identity.is_reparse_point:
                raise GenerationResolutionError(f"Reparse-point file rejected: {path}")
            if identity.file_attributes & _FILE_ATTRIBUTE_DIRECTORY:
                raise GenerationResolutionError(f"Expected a regular file: {path}")
            chunks: list[bytes] = []
            while True:
                buffer = ctypes.create_string_buffer(1024 * 1024)
                read = wintypes.DWORD()
                if not _kernel32.ReadFile(
                    handle,
                    buffer,
                    len(buffer),
                    ctypes.byref(read),
                    None,
                ):
                    _raise_last_windows_error(f"Cannot read governed file {path}")
                if read.value == 0:
                    break
                chunks.append(buffer.raw[: read.value])
            return b"".join(chunks)
        finally:
            _kernel32.CloseHandle(handle)

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise GenerationResolutionError(f"Expected a regular file: {path}")
        chunks = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _decode_json_object(body: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenerationResolutionError(f"Malformed {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise GenerationResolutionError(f"Malformed {label}: expected a JSON object.")
    return value


def _validate_generation_id(value: object) -> str:
    generation_id = str(value)
    if not _GENERATION_ID_RE.fullmatch(generation_id):
        raise GenerationResolutionError("Pointer contains an unsafe generation ID.")
    return generation_id


def _load_generation(
    *,
    root: Path,
    generation_id: str,
    expected_manifest_hash: str,
    layout: _AuthenticatedLayout,
    pointer: Mapping[str, Any],
) -> GenerationSnapshot:
    generation_path = root / "generations" / generation_id
    generation_handle = _DirectoryHandle(generation_path)
    try:
        root_identity = layout.handle_for(root).identity
        if generation_handle.identity.volume_serial != root_identity.volume_serial:
            raise GenerationResolutionError("Generation volume identity does not match safe root.")
        layout.revalidate()
        manifest_path = generation_path / GENERATION_MANIFEST_FILENAME
        manifest_body = _read_file_no_reparse(manifest_path)
        actual_manifest_hash = hashlib.sha256(manifest_body).hexdigest()
        if actual_manifest_hash != expected_manifest_hash:
            raise GenerationResolutionError("Generation manifest hash does not match pointer.")
        manifest = _decode_json_object(manifest_body, label="generation manifest")
        if manifest.get("schema_version") != GENERATION_MANIFEST_SCHEMA:
            raise GenerationResolutionError("Unsupported generation manifest schema.")
        if manifest.get("output_schema_version") != OUTPUT_SCHEMA_VERSION:
            raise GenerationResolutionError("Unsupported DynastyProcess output schema.")
        if manifest.get("completion_status") != PublicationState.STAGED_COMPLETE:
            raise GenerationResolutionError("Generation manifest is not complete.")
        if manifest.get("generation_id") != generation_id:
            raise GenerationResolutionError("Generation manifest identity mismatch.")
        if manifest.get("expected_file_count") != len(OUTPUT_FILE_NAMES):
            raise GenerationResolutionError("Generation manifest file count is invalid.")
        inventory = manifest.get("inventory")
        if not isinstance(inventory, list):
            raise GenerationResolutionError("Generation inventory is malformed.")
        by_name: dict[str, Mapping[str, Any]] = {}
        for item in inventory:
            if not isinstance(item, dict):
                raise GenerationResolutionError("Generation inventory entry is malformed.")
            name = str(item.get("file_name", ""))
            if name in by_name:
                raise GenerationResolutionError(f"Duplicate generation inventory entry: {name}")
            by_name[name] = item
        if frozenset(by_name) != OUTPUT_FILE_SET:
            raise GenerationResolutionError("Generation does not contain the exact five files.")

        payloads: dict[str, bytes] = {}
        files: dict[str, Path] = {}
        for name in OUTPUT_FILE_NAMES:
            item = by_name[name]
            expected_hash = str(item.get("sha256", ""))
            expected_size = item.get("bytes")
            if not _SHA256_RE.fullmatch(expected_hash) or not isinstance(
                expected_size, int
            ):
                raise GenerationResolutionError(f"Invalid manifest metadata for {name}.")
            path = generation_path / name
            body = _read_file_no_reparse(path)
            if len(body) != expected_size:
                raise GenerationResolutionError(f"Generation size mismatch for {name}.")
            if hashlib.sha256(body).hexdigest() != expected_hash:
                raise GenerationResolutionError(f"Generation hash mismatch for {name}.")
            files[name] = path
            payloads[name] = body
        layout.revalidate()
        return GenerationSnapshot(
            generation_id=generation_id,
            pointer=MappingProxyType(dict(pointer)),
            manifest=MappingProxyType(manifest),
            files=MappingProxyType(files),
            payloads=MappingProxyType(payloads),
        )
    finally:
        generation_handle.close()


def _resolve_with_layout(root: Path, layout: _AuthenticatedLayout) -> GenerationSnapshot:
    pointer_path = root / CURRENT_POINTER_FILENAME
    pointer_body = _read_file_no_reparse(pointer_path)
    pointer = _decode_json_object(pointer_body, label="current-generation pointer")
    if pointer.get("schema_version") != CURRENT_POINTER_SCHEMA:
        raise GenerationResolutionError("Unsupported current-generation pointer schema.")
    if pointer.get("publication_state") != PublicationState.PUBLISHED:
        raise GenerationResolutionError("Current-generation pointer is not published.")
    if pointer.get("manifest_file") != GENERATION_MANIFEST_FILENAME:
        raise GenerationResolutionError("Current-generation manifest name is invalid.")
    generation_id = _validate_generation_id(pointer.get("generation_id"))
    manifest_hash = str(pointer.get("manifest_sha256", ""))
    if not _SHA256_RE.fullmatch(manifest_hash):
        raise GenerationResolutionError("Current-generation manifest hash is invalid.")
    layout.revalidate()
    return _load_generation(
        root=root,
        generation_id=generation_id,
        expected_manifest_hash=manifest_hash,
        layout=layout,
        pointer=pointer,
    )


def resolve_current_generation(
    safe_root: Path,
    *,
    repo_root: Path,
    trusted_runtime_root: Path | None = None,
) -> GenerationSnapshot:
    root = _validate_requested_safe_root(
        safe_root,
        repo_root,
        expected_root=trusted_runtime_root,
    )
    with _authenticate_layout(
        root,
        repo_root,
        create=False,
        include_staging=False,
        expected_root=trusted_runtime_root,
    ) as layout:
        return _resolve_with_layout(root, layout)


def resolve_legacy_latest_snapshot(
    safe_root: Path,
    *,
    repo_root: Path,
    trusted_runtime_root: Path,
) -> GenerationSnapshot:
    """Read the complete pre-generation ``latest`` bundle through the same path guards.

    This compatibility reader exists only for display consumers while launcher-owned data is
    migrated to transactional generations. It never publishes, mutates, or treats the bundle as
    current merely because the directory is named ``latest``.
    """

    root = _validate_requested_safe_root(
        safe_root,
        repo_root,
        expected_root=trusted_runtime_root,
    )
    with _authenticate_layout(
        root,
        repo_root,
        create=False,
        include_staging=False,
        expected_root=trusted_runtime_root,
        required_children=("latest",),
    ) as layout:
        payloads: dict[str, bytes] = {}
        files: dict[str, Path] = {}
        hashes: dict[str, str] = {}
        for name in OUTPUT_FILE_NAMES:
            path = root / "latest" / name
            body = _read_file_no_reparse(path)
            payloads[name] = body
            files[name] = path
            hashes[name] = hashlib.sha256(body).hexdigest()
        layout.revalidate()
        generation_id = f"legacy-latest-{hashes['dp_freshness_report.csv'][:12]}"
        return GenerationSnapshot(
            generation_id=generation_id,
            pointer=MappingProxyType(
                {
                    "schema_version": "nwr-legacy-latest-compat-v1",
                    "publication_state": "LEGACY_DISPLAY_ONLY",
                    "generation_id": generation_id,
                }
            ),
            manifest=MappingProxyType(
                {
                    "schema_version": "nwr-legacy-latest-compat-v1",
                    "files": hashes,
                }
            ),
            files=MappingProxyType(files),
            payloads=MappingProxyType(payloads),
        )


def _durable_write(
    path: Path,
    body: bytes,
    *,
    during_write_event: str,
    during_flush_event: str,
    inject: FaultInjector,
) -> None:
    midpoint = max(1, len(body) // 2)
    with path.open("xb") as handle:
        handle.write(body[:midpoint])
        inject(during_write_event)
        handle.write(body[midpoint:])
        inject(during_flush_event)
        handle.flush()
        os.fsync(handle.fileno())


def _native_rename_to_parent(
    source: Path,
    *,
    expected_source_identity: PathIdentity,
    target_parent: _DirectoryHandle,
    target_name: str,
    replace: bool,
) -> None:
    if "/" in target_name or "\\" in target_name or target_name in {"", ".", ".."}:
        raise PublicationError(
            f"Unsafe relative rename target: {target_name!r}",
            state=PublicationState.FAILED_UNPUBLISHED,
        )
    if os.name != "nt":
        operation = os.replace if replace else os.rename
        operation(
            source.name,
            target_name,
            src_dir_fd=os.open(source.parent, os.O_RDONLY),
            dst_dir_fd=target_parent.raw,
        )
        return

    source_is_directory = bool(
        expected_source_identity.file_attributes & _FILE_ATTRIBUTE_DIRECTORY
    )
    source_handle = _native_open(
        source,
        access=_DELETE | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
        directory=source_is_directory,
        share_delete=True,
    )
    try:
        observed = _native_identity(source_handle, source)
        if (
            observed.final_path != expected_source_identity.final_path
            or observed.volume_serial != expected_source_identity.volume_serial
            or observed.file_id != expected_source_identity.file_id
            or observed.is_reparse_point
        ):
            raise GenerationResolutionError(f"Rename source identity changed: {source}")

        file_name_type = wintypes.WCHAR * (len(target_name) + 1)

        class _FILE_RENAME_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("ReplaceUnion", wintypes.ULONG),
                ("RootDirectory", wintypes.HANDLE),
                ("FileNameLength", wintypes.DWORD),
                ("FileName", file_name_type),
            ]

        information = _FILE_RENAME_INFORMATION()
        information.ReplaceUnion = 1 if replace else 0
        information.RootDirectory = target_parent.raw
        information.FileNameLength = len(target_name.encode("utf-16-le"))
        information.FileName = target_name
        io_status = _IO_STATUS_BLOCK()
        status = _ntdll.NtSetInformationFile(
            source_handle,
            ctypes.byref(io_status),
            ctypes.byref(information),
            ctypes.sizeof(information),
            _FILE_RENAME_INFORMATION_CLASS,
        )
        if status < 0:
            error = int(_ntdll.RtlNtStatusToDosError(status))
            raise OSError(
                error,
                f"Atomic handle-bound rename failed for {source}: "
                f"{ctypes.FormatError(error).strip()}",
            )
    finally:
        _kernel32.CloseHandle(source_handle)


def _manifest_document(
    *,
    run_id: str,
    generation_id: str,
    payloads: Mapping[str, bytes],
    created_at_utc: str,
) -> dict[str, Any]:
    return {
        "schema_version": GENERATION_MANIFEST_SCHEMA,
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "run_id": run_id,
        "generation_id": generation_id,
        "created_at_utc": created_at_utc,
        "completion_status": PublicationState.STAGED_COMPLETE,
        "expected_file_count": len(OUTPUT_FILE_NAMES),
        "inventory": [
            {
                "file_name": name,
                "bytes": len(payloads[name]),
                "sha256": hashlib.sha256(payloads[name]).hexdigest(),
            }
            for name in sorted(OUTPUT_FILE_NAMES)
        ],
        "state_history": [
            PublicationState.STAGING,
            PublicationState.STAGED_COMPLETE,
        ],
    }


def _pointer_document(
    *,
    generation_id: str,
    manifest_hash: str,
    published_at_utc: str,
) -> dict[str, Any]:
    return {
        "schema_version": CURRENT_POINTER_SCHEMA,
        "generation_id": generation_id,
        "manifest_file": GENERATION_MANIFEST_FILENAME,
        "manifest_sha256": manifest_hash,
        "publication_state": PublicationState.PUBLISHED,
        "published_at_utc": published_at_utc,
    }


def _identity_for_regular_file(path: Path) -> PathIdentity:
    if os.name == "nt":
        handle = _native_open(
            path,
            access=_FILE_READ_ATTRIBUTES,
            directory=False,
            share_delete=True,
        )
        try:
            identity = _native_identity(handle, path)
        finally:
            _kernel32.CloseHandle(handle)
        if identity.is_reparse_point or identity.file_attributes & _FILE_ATTRIBUTE_DIRECTORY:
            raise GenerationResolutionError(f"Expected a non-reparse regular file: {path}")
        return identity
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise GenerationResolutionError(f"Expected a regular file: {path}")
    return PathIdentity(
        requested_path=path,
        final_path=_path_text(path),
        volume_serial=int(metadata.st_dev),
        file_id=int(metadata.st_ino),
        file_attributes=0,
    )


def publish_generation(
    payloads: Mapping[str, bytes],
    *,
    safe_root: Path,
    repo_root: Path,
    run_id: str | None = None,
    generation_id: str | None = None,
    fault_injector: FaultInjector | None = None,
    retention_count: int = 3,
    stale_staging_seconds: int = 86_400,
) -> PublicationResult:
    """Publish one exact five-file generation through one pointer replacement."""

    if frozenset(payloads) != OUTPUT_FILE_SET:
        raise PublicationError(
            "Publisher requires the exact five-file inventory.",
            state=PublicationState.FAILED_UNPUBLISHED,
        )
    normalized_payloads: dict[str, bytes] = {}
    for name in OUTPUT_FILE_NAMES:
        body = payloads[name]
        if not isinstance(body, bytes) or not body:
            raise PublicationError(
                f"Generation payload must be non-empty bytes: {name}",
                state=PublicationState.FAILED_UNPUBLISHED,
            )
        normalized_payloads[name] = body
    if retention_count < 1:
        raise ValueError("retention_count must retain at least the current generation.")

    root = _validate_requested_safe_root(safe_root, repo_root)
    effective_run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    if not _GENERATION_ID_RE.fullmatch(effective_run_id):
        raise ValueError(f"Invalid run ID: {effective_run_id!r}")
    effective_generation_id = generation_id or make_generation_id(effective_run_id)
    if not _GENERATION_ID_RE.fullmatch(effective_generation_id):
        raise ValueError(f"Invalid generation ID: {effective_generation_id!r}")
    if effective_generation_id == effective_run_id:
        raise ValueError("Generation ID must be unique from the run ID.")

    state = PublicationState.STAGING
    inject = fault_injector or (lambda _event: None)
    pointer_path = root / CURRENT_POINTER_FILENAME
    staging_path = root / ".staging" / effective_generation_id
    generation_path = root / "generations" / effective_generation_id
    cleanup_errors: list[str] = []
    pointer_committed = False

    try:
        with _authenticate_layout(
            root,
            repo_root,
            create=True,
            include_staging=True,
        ) as layout:
            inject("after_initial_identity_validation")
            layout.revalidate()

            if pointer_path.exists() or pointer_path.is_symlink():
                _resolve_with_layout(root, layout)

            inject("before_staging_creation")
            staging_path.mkdir()
            state = PublicationState.STAGING
            inject("after_staging_creation")

            with _DirectoryHandle(staging_path) as staging_guard:
                for name in OUTPUT_FILE_NAMES:
                    path = staging_path / name
                    _durable_write(
                        path,
                        normalized_payloads[name],
                        during_write_event=f"during_file_write:{name}",
                        during_flush_event=f"during_file_flush:{name}",
                        inject=inject,
                    )
                    inject(f"after_file_write:{name}")
                inject("before_generation_manifest_creation")
                manifest = _manifest_document(
                    run_id=effective_run_id,
                    generation_id=effective_generation_id,
                    payloads=normalized_payloads,
                    created_at_utc=_utc_now(),
                )
                manifest_body = _json_bytes(manifest)
                manifest_staging_path = staging_path / GENERATION_MANIFEST_FILENAME
                _durable_write(
                    manifest_staging_path,
                    manifest_body,
                    during_write_event="during_generation_manifest_write",
                    during_flush_event="during_generation_manifest_flush",
                    inject=inject,
                )
                inject("after_generation_manifest_write")
                staging_guard.flush_metadata()
                state = PublicationState.STAGED_COMPLETE
                inject("before_generation_rename")
                layout.revalidate()
                observed_staging = _capture_path_identity(staging_path)
                if observed_staging != staging_guard.identity:
                    raise GenerationResolutionError("Staging directory identity changed.")
                inject("after_generation_identity_validation")
                layout.revalidate()

            inject("during_generation_rename")
            _native_rename_to_parent(
                staging_path,
                expected_source_identity=staging_guard.identity,
                target_parent=layout.handle_for(root / "generations"),
                target_name=effective_generation_id,
                replace=False,
            )
            state = PublicationState.GENERATION_IMMUTABLE
            layout.revalidate()
            inject("after_generation_rename_before_pointer_write")

            expected_manifest_hash = hashlib.sha256(manifest_body).hexdigest()
            candidate = _load_generation(
                root=root,
                generation_id=effective_generation_id,
                expected_manifest_hash=expected_manifest_hash,
                layout=layout,
                pointer={},
            )
            if dict(candidate.payloads) != normalized_payloads:
                raise GenerationResolutionError("Candidate generation payload verification failed.")

            pointer = _pointer_document(
                generation_id=effective_generation_id,
                manifest_hash=expected_manifest_hash,
                published_at_utc=_utc_now(),
            )
            pointer_body = _json_bytes(pointer)
            pointer_temp = root / f".{CURRENT_POINTER_FILENAME}.{uuid.uuid4().hex}.tmp"
            _durable_write(
                pointer_temp,
                pointer_body,
                during_write_event="during_pointer_temporary_file_write",
                during_flush_event="during_pointer_flush",
                inject=inject,
            )
            pointer_temp_identity = _identity_for_regular_file(pointer_temp)
            layout.handle_for(root).flush_metadata()
            state = PublicationState.COMMITTING_POINTER
            layout.revalidate()
            if pointer_path.exists() or pointer_path.is_symlink():
                _read_file_no_reparse(pointer_path)
            inject("after_pointer_identity_validation")
            layout.revalidate()
            if pointer_path.exists() or pointer_path.is_symlink():
                _read_file_no_reparse(pointer_path)
            inject("during_atomic_pointer_replacement")
            layout.revalidate()
            if pointer_path.exists() or pointer_path.is_symlink():
                _read_file_no_reparse(pointer_path)
            _native_rename_to_parent(
                pointer_temp,
                expected_source_identity=pointer_temp_identity,
                target_parent=layout.handle_for(root),
                target_name=CURRENT_POINTER_FILENAME,
                replace=True,
            )
            pointer_committed = True
            state = PublicationState.PUBLISHED
            layout.handle_for(root).flush_metadata()
            committed = _resolve_with_layout(root, layout)
            if committed.generation_id != effective_generation_id:
                raise GenerationResolutionError("Pointer readback selected the wrong generation.")
            inject("after_pointer_replacement")

            try:
                inject("during_old_generation_cleanup")
                _cleanup_old_generations(
                    root,
                    current_generation_id=effective_generation_id,
                    retention_count=retention_count,
                )
            except Exception as exc:  # cleanup is deliberately non-authoritative
                cleanup_errors.append(f"old-generation cleanup: {exc}")
            try:
                inject("during_stale_staging_cleanup")
                _cleanup_stale_staging(
                    root,
                    stale_staging_seconds=stale_staging_seconds,
                )
            except Exception as exc:  # cleanup is deliberately non-authoritative
                cleanup_errors.append(f"stale-staging cleanup: {exc}")
            state = (
                PublicationState.CLEANUP_PENDING
                if cleanup_errors
                else PublicationState.PUBLISHED
            )
            return PublicationResult(
                run_id=effective_run_id,
                generation_id=effective_generation_id,
                state=state,
                pointer_path=pointer_path,
                manifest_path=generation_path / GENERATION_MANIFEST_FILENAME,
                files=MappingProxyType(
                    {name: generation_path / name for name in OUTPUT_FILE_NAMES}
                ),
                cleanup_errors=tuple(cleanup_errors),
            )
    except PublicationCommittedError:
        raise
    except Exception as exc:
        if pointer_committed:
            raise PublicationCommittedError(
                f"Publication committed before failure: {exc}",
                state=PublicationState.PUBLISHED,
            ) from exc
        raise PublicationError(
            f"Generation was not published: {exc}",
            state=PublicationState.FAILED_UNPUBLISHED,
        ) from exc


def _cleanup_old_generations(
    root: Path,
    *,
    current_generation_id: str,
    retention_count: int,
) -> None:
    generations = root / "generations"
    candidates = sorted(
        (
            path
            for path in generations.iterdir()
            if path.is_dir() and not path.is_symlink()
        ),
        key=lambda path: path.name,
        reverse=True,
    )
    retained = {path.name for path in candidates[:retention_count]}
    retained.add(current_generation_id)
    for path in candidates:
        if path.name in retained:
            continue
        if not _GENERATION_ID_RE.fullmatch(path.name):
            continue
        shutil.rmtree(path)


def _cleanup_stale_staging(
    root: Path,
    *,
    stale_staging_seconds: int,
) -> None:
    cutoff = datetime.now(UTC).timestamp() - stale_staging_seconds
    staging = root / ".staging"
    for path in staging.iterdir():
        if (
            path.is_dir()
            and not path.is_symlink()
            and _GENERATION_ID_RE.fullmatch(path.name)
            and path.stat().st_mtime <= cutoff
        ):
            shutil.rmtree(path)


def inspect_recovery_state(
    safe_root: Path,
    *,
    repo_root: Path,
) -> RecoveryInventory:
    root = _validate_requested_safe_root(safe_root, repo_root)
    snapshot = resolve_current_generation(root, repo_root=repo_root)
    generations = root / "generations"
    staging = root / ".staging"
    orphan_ids = tuple(
        sorted(
            path.name
            for path in generations.iterdir()
            if path.is_dir()
            and not path.is_symlink()
            and path.name != snapshot.generation_id
            and _GENERATION_ID_RE.fullmatch(path.name)
        )
    )
    stale_ids = tuple(
        sorted(
            path.name
            for path in staging.iterdir()
            if path.is_dir()
            and not path.is_symlink()
            and _GENERATION_ID_RE.fullmatch(path.name)
        )
    )
    return RecoveryInventory(
        current_generation_id=snapshot.generation_id,
        orphan_generation_ids=orphan_ids,
        stale_staging_ids=stale_ids,
    )
