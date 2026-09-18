"""Dynasty League Import V1 (Worker 2, 2026-09-18).

Facade-level wiring tests. The single most important guarantee this pass
adds: `dynasty_bootstrap`/`dynasty_workspace`/`dynasty_asset` must return
BYTE-IDENTICAL output when the new `league_profile_id` parameter is
omitted -- zero risk to the existing, working, valuation-only Dynasty
experience when no league is connected. These tests prove that with a
real `json.dumps(..., sort_keys=True)` comparison, not just an assumption,
plus prove the annotated path actually adds real ownership context using a
fake (no-network) Sleeper client.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.application.desktop_facade import DesktopBackendFacade, FacadeError

REPO_ROOT = Path(__file__).resolve().parents[1]


class _FakeSleeperClient:
    """A real, deterministic, no-network stand-in for `SleeperHttpClient`,
    shaped after this cycle's actual live league (roster 7 = Niners,
    owner 1352768154031374336) but small enough to keep this test fast and
    self-contained. Includes one governed-board current player
    (`player_id` 9493, Puka Nacua's real governed asset id) on roster 7's
    real player list so the annotated-path assertions are meaningful."""

    def get_json(self, path: str):
        if path == "league/TESTLID":
            return {
                "league_id": "TESTLID",
                "name": "Fixture Dynasty League",
                "season": "2026",
                "status": "in_season",
                "scoring_settings": {"rec": 0.0, "pass_td": 3.0},
                "roster_positions": ["QB", "RB", "WR", "TE", "FLEX", "K"] + ["BN"] * 18,
                "settings": {
                    "num_teams": 2,
                    "taxi_slots": 0,
                    "reserve_slots": 2,
                    "playoff_teams": 4,
                    "playoff_week_start": 16,
                    "trade_deadline": 99,
                    "pick_trading": 1,
                    "waiver_type": 2,
                    "waiver_budget": 100,
                    "max_keepers": 1,
                    "draft_rounds": 5,
                },
            }
        if path == "league/TESTLID/rosters":
            return [
                {
                    "roster_id": 7,
                    "owner_id": "1352768154031374336",
                    "players": ["9493"],
                    "starters": ["9493"],
                    "reserve": [],
                    "taxi": None,
                    "settings": {"wins": 1, "losses": 0, "ties": 0, "fpts": 108, "fpts_decimal": 10},
                },
                {
                    "roster_id": 2,
                    "owner_id": "owner-2",
                    "players": [],
                    "starters": [],
                    "reserve": [],
                    "taxi": None,
                    "settings": {"wins": 0, "losses": 1, "ties": 0, "fpts": 0, "fpts_decimal": 0},
                },
            ]
        if path == "league/TESTLID/users":
            return [
                {
                    "user_id": "1352768154031374336",
                    "display_name": "mcolety1",
                    "metadata": {"team_name": "Niners"},
                },
                {"user_id": "owner-2", "display_name": "owner-2", "metadata": {}},
            ]
        if path == "league/TESTLID/traded_picks":
            return []
        if path == "league/TESTLID/drafts":
            return []
        raise AssertionError(f"Unexpected GET path in test fixture: {path}")


def _facade(tmp_path: Path) -> DesktopBackendFacade:
    return DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        redraft_root=tmp_path / "redraft",
        workspace_root=tmp_path / "workspace",
        dynasty_league_root=tmp_path / "dynasty_v1",
    )


def _import_fixture_league(facade: DesktopBackendFacade) -> str:
    result = facade.import_dynasty_sleeper_league(
        "TESTLID", my_owner_id="1352768154031374336", client=_FakeSleeperClient()
    )
    return result.data["profileId"]


# --------------------------------------------------------------------------
# The single most important guarantee: byte-identical when omitted
# --------------------------------------------------------------------------


def test_dynasty_bootstrap_is_byte_identical_when_league_profile_id_omitted(
    tmp_path: Path,
) -> None:
    facade = _facade(tmp_path)
    baseline = facade.dynasty_bootstrap()
    explicit_none = facade.dynasty_bootstrap(league_profile_id=None)
    assert json.dumps(baseline.data, sort_keys=True, default=str) == json.dumps(
        explicit_none.data, sort_keys=True, default=str
    )
    assert baseline.warnings == explicit_none.warnings
    assert "dynastyLeague" not in baseline.data
    assert all("ownership" not in row for row in baseline.data.get("rankings", ()))


def test_dynasty_workspace_is_byte_identical_when_league_profile_id_omitted(
    tmp_path: Path,
) -> None:
    facade = _facade(tmp_path)
    baseline = facade.dynasty_workspace()
    explicit_none = facade.dynasty_workspace(league_profile_id=None)
    assert json.dumps(baseline.data, sort_keys=True, default=str) == json.dumps(
        explicit_none.data, sort_keys=True, default=str
    )
    assert "dynastyLeague" not in baseline.data


def test_dynasty_asset_is_byte_identical_when_league_profile_id_omitted(
    tmp_path: Path,
) -> None:
    facade = _facade(tmp_path)
    baseline = facade.dynasty_asset("current:9493")
    explicit_none = facade.dynasty_asset("current:9493", league_profile_id=None)
    assert json.dumps(baseline.data, sort_keys=True, default=str) == json.dumps(
        explicit_none.data, sort_keys=True, default=str
    )
    assert "ownership" not in baseline.data


def test_repeated_bootstrap_calls_without_annotation_stay_stable(tmp_path: Path) -> None:
    """Guards against an aliasing/mutation bug where an earlier annotated
    call could leak state into a later unannotated call (they share one
    cached `_OwnerSnapshot`)."""

    facade = _facade(tmp_path)
    profile_id = _import_fixture_league(facade)
    before = facade.dynasty_bootstrap()
    facade.dynasty_bootstrap(league_profile_id=profile_id)  # annotated call in between
    after = facade.dynasty_bootstrap()
    assert json.dumps(before.data, sort_keys=True, default=str) == json.dumps(
        after.data, sort_keys=True, default=str
    )


# --------------------------------------------------------------------------
# The annotated path actually works
# --------------------------------------------------------------------------


def test_import_dynasty_sleeper_league_persists_and_reports_real_fields(
    tmp_path: Path,
) -> None:
    facade = _facade(tmp_path)
    result = facade.import_dynasty_sleeper_league(
        "TESTLID", my_owner_id="1352768154031374336", client=_FakeSleeperClient()
    )
    assert result.data["leagueName"] == "Fixture Dynasty League"
    assert result.data["myRosterId"] == 7
    assert result.data["rosterCount"] == 2
    assert (tmp_path / "dynasty_v1" / "league_profiles" / "TESTLID.json").is_file()


def test_dynasty_bootstrap_with_league_profile_id_annotates_ownership(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    profile_id = _import_fixture_league(facade)

    annotated = facade.dynasty_bootstrap(league_profile_id=profile_id)
    assert annotated.data["dynastyLeague"]["profileId"] == profile_id
    puka_row = next(row for row in annotated.data["rankings"] if row["assetId"] == "current:9493")
    assert puka_row["ownership"]["ownershipStatus"] == "OWNED"
    assert puka_row["ownership"]["rosterTeamName"] == "Niners"
    assert puka_row["ownership"]["isMyTeam"] is True
    # Every OTHER field on the row must be untouched -- this is an
    # annotation, never a recomputation.
    baseline_row = next(
        row for row in facade.dynasty_bootstrap().data["rankings"] if row["assetId"] == "current:9493"
    )
    for key, value in baseline_row.items():
        assert puka_row[key] == value

    rookie_rows_with_ownership = [row for row in annotated.data["rookies"] if "ownership" in row]
    assert rookie_rows_with_ownership
    assert all(
        row["ownership"]["ownershipStatus"] == "UNRESOLVED" for row in rookie_rows_with_ownership
    )


def test_dynasty_asset_with_league_profile_id_annotates_single_row(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    profile_id = _import_fixture_league(facade)
    annotated = facade.dynasty_asset("current:9493", league_profile_id=profile_id)
    assert annotated.data["ownership"]["ownershipStatus"] == "OWNED"
    assert annotated.data["ownership"]["isMyTeam"] is True


def test_dynasty_bootstrap_rejects_unknown_league_profile_id(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    with pytest.raises(FacadeError) as exc_info:
        facade.dynasty_bootstrap(league_profile_id="never-imported")
    assert exc_info.value.code == "DYNASTY_LEAGUE_PROFILE_NOT_FOUND"


def test_import_dynasty_sleeper_league_unavailable_outside_dynasty_mode(tmp_path: Path) -> None:
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="redraft",
        redraft_root=tmp_path / "redraft",
        dynasty_league_root=tmp_path / "dynasty_v1",
    )
    with pytest.raises(FacadeError) as exc_info:
        facade.import_dynasty_sleeper_league("TESTLID", client=_FakeSleeperClient())
    assert exc_info.value.code == "MODE_ROUTE_UNAVAILABLE"


def test_load_dynasty_league_profile_round_trips_persisted_state(tmp_path: Path) -> None:
    facade = _facade(tmp_path)
    profile_id = _import_fixture_league(facade)
    loaded = facade.load_dynasty_league_profile(profile_id)
    assert loaded.data["leagueName"] == "Fixture Dynasty League"
    assert loaded.data["myRosterId"] == 7
    niners_row = next(row for row in loaded.data["rosters"] if row["rosterId"] == 7)
    assert niners_row["isMyTeam"] is True
    assert niners_row["teamName"] == "Niners"
