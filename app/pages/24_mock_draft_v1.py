from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_final_board_table,
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_frozen_board, load_lane_prop_frame

bundle = load_frozen_board()

page_header(
    "Mock Draft",
    eyebrow="Draft-Day App V1",
    description=(
        "Reference-only shell. It can point at the frozen board, but it does not alter "
        "Mock Draft simulator logic or the pinned snapshot."
    ),
    status_items=(("Reference only", "review"), ("Simulator logic unchanged", "safe")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

prop_frame, prop_path = load_lane_prop_frame("mock_draft")
if prop_path is None:
    render_yellow_hold("Mock Draft props are missing. Use the frozen board as reference only.")
else:
    st.caption(f"Mock Draft props loaded: {prop_path}")
    st.dataframe(prop_frame.head(50), use_container_width=True, hide_index=True)

st.subheader("Frozen Board Reference")
render_final_board_table(bundle.frame.head(30), key="mock_draft_reference_board")
