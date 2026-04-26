from __future__ import annotations

from pathlib import Path


def resolve_data_pack(path: str | Path) -> Path:
    return Path(path).resolve()
