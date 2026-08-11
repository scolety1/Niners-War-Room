from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.post_release_status import render_source_freshness  # noqa: E402
from app.components.ui_framework import page_header  # noqa: E402
from src.services.personal_workspace_service import load_store  # noqa: E402
from src.services.post_release_usability_service import freshness_for_sources  # noqa: E402
from src.services.rookie_owner_experience_service import (  # noqa: E402
    load_owner_rookie_board,
    rookie_component_rows,
)

page_header(
    "2026 Rookie Review",
    eyebrow="Why each rookie is ranked here",
    description=(
        "Review all 80 drafted prospects with fantasy draft range, NFL draft capital, "
        "college/model components, and a plain-language explanation of rank versus score."
    ),
    status_items=(
        ("73 ranked", "safe"),
        ("7 visible but unscored", "blocked"),
        ("Review context", "review"),
    ),
)
render_source_freshness(freshness_for_sources(("Model V4 2026 Rookie Review",)))

rookies = load_owner_rookie_board()
personal = {row["asset_id"]: row for row in load_store("personal_board").records}


def _asset_id(row: pd.Series) -> str:
    player_id = str(row.get("player_id") or "").strip()
    if player_id:
        return f"rookie:{player_id}"
    slug = "-".join(str(row["player_name"]).lower().replace("'", "").split())
    return f"blocked-rookie:{slug}"


rookies["asset_id"] = rookies.apply(_asset_id, axis=1)
rookies["My Tier"] = rookies["asset_id"].map(
    lambda key: personal.get(key, {}).get("my_tier", "")
)
rookies["Watchlist"] = rookies["asset_id"].map(
    lambda key: bool(personal.get(key, {}).get("watchlist"))
)

controls = st.columns((2, 2, 1))
query = controls[0].text_input("Find rookie", placeholder="Carnell Tate")
positions = sorted(rookies["position"].unique())
selected = controls[1].multiselect("Position", positions, default=positions)
show_unscored = controls[2].checkbox("Show unscored", value=True)
filtered = rookies.loc[rookies["position"].isin(selected)].copy()
if query.strip():
    filtered = filtered.loc[
        filtered["player_name"].str.contains(query.strip(), case=False, regex=False)
    ]
if not show_unscored:
    filtered = filtered.loc[filtered["overall_review_rank"].str.strip().ne("")]
filtered["_rank"] = pd.to_numeric(filtered["overall_review_rank"], errors="coerce").fillna(9999)
filtered = filtered.sort_values(["_rank", "overall_pick", "player_name"])

display_columns = [
    "Rank",
    "Player",
    "Pos",
    "NFL Team",
    "Rookie draft range",
    "NFL Draft Capital",
    "college",
    "Board Score",
    "Review Score",
    "Why this rank",
    "production_component",
    "market_share_component",
    "age_at_draft",
    "athletic_component",
    "Authority",
    "My Tier",
    "Watchlist",
    "Confidence",
    "Blocked / pending reason",
    "Warnings",
]
st.dataframe(filtered[display_columns], hide_index=True, use_container_width=True)
st.caption(
    "Board Score controls order after league-format and evidence gates. Review Score is a "
    "broader model diagnostic, so a higher Review Score can legitimately rank lower."
)

st.markdown("## Why is this rookie here?")
selected_name = st.selectbox("Rookie", filtered["player_name"].tolist())
detail = rookies.loc[rookies["player_name"].eq(selected_name)].iloc[0].to_dict()
summary = st.columns(4)
summary[0].metric("Rookie rank", detail["Rank"])
summary[1].metric("Draft range", detail["Rookie draft range"])
summary[2].metric("Board Score", detail["Board Score"])
summary[3].metric("Review Score", detail["Review Score"])
st.write(detail["Why this rank"])
if detail["Blocked / pending reason"]:
    st.info(detail["Blocked / pending reason"])
st.dataframe(rookie_component_rows(detail), hide_index=True, use_container_width=True)
st.caption(
    "HELPED / NEUTRAL / HURT reflects the admitted normalized component relative to the "
    "model midpoint. Missing components stay unavailable; no contribution percentage is invented."
)
with st.expander("Warnings and advanced model details", expanded=False):
    st.write(detail["Warnings"] or "No translated warning is available.")
    st.write(
        {
            "confidence_cap": detail.get("confidence_cap", ""),
            "missing_components": detail.get("missing_components", ""),
            "formula_version": detail.get("formula_version", ""),
            "board_formula_version": detail.get("board_formula_version", ""),
            "raw_tier": detail.get("tier", ""),
            "raw_warning_codes": detail.get("warning_codes", ""),
        }
    )

st.link_button("Edit rookie notes and personal tiers", "/personal-board")
st.info(
    "Rookie Review remains a separate decision-context authority. Its scores are not "
    "directly comparable with Finished V1 veteran scores or market values."
)
