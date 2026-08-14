from __future__ import annotations

import json

import pytest

from src.services.sleeper_redraft_owner_service import (
    SleeperRedraftImportError,
    import_sleeper_redraft_profile,
    load_sleeper_draft_picks,
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
