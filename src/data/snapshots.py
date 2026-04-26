from __future__ import annotations

from datetime import UTC, datetime


def utc_snapshot_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
