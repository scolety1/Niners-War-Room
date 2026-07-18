from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.services.data_refresh_orchestrator_service import DEFAULT_STATUS_PATH


def _status_root_snapshot() -> dict[str, str]:
    root = DEFAULT_STATUS_PATH.parent
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    "page_path",
    (
        Path("app/pages/24_refresh_data_v1.py"),
        Path("app/pages/28_settings_data_health_v1.py"),
    ),
)
def test_page_open_route_smoke_has_no_refresh_or_receipt_write_side_effect(
    page_path: Path,
) -> None:
    before = _status_root_snapshot()

    at = AppTest.from_file(str(page_path)).run(timeout=40)

    assert not at.exception
    assert _status_root_snapshot() == before
