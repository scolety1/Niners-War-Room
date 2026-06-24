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
    APPROVED_OUTCOME_DISPLAY_FIELDS,
    FULL_DYNASTY_VIEW,
    OUTCOME_DISPLAY_MODE_POSITION_APPLICABLE,
    OUTCOME_DISPLAY_MODES,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    ROOKIES_DRAFT_BOARD_VIEW,
    UNIFIED_REVIEW_VIEW,
    DynastyRankingsBundle,
    FrozenBoardBundle,
    build_unified_player_board,
    display_unified_player_board_frame,
    enrich_unified_player_board_with_market_baseline,
    frozen_board_outcome_support_counts,
    load_dynasty_rankings,
    load_frozen_board,
    market_baseline_age_coverage,
    market_baseline_freshness_status,
    market_baseline_join_coverage,
    outcome_columns_for_display,
    outcome_display_coverage_counts,
    sort_unified_player_board_for_view,
)

VIEW_MODES = (FULL_DYNASTY_VIEW, ROOKIES_DRAFT_BOARD_VIEW, UNIFIED_REVIEW_VIEW)
SORT_COLUMNS = {
    "Dynasty Rank": "nwr_rank",
    "Final Board Rank": "final_board_rank",
    "Position Rank": "nwr_position_rank",
    "Age": "age",
    "Player": "player_name",
    "Candidate Rank (Review-Only)": "cross_asset_candidate_rank",
}
BASE_POSITION_FILTERS = ("QB", "RB", "WR", "TE")
MARKET_SANITY_FILTERS = (
    "All",
    "NWR much higher",
    "NWR much lower",
    "Aligned",
    "No market match",
)
MARKET_MATCH_FILTERS = ("All", "Has market match", "No market match")


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


def _apply_player_filters(
    frame: pd.DataFrame,
    view_mode: str,
) -> tuple[pd.DataFrame, str, str, bool]:
    filtered = _view_base_frame(frame, view_mode)
    filter_row_one = st.columns([1.4, 1.2, 1.2, 1.0])
    search = filter_row_one[0].text_input(
        "Search player",
        key="dynasty_rankings_search",
        placeholder="Type a player, team, or position",
    )
    position_values = _position_filter_values(filtered)
    default_positions = position_values
    if not default_positions:
        default_positions = position_values
    selected_positions = filter_row_one[1].multiselect(
        "Position",
        position_values,
        default=default_positions,
        key="dynasty_rankings_positions",
    )
    source_filter = filter_row_one[2].selectbox(
        "Player type",
        _source_filter_options_for_view(view_mode),
        key=f"dynasty_rankings_source_filter_{view_mode}",
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
    filter_row_three = st.columns([1.2, 1.2, 1.4])
    tier_values = ["All", *_column_values(filtered, "candidate_value_band")]
    selected_tier = filter_row_three[0].selectbox(
        "Tier / band",
        tier_values,
        key="dynasty_rankings_candidate_band",
    )
    confidence_values = ["All", *_column_values(filtered, "confidence_band")]
    selected_confidence = filter_row_three[1].selectbox(
        "Confidence",
        confidence_values,
        key="dynasty_rankings_confidence",
    )
    review_filter = filter_row_three[2].selectbox(
        "Manual review",
        ["All", "Needs manual review", "No manual-review flag"],
        key="dynasty_rankings_manual_review",
    )
    outcome_mode = st.selectbox(
        "Outcome columns",
        OUTCOME_DISPLAY_MODES,
        index=OUTCOME_DISPLAY_MODES.index(OUTCOME_DISPLAY_MODE_POSITION_APPLICABLE),
        key="dynasty_rankings_outcome_columns",
        help=(
            "Outcome columns are display-only. Position-applicable mode hides other-position "
            "heads; all-outcome mode shows wrong-position heads as N/A."
        ),
    )
    market_row = st.columns([1.2, 1.2, 1.2])
    show_market_baseline = market_row[0].toggle(
        "Show Market Baseline columns",
        value=False,
        key="dynasty_rankings_show_market_baseline",
        help=(
            "Adds DynastyProcess market sanity columns as display-only context. "
            "They do not change Dynasty Rank, Candidate Rank, or default sort."
        ),
    )
    market_sanity_filter = market_row[1].selectbox(
        "Market sanity",
        MARKET_SANITY_FILTERS,
        key="dynasty_rankings_market_sanity_filter",
    )
    market_match_filter = market_row[2].selectbox(
        "Market match",
        MARKET_MATCH_FILTERS,
        key="dynasty_rankings_market_match_filter",
    )

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
    elif source_filter == "Frozen Baseline only" and "source_coverage" in filtered.columns:
        filtered = filtered.loc[
            filtered["source_coverage"].astype(str).eq("Frozen Baseline only")
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
    if selected_tier != "All" and "candidate_value_band" in filtered.columns:
        filtered = filtered.loc[
            filtered["candidate_value_band"].astype(str) == selected_tier
        ].copy()
    if selected_confidence != "All" and "confidence_band" in filtered.columns:
        filtered = filtered.loc[
            filtered["confidence_band"].astype(str) == selected_confidence
        ].copy()
    if review_filter != "All" and "manual_review_flag" in filtered.columns:
        review_mask = filtered["manual_review_flag"].astype(str).str.lower().isin(
            {"yes", "true", "1", "human_decision_only"}
        )
        if review_filter == "Needs manual review":
            filtered = filtered.loc[review_mask].copy()
        else:
            filtered = filtered.loc[~review_mask].copy()
    filtered = _apply_market_filters(filtered, market_sanity_filter, market_match_filter)

    filtered = _sort_player_board(filtered, sort_by, ascending=ascending, view_mode=view_mode)
    return filtered, sort_by, outcome_mode, show_market_baseline


def _apply_market_filters(
    frame: pd.DataFrame,
    market_sanity_filter: str,
    market_match_filter: str,
) -> pd.DataFrame:
    filtered = frame.copy()
    if market_sanity_filter != "All" and "market_sanity_label" in filtered.columns:
        filtered = filtered.loc[
            filtered["market_sanity_label"].astype(str).eq(market_sanity_filter)
        ].copy()
    if market_match_filter != "All" and "market_sanity_label" in filtered.columns:
        has_match = ~filtered["market_sanity_label"].astype(str).eq("No market match")
        if market_match_filter == "Has market match":
            filtered = filtered.loc[has_match].copy()
        else:
            filtered = filtered.loc[~has_match].copy()
    return filtered


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


def _position_filter_values(frame: pd.DataFrame) -> list[str]:
    present = set(_column_values(frame, "position"))
    return [position for position in BASE_POSITION_FILTERS if position in present]


def _source_filter_options_for_view(view_mode: str) -> list[str]:
    options = ["All", "Rookies / prospects", "Veterans", "Full Dynasty source"]
    if view_mode != FULL_DYNASTY_VIEW:
        options.append("Frozen Baseline only")
    return options


def _outcome_head_caption(frame: pd.DataFrame, outcome_mode: str) -> str:
    targets = outcome_columns_for_display(
        outcome_mode=outcome_mode,
        selected_positions=frame.get("position", pd.Series(dtype=str)).tolist(),
    )
    labels_by_target = {
        target: f"{label} (Display-Only)"
        for _source, target, label in APPROVED_OUTCOME_DISPLAY_FIELDS
    }
    labels = [labels_by_target[target] for target in targets if target in labels_by_target]
    return ", ".join(labels) if labels else "Hidden"


def _default_sort_label(view_mode: str) -> str:
    if view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        return "Final Board Rank"
    return "Dynasty Rank"


def _sort_options_for_view(view_mode: str) -> list[str]:
    if view_mode == FULL_DYNASTY_VIEW:
        return ["Dynasty Rank", "Position Rank", "Age", "Player"]
    if view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        return ["Final Board Rank", "Player", "Position Rank", "Age", "Dynasty Rank"]
    return [
        "Dynasty Rank",
        "Final Board Rank",
        "Position Rank",
        "Age",
        "Player",
        "Candidate Rank (Review-Only)",
    ]


def _sort_player_board(
    frame: pd.DataFrame,
    sort_by: str,
    *,
    ascending: bool,
    view_mode: str,
) -> pd.DataFrame:
    filtered = _apply_age_range_if_available(frame)
    column = _sort_column_for_view(sort_by, view_mode)
    if column not in filtered.columns:
        return sort_unified_player_board_for_view(filtered, view_mode)
    sorted_frame = filtered.copy()
    if column in {
        "nwr_rank",
        "final_board_rank",
        "position_rank",
        "nwr_position_rank",
        "cross_asset_candidate_rank",
        "age",
    }:
        sorted_frame["_ui_sort"] = pd.to_numeric(sorted_frame[column], errors="coerce")
        if column == "nwr_position_rank":
            sorted_frame["_ui_sort"] = pd.to_numeric(
                sorted_frame[column].astype(str).str.extract(r"(\d+)", expand=False),
                errors="coerce",
            )
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


def _sort_column_for_view(sort_by: str, view_mode: str) -> str:
    if sort_by == "Position Rank" and view_mode != FULL_DYNASTY_VIEW:
        return "position_rank"
    return SORT_COLUMNS.get(sort_by, "nwr_rank")


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
                "frozen_baseline_rows": frozen_board.row_count,
                "frozen_baseline_source": str(frozen_board.source_path or "missing"),
                "frozen_baseline_only_rows": _source_count(unified, "Frozen Baseline only"),
                "outcome_support": frozen_board_outcome_support_counts(frozen_board.frame),
                "age_supported_rows": _supported_age_count(unified),
            }
        )
        for warning in dynasty.warnings + frozen_board.warnings:
            st.warning(warning)
        for error in dynasty.errors + frozen_board.errors:
            st.error(error)


def _render_market_baseline_status(unified: pd.DataFrame) -> None:
    freshness = market_baseline_freshness_status()
    age = market_baseline_age_coverage(unified)
    join = market_baseline_join_coverage(unified)
    scrape_date = freshness.get("upstream_scrape_date") or "Not enough information"
    freshness_status = freshness.get("freshness_status") or "Not enough information"
    st.caption(
        "Market Baseline / Display-Only: "
        f"{freshness_status} | Scrape date: {scrape_date} | "
        "hidden by default; not used for rank, model value, Candidate Rank, or hidden sort."
    )
    with st.expander("Market Baseline / Display-Only diagnostics", expanded=False):
        st.write(
            {
                "source_label": "DynastyProcess public market baseline",
                "freshness_status": freshness_status,
                "scrape_date": scrape_date,
                "join_rows": join["rows"],
                "market_matches": join["matched"],
                "no_market_match": join["unmatched"],
                "age_supported_before_market_fallback": age["before"],
                "age_supported_after_market_fallback": age["after"],
                "market_age_fallback_rows": age["market_fallback"],
                "display_only_warning": (
                    "DynastyProcess market baseline is display-only market sanity context. "
                    "It does not replace NWR ranks or source truth."
                ),
            }
        )
        stale_warning = freshness.get("market_baseline_stale_warning")
        if stale_warning:
            st.warning(stale_warning)


bundle = load_frozen_board()
dynasty_bundle = load_dynasty_rankings()
raw_unified_board = build_unified_player_board(dynasty_bundle.frame, bundle.frame)
unified_board = enrich_unified_player_board_with_market_baseline(raw_unified_board)
outcome_counts = outcome_display_coverage_counts(unified_board)
frozen_outcome_counts = frozen_board_outcome_support_counts(bundle.frame)

page_header(
    "Dynasty Rankings",
    eyebrow="Draft-Day App V1",
    description=(
        "Full dynasty rankings first, with frozen-baseline and Outcome context kept display-only."
    ),
    status_items=(
        (
            f"Full dynasty rows: {dynasty_bundle.row_count}",
            "safe" if dynasty_bundle.loaded else "review",
        ),
        (
            f"Veterans: {dynasty_bundle.veteran_count} | rookies/prospects: "
            f"{dynasty_bundle.rookie_count}",
            "safe" if dynasty_bundle.loaded else "review",
        ),
        (f"Frozen baseline rows: {bundle.row_count}", "safe" if bundle.loaded else "blocked"),
        (
            "Outcome support: "
            f"{frozen_outcome_counts['supported']}/{frozen_outcome_counts['rows']}",
            "review",
        ),
    ),
)
st.markdown(
    '<a href="/drafting-mode" target="_self">Back to Drafting Mode</a>',
    unsafe_allow_html=True,
)
st.caption(
    "Deep tool: full dynasty source board. Market and Outcome context are display-only and "
    "never replace Dynasty Rank, Final Board Rank, tiers, or model values."
)

if not bundle.loaded:
    st.error("Frozen Final Draft Board V1 baseline is unavailable; baseline context is blocked.")
    st.stop()
if not dynasty_bundle.loaded:
    st.warning(
        "Full Dynasty Rankings cannot be fabricated from sample data. Frozen-baseline rows remain "
        "visible as frozen-baseline-only context until the approved dynasty source is available."
    )

_render_market_baseline_status(raw_unified_board)
view_mode = st.radio(
    "View",
    VIEW_MODES,
    horizontal=True,
    key="dynasty_rankings_view_mode",
)
filtered_board, sort_by, outcome_mode, show_market_baseline = _apply_player_filters(
    unified_board,
    view_mode,
)

st.caption(
    f"Rows shown: {int(filtered_board.shape[0])} | View: {view_mode} | Sort: {sort_by} | "
    f"Outcome columns: {outcome_mode}. Outcome is display-only and does not drive sort."
)
st.caption(
    "Candidate Rank / Candidate Value, when present, are review-only cross-asset context "
    "and do not replace Dynasty Rank or Final Board Rank."
)
st.caption(f"Visible Outcome heads: {_outcome_head_caption(filtered_board, outcome_mode)}")
if show_market_baseline:
    st.caption(
        "Market Baseline columns are display-only DynastyProcess context and do not drive "
        "Dynasty Rank, Candidate Rank, Final Board Rank, or default sort."
    )
st.dataframe(
    display_unified_player_board_frame(
        filtered_board,
        view_mode=view_mode,
        outcome_mode=outcome_mode,
        selected_positions=filtered_board.get("position", pd.Series(dtype=str)).tolist(),
        show_market_baseline=show_market_baseline,
    ),
    use_container_width=True,
    hide_index=True,
    key="dynasty_unified_player_board_table",
)
st.caption(
    "This table does not create, replace, or override source ranks, model scores, or "
    "Outcome probabilities."
)
_render_source_diagnostics(dynasty_bundle, bundle, unified_board)
