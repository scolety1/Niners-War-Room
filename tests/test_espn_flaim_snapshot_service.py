from __future__ import annotations

import json
from pathlib import Path

from src.services.espn_flaim_snapshot_service import (
    EspnFlaimSnapshotError,
    espn_flaim_snapshot_path,
    load_espn_flaim_snapshot,
)


def _synthetic_snapshot_dict() -> dict:
    return {
        "profile_id": "profile-abc",
        "provider_league_id": "1009373442",
        "league_name": "SYNTHETIC — not a real league",
        "season": 2026,
        "team_count": 8,
        "owner_team_id": "5",
        "owner_team_name": "Synthetic Team",
        "roster": [
            {
                "provider_player_id": "espn-1",
                "player_name": "Synthetic Player",
                "position": "QB",
                "team": "SF",
                "slot": "STARTER",
            }
        ],
        "scoring_settings": [],
        "scoring_completeness": "UNKNOWN",
        "available_player_pool": [],
        "available_player_pool_coverage": "NONE",
        "available_player_pool_bound_description": None,
        "retrieved_at_utc": "2026-09-19T18:00:00+00:00",
        "provider_as_of_utc": None,
    }


def test_snapshot_path_mirrors_the_sleeper_import_receipt_convention(tmp_path: Path) -> None:
    path = espn_flaim_snapshot_path(tmp_path, "profile-abc")
    assert path == tmp_path / "espn_flaim_snapshots" / "profile-abc.json"


def test_load_returns_none_when_no_snapshot_file_exists_yet(tmp_path: Path) -> None:
    # This is the correct, honest state for every real profile today --
    # no real Flaim connection has fetched anything yet.
    assert load_espn_flaim_snapshot(tmp_path, "profile-abc") is None


def test_load_parses_a_real_snapshot_file_from_the_documented_location(tmp_path: Path) -> None:
    path = espn_flaim_snapshot_path(tmp_path, "profile-abc")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_synthetic_snapshot_dict()), encoding="utf-8")

    snapshot = load_espn_flaim_snapshot(tmp_path, "profile-abc")

    assert snapshot is not None
    assert snapshot.provider_league_id == "1009373442"
    assert snapshot.retrieved_at_utc == "2026-09-19T18:00:00+00:00"


def test_load_raises_a_specific_error_for_a_present_but_malformed_file(tmp_path: Path) -> None:
    path = espn_flaim_snapshot_path(tmp_path, "profile-abc")
    path.parent.mkdir(parents=True, exist_ok=True)
    broken = _synthetic_snapshot_dict()
    del broken["league_name"]
    path.write_text(json.dumps(broken), encoding="utf-8")

    try:
        load_espn_flaim_snapshot(tmp_path, "profile-abc")
        assert False, "expected EspnFlaimSnapshotError, not a silent None/default"
    except EspnFlaimSnapshotError as exc:
        assert "league_name" in str(exc)
