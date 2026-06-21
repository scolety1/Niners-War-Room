from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.draft_day_app_v1_service import (
    FrozenBoardBundle,
    display_board_frame,
    lane_prop_status_rows,
)


def render_source_of_truth_badge(bundle: FrozenBoardBundle) -> None:
    status = "GREEN" if bundle.loaded else "RED"
    source = str(bundle.source_path or "missing")
    st.info(
        f"Source of truth: Frozen Final Draft Board V1 | {status} | "
        f"{bundle.row_count} rows | {bundle.source_label} | {source}"
    )
    for warning in bundle.warnings:
        st.warning(warning)
    for error in bundle.errors:
        st.error(error)


def stop_if_board_blocked(bundle: FrozenBoardBundle) -> None:
    if not bundle.loaded:
        st.stop()


def render_board_metrics(frame: pd.DataFrame) -> None:
    manual_count = 0
    if "needs_manual_review" in frame.columns:
        manual_count = int(
            frame["needs_manual_review"].astype(str).str.lower().isin({"true", "yes", "1"}).sum()
        )
    positions = int(frame["position"].astype(str).nunique()) if "position" in frame.columns else 0
    candidates = (
        int(frame["candidate_status"].astype(str).nunique())
        if "candidate_status" in frame.columns
        else 0
    )
    cols = st.columns(4)
    cols[0].metric("Frozen rows", len(frame))
    cols[1].metric("Positions", positions)
    cols[2].metric("Manual flags", manual_count)
    cols[3].metric("Candidate statuses", candidates)


def filter_board_frame(frame: pd.DataFrame, *, key_prefix: str) -> pd.DataFrame:
    filtered = frame.copy()
    with st.expander("Filters", expanded=False):
        cols = st.columns(4)
        position_values = filtered.get("position", pd.Series(dtype=str)).astype(str).unique()
        positions = ["All"] + sorted(
            value for value in position_values if value
        )
        position = cols[0].selectbox("Position", positions, key=f"{key_prefix}_position")
        if position != "All" and "position" in filtered.columns:
            filtered = filtered.loc[filtered["position"].astype(str) == position]

        tier_values = filtered.get("final_tier", pd.Series(dtype=str)).astype(str).unique()
        tiers = ["All"] + sorted(
            value for value in tier_values if value
        )
        tier = cols[1].selectbox("Tier", tiers, key=f"{key_prefix}_tier")
        if tier != "All" and "final_tier" in filtered.columns:
            filtered = filtered.loc[filtered["final_tier"].astype(str) == tier]

        statuses = ["All"] + sorted(
            value
            for value in filtered.get("candidate_status", pd.Series(dtype=str)).astype(str).unique()
            if value
        )
        status = cols[2].selectbox("Candidate status", statuses, key=f"{key_prefix}_status")
        if status != "All" and "candidate_status" in filtered.columns:
            filtered = filtered.loc[filtered["candidate_status"].astype(str) == status]

        manual_only = cols[3].checkbox("Manual review only", key=f"{key_prefix}_manual")
        if manual_only and "needs_manual_review" in filtered.columns:
            mask = (
                filtered["needs_manual_review"]
                .astype(str)
                .str.lower()
                .isin({"true", "yes", "1"})
            )
            filtered = filtered.loc[mask]

        search = st.text_input("Search", key=f"{key_prefix}_search")
        if search and "player" in filtered.columns:
            mask = filtered["player"].astype(str).str.contains(search, case=False, na=False)
            filtered = filtered.loc[mask]
    return filtered


def render_final_board_table(frame: pd.DataFrame, *, key: str) -> None:
    st.dataframe(display_board_frame(frame), use_container_width=True, hide_index=True, key=key)


def render_lane_status_table() -> None:
    st.dataframe(pd.DataFrame(lane_prop_status_rows()), use_container_width=True, hide_index=True)


def render_yellow_hold(message: str) -> None:
    st.warning(f"YELLOW-HOLD: {message}")
