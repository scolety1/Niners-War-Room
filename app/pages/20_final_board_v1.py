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
    outcome_display_coverage_counts,
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
    _render_outcome_metrics(dynasty)
    _render_dynasty_source_samples(dynasty)
    filtered = _filter_dynasty_frame(dynasty.frame)
    st.dataframe(
        display_dynasty_rankings_frame(filtered),
        use_container_width=True,
        hide_index=True,
        key="dynasty_rankings_full_table",
    )
    st.caption(
        "Outcome probabilities, market ranks, and league ranks are display-only context. "
        "They do not create, replace, or override NWR Dynasty Score or Dynasty Rank."
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
    cols[2].metric("Rookie flag", dynasty.rookie_count)
    cols[3].metric("Positions", positions)
    cols[4].metric("NWR scored", scored)
    if dynasty.rookie_count == 0:
        st.caption(
            "The approved full-player artifact includes young players, but its "
            "`is_rookie` flag is not populated for a rookie-only split."
        )


def _render_dynasty_source_samples(dynasty: DynastyRankingsBundle) -> None:
    if dynasty.frame.empty or "player_name" not in dynasty.frame.columns:
        return
    top_players = ", ".join(dynasty.frame["player_name"].astype(str).head(3))
    st.caption(f"Top Dynasty rows loaded: {top_players}.")
    outcome_sample = _first_outcome_sample(dynasty.frame)
    if outcome_sample:
        st.caption(f"Outcome display sample: {outcome_sample}.")


def _first_outcome_sample(frame: pd.DataFrame) -> str:
    outcome_columns = (
        ("qb_t12_display_only", "QB T12"),
        ("rb_t12_display_only", "RB T12"),
        ("rb_t24_display_only", "RB T24"),
        ("wr_t12_display_only", "WR T12"),
        ("wr_t24_display_only", "WR T24"),
        ("wr_t36_display_only", "WR T36"),
        ("te_t12_display_only", "TE T12"),
    )
    for _, row in frame.iterrows():
        player = str(row.get("player_name") or "").strip()
        for column, label in outcome_columns:
            value = str(row.get(column) or "").strip()
            if player and value and value != "Not enough information.":
                return f"{player} {label} {value}"
    return ""


def _render_outcome_metrics(dynasty: DynastyRankingsBundle) -> None:
    counts = outcome_display_coverage_counts(dynasty.frame)
    cols = st.columns(3)
    cols[0].metric("Outcome context rows", counts["rows"])
    cols[1].metric("Outcome available", counts["available"])
    cols[2].metric("Outcome not enough info", counts["not_enough_information"])
    st.info(
        "Outcome columns are display-only. Missing or unavailable Outcome cells show "
        "`Not enough information.` and do not drive sorting or ranking."
    )


def _filter_dynasty_frame(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()
    with st.expander("Dynasty Filters", expanded=False):
        cols = st.columns(5)
        position_values = filtered.get("position", pd.Series(dtype=str)).astype(str).unique()
        positions = ["All"] + sorted(value for value in position_values if value)
        position = cols[0].selectbox("Position", positions, key="dynasty_full_position")
        if position != "All" and "position" in filtered.columns:
            filtered = filtered.loc[filtered["position"].astype(str) == position]

        team_values = filtered.get("nfl_team", pd.Series(dtype=str)).astype(str).unique()
        teams = ["All"] + sorted(value for value in team_values if value)
        team = cols[1].selectbox("Team", teams, key="dynasty_full_team")
        if team != "All" and "nfl_team" in filtered.columns:
            filtered = filtered.loc[filtered["nfl_team"].astype(str) == team]

        pool_values = filtered.get("pool_status", pd.Series(dtype=str)).astype(str).unique()
        pools = ["All"] + sorted(value for value in pool_values if value)
        pool = cols[2].selectbox("Status", pools, key="dynasty_full_pool")
        if pool != "All" and "pool_status" in filtered.columns:
            filtered = filtered.loc[filtered["pool_status"].astype(str) == pool]

        rookie_mode = cols[3].selectbox(
            "Rookie/Veteran",
            ["All", "Veterans/current", "Rookie-flagged"],
            key="dynasty_full_rookie_mode",
        )
        if rookie_mode != "All" and "is_rookie" in filtered.columns:
            rookie_mask = (
                filtered["is_rookie"].astype(str).str.lower().isin({"1", "true", "yes"})
            )
            filtered = filtered.loc[
                rookie_mask if rookie_mode == "Rookie-flagged" else ~rookie_mask
            ]

        outcome = cols[4].selectbox(
            "Outcome",
            ["All", "Available", "Not enough information."],
            key="dynasty_full_outcome",
        )
        if outcome != "All" and "outcome_availability_display_only" in filtered.columns:
            filtered = filtered.loc[
                filtered["outcome_availability_display_only"].astype(str) == outcome
            ]

        search = st.text_input("Search", key="dynasty_full_search")
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
