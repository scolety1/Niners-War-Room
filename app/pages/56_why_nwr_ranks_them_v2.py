from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_data import current_row_by_id, load_owner_data  # noqa: E402
from app.components.owner_mode import (  # noqa: E402
    floor_expected_ceiling,
    market_readout,
    owner_intro,
)
from app.components.ui_framework import page_header  # noqa: E402
from src.services.owner_mode_view_service import market_decision_label, owner_range  # noqa: E402
from src.services.player_rank_owner_explanation_service import (  # noqa: E402
    owner_rank_explanation,
    owner_rank_reason_bullets,
)

data = load_owner_data(str(REPO_ROOT))
assets = {row["asset_id"]: row for row in data.current_rows}
requested = str(st.query_params.get("asset", "")).strip()
ids = sorted(assets, key=lambda key: int(float(assets[key].get("dynasty_rank") or 9999)))
index = ids.index(requested) if requested in ids else 0

page_header(
    "Why NWR Ranks Them",
    eyebrow="NWR's signature explanation tool",
    description="A concise answer first, with the admitted receipts available underneath.",
    status_items=(("Finished V1 order", "safe"), ("No invented weights", "safe")),
)
asset_id = st.selectbox(
    "Player",
    ids,
    index=index,
    format_func=lambda key: (
        f"#{assets[key]['dynasty_rank']} {assets[key]['asset_name']} · {assets[key]['position']}"
    ),
)
st.query_params["asset"] = asset_id
asset = assets[asset_id]
current = current_row_by_id(data, asset_id)
if current is None:
    st.error("The accepted Finished V1 receipt is unavailable for this player.")
    st.stop()

summary, receipts, caveat = owner_rank_explanation(current, total_ranked=len(data.dynasty.frame))
owner_intro(asset["asset_name"], summary)
identity = st.columns(5)
identity[0].metric("Overall", f"#{asset['dynasty_rank']}")
identity[1].metric("Position", asset.get("position_rank") or asset["position"])
identity[2].metric("Team", asset.get("team") or "—")
identity[3].metric("NWR Score", asset.get("nwr_dynasty_score") or "—")
identity[4].metric("Confidence", asset.get("confidence") or "Not enough information")

st.markdown("### The short answer")
bullets = owner_rank_reason_bullets(current)
if bullets:
    for bullet in bullets:
        st.markdown(f"- {bullet}")
else:
    st.info("The rank is admitted, but a more detailed component receipt is not available.")

st.markdown("### Floor / Expected / Ceiling")
floor_expected_ceiling(
    owner_range(asset),
    note="Research context only. These labels do not change the Finished V1 rank or score.",
)

st.markdown("### NWR versus market")
label, gap = market_decision_label(asset.get("dynasty_rank"), asset.get("market_dp_rank"))
market_readout(label, gap=gap, status=asset.get("market_status", ""))

with st.expander("Show admitted receipts", expanded=False):
    st.dataframe(receipts, hide_index=True, use_container_width=True)
    st.caption(
        "Exact weighted contribution percentages are not admitted and are intentionally omitted."
    )
if caveat:
    st.warning(caveat)
