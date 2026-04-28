from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import get_settings
from src.services.trade_service import build_trade_central


@st.cache_data
def _load_board(active_data_pack: str):
    return build_trade_central(active_data_pack)


settings = get_settings()
board = _load_board(str(settings.active_data_pack))
player_frame = pd.DataFrame(board.player_rows)
path_frame = pd.DataFrame(board.path_rows)

st.title("Trade Central")
st.caption(f"`{settings.active_data_pack}`")

left, middle, right = st.columns(3)
shop_signal_count = (
    int((player_frame["signal"] == "Shop").sum()) if not player_frame.empty else 0
)
left.metric("Shop Signals", shop_signal_count)
middle.metric("Pick Paths", len(path_frame))
right.metric("Snapshot", board.snapshot_date or "unknown")

if player_frame.empty:
    st.dataframe(player_frame, use_container_width=True, hide_index=True)
else:
    controls = st.columns(2)
    signals = controls[0].multiselect("Signal", board.signals, default=board.signals)
    filtered_players = player_frame[player_frame["signal"].isin(signals)]

    st.subheader("Player Signals")
    st.dataframe(
        filtered_players[
            [
                "player",
                "pos",
                "signal",
                "trade_value",
                "keeper_score",
                "drop_score",
                "official_rank",
                "market_score",
                "war_score",
                "my_score",
                "confidence",
                "risk",
            ]
        ],
        column_config={
            "player": "Player",
            "pos": "Pos",
            "signal": "Signal",
            "trade_value": "Trade Value",
            "keeper_score": "Keeper",
            "drop_score": "Drop",
            "official_rank": "Official Rank",
            "market_score": "Market",
            "war_score": "War Room",
            "my_score": "My Score",
            "confidence": "Confidence",
            "risk": "Risk",
        },
        use_container_width=True,
        hide_index=True,
    )

    if path_frame.empty:
        st.subheader("Pick Paths")
        st.dataframe(path_frame, use_container_width=True, hide_index=True)
    else:
        path_signals = controls[1].multiselect(
            "Path Signal",
            board.pick_signals,
            default=board.pick_signals,
        )
        filtered_paths = path_frame[
            path_frame["signal"].isin(signals)
            & path_frame["path_signal"].isin(path_signals)
        ]
        st.subheader("Pick Paths")
        st.dataframe(
            filtered_paths[
                [
                    "player",
                    "signal",
                    "trade_value",
                    "pick",
                    "certainty",
                    "pick_value",
                    "value_gap",
                    "path_signal",
                ]
            ],
            column_config={
                "player": "Player",
                "signal": "Signal",
                "trade_value": "Trade Value",
                "pick": "Pick",
                "certainty": "Certainty",
                "pick_value": "Pick Value",
                "value_gap": "Gap",
                "path_signal": "Path",
            },
            use_container_width=True,
            hide_index=True,
        )
