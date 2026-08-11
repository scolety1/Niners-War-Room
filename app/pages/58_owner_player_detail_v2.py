from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd
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
from src.services.outcome_v3_calibration_service import POSITION_THRESHOLDS  # noqa: E402
from src.services.outcome_v3_display_service import outcome_v3_player_matrix  # noqa: E402
from src.services.owner_caveat_presentation_service import owner_caveat_summary  # noqa: E402
from src.services.owner_mode_view_service import (  # noqa: E402
    market_decision_label,
    owner_range_contract,
    owner_risk,
    translate_research_tier,
)
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
    eyebrow="Owner Mode - One player, one decision hub",
    description="Rank, range, outcomes, market, reasons, risk, and personal context in one place.",
    status_items=(("Governed identity", "safe"), ("Source-separated", "safe")),
)
asset_id = st.selectbox(
    "Find a player, rookie, or future pick",
    ids,
    index=index,
    format_func=lambda key: f"{assets[key]['asset_name']} - {assets[key]['asset_type']}",
)
st.query_params["asset"] = asset_id
asset = assets[asset_id]
current = current_row_by_id(data, asset_id) if asset_id.startswith("current:") else None


def _research_number(value: object, *, prefix: str = "") -> str:
    try:
        return f"{prefix}{float(str(value)):.1f}"
    except ValueError:
        return "Not enough information"


def _research_confidence(value: object) -> str:
    try:
        return f"{float(str(value)):.1%}"
    except ValueError:
        return "Not enough information"

rank = asset.get("dynasty_rank") or asset.get("rank_value") or "Unranked"
owner_intro(
    asset["asset_name"],
    f"{asset['asset_type']} - {asset.get('position') or 'No position'} - "
    f"{asset.get('team') or 'No team'}",
)
identity = st.columns(5)
identity[0].metric(asset.get("rank_label") or "Rank", f"#{rank}" if str(rank).isdigit() else rank)
identity[1].metric("Position rank", asset.get("position_rank") or "-")
identity[2].metric("NWR Score", asset.get("nwr_dynasty_score") or asset.get("score_value") or "-")
identity[3].metric("Age", asset.get("age") or "-")
identity[4].metric("Confidence", asset.get("confidence") or "Not enough information")

st.markdown("### Owner outlook")
range_contract = owner_range_contract(asset)
floor_expected_ceiling(
    range_contract,
    note=f"{range_contract['Authority']}. This context never changes a canonical rank.",
)
with st.expander("How this range is built", expanded=False):
    st.write(range_contract["Method"])

st.markdown("### Outcomes")
position = str(asset.get("position") or "").upper()
if current and data.outcome.loaded and position in POSITION_THRESHOLDS:
    board = pd.DataFrame(
        [
            {
                "player_id": asset_id.split(":", maxsplit=1)[1],
                "player_name": asset["asset_name"],
                "position": position,
                "nwr_rank": asset.get("dynasty_rank", ""),
            }
        ]
    )
    outcome_matrix, outcome_audit, outcome_detail = outcome_v3_player_matrix(
        board,
        data.outcome.frame,
        position=position,
    )
    st.dataframe(outcome_matrix, hide_index=True, width="stretch")
    st.caption(
        f"{outcome_audit.numeric} of {outcome_audit.applicable} applicable cells have "
        f"governed numeric evidence ({outcome_audit.percent:.1f}%)."
    )
    missing = outcome_detail.loc[outcome_detail["Classification"].ne("numeric evidence")]
    if not missing.empty:
        with st.expander("Why some outcomes are unavailable", expanded=False):
            st.dataframe(missing, hide_index=True, width="stretch")
else:
    st.info("No applicable governed Outcome V3 row is available for this asset authority.")
st.link_button("Open full Dynasty Outcomes", "/outcome-columns")

market_col, risk_col = st.columns(2)
with market_col:
    st.markdown("### Market")
    label, gap = market_decision_label(asset.get("dynasty_rank"), asset.get("market_dp_rank"))
    market_readout(label, gap=gap, status=asset.get("market_status", ""))
    if asset.get("market_evidence_date"):
        st.caption(f"Market evidence date: {asset['market_evidence_date']}")
    st.caption("External comparison only; never a model input or trade value.")
with risk_col:
    st.markdown("### Risk / uncertainty")
    st.info(owner_risk(asset))
    if asset.get("warnings") or asset.get("blocking_reason"):
        st.caption(owner_caveat_summary(asset.get("warnings") or asset.get("blocking_reason")))

st.markdown("### Why NWR has them here")
if current:
    summary, receipts, caveat = owner_rank_explanation(
        current, total_ranked=len(data.dynasty.frame)
    )
    st.write(summary)
    for bullet in owner_rank_reason_bullets(current, limit=4):
        st.markdown(f"- {bullet}")
    with st.expander("Show score receipts", expanded=False):
        st.dataframe(receipts, hide_index=True, width="stretch")
    if caveat:
        st.warning(caveat)
else:
    st.info("Finished V1 scoring reasons do not apply to this asset authority.")

if asset.get("research_rank") or asset.get("research_tier"):
    research_heading = (
        "Rookie / research context"
        if asset.get("asset_type") in {"Rookie Review", "Blocked Rookie"}
        else "Research context"
    )
    st.markdown(f"### {research_heading}")
    research = st.columns(5)
    research[0].metric(
        "Research rank", _research_number(asset.get("research_rank"), prefix="#")
    )
    research[1].metric("Research tier", translate_research_tier(asset.get("research_tier")))
    research[2].metric(
        "3-year research score", _research_number(asset.get("research_outlook_3y"))
    )
    research[3].metric(
        "5-year research score", _research_number(asset.get("research_outlook_5y"))
    )
    research[4].metric(
        "Research confidence", _research_confidence(asset.get("research_confidence"))
    )
    st.caption("Frozen research context only; it is not a production dynasty rank or score.")

st.markdown("### My context")
personal = next(
    (row for row in load_store("personal_board").records if row.get("asset_id") == asset_id), {}
)
personal_columns = st.columns(4)
personal_columns[0].metric("Watchlist", "Yes" if personal.get("watchlist") else "No")
personal_columns[1].metric("Target", "Yes" if personal.get("target") else "No")
personal_columns[2].metric("Avoid", "Yes" if personal.get("avoid") else "No")
personal_columns[3].metric("My tier", personal.get("my_tier") or "-")
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
