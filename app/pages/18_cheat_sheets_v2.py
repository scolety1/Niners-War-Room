from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import render_source_of_truth_badge, stop_if_board_blocked
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    load_expanded_draftable_player_pool,
    load_frozen_board,
)
from src.services.draft_day_workflow_service import NOT_ENOUGH_INFORMATION, sort_workflow_frame


def _display_cheat_sheet(frame: pd.DataFrame, note_density: str) -> pd.DataFrame:
    base_columns = [
        "dynasty_asset_rank",
        "final_board_rank",
        "player",
        "position",
        "nfl_team",
        "age",
        "position_rank",
        "dynasty_asset_score",
        "dynasty_asset_confidence",
        "main_risk",
    ]
    if note_density in {"Detailed", "Expert"}:
        base_columns.extend(["why_draft", "outcome_applicable_summary", "available_pool_adp_range"])
    if note_density == "Expert":
        base_columns.extend(["source_label_display_only", "candidate_key_caveat"])
    columns = [column for column in base_columns if column in frame.columns]
    display = frame.loc[:, columns].fillna(NOT_ENOUGH_INFORMATION).copy()
    return display.rename(
        columns={
            "dynasty_asset_rank": "Candidate Rank (Review-Only)",
            "final_board_rank": "Final Board Rank",
            "player": "Player",
            "position": "Pos",
            "nfl_team": "NFL Team",
            "age": "Age",
            "position_rank": "Position Rank",
            "dynasty_asset_score": "Candidate Value",
            "dynasty_asset_confidence": "Confidence",
            "main_risk": "Key Risk",
            "why_draft": "Why Draft",
            "outcome_applicable_summary": "Outcome/Horizon",
            "available_pool_adp_range": "ADP Range (Display-Only)",
            "source_label_display_only": "Source",
            "candidate_key_caveat": "Caveat",
        }
    )


bundle = load_frozen_board()
pool = load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame

page_header(
    "Cheat Sheets",
    eyebrow="Draft-Day App V2",
    description=(
        "Overall-first tiered board for fast draft decisions. Position views are secondary, "
        "and all candidate/model context remains review-only."
    ),
    status_items=(
        ("Overall-first", "safe"),
        ("Tiered", "safe"),
        ("No source mutation", "safe"),
    ),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

control_cols = st.columns([1.0, 1.0, 1.0, 1.0, 1.2])
view = control_cols[0].selectbox(
    "View",
    ["Overall", "By Position", "Manual Review"],
    key="cheat_sheet_view",
)
positions = sorted(
    value
    for value in pool.get("position", pd.Series(dtype=str)).astype(str).unique().tolist()
    if value and value.upper() not in {"K", "DST"}
)
selected_positions = control_cols[1].multiselect(
    "Position",
    positions,
    default=positions,
    key="cheat_sheet_positions",
)
limit = control_cols[2].number_input(
    "Players",
    min_value=10,
    max_value=200,
    value=60,
    step=10,
    key="cheat_sheet_limit",
)
note_density = control_cols[3].selectbox(
    "Notes",
    ["Summary", "Detailed", "Expert"],
    key="cheat_sheet_note_density",
)
show_pdf = control_cols[4].toggle(
    "Show PDF free agents",
    value=True,
    key="cheat_sheet_show_pdf",
)

frame = pool.copy()
if selected_positions and "position" in frame.columns:
    frame = frame.loc[frame["position"].astype(str).isin(selected_positions)].copy()
if not show_pdf and "source_group" in frame.columns:
    frame = frame.loc[~frame["source_group"].astype(str).eq("LVE PDF Free Agent")].copy()
if "position" in frame.columns:
    frame = frame.loc[~frame["position"].astype(str).str.upper().isin({"K", "DST"})].copy()
if view == "Manual Review" and "needs_manual_review" in frame.columns:
    frame = frame.loc[
        frame["needs_manual_review"].astype(str).str.lower().isin({"true", "yes", "1"})
    ].copy()

frame = sort_workflow_frame(frame, "Dynasty Asset Tier/Rank").head(int(limit))

st.caption(
    "Use tiers first, then compare Final Board Rank, review-only candidate context, and caveats. "
    "Missing data is shown as Not enough information."
)

if view == "By Position":
    for position in selected_positions:
        position_frame = frame.loc[frame["position"].astype(str).eq(position)].copy()
        if not position_frame.empty:
            st.subheader(position)
            st.dataframe(
                _display_cheat_sheet(position_frame, note_density),
                use_container_width=True,
                hide_index=True,
            )
else:
    tier_column = "dynasty_asset_tier" if "dynasty_asset_tier" in frame.columns else "final_tier"
    if tier_column in frame.columns:
        for tier, tier_frame in frame.groupby(frame[tier_column].fillna(NOT_ENOUGH_INFORMATION)):
            st.subheader(str(tier) or NOT_ENOUGH_INFORMATION)
            st.dataframe(
                _display_cheat_sheet(tier_frame, note_density),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.dataframe(
            _display_cheat_sheet(frame, note_density),
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Source / guardrails", expanded=False):
    st.caption(
        "Cheat Sheets V2 uses the frozen board plus existing app overlay context. It does not "
        "change Final Board Rank, Dynasty Rank, latest files, or pinned snapshots."
    )
    st.caption(f"Rows available before filters: {len(pool)}")
