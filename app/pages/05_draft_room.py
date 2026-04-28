from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.services.draft_service import build_draft_room


@st.cache_data
def _load_board(active_data_pack: str):
    return build_draft_room(active_data_pack)


settings = get_settings()
board = _load_board(str(settings.active_data_pack))
pick_frame = pd.DataFrame(board.pick_rows)
team_frame = pd.DataFrame(board.team_rows)

st.title("Draft Room")
st.caption(f"`{settings.active_data_pack}`")

left, middle, right = st.columns(3)
left.metric("Picks", len(board.pick_rows))
middle.metric(
    "Snapshot Value",
    f"{pick_frame['snapshot_value'].sum():,.1f}" if not pick_frame.empty else "0.0",
)
right.metric("Snapshot", board.snapshot_date or "unknown")

if pick_frame.empty:
    st.dataframe(pick_frame, use_container_width=True, hide_index=True)
else:
    controls = st.columns(3)
    teams = controls[0].multiselect("Current Team", board.teams, default=board.teams)
    certainties = controls[1].multiselect(
        "Certainty",
        board.certainties,
        default=board.certainties,
    )
    current_year_only = controls[2].checkbox("Current Year Only")

    filtered = pick_frame[
        pick_frame["current_team"].isin(teams)
        & pick_frame["certainty"].isin(certainties)
    ]
    if current_year_only:
        current_year = int(filtered["pick_year"].min()) if not filtered.empty else None
        if current_year is not None:
            filtered = filtered[filtered["pick_year"] == current_year]

    st.subheader("Pick Value Table")
    st.dataframe(
        filtered[
            [
                "pick",
                "current_team",
                "original_team",
                "certainty",
                "overall_pick",
                "base_value",
                "future_discount",
                "certainty_factor",
                "snapshot_value",
                "bucket",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Team Totals"):
        st.dataframe(team_frame, use_container_width=True, hide_index=True)
