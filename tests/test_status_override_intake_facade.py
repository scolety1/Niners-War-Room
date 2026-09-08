"""NWR class-time autonomous hardening, section 6: the real status/risk
intake CONTRACT (`add_verified_status_override`) has existed since the
post-draft overnight repair, but was never reachable from any facade
method -- the only way to add a new real, verified event was to hand-edit
the committed JSON file directly, bypassing that validation entirely.
Proves the new `submit_player_status_override`/`list_player_status_overrides`
facade methods actually close that gap, using an isolated fixture config
file (never the real committed overrides file)."""

import json
from pathlib import Path

import pytest

from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.current_player_status_overrides_service import OVERRIDES_RELATIVE_PATH


def _fixture_repo_root(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / OVERRIDES_RELATIVE_PATH.name).write_text(
        json.dumps({"schema_version": 1, "overrides": []}), encoding="utf-8"
    )
    return tmp_path


def _facade(tmp_path: Path) -> DesktopBackendFacade:
    root = _fixture_repo_root(tmp_path)
    return DesktopBackendFacade(repo_root=root, mode="redraft", redraft_root=tmp_path / "redraft")


def test_submit_player_status_override_writes_a_real_verified_event(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    result = facade.submit_player_status_override(
        player_id="00-9999999",
        player_name="Test Player",
        kind="SEASON_OUT",
        reason="Real, cited season-ending injury.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00Z",
        sources=["https://example.com/real-report"],
    )
    assert result.data["playerId"] == "00-9999999"
    assert result.data["kind"] == "SEASON_OUT"

    listed = facade.list_player_status_overrides()
    assert [row["playerId"] for row in listed.data["overrides"]] == ["00-9999999"]


def test_submit_player_status_override_rejects_an_uncited_event(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    with pytest.raises(FacadeError) as exc_info:
        facade.submit_player_status_override(
            player_id="00-9999999",
            player_name="Test Player",
            kind="SEASON_OUT",
            reason="Real reason but no source.",
            effective_date="2026-09-01",
            verified_at_utc="2026-09-01T12:00:00Z",
            sources=[],
        )
    assert exc_info.value.code == "STATUS_OVERRIDE_REJECTED"
    assert exc_info.value.status == 422
    # A rejected submission must never be written.
    assert facade.list_player_status_overrides().data["overrides"] == []


def test_submit_player_status_override_rejects_a_duplicate_player(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    kwargs = {
        "player_id": "00-9999999",
        "player_name": "Test Player",
        "kind": "NOT_WITH_TEAM",
        "reason": "Real, cited release.",
        "effective_date": "2026-09-01",
        "verified_at_utc": "2026-09-01T12:00:00Z",
        "sources": ["https://example.com/real-report"],
    }
    facade.submit_player_status_override(**kwargs)
    with pytest.raises(FacadeError) as exc_info:
        facade.submit_player_status_override(**kwargs)
    assert exc_info.value.code == "STATUS_OVERRIDE_REJECTED"


def test_submit_player_status_override_unavailable_outside_redraft_mode(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    facade = DesktopBackendFacade(repo_root=root, mode="dynasty", redraft_root=tmp_path / "redraft")
    with pytest.raises(FacadeError) as exc_info:
        facade.submit_player_status_override(
            player_id="00-9999999",
            player_name="Test Player",
            kind="SEASON_OUT",
            reason="Real, cited season-ending injury.",
            effective_date="2026-09-01",
            verified_at_utc="2026-09-01T12:00:00Z",
            sources=["https://example.com/real-report"],
        )
    assert exc_info.value.code == "MODE_ROUTE_UNAVAILABLE"


def test_list_player_status_overrides_reflects_the_real_committed_fixture(tmp_path: Path) -> None:
    root = _fixture_repo_root(tmp_path)
    (root / OVERRIDES_RELATIVE_PATH).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "overrides": [
                    {
                        "player_id": "00-1111111",
                        "player_name": "Existing Player",
                        "kind": "TEAM_CORRECTION",
                        "reason": "Real trade.",
                        "effective_date": "2026-08-01",
                        "verified_at_utc": "2026-08-01T00:00:00Z",
                        "sources": ["https://example.com/trade"],
                        "corrected_team": "SF",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    facade = DesktopBackendFacade(repo_root=root, mode="redraft", redraft_root=tmp_path / "redraft")
    result = facade.list_player_status_overrides()
    assert result.data["overrides"][0]["correctedTeam"] == "SF"
