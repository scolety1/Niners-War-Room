from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.services.league_service import build_league_intel


@st.cache_data
def _load_board(active_data_pack: str):
    return build_league_intel(active_data_pack)


settings = get_settings()
board = _load_board(str(settings.active_data_pack))
pressure_frame = pd.DataFrame(board.pressure_rows)
release_frame = pd.DataFrame(board.default_release_rows)
shield_frame = pd.DataFrame(board.shield_rows)

st.title("League Intel")
st.caption(f"`{settings.active_data_pack}`")

left, middle, right = st.columns(3)
under_pressure = (
    int((pressure_frame["pressure_count"] > 0).sum())
    if not pressure_frame.empty
    else 0
)
left.metric("Teams Under Pressure", under_pressure)
middle.metric("Default Releases", len(board.default_release_rows))
right.metric("Snapshot", board.snapshot_date or "unknown")

if pressure_frame.empty:
    st.dataframe(pressure_frame, use_container_width=True, hide_index=True)
else:
    levels = st.multiselect(
        "Pressure Level",
        board.pressure_levels,
        default=board.pressure_levels,
    )
    filtered_pressure = pressure_frame[
        pressure_frame["pressure_level"].isin(levels)
    ]

    st.subheader("Keeper Pressure by Team")
    st.dataframe(
        filtered_pressure[
            [
                "team",
                "pressure_level",
                "pressure_count",
                "forced_release_count",
                "official_top_five_count",
                "roster_count",
                "protect_limit",
            ]
        ],
        column_config={
            "team": "Team",
            "pressure_level": "Pressure",
            "pressure_count": "Pressure Count",
            "forced_release_count": "Default Releases",
            "official_top_five_count": "Official Top 5",
            "roster_count": "Roster",
            "protect_limit": "Protect Limit",
        },
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Default Release Candidates"):
        st.dataframe(
            release_frame,
            column_config={
                "team": "Team",
                "player": "Player",
                "pos": "Pos",
                "signal": "Signal",
                "official_rank": "Official Rank",
                "keeper_score": "Keeper",
                "drop_score": "Drop",
                "confidence": "Confidence",
            },
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Top-Five Shield Candidates"):
        st.dataframe(
            shield_frame,
            column_config={
                "team": "Team",
                "player": "Player",
                "pos": "Pos",
                "signal": "Signal",
                "official_rank": "Official Rank",
                "keeper_score": "Keeper",
                "drop_score": "Drop",
                "confidence": "Confidence",
            },
            use_container_width=True,
            hide_index=True,
        )
