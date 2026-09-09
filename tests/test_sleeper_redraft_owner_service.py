from __future__ import annotations

import json

import pytest

from src.services.sleeper_redraft_owner_service import (
    SleeperRedraftImportError,
    import_sleeper_redraft_profile,
    load_sleeper_draft_picks,
    resync_sleeper_redraft_profile,
)


class FakeSleeperClient:
    def __init__(self, *, league_id: str = "league-1", scoring: object | None = None, drafts: object | None = None) -> None:
        self.league_id = league_id
        self.scoring = scoring if scoring is not None else {
            "pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1,
            "rush_td": 6, "rec_yd": 0.1, "rec": 1, "rec_td": 6,
            "fum_lost": -2, "fgm_50_59": 5,
        }
        self.drafts = drafts if drafts is not None else [
            {"draft_id": "draft-2026", "season": "2026", "status": "pre_draft", "type": "snake", "draft_order": None, "start_time": None, "settings": {"rounds": 15, "teams": 10, "pick_timer": 60}},
        ]

    def get_json(self, path: str):
        values = {
            f"league/{self.league_id}": {"league_id": self.league_id, "name": "Fantasy Gamers", "season": "2026", "status": "pre_draft", "settings": {"num_teams": 10}, "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF", "BN", "BN", "BN", "BN", "BN", "BN"], "scoring_settings": self.scoring},
            "user/scolety": {"user_id": "owner-9", "username": "scolety", "display_name": "scolety"},
            f"league/{self.league_id}/users": [{"user_id": "owner-9", "metadata": {"team_name": "Brown Town & Big Mike"}}],
            f"league/{self.league_id}/rosters": [{"roster_id": 9, "owner_id": "owner-9", "keepers": [], "players": []}],
            f"league/{self.league_id}/drafts": self.drafts,
            "draft/draft-2026/picks": [{"pick_no": 1, "player_id": "p1"}],
        }
        return values[path]


def test_import_maps_exact_core_settings_and_records_unsupported_scoring(tmp_path) -> None:
    imported = import_sleeper_redraft_profile(
        league_id="league-1", username="scolety", redraft_root=tmp_path, client=FakeSleeperClient()
    )
    assert imported.profile.team_count == 10
    assert imported.profile.roster.bench_size == 6
    assert imported.profile.roster.flex == 1
    assert imported.profile.scoring.reception == 1
    assert imported.profile.scoring.return_td == 0
    assert imported.profile.draft.rounds == 15
    assert imported.profile.draft.draft_slot is None
    assert imported.unsupported_scoring == ("fgm_50_59",)
    receipt = json.loads((tmp_path / "sleeper_imports" / f"{imported.profile.profile_id}.json").read_text())
    assert receipt["owner"]["user_id"] == "owner-9"
    assert receipt["owner"]["roster_id"] == 9
    assert receipt["write_behavior"] == "NO_SLEEPER_WRITES"
    assert {row["sleeper_setting"] for row in receipt["scoring_reconciliation"] if row["status"] == "exact"} == {"pass_yd", "pass_td", "pass_int", "rush_yd", "rush_td", "rec_yd", "rec", "rec_td", "fum_lost"}


def test_fantasy_gamers_identity_is_stable_and_ppr(tmp_path) -> None:
    league_id = "1312983576827920384"
    imported = import_sleeper_redraft_profile(
        league_id=league_id,
        username="scolety",
        redraft_root=tmp_path,
        client=FakeSleeperClient(league_id=league_id),
    )

    assert imported.profile.league_name == "Fantasy Gamers"
    assert imported.profile.team_count == 10
    assert imported.profile.scoring.reception == 1.0
    assert imported.profile.provider == "sleeper"
    assert imported.profile.provider_league_id == league_id


def test_import_rejects_malformed_and_ambiguous_sleeper_responses(tmp_path) -> None:
    with pytest.raises(SleeperRedraftImportError, match="ambiguous"):
        import_sleeper_redraft_profile(
            league_id="league-1", username="scolety", redraft_root=tmp_path,
            client=FakeSleeperClient(drafts=[
                {"draft_id": "a", "season": "2026", "status": "pre_draft", "type": "snake", "settings": {"rounds": 15}},
                {"draft_id": "b", "season": "2026", "status": "pre_draft", "type": "snake", "settings": {"rounds": 15}},
            ]),
        )
    with pytest.raises(SleeperRedraftImportError, match="not numeric"):
        import_sleeper_redraft_profile(
            league_id="league-1", username="scolety", redraft_root=tmp_path,
            client=FakeSleeperClient(scoring={"rec": "unknown"}),
        )


def test_live_companion_read_is_pick_only() -> None:
    assert load_sleeper_draft_picks(draft_id="draft-2026", client=FakeSleeperClient()) == ({"pick_no": 1, "player_id": "p1"},)


# --- NWR Overnight V3, Lane 2: recurring (not one-shot) Sleeper resync.


class ResyncFakeSleeperClient(FakeSleeperClient):
    """Same league as FakeSleeperClient, plus a `players/nfl` endpoint and a
    roster that can be mutated between the initial import and a resync call
    -- proves a real second read, not a replay of the first one."""

    def __init__(self, *, roster_players: list[str] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.roster_players = roster_players if roster_players is not None else []

    def get_json(self, path: str):
        if path == "players/nfl":
            return {
                "p1": {"full_name": "Roster Player One", "position": "WR", "team": "SF", "active": True},
                "p2": {"full_name": "Roster Player Two", "position": "RB", "team": "DAL", "active": True},
            }
        if path == f"league/{self.league_id}/rosters":
            return [{"roster_id": 9, "owner_id": "owner-9", "keepers": [], "players": list(self.roster_players)}]
        return super().get_json(path)


def test_resync_refreshes_the_stored_roster_snapshot_without_any_sleeper_write(tmp_path) -> None:
    initial_client = ResyncFakeSleeperClient(roster_players=["p1"])
    imported = import_sleeper_redraft_profile(
        league_id="league-1", username="scolety", redraft_root=tmp_path, client=initial_client,
    )
    profile_id = imported.profile.profile_id

    resynced_client = ResyncFakeSleeperClient(roster_players=["p1", "p2"])
    result = resync_sleeper_redraft_profile(
        profile_id=profile_id, redraft_root=tmp_path, client=resynced_client,
        synced_at_utc="2026-09-09T00:00:00+00:00",
    )

    snapshot = result.receipt["roster_snapshot"]
    assert snapshot["synced_at_utc"] == "2026-09-09T00:00:00+00:00"
    assert {row["player_name"] for row in snapshot["players"]} == {"Roster Player One", "Roster Player Two"}
    assert snapshot["unresolved_sleeper_player_ids"] == []

    persisted = json.loads((tmp_path / "sleeper_imports" / f"{profile_id}.json").read_text())
    assert persisted["roster_snapshot"]["players"] == snapshot["players"]
    assert persisted["write_behavior"] == "NO_SLEEPER_WRITES"


def test_resync_records_unresolved_players_without_dropping_them(tmp_path) -> None:
    imported = import_sleeper_redraft_profile(
        league_id="league-1", username="scolety", redraft_root=tmp_path,
        client=ResyncFakeSleeperClient(roster_players=[]),
    )
    result = resync_sleeper_redraft_profile(
        profile_id=imported.profile.profile_id, redraft_root=tmp_path,
        client=ResyncFakeSleeperClient(roster_players=["p1", "unresolved-id"]),
    )
    snapshot = result.receipt["roster_snapshot"]
    assert snapshot["unresolved_sleeper_player_ids"] == ["unresolved-id"]
    assert {row["player_name"] for row in snapshot["players"]} == {"Roster Player One"}


def test_resync_rejects_a_non_sleeper_profile(tmp_path) -> None:
    from src.services.redraft_engine_v1_service import (
        DraftContext, LeagueProfile, RosterSettings, ScoringSettings, create_profile,
    )

    local_profile = create_profile(
        tmp_path,
        LeagueProfile(
            profile_id="local-only", league_name="Local League", season=2026, team_count=10,
            roster=RosterSettings(), scoring=ScoringSettings(), draft=DraftContext(rounds=15),
            provider="local",
        ),
        league_name="Local League",
    )
    with pytest.raises(SleeperRedraftImportError, match="Sleeper-imported"):
        resync_sleeper_redraft_profile(
            profile_id=local_profile.profile_id, redraft_root=tmp_path,
            client=ResyncFakeSleeperClient(),
        )


# --- NWR Overnight V3 retry-queue follow-up: roster_limits contract fix.
# Before this fix, `resync`/re-import fully replaced `draft=template.draft`,
# silently discarding any position maximum the owner had manually entered in
# Profile & Scoring for a position Sleeper's own settings don't expose a
# real maximum for (e.g. QB in a non-Superflex league). Real known K/DST
# maxima must still refresh from the live Sleeper read on every resync.


def test_resync_preserves_owner_entered_roster_limits_while_refreshing_kdst(tmp_path) -> None:
    from dataclasses import replace as dataclass_replace

    from src.services.redraft_engine_v1_service import load_profile, save_profile

    imported = import_sleeper_redraft_profile(
        league_id="league-1", username="scolety", redraft_root=tmp_path,
        client=ResyncFakeSleeperClient(roster_players=["p1"]),
    )
    profile_id = imported.profile.profile_id
    assert imported.profile.draft.roster_limits == {"K": 1, "DST": 1}

    # Owner manually enters a real, platform-confirmed QB maximum this
    # import path has no way to discover on its own (Profile & Scoring UI).
    stored = load_profile(tmp_path, profile_id)
    owner_edited = save_profile(
        tmp_path,
        dataclass_replace(
            stored,
            draft=dataclass_replace(
                stored.draft, roster_limits={**stored.draft.roster_limits, "QB": 3},
            ),
        ),
    )
    assert owner_edited.draft.roster_limits == {"K": 1, "DST": 1, "QB": 3}

    result = resync_sleeper_redraft_profile(
        profile_id=profile_id, redraft_root=tmp_path,
        client=ResyncFakeSleeperClient(roster_players=["p1", "p2"]),
    )

    # QB=3 (owner-entered, no real Sleeper source) survives the resync;
    # K/DST are refreshed from the real, just-read Sleeper roster settings
    # (unchanged here, but sourced fresh, not merely carried over).
    assert result.profile.draft.roster_limits == {"K": 1, "DST": 1, "QB": 3}
