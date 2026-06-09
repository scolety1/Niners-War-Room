from __future__ import annotations

import pytest

from src.config.api_settings import get_api_settings, require_live_api_enabled


def test_api_settings_default_to_safe_local_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_V4_LIVE_API_ENABLED", raising=False)
    monkeypatch.delenv("CFBD_API_KEY", raising=False)
    monkeypatch.delenv("SPORTSDATAIO_API_KEY", raising=False)
    settings = get_api_settings()

    assert settings.sleeper_league_id == "1344772855908290560"
    assert settings.live_api_enabled is False
    assert settings.cfbd_api_key == ""
    assert settings.sportsdataio_api_key == ""
    assert settings.rotowire_export_root is None
    assert settings.api_cache_root.as_posix().endswith("local_exports/api_cache")


def test_live_api_guard_fails_closed_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_V4_LIVE_API_ENABLED", "false")

    with pytest.raises(RuntimeError, match="Live API calls"):
        require_live_api_enabled("collegefootballdata")


def test_live_api_guard_can_be_enabled_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_V4_LIVE_API_ENABLED", "true")

    require_live_api_enabled("sleeper")
