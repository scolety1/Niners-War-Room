from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import src.services.data_refresh_orchestrator_service as orchestrator
import src.services.refresh_receipt_store_service as receipt_store
from src.services.refresh_receipt_store_service import RECEIPT_MAX_BYTES, write_refresh_receipt

PAGES = (
    Path("app/pages/24_refresh_data_v1.py"),
    Path("app/pages/28_settings_data_health_v1.py"),
)
CASES = (
    "valid_latest",
    "missing_latest",
    "corrupt_latest",
    "unsupported_schema",
    "oversized_receipt",
    "duplicate_key_receipt",
    "invalid_type_receipt",
)


def _payload() -> dict[str, object]:
    return {
        "run_id": "20260713_160001",
        "started_at_utc": "2026-07-13T16:00:00+00:00",
        "finished_at_utc": "2026-07-13T16:01:00+00:00",
        "loader_mode": "QUICK_REFRESH",
        "overall_status": "GREEN",
        "results": [
            {
                "source_id": "page_fixture",
                "source_name": "Page fixture",
                "dataset_id": "",
                "source_family": "",
                "action_type": "REFRESHED",
                "status": "GREEN",
                "refreshed": True,
                "execution_status": "success",
                "headline_status": "current",
                "freshness_status": "CURRENT",
            }
        ],
    }


def _snapshot(root: Path) -> tuple[tuple[object, ...], ...]:
    if not root.exists():
        return ()
    output: list[tuple[object, ...]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            output.append(("directory", relative))
            continue
        body = path.read_bytes()
        output.append(
            (
                "file",
                relative,
                len(body),
                hashlib.sha256(body).hexdigest(),
                path.stat().st_mtime_ns,
            )
        )
    return tuple(output)


def _prepare_case(root: Path, case: str) -> Path:
    latest = root / receipt_store.LATEST_RECEIPT_NAME
    if case == "missing_latest":
        return latest
    if case in {"valid_latest", "invalid_type_receipt"}:
        latest = write_refresh_receipt(
            _payload(),
            status_root=root,
            created_at_utc="2026-07-13T16:02:00+00:00",
        ).latest_path
        if case == "invalid_type_receipt":
            document = json.loads(latest.read_bytes())
            document["results"][0]["refreshed"] = "yes"
            document["integrity"]["digest"] = receipt_store._integrity_digest(document)
            latest.write_bytes(receipt_store._serialized_receipt_bytes(document))
        return latest
    root.mkdir(parents=True)
    raw = {
        "corrupt_latest": b"{corrupt",
        "unsupported_schema": b'{"schema_version":1}\n',
        "oversized_receipt": b"x" * (RECEIPT_MAX_BYTES + 1),
        "duplicate_key_receipt": b'{"schema_version":2,"schema_version":2}\n',
    }[case]
    latest.write_bytes(raw)
    return latest


@pytest.mark.parametrize("page_path", PAGES, ids=("refresh_data", "settings_data_health"))
@pytest.mark.parametrize("case", CASES)
def test_page_open_is_read_only_for_every_receipt_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    page_path: Path,
    case: str,
) -> None:
    root = tmp_path / case
    latest = _prepare_case(root, case)
    protected = tmp_path / "protected_source_and_production_sentinel.bin"
    protected.write_bytes(b"source and production state must remain unchanged")
    monkeypatch.setattr(orchestrator, "DEFAULT_STATUS_PATH", latest)

    refresh_calls: list[str] = []

    def forbidden_refresh(*args: object, **kwargs: object) -> None:
        del args, kwargs
        refresh_calls.append("called")
        raise AssertionError("Page open attempted a refresh")

    for name in (
        "run_quick_refresh",
        "run_full_safe_refresh",
        "run_check_protected_artifacts",
        "run_manual_sources_checklist",
    ):
        monkeypatch.setattr(orchestrator, name, forbidden_refresh)

    before = _snapshot(tmp_path)
    at = AppTest.from_file(str(page_path)).run(timeout=40)

    assert not at.exception
    assert refresh_calls == []
    assert _snapshot(tmp_path) == before
