from __future__ import annotations

import streamlit as st

from src.services.draft_state_service import DraftBoardState, create_empty_draft_state


def draft_state_key(
    active_data_pack: str,
    active_fingerprint: tuple[str, int, int, int],
) -> str:
    return f"draft_board_state::{active_data_pack}::{active_fingerprint}"


def selected_pick_key(
    active_data_pack: str,
    active_fingerprint: tuple[str, int, int, int],
) -> str:
    return f"draft_board_selected_pick::{active_data_pack}::{active_fingerprint}"


def dirty_key(
    active_data_pack: str,
    active_fingerprint: tuple[str, int, int, int],
) -> str:
    return f"draft_board_dirty::{active_data_pack}::{active_fingerprint}"


def reset_confirm_key(
    active_data_pack: str,
    active_fingerprint: tuple[str, int, int, int],
) -> str:
    return f"draft_board_reset_confirm::{active_data_pack}::{active_fingerprint}"


def clear_board_confirm_key(
    active_data_pack: str,
    active_fingerprint: tuple[str, int, int, int],
) -> str:
    return f"draft_board_clear_board_confirm::{active_data_pack}::{active_fingerprint}"


def state_from_session(
    key: str,
    *,
    contract_rows: list[dict[str, object]],
    ranking_rows: list[dict[str, object]],
) -> DraftBoardState:
    if key not in st.session_state:
        st.session_state[key] = create_empty_draft_state(
            pick_rows=contract_rows,
            available_rows=ranking_rows,
        )
    return st.session_state[key]


def selected_pick_number(state: DraftBoardState, key: str) -> int | None:
    selected = st.session_state.get(key)
    valid_picks = {pick.overall_pick for pick in state.picks}
    if isinstance(selected, int) and selected in valid_picks:
        return selected
    if state.current_pick in valid_picks:
        st.session_state[key] = state.current_pick
        return state.current_pick
    return None
