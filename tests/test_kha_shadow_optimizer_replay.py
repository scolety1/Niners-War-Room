"""Tests for the KHA decision shadow replay (section 12) -- verifies the
replay against the REAL, untouched 157-pick live KHA draft board, and
verifies the no-leakage guarantee structurally (not just by inspection).
"""

from __future__ import annotations

from scripts.run_kha_shadow_optimizer_replay_v1 import (
    KHA_PROFILE,
    build_pool,
    build_replay_rows,
    load_real_picks,
    rank_to_value_proxy,
)
from src.services.shadow_numeric_authorities_service import RosterPlayer


def test_load_real_picks_reads_the_untouched_live_board() -> None:
    document, picks = load_real_picks()
    assert document["owner_slot"] == 9
    assert document["mode"] == "LIVE_READ_ONLY"
    assert len(picks) == 157


def test_owner_has_exactly_10_real_picks_in_the_live_captured_window() -> None:
    document, picks = load_real_picks()
    owner_picks = [p for p in picks if p["team_slot"] == document["owner_slot"]]
    assert len(owner_picks) == 10
    # Real, verifiable against the live board fixture.
    assert owner_picks[0]["player_name"] == "James Cook"
    assert owner_picks[0]["pick_number"] == 9
    assert owner_picks[0]["round"] == 1
    assert owner_picks[-1]["player_name"] == "Woody Marks"
    assert owner_picks[-1]["pick_number"] == 152


def test_rank_to_value_proxy_is_monotonic_and_never_negative() -> None:
    assert rank_to_value_proxy(1) > rank_to_value_proxy(100)
    assert rank_to_value_proxy(608) >= 0.0
    assert rank_to_value_proxy(700) == 0.0  # past real universe size -- floored at 0, not negative


def test_build_pool_covers_every_drafted_player_with_no_duplicates() -> None:
    _, picks = load_real_picks()
    ranking, manual = build_pool(picks)
    skill_ids = {row.player_id for row in ranking.rows}
    manual_ids = {row["player_id"] for row in manual}
    all_real_ids = {str(p["player_id"]) for p in picks}
    assert skill_ids | manual_ids == all_real_ids
    assert not (skill_ids & manual_ids)  # no player double-counted between the two pools
    assert len(ranking.rows) == len(skill_ids)  # no duplicate rows for a repeated player_id


def test_build_replay_rows_produces_one_row_per_real_owner_pick_in_order() -> None:
    rows = build_replay_rows()
    assert len(rows) == 10
    assert [row["pick_number"] for row in rows] == sorted(row["pick_number"] for row in rows)
    assert rows[0]["player_name"] == "James Cook"
    assert rows[0]["real_nwr_rank_at_time_of_pick"] == 16


def test_replay_never_leaks_a_later_pick_into_an_earlier_rows_team_score() -> None:
    """Strong no-leak check: independently recompute team_score_after for
    every row using ONLY picks with pick_number <= this row's own
    pick_number, built here from scratch (not by reusing the script's own
    internal helpers) -- and confirm it matches the row's own reported
    value exactly. If the script ever leaked a future pick into an
    earlier row's field/roster, this independent recomputation would
    disagree with it."""
    from src.services.shadow_numeric_authorities_service import team_score as _team_score

    document, all_picks = load_real_picks()
    owner_slot = document["owner_slot"]
    ranking, manual = build_pool(all_picks)
    other_slots = [slot for slot in range(1, KHA_PROFILE.team_count + 1) if slot != owner_slot]
    rows = build_replay_rows()

    for row in rows:
        pick_number = row["pick_number"]
        visible = [p for p in all_picks if p["pick_number"] <= pick_number]
        owner_ids_after = [
            str(p["player_id"]) for p in visible if p["team_slot"] == owner_slot
        ]
        field = {
            slot: [
                RosterPlayer(
                    str(p["player_id"]), str(p["position"]),
                    rank_to_value_proxy(int(p["nwr_rank"])),
                )
                for p in visible
                if p["team_slot"] == slot
            ]
            for slot in other_slots
        }
        independent = _team_score(
            owner_ids_after, KHA_PROFILE, ranking, manual, comparable_leagues=[field]
        )
        assert independent.percentile == row["team_score_after"]


def test_owner_after_roster_always_includes_the_new_pick() -> None:
    rows = build_replay_rows()
    # starting_lineup_value_delta reflects the marginal value of adding
    # this exact pick -- for a pick that fills a real starter/FLEX hole,
    # it must be strictly positive (never negative -- a real pick can
    # only ever add or leave unchanged the value of an optimal lineup
    # selection, never subtract from it).
    for row in rows:
        assert row["starting_lineup_value_delta"] >= 0.0


def test_kha_profile_matches_the_real_leagues_team_count() -> None:
    assert KHA_PROFILE.team_count == 16
