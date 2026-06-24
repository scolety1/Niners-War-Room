from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.services.draft_day_runtime_state_service import (
    apply_trade_events_to_pick_frame,
    empty_runtime_state,
    export_runtime_state,
    load_runtime_state,
    pick_label_mentions,
    record_trade_event,
    reset_runtime_state,
    runtime_state_path,
    update_workflow_state,
)


def test_runtime_state_autosaves_and_restores_workflow(tmp_path: Path) -> None:
    state = empty_runtime_state(mode="live")
    workflow = {
        "assignments": [
            {
                "player_key": "1|Player|WR|SF",
                "overall_pick": 1,
                "pick_label": "1.01",
                "player": "Player",
                "position": "WR",
            }
        ]
    }

    saved = update_workflow_state(
        state,
        workflow,
        event_type="pick_assigned",
        event_detail={"player": "Player", "pick_label": "1.01"},
        root=tmp_path,
    )
    restored = load_runtime_state(mode="live", root=tmp_path)

    assert saved["workflow_state"] == workflow
    assert restored["workflow_state"] == workflow
    assert restored["event_log"][0]["event_type"] == "pick_assigned"
    assert runtime_state_path(mode="live", root=tmp_path).exists()


def test_trade_event_updates_current_year_pick_ownership(tmp_path: Path) -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        trade_type="Trade away current pick",
        counterparty="Team Rocket",
        sends="1.04",
        receives="2028 1st + 2.03",
        root=tmp_path,
    )
    pick_frame = pd.DataFrame(
        [
            {"overall_pick": 4, "pick_label": "1.04", "current_owner": "NWR"},
            {"overall_pick": 13, "pick_label": "2.03", "current_owner": "Other"},
        ]
    )

    adjusted = apply_trade_events_to_pick_frame(pick_frame, state)

    assert adjusted.loc[0, "current_owner"] == "Team Rocket"
    assert adjusted.loc[1, "current_owner"] == "NWR"
    assert state["trade_events"][0]["future_picks"] == ["2028 1st"]


def test_export_runtime_state_writes_json_csv_and_markdown(tmp_path: Path) -> None:
    state = update_workflow_state(
        empty_runtime_state(mode="mock"),
        {"assignments": []},
        event_type="export_fixture",
        event_detail={},
        root=tmp_path,
    )

    exports = export_runtime_state(state, root=tmp_path)

    assert set(exports) == {"json", "csv", "markdown"}
    assert all(path.exists() for path in exports.values())
    assert json.loads(exports["json"].read_text(encoding="utf-8"))["mode"] == "mock"


def test_reset_runtime_state_clears_assignments_and_logs_reset(tmp_path: Path) -> None:
    state = update_workflow_state(
        empty_runtime_state(mode="live"),
        {"assignments": [{"player_key": "x", "overall_pick": 1}]},
        event_type="pick_assigned",
        root=tmp_path,
    )

    reset = reset_runtime_state(state, reason="test reset", root=tmp_path)

    assert reset["workflow_state"] == {"assignments": []}
    assert reset["event_log"][-1]["event_type"] == "reset_confirmed"


def test_pick_label_mentions_normalizes_round_pick() -> None:
    assert pick_label_mentions("send 1.4 and receive 2.03") == ["1.04", "2.03"]
