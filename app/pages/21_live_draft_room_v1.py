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

bundle = load_frozen_board()
live_board_frame = (
    load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame
)
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")
nwr_frame, nwr_path = load_lane_prop_file("mock_draft", "nwr_pick_windows.csv")

page_header(
    "Live Draft Room",
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
stop_if_board_blocked(bundle)

if pick_path is None or pick_frame.empty:
    render_yellow_hold("Pick order props are missing, so the live draft board cannot be shown.")
elif nwr_path is None or nwr_frame.empty:
    render_yellow_hold("NWR pick window props are missing, so NWR pick highlights are limited.")
else:
    render_draft_workflow(
        mode_label="Live Draft Room",
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
