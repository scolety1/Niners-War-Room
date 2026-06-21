from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    filter_board_frame,
    render_final_board_table,
    render_source_of_truth_badge,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    best_available_frame,
    display_board_frame,
    load_frozen_board,
)

TAKEN_KEY = "draft_day_v1_taken_players"

bundle = load_frozen_board()

page_header(
    "Live Draft Room",
    eyebrow="Draft-Day App V1",
    description=(
        "Reference board for live drafting. Taken-player marking is session-state only "
        "and never mutates the frozen source CSV."
    ),
    status_items=(
        ("Session-only taken list", "safe"),
        ("Frozen board order", "safe"),
        ("No source mutation", "safe"),
    ),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

if TAKEN_KEY not in st.session_state:
    st.session_state[TAKEN_KEY] = []

players = bundle.frame["player"].astype(str).tolist() if "player" in bundle.frame.columns else []
control_cols = st.columns([2, 1, 1])
selected = control_cols[0].multiselect(
    "Mark players taken in this local session",
    players,
    default=st.session_state[TAKEN_KEY],
)
if control_cols[1].button("Apply taken list"):
    st.session_state[TAKEN_KEY] = selected
if control_cols[2].button("Clear taken list"):
    st.session_state[TAKEN_KEY] = []

available = best_available_frame(bundle.frame, st.session_state[TAKEN_KEY])
summary_cols = st.columns(4)
summary_cols[0].metric("Board rows", len(bundle.frame))
summary_cols[1].metric("Taken in session", len(st.session_state[TAKEN_KEY]))
summary_cols[2].metric("Available", len(available))
best_rank = int(available["final_board_rank"].min()) if len(available) else 0
summary_cols[3].metric("Best available rank", best_rank)

st.subheader("Best Available Overall")
render_final_board_table(available.head(20), key="live_best_available")

st.subheader("Best Available By Position")
position_rows = []
for _position, group in available.groupby("position", dropna=False):
    first = group.sort_values("final_board_rank", kind="stable").head(1)
    if not first.empty:
        position_rows.append(first)
if position_rows:
    st.dataframe(
        display_board_frame(pd.concat(position_rows, ignore_index=True)),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No available players remain after session taken-list filters.")

st.subheader("Filtered Available Board")
filtered = filter_board_frame(available, key_prefix="live_draft_room_v1")
render_final_board_table(filtered, key="live_filtered_available")
