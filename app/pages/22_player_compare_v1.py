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
from src.services.draft_day_app_v1_service import load_frozen_board, load_lane_prop_frame

bundle = load_frozen_board()

page_header(
    "Player Compare",
    eyebrow="Draft-Day App V1",
    description=(
        "Compare 2 to 4 players using the frozen board fields. Lane prop context is "
        "shown only when present and remains secondary to final_board_rank."
    ),
    status_items=(("Frozen board comparison", "safe"), ("Missing props show hold", "review")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

players = bundle.frame["player"].astype(str).tolist() if "player" in bundle.frame.columns else []
selected = st.multiselect("Players to compare", players, max_selections=4)
if len(selected) < 2:
    st.info("Select 2 to 4 players from the frozen board.")
    st.stop()

compare = bundle.frame.loc[bundle.frame["player"].astype(str).isin(selected)].copy()
render_final_board_table(compare, key="player_compare_board")

st.subheader("Lane Prop Context")
for lane in ("outcome_columns", "trading_lab", "rookie_hq", "decision_board"):
    prop_frame, prop_path = load_lane_prop_frame(lane)
    if prop_path is None:
        render_yellow_hold(f"{lane} props are missing.")
        continue
    st.caption(f"{lane} props: {prop_path}")
    join_columns = [column for column in ("player", "position") if column in prop_frame.columns]
    if not join_columns:
        st.dataframe(prop_frame.head(25), use_container_width=True, hide_index=True)
        continue
    context = pd.merge(compare[["player", "position"]], prop_frame, on=join_columns, how="left")
    st.dataframe(context, use_container_width=True, hide_index=True)
