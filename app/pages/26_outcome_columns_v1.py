from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_source_of_truth_badge,
    render_yellow_hold,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_frozen_board, load_lane_prop_frame

bundle = load_frozen_board()

page_header(
    "Outcome Columns",
    eyebrow="Draft-Day App V1",
    description=(
        "Display-only outcome shell. Outcome props may enrich the frozen board but "
        "cannot become hidden sort or private value."
    ),
    status_items=(("Display-only", "review"), ("No hidden sort", "safe")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

prop_frame, prop_path = load_lane_prop_frame("outcome_columns")
if prop_path is None:
    render_yellow_hold(
        "Outcome props are missing. No outcome columns are released in this app view."
    )
    st.stop()

st.caption(f"Outcome props loaded: {prop_path}")
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
