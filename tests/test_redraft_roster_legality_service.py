from __future__ import annotations

from collections import Counter
from dataclasses import replace

from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from tests.fixtures.test18_redraft_fixture import make_test18_profile


def test_configured_position_maximum_is_enforced_without_named_player_logic() -> None:
    profile = make_test18_profile(wr_maximum=8)

    result = evaluate_draft_pick_legality(profile, Counter({"WR": 8}), "WR")

    assert result.allowed is False
    assert result.code == "POSITION_MAXIMUM_REACHED"
    assert result.position_maximum == 8


def test_unknown_position_maximum_does_not_invent_a_qb_or_te_cap() -> None:
    profile = make_test18_profile(wr_maximum=None)

    assert evaluate_draft_pick_legality(profile, Counter({"QB": 2}), "QB").allowed
    assert evaluate_draft_pick_legality(profile, Counter({"TE": 2}), "TE").allowed


def test_remaining_picks_preserve_a_path_to_mandatory_k_and_dst_slots() -> None:
    profile = make_test18_profile(wr_maximum=8)
    at_round_14 = Counter({"WR": 8, "QB": 2, "RB": 2, "TE": 1})
    assert evaluate_draft_pick_legality(profile, at_round_14, "QB").allowed

    at_round_15 = at_round_14 + Counter({"QB": 1})
    blocked = evaluate_draft_pick_legality(profile, at_round_15, "RB")
    assert blocked.allowed is False
    assert blocked.code == "MANDATORY_SLOTS_WOULD_BE_UNFILLABLE"
    assert evaluate_draft_pick_legality(profile, at_round_15, "K").allowed
    assert evaluate_draft_pick_legality(profile, at_round_15, "DST").allowed


def test_flex_and_superflex_players_satisfy_their_real_shared_slots() -> None:
    base = make_test18_profile(wr_maximum=None)
    profile = replace(
        base,
        roster=replace(base.roster, flex=1, superflex=1, k=0, dst=0),
        draft=replace(base.draft, rounds=9),
    )
    fixed = Counter({"QB": 1, "RB": 2, "WR": 2, "TE": 1})

    after_flex = evaluate_draft_pick_legality(profile, fixed, "WR")
    after_superflex = evaluate_draft_pick_legality(profile, fixed + Counter({"WR": 1}), "QB")

    assert after_flex.mandatory_slots_open_after == 1
    assert after_superflex.mandatory_slots_open_after == 0


def test_dst_aliases_use_the_same_configured_maximum() -> None:
    base = make_test18_profile(wr_maximum=None)
    profile = replace(base, draft=replace(base.draft, roster_limits={"DST": 1}))

    result = evaluate_draft_pick_legality(profile, Counter({"D/ST": 1}), "DEF")

    assert result.allowed is False
    assert result.position == "DST"
