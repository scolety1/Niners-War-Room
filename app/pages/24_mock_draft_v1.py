from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_player_context import render_nflverse_player_context_expander
from app.components.draft_day_v1 import (
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.draft_workflow import render_draft_workflow
from app.components.post_release_status import render_source_freshness
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    load_expanded_draftable_player_pool,
    load_frozen_board,
    load_lane_prop_file,
)
from src.services.draft_day_runtime_state_service import (
    load_runtime_state_with_status,
    runtime_paths,
)
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
    mock_draft_manifest_health,
    rename_mock_draft_session,
    selected_mock_draft_session,
    session_options,
)
from src.services.post_release_usability_service import freshness_for_sources

ACTIVE_MOCK_SESSION_KEY = "mock_draft_room_active_session_id"


def _render_mock_secondary_context(*, player_context_frame, pick_frame, mock_state, draft_id):
    st.markdown("### Secondary mock-draft context")
    st.caption(
        "Runtime rails, guardrails, and display-only player context follow the primary pick "
        "controls so keyboard and compact-width reading order stays logical."
    )
    with st.expander("Mock runtime rail", expanded=False):
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
            st.caption("Mock state stays local/untracked and separate from Draft Cockpit.")
            st.caption("No trade valuation, model input, rank changes, or source-truth mutation.")
            st.caption("Mock manifest issues never imply live Draft Cockpit state was reset.")

    render_nflverse_player_context_expander(
        player_context_frame,
        key=f"mock_draft_{draft_id}",
        title="NFLVerse player context / display-only",
    )


bundle = load_frozen_board()
mock_player_context_frame = (
    load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame
)
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
render_source_freshness(freshness_for_sources(("Frozen 2026 Draft Context", "Finished V1")))
st.markdown(
    '<a href="/draft-cockpit" target="_self">Back to Draft Cockpit</a>',
    unsafe_allow_html=True,
)
st.markdown("## MOCK DRAFTS")
st.warning(
    "MOCK DRAFTS - practice state only. Mock state is separate from Draft Cockpit and safe "
    "for experimenting; deletes/resets require confirmation."
)
st.caption(
    "Mock Drafts use the same draft-room workflow as Draft Cockpit with a separate mock "
    "runtime scope. Mock actions do not overwrite live draft state."
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

if pick_path is None or pick_frame.empty:
    render_yellow_hold("Mock Draft pick props are missing, so manual mock selection is blocked.")
elif nwr_path is None or nwr_frame.empty:
    render_yellow_hold("NWR pick windows are missing, so pick highlights are limited.")
else:
    manifest_health = mock_draft_manifest_health()
    if manifest_health.status == "OK":
        st.caption(f"Mock manifest status: {manifest_health.message}")
    else:
        st.warning(f"Mock manifest status: {manifest_health.message}")
    st.caption(f"Mock manifest path: {manifest_health.path}")

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

    with st.expander("Manage saved mock drafts", expanded=False):
        st.caption(
            "Session management is secondary to the active pick workflow. Delete remains "
            "unavailable until its confirmation is checked."
        )
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
            help=(
                "Delete the selected mock draft."
                if delete_confirmed
                else "Delete unavailable: confirm deletion first."
            ),
            use_container_width=True,
        ):
            sessions = delete_mock_draft_session(active_session.draft_id)
            st.session_state[ACTIVE_MOCK_SESSION_KEY] = sessions[0].draft_id
            st.rerun()
        if not delete_confirmed:
            manage_cols[3].caption("Delete unavailable: confirm deletion first.")

    source_caption = (
        f"Ranking source: {bundle.source_path}. Mock Draft pick props: {pick_path}. "
        f"Selected mock draft: {active_session.name} ({active_session.draft_id}). "
        "This is manual practice state, not a simulator run or model input."
    )
    load_result = load_runtime_state_with_status(
        mode="mock",
        draft_id=active_session.draft_id,
        source_checkpoint=source_caption,
    )
    mock_state = load_result.state
    summary = build_cockpit_summary(
        board_frame=bundle.frame,
        pick_frame=pick_frame,
        runtime_state=mock_state,
    )
    if load_result.status == "LOADED":
        st.success("Runtime state status: loaded existing mock runtime state.")
    else:
        st.warning(f"Runtime state status: {load_result.warning}")
    st.caption(f"Runtime state path: {load_result.path}")
    metric_cols = st.columns([1, 1.2, 0.8, 0.8, 1.2])
    metric_cols[0].metric("Current pick", summary.current_pick)
    metric_cols[1].metric("On-clock team", summary.on_clock_team)
    metric_cols[2].metric("Drafted", summary.drafted_count)
    metric_cols[3].metric("Trades", summary.trade_count)
    metric_cols[4].metric("Autosave", summary.autosave_status, help=summary.last_saved)

    render_draft_workflow(
        mode_label="Mock Draft manual practice",
        board_frame=bundle.frame,
        pick_frame=pick_frame,
        nwr_picks_frame=nwr_frame,
        session_key=f"draft_day_v1_mock_draft_workflow_{active_session.draft_id}",
        source_caption=source_caption,
        draft_id=active_session.draft_id,
    )
    _render_mock_secondary_context(
        player_context_frame=mock_player_context_frame,
        pick_frame=pick_frame,
        mock_state=mock_state,
        draft_id=active_session.draft_id,
    )

with st.expander("Reference-only availability context", expanded=False):
    if availability_path and not availability_frame.empty:
        st.caption(f"Display-only Mock Draft availability props: {availability_path}")
        st.dataframe(availability_frame.astype(str), use_container_width=True, hide_index=True)
    else:
        render_yellow_hold("Mock Draft availability props are missing.")
