from __future__ import annotations

import pytest

from src.services.mock_draft_operator_session import (
    PRACTICE_MARKET_ROWS,
    PRACTICE_PRIVATE_VALUE_ROWS,
    create_practice_session,
    deserialize_session_state,
    draft_history,
    list_available_assets,
    load_session_state,
    mark_asset_drafted,
    render_operator_status,
    save_session_state,
    serialize_session_state,
    session_status,
    undo_last_pick,
    upcoming_my_picks,
    validate_operator_session,
)


def test_create_practice_session_starts_at_first_pick() -> None:
    session = create_practice_session()

    status = session_status(session)

    assert status["fixture_only"] is True
    assert status["no_real_inputs"] is True
    assert status["no_simulations_run"] is True
    assert status["current_pick"] == 1
    assert status["current_pick_label"] == "1.01"


def test_available_assets_are_deterministic_fixture_display_rows() -> None:
    session = create_practice_session()

    rows = list_available_assets(session)

    assert [row["asset_id"] for row in rows] == [
        "fixture:rookie_a",
        "fixture:veteran_b",
        "fixture:rookie_c",
    ]
    assert rows[0]["fixture_display_value"] == 90.0


def test_mark_asset_drafted_removes_available_and_advances_pick() -> None:
    session = mark_asset_drafted(create_practice_session(), "fixture:rookie_a")

    assert session_status(session)["current_pick"] == 2
    assert "fixture:rookie_a" not in {
        row["asset_id"] for row in list_available_assets(session)
    }
    assert draft_history(session)[0]["asset_id"] == "fixture:rookie_a"


def test_undo_restores_availability_current_pick_and_history() -> None:
    session = mark_asset_drafted(create_practice_session(), "fixture:rookie_a")
    undone = undo_last_pick(session)

    assert session_status(undone)["current_pick"] == 1
    assert draft_history(undone) == ()
    assert "fixture:rookie_a" in {row["asset_id"] for row in list_available_assets(undone)}


def test_duplicate_asset_draft_fails() -> None:
    session = mark_asset_drafted(create_practice_session(), "fixture:rookie_a")

    with pytest.raises(ValueError, match="already drafted"):
        mark_asset_drafted(session, "fixture:rookie_a", overall_pick=2)


def test_duplicate_pick_fails() -> None:
    session = mark_asset_drafted(create_practice_session(), "fixture:rookie_a")

    with pytest.raises(ValueError, match="already has"):
        mark_asset_drafted(session, "fixture:veteran_b", overall_pick=1)


def test_unavailable_asset_draft_fails() -> None:
    with pytest.raises(ValueError, match="not available"):
        mark_asset_drafted(create_practice_session(), "fixture:missing")


def test_upcoming_my_picks_report_next_nwr_pick() -> None:
    rows = upcoming_my_picks(create_practice_session())

    assert rows == (
        {
            "overall_pick": 2,
            "pick_label": "1.02",
            "owner": "NWR",
            "is_next": True,
        },
    )


def test_serialization_round_trip_preserves_fixture_state() -> None:
    session = mark_asset_drafted(create_practice_session(), "fixture:rookie_a")

    restored = deserialize_session_state(serialize_session_state(session))

    assert session_status(restored)["current_pick"] == 2
    assert draft_history(restored)[0]["asset_id"] == "fixture:rookie_a"
    validate_operator_session(restored)


def test_render_status_keeps_no_simulation_language() -> None:
    rendered = render_operator_status(create_practice_session())

    assert "fixture-only practice" in rendered
    assert "No real inputs read." in rendered
    assert "No real simulation run." in rendered


def test_no_files_written_by_default(tmp_path) -> None:  # type: ignore[no-untyped-def]
    _ = create_practice_session()

    assert list(tmp_path.iterdir()) == []


def test_temp_file_save_and_load_requires_explicit_path(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "operator_state.json"
    session = mark_asset_drafted(create_practice_session(), "fixture:rookie_a")

    save_session_state(session, path)
    restored = load_session_state(path)

    assert path.exists()
    assert draft_history(restored)[0]["asset_id"] == "fixture:rookie_a"


def test_unsafe_state_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="local-only"):
        save_session_state(create_practice_session(), "unsafe_state.json")


def test_market_and_private_fixture_rows_remain_separate() -> None:
    private_columns = {column for row in PRACTICE_PRIVATE_VALUE_ROWS for column in row}
    market_columns = {column for row in PRACTICE_MARKET_ROWS for column in row}

    assert "market_adp_pick" not in private_columns
    assert "nwr_private_value" not in market_columns


def test_no_simulation_function_is_required() -> None:
    session = create_practice_session()

    assert not hasattr(session, "run_simulation")
    assert not hasattr(session, "simulate_draft")
