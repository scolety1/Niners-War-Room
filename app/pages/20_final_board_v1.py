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
    APPROVED_OUTCOME_V2_DISPLAY_FIELDS,
    BLOCKED_OUTCOME_V2_FIELDS,
    FULL_DYNASTY_VIEW,
    OUTCOME_DISPLAY_MODE_HIDE,
    OUTCOME_DISPLAY_MODE_POSITION_APPLICABLE,
    OUTCOME_DISPLAY_MODES,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    OUTCOME_V2_CURRENT_PLAYER_DISPLAY_PATH,
    OUTCOME_V2_INJURY_CONTEXT_DISPLAY_FIELDS,
    RANKINGS_IDENTITY_COLUMN_CONFIG,
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
    load_outcome_v2_current_player_display,
    market_baseline_age_coverage,
    market_baseline_freshness_status,
    market_baseline_join_coverage,
    outcome_columns_for_display,
    outcome_display_coverage_counts,
    outcome_v2_display_coverage_counts,
    sort_unified_player_board_for_view,
)

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
VIEW_PRESET_CLEAN_BOARD = "Clean Board"
VIEW_PRESET_MARKET_ANALYZER = "Market Analyzer"
VIEW_PRESET_OUTCOME_LENS = "Outcome Lens"
VIEW_PRESET_DATA_REVIEW = "Data Review"
VIEW_PRESET_COMPACT_DRAFT = "Compact Draft View"
VIEW_PRESETS = (
    VIEW_PRESET_CLEAN_BOARD,
    VIEW_PRESET_MARKET_ANALYZER,
    VIEW_PRESET_OUTCOME_LENS,
    VIEW_PRESET_DATA_REVIEW,
    VIEW_PRESET_COMPACT_DRAFT,
)
VIEW_PRESET_HELP = {
    VIEW_PRESET_CLEAN_BOARD: (
        "Default full dynasty board. Market basics are visible as display-only context; "
        "outcome heads stay out of the first scan."
    ),
    VIEW_PRESET_MARKET_ANALYZER: (
        "Full dynasty board with DynastyProcess market sanity columns visible. "
        "Display-only; Dynasty Rank remains the default sort."
    ),
    VIEW_PRESET_OUTCOME_LENS: (
        "Shows only approved outcome heads that exist in committed display artifacts. "
        "Missing horizons are noted, not invented."
    ),
    VIEW_PRESET_DATA_REVIEW: (
        "Human-review lens for trust, confidence, caveats, and review flags."
    ),
    VIEW_PRESET_COMPACT_DRAFT: (
        "Fast-scan rookie/draft-board view with review context pushed back."
    ),
}


def _source_count(frame: pd.DataFrame, source_coverage: str) -> int:
    if "source_coverage" not in frame.columns:
        return 0
    return int(frame["source_coverage"].astype(str).eq(source_coverage).sum())


def _rankings_identity_column_config() -> dict[str, object]:
    return {
        column: st.column_config.TextColumn(
            str(config["label"]),
            width=int(config["width"]),
            pinned=bool(config["pinned"]),
            help=str(config["help"]),
        )
        for column, config in RANKINGS_IDENTITY_COLUMN_CONFIG.items()
    }


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


def _view_mode_for_preset(preset: str) -> str:
    if preset == VIEW_PRESET_DATA_REVIEW:
        return UNIFIED_REVIEW_VIEW
    if preset == VIEW_PRESET_COMPACT_DRAFT:
        return ROOKIES_DRAFT_BOARD_VIEW
    return FULL_DYNASTY_VIEW


def _outcome_mode_for_preset(preset: str) -> str:
    if preset in {VIEW_PRESET_OUTCOME_LENS, VIEW_PRESET_DATA_REVIEW}:
        return OUTCOME_DISPLAY_MODE_POSITION_APPLICABLE
    return OUTCOME_DISPLAY_MODE_HIDE


def _show_market_for_preset(preset: str) -> bool:
    return preset in {
        VIEW_PRESET_CLEAN_BOARD,
        VIEW_PRESET_MARKET_ANALYZER,
        VIEW_PRESET_OUTCOME_LENS,
        VIEW_PRESET_DATA_REVIEW,
    }


def _apply_player_filters(
    frame: pd.DataFrame,
    preset: str,
) -> tuple[pd.DataFrame, str, str, bool, str]:
    view_mode = _view_mode_for_preset(preset)
    filtered = _view_base_frame(frame, view_mode)
    st.caption(VIEW_PRESET_HELP[preset])
    filter_row_one = st.columns([1.5, 1.5, 1.2, 1.0])
    selected_preset = filter_row_one[0].selectbox(
        "View preset",
        VIEW_PRESETS,
        index=VIEW_PRESETS.index(preset),
        key="dynasty_rankings_view_preset_inline",
        help=(
            "Presets change visible columns and review emphasis only. They do not change "
            "rank values, model values, or hidden sort behavior."
        ),
    )
    if selected_preset != preset:
        st.session_state["dynasty_rankings_view_preset"] = selected_preset
        st.rerun()
    search = filter_row_one[1].text_input(
        "Search player",
        key="dynasty_rankings_search",
        placeholder="Type a player, team, or position",
    )
    position_values = _position_filter_values(filtered)
    default_positions = position_values
    if not default_positions:
        default_positions = position_values
    selected_positions = filter_row_one[2].multiselect(
        "Position",
        position_values,
        default=default_positions,
        key="dynasty_rankings_positions",
    )
    team_values = ["All", *_column_values(filtered, "nfl_team")]
    selected_team = filter_row_one[3].selectbox(
        "NFL Team",
        team_values,
        key="dynasty_rankings_team",
    )

    filter_row_two = st.columns([1.2, 1.0, 1.4, 1.0])
    source_filter = filter_row_two[0].selectbox(
        "Player type",
        _source_filter_options_for_view(view_mode),
        key=f"dynasty_rankings_source_filter_{view_mode}",
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
    show_market_baseline = _show_market_for_preset(preset)
    outcome_mode = _outcome_mode_for_preset(preset)
    outcome_filter = "All"
    selected_tier = "All"
    selected_confidence = "All"
    review_filter = "All"
    market_sanity_filter = "All"
    market_match_filter = "All"
    with st.expander("Advanced filters", expanded=False):
        st.caption(
            "Review filters live here so the main board stays readable. These filters do not "
            "change source values, ranks, model logic, or hidden sort behavior."
        )
        advanced_row_one = st.columns([1.2, 1.2, 1.2])
        outcome_filter = advanced_row_one[0].selectbox(
            "Outcome availability",
            ["All", "Has Outcome support", OUTCOME_NOT_ENOUGH_INFORMATION],
            key="dynasty_rankings_outcome_filter",
        )
        tier_values = ["All", *_column_values(filtered, "candidate_value_band")]
        selected_tier = advanced_row_one[1].selectbox(
            "Value band / review band",
            tier_values,
            key="dynasty_rankings_candidate_band",
        )
        confidence_values = ["All", *_column_values(filtered, "confidence_band")]
        selected_confidence = advanced_row_one[2].selectbox(
            "Confidence",
            confidence_values,
            key="dynasty_rankings_confidence",
        )
        advanced_row_two = st.columns([1.2, 1.2, 1.2])
        review_filter = advanced_row_two[0].selectbox(
            "Review needed",
            ["All", "Needs review", "No review flag"],
            key="dynasty_rankings_manual_review",
        )
        outcome_mode = advanced_row_two[1].selectbox(
            "Outcome columns",
            OUTCOME_DISPLAY_MODES,
            index=OUTCOME_DISPLAY_MODES.index(outcome_mode),
            key="dynasty_rankings_outcome_columns",
            help=(
                "Outcome columns are display-only. Position-applicable mode hides "
                "other-position heads; all-outcome mode shows wrong-position heads as N/A."
            ),
        )
        market_sanity_filter = advanced_row_two[2].selectbox(
            "Market sanity",
            MARKET_SANITY_FILTERS,
            key="dynasty_rankings_market_sanity_filter",
        )
        market_match_filter = st.selectbox(
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
        if review_filter == "Needs review":
            filtered = filtered.loc[review_mask].copy()
        else:
            filtered = filtered.loc[~review_mask].copy()
    filtered = _apply_market_filters(filtered, market_sanity_filter, market_match_filter)

    filtered = _sort_player_board(filtered, sort_by, ascending=ascending, view_mode=view_mode)
    return filtered, sort_by, outcome_mode, show_market_baseline, view_mode


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


def _outcome_head_caption(
    frame: pd.DataFrame,
    outcome_mode: str,
    *,
    include_injury_context: bool = False,
) -> str:
    targets = outcome_columns_for_display(
        outcome_mode=outcome_mode,
        selected_positions=frame.get("position", pd.Series(dtype=str)).tolist(),
        include_injury_context=include_injury_context,
    )
    labels_by_target = {
        target: f"{label} (Display-Only)"
        for _source, target, label in APPROVED_OUTCOME_DISPLAY_FIELDS
    }
    labels_by_target.update(
        {
            target: f"{label} (Outcome V2 / Display-Only)"
            for _source, target, label, _position in APPROVED_OUTCOME_V2_DISPLAY_FIELDS
        }
    )
    labels_by_target.update(
        {
            target: label
            for _source, target, label in OUTCOME_V2_INJURY_CONTEXT_DISPLAY_FIELDS
        }
    )
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
        "visible in the main lenses; not used for rank, model value, Candidate Rank, "
        "or hidden sort."
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


def _render_outcome_lens_status(unified: pd.DataFrame) -> None:
    counts = outcome_v2_display_coverage_counts(unified)
    artifact = load_outcome_v2_current_player_display()
    st.info(
        "Outcome V2 is display-only. It does not drive Dynasty Rank, model input, "
        "hidden sort, trade value, or pick value. This Year = 2026 NFL season. "
        "Missing data is Not enough information, not low probability."
    )
    st.caption(
        "Scoring caveat: partial exact first-down scoring; sack_fumbles_lost missing. "
        "Availability caveat: games field missing; no row is Not enough information, "
        "not clean health."
    )
    st.info(
        "Injury context is review-only. No medical recovery projection is made. "
        "Missing injury context is not clean health."
    )
    st.caption(
        "Missing / limited recent sample is not a low-probability signal. Injury context "
        "does not change Dynasty Rank, hidden sort, model input, trade value, or pick value."
    )
    st.caption(
        "Outcome V2 coverage: "
        f"{counts['available']}/{counts['rows']} rows with validated display context; "
        f"{counts['not_enough_information']} rows remain Not enough information; "
        f"{counts['rookie_out_of_scope']} rookies/prospects out of scope; "
        f"{counts['missing_feature']} veterans missing 2025 feature rows."
    )
    st.caption(
        "Injury Context Flags V0 coverage: "
        f"{counts['injury_context_available']} rows with review-only injury context; "
        f"{counts['limited_recent_sample']} rows with limited recent sample caveats."
    )
    st.caption(
        "Blocked V2 fields: "
        f"{', '.join(BLOCKED_OUTCOME_V2_FIELDS)} = Not enough information; "
        "weak calibration, no probability shown."
    )
    st.caption(f"Outcome V2 artifact: {OUTCOME_V2_CURRENT_PLAYER_DISPLAY_PATH}")
    with st.expander("Outcome V1 / Legacy and blocked V2 fields", expanded=False):
        st.write(
            {
                "Outcome V1 / Legacy": (
                    "QB T12, RB T12, RB T24, WR T12, WR T24, WR T36, TE T12 "
                    "remain available as legacy display-only context."
                ),
                "Outcome V2 blocked fields": (
                    ", ".join(BLOCKED_OUTCOME_V2_FIELDS)
                    + " = Not enough information; weak calibration."
                ),
                "Outcome V2 artifact status": "GREEN" if artifact.loaded else "YELLOW-HOLD",
                "Outcome V2 artifact rows": artifact.row_count,
                "Outcome V2 artifact hash": artifact.source_hash or OUTCOME_NOT_ENOUGH_INFORMATION,
            }
        )
        for error in artifact.errors:
            st.error(error)


def _render_tier_board_cheat_sheet(frame: pd.DataFrame, view_mode: str) -> None:
    with st.expander("Tier Board / Cheat Sheet", expanded=False):
        st.caption(
            "Draft-day scan view for the currently filtered rankings. This is a view of "
            "existing ranks/tiers only; it does not change sort rules, model values, "
            "or source truth."
        )
        tier_column = _first_existing_column(
            frame,
            ("candidate_value_band", "dynasty_asset_tier", "final_tier"),
        )
        if tier_column is None or frame.empty:
            st.info(OUTCOME_NOT_ENOUGH_INFORMATION)
            return
        player_column = _first_existing_column(frame, ("player_name", "player"))
        position_column = _first_existing_column(frame, ("position",))
        rank_column = _first_existing_column(
            frame,
            ("nwr_rank", "dynasty_asset_rank", "final_board_rank"),
        )
        working = frame.copy()
        working["_tier_display"] = (
            working[tier_column]
            .fillna(OUTCOME_NOT_ENOUGH_INFORMATION)
            .astype(str)
            .replace("", OUTCOME_NOT_ENOUGH_INFORMATION)
        )
        if rank_column is not None:
            working["_rank_sort"] = pd.to_numeric(working[rank_column], errors="coerce")
        else:
            working["_rank_sort"] = pd.Series(range(len(working)), index=working.index)

        rows: list[dict[str, str]] = []
        for tier, tier_frame in working.sort_values("_rank_sort").groupby(
            "_tier_display",
            sort=False,
        ):
            names = _top_names_for_tier(tier_frame, player_column, position_column)
            rows.append(
                {
                    "View": view_mode,
                    "Tier / Band": str(tier),
                    "Rows": str(int(tier_frame.shape[0])),
                    "Top visible names": names or OUTCOME_NOT_ENOUGH_INFORMATION,
                    "Guardrail": "Existing rank/tier view only; no hidden market sort.",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(
            "Cheat Sheets remain available by direct URL, but the main draft-day tier scan now "
            "lives inside Dynasty Rankings and Live Draft."
        )


def _first_existing_column(frame: pd.DataFrame, columns: tuple[str, ...]) -> str | None:
    return next((column for column in columns if column in frame.columns), None)


def _top_names_for_tier(
    frame: pd.DataFrame,
    player_column: str | None,
    position_column: str | None,
) -> str:
    if player_column is None:
        return ""
    names: list[str] = []
    for _index, row in frame.head(8).iterrows():
        name = str(row.get(player_column) or "").strip()
        position = str(row.get(position_column) or "").strip() if position_column else ""
        if not name:
            continue
        names.append(f"{name} ({position})" if position else name)
    return "; ".join(names)


bundle = load_frozen_board()
dynasty_bundle = load_dynasty_rankings()
raw_unified_board = build_unified_player_board(dynasty_bundle.frame, bundle.frame)
unified_board = enrich_unified_player_board_with_market_baseline(raw_unified_board)
outcome_counts = outcome_display_coverage_counts(unified_board)
outcome_v2_counts = outcome_v2_display_coverage_counts(unified_board)
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
        (
            "Outcome V2 display rows: "
            f"{outcome_v2_counts['available']}/{outcome_v2_counts['rows']}",
            "review",
        ),
    ),
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
preset = st.session_state.get("dynasty_rankings_view_preset", VIEW_PRESET_CLEAN_BOARD)
if preset not in VIEW_PRESETS:
    preset = VIEW_PRESET_CLEAN_BOARD
filtered_board, sort_by, outcome_mode, show_market_baseline, view_mode = _apply_player_filters(
    unified_board,
    preset,
)

st.caption(
    f"Rows shown: {int(filtered_board.shape[0])} | Preset: {preset} | View: {view_mode} | "
    f"Sort: {sort_by} | Outcome columns: {outcome_mode}. Outcome is display-only and does "
    "not drive sort."
)
st.caption(
    "Candidate Rank / Candidate Value, when present, are review-only cross-asset context "
    "and do not replace Dynasty Rank or Final Board Rank."
)
st.caption(
    "Visible Outcome heads: "
    + _outcome_head_caption(
        filtered_board,
        outcome_mode,
        include_injury_context=preset == VIEW_PRESET_OUTCOME_LENS,
    )
)
st.caption(
    "Market Baseline columns are display-only DynastyProcess context, visible for the main "
    "lenses, and do not drive Dynasty Rank, Candidate Rank, Final Board Rank, default sort, "
    "trade value, or model input."
)
if show_market_baseline:
    st.caption(
        "Visible market basics: DP 1QB Value, DP 1QB Market Rank, NWR vs Market Gap, "
        "and Market Sanity Flag."
    )
if preset == VIEW_PRESET_OUTCOME_LENS:
    _render_outcome_lens_status(unified_board)
_render_tier_board_cheat_sheet(filtered_board, view_mode)
st.dataframe(
    display_unified_player_board_frame(
        filtered_board,
        view_mode=view_mode,
        outcome_mode=outcome_mode,
        selected_positions=filtered_board.get("position", pd.Series(dtype=str)).tolist(),
        show_market_baseline=show_market_baseline,
        include_injury_context=preset == VIEW_PRESET_OUTCOME_LENS,
    ),
    use_container_width=True,
    hide_index=True,
    column_config=_rankings_identity_column_config(),
    key="dynasty_unified_player_board_table",
)
st.caption(
    "This table does not create, replace, or override source ranks, model scores, or "
    "Outcome probabilities."
)
_render_source_diagnostics(dynasty_bundle, bundle, unified_board)
