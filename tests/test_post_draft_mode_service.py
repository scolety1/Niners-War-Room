from __future__ import annotations

import pandas as pd

from src.services.draft_day_runtime_state_service import (
    empty_runtime_state,
    record_trade_event,
    update_workflow_state,
)
from src.services.post_draft_mode_service import (
    MARKET_DISPLAY_ONLY_LABEL,
    NOT_ENOUGH_INFORMATION,
    build_post_draft_summary,
    post_draft_summary_export,
)


def test_post_draft_summary_loads_empty_runtime_state() -> None:
    summary = build_post_draft_summary(empty_runtime_state(mode="live"))

    assert summary.metrics["drafted_count"] == "0"
    assert summary.metrics["trade_count"] == "0"
    assert summary.draft_recap.empty
    assert "No runtime pick events recorded for this mode." in summary.missing_data_warnings


def test_post_draft_summary_works_with_pick_events(tmp_path) -> None:
    state = update_workflow_state(
        empty_runtime_state(mode="live"),
        {
            "assignments": [
                {
                    "player_key": "zay|wr",
                    "overall_pick": 4,
                    "pick_label": "1.04",
                    "player": "Zay Flowers",
                    "position": "WR",
                    "nfl_team": "BAL",
                }
            ]
        },
        event_type="pick_assigned",
        event_detail={"player": "Zay Flowers", "pick_label": "1.04"},
        root=tmp_path,
    )
    context = pd.DataFrame(
        [
            {
                "player": "Zay Flowers",
                "position": "WR",
                "nfl_team": "BAL",
                "final_board_rank": 12,
            }
        ]
    )

    summary = build_post_draft_summary(state, player_context=context, include_market_context=False)

    assert summary.draft_recap.iloc[0]["Player"] == "Zay Flowers"
    assert summary.draft_recap.iloc[0]["NWR Rank"] == "12"
    assert "Highest NWR-ranked player acquired" in summary.value_audit["Audit Item"].tolist()


def test_post_draft_summary_works_with_trade_events(tmp_path) -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="Other",
        team_a_sends="2026 1.04, mystery asset",
        team_b_sends="2028 1st, 2026 2.03",
        root=tmp_path,
    )

    summary = build_post_draft_summary(state)

    assert summary.trade_recap.iloc[0]["Team A Sends"] == "2026 1.04, mystery asset"
    assert "2028 1st" in summary.trade_recap.iloc[0]["Future Picks"]
    assert "mystery asset" in summary.trade_recap.iloc[0]["Review-Needed Assets"]
    assert "Pick Ownership Effect" in summary.trade_recap.columns
    assert (
        summary.trade_recap.iloc[0]["Valuation Status"]
        == "No trade valuation or pick valuation; manual runtime event only."
    )


def test_future_pick_assets_display_without_crashing(tmp_path) -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="Other",
        team_a_sends="2028 2nd",
        team_b_sends="2028 1st",
        root=tmp_path,
    )

    summary = build_post_draft_summary(state)

    assert "2028 1st" in summary.trade_recap.iloc[0]["Future Picks"]
    assert summary.metrics["trade_count"] == "1"


def test_missing_market_match_does_not_drop_player() -> None:
    state = {
        **empty_runtime_state(mode="live"),
        "workflow_state": {
            "assignments": [
                {
                    "player": "Unknown Player",
                    "position": "WR",
                    "pick_label": "1.01",
                }
            ]
        },
    }

    summary = build_post_draft_summary(state, player_context=pd.DataFrame())

    assert summary.draft_recap.iloc[0]["Player"] == "Unknown Player"
    assert summary.draft_recap.iloc[0]["NWR Rank"] == NOT_ENOUGH_INFORMATION


def test_market_context_has_display_only_label_when_present() -> None:
    state = {
        **empty_runtime_state(mode="live"),
        "workflow_state": {
            "assignments": [
                {
                    "player": "Zay Flowers",
                    "position": "WR",
                    "pick_label": "1.01",
                }
            ]
        },
    }

    summary = build_post_draft_summary(
        state,
        player_context=pd.DataFrame(),
        include_market_context=False,
    )

    assert MARKET_DISPLAY_ONLY_LABEL.endswith("Display-Only")
    assert "Market Rank / Display-Only" in summary.draft_recap.columns


def test_post_draft_summary_export_is_display_only() -> None:
    summary = build_post_draft_summary(empty_runtime_state(mode="mock"))

    exported = post_draft_summary_export(summary)

    assert "display only" in exported.lower()
    assert "source truth" in exported.lower()
