from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_lane_status_table,
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.draft_workflow import render_draft_workflow
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    load_expanded_draftable_player_pool,
    load_frozen_board,
    load_lane_prop_file,
)
from src.services.draft_day_runtime_state_service import load_runtime_state, runtime_paths
from src.services.drafting_mode_cockpit_service import (
    build_cockpit_summary,
    owned_pick_rows,
    recent_event_rows,
    recent_trade_rows,
    tier_count_rows,
)

SOURCE_CAPTION = (
    "Draft Cockpit live runtime session. This state is local/manual draft execution data, "
    "not official source truth and not model input."
)


def _render_live_draft_command_center(
    *,
    board_frame,
    pick_frame,
    source_caption: str,
) -> None:
    state = load_runtime_state(mode="live", source_checkpoint=source_caption)
    summary = build_cockpit_summary(
        board_frame=board_frame,
        pick_frame=pick_frame,
        runtime_state=state,
    )

    st.markdown("## DRAFT COCKPIT")
    st.warning(
        "DRAFT COCKPIT - actions on this page write to the real local draft runtime state. "
        "State changes become part of the draft event log. Use Mock Drafts for experiments."
    )
    st.caption(
        "Draft Cockpit command center: current pick, owned picks, runtime events, trade log, "
        "export/import, and the live draft board share one local live state scope."
    )

    metric_cols = st.columns([1, 1.2, 0.8, 0.8, 1.2])
    metric_cols[0].metric("Current pick", summary.current_pick)
    metric_cols[1].metric("On-clock team", summary.on_clock_team)
    metric_cols[2].metric("Drafted", summary.drafted_count)
    metric_cols[3].metric("Trades", summary.trade_count)
    metric_cols[4].metric("Autosave", summary.autosave_status, help=summary.last_saved)

    quick_cols = st.columns(5)
    quick_cols[0].link_button("Dynasty Rankings", "/rankings", use_container_width=True)
    quick_cols[1].link_button("Player Compare", "/player-compare", use_container_width=True)
    quick_cols[2].link_button("Trading Lab", "/trading-lab", use_container_width=True)
    quick_cols[3].link_button("Draft Analyzer", "/post-draft-mode", use_container_width=True)
    quick_cols[4].link_button(
        "Settings / Data Health",
        "/settings-data-health",
        use_container_width=True,
    )

    with st.expander("Draft Cockpit rail", expanded=False):
        rail_cols = st.columns(3)
        with rail_cols[0]:
            st.caption("Owned current picks")
            owned = owned_pick_rows(pick_frame, state)
            if owned.empty:
                st.info("Not enough information")
            else:
                st.dataframe(owned.head(8), use_container_width=True, hide_index=True)
        with rail_cols[1]:
            st.caption("Recent pick/trade events")
            events = recent_event_rows(state)
            if events.empty:
                st.write("No runtime events yet.")
            else:
                st.dataframe(events, use_container_width=True, hide_index=True)
        with rail_cols[2]:
            st.caption("Recent trades")
            trades = recent_trade_rows(state)
            if trades.empty:
                st.write("No trade events recorded.")
            else:
                st.dataframe(trades, use_container_width=True, hide_index=True)

        tiers = tier_count_rows(board_frame)
        if tiers:
            with st.expander("Tier Board / value cliffs", expanded=False):
                st.dataframe(tiers, use_container_width=True, hide_index=True)

    with st.expander("Live runtime guardrails", expanded=False):
        paths = runtime_paths()
        st.caption(f"Runtime root: {paths.root}")
        st.caption("Runtime state is local/manual and must not be tracked.")
        st.caption(
            "No trade valuation, model input, rank changes, or hidden market sort occurs here."
        )

bundle = load_frozen_board()
live_board_frame = (
    load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame
)
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")
nwr_frame, nwr_path = load_lane_prop_file("mock_draft", "nwr_pick_windows.csv")

page_header(
    "Draft Cockpit",
    eyebrow="Draft-Day App V1",
    description=(
        "One active draftable-pool table plus an interactive draft board. The frozen "
        "66-row board is a baseline checkpoint only; PDF/free-agent overlays extend "
        "the draftable universe without mutating source CSVs."
    ),
    status_items=(
        ("Active draftable pool", "safe"),
        ("Frozen baseline rank visible", "review"),
        ("Persistent local draft state", "safe"),
    ),
)
st.caption("Primary draft cockpit: live pick-by-pick execution and command-center context.")
stop_if_board_blocked(bundle)

if pick_path is None or pick_frame.empty:
    render_yellow_hold("Pick order props are missing, so the live draft board cannot be shown.")
elif nwr_path is None or nwr_frame.empty:
    render_yellow_hold("NWR pick window props are missing, so NWR pick highlights are limited.")
else:
    _render_live_draft_command_center(
        board_frame=live_board_frame,
        pick_frame=pick_frame,
        source_caption=SOURCE_CAPTION,
    )
    render_draft_workflow(
        mode_label="Draft Cockpit",
        board_frame=live_board_frame,
        pick_frame=pick_frame,
        nwr_picks_frame=nwr_frame,
        session_key="draft_day_v1_live_draft_workflow",
        source_caption=(
            f"Frozen baseline checkpoint: {bundle.source_path}. Pick order: {pick_path}. "
            "Draftable overlay: LVE Rosters 061326.pdf page 3 Free Agents, "
            "QB/RB/WR/TE shown by default and K/DST hidden by default. "
            "Default candidate view uses Dynasty Asset Tier/Rank review-only columns "
            "where available; PDF-only free agents without internal value show Not enough "
            "information. Final Board Rank remains visible as a frozen baseline rank, "
            "not as the full available-player line of truth. Sleeper "
            "ADP context, when present, is display-only timing context and does not "
            "drive Dynasty Asset Score."
        ),
    )

with st.expander("Frozen baseline / guardrails", expanded=False):
    render_source_of_truth_badge(bundle)

with st.expander("Lane prop status", expanded=False):
    render_lane_status_table()
