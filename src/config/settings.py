from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK, DEFAULT_DATABASE


@dataclass(frozen=True)
class Settings:
    project_root: Path
    database_path: Path
    active_data_pack: Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_settings() -> Settings:
    root = get_project_root()
    return Settings(
        project_root=root,
        database_path=root / DEFAULT_DATABASE,
        active_data_pack=root / DEFAULT_DATA_PACK,
    )
