from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
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
from src.services.draft_day_app_v1_service import (
    load_frozen_board,
    load_lane_prop_frame,
    manual_review_frame,
)

bundle = load_frozen_board()

page_header(
    "Decision Board",
    eyebrow="Draft-Day App V1",
    description=(
        "Manual review flags and risk notes from the frozen board. Lane props may add "
        "context only when they reference the same frozen board."
    ),
    status_items=(("Manual flags visible", "safe"), ("Frozen board first", "safe")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

st.subheader("Manual Review Queue")
flags = manual_review_frame(bundle.frame)
if flags.empty:
    st.success("No manual review flags are present in the frozen board.")
else:
    st.dataframe(flags, use_container_width=True, hide_index=True)

prop_frame, prop_path = load_lane_prop_frame("decision_board")
if prop_path is None:
    render_yellow_hold("Decision Board props are missing. Frozen risk notes remain available.")
else:
    st.caption(f"Decision Board props loaded: {prop_path}")
    join_columns = [column for column in ("player", "position") if column in prop_frame.columns]
    if join_columns:
        display = pd.merge(
            bundle.frame[["player", "position", "final_board_rank"]],
            prop_frame,
            on=join_columns,
            how="left",
        )
    else:
        display = prop_frame
    st.dataframe(display, use_container_width=True, hide_index=True)

st.subheader("Top Board Context")
render_final_board_table(bundle.frame.head(20), key="decision_board_top_context")
