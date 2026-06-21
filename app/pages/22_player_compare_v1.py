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
    display_lane_prop_frame,
    load_frozen_board,
    load_lane_prop_file,
)

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
prop_files = {
    "outcome_columns": "outcome_player_context.csv",
    "trading_lab": "trade_helper_context.csv",
    "rookie_hq": "rookie_overlay_context.csv",
    "decision_board": "decision_flags_context.csv",
}
for lane, file_name in prop_files.items():
    prop_frame, prop_path = load_lane_prop_file(lane, file_name)
    if prop_path is None:
        render_yellow_hold(f"{lane} props are missing.")
        continue
    if prop_frame.empty:
        render_yellow_hold(f"{lane} props are missing: {prop_path}.")
        continue
    st.caption(f"{lane} props: {prop_path}")
    join_columns = [
        column
        for column in ("player", "position", "final_board_rank")
        if column in prop_frame.columns
    ]
    if not join_columns:
        st.dataframe(
            display_lane_prop_frame(prop_frame).head(25),
            use_container_width=True,
            hide_index=True,
        )
        continue
    base_columns = [column for column in join_columns if column in compare.columns]
    context = pd.merge(compare[base_columns], prop_frame, on=base_columns, how="left")
    st.dataframe(display_lane_prop_frame(context), use_container_width=True, hide_index=True)
