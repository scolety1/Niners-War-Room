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
    load_runtime_state_with_status,
    parse_trade_assets,
    pick_label_mentions,
    preview_runtime_state_import,
    record_trade_event,
    replay_runtime_state_from_event_log,
    reset_runtime_state,
    reset_runtime_state_if_confirmed,
    restore_runtime_state_from_json,
    restore_runtime_state_from_json_if_confirmed,
    runtime_import_preview_diff,
    runtime_paths,
    runtime_state_path,
    undo_last_trade_event,
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


def test_backup_created_on_state_write(tmp_path: Path) -> None:
    update_workflow_state(
        empty_runtime_state(mode="live"),
        {"assignments": [{"player_key": "x", "overall_pick": 1}]},
        event_type="pick_assigned",
        root=tmp_path,
    )

    backups = list(runtime_paths(tmp_path).backup_dir.glob("*auto_pick_assigned*.json"))

    assert backups


def test_missing_state_file_is_explicit_empty_state_not_silent_reset(tmp_path: Path) -> None:
    result = load_runtime_state_with_status(mode="live", root=tmp_path)

    assert result.status == "MISSING_STATE_FILE"
    assert result.state["runtime_recovery_required"] is True
    assert "not a silent official reset" in result.warning
    assert not runtime_state_path(mode="live", root=tmp_path).exists()


def test_corrupt_state_file_is_quarantined_and_recoverable(tmp_path: Path) -> None:
    path = runtime_state_path(mode="live", root=tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")

    result = load_runtime_state_with_status(mode="live", root=tmp_path)

    assert result.status == "CORRUPT_STATE_QUARANTINED"
    assert result.quarantine_path is not None
    assert result.quarantine_path.exists()
    assert result.quarantine_path.read_text(encoding="utf-8") == "{not json"
    assert not path.exists()
    assert result.state["runtime_recovery_required"] is True


def test_live_and_mock_runtime_state_paths_are_separate(tmp_path: Path) -> None:
    live_path = runtime_state_path(mode="live", root=tmp_path)
    mock_path = runtime_state_path(mode="mock", root=tmp_path)

    assert live_path != mock_path
    assert live_path.name.endswith("__live.json")
    assert mock_path.name.endswith("__mock.json")


def test_live_drafted_player_does_not_appear_in_mock_state(tmp_path: Path) -> None:
    update_workflow_state(
        empty_runtime_state(mode="live"),
        {
            "assignments": [
                {
                    "player_key": "live|player",
                    "overall_pick": 1,
                    "pick_label": "1.01",
                    "player": "Live Player",
                    "position": "WR",
                }
            ]
        },
        event_type="pick_assigned",
        root=tmp_path,
    )

    live_state = load_runtime_state(mode="live", root=tmp_path)
    mock_state = load_runtime_state(mode="mock", root=tmp_path)

    assert live_state["drafted_player_ids"] == ["live|player"]
    assert mock_state["drafted_player_ids"] == []


def test_mock_drafted_player_does_not_appear_in_live_state(tmp_path: Path) -> None:
    update_workflow_state(
        empty_runtime_state(mode="mock"),
        {
            "assignments": [
                {
                    "player_key": "mock|player",
                    "overall_pick": 2,
                    "pick_label": "1.02",
                    "player": "Mock Player",
                    "position": "RB",
                }
            ]
        },
        event_type="pick_assigned",
        root=tmp_path,
    )

    live_state = load_runtime_state(mode="live", root=tmp_path)
    mock_state = load_runtime_state(mode="mock", root=tmp_path)

    assert live_state["drafted_player_ids"] == []
    assert mock_state["drafted_player_ids"] == ["mock|player"]


def test_trade_events_are_separated_by_session_type(tmp_path: Path) -> None:
    record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="Live Team",
        team_a_sends="2026 1.04",
        team_b_sends="2026 2.03",
        root=tmp_path,
    )
    record_trade_event(
        empty_runtime_state(mode="mock"),
        team_a="NWR",
        team_b="Mock Team",
        team_a_sends="2026 1.05",
        team_b_sends="2028 1st",
        root=tmp_path,
    )

    live_state = load_runtime_state(mode="live", root=tmp_path)
    mock_state = load_runtime_state(mode="mock", root=tmp_path)

    assert live_state["trade_events"][0]["team_b"] == "Live Team"
    assert mock_state["trade_events"][0]["team_b"] == "Mock Team"
    assert live_state["trade_events"][0]["team_b"] != mock_state["trade_events"][0]["team_b"]


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


def test_required_trade_example_updates_current_and_future_assets(tmp_path: Path) -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="WhoDat",
        team_a_sends="1.04",
        team_b_sends="2028 1st + 2.03",
        root=tmp_path,
    )

    trade = state["trade_events"][0]
    assert state["pick_ownership_overrides"]["1.04"]["new_owner"] == "WhoDat"
    assert state["pick_ownership_overrides"]["2.03"]["new_owner"] == "NWR"
    assert trade["future_picks"] == ["2028 1st"]
    assert trade["current_year_pick_changes"] == [
        {"pick_label": "1.04", "new_owner": "WhoDat", "direction": "NWR sends"},
        {"pick_label": "2.03", "new_owner": "NWR", "direction": "WhoDat sends"},
    ]
    assert state["event_log"][-1]["event_type"] == "trade_recorded"


def test_trade_undo_removes_last_trade_and_rebuilds_ownership(tmp_path: Path) -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="A",
        team_a_sends="1.04",
        team_b_sends="2.03",
        root=tmp_path,
    )
    state = record_trade_event(
        state,
        team_a="NWR",
        team_b="B",
        team_a_sends="2.03",
        team_b_sends="2028 1st",
        root=tmp_path,
    )

    undone = undo_last_trade_event(state, root=tmp_path)

    assert len(undone["trade_events"]) == 1
    assert undone["pick_ownership_overrides"]["1.04"]["new_owner"] == "A"
    assert undone["pick_ownership_overrides"]["2.03"]["new_owner"] == "NWR"
    assert undone["event_log"][-1]["event_type"] == "trade_undone"


def test_event_log_replay_rebuilds_pick_and_trade_state(tmp_path: Path) -> None:
    state = update_workflow_state(
        empty_runtime_state(mode="live"),
        {
            "assignments": [
                {
                    "player_key": "zay|wr",
                    "overall_pick": 1,
                    "pick_label": "1.01",
                    "player": "Zay Flowers",
                    "position": "WR",
                }
            ]
        },
        event_type="pick_assigned",
        event_detail={
            "player": "Zay Flowers",
            "player_key": "zay|wr",
            "pick_label": "1.01",
            "overall_pick": 1,
            "position": "WR",
        },
        root=tmp_path,
    )
    state = record_trade_event(
        state,
        team_a="NWR",
        team_b="WhoDat",
        team_a_sends="1.04",
        team_b_sends="2.03, 2028 1st",
        root=tmp_path,
    )

    replayed = replay_runtime_state_from_event_log(
        state["event_log"],
        mode="live",
        draft_id="draft_day_v2",
    )

    assert replayed["workflow_state"]["assignments"][0]["player"] == "Zay Flowers"
    assert replayed["drafted_player_ids"] == ["zay|wr"]
    assert replayed["pick_ownership_overrides"]["1.04"]["new_owner"] == "WhoDat"
    assert replayed["pick_ownership_overrides"]["2.03"]["new_owner"] == "NWR"


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


def test_import_preview_blocks_overwrite_without_confirmation(tmp_path: Path) -> None:
    current = update_workflow_state(
        empty_runtime_state(mode="live"),
        {
            "assignments": [
                {
                    "player_key": "current|player",
                    "overall_pick": 1,
                    "pick_label": "1.01",
                    "player": "Current Player",
                    "position": "WR",
                }
            ]
        },
        event_type="pick_assigned",
        root=tmp_path,
    )
    incoming = update_workflow_state(
        empty_runtime_state(mode="live"),
        {
            "assignments": [
                {
                    "player_key": "incoming|player",
                    "overall_pick": 2,
                    "pick_label": "1.02",
                    "player": "Incoming Player",
                    "position": "RB",
                }
            ]
        },
        event_type="pick_assigned",
        root=tmp_path / "incoming",
    )
    payload = export_runtime_state_json(incoming)

    preview = preview_runtime_state_import(payload, mode="live")
    not_restored = restore_runtime_state_from_json_if_confirmed(
        payload,
        mode="live",
        confirmed=False,
        current_state=current,
        root=tmp_path,
    )

    assert preview.valid is True
    assert preview.summary["assignment_count"] == "1"
    assert not_restored["drafted_player_ids"] == ["current|player"]
    assert load_runtime_state(mode="live", root=tmp_path)["drafted_player_ids"] == [
        "current|player"
    ]


def test_import_preview_diff_is_display_only_summary(tmp_path: Path) -> None:
    current = update_workflow_state(
        empty_runtime_state(mode="mock", draft_id="mock_a"),
        {"assignments": [{"player_key": "alpha", "overall_pick": 1, "player": "Alpha"}]},
        event_type="pick_assigned",
        root=tmp_path,
    )
    incoming = record_trade_event(
        empty_runtime_state(mode="mock", draft_id="mock_a"),
        team_a="NWR",
        team_b="Other",
        team_a_sends="1.04",
        team_b_sends="2.03",
        root=tmp_path / "incoming",
    )
    preview = preview_runtime_state_import(
        export_runtime_state_json(incoming),
        mode="mock",
        draft_id="mock_a",
    )

    diff = runtime_import_preview_diff(current, preview)
    by_field = {row["Field"]: row for row in diff}

    assert by_field["assignment_count"]["Current"] == "1"
    assert by_field["assignment_count"]["Imported"] == "0"
    assert by_field["assignment_count"]["Change"] == "will change"
    assert by_field["trade_count"]["Imported"] == "1"


def test_import_with_confirmation_creates_backup_and_restores(tmp_path: Path) -> None:
    current = update_workflow_state(
        empty_runtime_state(mode="live"),
        {"assignments": [{"player_key": "current|player", "overall_pick": 1}]},
        event_type="pick_assigned",
        root=tmp_path,
    )
    incoming = update_workflow_state(
        empty_runtime_state(mode="live"),
        {
            "assignments": [
                {
                    "player_key": "incoming|player",
                    "overall_pick": 2,
                    "pick_label": "1.02",
                    "player": "Incoming Player",
                    "position": "RB",
                }
            ]
        },
        event_type="pick_assigned",
        root=tmp_path / "incoming",
    )

    restored = restore_runtime_state_from_json_if_confirmed(
        export_runtime_state_json(incoming),
        mode="live",
        confirmed=True,
        current_state=current,
        root=tmp_path,
    )

    backups = list(runtime_paths(tmp_path).backup_dir.glob("*before_import_restore*.json"))
    assert backups
    assert restored["drafted_player_ids"] == ["incoming|player"]


def test_export_import_respects_session_type(tmp_path: Path) -> None:
    mock_state = update_workflow_state(
        empty_runtime_state(mode="mock"),
        {
            "assignments": [
                {
                    "player_key": "mock|zay",
                    "overall_pick": 4,
                    "pick_label": "1.04",
                    "player": "Mock Zay",
                    "position": "WR",
                }
            ]
        },
        event_type="pick_assigned",
        root=tmp_path,
    )

    restored = restore_runtime_state_from_json(
        export_runtime_state_json(mock_state),
        mode="mock",
        root=tmp_path,
    )
    live_state = load_runtime_state(mode="live", root=tmp_path)

    assert restored["mode"] == "mock"
    assert restored["drafted_player_ids"] == ["mock|zay"]
    assert live_state["drafted_player_ids"] == []


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


def test_backup_created_before_destructive_reset(tmp_path: Path) -> None:
    state = update_workflow_state(
        empty_runtime_state(mode="live"),
        {"assignments": [{"player_key": "x", "overall_pick": 1}]},
        event_type="pick_assigned",
        root=tmp_path,
    )

    reset_runtime_state(state, reason="test reset", root=tmp_path)

    backups = list(runtime_paths(tmp_path).backup_dir.glob("*before_reset*.json"))
    assert backups
    backup_payload = json.loads(backups[0].read_text(encoding="utf-8"))
    assert backup_payload["drafted_player_ids"] == ["x"]


def test_reset_affects_only_selected_session_type(tmp_path: Path) -> None:
    live_state = update_workflow_state(
        empty_runtime_state(mode="live"),
        {"assignments": [{"player_key": "live|x", "overall_pick": 1}]},
        event_type="pick_assigned",
        root=tmp_path,
    )
    update_workflow_state(
        empty_runtime_state(mode="mock"),
        {"assignments": [{"player_key": "mock|x", "overall_pick": 2}]},
        event_type="pick_assigned",
        root=tmp_path,
    )

    reset_runtime_state(live_state, reason="test live reset", root=tmp_path)

    assert load_runtime_state(mode="live", root=tmp_path)["drafted_player_ids"] == []
    assert load_runtime_state(mode="mock", root=tmp_path)["drafted_player_ids"] == ["mock|x"]


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


def test_protected_frozen_board_artifact_remains_unchanged() -> None:
    frozen_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "draft_day_exports"
        / "final_board_v1_20260622"
        / "FINAL_DRAFT_BOARD_V1_FROZEN.csv"
    )

    frozen = pd.read_csv(frozen_path)

    assert len(frozen) == 66
    assert "final_board_rank" in frozen.columns


def test_trade_events_keep_market_and_adp_display_only() -> None:
    state = record_trade_event(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_b="WhoDat",
        team_a_sends="1.04",
        team_b_sends="2.03, 2028 1st",
    )
    trade = state["trade_events"][0]

    assert trade["guardrail_status"] == "display-only event; no trade calculator or model advice"
    assert "market_value" not in trade
    assert "adp_value" not in trade
    assert "dynastyprocess_value" not in trade
