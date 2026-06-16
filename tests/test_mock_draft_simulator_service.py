from __future__ import annotations

from src.services.draft_state_service import create_empty_draft_state
from src.services.mock_draft_simulator_service import build_review_mock_draft_scenario


def _pick_rows(my_picks: set[int] | None = None) -> list[dict[str, object]]:
    my_picks = my_picks or set()
    rows: list[dict[str, object]] = []
    for overall_pick in range(1, 11):
        rows.append(
            {
                "overall_pick": overall_pick,
                "round": 1,
                "round_pick": overall_pick,
                "pick_label": f"1.{overall_pick:02d}",
                "current_owner": "Niners" if overall_pick in my_picks else "Opponent",
                "original_owner": "Niners" if overall_pick in my_picks else "Opponent",
                "is_my_pick": overall_pick in my_picks,
            }
        )
    return rows


def _available_rows() -> list[dict[str, object]]:
    return [
        {
            "asset_id": "rookie:alpha_wr",
            "player": "Alpha WR",
            "position": "WR",
            "nfl_team": "Rookie Pool",
            "asset_type": "Rookie",
            "asset_lifecycle": "incoming_rookie",
            "stats_model_value": 91.0,
            "market_value": 0.0,
            "market_edge": 0.0,
            "confidence": 88.0,
            "overall_rank": 1,
        },
        {
            "asset_id": "released_veteran:steady_wr",
            "player": "Steady Released WR",
            "position": "WR",
            "nfl_team": "FA",
            "asset_type": "Released Veteran",
            "asset_lifecycle": "dropped_veteran",
            "why_available": "Dropped on declaration day.",
            "stats_model_value": 74.0,
            "market_value": 0.0,
            "market_edge": 0.0,
            "confidence": 80.0,
            "overall_rank": 5,
        },
        {
            "asset_id": "free_agent:bench_rb",
            "player": "Bench RB",
            "position": "RB",
            "nfl_team": "FA",
            "asset_type": "Free Agent",
            "asset_lifecycle": "free_agent",
            "stats_model_value": 69.0,
            "market_value": 0.0,
            "market_edge": 0.0,
            "confidence": 70.0,
            "overall_rank": 7,
        },
    ]


def test_review_mock_scenario_uses_full_rookie_and_available_veteran_pool() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({4}),
        available_rows=_available_rows(),
    )

    scenario = build_review_mock_draft_scenario(
        state,
        market_context_rows=[
            {
                "asset_id": "released_veteran:steady_wr",
                "player": "Steady Released WR",
                "market_adp": 1.2,
            },
            {"asset_id": "free_agent:bench_rb", "player": "Bench RB", "market_adp": 2.1},
            {"asset_id": "rookie:alpha_wr", "player": "Alpha WR", "market_adp": 6.0},
        ],
    )

    assert scenario.review_only is True
    assert scenario.starting_current_pick == 1
    assert scenario.ending_current_pick == 4
    assert [row.asset_type for row in scenario.simulated_picks] == [
        "Released Veteran",
        "Free Agent",
        "Rookie",
    ]
    assert scenario.simulated_picks[0].selected_by == "opponent_market_timing"
    assert scenario.quality_score_firewall_passed is True
    assert "ADP/market context is used only for opponent timing" in (
        scenario.market_context_policy
    )


def test_adp_context_never_changes_nwr_quality_or_value_fields() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({2}),
        available_rows=_available_rows(),
    )

    scenario = build_review_mock_draft_scenario(
        state,
        market_context_rows=[
            {
                "asset_id": "released_veteran:steady_wr",
                "player": "Steady Released WR",
                "market_adp": 1.0,
                "stats_model_value": 1.0,
                "draft_value": 1.0,
                "nwr_quality_score": 1.0,
            }
        ],
    )

    selected = scenario.simulated_picks[0]

    assert selected.player == "Steady Released WR"
    assert selected.stats_model_value == 74.0
    assert scenario.state_after_simulation.drafted_players[0].stats_model_value == 74.0
    assert scenario.quality_score_firewall_passed is True
    assert any("Ignored market context score/value fields" in row for row in scenario.warnings)
    assert any("draft_value" in row and "stats_model_value" in row for row in scenario.warnings)


def test_scenario_stops_before_my_pick_and_reports_availability() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({1}),
        available_rows=_available_rows(),
    )

    scenario = build_review_mock_draft_scenario(
        state,
        market_context_rows=[
            {"asset_id": "rookie:alpha_wr", "player": "Alpha WR", "market_adp": 1.0}
        ],
    )

    assert scenario.simulated_picks == ()
    assert scenario.ending_current_pick == 1
    assert scenario.availability_at_my_next_pick[0]["player"] == "Alpha WR"
    assert scenario.availability_at_my_next_pick[0]["market_context_used"] is True
    assert scenario.availability_at_my_next_pick[0]["nwr_score_status"] == (
        "unchanged_from_input"
    )


def test_fallback_board_order_is_review_only_when_no_market_context_is_in_range() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({2}),
        available_rows=_available_rows(),
    )

    scenario = build_review_mock_draft_scenario(
        state,
        market_context_rows=[
            {
                "asset_id": "released_veteran:steady_wr",
                "player": "Steady Released WR",
                "market_adp": 50.0,
            }
        ],
        opponent_lookahead=2,
    )

    assert scenario.simulated_picks[0].player == "Alpha WR"
    assert scenario.simulated_picks[0].selected_by == "fallback_board_order"
    assert "review only" in scenario.simulated_picks[0].selection_reason
