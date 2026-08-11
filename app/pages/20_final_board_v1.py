from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.decision_trust_strip import render_decision_trust_strips
from app.components.post_release_status import render_source_freshness
from app.components.ui_framework import page_header
from src.services.decision_trust_strip_service import build_rankings_dataset_trust_strip
from src.services.draft_day_app_v1_service import (
    APPROVED_OUTCOME_DISPLAY_FIELDS,
    APPROVED_OUTCOME_V2_DISPLAY_FIELDS,
    BLOCKED_OUTCOME_V2_FIELDS,
    FULL_DYNASTY_VIEW,
    OUTCOME_DISPLAY_MODE_HIDE,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    OUTCOME_V2_CURRENT_PLAYER_DISPLAY_PATH,
    OUTCOME_V2_INJURY_CONTEXT_DISPLAY_FIELDS,
    RANKINGS_TABLE_COLUMN_CONFIG,
    ROOKIES_DRAFT_BOARD_VIEW,
    UNIFIED_PLAYER_BOARD_DISPLAY_LABELS,
    UNIFIED_REVIEW_VIEW,
    DynastyRankingsBundle,
    FrozenBoardBundle,
    OutcomeDisplayBundle,
    build_unified_player_board,
    display_unified_player_board_frame,
    enrich_unified_player_board_with_market_baseline,
    frozen_board_outcome_support_counts,
    integrate_nflverse_player_context_display,
    load_dynasty_rankings,
    load_frozen_board,
    load_nflverse_player_context_display,
    load_outcome_v2_current_player_display,
    market_baseline_age_coverage,
    market_baseline_freshness_status,
    market_baseline_join_coverage,
    nflverse_player_context_display_counts,
    outcome_columns_for_display,
    outcome_display_coverage_counts,
    outcome_v2_display_coverage_counts,
    sort_rankings_frame_by_column,
    sort_unified_player_board_for_view,
)
from src.services.governed_asset_registry_service import (
    finished_v1_coverage_counts,
    load_governed_asset_registry,
)
from src.services.nflverse_refresh_health_service import (
    dataset_registry_rows,
    full_safe_refresh_dataset_ids,
    safe_refresh_dataset_ids,
)
from src.services.outcome_v3_calibration_service import (
    POSITION_THRESHOLDS as OUTCOME_V3_POSITION_THRESHOLDS,
)
from src.services.outcome_v3_display_service import (
    load_outcome_v3_display,
    rankings_outcome_v3_rows,
)
from src.services.player_rank_owner_explanation_service import owner_rank_explanation
from src.services.post_release_usability_service import freshness_for_sources
from src.services.unified_research_preview_service import load_unified_research_preview

SORT_COLUMNS = {
    "Dynasty Rank": "nwr_rank",
    "NWR Dynasty Score": "nwr_dynasty_score",
    "Final Board Rank": "final_board_rank",
    "Position Rank": "nwr_position_rank",
    "Age": "age",
    "Player": "player_name",
    "Research Context Rank": "cross_asset_candidate_rank",
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
VIEW_PRESET_DYNASTY_REVIEW = "Dynasty Review"
VIEW_PRESET_MARKET_CONTEXT = "Market Context"
VIEW_PRESET_OUTCOME_CONTEXT = "Outcome Context"
VIEW_PRESET_DATA_REVIEW = "Ranking Context"
VIEW_PRESET_STATISTIC_ANALYSIS = "Why NWR Ranks Them"
VIEW_PRESET_DRAFT_RANKINGS = "Dynasty Draft Board"
VIEW_PRESETS = (
    VIEW_PRESET_DYNASTY_REVIEW,
    VIEW_PRESET_MARKET_CONTEXT,
    VIEW_PRESET_OUTCOME_CONTEXT,
    VIEW_PRESET_DATA_REVIEW,
    VIEW_PRESET_STATISTIC_ANALYSIS,
    VIEW_PRESET_DRAFT_RANKINGS,
)
VIEW_PRESET_HELP = {
    VIEW_PRESET_DYNASTY_REVIEW: (
        "Default full dynasty board. Dynasty Rank remains primary; market, Outcome, "
        "and injury-review detail columns stay hidden by default."
    ),
    VIEW_PRESET_MARKET_CONTEXT: (
        "Full dynasty board with DynastyProcess market sanity columns visible. "
        "Display-only; Dynasty Rank remains the default sort."
    ),
    VIEW_PRESET_OUTCOME_CONTEXT: (
        "Shows only approved outcome heads that exist in committed display artifacts. "
        "Missing horizons are noted, not invented."
    ),
    VIEW_PRESET_DATA_REVIEW: (
        "Human-review lens for trust, confidence, caveats, and review flags."
    ),
    VIEW_PRESET_STATISTIC_ANALYSIS: (
        "Read-only score explanation view. It exposes approved NWR Score metadata where "
        "available and does not change Dynasty Rank, tiers, or model/source approvals."
    ),
    VIEW_PRESET_DRAFT_RANKINGS: (
        "Fast-scan full dynasty board with review context pushed back. Dynasty Rank "
        "remains the default sort."
    ),
}
NFLVERSE_REFRESH_HEALTH_ROOT = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "nflverse_dataset_level_refresh_health_20260630"
)
NFLVERSE_REFRESH_HEALTH_REGISTRY = NFLVERSE_REFRESH_HEALTH_ROOT / "nflverse_dataset_registry_v1.csv"
NFLVERSE_REFRESH_HEALTH_SAFETY_REPORT = (
    NFLVERSE_REFRESH_HEALTH_ROOT / "NFLVERSE_REFRESH_HEALTH_SAFETY_REPORT_20260630.md"
)
NFLVERSE_REFRESH_HEALTH_WAIT_STATUS = "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN"


def _source_count(frame: pd.DataFrame, source_coverage: str) -> int:
    if "source_coverage" not in frame.columns:
        return 0
    return int(frame["source_coverage"].astype(str).eq(source_coverage).sum())


def _rankings_identity_column_config() -> dict[str, object]:
    configs: dict[str, object] = {}
    for column, config in RANKINGS_TABLE_COLUMN_CONFIG.items():
        common = {
            "label": str(config["label"]),
            "width": int(config["width"]),
            "help": str(config["help"]),
        }
        pinned = config.get("pinned")
        if pinned is not None:
            common["pinned"] = bool(pinned)
        if config.get("type") == "number":
            configs[column] = st.column_config.NumberColumn(
                **common,
                format=str(config.get("format", "%s")),
            )
        else:
            configs[column] = st.column_config.TextColumn(**common)
    for _source, _target, label in APPROVED_OUTCOME_DISPLAY_FIELDS:
        configs[label] = st.column_config.NumberColumn(label, format="%.0f%%")
    for _source, target, _label, _position in APPROVED_OUTCOME_V2_DISPLAY_FIELDS:
        display_label = UNIFIED_PLAYER_BOARD_DISPLAY_LABELS.get(target)
        if display_label:
            configs[str(display_label)] = st.column_config.NumberColumn(
                str(display_label), format="%.0f%%"
            )
    return configs


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
    return FULL_DYNASTY_VIEW


def _outcome_mode_for_preset(preset: str) -> str:
    return OUTCOME_DISPLAY_MODE_HIDE


def _show_market_for_preset(preset: str) -> bool:
    return preset in {
        VIEW_PRESET_MARKET_CONTEXT,
        VIEW_PRESET_DATA_REVIEW,
    }


def _show_statistic_analysis_for_preset(preset: str) -> bool:
    return False


def _reset_rankings_filters() -> None:
    dynamic_prefixes = (
        "dynasty_rankings_source_filter_",
        "dynasty_rankings_sort_by_",
        "dynasty_rankings_ascending_",
    )
    for key in list(st.session_state):
        if key.startswith(dynamic_prefixes) or key in {
            "dynasty_rankings_age_range",
            "dynasty_rankings_age_filter",
        }:
            del st.session_state[key]
    st.session_state.update(
        {
            "dynasty_rankings_view_preset": VIEW_PRESET_DYNASTY_REVIEW,
            "dynasty_rankings_view_preset_inline": VIEW_PRESET_DYNASTY_REVIEW,
            "dynasty_rankings_search": "",
            "dynasty_rankings_positions": ["QB", "RB", "WR", "TE"],
            "dynasty_rankings_team": "All",
            "dynasty_rankings_outcome_filter": "All",
            "dynasty_rankings_candidate_band": "All",
            "dynasty_rankings_confidence": "All",
            "dynasty_rankings_manual_review": "All",
            "dynasty_rankings_market_sanity_filter": "All",
            "dynasty_rankings_market_match_filter": "All",
        }
    )


def _default_ascending_for_sort(sort_by: str) -> bool:
    return sort_by != "NWR Dynasty Score"


def _sort_state_key(sort_by: str) -> str:
    return "dynasty_rankings_ascending_" + "".join(
        char.lower() if char.isalnum() else "_" for char in sort_by
    )


def _apply_player_filters(
    frame: pd.DataFrame,
    preset: str,
) -> tuple[pd.DataFrame, str, str, bool, bool, str]:
    view_mode = _view_mode_for_preset(preset)
    filtered = _view_base_frame(frame, view_mode)
    st.caption(VIEW_PRESET_HELP[preset])
    st.button(
        "Reset Filters",
        key="dynasty_rankings_reset_filters",
        on_click=_reset_rankings_filters,
    )
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
        value=_default_ascending_for_sort(sort_by),
        key=_sort_state_key(sort_by),
        help=(
            "Dynasty Rank defaults ascending. NWR Dynasty Score defaults descending. "
            "Missing numeric values sort last and never as zero."
        ),
    )
    _render_age_filter(filter_row_two[3], filtered)
    show_market_baseline = _show_market_for_preset(preset)
    show_statistic_analysis = _show_statistic_analysis_for_preset(preset)
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
        advanced_row_two[1].caption(
            "Outcome V3 is shown only in the canonical Outcome Context lens."
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
            filtered["outcome_availability_display_only"]
            .astype(str)
            .eq(OUTCOME_NOT_ENOUGH_INFORMATION)
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
        review_mask = (
            filtered["manual_review_flag"]
            .astype(str)
            .str.lower()
            .isin({"yes", "true", "1", "human_decision_only"})
        )
        if review_filter == "Needs review":
            filtered = filtered.loc[review_mask].copy()
        else:
            filtered = filtered.loc[~review_mask].copy()
    filtered = _apply_market_filters(filtered, market_sanity_filter, market_match_filter)

    filtered = _sort_player_board(filtered, sort_by, ascending=ascending, view_mode=view_mode)
    return (
        filtered,
        sort_by,
        outcome_mode,
        show_market_baseline,
        show_statistic_analysis,
        view_mode,
    )


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
    supported_ages = ages.dropna()
    if supported_ages.empty:
        return frame
    minimum = round(float(supported_ages.min()), 1)
    maximum = round(float(supported_ages.max()), 1)
    if float(selected[0]) <= minimum and float(selected[1]) >= maximum:
        return frame
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
    values = (
        frame[column]
        .fillna("")
        .map(lambda value: str(value).strip())
        .replace({"nan": "", "NaN": "", "<NA>": "", "None": ""})
        .unique()
        .tolist()
    )
    return sorted(value for value in values if value)


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
        {target: label for _source, target, label in OUTCOME_V2_INJURY_CONTEXT_DISPLAY_FIELDS}
    )
    labels = [labels_by_target[target] for target in targets if target in labels_by_target]
    return ", ".join(labels) if labels else "Hidden"


def _default_sort_label(view_mode: str) -> str:
    if view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        return "Final Board Rank"
    return "Dynasty Rank"


def _sort_options_for_view(view_mode: str) -> list[str]:
    if view_mode == FULL_DYNASTY_VIEW:
        return ["Dynasty Rank", "NWR Dynasty Score", "Position Rank", "Age", "Player"]
    if view_mode == ROOKIES_DRAFT_BOARD_VIEW:
        return [
            "Final Board Rank",
            "Player",
            "Position Rank",
            "Age",
            "Dynasty Rank",
            "NWR Dynasty Score",
        ]
    return [
        "Dynasty Rank",
        "NWR Dynasty Score",
        "Final Board Rank",
        "Position Rank",
        "Age",
        "Player",
        "Research Context Rank",
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
    return sort_rankings_frame_by_column(
        filtered,
        column,
        ascending=ascending,
        view_mode=view_mode,
    )


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


def _nflverse_refresh_health_status() -> dict[str, object]:
    try:
        registry = dataset_registry_rows()
        safe_ids = set(safe_refresh_dataset_ids())
        full_safe_ids = set(full_safe_refresh_dataset_ids())
    except Exception as exc:  # pragma: no cover - defensive app display guard
        return {
            "status": "YELLOW_REFRESH_HEALTH_SERVICE_UNAVAILABLE",
            "dataset_rows": 0,
            "blocked_datasets": ("ff_rankings",),
            "available_display_fields": (),
            "unavailable_display_fields": ("dataset-backed fields",),
            "note": f"Centralized nflverse refresh-health service could not load: {exc}",
        }
    if not registry or not NFLVERSE_REFRESH_HEALTH_REGISTRY.exists():
        return {
            "status": NFLVERSE_REFRESH_HEALTH_WAIT_STATUS,
            "dataset_rows": 0,
            "blocked_datasets": ("ff_rankings",),
            "available_display_fields": (),
            "unavailable_display_fields": (
                "roster age fallback",
                "roster status",
                "injury report status",
                "next game / bye context",
                "depth chart role context",
                "snap-share recency",
                "draft capital display",
                "identity bridge health",
            ),
            "note": (
                "Dataset-level nflverse refresh-health registry is not present in this "
                "branch. Dataset-backed fields remain unavailable rather than guessed."
            ),
        }
    blocked = [
        row["dataset_id"]
        for row in registry
        if row.get("default_mode") == "blocked" or row.get("policy_status") == "blocked_policy"
    ]
    if "ff_rankings" not in blocked:
        blocked.append("ff_rankings")
    player_context_sources = tuple(
        dataset
        for dataset in (
            "players",
            "rosters",
            "weekly_rosters",
            "schedules",
            "depth_charts",
            "injuries",
            "snap_counts",
            "draft_picks",
            "ff_playerids",
        )
        if dataset in safe_ids or dataset in full_safe_ids
    )
    return {
        "status": "GREEN_TRACKED_REFRESH_HEALTH_CONTRACT_PRESENT",
        "dataset_rows": len(registry),
        "blocked_datasets": tuple(dict.fromkeys(blocked)),
        "available_display_fields": (
            "dataset health/status panel",
            "safe refresh dataset list",
            "full safe refresh dataset list",
            "ff_rankings blocked status",
            "source-policy display warnings",
            "rebuilt NFLVerse player context display artifact",
            "safe row-level NFLVerse context where identity/status/schema gates pass",
        ),
        "unavailable_display_fields": (
            "gated NFLVerse player context rows remain Needs identity review / "
            "Not enough information",
        ),
        "note": (
            "Centralized dataset-level refresh-health contract is present and GREEN for "
            "guardrails. The rebuilt row-level NFLVerse player context display artifact "
            f"exists for {', '.join(player_context_sources)} context and remains "
            "display-only/review-only."
        ),
    }


def _nflverse_player_context_artifact_counts(
    player_context: OutcomeDisplayBundle,
) -> dict[str, int]:
    frame = player_context.frame
    if frame.empty or "identity_join_status" not in frame.columns:
        return {"rows": 0, "safe": 0, "gated": 0}
    status = frame["identity_join_status"].astype(str)
    safe = int(status.eq("SAFE_NOW_DISPLAY_ONLY").sum())
    gated = int(status.eq("NEED_IDENTITY_REVIEW").sum())
    return {"rows": int(frame.shape[0]), "safe": safe, "gated": gated}


def _render_dataset_refresh_status_panel(unified: pd.DataFrame) -> None:
    status = _nflverse_refresh_health_status()
    player_context = load_nflverse_player_context_display()
    artifact_counts = _nflverse_player_context_artifact_counts(player_context)
    counts = nflverse_player_context_display_counts(unified)
    with st.expander("Dataset Refresh / Outcome Status", expanded=False):
        st.write(
            {
                "Outcome V2": (
                    "Display-only/review-only. Missing data is Not enough information, "
                    "not low probability."
                ),
                "Rookie Outcome Gate G": (
                    "Blocked unless an explicit GREEN Gate G approval artifact exists."
                ),
                "nflverse refresh-health": status["status"],
                "dataset_rows": status["dataset_rows"],
                "NFLVerse player context artifact": (
                    "GREEN rebuilt tracked display artifact"
                    if player_context.loaded
                    else "YELLOW-HOLD"
                ),
                "NFLVerse artifact total rows": artifact_counts["rows"],
                "NFLVerse artifact safe display rows": artifact_counts["safe"],
                "NFLVerse artifact gated rows": artifact_counts["gated"],
                "NFLVerse context rows": counts["rows"],
                "NFLVerse safe context rows": counts["safe"],
                "NFLVerse identity review rows": counts["review"],
                "NFLVerse missing context rows": counts["missing"],
                "NFLVerse age fallback rows": counts["age_fallback"],
                "NFLVerse injury context rows": counts["injury_available"],
                "NFLVerse depth context rows": counts["depth_available"],
                "NFLVerse snap context rows": counts["snap_available"],
                "NFLVerse draft capital rows": counts["draft_available"],
                "blocked_datasets": ", ".join(status["blocked_datasets"])
                or OUTCOME_NOT_ENOUGH_INFORMATION,
                "available_dataset_display_fields": ", ".join(status["available_display_fields"])
                or OUTCOME_NOT_ENOUGH_INFORMATION,
                "unavailable_dataset_display_fields": ", ".join(
                    status["unavailable_display_fields"]
                )
                or OUTCOME_NOT_ENOUGH_INFORMATION,
                "missing_data_rule": "Not enough information; never 0%, false, or clean health.",
                "NFLVerse gated row rule": (
                    "Needs identity review / Not enough information; gated values stay hidden."
                ),
                "market_warning": (
                    "DynastyProcess/market context is display-only and never rank logic."
                ),
                "NFLVerse display warning": (
                    "NFLVerse is display/review-only. It never drives Dynasty Rank, model "
                    "input, source truth, hidden sort, trade value, pick value, recommendations, "
                    "injury risk, or medical projection."
                ),
                "note": status["note"],
            }
        )
        st.caption(
            "This panel reads only tracked repo artifacts. It does not read raw/cache/shared "
            "nflverse paths and does not create app-facing dataset fields."
        )
        if NFLVERSE_REFRESH_HEALTH_SAFETY_REPORT.exists():
            st.caption(f"Safety report: {NFLVERSE_REFRESH_HEALTH_SAFETY_REPORT}")
        if player_context.source_path:
            st.caption(f"Player context artifact: {player_context.source_path}")
        for error in player_context.errors:
            st.error(error)


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


def _render_outcome_v3_compact_lens(frame: pd.DataFrame) -> None:
    st.subheader("Outcome Columns V3")
    artifact = load_outcome_v3_display()
    st.info(
        "NWR_OUTCOME_COLUMNS_V3_RC1 is a display-only dynasty-horizon lens. "
        "It never changes Finished V1 rank, scores, trade/pick values, or sort."
    )
    if not artifact.loaded:
        st.warning("Outcome V3 is unavailable. Applicable values remain Not enough information.")
        for error in artifact.errors:
            st.error(error)
        return

    present_positions = set(frame.get("position", pd.Series(dtype=str)).astype(str).str.upper())
    position_options = [
        position for position in OUTCOME_V3_POSITION_THRESHOLDS if position in present_positions
    ]
    if not position_options:
        st.info("No governed QB/RB/WR/TE players are visible in the current filter.")
        return
    controls = st.columns(2)
    selected_position = controls[0].selectbox(
        "Outcome V3 position",
        position_options,
        key="rankings_outcome_v3_position",
        help="Select the governed position family shown in the compact lens.",
    )
    selected_threshold = controls[1].selectbox(
        "Outcome V3 threshold",
        OUTCOME_V3_POSITION_THRESHOLDS[selected_position],
        format_func=lambda value: f"{selected_position} T{value}",
        key="rankings_outcome_v3_threshold",
        help="T6 is a top-six finish; broader thresholds include more finish outcomes.",
    )
    rows = rankings_outcome_v3_rows(
        frame,
        artifact.frame,
        position=selected_position,
        threshold=int(selected_threshold),
    )
    horizon_labels = rows["Horizon"].drop_duplicates().astype(str).tolist()
    horizon_text = ", ".join(horizon_labels)
    if len(horizon_labels) > 1:
        horizon_text = f"{', '.join(horizon_labels[:-1])}, and {horizon_labels[-1]}"
    st.caption(
        f"Visible horizons: {horizon_text}. "
        "Wrong-position is N/A; blocked or insufficient applicable evidence is "
        "Not enough information."
    )
    columns = [
        "Finished V1 Rank",
        "Player",
        "Pos",
        "Threshold",
        "Horizon",
        "Probability",
        "Calibration status",
        "Evidence",
        "Historical sample",
        "Confidence",
        "Missing-state explanation",
    ]
    st.dataframe(
        rows.loc[:, columns],
        use_container_width=True,
        hide_index=True,
        key="rankings_outcome_v3_compact_lens",
    )
    st.caption(
        f"Release: {artifact.release_identifier} | Exact player_id joins | "
        f"Artifact rows: {artifact.row_count} | SHA-256: {artifact.source_hash}"
    )


def _render_statistic_analysis_status(frame: pd.DataFrame) -> None:
    ranked = frame.loc[
        frame.get("nwr_rank", pd.Series(index=frame.index, dtype=str))
        .astype(str)
        .str.strip()
        .astype(bool)
    ].copy()
    receipt_fields = (
        "player_name",
        "position",
        "nwr_rank",
        "nwr_dynasty_score",
        "confidence_cap",
        "confidence_status",
        "candidate_adjustment",
        "candidate_reason_codes",
        "candidate_evidence_fields_used",
        "candidate_confidence_trust_impact",
        "risk_level",
        "warning_flags",
        "data_needed",
    )
    available = [column for column in receipt_fields if column in ranked.columns]
    st.info(
        f"Choose any of the {len(ranked)} ranked Finished V1 players to answer: "
        "Why is NWR high or low on this player? Exact weighted contributions are shown only "
        "when the governed receipt carries them."
    )
    if not ranked.empty:
        ranked_names = ranked.sort_values(
            "nwr_rank",
            key=lambda values: pd.to_numeric(values, errors="coerce"),
        )["player_name"].astype(str).tolist()
        selected_name = st.selectbox(
            "Explain player",
            ranked_names,
            key="rankings_statistical_analysis_player",
        )
        selected_row = ranked.loc[ranked["player_name"].astype(str).eq(selected_name)].iloc[0]
        summary, evidence, caveat = owner_rank_explanation(
            selected_row.to_dict(), total_ranked=len(ranked)
        )
        st.markdown(f"### {selected_name}: why this rank")
        st.write(summary)
        st.dataframe(evidence, use_container_width=True, hide_index=True)
        if caveat:
            st.warning(caveat)
    if available:
        st.dataframe(
            ranked.loc[:, available].rename(
                columns={
                    "player_name": "Player",
                    "position": "Pos",
                    "nwr_rank": "Rank",
                    "nwr_dynasty_score": "Score",
                    "confidence_cap": "Confidence Cap",
                    "confidence_status": "Confidence",
                    "candidate_adjustment": "Admitted Adjustment",
                    "candidate_reason_codes": "Why / Gate Reasons",
                    "candidate_evidence_fields_used": "Evidence Fields Used",
                    "candidate_confidence_trust_impact": "Confidence Impact",
                    "risk_level": "Risk",
                    "warning_flags": "Warnings",
                    "data_needed": "Data Needed",
                }
            ),
            use_container_width=True,
            hide_index=True,
            key="rankings_statistical_receipts",
        )
    with st.expander("Score Breakdown feasibility", expanded=False):
        st.write(
            {
                "current_status": "DEFER",
                "future_candidate_status": "MODEL_FEATURE_CANDIDATE",
                "available_fields": (
                    "nwr_dynasty_score, score_status, source_path, source_column, "
                    "model_version, score_type, score_as_of_date, confidence_cap, "
                    "confidence_status, allowed_use, blocked_use, "
                    "candidate_evidence_fields_used"
                ),
                "missing_fields": (
                    "approved component names, component weights, component scores, "
                    "weighted contribution amounts, percent contribution, and component "
                    "receipt rows"
                ),
                "main_table_behavior": "Unsupported contribution fields are omitted.",
                "doc": (
                    "docs/hq/rankings/statistic_analysis_v0_20260630/statistic_analysis_design.md"
                ),
            }
        )


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
            "lives inside Dynasty Rankings and Draft Cockpit."
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
nflverse_unified_board = integrate_nflverse_player_context_display(raw_unified_board)
unified_board = enrich_unified_player_board_with_market_baseline(nflverse_unified_board)
outcome_counts = outcome_display_coverage_counts(unified_board)
outcome_v2_counts = outcome_v2_display_coverage_counts(unified_board)
nflverse_context_counts = nflverse_player_context_display_counts(unified_board)
frozen_outcome_counts = frozen_board_outcome_support_counts(bundle.frame)
finished_v1_counts = finished_v1_coverage_counts(dynasty_bundle.frame)

page_header(
    "Dynasty Rankings",
    eyebrow="Draft-Day App V1",
    description=(
        "Search and filter the 232 production-ranked QB/RB/WR/TE players. Eight structural "
        "kicker assets remain discoverable elsewhere and are not presented as ranked."
    ),
    status_items=(
        (
            f"{finished_v1_counts['ranked_skill_players']} production-ranked QB/RB/WR/TE players",
            "safe" if dynasty_bundle.loaded else "review",
        ),
        (
            f"{finished_v1_counts['unranked_kickers']} structural kicker assets · "
            "outside ranking coverage",
            "review",
        ),
        (f"Frozen baseline rows: {bundle.row_count}", "safe" if bundle.loaded else "blocked"),
        (
            "Outcome support: "
            f"{frozen_outcome_counts['supported']}/{frozen_outcome_counts['rows']}",
            "review",
        ),
        (
            "NFLVerse context rows: "
            f"{nflverse_context_counts['safe']}/{nflverse_context_counts['rows']}",
            "review",
        ),
    ),
)
ranking_authority_view = st.radio(
    "Ranking authority view",
    (
        "Finished V1 — Production",
        "Unified Dynasty Preview — Research Only",
        "Rookie Review — Review Only",
    ),
    index=0,
    horizontal=True,
    key="dynasty_ranking_authority_view",
)
owner_registry = load_governed_asset_registry(
    repo_root=REPO_ROOT,
    current_board_path=dynasty_bundle.source_path,
)
if not owner_registry.errors:
    owner_assets = {row["asset_id"]: row for row in owner_registry.rows}
    owner_asset_id = st.selectbox(
        "Find any governed asset",
        sorted(owner_assets, key=lambda key: owner_assets[key]["asset_name"]),
        format_func=lambda key: (
            f"{owner_assets[key]['asset_name']} · {owner_assets[key]['asset_type']} · "
            f"{owner_assets[key]['authority_status']}"
        ),
        key="dynasty_rankings_governed_asset_search",
    )
    st.markdown(f"[Open Player Detail](/player-detail?asset={quote(owner_asset_id, safe='')})")
if ranking_authority_view == "Unified Dynasty Preview — Research Only":
    st.warning(
        "RESEARCH ONLY — NOT PRODUCTION AUTHORITY. Calibration is not fully validated and "
        "there is no fresh mature 5Y rookie cohort. Decision support only; this view does "
        "not replace Finished V1 or admit a production rookie-veteran ranking."
    )
    try:
        research_preview = load_unified_research_preview()
    except (OSError, ValueError) as exc:
        st.error(f"Frozen Unified Dynasty Preview is unavailable: {exc}")
        st.stop()
    preview = research_preview.board.copy()
    preview_controls = st.columns((2, 1, 1, 1))
    preview_query = preview_controls[0].text_input("Search", key="unified_preview_search")
    preview_positions = preview_controls[1].multiselect(
        "Position", sorted(preview["position"].dropna().unique()), key="unified_preview_position"
    )
    preview_types = preview_controls[2].multiselect(
        "Asset Type", ("VETERAN", "ROOKIE"), key="unified_preview_asset_type"
    )
    include_blocked = preview_controls[3].checkbox(
        "Include blocked", value=True, key="unified_preview_include_blocked"
    )
    if preview_query.strip():
        preview = preview.loc[
            preview["player"]
            .fillna("")
            .str.contains(preview_query.strip(), case=False, regex=False)
        ]
    if preview_positions:
        preview = preview.loc[preview["position"].isin(preview_positions)]
    if preview_types:
        preview = preview.loc[preview["asset_type"].isin(preview_types)]
    if not include_blocked:
        preview = preview.loc[preview["research_rank"].notna()]
    preview["_rank_sort"] = pd.to_numeric(preview["research_rank"], errors="coerce").fillna(9999)
    preview = preview.sort_values(["_rank_sort", "player"], kind="stable")
    st.caption(
        "Frozen exact order: 231 eligible veterans + 73 eligible rookies; 16 blocked assets "
        "remain visible and unranked. No refit, tuning, or manual reorder was performed."
    )
    st.dataframe(
        preview[
            [
                "research_rank",
                "player",
                "position",
                "asset_type",
                "research_tier",
                "outlook_3y",
                "outlook_5y",
                "ceiling_signal",
                "downside_signal",
                "confidence",
                "evidence_coverage",
                "existing_finished_v1_rank",
                "existing_rookie_review_rank",
                "status",
                "blocking_reason",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        key="unified_dynasty_research_preview_table",
    )
    st.markdown("### Rookie veteran neighborhoods — Research Only")
    rookie_neighborhoods = research_preview.neighborhoods.copy()
    rookie_choice = st.selectbox(
        "Eligible rookie",
        rookie_neighborhoods["rookie"].astype(str).tolist(),
        key="unified_preview_rookie_neighborhood",
    )
    neighborhood = rookie_neighborhoods.loc[
        rookie_neighborhoods["rookie"].astype(str).eq(rookie_choice)
    ].iloc[0]
    st.caption(
        f"{neighborhood['rookie']} ({neighborhood['position']}) — research rank "
        f"{int(neighborhood['research_rank'])}, {neighborhood['research_tier']}. "
        f"Veterans above: {neighborhood['veterans_above'] or 'none'}. "
        f"Veterans below: {neighborhood['veterans_below'] or 'none'}."
    )
    st.caption(
        f"Uncertainty context: confidence {float(neighborhood['confidence']):.3f}; "
        f"evidence coverage {float(neighborhood['evidence_coverage']):.3f}. Frozen ordering; "
        "not production-admitted."
    )
    st.caption(
        "Research ranks are comparable only inside this frozen research preview. They are not "
        "trade values, recommendations, fair values, or production ranks."
    )
    st.stop()
if ranking_authority_view == "Rookie Review — Review Only":
    st.info(
        "Rookie Review remains a separate review-only authority. Its cohort ranks and scores "
        "are not comparable with Finished V1 production values."
    )
    st.page_link("pages/48_rookie_board_v1.py", label="Open Rookie Board — Review Only")
    st.stop()
render_source_freshness(freshness_for_sources(("Finished V1", "Outcome V3")))
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

_rankings_freshness = market_baseline_freshness_status()
with st.expander("Advanced Data Details", expanded=False):
    render_decision_trust_strips(
        [
            build_rankings_dataset_trust_strip(
                source_available=dynasty_bundle.loaded,
                source_label=str(dynasty_bundle.source_path or "approved dynasty source"),
                source_hash=dynasty_bundle.source_hash or "",
                freshness_status=(
                    _rankings_freshness.get("freshness_status") or OUTCOME_NOT_ENOUGH_INFORMATION
                ),
                identity_review_rows=int(nflverse_context_counts.get("review", 0)),
                missing_rows=_source_count(unified_board, "Frozen Baseline only"),
                warnings=(*dynasty_bundle.warnings, *bundle.warnings),
            )
        ],
        heading="Board evidence trust",
    )
    _render_market_baseline_status(raw_unified_board)
    _render_dataset_refresh_status_panel(unified_board)
preset = st.session_state.get("dynasty_rankings_view_preset", VIEW_PRESET_DYNASTY_REVIEW)
if preset not in VIEW_PRESETS:
    preset = VIEW_PRESET_DYNASTY_REVIEW
(
    filtered_board,
    sort_by,
    outcome_mode,
    show_market_baseline,
    show_statistic_analysis,
    view_mode,
) = _apply_player_filters(
    unified_board,
    preset,
)

st.caption(
    f"Rows shown: {int(filtered_board.shape[0])} | Preset: {preset} | View: {view_mode} | "
    f"Sort: {sort_by} | Outcome columns: {outcome_mode}. Outcome is display-only and does "
    "not drive sort."
)
st.caption(
    "Research Context Rank / Score, when present, are review-only cross-asset context "
    "and do not replace Dynasty Rank or Final Board Rank."
)
st.caption(
    "Visible Outcome heads: "
    + _outcome_head_caption(
        filtered_board,
        outcome_mode,
        include_injury_context=preset == VIEW_PRESET_OUTCOME_CONTEXT,
    )
)
st.caption(
    "Market fields, when visible, are external market context only. Not rank logic, "
    "not model input, not trade value, and not a replacement for Dynasty Rank."
)
if show_market_baseline:
    st.caption(
        "Visible market basics: DP 1QB Value, DP 1QB Market Rank, NWR vs Market Gap, "
        "and Market Sanity Flag."
    )
if preset == VIEW_PRESET_OUTCOME_CONTEXT:
    _render_outcome_v3_compact_lens(filtered_board)
if preset == VIEW_PRESET_STATISTIC_ANALYSIS:
    _render_statistic_analysis_status(filtered_board)
_render_tier_board_cheat_sheet(filtered_board, view_mode)
st.dataframe(
    display_unified_player_board_frame(
        filtered_board,
        view_mode=view_mode,
        outcome_mode=outcome_mode,
        selected_positions=filtered_board.get("position", pd.Series(dtype=str)).tolist(),
        show_market_baseline=show_market_baseline,
        include_injury_context=preset == VIEW_PRESET_OUTCOME_CONTEXT,
        show_statistic_analysis=show_statistic_analysis,
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
