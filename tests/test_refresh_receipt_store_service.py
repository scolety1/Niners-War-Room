from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.services.refresh_receipt_store_service as receipt_store
from src.services.refresh_receipt_store_service import (
    BACKUP_RECEIPT_NAME,
    CORRUPT,
    MISSING,
    OVERSIZED,
    RECEIPT_MAX_ARCHIVES,
    RECEIPT_MAX_BYTES,
    RECEIPT_MAX_QUARANTINE,
    RECEIPT_SCHEMA_VERSION,
    STALE_RETAINED_DATA,
    UNSUPPORTED_SCHEMA,
    VALID_BACKUP,
    VALID_LATEST,
    load_refresh_receipt,
    quarantine_invalid_refresh_receipt,
    write_refresh_receipt,
)


def _row(
    *,
    source_id: str = "source_a",
    action_type: str = "REFRESHED",
    status: str = "GREEN",
    refreshed: bool = True,
    freshness_status: str = "CURRENT",
    **extra,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_name": source_id,
        "dataset_id": "",
        "source_family": "",
        "action_type": action_type,
        "status": status,
        "refreshed": refreshed,
        "freshness_status": freshness_status,
        "execution_status": "success" if refreshed else "",
        **extra,
    }


def _payload(
    run_id: str,
    rows: list[dict[str, object]],
    *,
    overall_status: str = "GREEN",
) -> dict[str, object]:
    second = int(run_id[-2:]) % 60
    started = f"2026-07-13T12:00:{second:02d}+00:00"
    finished = f"2026-07-13T12:01:{second:02d}+00:00"
    return {
        "run_id": run_id,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "loader_mode": "QUICK_REFRESH",
        "overall_status": overall_status,
        "results": rows,
    }


def test_valid_receipt_round_trip_and_fresh_process_load(tmp_path: Path) -> None:
    root = tmp_path / "refresh_data"
    latest = write_refresh_receipt(
        _payload("20260713_120001", [_row()]),
        status_root=root,
        created_at_utc="2026-07-13T12:02:01+00:00",
    ).latest_path

    first = load_refresh_receipt(status_path=latest)
    second = load_refresh_receipt(status_path=Path(str(latest)))

    assert first.load_status == VALID_LATEST
    assert second.latest_receipt == first.latest_receipt
    assert first.latest_receipt["schema_version"] == RECEIPT_SCHEMA_VERSION
    assert first.latest_receipt["receipt_id"].startswith("rr_")
    assert len(first.latest_receipt["integrity"]["digest"]) == 64
    assert not list(root.glob("*.tmp"))


def test_atomic_write_uses_replace_and_leaves_only_complete_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replaced: list[str] = []
    original_replace = receipt_store._replace_file

    def replace_spy(path: Path, target: Path) -> None:
        replaced.append(Path(target).name)
        original_replace(path, target)

    monkeypatch.setattr(receipt_store, "_replace_file", replace_spy)
    root = tmp_path / "refresh_data"
    latest = write_refresh_receipt(
        _payload("20260713_120002", [_row()]),
        status_root=root,
    ).latest_path

    assert latest.name in replaced
    assert json.loads(latest.read_text(encoding="utf-8"))["run_id"] == "20260713_120002"
    assert not list(root.rglob("*.tmp"))


def test_latest_success_and_last_known_good_are_separate(tmp_path: Path) -> None:
    root = tmp_path / "refresh_data"
    write_refresh_receipt(_payload("20260713_120003", [_row()]), status_root=root)
    prior = load_refresh_receipt(status_path=root / "latest_refresh_status.json")
    prior_id = prior.latest_receipt["receipt_id"]

    write_refresh_receipt(
        _payload(
            "20260713_120004",
            [
                _row(
                    action_type="FAILED",
                    status="RED",
                    refreshed=False,
                    freshness_status="",
                    execution_status="failed",
                )
            ],
            overall_status="RED",
        ),
        status_root=root,
    )
    loaded = load_refresh_receipt(status_path=root / "latest_refresh_status.json")
    result = loaded.latest_receipt["results"][0]

    assert result["latest_successful_receipt_id"] == prior_id
    assert result["last_known_good_receipt_id"] == ""
    assert result["retained_data_status"] == "NOT_ENOUGH_INFORMATION"


def test_failed_latest_with_explicit_stale_retained_data_links_lkg(tmp_path: Path) -> None:
    root = tmp_path / "refresh_data"
    write_refresh_receipt(_payload("20260713_120005", [_row()]), status_root=root)
    prior_id = load_refresh_receipt(
        status_path=root / "latest_refresh_status.json"
    ).latest_receipt["receipt_id"]

    write_refresh_receipt(
        _payload(
            "20260713_120006",
            [
                _row(
                    action_type="FAILED",
                    status="RED",
                    refreshed=False,
                    freshness_status="STALE",
                    execution_status="failed",
                )
            ],
            overall_status="RED",
        ),
        status_root=root,
    )
    loaded = load_refresh_receipt(status_path=root / "latest_refresh_status.json")
    result = loaded.latest_receipt["results"][0]

    assert result["retained_data_status"] == STALE_RETAINED_DATA
    assert result["latest_successful_receipt_id"] == prior_id
    assert result["last_known_good_receipt_id"] == prior_id
    assert loaded.backup_status == VALID_BACKUP
    assert loaded.backup_receipt["receipt_id"] == prior_id


def test_corrupt_latest_inspection_is_read_only_and_explicit_quarantine_is_separate(
    tmp_path: Path,
) -> None:
    root = tmp_path / "refresh_data"
    write_refresh_receipt(_payload("20260713_120007", [_row()]), status_root=root)
    write_refresh_receipt(_payload("20260713_120008", [_row()]), status_root=root)
    latest = root / "latest_refresh_status.json"
    latest.write_text("{truncated", encoding="utf-8")
    before = latest.read_bytes()

    loaded = load_refresh_receipt(status_path=latest)

    assert loaded.load_status == CORRUPT
    assert loaded.latest_receipt is None
    assert loaded.backup_status == VALID_BACKUP
    assert loaded.backup_receipt is not None
    assert loaded.quarantine_path is None
    assert loaded.automatic_mutation_performed is False
    assert loaded.maintenance_required is True
    assert latest.read_bytes() == before
    assert not (root / "quarantine").exists()

    with pytest.raises(PermissionError, match="confirmation"):
        quarantine_invalid_refresh_receipt(status_path=latest)
    quarantine = quarantine_invalid_refresh_receipt(status_path=latest, confirmed=True)
    assert quarantine.read_bytes() == before
    assert not latest.exists()


def test_corrupt_latest_and_corrupt_backup_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "refresh_data"
    write_refresh_receipt(_payload("20260713_120009", [_row()]), status_root=root)
    write_refresh_receipt(_payload("20260713_120010", [_row()]), status_root=root)
    latest = root / "latest_refresh_status.json"
    latest.write_text("{bad", encoding="utf-8")
    backup = root / "backups" / BACKUP_RECEIPT_NAME
    backup.write_text("{bad", encoding="utf-8")

    loaded = load_refresh_receipt(status_path=latest)

    assert loaded.load_status == CORRUPT
    assert loaded.backup_status == CORRUPT
    assert loaded.backup_receipt is None


def test_missing_unsupported_duplicate_and_oversized_states_fail_closed(
    tmp_path: Path,
) -> None:
    latest = tmp_path / "refresh_data" / "latest_refresh_status.json"
    assert load_refresh_receipt(status_path=latest).load_status == MISSING

    latest.parent.mkdir(parents=True)
    latest.write_text('{"schema_version":99}', encoding="utf-8")
    unsupported = load_refresh_receipt(status_path=latest)
    assert unsupported.load_status == UNSUPPORTED_SCHEMA
    assert latest.exists()
    assert unsupported.quarantine_path is None

    latest.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    assert load_refresh_receipt(status_path=latest).load_status == CORRUPT

    latest.write_bytes(b"x" * (RECEIPT_MAX_BYTES + 1))
    oversized = load_refresh_receipt(status_path=latest)
    assert oversized.load_status == OVERSIZED
    assert oversized.latest_receipt is None


def test_archive_and_quarantine_retention_are_bounded(tmp_path: Path) -> None:
    root = tmp_path / "refresh_data"
    for index in range(RECEIPT_MAX_ARCHIVES + 3):
        run_id = f"20260713_12{index:04d}"
        write_refresh_receipt(_payload(run_id, [_row()]), status_root=root)
    archives = [
        path
        for path in root.glob("*_status.json")
        if path.name != "latest_refresh_status.json"
    ]
    assert len(archives) == RECEIPT_MAX_ARCHIVES

    latest = root / "latest_refresh_status.json"
    for _ in range(RECEIPT_MAX_QUARANTINE + 3):
        latest.write_text("{bad", encoding="utf-8")
        quarantine_invalid_refresh_receipt(status_path=latest, confirmed=True)
        write_refresh_receipt(_payload(f"20260713_13{_:04d}", [_row()]), status_root=root)
    assert len(list((root / "quarantine").glob("*.json"))) == RECEIPT_MAX_QUARANTINE


def test_receipt_rejects_credential_or_raw_payload_keys(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown keys"):
        write_refresh_receipt(
            _payload("20260713_120011", [_row(token="private")]),
            status_root=tmp_path,
        )
