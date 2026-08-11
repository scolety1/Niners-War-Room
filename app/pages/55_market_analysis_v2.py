from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_data import load_owner_data  # noqa: E402
from app.components.owner_mode import owner_intro  # noqa: E402
from app.components.ui_framework import page_header  # noqa: E402
from src.services.owner_mode_view_service import MARKET_BANDS, owner_rankings_frame  # noqa: E402

data = load_owner_data(str(REPO_ROOT))
board = owner_rankings_frame(data.evidence.rows)
available = board.loc[board["Market"].ne("Market data unavailable")].copy()

page_header(
    "Market Analysis",
    eyebrow="Owner Mode · Find disagreement",
    description=(
        "Use external consensus as a comparison lens, never as NWR authority or a trade value."
    ),
    status_items=((f"{len(available)} matched players", "safe"), ("Display-only", "review")),
)
owner_intro(
    "Disagreement creates the watchlist.",
    "Large gaps are prompts to investigate—not automatic buy or sell instructions.",
)

market_date = str(data.evidence.market_freshness.get("upstream_scrape_date", "")).strip()
freshness = str(data.evidence.market_freshness.get("freshness_status", "")).strip()
if market_date:
    st.info(f"Market snapshot: {market_date} · {freshness or 'freshness not classified'}")
else:
    st.warning("Market snapshot date unavailable. Treat every comparison as stale until refreshed.")

counts = available["Market"].value_counts()
metrics = st.columns(5)
bands = MARKET_BANDS
for column, band in zip(metrics, bands, strict=True):
    column.metric(band, int(counts.get(band, 0)))

controls = st.columns((2, 1, 1, 1))
query = controls[0].text_input("Find a player")
selected_band = controls[1].selectbox("Signal", ("All", *bands))
positions = sorted(value for value in available["Pos"].unique() if value)
selected_positions = controls[2].multiselect("Position", positions, default=positions)
sort_mode = controls[3].selectbox(
    "Sort",
    (
        "Biggest NWR-over-market opportunity",
        "Biggest market-over-NWR difference",
        "NWR rank",
    ),
)
filtered = available.loc[available["Pos"].isin(selected_positions)]
if selected_band != "All":
    filtered = filtered.loc[filtered["Market"].eq(selected_band)]
if query.strip():
    filtered = filtered.loc[filtered["Player"].str.contains(query.strip(), case=False, regex=False)]
if sort_mode == "Biggest NWR-over-market opportunity":
    filtered = filtered.sort_values("NWR vs Market", ascending=False, na_position="last")
elif sort_mode == "Biggest market-over-NWR difference":
    filtered = filtered.sort_values("NWR vs Market", ascending=True, na_position="last")
else:
    filtered = filtered.sort_values("Rank", ascending=True, na_position="last")

st.dataframe(
    filtered[
        [
            "Rank",
            "Player",
            "Pos",
            "Team",
            "Market",
            "Market Rank",
            "NWR vs Market",
            "Market Value",
            "Market Date",
            "NWR View",
            "Confidence",
            "Risk",
        ]
    ],
    hide_index=True,
    width="stretch",
    column_config={
        "Rank": st.column_config.NumberColumn("NWR Rank", format="#%d"),
        "Market Rank": st.column_config.NumberColumn(format="#%d"),
        "NWR vs Market": st.column_config.NumberColumn(
            format="%+.0f",
            help="Market rank minus NWR rank. Positive means NWR is higher.",
        ),
        "Market Value": st.column_config.NumberColumn(format="%.0f"),
    },
)
if not filtered.empty:
    selected_asset = st.selectbox(
        "Investigate",
        filtered["asset_id"].tolist(),
        format_func=lambda key: filtered.loc[filtered["asset_id"].eq(key), "Player"].iloc[0],
    )
    st.link_button("Open Player Detail", f"/player-detail?asset={quote(selected_asset, safe='')}")

st.caption(
    "Band contract: 20+ rank gap = material; 6–19 = higher; within five ranks = aligned. "
    "The market feed never changes Finished V1 order or score."
)
