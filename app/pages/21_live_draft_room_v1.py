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
from src.services.draft_day_app_v1_service import load_frozen_board, load_lane_prop_file

bundle = load_frozen_board()
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")
nwr_frame, nwr_path = load_lane_prop_file("mock_draft", "nwr_pick_windows.csv")

page_header(
    "Live Draft Room",
    eyebrow="Draft-Day App V1",
    description=(
        "One frozen-board ranking table plus an interactive draft board. Picked-player "
        "state is session-only and never mutates the frozen source CSV."
    ),
    status_items=(
        ("Frozen 66-row board", "safe"),
        ("Session-only draft state", "safe"),
        ("Manual pick controls", "review"),
    ),
)
stop_if_board_blocked(bundle)

if pick_path is None or pick_frame.empty:
    render_yellow_hold("Pick order props are missing, so the live draft board cannot be shown.")
elif nwr_path is None or nwr_frame.empty:
    render_yellow_hold("NWR pick window props are missing, so NWR pick highlights are limited.")
else:
    render_draft_workflow(
        mode_label="Live Draft Room",
        board_frame=bundle.frame,
        pick_frame=pick_frame,
        nwr_picks_frame=nwr_frame,
        session_key="draft_day_v1_live_draft_workflow",
        source_caption=(
            f"Ranking source: {bundle.source_path}. Pick order: {pick_path}. "
            "Default candidate view uses the Tuned V2 Candidate overlay where "
            "available. Final Board Rank remains visible and unchanged. Sleeper ADP "
            "context, when present, is display-only and does not drive rank or sort."
        ),
    )

with st.expander("Frozen board source / guardrails", expanded=False):
    render_source_of_truth_badge(bundle)

with st.expander("Lane prop status", expanded=False):
    render_lane_status_table()
