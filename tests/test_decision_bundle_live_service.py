from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.services.decision_bundle_live_service import (
    LiveDecisionBundleUnavailable,
    build_live_decision_bundle,
    diversify_candidate_shortlist,
)
from src.services.redraft_draft_room_v1_service import AdpSnapshot, draft_order
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import simulate_comparable_leagues


def _ranking(team_count: int = 6, rounds: int = 8) -> RankingResult:
    rows = []
    for position, count in (("QB", 8), ("RB", 20), ("WR", 24), ("TE", 8)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank, index + 1, f"{position}-{index}", f"{position} {index}", position,
                    "TST", 400 - rank, 0, 400 - rank, 0,
                    "HIGH" if index < 5 else "MEDIUM", 1 + (rank - 1) // 10,
                    "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-08-17", False,
                    position_tier=1 + index // 6,
                )
            )
    profile = LeagueProfile(
        "fixture", "Fixture", 2026, team_count,
        RosterSettings(k=1, dst=1, bench_size=3),
        ScoringSettings(reception=1), DraftContext(rounds=rounds, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _manual_assets() -> list[dict[str, str]]:
    return [
        {"player_id": f"manual:{p}:{i}", "player_name": f"{p} {i}", "position": p, "team": f"T{i}"}
        for p in ("K", "DST")
        for i in range(6)
    ]


def _empty_adp(profile: LeagueProfile) -> AdpSnapshot:
    return AdpSnapshot(profile.profile_id, "", "ppr", profile.team_count, "", "", "", (), ())


def _provenance():
    return build_score_provenance(
        league_profile_hash="lp", roster_state_hash="rs", available_player_hash="ap",
        universe_hash="uh", projection_model_version="proj-v1", market_snapshot_hash="mk",
        feature_set_version="fs-v1", team_score_version="ts-v1",
        championship_equity_version="ce-v1", pick_score_version="ps-v1",
        optimizer_version="opt-v1", seed=7, simulation_count=10,
        timestamp_utc="2026-09-03T12:00:00Z",
    )


def _room_state(*, owner_slot=1, picks=()):
    picks = list(picks)
    return {
        "owner_slot": owner_slot,
        "drafted": [p["player_id"] for p in picks],
        "picks": picks,
    }


def test_build_live_decision_bundle_returns_a_real_bundle_for_a_fresh_draft() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=3
    )

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=3,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    # NWR OVERNIGHT (K/DST completion): on a fresh (empty) roster, K and
    # DST are both genuinely needed (0 rostered, 1 required each) --
    # `max_candidates` bounds the ranked skill-position shortlist, but a
    # real, honestly-labeled K/DST candidate is ADDED on top rather than
    # silently excluded, so the real candidate count can legitimately
    # exceed max_candidates when a required manual-only position is due.
    assert len(result.candidates) >= 5
    manual_positions = {
        str(c.player_id).split(":")[1]
        for c in result.candidates
        if c.player_id.startswith("manual:")
    }
    assert "K" in manual_positions
    assert "DST" in manual_positions
    ranked_candidates = [c for c in result.candidates if not c.player_id.startswith("manual:")]
    assert len(ranked_candidates) == 5
    assert all(c.player_score is not None for c in ranked_candidates)
    manual_candidates = [c for c in result.candidates if c.player_id.startswith("manual:")]
    # Never a fabricated K/DST score -- the honest absence of a Player
    # Score is preserved exactly as it already was for any other
    # unmodeled manual asset.
    assert all(c.player_score is None for c in manual_candidates)


def test_build_live_decision_bundle_respects_already_drafted_players() -> None:
    # team_count=2 snake order is [1, 2, 2, 1, 1, 2, ...]: after ONE real
    # pick by team 1, pick #2 is genuinely team 2's turn -- owner_slot=2
    # keeps this test's "it's actually your turn" precondition real,
    # matching the same guard the live decision bundle enforces.
    ranking = _ranking(team_count=2)
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=5
    )

    picks = [
        {"player_id": "RB-0", "team_slot": 1, "position": "RB", "player_name": "RB 0"},
    ]
    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=2, picks=picks),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=5,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    ids = {c.player_id for c in result.candidates}
    assert "RB-0" not in ids


def test_build_live_decision_bundle_respects_position_maximum_legality() -> None:
    # The league explicitly configures QB max 2; legality never invents a
    # strategy cap from the number of starting slots.
    # team_count=2 order is [1,2,2,1,1,2,...]: after 4 real picks
    # (team1, team2, team2, team1 -- the owner's 2 real QB picks land at
    # positions 1 and 4), pick #5 genuinely belongs to team 1 (owner)
    # again, so this stays a real "it's your turn" case, not a skipped one.
    ranking = _ranking(team_count=2)
    profile = replace(
        ranking.profile,
        draft=replace(ranking.profile.draft, roster_limits={"QB": 2}),
    )
    ranking = replace(ranking, profile=profile)
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=9
    )

    picks = [
        {"player_id": "QB-0", "team_slot": 1, "position": "QB", "player_name": "QB 0"},
        {"player_id": "WR-0", "team_slot": 2, "position": "WR", "player_name": "WR 0"},
        {"player_id": "WR-1", "team_slot": 2, "position": "WR", "player_name": "WR 1"},
        {"player_id": "QB-1", "team_slot": 1, "position": "QB", "player_name": "QB 1"},
    ]
    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=1, picks=picks),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=40,
        trials=2, seasons=20, base_seed=9,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    positions = {c.player_id.split("-")[0] for c in result.candidates}
    assert "QB" not in positions  # already at the QB cap of 2


def test_build_live_decision_bundle_reports_unavailable_when_owner_slot_missing() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=1
    )

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=None),
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=1,
    )
    assert isinstance(result, LiveDecisionBundleUnavailable)
    assert "Owner slot" in result.reason


def test_build_live_decision_bundle_reports_unavailable_when_ranking_not_ready() -> None:
    profile = _ranking().profile
    unready = RankingResult(
        profile, (), (), (), "2026-08-17T00:00:00+00:00", "fixture", errors=("blocked",)
    )
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)

    result = build_live_decision_bundle(
        profile, unready, manual_assets, adp, _room_state(),
        comparable_leagues=[], provenance=_provenance(),
    )
    assert isinstance(result, LiveDecisionBundleUnavailable)
    assert "not ready" in result.reason


def test_build_live_decision_bundle_continues_the_real_room_not_an_empty_draft() -> None:
    """Regression: the look-ahead simulation (evaluate_pick_candidates ->
    simulate_pick_now) must continue from the REAL current room state, not
    silently restart an empty draft -- otherwise it can force a candidate
    that its own from-scratch simulation independently already "drafted"
    for another team, crashing with 'already drafted'. Reproduced here with
    a room that already has OTHER teams' real picks recorded (the exact
    shape that surfaced the bug in facade-level testing)."""
    ranking = _ranking(team_count=4)
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=11
    )
    # Owner drafts LAST in round 1 (slot 4), and the REAL room recorded
    # teams 1-3 making picks that DIVERGE from what a from-scratch
    # simulation's own deterministic-fallback CPU logic would independently
    # choose (e.g. team 1 taking a low-ranked player instead of the real
    # best-available QB-0) -- exactly the shape that reproduced the bug in
    # facade-level testing: without the real from_state, the simulation's
    # own from-empty CPU picks can collide with a candidate this function
    # legitimately selected from the REAL available pool.
    picks = [
        {"player_id": "TE-7", "team_slot": 1, "position": "TE", "player_name": "TE 7"},
        {"player_id": "WR-9", "team_slot": 2, "position": "WR", "player_name": "WR 9"},
        {"player_id": "RB-9", "team_slot": 3, "position": "RB", "player_name": "RB 9"},
    ]
    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=4, picks=picks),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=11,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    candidate_ids = {c.player_id for c in result.candidates}
    # Already-drafted players (by other teams) must never appear, and the
    # call must not raise -- proves the simulation is aware of the REAL
    # room's actual history, not an independently re-simulated one.
    assert candidate_ids.isdisjoint({"TE-7", "WR-9", "RB-9"})
    assert "QB-0" in candidate_ids  # the real best-available player, untouched


class _Row:
    """Minimal stand-in for a ranked-row object -- only `.player_id`/
    `.position` are read by diversify_candidate_shortlist, so a real
    RedraftRankingRow is unnecessary overhead for these pure-function
    tests."""

    def __init__(self, player_id: str, position: str):
        self.player_id = player_id
        self.position = position


def _row_ids(rows) -> list[str]:
    return [row.player_id for row in rows]


def test_diversify_candidate_shortlist_breaks_up_a_qb_heavy_rank_slice() -> None:
    # Owner-test follow-up: reproduces the real complaint verbatim -- 7 of
    # 8 real Suggestions candidates were QBs because the top of the rank
    # order happened to cluster QB value. This exact shape (8 QBs, THEN
    # everything else) is what a naive legal_rows[:max_candidates] slice
    # would return unchanged.
    rows = [_Row(f"QB-{i}", "QB") for i in range(8)]
    rows += [_Row(f"RB-{i}", "RB") for i in range(8)]
    rows += [_Row(f"WR-{i}", "WR") for i in range(8)]
    rows += [_Row(f"TE-{i}", "TE") for i in range(8)]
    selected = diversify_candidate_shortlist(rows, max_candidates=8)
    positions = [row.position for row in selected]
    # Round 2 of this fix: a hard per-position domination cap (60% of
    # max_candidates, so 4 of 8 here) replaced the original round-robin's
    # implicit ~2-per-position ceiling -- deliberately loosened so a
    # genuinely deep, needed position isn't capped at exactly one extra
    # slot (see the "superior third WR" owner complaint this same pass
    # fixed). The real bug this guards against was 7 of 8 (87.5%); 4 of 8
    # (50%) is a real, intentional improvement, not the original bound.
    assert positions.count("QB") <= 4, f"expected QB coverage, not the original 7-of-8 domination: {positions}"
    assert set(positions) >= {"QB", "RB", "WR", "TE"}, "every core position should get a comparison point"


def test_diversify_candidate_shortlist_always_keeps_the_single_best_overall_candidate() -> None:
    rows = [_Row(f"QB-{i}", "QB") for i in range(5)]
    selected = diversify_candidate_shortlist(rows, max_candidates=3)
    assert selected[0].player_id == "QB-0"


def test_diversify_candidate_shortlist_preserves_real_depth_at_one_position() -> None:
    # A genuine run on RB (RB truly is the deepest, best-ranked position
    # right now) must still be allowed to fill most of the slate -- this
    # is NOT "mechanically force exactly one player per position".
    rows = [_Row(f"RB-{i}", "RB") for i in range(6)]
    rows += [_Row("WR-0", "WR"), _Row("QB-0", "QB"), _Row("TE-0", "TE")]
    selected = diversify_candidate_shortlist(rows, max_candidates=6)
    positions = [row.position for row in selected]
    assert positions.count("RB") >= 3, f"legitimate RB depth should not be discarded: {positions}"
    assert set(positions) >= {"RB", "WR", "QB", "TE"}


def test_diversify_candidate_shortlist_does_not_force_a_backup_at_an_unneeded_position() -> None:
    # Owner-test follow-up, round 2: the real reported regression -- TE is
    # already filled (no remaining starter/FLEX need), so a legal-but-
    # unneeded backup TE must not be forced into the slate just to satisfy
    # a coverage quota. QB/RB/WR are genuinely needed here and should get
    # real coverage; TE should NOT unless it is independently top-ranked.
    rows = [_Row("QB-0", "QB"), _Row("RB-0", "RB"), _Row("RB-1", "RB"), _Row("WR-0", "WR")]
    rows += [_Row(f"TE-{i}", "TE") for i in range(4)]  # ranked below the needed positions
    selected = diversify_candidate_shortlist(rows, max_candidates=4, needed_positions=frozenset({"QB", "RB", "WR"}))
    positions = [row.position for row in selected]
    assert "TE" not in positions, f"an unneeded backup TE should not be forced into a full slate: {positions}"


def test_diversify_candidate_shortlist_still_allows_an_unneeded_position_if_it_independently_ranks_well() -> None:
    # The fix is "don't force a quota slot", never "exclude a position
    # outright" -- an unneeded TE that is still the objectively best
    # remaining option (nothing else left to fill the slate) must appear.
    rows = [_Row("QB-0", "QB"), _Row("TE-0", "TE"), _Row("TE-1", "TE")]
    selected = diversify_candidate_shortlist(rows, max_candidates=3, needed_positions=frozenset({"QB"}))
    assert {row.player_id for row in selected} == {"QB-0", "TE-0", "TE-1"}


def test_diversify_candidate_shortlist_needed_positions_none_falls_back_to_covering_everything() -> None:
    # Backward-compatible default (no needed_positions supplied) -- callers
    # that haven't computed real roster need yet still get the original
    # "cover every core position" behavior, never a crash or empty pane.
    rows = [_Row(f"QB-{i}", "QB") for i in range(4)] + [_Row("RB-0", "RB"), _Row("WR-0", "WR"), _Row("TE-0", "TE")]
    selected = diversify_candidate_shortlist(rows, max_candidates=4)
    positions = {row.position for row in selected}
    assert positions == {"QB", "RB", "WR", "TE"}


def test_diversify_candidate_shortlist_never_invents_or_drops_a_row() -> None:
    rows = [_Row(f"WR-{i}", "WR") for i in range(4)]
    selected = diversify_candidate_shortlist(rows, max_candidates=10)
    assert _row_ids(selected) == _row_ids(rows)  # fewer legal rows than the cap -> return them all, untouched


def test_diversify_candidate_shortlist_returns_empty_for_no_legal_rows() -> None:
    assert diversify_candidate_shortlist([], max_candidates=8) == []


def test_build_live_decision_bundle_does_not_let_qb_dominate_suggestions_early_mid_late_draft() -> None:
    """Owner-test follow-up, section 3: reproduces the real-world shape
    (a QB-clustered top-of-rank-order pool, matching this fixture's own
    `_ranking()` layout of QB ranks 1-8) across early/middle/late 1QB
    draft states and asserts Suggestions is never QB-dominated."""
    # team_count=6/rounds=8 (this file's own default _ranking() shape) --
    # 48 total picks fits comfortably inside the 60-skill-player fixture
    # pool a larger team_count x rounds combination would exhaust.
    ranking = _ranking(team_count=6, rounds=8)
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=2, base_seed=21)

    order = draft_order(profile)
    # Real snake order (owner_slot=1 picks FIRST, then LAST in round 2,
    # first again in round 3, ...) -- the Nth owner turn is not simply
    # N * team_count picks in, so find each owner-turn pick INDEX
    # directly from the real draft_order() rather than assuming a
    # uniform round-count offset.
    owner_turn_indices = [index for index, slot in enumerate(order) if slot == 1]

    def _picks_up_to(pick_index: int) -> list[dict]:
        # Real picks for every pick strictly before `pick_index`: the
        # owner's own prior turns take RB (building a real, growing
        # roster), every other team takes WR filler -- leaving the QB
        # pool this test cares about completely untouched.
        picks: list[dict] = []
        wr_index = 0
        owner_round = 0
        for index in range(pick_index):
            team_slot = order[index]
            if team_slot == 1:
                picks.append({"player_id": f"RB-{owner_round}", "team_slot": team_slot, "position": "RB", "player_name": f"RB {owner_round}"})
                owner_round += 1
            else:
                picks.append({"player_id": f"WR-{wr_index}", "team_slot": team_slot, "position": "WR", "player_name": f"WR {wr_index}"})
                wr_index += 1
        return picks

    for label, turn in (("early", owner_turn_indices[0]), ("middle", owner_turn_indices[1]), ("late", owner_turn_indices[2])):
        picks = _picks_up_to(turn)
        result = build_live_decision_bundle(
            profile, ranking, manual_assets, adp,
            _room_state(owner_slot=1, picks=picks),
            comparable_leagues=leagues, provenance=_provenance(), max_candidates=8,
            trials=2, seasons=20, base_seed=21,
        )
        assert not isinstance(result, LiveDecisionBundleUnavailable), label
        positions = [c.player_id.split("-")[0] for c in result.candidates]
        # See the domination-cap comment in the pure-function test above --
        # 4 of 8 (50%) is the intentional new bound, a real improvement on
        # the original 7-of-8 bug, not a stricter target than designed.
        assert positions.count("QB") <= 4, f"{label} draft state: QB-dominated slate {positions}"


def test_position_filter_returns_real_eligible_players_of_that_position_only() -> None:
    """Owner-test follow-up, section 8: an explicit position filter must
    draw from the REAL eligible pool of that position -- never a client-
    side re-filter of the default top-N slice, which could falsely report
    "no candidates" for a position simply absent from that slice. Uses
    this file's own _ranking() fixture, where the default top-8 rank
    slice is QB-only (ranks 1-8) -- filtering to WR here would return
    nothing under the old "re-filter the shortlist" approach, but must
    return real WR candidates under the fix."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=2, base_seed=31)

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=31, position_filter="WR",
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    assert len(result.candidates) == 5
    assert all(c.player_id.startswith("WR-") for c in result.candidates)


def test_default_shortlist_uses_canonical_feasibility_for_kdst_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When two picks remain and K/DST are the only missing mandatory slots,
    the canonical service excludes every skill player while keeping both
    honest manual choices. No fixed-round or arbitrary K-before-DST rule is
    involved."""
    ranking = _ranking(team_count=2, rounds=9)
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    order = draft_order(profile)
    # Team 1's starter slots (QB1/RB2/WR2/TE1/FLEX-via-extra-RB) filled by
    # its own first 7 picks -- K and DST are both still 0/1, with exactly
    # two picks remaining.
    team1_players = ["QB-0", "RB-0", "RB-1", "RB-2", "WR-0", "WR-1", "TE-0"]
    picks = []
    t1_index = 0
    pick_number = 0
    while t1_index < len(team1_players):
        team_slot = order[pick_number]
        pick_number += 1
        if team_slot == 1:
            player_id = team1_players[t1_index]
            t1_index += 1
        else:
            player_id = f"WR-{10 + pick_number}"
        picks.append(
            {"pickNumber": pick_number, "teamSlot": team_slot, "team_slot": team_slot,
             "playerId": player_id, "player_id": player_id,
             "position": player_id.split("-")[0]}
        )
    # Consume any remaining non-owner turns before the owner's own next
    # turn genuinely arrives (snake order can give a team two turns in a
    # row across a round boundary) -- never leave the fixture claiming a
    # turn that isn't really next.
    while order[pick_number] != 1:
        pick_number += 1
        filler = f"WR-{10 + pick_number}"
        picks.append(
            {"pickNumber": pick_number, "teamSlot": order[pick_number - 1],
             "team_slot": order[pick_number - 1], "playerId": filler, "player_id": filler,
             "position": "WR"}
        )
    room_state = _room_state(owner_slot=1, picks=picks)
    positions_by_id = {
        str(asset["player_id"]): str(asset["position"])
        for asset in manual_assets
    }

    def capture_candidates(**kwargs: object) -> SimpleNamespace:
        candidate_ids = kwargs["candidate_player_ids"]
        assert isinstance(candidate_ids, list)
        return SimpleNamespace(
            candidates=tuple(
                SimpleNamespace(player_id=player_id, position=positions_by_id[player_id])
                for player_id in candidate_ids
            )
        )

    monkeypatch.setattr(
        "src.services.decision_bundle_live_service.build_decision_bundle",
        capture_candidates,
    )

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, room_state,
        comparable_leagues=(), provenance=_provenance(), max_candidates=8,
        trials=2, seasons=20, base_seed=17,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable), result
    assert len(result.candidates) > 0
    positions = {c.position for c in result.candidates}
    assert positions == {"K", "DST"}


def test_position_filter_of_k_returns_real_manual_candidates_not_empty() -> None:
    """NWR OVERNIGHT (K/DST completion): before this fix, an explicit K or
    DST filter always reported "no candidates" -- `legal_rows` is built
    from `ranking.rows`, which structurally never contains K/DST (they
    exist only in `manual_assets`, NWR has no model for them). The filter
    must draw from the real manual pool instead."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=2, base_seed=41)

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=41, position_filter="K",
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    assert len(result.candidates) > 0
    assert all(c.player_id.startswith("manual:K:") for c in result.candidates)
    # Never a fabricated NWR score for an unmodeled position.
    assert all(c.player_score is None for c in result.candidates)


def test_position_filter_of_all_behaves_like_no_filter() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=2, base_seed=33)

    filtered = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=33, position_filter="ALL",
    )
    unfiltered = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=33, position_filter=None,
    )
    assert not isinstance(filtered, LiveDecisionBundleUnavailable)
    assert not isinstance(unfiltered, LiveDecisionBundleUnavailable)
    assert {c.player_id for c in filtered.candidates} == {c.player_id for c in unfiltered.candidates}


def test_position_filter_flex_returns_real_flex_eligible_positions_only() -> None:
    """Owner feedback closure, section 9: FLEX means the league's real
    FLEX-eligible positions (RB/WR/TE) -- no candidate row's `position`
    is ever literally "FLEX", so a naive exact-match filter would falsely
    report zero candidates for a real, legal request."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=2, base_seed=41)

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=41, position_filter="FLEX",
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    assert len(result.candidates) == 5
    assert all(c.player_id.split("-")[0] in {"RB", "WR", "TE"} for c in result.candidates)


def test_position_filter_sflx_unavailable_without_a_configured_superflex_slot() -> None:
    """A league that does not configure Superflex must never silently
    treat an SFLX request as ordinary FLEX or fabricate candidates for a
    slot the league does not have."""
    ranking = _ranking()
    profile = ranking.profile
    assert profile.roster.superflex == 0
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=2, base_seed=43)

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=43, position_filter="SFLX",
    )
    assert isinstance(result, LiveDecisionBundleUnavailable)


def test_position_filter_sflx_returns_real_superflex_eligible_positions_when_configured() -> None:
    ranking = _ranking()
    profile = replace(ranking.profile, roster=replace(ranking.profile.roster, superflex=1))
    ranking = replace(ranking, profile=profile)
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=2, base_seed=47)

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=47, position_filter="SFLX",
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    assert len(result.candidates) == 5
    assert all(c.player_id.split("-")[0] in {"QB", "RB", "WR", "TE"} for c in result.candidates)
