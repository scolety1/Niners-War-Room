from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_source_of_truth_badge,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    OUTCOME_NOT_ENOUGH_INFORMATION,
    DynastyRankingsBundle,
    FrozenBoardBundle,
    build_unified_player_board,
    display_unified_player_board_frame,
    frozen_board_outcome_support_counts,
    load_dynasty_rankings,
    load_frozen_board,
    outcome_display_coverage_counts,
    sort_unified_player_board_for_view,
)


def _render_source_badges(
    dynasty: DynastyRankingsBundle,
    frozen_board: FrozenBoardBundle,
) -> None:
    status = "GREEN" if dynasty.loaded else "YELLOW-HOLD"
    source = str(dynasty.source_path or "missing")
    st.info(
        f"Source: Approved full Dynasty Rankings | {status} | "
        f"{dynasty.row_count} rows | {dynasty.source_label} | {source}"
    )
    if dynasty.source_hash:
        st.caption(f"Dynasty source hash: `{dynasty.source_hash}`")
    for warning in dynasty.warnings:
        st.warning(warning)
    for error in dynasty.errors:
        st.error(error)

    render_source_of_truth_badge(frozen_board)
    stop_if_board_blocked(frozen_board)


def _render_player_board_metrics(
    unified: pd.DataFrame,
    dynasty: DynastyRankingsBundle,
    frozen_board: FrozenBoardBundle,
) -> None:
    board_only = _source_count(unified, "Frozen Draft Board only")
    outcome_counts = outcome_display_coverage_counts(unified)
    frozen_outcome = frozen_board_outcome_support_counts(frozen_board.frame)
    cols = st.columns(5)
    cols[0].metric("Unified rows", int(unified.shape[0]))
    cols[1].metric("Full dynasty rows", dynasty.row_count)
    cols[2].metric("Frozen board rows", frozen_board.row_count)
    cols[3].metric("Draft-board only", board_only)
    cols[4].metric(
        "Frozen-board Outcome support",
        f"{frozen_outcome['supported']} / {frozen_outcome['rows']}",
    )
    st.info(
        "Outcome Display-Only columns are display-only context. Missing or unavailable "
        f"Outcome cells show `{OUTCOME_NOT_ENOUGH_INFORMATION}` and do not drive "
        "sorting or ranking."
    )
    st.caption(
        "Default order: Full Dynasty Rank is the dynasty order; Final Board Rank is the "
        "frozen draft-board order. Source Coverage is informational only and is not the "
        "primary sort."
    )
    st.caption(
        "Frozen-board-only rows keep their Final Board Rank and show `Draft-board only` "
        "or `Not enough information` where the approved dynasty source has no row."
    )
    st.caption(
        "Outcome coverage in this player board: "
        f"{outcome_counts['available']} available / {outcome_counts['rows']} rows; "
        f"{outcome_counts['not_enough_information']} rows need more information."
    )


def _source_count(frame: pd.DataFrame, source_coverage: str) -> int:
    if "source_coverage" not in frame.columns:
        return 0
    return int(frame["source_coverage"].astype(str).eq(source_coverage).sum())


def _render_player_board_samples(frame: pd.DataFrame) -> None:
    if frame.empty or "player_name" not in frame.columns:
        return
    veteran_sample = _first_player_match(frame, ("Christian McCaffrey", "Puka Nacua"))
    board_prospect_sample = _first_source_match(frame, "Frozen Draft Board only")
    outcome_sample = _first_outcome_sample(frame)
    if veteran_sample:
        st.caption(f"Veteran proof row loaded: {veteran_sample}.")
    if board_prospect_sample:
        st.caption(
            "Frozen-board rookie/prospect proof row loaded: "
            f"{board_prospect_sample}."
        )
    if outcome_sample:
        st.caption(f"Outcome display sample: {outcome_sample}.")


def _first_player_match(frame: pd.DataFrame, names: tuple[str, ...]) -> str:
    for name in names:
        rows = frame.loc[frame["player_name"].astype(str).str.casefold() == name.casefold()]
        if rows.empty:
            continue
        row = rows.iloc[0]
        source = str(row.get("source_coverage") or "").strip()
        position = str(row.get("position") or "").strip()
        return f"{name} ({position}, {source})"
    return ""


def _first_source_match(frame: pd.DataFrame, source_coverage: str) -> str:
    if "source_coverage" not in frame.columns:
        return ""
    rows = frame.loc[frame["source_coverage"].astype(str) == source_coverage]
    if rows.empty:
        return ""
    row = rows.iloc[0]
    player = str(row.get("player_name") or "").strip()
    position = str(row.get("position") or "").strip()
    final_rank = str(row.get("final_board_rank") or "").strip()
    rank_text = f", Final Board Rank {final_rank}" if final_rank else ""
    return f"{player} ({position}, {source_coverage}{rank_text})"


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
            if player and value and value != OUTCOME_NOT_ENOUGH_INFORMATION:
                return f"{player} {label} {value}"
    return ""


def _filter_player_board_frame(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()
    view_mode = st.radio(
        "View mode",
        ["Unified Review View", "Full Dynasty source", "Frozen Draft Board"],
        horizontal=True,
        key="dynasty_player_board_view_mode",
    )
    if view_mode == "Full Dynasty source" and "source_coverage" in filtered.columns:
        filtered = filtered.loc[
            filtered["source_coverage"].astype(str).str.startswith("Full Dynasty source")
        ]
    elif view_mode == "Frozen Draft Board" and "final_board_rank" in filtered.columns:
        filtered = filtered.loc[filtered["final_board_rank"].astype(str).str.strip().astype(bool)]

    with st.expander("Player Board Filters", expanded=False):
        cols = st.columns(4)
        position_values = filtered.get("position", pd.Series(dtype=str)).astype(str).unique()
        positions = ["All"] + sorted(value for value in position_values if value)
        position = cols[0].selectbox("Position", positions, key="dynasty_player_board_position")
        if position != "All" and "position" in filtered.columns:
            filtered = filtered.loc[filtered["position"].astype(str) == position]

        source_values = filtered.get("source_coverage", pd.Series(dtype=str)).astype(str).unique()
        sources = ["All"] + sorted(value for value in source_values if value)
        source = cols[1].selectbox("Source Coverage", sources, key="dynasty_player_board_source")
        if source != "All" and "source_coverage" in filtered.columns:
            filtered = filtered.loc[filtered["source_coverage"].astype(str) == source]

        outcome = cols[2].selectbox(
            "Outcome",
            ["All", "Available", OUTCOME_NOT_ENOUGH_INFORMATION],
            key="dynasty_player_board_outcome",
        )
        if outcome != "All" and "outcome_availability_display_only" in filtered.columns:
            filtered = filtered.loc[
                filtered["outcome_availability_display_only"].astype(str) == outcome
            ]

        manual_only = cols[3].checkbox("Manual review only", key="dynasty_player_board_manual")
        if manual_only and "needs_manual_review" in filtered.columns:
            filtered = filtered.loc[
                filtered["needs_manual_review"].astype(str).str.lower().isin({"true", "yes", "1"})
            ]

        search = st.text_input("Search", key="dynasty_player_board_search")
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
    filtered = sort_unified_player_board_for_view(filtered, view_mode)
    st.caption(f"Rows shown: {int(filtered.shape[0])}")
    return filtered


bundle = load_frozen_board()
dynasty_bundle = load_dynasty_rankings()
unified_board = build_unified_player_board(dynasty_bundle.frame, bundle.frame)

page_header(
    "Dynasty Rankings / Player Board",
    eyebrow="Draft-Day App V1",
    description=(
        "One player-board surface for full dynasty rankings plus frozen draft-board context. "
        "Final Draft Board remains the frozen 66-row source for draft-day workflows."
    ),
    status_items=(
        ("Full dynasty rankings", "safe" if dynasty_bundle.loaded else "review"),
        ("Final Draft Board frozen", "safe" if bundle.loaded else "danger"),
        ("No hidden sort", "safe"),
    ),
)

_render_source_badges(dynasty_bundle, bundle)
if not dynasty_bundle.loaded:
    st.warning(
        "Full Dynasty Rankings cannot be fabricated from sample data. Frozen-board rows remain "
        "visible as draft-board-only context until the approved dynasty source is available."
    )

_render_player_board_metrics(unified_board, dynasty_bundle, bundle)
_render_player_board_samples(unified_board)
filtered_board = _filter_player_board_frame(unified_board)
st.dataframe(
    display_unified_player_board_frame(filtered_board),
    use_container_width=True,
    hide_index=True,
    key="dynasty_unified_player_board_table",
)
st.caption(
    "This table does not create, replace, or override Final Board Rank, NWR Dynasty Score, "
    "Dynasty Rank, or Outcome probabilities."
)
