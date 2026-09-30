from src.services.dynasty_waiver_service import (
    age_upside_bonus,
    dynasty_waiver_priority_score,
    rank_dynasty_waiver_candidates,
    stash_value_band,
    suggest_dynasty_faab_range,
)


def _row(player_id, name, position, score, rank, age, *, status=None):
    return {
        "asset_id": f"current:{player_id}",
        "asset_name": name,
        "position": position,
        "team": "SF",
        "nwr_dynasty_score": score,
        "dynasty_rank": rank,
        "age": age,
        "current_status_override": status,
    }


def test_age_and_stash_formulas_are_deterministic_and_bounded() -> None:
    assert age_upside_bonus(21.0) == (3.0, "HIGH")
    assert age_upside_bonus(24.0) == (2.0, "HIGH")
    assert age_upside_bonus(26.0) == (1.0, "MEDIUM")
    assert age_upside_bonus(29.0) == (-1.0, "LOW")
    assert age_upside_bonus(None) == (0.0, "UNKNOWN")
    assert stash_value_band(dynasty_score=18.0, age=23.0) == "HIGH"
    assert stash_value_band(dynasty_score=10.0, age=27.0) == "MEDIUM"
    assert stash_value_band(dynasty_score=7.9, age=21.0) == "LOW"


def test_priority_formula_preserves_source_score_and_penalizes_known_season_out() -> None:
    assert (
        dynasty_waiver_priority_score(
            dynasty_score=20.0, age_bonus=2.0, roster_fit_bonus=3.0, status_kind=""
        )
        == 25.0
    )
    assert (
        dynasty_waiver_priority_score(
            dynasty_score=20.0,
            age_bonus=2.0,
            roster_fit_bonus=3.0,
            status_kind="SEASON_OUT",
        )
        == 20.0
    )


def test_dynasty_faab_formula_never_prices_unknown_or_nonpositive_net() -> None:
    assert suggest_dynasty_faab_range(
        remaining_budget=None,
        percentile=1.0,
        transaction_net_value=10.0,
        stash_value="HIGH",
        roster_fit="ROSTER_UPGRADE",
    ) == (None, None, "LIVE_FAAB_BALANCE_UNAVAILABLE")
    assert suggest_dynasty_faab_range(
        remaining_budget=80,
        percentile=1.0,
        transaction_net_value=0.0,
        stash_value="HIGH",
        roster_fit="ROSTER_UPGRADE",
    ) == (0, 0, "NONPOSITIVE_OR_UNKNOWN_TRANSACTION_NET")


def test_dynasty_faab_formula_uses_remaining_budget_and_caps_range() -> None:
    low, high, reason = suggest_dynasty_faab_range(
        remaining_budget=80,
        percentile=1.0,
        transaction_net_value=10.0,
        stash_value="HIGH",
        roster_fit="STARTER_NEED",
    )
    assert (low, high, reason) == (12, 23, "RELATIVE_DYNASTY_HEURISTIC")
    assert 0 <= low <= high <= round(80 * 0.35)


def test_ranking_excludes_every_rostered_player_and_unsupported_position() -> None:
    rows = [
        _row("owned", "Owned Star", "WR", 30, 1, 23),
        _row("free", "Free Stash", "WR", 18, 50, 22),
        _row("dst", "Defense", "DST", 40, 2, None),
    ]
    result = rank_dynasty_waiver_candidates(
        asset_rows=rows,
        all_rostered_player_ids=["owned"],
        owner_roster_status_by_player_id={"owned": "STARTER"},
        roster_positions=["QB", "RB", "WR", "TE", "FLEX", "BN"],
        remaining_faab_budget=100,
        open_active_roster_slot=True,
    )
    assert [row.sleeper_player_id for row in result] == ["free"]
    assert result[0].drop_candidate is None
    assert result[0].drop_required is False


def test_ranking_protects_starters_reserve_and_taxi_from_drop_recommendations() -> None:
    rows = [
        _row("starter", "Starter", "WR", 3, 200, 29),
        _row("reserve", "Reserve", "RB", 2, 210, 25),
        _row("taxi", "Taxi", "WR", 1, 220, 21),
        _row("bench", "Bench", "TE", 5, 190, 28),
        _row("free", "Free Agent", "WR", 20, 80, 23),
    ]
    result = rank_dynasty_waiver_candidates(
        asset_rows=rows,
        all_rostered_player_ids=["starter", "reserve", "taxi", "bench"],
        owner_roster_status_by_player_id={
            "starter": "STARTER",
            "reserve": "RESERVE",
            "taxi": "TAXI",
            "bench": "BENCH",
        },
        roster_positions=["QB", "RB", "WR", "TE", "FLEX", "BN"],
        remaining_faab_budget=100,
        open_active_roster_slot=False,
    )
    assert result[0].drop_candidate is not None
    assert result[0].drop_candidate.player_name == "Bench"
    assert result[0].transaction_net_value == 15.0


def test_ranking_is_stable_and_dynasty_value_is_primary_context() -> None:
    rows = [
        _row("older", "Older Value", "WR", 22, 70, 28),
        _row("young", "Young Stash", "WR", 20, 80, 21),
    ]
    kwargs = dict(
        asset_rows=rows,
        all_rostered_player_ids=[],
        owner_roster_status_by_player_id={},
        roster_positions=["WR", "BN"],
        remaining_faab_budget=100,
        open_active_roster_slot=True,
    )
    first = rank_dynasty_waiver_candidates(**kwargs)
    second = rank_dynasty_waiver_candidates(**kwargs)
    assert first == second
    assert [row.player_name for row in first] == ["Young Stash", "Older Value"]
    assert first[0].dynasty_score == 20.0
    assert first[0].priority_score == 27.0


def test_flex_slot_is_not_double_counted_as_a_need_for_every_position() -> None:
    rows = [
        _row("rb1", "RB One", "RB", 30, 10, 24),
        _row("rb2", "RB Two", "RB", 25, 20, 25),
        _row("rb3", "RB Three", "RB", 15, 80, 26),
        _row("free", "Free Back", "RB", 18, 60, 23),
    ]
    result = rank_dynasty_waiver_candidates(
        asset_rows=rows,
        all_rostered_player_ids=["rb1", "rb2", "rb3"],
        owner_roster_status_by_player_id={
            "rb1": "STARTER",
            "rb2": "STARTER",
            "rb3": "BENCH",
        },
        roster_positions=["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN"],
        remaining_faab_budget=100,
        open_active_roster_slot=False,
    )

    assert result[0].roster_fit == "DEPTH_NEED"
    assert "2 eligible starting slot(s)" in result[0].roster_fit_reason
