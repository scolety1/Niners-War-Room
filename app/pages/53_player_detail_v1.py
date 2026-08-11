from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.player_detail_card import render_player_detail_card
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    load_dynasty_rankings,
    resolve_dynasty_rankings_path,
)
from src.services.governed_asset_registry_service import load_governed_asset_registry
from src.services.outcome_v3_calibration_service import POSITION_THRESHOLDS
from src.services.outcome_v3_display_service import (
    load_outcome_v3_display,
    rankings_outcome_v3_rows,
)
from src.services.owner_asset_evidence_service import compose_owner_asset_evidence
from src.services.owner_caveat_presentation_service import owner_caveat_summary
from src.services.personal_workspace_service import load_store
from src.services.player_detail_card_service import build_player_detail_card_payload
from src.services.unified_research_preview_service import load_unified_research_preview


@st.cache_data
def _sources():
    current_path, _label, _warnings = resolve_dynasty_rankings_path()
    registry = load_governed_asset_registry(
        repo_root=REPO_ROOT,
        current_board_path=current_path,
    )
    dynasty = load_dynasty_rankings()
    research = load_unified_research_preview()
    outcome = load_outcome_v3_display()
    evidence = compose_owner_asset_evidence(
        registry.rows,
        dynasty_frame=dynasty.frame,
        research_frame=research.board,
        outcome_frame=outcome.frame,
    )
    return registry, dynasty, research, outcome, evidence


registry, dynasty, research, outcome, evidence = _sources()
rows_by_id = evidence.by_id
asset_ids = sorted(rows_by_id, key=lambda key: (rows_by_id[key]["asset_name"], key))
requested = str(st.query_params.get("asset", "")).strip()
default_index = asset_ids.index(requested) if requested in rows_by_id else 0

page_header(
    "Player Detail",
    eyebrow="One governed asset · source-separated evidence",
    description=(
        "See identity, admitted rank context, approximate score receipts, useful Outcome V3 and "
        "market evidence, personal context, caveats, and provenance without blending authorities."
    ),
    status_items=(("Read-only", "safe"), ("No new model", "safe"), ("Exact IDs", "safe")),
)

asset_id = st.selectbox(
    "Search governed veteran, rookie, blocked prospect, or pick",
    asset_ids,
    index=default_index,
    format_func=lambda key: (
        f"{rows_by_id[key]['asset_name']} · {rows_by_id[key]['asset_type']} · "
        f"{rows_by_id[key]['authority_status']}"
    ),
)
st.query_params["asset"] = asset_id
asset = rows_by_id[asset_id]

st.subheader(asset["asset_name"])
identity = st.columns(6)
identity[0].metric("Asset type", asset["asset_type"])
identity[1].metric("Position", asset["position"] or "—")
identity[2].metric("Team", asset["team"] or "—")
identity[3].metric(asset["rank_label"], asset["rank_value"] or "Unranked")
identity[4].metric("Position rank", asset.get("position_rank") or "—")
identity[5].metric("Authority", asset["authority_status"])

current_row: dict[str, object] | None = None
if asset_id.startswith("current:") and dynasty.loaded:
    player_id = asset_id.removeprefix("current:")
    match = dynasty.frame.loc[dynasty.frame["player_id"].astype(str).eq(player_id)]
    if not match.empty:
        current_row = match.iloc[0].to_dict()
        st.markdown("## Dynasty")
        render_player_detail_card(build_player_detail_card_payload(current_row))
else:
    st.markdown("## Source authority")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Source": asset["source_label"],
                    "Rank": asset["rank_value"] or "Not ranked",
                    "Tier": asset["tier"] or "Not available",
                    "Score": asset["score_value"] or "Not available",
                    "Confidence / uncertainty": asset["confidence"] or "Not available",
                    "Scope": asset["comparison_scope"],
                }
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )

st.markdown("## Unified Research")
research_row = research.board.loc[research.board["source_asset_id"].astype(str).eq(asset_id)]
if research_row.empty:
    st.caption("No Unified Research row is available for this asset.")
else:
    st.warning("Research Only · not production authority and not a trade value.")
    st.dataframe(
        research_row[
            [
                "research_rank",
                "research_tier",
                "outlook_3y",
                "outlook_5y",
                "ceiling_signal",
                "downside_signal",
                "confidence",
                "evidence_coverage",
                "status",
                "blocking_reason",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

st.markdown("## Outcomes · V3 canonical lens")
if current_row and outcome.loaded and str(current_row.get("position")) in POSITION_THRESHOLDS:
    position = str(current_row["position"])
    threshold = st.selectbox(
        "Applicable finish threshold",
        POSITION_THRESHOLDS[position],
        format_func=lambda value: f"{position} T{value}",
    )
    outcome_rows = rankings_outcome_v3_rows(
        pd.DataFrame([current_row]),
        outcome.frame,
        position=position,
        threshold=int(threshold),
    )
    st.dataframe(outcome_rows, hide_index=True, use_container_width=True)
else:
    st.caption("Outcome V3 is unavailable or not applicable for this asset; no value is inferred.")

st.markdown("## Market")
if current_row:
    if asset.get("market_dp_value") or asset.get("market_dp_rank"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "DP 1QB market rank": asset.get("market_dp_rank", ""),
                        "DP 1QB display value": asset.get("market_dp_value", ""),
                        "Join": asset.get("market_join", ""),
                        "Evidence date": asset.get("market_evidence_date", ""),
                        "Status": asset.get("market_status", ""),
                    }
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.caption("External display-only context; never a model input, rank, or trade value.")
    else:
        st.caption("Market data unavailable for this asset.")
else:
    st.caption("Market evidence is not admitted for this asset type.")

st.markdown("## Components / why approximately")
if current_row:
    component_fields = {
        "NWR score": "nwr_dynasty_score",
        "Confidence cap": "confidence_cap",
        "Confidence": "confidence_status",
        "Admitted adjustment": "candidate_adjustment",
        "Reason / gate codes": "candidate_reason_codes",
        "Evidence fields used": "candidate_evidence_fields_used",
        "Confidence impact": "candidate_confidence_trust_impact",
        "Risk": "risk_level",
        "Data needed": "data_needed",
    }
    st.dataframe(
        pd.DataFrame(
            {"Evidence": label, "Value": current_row.get(column, "") or "—"}
            for label, column in component_fields.items()
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.caption("Exact weighted contribution percentages are not admitted and are omitted.")
else:
    st.caption("No Finished V1 score receipts apply to this asset.")

st.markdown("## Personal")
personal = next(
    (row for row in load_store("personal_board").records if row.get("asset_id") == asset_id),
    {},
)
st.dataframe(
    pd.DataFrame(
        [
            {
                "Watchlist": bool(personal.get("watchlist")),
                "Target": bool(personal.get("target")),
                "Avoid": bool(personal.get("avoid")),
                "My tier": personal.get("my_tier", ""),
                "My rank": personal.get("my_rank", ""),
                "Tags": ", ".join(personal.get("tags", [])),
                "Notes": personal.get("notes", ""),
            }
        ]
    ),
    hide_index=True,
    use_container_width=True,
)
st.link_button("Edit personal context in My Board", "/personal-board")

st.markdown("## Caveats")
st.write(
    owner_caveat_summary(
        asset.get("raw_caveat_codes")
        or asset["blocking_reason"]
        or asset["warnings"]
        or asset["comparison_scope"]
    )
)
with st.expander("Advanced Data Details", expanded=False):
    st.write(
        {
            "asset_id": asset_id,
            "source": asset["source_label"],
            "authority": asset["authority_status"],
            "comparison_scope": asset["comparison_scope"],
            "registry_source_hashes": registry.source_hashes,
            "outcome_v3_hash": outcome.source_hash if outcome.loaded else "unavailable",
            "outcome_v3_release": outcome.release_identifier,
            "raw_caveat_codes": asset.get("raw_caveat_codes", ""),
        }
    )
