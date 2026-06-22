from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    FULL_DYNASTY_VIEW,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    ROOKIES_DRAFT_BOARD_VIEW,
    UNIFIED_REVIEW_VIEW,
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

VIEW_MODES = (FULL_DYNASTY_VIEW, ROOKIES_DRAFT_BOARD_VIEW, UNIFIED_REVIEW_VIEW)
SORT_COLUMNS = {
    "Dynasty Rank": "nwr_rank",
    "Final Board Rank": "final_board_rank",
    "Position Rank": "position_rank",
    "Age": "age",
    "Player": "player_name",
}


def _source_count(frame: pd.DataFrame, source_coverage: str) -> int:
    if "source_coverage" not in frame.columns:
        return 0
    return int(frame["source_coverage"].astype(str).eq(source_coverage).sum())


def _supported_age_count(frame: pd.DataFrame) -> int:
    if "age" not in frame.columns:
        return 0
    ages = pd.to_numeric(frame["age"], errors="coerce")
    return int(ages.notna().sum())


def _view_base_frame(frame: pd.DataFrame, view_mode: str) -> pd.DataFrame:
    filtered = frame.copy()
    if view_mode == FULL_DYNASTY_VIEW and "source_coverage" in filtered.columns:
        filtered = filtered.loc[
            filtered["source_coverage"].astype(str).str.startswith("Full Dynasty source")
        ].copy()
    elif view_mode == ROOKIES_DRAFT_BOARD_VIEW and "final_board_rank" in filtered.columns:
        filtered = filtered.loc[
            filtered["final_board_rank"].astype(str).str.strip().astype(bool)
        ].copy()
    return filtered


def _apply_player_filters(frame: pd.DataFrame, view_mode: str) -> tuple[pd.DataFrame, str]:
    filtered = _view_base_frame(frame, view_mode)
    filter_row_one = st.columns([1.4, 1.2, 1.2, 1.0])
    search = filter_row_one[0].text_input(
        "Search player",
        key="dynasty_rankings_search",
        placeholder="Type a player, team, or position",
    )
    position_values = _column_values(filtered, "position")
    selected_positions = filter_row_one[1].multiselect(
        "Position",
        position_values,
        default=position_values,
        key="dynasty_rankings_positions",
    )
    source_filter = filter_row_one[2].selectbox(
        "Source / player type",
        [
            "All",
            "Rookies / prospects",
            "Veterans",
            "Full Dynasty source",
            "Frozen Draft Board only",
        ],
        key="dynasty_rankings_source_filter",
    )
    team_values = ["All", *_column_values(filtered, "nfl_team")]
    selected_team = filter_row_one[3].selectbox(
        "NFL Team",
        team_values,
        key="dynasty_rankings_team",
    )

    filter_row_two = st.columns([1.2, 1.1, 1.0, 1.4])
    outcome_filter = filter_row_two[0].selectbox(
        "Outcome availability",
        ["All", "Has Outcome support", OUTCOME_NOT_ENOUGH_INFORMATION],
        key="dynasty_rankings_outcome_filter",
    )
    sort_default = _default_sort_label(view_mode)
    sort_options = _sort_options_for_view(view_mode)
    sort_by = filter_row_two[1].selectbox(
        "Sort by",
        sort_options,
        index=sort_options.index(sort_default),
        key=f"dynasty_rankings_sort_by_{view_mode}",
    )
    ascending = filter_row_two[2].toggle(
        "Ascending",
        value=True,
        key="dynasty_rankings_ascending",
    )
    _render_age_filter(filter_row_two[3], filtered)

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
        filtered = filtered.loc[mask].copy()
    if selected_positions and "position" in filtered.columns:
        filtered = filtered.loc[filtered["position"].astype(str).isin(selected_positions)].copy()
    if selected_team != "All" and "nfl_team" in filtered.columns:
        filtered = filtered.loc[filtered["nfl_team"].astype(str) == selected_team].copy()
    if source_filter == "Rookies / prospects":
        filtered = _filter_asset_type(filtered, "rookie")
    elif source_filter == "Veterans":
        filtered = _filter_asset_type(filtered, "veteran")
    elif source_filter == "Full Dynasty source" and "source_coverage" in filtered.columns:
        filtered = filtered.loc[
            filtered["source_coverage"].astype(str).str.startswith("Full Dynasty source")
        ].copy()
    elif source_filter == "Frozen Draft Board only" and "source_coverage" in filtered.columns:
        filtered = filtered.loc[
            filtered["source_coverage"].astype(str).eq("Frozen Draft Board only")
        ].copy()
    if outcome_filter == "Has Outcome support" and "outcome_availability_display_only" in filtered:
        filtered = filtered.loc[
            filtered["outcome_availability_display_only"].astype(str).eq("Available")
        ].copy()
    elif (
        outcome_filter == OUTCOME_NOT_ENOUGH_INFORMATION
        and "outcome_availability_display_only" in filtered
    ):
        filtered = filtered.loc[
            filtered["outcome_availability_display_only"].astype(str).eq(
                OUTCOME_NOT_ENOUGH_INFORMATION
            )
        ].copy()

    filtered = _sort_player_board(filtered, sort_by, ascending=ascending, view_mode=view_mode)
    return filtered, sort_by


def _render_age_filter(container: st.delta_generator.DeltaGenerator, frame: pd.DataFrame) -> None:
    ages = pd.to_numeric(frame.get("age", pd.Series(dtype=str)), errors="coerce").dropna()
    if ages.empty:
        container.caption("Age filter: Not enough information")
        return
    minimum = float(ages.min())
    maximum = float(ages.max())
    selected = container.slider(
        "Age range",
        min_value=round(minimum, 1),
        max_value=round(maximum, 1),
        value=(round(minimum, 1), round(maximum, 1)),
        step=0.1,
        key="dynasty_rankings_age_range",
    )
    st.session_state["dynasty_rankings_age_filter"] = selected


def _apply_age_range_if_available(frame: pd.DataFrame) -> pd.DataFrame:
    selected = st.session_state.get("dynasty_rankings_age_filter")
    if not selected or "age" not in frame.columns:
        return frame
    ages = pd.to_numeric(frame["age"], errors="coerce")
    return frame.loc[ages.between(float(selected[0]), float(selected[1]), inclusive="both")].copy()


def _filter_asset_type(frame: pd.DataFrame, token: str) -> pd.DataFrame:
    if "asset_type_display" not in frame.columns:
        return frame.copy()
    return frame.loc[
        frame["asset_type_display"].astype(str).str.contains(token, case=False, na=False)
    ].copy()


def _column_values(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame.columns:
        return []
    return sorted(value for value in frame[column].astype(str).unique().tolist() if value)


def _default_sort_label(view_mode: str) -> str:
    if view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        return "Final Board Rank"
    return "Dynasty Rank"


def _sort_options_for_view(view_mode: str) -> list[str]:
    options = ["Dynasty Rank", "Final Board Rank", "Position Rank", "Age", "Player"]
    if view_mode == FULL_DYNASTY_VIEW:
        return ["Dynasty Rank", "Position Rank", "Age", "Player", "Final Board Rank"]
    if view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        return ["Final Board Rank", "Player", "Position Rank", "Age", "Dynasty Rank"]
    return options


def _sort_player_board(
    frame: pd.DataFrame,
    sort_by: str,
    *,
    ascending: bool,
    view_mode: str,
) -> pd.DataFrame:
    filtered = _apply_age_range_if_available(frame)
    column = SORT_COLUMNS.get(sort_by, "nwr_rank")
    if column not in filtered.columns:
        return sort_unified_player_board_for_view(filtered, view_mode)
    sorted_frame = filtered.copy()
    if column in {"nwr_rank", "final_board_rank", "position_rank", "age"}:
        sorted_frame["_ui_sort"] = pd.to_numeric(sorted_frame[column], errors="coerce")
        sorted_frame = sorted_frame.sort_values(
            by=["_ui_sort", "player_name"],
            ascending=[ascending, True],
            na_position="last",
            kind="stable",
        ).drop(columns=["_ui_sort"])
    else:
        sorted_frame = sorted_frame.sort_values(
            by=[column],
            ascending=[ascending],
            na_position="last",
            kind="stable",
        )
    return sorted_frame.reset_index(drop=True)


def _render_source_diagnostics(
    dynasty: DynastyRankingsBundle,
    frozen_board: FrozenBoardBundle,
    unified: pd.DataFrame,
) -> None:
    with st.expander("Source / diagnostics", expanded=False):
        status = "GREEN" if dynasty.loaded else "YELLOW-HOLD"
        st.write(
            {
                "dynasty_status": status,
                "dynasty_rows": dynasty.row_count,
                "dynasty_source": str(dynasty.source_path or "missing"),
                "dynasty_hash": dynasty.source_hash or "missing",
                "frozen_board_rows": frozen_board.row_count,
                "frozen_board_source": str(frozen_board.source_path or "missing"),
                "draft_board_only_rows": _source_count(unified, "Frozen Draft Board only"),
                "outcome_support": frozen_board_outcome_support_counts(frozen_board.frame),
                "age_supported_rows": _supported_age_count(unified),
            }
        )
        for warning in dynasty.warnings + frozen_board.warnings:
            st.warning(warning)
        for error in dynasty.errors + frozen_board.errors:
            st.error(error)


bundle = load_frozen_board()
dynasty_bundle = load_dynasty_rankings()
unified_board = build_unified_player_board(dynasty_bundle.frame, bundle.frame)
outcome_counts = outcome_display_coverage_counts(unified_board)
frozen_outcome_counts = frozen_board_outcome_support_counts(bundle.frame)

page_header(
    "Dynasty Rankings",
    eyebrow="Draft-Day App V1",
    description=(
        "Full dynasty rankings first, with draft-board and Outcome context kept display-only."
    ),
    status_items=(
        (
            f"Full dynasty rows: {dynasty_bundle.row_count}",
            "safe" if dynasty_bundle.loaded else "review",
        ),
        (f"Frozen board rows: {bundle.row_count}", "safe" if bundle.loaded else "blocked"),
        (
            "Outcome support: "
            f"{frozen_outcome_counts['supported']}/{frozen_outcome_counts['rows']}",
            "review",
        ),
    ),
)

if not bundle.loaded:
    st.error("Frozen Final Draft Board V1 is unavailable; rankings context is blocked.")
    st.stop()
if not dynasty_bundle.loaded:
    st.warning(
        "Full Dynasty Rankings cannot be fabricated from sample data. Frozen-board rows remain "
        "visible as draft-board-only context until the approved dynasty source is available."
    )

view_mode = st.radio(
    "View",
    VIEW_MODES,
    horizontal=True,
    key="dynasty_rankings_view_mode",
)
filtered_board, sort_by = _apply_player_filters(unified_board, view_mode)

st.caption(
    f"Rows shown: {int(filtered_board.shape[0])} | View: {view_mode} | Sort: {sort_by} | "
    "Outcome columns are display-only; missing values show Not enough information."
)
st.dataframe(
    display_unified_player_board_frame(filtered_board, view_mode=view_mode),
    use_container_width=True,
    hide_index=True,
    key="dynasty_unified_player_board_table",
)
st.caption(
    "This table does not create, replace, or override source ranks, model scores, or "
    "Outcome probabilities."
)
_render_source_diagnostics(dynasty_bundle, bundle, unified_board)
