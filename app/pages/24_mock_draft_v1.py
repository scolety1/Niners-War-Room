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

bundle = load_frozen_board()
availability_frame, availability_path = load_lane_prop_file(
    "mock_draft",
    "availability_context.csv",
)
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")
nwr_frame, nwr_path = load_lane_prop_file("mock_draft", "nwr_pick_windows.csv")

page_header(
    "Mock Draft",
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
st.caption("Deep tool: manual practice workflow. Mock state does not affect live draft state.")
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

if pick_path is None or pick_frame.empty:
    render_yellow_hold("Mock Draft pick props are missing, so manual mock selection is blocked.")
elif nwr_path is None or nwr_frame.empty:
    render_yellow_hold("NWR pick windows are missing, so pick highlights are limited.")
else:
    render_draft_workflow(
        mode_label="Mock Draft manual practice",
        board_frame=bundle.frame,
        pick_frame=pick_frame,
        nwr_picks_frame=nwr_frame,
        session_key="draft_day_v1_mock_draft_workflow",
        source_caption=(
            f"Ranking source: {bundle.source_path}. Mock Draft pick props: {pick_path}. "
            "This is manual practice state, not a simulator run."
        ),
    )

with st.expander("Reference-only availability context", expanded=False):
    if availability_path and not availability_frame.empty:
        st.caption(f"Display-only Mock Draft availability props: {availability_path}")
        st.dataframe(availability_frame.astype(str), use_container_width=True, hide_index=True)
    else:
        render_yellow_hold("Mock Draft availability props are missing.")
