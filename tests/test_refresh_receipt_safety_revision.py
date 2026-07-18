from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

import src.services.refresh_receipt_store_service as receipt_store
from src.services.refresh_receipt_store_service import (
    CORRUPT,
    MISSING,
    OVERSIZED,
    RECEIPT_MAX_BYTES,
    RECEIPT_SCHEMA_VERSION,
    RESULT_FIELDS,
    TOP_LEVEL_FIELDS,
    UNSUPPORTED_SCHEMA,
    inspect_refresh_receipt,
    write_refresh_receipt,
)


def _row(**changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "source_id": "source_a",
        "source_name": "Source A",
        "dataset_id": "",
        "source_family": "",
        "action_type": "REFRESHED",
        "status": "GREEN",
        "refreshed": True,
        "execution_status": "success",
        "headline_status": "current",
        "freshness_status": "CURRENT",
    }
    row.update(changes)
    return row


def _payload(run_id: str = "20260713_150001") -> dict[str, object]:
    return {
        "run_id": run_id,
        "started_at_utc": "2026-07-13T15:00:00+00:00",
        "finished_at_utc": "2026-07-13T15:01:00+00:00",
        "loader_mode": "QUICK_REFRESH",
        "overall_status": "GREEN",
        "results": [_row()],
    }


def _tree_snapshot(root: Path) -> tuple[tuple[object, ...], ...]:
    if not root.exists():
        return ()
    output: list[tuple[object, ...]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            output.append(("directory", relative))
            continue
        body = path.read_bytes()
        stat = path.stat()
        output.append(
            (
                "file",
                relative,
                len(body),
                hashlib.sha256(body).hexdigest(),
                stat.st_mtime_ns,
            )
        )
    return tuple(output)


def _seed_valid_tree(root: Path) -> Path:
    return write_refresh_receipt(_payload(), status_root=root).latest_path


def _rejected_variants() -> list[tuple[str, dict[str, object]]]:
    variants: list[tuple[str, dict[str, object]]] = []

    def add(
        name: str,
        *,
        payload_change: dict[str, object] | None = None,
        row_change: dict[str, object] | None = None,
    ) -> None:
        candidate = copy.deepcopy(_payload("20260713_150002"))
        candidate.update(payload_change or {})
        if row_change:
            candidate["results"][0].update(row_change)  # type: ignore[index,union-attr]
        variants.append((name, candidate))

    add("string_boolean", row_change={"refreshed": "yes"})
    add("integer_boolean", row_change={"refreshed": 1})
    add("boolean_action_mismatch", row_change={"refreshed": False})
    add("malformed_timestamp", payload_change={"started_at_utc": "July 13, 2026"})
    add("unsupported_outcome", payload_change={"overall_status": "BLUE"})
    add("unknown_top_level", payload_change={"unknown": "value"})
    add("unknown_nested_key", row_change={"metadata": {"unexpected": "value"}})
    add(
        "nested_authorization_header",
        row_change={"source_name": {"authorization": "Basic private"}},
    )
    add(
        "nested_bearer_token",
        row_change={"source_name": {"header": "Bearer private-token"}},
    )
    add("api_key_like_field", row_change={"api_key": "private"})
    add("cookie_session_field", row_change={"session_cookie": "private"})
    add("absolute_windows_path", row_change={"source_name": r"C:\Users\private\receipt.json"})
    add("absolute_posix_path", row_change={"source_name": "/home/private/receipt.json"})
    add(
        "raw_provider_response",
        row_change={"provider_response": {"players": [{"id": 1}]}},
    )
    add("nested_arbitrary_metadata", row_change={"metadata": {"arbitrary": {"x": 1}}})
    add("oversized_nested_list", row_change={"source_name": ["x"] * 257})
    add("excessive_string", row_change={"source_name": "x" * 161})

    missing = copy.deepcopy(_payload("20260713_150002"))
    del missing["results"][0]["source_id"]  # type: ignore[index,union-attr]
    variants.append(("missing_required_field", missing))

    add("null_non_nullable", row_change={"source_id": None})
    add("invalid_dataset_id_type", row_change={"dataset_id": 7})
    add("unsupported_schema_version", payload_change={"schema_version": 1})
    return variants


REJECTED_VARIANTS = _rejected_variants()


@pytest.mark.parametrize(
    ("case", "candidate"),
    REJECTED_VARIANTS,
    ids=[name for name, _ in REJECTED_VARIANTS],
)
def test_rejected_candidates_leave_complete_storage_tree_unchanged(
    tmp_path: Path,
    case: str,
    candidate: dict[str, object],
) -> None:
    root = tmp_path / case
    _seed_valid_tree(root)
    before = _tree_snapshot(root)

    with pytest.raises(ValueError):
        write_refresh_receipt(candidate, status_root=root)

    assert _tree_snapshot(root) == before


def test_oversized_serialized_candidate_is_rejected_before_any_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "oversized_candidate"
    _seed_valid_tree(root)
    before = _tree_snapshot(root)
    monkeypatch.setattr(receipt_store, "RECEIPT_MAX_BYTES", 128)

    with pytest.raises(ValueError, match="2 MiB"):
        write_refresh_receipt(_payload("20260713_150003"), status_root=root)

    assert _tree_snapshot(root) == before


@pytest.mark.parametrize(
    ("limit_delta", "accepted"),
    ((1, True), (0, True), (-1, False)),
    ids=("one_byte_under", "exact_limit", "one_byte_over"),
)
def test_exact_final_serialized_byte_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit_delta: int,
    accepted: bool,
) -> None:
    root = tmp_path / f"size_boundary_{limit_delta}"
    payload = _payload(f"20260713_15100{limit_delta + 1}")
    created_at = "2026-07-13T15:10:00+00:00"
    provisional = receipt_store._build_receipt(
        payload,
        prior_receipt=None,
        created_at_utc=created_at,
    )
    _, serialized = receipt_store._finalize_candidate(provisional)
    monkeypatch.setattr(receipt_store, "RECEIPT_MAX_BYTES", len(serialized) + limit_delta)
    before = _tree_snapshot(root)

    if accepted:
        result = write_refresh_receipt(
            payload,
            status_root=root,
            created_at_utc=created_at,
        )
        assert result.serialized_bytes == len(serialized)
        assert result.latest_path.read_bytes() == serialized
    else:
        with pytest.raises(ValueError, match="2 MiB"):
            write_refresh_receipt(
                payload,
                status_root=root,
                created_at_utc=created_at,
            )
        assert _tree_snapshot(root) == before


def test_exact_rejected_2102591_byte_candidate_preserves_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "rejected_2102591_bytes"
    _seed_valid_tree(root)
    before = _tree_snapshot(root)
    rejected_size = 2_102_591
    monkeypatch.setattr(
        receipt_store,
        "_serialized_receipt_bytes",
        lambda _payload: b"x" * rejected_size,
    )

    with pytest.raises(ValueError, match="2 MiB"):
        write_refresh_receipt(_payload("20260713_151004"), status_root=root)

    assert rejected_size == RECEIPT_MAX_BYTES + 5_439
    assert _tree_snapshot(root) == before


def test_result_list_bound_is_rejected_before_any_mutation(tmp_path: Path) -> None:
    root = tmp_path / "result_list_bound"
    _seed_valid_tree(root)
    before = _tree_snapshot(root)
    candidate = _payload("20260713_150004")
    candidate["results"] = [
        _row(source_id=f"source_{index}") for index in range(receipt_store.RECEIPT_MAX_RESULTS + 1)
    ]

    with pytest.raises(ValueError, match="1-256"):
        write_refresh_receipt(candidate, status_root=root)

    assert _tree_snapshot(root) == before


def test_interrupted_latest_replacement_rolls_back_every_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "interrupted"
    _seed_valid_tree(root)
    write_refresh_receipt(_payload("20260713_150005"), status_root=root)
    before = _tree_snapshot(root)
    real_replace = receipt_store._replace_file

    def fail_latest(source: Path, target: Path) -> None:
        if target.name == receipt_store.LATEST_RECEIPT_NAME:
            raise OSError("synthetic interrupted latest replacement")
        real_replace(source, target)

    monkeypatch.setattr(receipt_store, "_replace_file", fail_latest)
    with pytest.raises(OSError, match="interrupted"):
        write_refresh_receipt(_payload("20260713_150006"), status_root=root)

    assert _tree_snapshot(root) == before
    assert not list(root.rglob("*.tmp"))


def test_valid_write_is_closed_deterministic_bounded_and_structured(tmp_path: Path) -> None:
    root = tmp_path / "valid"
    result = write_refresh_receipt(
        _payload(),
        status_root=root,
        created_at_utc="2026-07-13T15:02:00+00:00",
    )
    body = result.latest_path.read_bytes()
    document = json.loads(body)

    assert result.committed is True
    assert result.receipt_id == document["receipt_id"]
    assert result.serialized_bytes == len(body) <= RECEIPT_MAX_BYTES
    assert result.archive_path.read_bytes() == body
    assert set(document) == TOP_LEVEL_FIELDS
    assert set(document["results"][0]) == RESULT_FIELDS
    assert document["schema_version"] == RECEIPT_SCHEMA_VERSION
    assert body == receipt_store._serialized_receipt_bytes(document)
    assert "runner_path" not in body.decode("utf-8")
    assert "metadata" not in document["results"][0]


@pytest.mark.parametrize(
    ("case", "raw", "expected"),
    (
        ("missing", None, MISSING),
        ("corrupt", b"{bad", CORRUPT),
        ("unsupported", b'{"schema_version":1}\n', UNSUPPORTED_SCHEMA),
        (
            "duplicate_key",
            b'{"schema_version":2,"schema_version":2}\n',
            CORRUPT,
        ),
        ("oversized", "oversized", OVERSIZED),
    ),
)
def test_invalid_inspection_states_are_strictly_read_only(
    tmp_path: Path,
    case: str,
    raw: bytes | str | None,
    expected: str,
) -> None:
    root = tmp_path / case
    latest = root / receipt_store.LATEST_RECEIPT_NAME
    if raw is not None:
        root.mkdir(parents=True)
        latest.write_bytes(
            b"x" * (RECEIPT_MAX_BYTES + 1) if raw == "oversized" else raw
        )
    before = _tree_snapshot(root)

    inspected = inspect_refresh_receipt(status_path=latest)

    assert inspected.load_status == expected
    assert inspected.automatic_mutation_performed is False
    assert inspected.quarantine_path is None
    assert _tree_snapshot(root) == before


def test_invalid_type_document_with_valid_integrity_is_rejected_read_only(tmp_path: Path) -> None:
    root = tmp_path / "invalid_type"
    latest = _seed_valid_tree(root)
    document = json.loads(latest.read_bytes())
    document["results"][0]["refreshed"] = "yes"
    document["integrity"]["digest"] = receipt_store._integrity_digest(document)
    latest.write_bytes(receipt_store._serialized_receipt_bytes(document))
    before = _tree_snapshot(root)

    inspected = inspect_refresh_receipt(status_path=latest)

    assert inspected.load_status == CORRUPT
    assert _tree_snapshot(root) == before


def test_corrupt_latest_and_backup_inspection_never_mutates_either(tmp_path: Path) -> None:
    root = tmp_path / "corrupt_both"
    _seed_valid_tree(root)
    write_refresh_receipt(_payload("20260713_150007"), status_root=root)
    latest = root / receipt_store.LATEST_RECEIPT_NAME
    backup = root / "backups" / receipt_store.BACKUP_RECEIPT_NAME
    latest.write_bytes(b"{latest-corrupt")
    backup.write_bytes(b"{backup-corrupt")
    before = _tree_snapshot(root)

    inspected = inspect_refresh_receipt(status_path=latest)

    assert inspected.load_status == CORRUPT
    assert inspected.backup_status == CORRUPT
    assert _tree_snapshot(root) == before
