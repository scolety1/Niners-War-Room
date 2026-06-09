from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from src.config.settings import get_project_root


@dataclass(frozen=True)
class ApiSettings:
    sleeper_league_id: str
    sleeper_api_base: str
    cfbd_api_key: str
    cfbd_api_base: str
    sportsdataio_api_key: str
    sportsdataio_api_base: str
    rotowire_export_root: Path | None
    pff_export_root: Path | None
    live_api_enabled: bool
    api_cache_root: Path
    api_timeout_seconds: int
    max_requests_per_minute: int


def get_api_settings() -> ApiSettings:
    root = get_project_root()
    return ApiSettings(
        sleeper_league_id=_env("NINERS_SLEEPER_LEAGUE_ID", "1344772855908290560"),
        sleeper_api_base=_env("SLEEPER_API_BASE", "https://api.sleeper.app/v1").rstrip("/"),
        cfbd_api_key=_env("CFBD_API_KEY", ""),
        cfbd_api_base=_env("CFBD_API_BASE", "https://api.collegefootballdata.com").rstrip("/"),
        sportsdataio_api_key=_env("SPORTSDATAIO_API_KEY", ""),
        sportsdataio_api_base=_env("SPORTSDATAIO_API_BASE", "https://api.sportsdata.io").rstrip(
            "/"
        ),
        rotowire_export_root=_optional_path("ROTOWIRE_EXPORT_ROOT"),
        pff_export_root=_optional_path("PFF_EXPORT_ROOT"),
        live_api_enabled=_bool_env("MODEL_V4_LIVE_API_ENABLED", default=False),
        api_cache_root=_path_env("MODEL_V4_API_CACHE_ROOT", root / "local_exports/api_cache"),
        api_timeout_seconds=_int_env("MODEL_V4_API_TIMEOUT_SECONDS", default=30),
        max_requests_per_minute=_int_env("MODEL_V4_MAX_REQUESTS_PER_MINUTE", default=60),
    )


def require_live_api_enabled(source_name: str) -> None:
    if not get_api_settings().live_api_enabled:
        raise RuntimeError(
            f"Live API calls for {source_name} are disabled. Set "
            "MODEL_V4_LIVE_API_ENABLED=true only when a source-specific importer is "
            "approved and cached."
        )


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


def _bool_env(name: str, *, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, *, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _path_env(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else default


def _optional_path(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    return Path(value) if value else None
