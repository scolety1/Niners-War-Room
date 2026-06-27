from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.draft_workflow import render_draft_workflow
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_frozen_board, load_lane_prop_file
from src.services.draft_day_runtime_state_service import load_runtime_state, runtime_paths
from src.services.drafting_mode_cockpit_service import (
    build_cockpit_summary,
    owned_pick_rows,
    recent_event_rows,
    recent_trade_rows,
)
from src.services.mock_draft_room_service import (
    create_mock_draft_session,
    delete_mock_draft_session,
    duplicate_mock_draft_session,
    load_mock_draft_sessions,
    rename_mock_draft_session,
    selected_mock_draft_session,
    session_options,
)

ACTIVE_MOCK_SESSION_KEY = "mock_draft_room_active_session_id"


bundle = load_frozen_board()
availability_frame, availability_path = load_lane_prop_file(
    "mock_draft",
    "availability_context.csv",
)
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")
nwr_frame, nwr_path = load_lane_prop_file("mock_draft", "nwr_pick_windows.csv")

page_header(
    "Mock Drafts",
    eyebrow="Draft-Day App V1",
    description=(
        "Manual mock selection workflow using the frozen board and reference-only Mock Draft "
        "props. Simulator/model valuation logic remains unchanged."
    ),
    status_items=(
        ("Manual mock mode", "review"),
        ("Simulator logic unchanged", "safe"),
        ("No automatic recommendations", "safe"),
    ),
)
st.markdown(
    '<a href="/live-draft-room" target="_self">Back to Live Draft</a>',
    unsafe_allow_html=True,
)
st.markdown("## MOCK DRAFTS")
st.warning(
    "MOCK DRAFTS - practice state only. Mock state is separate from Live Draft and safe "
    "for experimenting; deletes/resets require confirmation."
)
st.caption(
    "Mock Drafts use the same draft-room workflow as Live Draft with a separate mock "
    "runtime scope. Mock actions do not overwrite live draft state."
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

if pick_path is None or pick_frame.empty:
    render_yellow_hold("Mock Draft pick props are missing, so manual mock selection is blocked.")
elif nwr_path is None or nwr_frame.empty:
    render_yellow_hold("NWR pick windows are missing, so pick highlights are limited.")
else:
    sessions = load_mock_draft_sessions()
    active_session = selected_mock_draft_session(
        sessions,
        st.session_state.get(ACTIVE_MOCK_SESSION_KEY),
    )
    options = session_options(sessions)
    selected_label = st.selectbox(
        "Saved mock draft",
        list(options),
        index=list(options.values()).index(active_session.draft_id),
    )
    selected_id = options[selected_label]
    st.session_state[ACTIVE_MOCK_SESSION_KEY] = selected_id
    active_session = selected_mock_draft_session(sessions, selected_id)

    manage_cols = st.columns([1, 1, 1, 1])
    new_name = manage_cols[0].text_input(
        "New mock name",
        value=f"Mock Draft {len(sessions) + 1}",
        key="mock_draft_room_new_name",
    )
    if manage_cols[0].button("Create Mock", use_container_width=True):
        sessions = create_mock_draft_session(new_name)
        st.session_state[ACTIVE_MOCK_SESSION_KEY] = sessions[-1].draft_id
        st.rerun()

    rename_name = manage_cols[1].text_input(
        "Rename selected",
        value=active_session.name,
        key=f"mock_draft_room_rename_{active_session.draft_id}",
    )
    if manage_cols[1].button("Rename Mock", use_container_width=True):
        rename_mock_draft_session(active_session.draft_id, rename_name)
        st.session_state[ACTIVE_MOCK_SESSION_KEY] = active_session.draft_id
        st.rerun()

    duplicate_name = manage_cols[2].text_input(
        "Duplicate as",
        value=f"{active_session.name} Copy",
        key=f"mock_draft_room_duplicate_{active_session.draft_id}",
    )
    if manage_cols[2].button("Duplicate Mock", use_container_width=True):
        sessions = duplicate_mock_draft_session(active_session.draft_id, duplicate_name)
        st.session_state[ACTIVE_MOCK_SESSION_KEY] = sessions[-1].draft_id
        st.rerun()

    delete_confirmed = manage_cols[3].checkbox(
        "Confirm delete selected mock",
        key=f"mock_draft_room_delete_confirm_{active_session.draft_id}",
    )
    if manage_cols[3].button(
        "Delete Mock",
        disabled=not delete_confirmed,
        use_container_width=True,
    ):
        sessions = delete_mock_draft_session(active_session.draft_id)
        st.session_state[ACTIVE_MOCK_SESSION_KEY] = sessions[0].draft_id
        st.rerun()

    source_caption = (
        f"Ranking source: {bundle.source_path}. Mock Draft pick props: {pick_path}. "
        f"Selected mock draft: {active_session.name} ({active_session.draft_id}). "
        "This is manual practice state, not a simulator run or model input."
    )
    mock_state = load_runtime_state(
        mode="mock",
        draft_id=active_session.draft_id,
        source_checkpoint=source_caption,
    )
    summary = build_cockpit_summary(
        board_frame=bundle.frame,
        pick_frame=pick_frame,
        runtime_state=mock_state,
    )
    metric_cols = st.columns([1, 1.2, 0.8, 0.8, 1.2])
    metric_cols[0].metric("Current pick", summary.current_pick)
    metric_cols[1].metric("On-clock team", summary.on_clock_team)
    metric_cols[2].metric("Drafted", summary.drafted_count)
    metric_cols[3].metric("Trades", summary.trade_count)
    metric_cols[4].metric("Autosave", summary.autosave_status, help=summary.last_saved)

    with st.expander("Mock runtime rail", expanded=True):
        rail_cols = st.columns(3)
        with rail_cols[0]:
            st.caption("Owned current picks")
            owned = owned_pick_rows(pick_frame, mock_state)
            if owned.empty:
                st.info("Not enough information")
            else:
                st.dataframe(owned.head(8), use_container_width=True, hide_index=True)
        with rail_cols[1]:
            st.caption("Recent pick/trade events")
            events = recent_event_rows(mock_state)
            if events.empty:
                st.write("No mock events yet.")
            else:
                st.dataframe(events, use_container_width=True, hide_index=True)
        with rail_cols[2]:
            st.caption("Recent trades")
            trades = recent_trade_rows(mock_state)
            if trades.empty:
                st.write("No mock trade events recorded.")
            else:
                st.dataframe(trades, use_container_width=True, hide_index=True)
        with st.expander("Mock runtime guardrails", expanded=False):
            paths = runtime_paths()
            st.caption(f"Runtime root: {paths.root}")
            st.caption("Mock state stays local/untracked and separate from Live Draft.")
            st.caption("No trade valuation, model input, rank changes, or source-truth mutation.")

    render_draft_workflow(
        mode_label="Mock Draft manual practice",
        board_frame=bundle.frame,
        pick_frame=pick_frame,
        nwr_picks_frame=nwr_frame,
        session_key=f"draft_day_v1_mock_draft_workflow_{active_session.draft_id}",
        source_caption=source_caption,
        draft_id=active_session.draft_id,
    )

with st.expander("Reference-only availability context", expanded=False):
    if availability_path and not availability_frame.empty:
        st.caption(f"Display-only Mock Draft availability props: {availability_path}")
        st.dataframe(availability_frame.astype(str), use_container_width=True, hide_index=True)
    else:
        render_yellow_hold("Mock Draft availability props are missing.")
