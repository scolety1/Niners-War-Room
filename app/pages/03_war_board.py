from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.services.command_board_service import build_war_board


@st.cache_data
def _load_board(active_data_pack: str):
    return build_war_board(active_data_pack)


settings = get_settings()
board = _load_board(str(settings.active_data_pack))
frame = pd.DataFrame(board.rows)

st.title("War Board")
st.caption(f"`{settings.active_data_pack}`")

if frame.empty:
    st.dataframe(frame, use_container_width=True, hide_index=True)
else:
    controls = st.columns(4)
    positions = controls[0].multiselect("Position", board.positions, default=board.positions)
    teams = controls[1].multiselect("Team", board.teams, default=board.teams)
    recommendations = controls[2].multiselect(
        "Recommendation",
        board.recommendations,
        default=board.recommendations,
    )
    top_five_only = controls[3].checkbox("Official Top 5")

    filtered = frame[
        frame["pos"].isin(positions)
        & frame["team"].isin(teams)
        & frame["recommendation"].isin(recommendations)
    ]
    if top_five_only:
        filtered = filtered[filtered["official_rank"].fillna(999).astype(int) <= 5]

    visible_columns = [
        "player",
        "pos",
        "team",
        "official_rank",
        "market_score",
        "war_score",
        "keeper_score",
        "drop_score",
        "confidence",
        "risk",
        "recommendation",
        "do_not_draft_before",
    ]
    st.dataframe(
        filtered[visible_columns],
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Notes"):
        st.dataframe(
            filtered[["player", "notes"]],
            use_container_width=True,
            hide_index=True,
        )
