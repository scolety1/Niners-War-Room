from __future__ import annotations

import csv
from pathlib import Path

from src.services.draft_state_service import create_empty_draft_state
from src.services.mock_draft_combined_state_service import CombinedSimulatorState
from src.services.mock_draft_run_report_service import build_mock_draft_run_report
from src.services.mock_draft_simulator_service import build_review_mock_draft_scenario

FIXTURE_PATH = Path("tests/fixtures/mock_draft/fake_market_timing_rows.csv")


def _fake_market_rows() -> list[dict[str, str]]:
    with FIXTURE_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _pick_rows(my_picks: set[int] | None = None) -> list[dict[str, object]]:
    my_picks = my_picks or set()
    return [
        {
            "overall_pick": overall_pick,
            "round": 1,
            "round_pick": overall_pick,
            "pick_label": f"1.{overall_pick:02d}",
            "current_owner": "Niners" if overall_pick in my_picks else "Opponent",
            "original_owner": "Niners" if overall_pick in my_picks else "Opponent",
            "is_my_pick": overall_pick in my_picks,
        }
        for overall_pick in range(1, 4)
    ]


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


def _combined_state_for_run_report() -> CombinedSimulatorState:
    return CombinedSimulatorState(
        review_only=True,
        available_rows=(
            {
                "asset_id": "frozen_rookie:alpha:rank1",
                "player": "Alpha Rookie",
                "position": "RB",
                "source_label": "frozen_rookie",
                "draft_rank": 1,
                "stats_model_value": 0.0,
                "rank": "1",
                "tier": "Tier 1",
                "draft_action": "priority_review",
                "warning_severity": "green",
                "draft_room_note": "Frozen note",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
            },
            {
                "asset_id": "rookie:beta_wr",
                "player": "Beta Rookie",
                "position": "WR",
                "source_label": "frozen_rookie",
                "draft_rank": 2,
                "stats_model_value": 0.0,
                "rank": "2",
                "tier": "Tier 2",
                "draft_action": "manual_review",
                "warning_severity": "yellow",
                "draft_room_note": "Frozen second note",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
            },
            {
                "asset_id": "free_agent:bench_rb",
                "player": "Bench RB",
                "position": "RB",
                "source_label": "free_agent",
                "draft_rank": 115,
                "stats_model_value": 0.0,
                "rank": "",
                "tier": "",
                "draft_action": "",
                "warning_severity": "",
                "draft_room_note": "",
                "review_flags": "value_neutral|free_agent",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
            },
        ),
        pick_rows=(
            {
                "overall_pick": 1,
                "round": 1,
                "round_pick": 1,
                "pick_label": "1.01",
                "current_owner": "Other",
                "manager": "Other Manager",
                "is_my_pick": False,
            },
            {
                "overall_pick": 2,
                "round": 1,
                "round_pick": 2,
                "pick_label": "1.02",
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "is_my_pick": True,
            },
        ),
        draft_state=None,
        manifest={},
        review_flags={},
        source_counts={"frozen_rookie": 2, "free_agent": 1},
        artifact_paths={},
    )


def test_fake_market_fixture_is_behavior_only_and_ignores_score_fields() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({3}),
        available_rows=_available_rows(),
    )

    scenario = build_review_mock_draft_scenario(
        state,
        market_context_rows=_fake_market_rows(),
        opponent_lookahead=2,
    )

    selected = scenario.simulated_picks[0]
    assert selected.player == "Steady Released WR"
    assert selected.selected_by == "opponent_market_timing"
    assert selected.stats_model_value == 74.0
    assert selected.opponent_timing_score > 0
    assert scenario.quality_score_firewall_passed is True
    assert any("Ignored market context score/value fields" in row for row in scenario.warnings)
    assert any("nwr_quality_score" in row for row in scenario.warnings)


def test_market_timing_cannot_overwrite_rookie_guidance_or_create_nwr_score() -> None:
    report = build_mock_draft_run_report(
        _combined_state_for_run_report(),
        market_context_rows=_fake_market_rows(),
        shortlist_size=3,
        opponent_lookahead=2,
    )

    beta = next(row for row in report.tim_shortlist_rows if row["player"] == "Beta Rookie")
    assert beta["rank"] == "2"
    assert beta["tier"] == "Tier 2"
    assert beta["draft_action"] == "manual_review"
    assert beta["warning_severity"] == "yellow"
    assert beta["stats_model_value"] == 0.0
    assert beta["nwr_score_status"] == "no_numeric_score_exposed_guidance_only"
    assert beta["market_context_used"] is False
    assert "No numeric NWR score is invented" in report.manifest["nwr_score_policy"]


def test_missing_market_timing_rows_fall_back_without_removing_value_neutral_flags() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({3}),
        available_rows=_available_rows(),
    )

    scenario = build_review_mock_draft_scenario(
        state,
        market_context_rows=[
            {
                "asset_id": "free_agent:bench_rb",
                "player": "Bench RB",
                "review_flags": "market_timing_missing_pick_value_review_required",
            }
        ],
        opponent_lookahead=1,
    )

    selected = scenario.simulated_picks[0]
    assert selected.player == "Alpha WR"
    assert selected.selected_by == "fallback_board_order"
    assert "review only" in selected.selection_reason
    assert scenario.quality_score_firewall_passed is True

    report = build_mock_draft_run_report(
        _combined_state_for_run_report(),
        market_context_rows=[
            {
                "asset_id": "free_agent:bench_rb",
                "player": "Bench RB",
                "review_flags": "market_timing_missing_pick_value_review_required",
            }
        ],
        shortlist_size=3,
        opponent_lookahead=1,
    )
    free_agent = next(row for row in report.tim_shortlist_rows if row["player"] == "Bench RB")
    assert free_agent["value_status"] == "value_neutral"
    assert "value_neutral" in str(free_agent["review_flags"])
    assert free_agent["stats_model_value"] == 0.0
