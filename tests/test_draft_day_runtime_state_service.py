from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.services.draft_day_runtime_state_service import (
    apply_trade_events_to_pick_frame,
    create_runtime_backup,
    empty_runtime_state,
    export_runtime_state,
    export_runtime_state_json,
    load_runtime_state,
    parse_trade_assets,
    pick_label_mentions,
    record_trade_event,
    reset_runtime_state,
    reset_runtime_state_if_confirmed,
    restore_runtime_state_from_json,
    runtime_paths,
    runtime_state_path,
    update_workflow_state,
)
from src.services.draft_day_workflow_service import available_board_frame


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
    assert saved["draft_session_id"] == "draft_day_v2"
    assert saved["drafted_players"][0]["player_name"] == "Player"
    assert saved["drafted_player_ids"] == ["1|Player|WR|SF"]
    assert saved["pick_events"][0]["source"] == "manual"
    assert restored["workflow_state"] == workflow
    assert restored["event_log"][0]["event_type"] == "pick_assigned"
    assert runtime_state_path(mode="live", root=tmp_path).exists()


def test_trade_event_updates_current_year_pick_ownership(tmp_path: Path) -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="Team Rocket",
        team_a_sends="2026 1.04",
        team_b_sends="2028 1st, 2026 2.03",
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
    assert state["trade_events"][0]["status"] == "active"
    assert state["pick_ownership_overrides"]["1.04"]["new_owner"] == "Team Rocket"


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


def test_export_import_roundtrip_restores_drafted_player(tmp_path: Path) -> None:
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
                }
            ]
        },
        event_type="pick_assigned",
        event_detail={
            "player": "Zay Flowers",
            "player_key": "zay|wr",
            "pick_label": "1.04",
            "overall_pick": 4,
            "position": "WR",
        },
        root=tmp_path,
    )
    exported = export_runtime_state_json(state)

    restored = restore_runtime_state_from_json(exported, mode="live", root=tmp_path)

    assert restored["workflow_state"]["assignments"][0]["player"] == "Zay Flowers"
    assert restored["drafted_players"][0]["player_name"] == "Zay Flowers"
    assert restored["event_log"][-1]["event_type"] == "state_restored_from_json"


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


def test_reset_requires_confirmation_logic(tmp_path: Path) -> None:
    state = update_workflow_state(
        empty_runtime_state(mode="live"),
        {"assignments": [{"player_key": "x", "overall_pick": 1}]},
        event_type="pick_assigned",
        root=tmp_path,
    )

    not_reset = reset_runtime_state_if_confirmed(
        state,
        confirmed=False,
        reason="not confirmed",
        root=tmp_path,
    )
    reset = reset_runtime_state_if_confirmed(
        state,
        confirmed=True,
        reason="confirmed",
        root=tmp_path,
    )

    assert not_reset["workflow_state"]["assignments"]
    assert reset["workflow_state"] == {"assignments": []}


def test_pick_label_mentions_normalizes_round_pick() -> None:
    assert pick_label_mentions("send 1.4 and receive 2.03") == ["1.04", "2.03"]


def test_pick_asset_parsing_required_examples() -> None:
    parsed = parse_trade_assets("2026 1.04, 2026 2.03, 2028 1st, 2028 2nd, mystery asset")

    rows = {row["raw_text"]: row for row in parsed}
    assert rows["2026 1.04"]["pick_label"] == "1.04"
    assert rows["2026 2.03"]["pick_label"] == "2.03"
    assert rows["2028 1st"]["asset_type"] == "future_pick"
    assert rows["2028 2nd"]["round"] == 2
    assert rows["mystery asset"]["status"] == "REVIEW_NEEDED"


def test_trade_event_schema_validation_and_review_needed_asset(tmp_path: Path) -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="Team B",
        team_a_sends="unknown raw text",
        team_b_sends="2026 2.03",
        notes="test",
        root=tmp_path,
    )
    trade = state["trade_events"][0]

    expected = {
        "trade_id",
        "timestamp",
        "team_a",
        "team_b",
        "team_a_sends",
        "team_b_sends",
        "affected_picks",
        "notes",
        "source",
        "status",
    }
    assert expected.issubset(trade)
    assert trade["team_a_assets"][0]["status"] == "REVIEW_NEEDED"
    assert trade["affected_picks"][0]["status"] == "REVIEW_NEEDED"


def test_backup_file_creation_uses_runtime_backup_path(tmp_path: Path) -> None:
    state = empty_runtime_state(mode="live")

    backup = create_runtime_backup(state, root=tmp_path, reason="test")

    assert backup.exists()
    assert backup.parent == runtime_paths(tmp_path).backup_dir
    assert "NWR_SHARED_DATA" not in str(backup)


def test_cheat_sheet_filtering_can_use_persisted_state() -> None:
    board = pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Drafted Player",
                "position": "WR",
                "nfl_team": "SF",
            },
            {
                "final_board_rank": 2,
                "player": "Available Player",
                "position": "RB",
                "nfl_team": "SF",
            },
        ]
    )
    state = {
        "assignments": [
            {
                "player_key": "1|Drafted Player|WR|SF",
                "overall_pick": 1,
                "pick_label": "1.01",
                "player": "Drafted Player",
                "position": "WR",
            }
        ]
    }

    available = available_board_frame(board, state)

    assert available["player"].tolist() == ["Available Player"]


def test_runtime_state_does_not_create_rank_model_or_source_truth_fields() -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="Team B",
        team_a_sends="2026 1.04",
        team_b_sends="2026 2.03",
    )
    forbidden = {
        "final_board_rank_override",
        "dynasty_rank_override",
        "tier_assignment_override",
        "model_input",
        "hidden_sort",
        "source_truth_replacement",
    }

    assert forbidden.isdisjoint(state)
