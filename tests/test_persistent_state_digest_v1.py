from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from post_v1_assertion_harness import (
    DIGEST_NAME,
    DIGEST_SERIALIZER,
    DigestInventoryRecord,
    canonical_digest_bytes,
    digest_records_from_csv,
    persistent_state_digest_v1,
)

REPRODUCTION_CSV = Path(
    "docs/hq/master/"
    "nwr_post_v1_assertion_harness_digest_revision_v1_20260722/"
    "PERSISTENT_STATE_DIGEST_REPRODUCTION.csv"
)


def _hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _records() -> tuple[DigestInventoryRecord, ...]:
    return (
        DigestInventoryRecord("refresh/latest.json", 5, _hash(b"alpha"), "2026-07-21T01:00:00Z"),
        DigestInventoryRecord("draft/state.json", 4, _hash(b"beta"), "2026-07-21T02:00:00Z"),
    )


def _digest(records: tuple[DigestInventoryRecord, ...]) -> str:
    return persistent_state_digest_v1(records, family="persistent")


def test_digest_is_byte_deterministic_and_documents_serializer_shape() -> None:
    first = canonical_digest_bytes(_records(), family="persistent")
    second = canonical_digest_bytes(_records(), family="persistent")

    assert first == second
    assert not first.startswith(b"\xef\xbb\xbf")
    assert not first.endswith(b"\n")
    assert json.loads(first) == {
        "version": DIGEST_NAME,
        "serializer": DIGEST_SERIALIZER,
        "family": "persistent",
        "records": [
            {
                "path": "draft/state.json",
                "bytes": 4,
                "sha256": _hash(b"beta"),
            },
            {
                "path": "refresh/latest.json",
                "bytes": 5,
                "sha256": _hash(b"alpha"),
            },
        ],
    }


def test_reversed_input_order_has_the_same_digest() -> None:
    assert _digest(_records()) == _digest(tuple(reversed(_records())))


def test_windows_and_posix_separators_normalize_to_the_same_digest() -> None:
    posix = (DigestInventoryRecord("refresh/latest.json", 5, _hash(b"alpha")),)
    windows = (DigestInventoryRecord(r"refresh\latest.json", 5, _hash(b"alpha")),)

    assert _digest(posix) == _digest(windows)


def test_duplicate_normalized_paths_are_rejected() -> None:
    records = (
        DigestInventoryRecord("refresh/latest.json", 5, _hash(b"alpha")),
        DigestInventoryRecord(r"refresh\latest.json", 5, _hash(b"alpha")),
    )

    with pytest.raises(AssertionError, match="duplicate normalized path"):
        _digest(records)


def test_case_is_preserved_and_compared_ordinally() -> None:
    upper = (DigestInventoryRecord("State/File.json", 5, _hash(b"alpha")),)
    lower = (DigestInventoryRecord("state/file.json", 5, _hash(b"alpha")),)

    assert _digest(upper) != _digest(lower)
    assert _digest(upper + lower)


def test_empty_inventory_has_a_stable_defined_digest() -> None:
    body = canonical_digest_bytes((), family="persistent")

    assert json.loads(body)["records"] == []
    assert persistent_state_digest_v1((), family="persistent") == hashlib.sha256(body).hexdigest()


def test_changed_file_bytes_change_digest_even_when_size_is_unchanged() -> None:
    original = (DigestInventoryRecord("state.bin", 5, _hash(b"alpha")),)
    changed = (DigestInventoryRecord("state.bin", 5, _hash(b"omega")),)

    assert _digest(original) != _digest(changed)


def test_changed_file_size_changes_digest() -> None:
    original = (DigestInventoryRecord("state.bin", 5, _hash(b"alpha")),)
    changed = (DigestInventoryRecord("state.bin", 6, _hash(b"alpha")),)

    assert _digest(original) != _digest(changed)


def test_timestamp_only_change_does_not_change_byte_state_digest() -> None:
    original = (DigestInventoryRecord("state.bin", 5, _hash(b"alpha"), "2026-07-21T00:00:00Z"),)
    changed = (DigestInventoryRecord("state.bin", 5, _hash(b"alpha"), "2026-07-22T00:00:00Z"),)

    assert _digest(original) == _digest(changed)


@pytest.mark.parametrize(
    "unsafe_path",
    ("../state.json", "state/../secret.json", "/absolute/state.json", r"C:\state.json"),
)
def test_path_traversal_and_absolute_paths_are_rejected(unsafe_path: str) -> None:
    with pytest.raises(AssertionError):
        _digest((DigestInventoryRecord(unsafe_path, 5, _hash(b"alpha")),))


def test_non_ascii_path_is_encoded_as_utf8_without_ascii_escaping() -> None:
    record = DigestInventoryRecord("état/状态.json", 5, _hash(b"alpha"))
    body = canonical_digest_bytes((record,), family="persistent")

    assert "état/状态.json".encode() in body
    assert _digest((record,))


def test_one_file_addition_and_removal_change_digest() -> None:
    base = _records()
    addition = DigestInventoryRecord("new/file.json", 5, _hash(b"gamma"))

    assert _digest(base) != _digest(base + (addition,))
    assert _digest(base) != _digest(base[1:])


def test_recorded_persistent_and_recovery_inventories_reproduce_exact_v1_digests() -> None:
    persistent = digest_records_from_csv(REPRODUCTION_CSV, family="persistent")
    recovery = digest_records_from_csv(REPRODUCTION_CSV, family="recovery")

    assert len(persistent) == 14
    assert sum(record.bytes for record in persistent) == 542_801
    assert persistent_state_digest_v1(persistent, family="persistent") == (
        "88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987"
    )
    assert len(recovery) == 7
    assert sum(record.bytes for record in recovery) == 172_878
    assert persistent_state_digest_v1(recovery, family="recovery") == (
        "1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835"
    )
