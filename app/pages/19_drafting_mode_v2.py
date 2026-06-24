from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import render_source_of_truth_badge, stop_if_board_blocked
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_frozen_board
from src.services.draft_day_runtime_state_service import (
    event_rows,
    load_runtime_state,
    runtime_paths,
)

bundle = load_frozen_board()
live_state = load_runtime_state(mode="live")
mock_state = load_runtime_state(mode="mock")

with st.sidebar:
    st.markdown("### Your Team")
    st.caption(
        "V2 keeps this sidebar reserved for roster, picks, and trade context. Current lane does "
        "not mutate roster/source truth."
    )
    st.metric("Live picks recorded", len(live_state["workflow_state"]["assignments"]))
    st.metric("Live trades recorded", len(live_state["trade_events"]))
    st.metric("Mock picks recorded", len(mock_state["workflow_state"]["assignments"]))

page_header(
    "Drafting Mode",
    eyebrow="Draft-Day App V2",
    description=(
        "One on-clock shell for Live Draft, Mock Draft, cheat sheets, trade tools, player "
        "compare, search, and post-draft review. Runtime state is local-only and reload-safe."
    ),
    status_items=(
        ("Persistent runtime state", "safe"),
        ("Source truth unchanged", "safe"),
        ("Decision support only", "review"),
    ),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

top_cols = st.columns([1, 1, 1, 2])
with top_cols[0]:
    st.page_link("pages/21_live_draft_room_v1.py", label="Enter Live Draft Room")
with top_cols[1]:
    st.page_link("pages/24_mock_draft_v1.py", label="Enter Mock Draft")
with top_cols[2]:
    st.page_link("pages/18_cheat_sheets_v2.py", label="Open Cheat Sheets")
with top_cols[3]:
    st.caption(
        "Drafting Mode is a workflow shell. Final Board Rank and Dynasty Rank remain visible "
        "baselines; V2 runtime events do not edit source artifacts."
    )

tabs = st.tabs(
    [
        "Cheat Sheets",
        "Draft Board",
        "Trade Lab",
        "Player Compare",
        "Search",
        "Settings / Data Health",
    ]
)

with tabs[0]:
    st.subheader("Cheat Sheets")
    st.caption("Overall-first tiered view for on-clock scanning.")
    st.page_link("pages/18_cheat_sheets_v2.py", label="Open Cheat Sheets V2")

with tabs[1]:
    st.subheader("Draft Board")
    st.caption("Use Live Draft for real picks or Mock Draft for practice state.")
    draft_cols = st.columns(2)
    draft_cols[0].page_link("pages/21_live_draft_room_v1.py", label="Live Draft Room")
    draft_cols[1].page_link("pages/24_mock_draft_v1.py", label="Mock Draft")

with tabs[2]:
    st.subheader("Trade Lab")
    st.caption("Manual package review plus V2 trade-event recording. No trade calculator logic.")
    st.page_link("pages/23_trading_lab_v1.py", label="Open Trade Lab")

with tabs[3]:
    st.subheader("Player Compare")
    st.caption("Decision summary first; detailed context behind expanders.")
    st.page_link("pages/22_player_compare_v1.py", label="Open Player Compare")

with tabs[4]:
    st.subheader("Search")
    if bundle.loaded and "player" in bundle.frame.columns:
        query = st.text_input("Find a player on the frozen board", placeholder="Search player")
        search_frame = bundle.frame.copy()
        if query:
            search_frame = search_frame.loc[
                search_frame["player"].astype(str).str.contains(query, case=False, na=False)
            ]
        columns = [
            column
            for column in ("final_board_rank", "player", "position", "nfl_team", "final_tier")
            if column in search_frame.columns
        ]
        st.dataframe(
            search_frame.loc[:, columns].head(40).rename(
                columns={
                    "final_board_rank": "Final Board Rank",
                    "player": "Player",
                    "position": "Pos",
                    "nfl_team": "NFL Team",
                    "final_tier": "Tier",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Frozen board search is unavailable.")

with tabs[5]:
    st.subheader("Settings / Data Health")
    paths = runtime_paths()
    st.caption(f"Runtime state root: {paths.root}")
    runtime_rows = [
        {
            "Mode": "Live",
            "Picks": len(live_state["workflow_state"]["assignments"]),
            "Trades": len(live_state["trade_events"]),
            "Events": len(event_rows(live_state)),
        },
        {
            "Mode": "Mock",
            "Picks": len(mock_state["workflow_state"]["assignments"]),
            "Trades": len(mock_state["trade_events"]),
            "Events": len(event_rows(mock_state)),
        },
    ]
    st.dataframe(pd.DataFrame(runtime_rows), use_container_width=True, hide_index=True)
    st.page_link("pages/28_settings_data_health_v1.py", label="Open full Settings / Data Health")
