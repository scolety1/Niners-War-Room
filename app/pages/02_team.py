from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.services.command_board_service import build_team_command_board


@st.cache_data
def _load_board(active_data_pack: str):
    return build_team_command_board(active_data_pack)


settings = get_settings()
board = _load_board(str(settings.active_data_pack))
pressure = board.keeper_board.pressure

st.title("Team")
st.caption(f"`{settings.active_data_pack}`")

left, middle, right, far_right = st.columns(4)
left.metric("Roster", pressure.roster_count)
middle.metric("Official Top 5", pressure.official_top_five_count)
right.metric("Forced Release", pressure.forced_release_count)
far_right.metric("Pressure", pressure.pressure_level.upper())

st.subheader("Niners Official Top Five")
st.dataframe(pd.DataFrame(board.top_five_rows), use_container_width=True, hide_index=True)

if board.forced_release_rows:
    st.subheader("Forced-Release Pressure")
    st.dataframe(
        pd.DataFrame(board.forced_release_rows),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Roster Command Table")
roster_frame = pd.DataFrame(board.roster_rows)
if roster_frame.empty:
    st.dataframe(roster_frame, use_container_width=True, hide_index=True)
else:
    recommendations = sorted(roster_frame["recommendation"].dropna().unique())
    selected = st.multiselect("Recommendation", recommendations, default=recommendations)
    filtered = roster_frame[roster_frame["recommendation"].isin(selected)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

with st.expander("League Keeper Pressure"):
    st.dataframe(pd.DataFrame(board.pressure_rows), use_container_width=True, hide_index=True)

with st.expander("Rules Used"):
    st.write(
        f"Protect limit is {board.rules.protect_limit}. "
        f"Official top-five keep limit is {board.rules.official_top_five_keep_limit}. "
        "Players are ranked by deterministic keeper/drop formulas from local snapshots."
    )
