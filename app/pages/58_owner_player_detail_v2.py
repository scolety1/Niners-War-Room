from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.owner_data import current_row_by_id, load_owner_data  # noqa: E402
from app.components.owner_mode import (  # noqa: E402
    advanced_details,
    floor_expected_ceiling,
    market_readout,
    owner_intro,
)
from app.components.ui_framework import page_header  # noqa: E402
from src.services.owner_caveat_presentation_service import owner_caveat_summary  # noqa: E402
from src.services.owner_mode_view_service import market_decision_label, owner_range  # noqa: E402
from src.services.personal_workspace_service import load_store  # noqa: E402
from src.services.player_rank_owner_explanation_service import (  # noqa: E402
    owner_rank_explanation,
    owner_rank_reason_bullets,
)

data = load_owner_data(str(REPO_ROOT))
assets = {row["asset_id"]: row for row in data.evidence.rows}
ids = sorted(assets, key=lambda key: (assets[key]["asset_name"], key))
requested = str(st.query_params.get("asset", "")).strip()
index = ids.index(requested) if requested in ids else 0

page_header(
    "Player Detail",
    eyebrow="Owner Mode · One player, one decision hub",
    description="Rank, range, outcomes, market, reasons, and personal context in one place.",
    status_items=(("Governed identity", "safe"), ("Source-separated", "safe")),
)
asset_id = st.selectbox(
    "Find a player, rookie, or future pick",
    ids,
    index=index,
    format_func=lambda key: f"{assets[key]['asset_name']} · {assets[key]['asset_type']}",
)
st.query_params["asset"] = asset_id
asset = assets[asset_id]
current = current_row_by_id(data, asset_id) if asset_id.startswith("current:") else None

rank = asset.get("dynasty_rank") or asset.get("rank_value") or "Unranked"
owner_intro(
    asset["asset_name"],
    f"{asset['asset_type']} · {asset.get('position') or 'No position'} · "
    f"{asset.get('team') or 'No team'}",
)
identity = st.columns(5)
identity[0].metric(asset.get("rank_label") or "Rank", f"#{rank}" if str(rank).isdigit() else rank)
identity[1].metric("Position rank", asset.get("position_rank") or "—")
identity[2].metric("NWR Score", asset.get("nwr_dynasty_score") or asset.get("score_value") or "—")
identity[3].metric("Age", asset.get("age") or "—")
identity[4].metric("Confidence", asset.get("confidence") or "Not enough information")

st.markdown("### Owner outlook")
floor_expected_ceiling(
    owner_range(asset),
    note="Dynasty range uses frozen research context only and never changes the canonical rank.",
)

left, right = st.columns(2)
with left:
    st.markdown("### Outcomes")
    signals = tuple(asset.get("outcome_signals") or ())
    if signals:
        for signal in signals:
            st.write(signal)
    else:
        st.info("No applicable governed Outcome V3 signal is available for this asset.")
    st.link_button("Open full Dynasty Outcomes", "/outcome-columns", use_container_width=True)
with right:
    st.markdown("### Market")
    label, gap = market_decision_label(asset.get("dynasty_rank"), asset.get("market_dp_rank"))
    market_readout(label, gap=gap, status=asset.get("market_status", ""))
    st.caption("External comparison only; never a model input or trade value.")

st.markdown("### Why NWR has them here")
if current:
    summary, receipts, caveat = owner_rank_explanation(
        current, total_ranked=len(data.dynasty.frame)
    )
    st.write(summary)
    for bullet in owner_rank_reason_bullets(current, limit=4):
        st.markdown(f"- {bullet}")
    with st.expander("Show score receipts", expanded=False):
        st.dataframe(receipts, hide_index=True, use_container_width=True)
    if caveat:
        st.warning(caveat)
else:
    st.info("Finished V1 scoring reasons do not apply to this asset authority.")

st.markdown("### My context")
personal = next(
    (row for row in load_store("personal_board").records if row.get("asset_id") == asset_id), {}
)
personal_columns = st.columns(4)
personal_columns[0].metric("Watchlist", "Yes" if personal.get("watchlist") else "No")
personal_columns[1].metric("Target", "Yes" if personal.get("target") else "No")
personal_columns[2].metric("Avoid", "Yes" if personal.get("avoid") else "No")
personal_columns[3].metric("My tier", personal.get("my_tier") or "—")
if personal.get("notes"):
    st.write(personal["notes"])
st.link_button("Edit in My Board", "/personal-board")

advanced_details(
    "Advanced source details",
    {
        "asset_id": asset_id,
        "source": asset.get("source_label"),
        "authority": asset.get("authority_status"),
        "comparison_scope": asset.get("comparison_scope"),
        "research_status": asset.get("research_status"),
        "market_join": asset.get("market_join"),
        "caveat": owner_caveat_summary(
            asset.get("raw_caveat_codes") or asset.get("blocking_reason") or asset.get("warnings")
        ),
    },
)

actions = st.columns(3)
actions[0].link_button(
    "Why NWR Ranks Them",
    f"/why-nwr-ranks?asset={quote(asset_id, safe='')}",
    use_container_width=True,
)
actions[1].link_button("Compare Players", "/player-compare", use_container_width=True)
actions[2].link_button("Analyze Trade", "/trading-lab", use_container_width=True)
