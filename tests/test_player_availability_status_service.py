import json
from pathlib import Path

from src.services.current_player_status_overrides_service import (
    OVERRIDES_RELATIVE_PATH,
    add_verified_status_override,
)
from src.services.player_availability_status_service import (
    load_player_availability_statuses,
    player_availability_authority_health,
)


def _seeded_repo_root(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / OVERRIDES_RELATIVE_PATH.name).write_text(
        json.dumps({"schema_version": 1, "overrides": []}), encoding="utf-8"
    )
    return tmp_path


def test_empty_when_no_overrides_file_exists(tmp_path: Path):
    assert load_player_availability_statuses(tmp_path) == ()
    health = player_availability_authority_health(tmp_path)
    assert health["entryCount"] == 0
    assert health["automatedFeed"] is False


def test_season_out_maps_to_out_for_season_with_injury_designation(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-1",
        player_name="Test Player",
        kind="SEASON_OUT",
        reason="ACL tear, placed on IR.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
    )
    statuses = load_player_availability_statuses(tmp_path)
    assert len(statuses) == 1
    status = statuses[0]
    assert status.status_category == "OUT_FOR_SEASON"
    assert status.injury_designation == "OUT"
    assert status.administrative_exempt is False
    assert status.released is False
    assert status.source == "MANUAL_VERIFIED_OVERRIDE"


def test_administrative_exempt_is_not_relabeled_as_injury(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-2",
        player_name="Exempt Player",
        kind="ADMINISTRATIVE_EXEMPT",
        reason="Placed on Commissioner Exempt list.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
    )
    status = load_player_availability_statuses(root)[0]
    assert status.status_category == "ADMINISTRATIVE_EXEMPT"
    assert status.injury_designation is None
    assert status.administrative_exempt is True


def test_not_with_team_marks_released_not_injured(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-3",
        player_name="Released Player",
        kind="NOT_WITH_TEAM",
        reason="Released, unsigned.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
    )
    status = load_player_availability_statuses(root)[0]
    assert status.status_category == "NOT_WITH_TEAM"
    assert status.released is True
    assert status.injury_designation is None


def test_team_correction_carries_corrected_team_as_current_team(tmp_path: Path):
    root = _seeded_repo_root(tmp_path)
    add_verified_status_override(
        root,
        player_id="player-4",
        player_name="Traded Player",
        kind="TEAM_CORRECTION",
        reason="Traded.",
        effective_date="2026-09-01",
        verified_at_utc="2026-09-01T12:00:00+00:00",
        sources=("https://example.com/report",),
        corrected_team="SF",
    )
    status = load_player_availability_statuses(root)[0]
    assert status.status_category == "TEAM_CORRECTION"
    assert status.current_team == "SF"


def test_authority_health_discloses_no_automated_feed(tmp_path: Path):
    health = player_availability_authority_health(tmp_path)
    assert health["automatedFeed"] is False
    assert any("no automated" in issue.lower() for issue in health["issues"])
