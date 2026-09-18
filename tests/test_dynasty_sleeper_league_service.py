"""Dynasty League Import V1 (Worker 2, 2026-09-18).

Unit tests for the pure/testable parts of `dynasty_sleeper_league_service`:
`annotate_ownership` (a pure join over synthetic board+league shapes) and
`resolve_owned_pick_capital`/`resolve_round_count_baseline` (the real
round-count-ambiguity reconciliation), plus a persistence round-trip test.
No network access -- every test here builds synthetic Sleeper-shaped data
directly; live-API verification is a separate, explicitly non-pytest pass
documented in `docs/codex/dynasty_league_import_v1/LEDGER.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.services.dynasty_sleeper_league_service import (
    DynastyDraftRecord,
    DynastyLeaguePersistenceError,
    DynastyLeagueSettings,
    DynastyLeagueSnapshot,
    DynastyRosterEntry,
    PickOwnership,
    RoundCountBaseline,
    active_league_profile_id,
    annotate_ownership,
    fetch_dynasty_league_snapshot,
    import_dynasty_league,
    load_latest_league_snapshot,
    load_league_profile,
    resolve_owned_pick_capital,
    resolve_round_count_baseline,
    save_league_profile,
    save_league_snapshot,
    set_active_league_profile,
)


def _settings(**overrides) -> DynastyLeagueSettings:
    base = dict(
        league_id="LID",
        name="Test League",
        season="2026",
        status="in_season",
        num_teams=3,
        scoring_settings={"rec": 0.0, "pass_td": 3.0},
        roster_positions=("QB", "RB", "WR", "BN", "BN"),
        taxi_slots=0,
        reserve_slots=1,
        playoff_teams=2,
        playoff_week_start=15,
        trade_deadline=99,
        pick_trading=1,
        waiver_type=2,
        waiver_budget=100,
        max_keepers=1,
        configured_draft_rounds=3,
    )
    base.update(overrides)
    return DynastyLeagueSettings(**base)


def _roster(
    roster_id: int,
    owner_id: str,
    team_name: str,
    *,
    players=(),
    starters=(),
    reserve=(),
    taxi=(),
) -> DynastyRosterEntry:
    return DynastyRosterEntry(
        roster_id=roster_id,
        owner_id=owner_id,
        co_owners=(),
        team_name=team_name,
        players=tuple(players),
        starters=tuple(starters),
        reserve=tuple(reserve),
        taxi=tuple(taxi),
        wins=0,
        losses=0,
        ties=0,
        fpts=0.0,
        ppts=0.0,
    )


def _snapshot(
    *,
    rosters,
    traded_picks=(),
    drafts=(),
    baseline=None,
    settings=None,
) -> DynastyLeagueSnapshot:
    resolved_settings = settings or _settings()
    resolved_baseline = baseline or RoundCountBaseline(
        rounds=resolved_settings.configured_draft_rounds,
        source="configured_draft_rounds_fallback",
        disclosure="test fallback",
        startup_draft_id=None,
        rookie_draft_ids=(),
        ambiguous=True,
    )
    owner_by_roster = {r.roster_id: r.owner_id for r in rosters}
    roster_by_owner = {r.owner_id: r.roster_id for r in rosters}
    return DynastyLeagueSnapshot(
        league_id=resolved_settings.league_id,
        fetched_at_utc="2026-09-18T00:00:00+00:00",
        settings=resolved_settings,
        rosters=tuple(rosters),
        owner_id_by_roster_id=owner_by_roster,
        roster_id_by_owner_id=roster_by_owner,
        traded_picks=tuple(traded_picks),
        drafts=tuple(drafts),
        round_count_baseline=resolved_baseline,
    )


# --------------------------------------------------------------------------
# annotate_ownership
# --------------------------------------------------------------------------


def test_annotate_ownership_current_player_match_on_my_roster():
    my_roster = _roster(
        7, "owner-7", "Niners", players=["100", "101"], starters=["100"], reserve=[]
    )
    other_roster = _roster(2, "owner-2", "Rivals", players=["200"], starters=["200"])
    snapshot = _snapshot(rosters=[my_roster, other_roster])

    annotations = annotate_ownership(
        [{"asset_id": "current:100"}], snapshot, my_owner_id="owner-7"
    )

    assert annotations["current:100"] == {
        "ownershipStatus": "OWNED",
        "rosterId": 7,
        "rosterTeamName": "Niners",
        "rosterSlotStatus": "starter",
        "isMyTeam": True,
        "reason": "",
    }


def test_annotate_ownership_current_player_on_opponent_roster_is_not_my_team():
    my_roster = _roster(7, "owner-7", "Niners", players=["100"], starters=["100"])
    other_roster = _roster(
        2, "owner-2", "Rivals", players=["200"], starters=[], reserve=["200"]
    )
    snapshot = _snapshot(rosters=[my_roster, other_roster])

    annotations = annotate_ownership(
        [{"asset_id": "current:200"}], snapshot, my_owner_id="owner-7"
    )

    assert annotations["current:200"]["ownershipStatus"] == "OWNED"
    assert annotations["current:200"]["rosterId"] == 2
    assert annotations["current:200"]["rosterTeamName"] == "Rivals"
    assert annotations["current:200"]["rosterSlotStatus"] == "reserve"
    assert annotations["current:200"]["isMyTeam"] is False


def test_annotate_ownership_current_player_on_nobodys_roster_is_free_agent():
    my_roster = _roster(7, "owner-7", "Niners", players=["100"], starters=["100"])
    snapshot = _snapshot(rosters=[my_roster])

    annotations = annotate_ownership(
        [{"asset_id": "current:999"}], snapshot, my_owner_id="owner-7"
    )

    assert annotations["current:999"] == {
        "ownershipStatus": "FREE_AGENT",
        "rosterId": None,
        "rosterTeamName": None,
        "rosterSlotStatus": None,
        "isMyTeam": False,
        "reason": "",
    }


def test_annotate_ownership_rookie_asset_is_always_unresolved_never_guessed():
    my_roster = _roster(7, "owner-7", "Niners", players=["100"], starters=["100"])
    snapshot = _snapshot(rosters=[my_roster])

    annotations = annotate_ownership(
        [{"asset_id": "rookie:LOV121782"}, {"asset_id": "blocked-rookie:some-player"}],
        snapshot,
        my_owner_id="owner-7",
    )

    for asset_id in ("rookie:LOV121782", "blocked-rookie:some-player"):
        row = annotations[asset_id]
        assert row["ownershipStatus"] == "UNRESOLVED"
        assert row["rosterId"] is None
        assert row["isMyTeam"] is False
        assert row["reason"]  # non-empty, explains WHY it is unresolved


def test_annotate_ownership_never_annotates_pick_or_future_pick_assets():
    my_roster = _roster(7, "owner-7", "Niners", players=[])
    snapshot = _snapshot(rosters=[my_roster])

    annotations = annotate_ownership(
        [{"asset_id": "pick:2026:1.01"}, {"asset_id": "future-pick:2027-r1"}],
        snapshot,
        my_owner_id="owner-7",
    )

    assert annotations == {}


def test_annotate_ownership_accepts_camelcase_asset_id_key():
    my_roster = _roster(7, "owner-7", "Niners", players=["100"], starters=["100"])
    snapshot = _snapshot(rosters=[my_roster])

    annotations = annotate_ownership([{"assetId": "current:100"}], snapshot)

    assert annotations["current:100"]["ownershipStatus"] == "OWNED"
    assert annotations["current:100"]["isMyTeam"] is False  # no my_owner_id supplied


def test_annotate_ownership_never_returns_score_rank_or_value_fields():
    my_roster = _roster(7, "owner-7", "Niners", players=["100"], starters=["100"])
    snapshot = _snapshot(rosters=[my_roster])
    annotations = annotate_ownership(
        [{"asset_id": "current:100", "nwrScore": 99.9, "rank": 1}], snapshot
    )
    forbidden_keys = {"nwrScore", "rank", "score", "value"}
    assert forbidden_keys.isdisjoint(annotations["current:100"].keys())


# --------------------------------------------------------------------------
# resolve_round_count_baseline / resolve_owned_pick_capital
# --------------------------------------------------------------------------


def test_resolve_round_count_baseline_classifies_real_startup_vs_rookie_pattern():
    startup = DynastyDraftRecord(
        draft_id="startup-draft",
        status="complete",
        draft_type="linear",
        season="2026",
        rounds=5,  # equals roster_slot_count below
        start_time=1,
        created=1,
        pick_count=15,
        rookie_pick_fraction=0.0,
        classification="startup",  # as `_classify_draft` would label it during a real fetch
    )
    rookie = DynastyDraftRecord(
        draft_id="rookie-draft",
        status="complete",
        draft_type="linear",
        season="2026",
        rounds=2,
        start_time=2,
        created=2,
        pick_count=6,
        rookie_pick_fraction=1.0,
        classification="rookie",
    )

    baseline = resolve_round_count_baseline((startup, rookie), configured_draft_rounds=2)

    assert baseline.rounds == 2
    assert baseline.source == "rookie_draft_classified"
    assert baseline.ambiguous is False
    assert baseline.startup_draft_id == "startup-draft"
    assert baseline.rookie_draft_ids == ("rookie-draft",)


def test_resolve_round_count_baseline_discloses_disagreement_with_configured_rounds():
    rookie = DynastyDraftRecord(
        draft_id="rookie-draft",
        status="complete",
        draft_type="linear",
        season="2026",
        rounds=5,
        start_time=2,
        created=2,
        pick_count=50,
        rookie_pick_fraction=0.62,
        classification="rookie",
    )
    baseline = resolve_round_count_baseline((rookie,), configured_draft_rounds=99)
    assert baseline.rounds == 5
    assert baseline.source == "rookie_draft_classified"
    assert "disagrees" in baseline.disclosure
    assert baseline.ambiguous is False


def test_resolve_round_count_baseline_falls_back_and_discloses_when_ambiguous():
    unknown = DynastyDraftRecord(
        draft_id="odd-draft",
        status="complete",
        draft_type="linear",
        season="2026",
        rounds=7,
        start_time=1,
        created=1,
        pick_count=21,
        rookie_pick_fraction=0.35,
        classification="unknown",
    )
    baseline = resolve_round_count_baseline((unknown,), configured_draft_rounds=5)
    assert baseline.rounds == 5
    assert baseline.source == "configured_draft_rounds_fallback"
    assert baseline.ambiguous is True
    assert "fallback" in baseline.disclosure.lower()


def test_fetch_dynasty_league_snapshot_classifies_startup_vs_rookie_from_real_pick_evidence():
    """End-to-end (fake client, no network) reproduction of this league's
    REAL shape (see the module docstring / LEDGER.md): a 24-round startup
    draft whose round-1 picks are established veterans (`years_exp` != "0")
    and a 5-round recurring rookie draft whose round-1 pick is a real
    rookie (`years_exp == "0"`) -- proves the classification pipeline
    (`fetch_dynasty_league_snapshot` -> `_classify_draft` ->
    `resolve_round_count_baseline`) reaches the correct real-evidence
    conclusion end-to-end, not just when classification is hand-supplied.
    """

    def _picks(count: int, years_exp: str) -> list[dict]:
        return [
            {"round": (i // 10) + 1, "metadata": {"years_exp": years_exp}}
            for i in range(count)
        ]

    class _FakeClient:
        def get_json(self, path: str):
            if path == "league/LID":
                return {
                    "league_id": "LID",
                    "name": "Fake Dynasty League",
                    "season": "2026",
                    "status": "in_season",
                    "scoring_settings": {},
                    "roster_positions": ["QB"] * 24,
                    "settings": {"num_teams": 10, "draft_rounds": 5},
                }
            if path == "league/LID/rosters":
                return []
            if path == "league/LID/users":
                return []
            if path == "league/LID/traded_picks":
                return []
            if path == "league/LID/drafts":
                return [
                    {
                        "draft_id": "startup-draft",
                        "status": "complete",
                        "type": "linear",
                        "season": "2026",
                        "settings": {"rounds": 24},
                    },
                    {
                        "draft_id": "rookie-draft",
                        "status": "complete",
                        "type": "linear",
                        "season": "2026",
                        "settings": {"rounds": 5},
                    },
                ]
            if path == "draft/startup-draft/picks":
                return _picks(240, "4")  # all veterans
            if path == "draft/rookie-draft/picks":
                return _picks(50, "0")  # all real rookies
            raise AssertionError(f"Unexpected GET path in test: {path}")

    snapshot = fetch_dynasty_league_snapshot("LID", client=_FakeClient())

    drafts_by_id = {d.draft_id: d for d in snapshot.drafts}
    assert drafts_by_id["startup-draft"].classification == "startup"
    assert drafts_by_id["rookie-draft"].classification == "rookie"
    assert snapshot.round_count_baseline.rounds == 5
    assert snapshot.round_count_baseline.source == "rookie_draft_classified"
    assert snapshot.round_count_baseline.ambiguous is False


def test_resolve_owned_pick_capital_matches_real_league_shape():
    """Synthetic re-creation of this cycle's real 3-roster slice: roster 7
    trades away its own round-1 pick to roster 2, and acquires roster 2's
    round-2 pick; round counts differ between an actual 2026 draft (2
    rounds) and the projected 2027 baseline (3 rounds, from
    round_count_baseline) -- proving both `round_source` values are used
    correctly."""

    rosters = [
        _roster(1, "owner-1", "Team One"),
        _roster(2, "owner-2", "Team Two"),
        _roster(7, "owner-7", "Niners"),
    ]
    actual_2026_draft = DynastyDraftRecord(
        draft_id="rookie-2026",
        status="complete",
        draft_type="linear",
        season="2026",
        rounds=2,
        start_time=1,
        created=1,
        pick_count=6,
        rookie_pick_fraction=1.0,
        classification="rookie",
    )
    baseline = RoundCountBaseline(
        rounds=3,
        source="rookie_draft_classified",
        disclosure="test",
        startup_draft_id=None,
        rookie_draft_ids=("rookie-2026",),
        ambiguous=False,
    )
    snapshot = _snapshot(
        rosters=rosters,
        traded_picks=[
            {"season": "2026", "round": 1, "roster_id": 7, "owner_id": 2},
            {"season": "2026", "round": 2, "roster_id": 2, "owner_id": 7},
        ],
        drafts=[actual_2026_draft],
        baseline=baseline,
    )

    capital = resolve_owned_pick_capital(snapshot, seasons=("2026", "2027"))

    rows_7_2026 = [row for row in capital[7] if row.season == "2026"]
    # 2026 (actual draft, 2 rounds): roster 7 lost its own R1 (traded to
    # roster 2), kept its own R2 (never traded), AND separately acquired
    # roster 2's R2 -- two distinct round-2 picks land on roster 7, exactly
    # the real multi-pick-per-round shape this league's own real data has
    # (see the module docstring / LEDGER.md).
    assert {(row.original_roster_id, row.round) for row in rows_7_2026} == {(7, 2), (2, 2)}
    assert all(row.round_source == "actual_draft" for row in rows_7_2026)
    acquired = next(row for row in rows_7_2026 if row.original_roster_id == 2)
    assert acquired.traded is True
    kept = next(row for row in rows_7_2026 if row.original_roster_id == 7)
    assert kept.traded is False

    # 2027 (no draft yet -> baseline projection, 3 rounds): roster 7 has no
    # traded_picks records for 2027 at all, so it owns all 3 of its own.
    rows_7_2027 = [row for row in capital[7] if row.season == "2027"]
    assert {row.round for row in rows_7_2027} == {1, 2, 3}
    assert all(row.round_source == "baseline_projection" for row in rows_7_2027)
    assert all(row.traded is False for row in rows_7_2027)
    assert all(row.original_roster_id == 7 for row in rows_7_2027)

    # roster 2 lost its own 2026 R2 (traded to 7) but kept its own 2026 R1,
    # and separately gained roster 7's traded-away 2026 R1.
    rows_2_2026 = [row for row in capital[2] if row.season == "2026"]
    assert {(row.original_roster_id, row.round) for row in rows_2_2026} == {(2, 1), (7, 1)}


def test_resolve_owned_pick_capital_never_drops_a_malformed_traded_pick_record():
    rosters = [_roster(1, "owner-1", "Team One")]
    snapshot = _snapshot(
        rosters=rosters,
        traded_picks=[{"season": "2026", "round": "not-a-number", "roster_id": 1, "owner_id": 1}],
    )
    # Must not raise -- malformed records are skipped, not fatal.
    capital = resolve_owned_pick_capital(snapshot, seasons=("2026",))
    assert 1 in capital


# --------------------------------------------------------------------------
# Persistence round-trip
# --------------------------------------------------------------------------


def test_persistence_round_trips_profile_and_snapshot(tmp_path: Path) -> None:
    rosters = [_roster(7, "owner-7", "Niners", players=["100"], starters=["100"])]
    snapshot = _snapshot(rosters=rosters)
    root = tmp_path / "dynasty_v1"

    profile = save_league_profile(root, snapshot, my_owner_id="owner-7")
    assert profile.my_roster_id == 7
    reloaded_profile = load_league_profile(root, profile.profile_id)
    assert reloaded_profile == profile

    capital = resolve_owned_pick_capital(snapshot, seasons=("2026",))
    save_league_snapshot(root, profile.profile_id, snapshot, capital)
    persisted = load_latest_league_snapshot(root, profile.profile_id)
    assert persisted is not None
    assert persisted.league_snapshot.rosters[0].team_name == "Niners"
    assert persisted.pick_capital_by_roster_id[7] == capital[7]


def test_load_league_profile_raises_for_missing_profile(tmp_path: Path) -> None:
    with pytest.raises(DynastyLeaguePersistenceError):
        load_league_profile(tmp_path / "dynasty_v1", "does-not-exist")


# --------------------------------------------------------------------------
# Active-profile ("Connect League") persistence -- Worker 3
# --------------------------------------------------------------------------


def test_active_league_profile_id_is_none_before_anything_is_connected(tmp_path: Path) -> None:
    root = tmp_path / "dynasty_v1"
    assert active_league_profile_id(root) is None


def test_set_active_league_profile_persists_and_survives_a_fresh_read(tmp_path: Path) -> None:
    root = tmp_path / "dynasty_v1"
    rosters = [_roster(7, "owner-7", "Niners", players=["100"], starters=["100"])]
    snapshot = _snapshot(rosters=rosters)
    profile = save_league_profile(root, snapshot, my_owner_id="owner-7")

    returned = set_active_league_profile(root, profile.profile_id)
    assert returned == profile
    # A brand-new read (simulating a full process/app restart -- no shared
    # in-memory state at all) must see the same persisted selection.
    assert active_league_profile_id(root) == profile.profile_id


def test_set_active_league_profile_none_disconnects(tmp_path: Path) -> None:
    root = tmp_path / "dynasty_v1"
    rosters = [_roster(7, "owner-7", "Niners", players=["100"], starters=["100"])]
    snapshot = _snapshot(rosters=rosters)
    profile = save_league_profile(root, snapshot, my_owner_id="owner-7")
    set_active_league_profile(root, profile.profile_id)
    assert active_league_profile_id(root) == profile.profile_id

    returned = set_active_league_profile(root, None)
    assert returned is None
    assert active_league_profile_id(root) is None


def test_set_active_league_profile_rejects_an_unimported_profile(tmp_path: Path) -> None:
    root = tmp_path / "dynasty_v1"
    with pytest.raises(DynastyLeaguePersistenceError):
        set_active_league_profile(root, "never-imported")
    # A failed activation must never leave a dangling/incorrect marker.
    assert active_league_profile_id(root) is None


def test_import_dynasty_league_uses_injected_client_and_persists(tmp_path: Path) -> None:
    """Proves `import_dynasty_league`'s own orchestration (fetch -> resolve
    -> persist) without any network access, via a fake GET-only client."""

    class _FakeClient:
        def get_json(self, path: str):
            if path == "league/LID":
                return {
                    "league_id": "LID",
                    "name": "Fake League",
                    "season": "2026",
                    "status": "in_season",
                    "scoring_settings": {"rec": 0.0},
                    "roster_positions": ["QB", "BN"],
                    "settings": {
                        "num_teams": 2,
                        "taxi_slots": 0,
                        "reserve_slots": 1,
                        "playoff_teams": 2,
                        "playoff_week_start": 15,
                        "trade_deadline": 99,
                        "pick_trading": 1,
                        "waiver_type": 2,
                        "waiver_budget": 100,
                        "max_keepers": 1,
                        "draft_rounds": 2,
                    },
                }
            if path == "league/LID/rosters":
                return [
                    {
                        "roster_id": 1,
                        "owner_id": "owner-1",
                        "players": ["100"],
                        "starters": ["100"],
                        "reserve": [],
                        "taxi": None,
                        "settings": {"wins": 1, "losses": 0, "ties": 0, "fpts": 10, "ppts": 12},
                    }
                ]
            if path == "league/LID/users":
                return [{"user_id": "owner-1", "display_name": "owner-1", "metadata": {}}]
            if path == "league/LID/traded_picks":
                return []
            if path == "league/LID/drafts":
                return []
            raise AssertionError(f"Unexpected GET path in test: {path}")

    result = import_dynasty_league(
        "LID", tmp_path / "dynasty_v1", client=_FakeClient(), my_owner_id="owner-1"
    )
    assert result.profile.league_name == "Fake League"
    assert result.profile.my_roster_id == 1
    reloaded = load_latest_league_snapshot(tmp_path / "dynasty_v1", result.profile.profile_id)
    assert reloaded is not None
    assert reloaded.league_snapshot.rosters[0].owner_id == "owner-1"
