from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    filter_board_frame,
    render_board_metrics,
    render_final_board_table,
    render_source_of_truth_badge,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    DynastyRankingsBundle,
    display_dynasty_rankings_frame,
    load_dynasty_rankings,
    load_frozen_board,
)


def _render_dynasty_rankings(dynasty: DynastyRankingsBundle) -> None:
    status = "GREEN" if dynasty.loaded else "YELLOW-HOLD"
    source = str(dynasty.source_path or "missing")
    st.info(
        f"Source: Approved full Dynasty Rankings | {status} | "
        f"{dynasty.row_count} rows | {dynasty.source_label} | {source}"
    )
    if dynasty.source_hash:
        st.caption(f"Source hash: `{dynasty.source_hash}`")
    for warning in dynasty.warnings:
        st.warning(warning)
    for error in dynasty.errors:
        st.error(error)

    if not dynasty.loaded:
        st.warning(
            "Dynasty Rankings cannot be fabricated from sample data. Restore the approved "
            "full-board CSV before using this page."
        )
        return

    _render_dynasty_metrics(dynasty)
    filtered = _filter_dynasty_frame(dynasty.frame)
    st.dataframe(
        display_dynasty_rankings_frame(filtered),
        use_container_width=True,
        hide_index=True,
        key="dynasty_rankings_full_table",
    )
    st.caption(
        "Market and league ranks are display-only context. They do not create, replace, "
        "or override NWR Dynasty Score or Dynasty Rank."
    )


def _render_dynasty_metrics(dynasty: DynastyRankingsBundle) -> None:
    positions = (
        int(dynasty.frame["position"].astype(str).nunique())
        if "position" in dynasty.frame.columns
        else 0
    )
    scored = 0
    if "nwr_dynasty_score" in dynasty.frame.columns:
        scored = int(dynasty.frame["nwr_dynasty_score"].astype(str).str.strip().astype(bool).sum())
    cols = st.columns(5)
    cols[0].metric("Dynasty rows", dynasty.row_count)
    cols[1].metric("Veterans", dynasty.veteran_count)
    cols[2].metric("Rookies", dynasty.rookie_count)
    cols[3].metric("Positions", positions)
    cols[4].metric("NWR scored", scored)


def _filter_dynasty_frame(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()
    with st.expander("Dynasty Filters", expanded=False):
        cols = st.columns(4)
        position_values = filtered.get("position", pd.Series(dtype=str)).astype(str).unique()
        positions = ["All"] + sorted(value for value in position_values if value)
        position = cols[0].selectbox("Position", positions, key="dynasty_full_position")
        if position != "All" and "position" in filtered.columns:
            filtered = filtered.loc[filtered["position"].astype(str) == position]

        pool_values = filtered.get("pool_status", pd.Series(dtype=str)).astype(str).unique()
        pools = ["All"] + sorted(value for value in pool_values if value)
        pool = cols[1].selectbox("Status", pools, key="dynasty_full_pool")
        if pool != "All" and "pool_status" in filtered.columns:
            filtered = filtered.loc[filtered["pool_status"].astype(str) == pool]

        rookie_mode = cols[2].selectbox(
            "Rookie/Veteran",
            ["All", "Veterans", "Rookies"],
            key="dynasty_full_rookie_mode",
        )
        if rookie_mode != "All" and "is_rookie" in filtered.columns:
            rookie_mask = (
                filtered["is_rookie"].astype(str).str.lower().isin({"1", "true", "yes"})
            )
            filtered = filtered.loc[rookie_mask if rookie_mode == "Rookies" else ~rookie_mask]

        search = cols[3].text_input("Search", key="dynasty_full_search")
        if search:
            mask = pd.Series(False, index=filtered.index)
            for column in ("player_name", "nfl_team", "position"):
                if column in filtered.columns:
                    mask = mask | filtered[column].astype(str).str.contains(
                        search,
                        case=False,
                        na=False,
                        regex=False,
                    )
            filtered = filtered.loc[mask]
    return filtered


bundle = load_frozen_board()
dynasty_bundle = load_dynasty_rankings()

page_header(
    "Dynasty Rankings / Final Draft Board",
    eyebrow="Draft-Day App V1",
    description=(
        "Dynasty Rankings shows the approved full veteran-plus-rookie rankings artifact. "
        "Final Draft Board remains the frozen 66-row source for draft-day live workflows."
    ),
    status_items=(
        ("Full dynasty rankings", "safe" if dynasty_bundle.loaded else "review"),
        ("Final Draft Board frozen", "safe" if bundle.loaded else "danger"),
        ("No hidden sort", "safe"),
    ),
)

dynasty_tab, final_board_tab = st.tabs(
    ["Dynasty Rankings (Full)", "Final Draft Board (Frozen 66)"]
)

with dynasty_tab:
    _render_dynasty_rankings(dynasty_bundle)

with final_board_tab:
    st.subheader("Final Draft Board")
    render_source_of_truth_badge(bundle)
    stop_if_board_blocked(bundle)

    render_board_metrics(bundle.frame)
    filtered = filter_board_frame(bundle.frame, key_prefix="final_board_v1")
    render_final_board_table(filtered, key="final_board_v1_table")

    st.caption(
        "Final Draft Board uses the frozen 66-row export. The visible final_board_rank, "
        "final_tier, and position_rank columns remain the source of truth for tomorrow's "
        "Live Draft Room and draft-board workflows."
    )
