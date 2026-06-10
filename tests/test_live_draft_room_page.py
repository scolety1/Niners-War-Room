from __future__ import annotations

from pathlib import Path

PAGE = Path("app/pages/07_live_draft_room.py")
NAVIGATION = Path("app/navigation.py")
DECISION_BOARD = Path("app/pages/08_june15_review.py")
HANDOFF = Path("docs/model_v4/LIVE_DRAFT_ROOM_PAGE_HANDOFF_20260609.md")


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


def test_live_draft_room_page_exists_and_has_route() -> None:
    text = _page_text()
    nav = NAVIGATION.read_text(encoding="utf-8")

    assert PAGE.exists()
    assert 'st.title("Live Draft Room")' in text
    assert 'title="Live Draft Room"' in nav
    assert 'url_path="live-draft-room"' in nav


def test_live_draft_room_shows_legal_pool_pending_and_source_cards() -> None:
    text = _page_text()

    assert "Mock/live draft tracking. Draft state is separate from source data." in text
    assert "Legal draft pool pending:" in text
    assert "dropped/released veteran data has" in text
    assert "Draft Shape" in text
    assert "Total Picks" in text
    assert "Scouting Pool" in text
    assert "Legal Pool" in text
    assert "Draft State" in text
    assert "Active legal pool is still pending required source files" in text
    assert "Legal pool source warnings" in text


def test_live_draft_room_reuses_existing_state_and_storage_services() -> None:
    text = _page_text()

    for symbol in (
        "state_from_session",
        "mark_player_drafted",
        "replace_drafted_player_at_pick",
        "undo_pick",
        "reset_mock",
        "draft_pick_grid_rows",
        "search_available_players",
        "save_mock_draft",
        "load_mock_draft",
        "duplicate_mock_draft",
        "clear_mock_draft",
    ):
        assert symbol in text


def test_live_draft_room_state_is_separate_from_source_data() -> None:
    text = _page_text()

    assert "live-draft-room::" in text
    assert "Session/local mock" in text
    assert "Session/local mock state only; source data is not mutated." in text
    assert "Never writes to active data packs." in text
    assert "Read-only input for session state." in text
    assert "path.write_text" not in text
    assert "to_csv(" in text


def test_live_draft_room_has_required_controls_without_forbidden_copy() -> None:
    text = _page_text().lower()

    for required in (
        "save mock",
        "load mock",
        "duplicate mock",
        "reset mock",
        "undo last",
        "replace pick",
        "mark drafted",
        "hide drafted",
        "best remaining",
        "my upcoming picks",
    ):
        assert required in text

    for forbidden in (
        "draft this player",
        "target",
        "buy",
        "sell",
        "cut",
        "defer",
    ):
        assert forbidden not in text


def test_live_draft_room_wires_shared_player_detail_card_read_only() -> None:
    text = _page_text()
    helper_start = text.index("def _render_live_player_detail")
    helper_end = text.index("def _render_best_remaining", helper_start)
    helper_text = text[helper_start:helper_end]

    assert "from app.components.player_detail_card import render_player_detail_card" in text
    assert (
        "from src.services.player_detail_card_service import build_player_detail_card_payload"
        in text
    )
    assert "Selected player detail" in text
    assert "Selected Player Detail:" in text
    assert 'build_player_detail_card_payload(detail_row, context="live_draft_room")' in text
    assert "render_player_detail_card(payload)" in text
    assert "Legal Pool Pending" in helper_text
    assert "does not mark or replace picks" in helper_text

    for state_mutation in (
        "mark_player_drafted",
        "replace_drafted_player_at_pick",
        "undo_pick",
        "reset_mock",
        "st.session_state[",
        "st.rerun",
    ):
        assert state_mutation not in helper_text


def test_decision_board_is_not_modified_by_live_draft_room_page() -> None:
    page_text = _page_text()
    decision_text = DECISION_BOARD.read_text(encoding="utf-8")

    assert "Decision Board" not in page_text
    assert "Live Draft Room" not in decision_text


def test_live_draft_room_handoff_exists() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    assert "Page file: `app/pages/07_live_draft_room.py`" in text
    assert "Route: `/live-draft-room`" in text
    assert "Active data packs are not mutated." in text
    assert "Draft Prep remains planning-only" in text
