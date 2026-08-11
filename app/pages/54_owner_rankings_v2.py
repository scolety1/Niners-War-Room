from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_data import load_owner_data  # noqa: E402
from app.components.owner_mode import decision_cards, owner_intro  # noqa: E402
from app.components.ui_framework import page_header  # noqa: E402
from src.services.owner_mode_view_service import MARKET_BANDS, owner_rankings_frame  # noqa: E402

data = load_owner_data(str(REPO_ROOT))
board = owner_rankings_frame(data.evidence.rows)

page_header(
    "Dynasty Rankings",
    eyebrow="Owner Mode · Decide who matters",
    description="The canonical Finished V1 order, organized for player decisions.",
    status_items=((f"{len(board)} ranked players", "safe"), ("Read-only", "safe")),
)
owner_intro(
    "Start with the board. Open the evidence only when you need it.",
    "Search, filter, and inspect the decision context without wading through model operations.",
)
decision_cards(
    (
        ("Rank", "The accepted NWR dynasty order."),
        ("NWR View", "The owner translation of the admitted value band."),
        ("Market", "Where NWR and external consensus differ."),
    )
)

if board.empty:
    st.error("The accepted Finished V1 board is unavailable. No substitute ranks are shown.")
    st.stop()

controls = st.columns((2, 1, 1, 1))
query = controls[0].text_input("Find a player", placeholder="Puka Nacua")
positions = sorted(value for value in board["Pos"].dropna().unique() if value)
selected_positions = controls[1].multiselect("Position", positions, default=positions)
market_options = ["All", *MARKET_BANDS, "Market data unavailable"]
market_filter = controls[2].selectbox("Market view", market_options)
limit = controls[3].selectbox("Show", (25, 50, 100, len(board)), index=1)

filtered = board.loc[board["Pos"].isin(selected_positions)].copy()
if query.strip():
    filtered = filtered.loc[filtered["Player"].str.contains(query.strip(), case=False, regex=False)]
if market_filter != "All":
    filtered = filtered.loc[filtered["Market"].eq(market_filter)]
filtered = filtered.head(limit)

st.dataframe(
    filtered.drop(columns=["asset_id"]),
    hide_index=True,
    width="stretch",
    column_config={
        "Rank": st.column_config.NumberColumn(format="#%d"),
        "Age": st.column_config.NumberColumn(format="%.1f"),
        "Tier": st.column_config.TextColumn(
            help="Owner-facing translation of the admitted Finished V1 value band."
        ),
        "NWR Score": st.column_config.NumberColumn(
            format="%.2f", help="Accepted Finished V1 score."
        ),
        "Market Rank": st.column_config.NumberColumn(format="#%d"),
        "NWR vs Market": st.column_config.NumberColumn(
            format="%+.0f",
            help="Market rank minus NWR rank. Positive means NWR ranks the player higher.",
        ),
    },
)

if not filtered.empty:
    chosen = st.selectbox(
        "Open a player decision",
        filtered["asset_id"].tolist(),
        format_func=lambda key: board.loc[board["asset_id"].eq(key), "Player"].iloc[0],
    )
    actions = st.columns(3)
    actions[0].link_button(
        "Player Detail", f"/player-detail?asset={quote(chosen, safe='')}", use_container_width=True
    )
    actions[1].link_button(
        "Why NWR Ranks Them",
        f"/why-nwr-ranks?asset={quote(chosen, safe='')}",
        use_container_width=True,
    )
    actions[2].link_button("Compare", "/player-compare", use_container_width=True)

with st.expander("Advanced board data", expanded=False):
    st.caption(
        "The previous dense production board is retained as Rankings Data in Advanced / Data."
    )
    st.link_button("Open Rankings Data", "/rankings-data")
