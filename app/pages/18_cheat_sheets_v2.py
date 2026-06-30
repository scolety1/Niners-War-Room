from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import render_frozen_baseline_badge, stop_if_board_blocked
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    load_expanded_draftable_player_pool,
    load_frozen_board,
    load_lane_prop_file,
)
from src.services.draft_day_runtime_state_service import (
    apply_trade_events_to_pick_frame,
    load_runtime_state,
)
from src.services.draft_day_workflow_service import (
    NOT_ENOUGH_INFORMATION,
    available_board_frame,
    current_pick_label,
    current_pick_number,
    sort_workflow_frame,
    with_workflow_columns,
    workflow_summary,
)


def _display_cheat_sheet(
    frame: pd.DataFrame,
    *,
    density: str,
    note_mode: str,
    show_drafted_context: bool,
    current_pick: int | None,
) -> pd.DataFrame:
    contextual = _with_current_pick_value(frame, current_pick=current_pick)
    base_columns = _columns_for_density(density)
    if note_mode in {"Detailed notes", "Data-health warnings"}:
        base_columns.extend(["why_draft", "main_risk"])
    if note_mode == "Data-health warnings":
        base_columns.extend(
            [
                "human_review_flag",
                "risk_notes",
                "needs_manual_review",
                "outcome_applicable_summary",
                "source_label_display_only",
                "candidate_key_caveat",
            ]
        )
    if show_drafted_context:
        base_columns = ["draft_status", "assigned_pick", *base_columns]
    columns = [column for column in dict.fromkeys(base_columns) if column in contextual.columns]
    display = contextual.loc[:, columns].fillna(NOT_ENOUGH_INFORMATION).copy()
    return display.rename(columns=_column_labels())


def _columns_for_density(density: str) -> list[str]:
    compact = [
        "dynasty_asset_rank",
        "player",
        "position",
        "nfl_team",
        "age",
        "dynasty_asset_tier",
        "final_board_rank",
    ]
    standard = [
        *compact,
        "position_rank",
        "dynasty_asset_confidence",
        "pool_adp_pick_equivalent",
        "available_pool_adp_range",
        "at_current_pick_value",
    ]
    detailed = [
        *standard,
        "dynasty_asset_score",
        "cross_asset_candidate_rank",
        "candidate_value_band",
        "confidence_band",
    ]
    if density == "Compact":
        return compact
    if density == "Detailed":
        return detailed
    return standard


def _column_labels() -> dict[str, str]:
    return {
        "draft_status": "Draft Status",
        "assigned_pick": "Assigned Pick",
        "dynasty_asset_rank": "Dynasty Rank",
        "dynasty_asset_tier": "Dynasty Asset Tier",
        "final_board_rank": "Final Board Rank",
        "player": "Player",
        "position": "Pos",
        "nfl_team": "NFL Team",
        "age": "Age",
        "position_rank": "Position Rank",
        "dynasty_asset_score": "Dynasty Value",
        "dynasty_asset_confidence": "Confidence",
        "cross_asset_candidate_rank": "Candidate Rank (Review-Only)",
        "candidate_value_band": "Candidate Band",
        "confidence_band": "Candidate Confidence",
        "pool_adp_pick_equivalent": "Pool ADP Pick (Display-Only)",
        "available_pool_adp_range": "ADP Range (Display-Only)",
        "at_current_pick_value": "Current Pick Value (Display-Only)",
        "why_draft": "Summary Note",
        "main_risk": "Key Risk",
        "human_review_flag": "Human Review",
        "risk_notes": "Risk Notes",
        "needs_manual_review": "Needs Manual Review",
        "outcome_applicable_summary": "Outcome/Horizon",
        "source_label_display_only": "Source",
        "candidate_key_caveat": "Data-Health Caveat",
    }


def _with_current_pick_value(frame: pd.DataFrame, *, current_pick: int | None) -> pd.DataFrame:
    contextual = frame.copy()
    if "available_pool_adp_rank" not in contextual.columns:
        return contextual
    contextual["at_current_pick_value"] = [
        _current_pick_value(current_pick, value)
        for value in contextual["available_pool_adp_rank"].tolist()
    ]
    if "pool_adp_pick_equivalent" not in contextual.columns:
        contextual["pool_adp_pick_equivalent"] = [
            _pool_adp_pick(value) for value in contextual["available_pool_adp_rank"].tolist()
        ]
    return contextual


def _current_pick_value(current_pick: int | None, value: object) -> str:
    if current_pick is None:
        return NOT_ENOUGH_INFORMATION
    try:
        pool_rank = float(str(value).strip())
    except ValueError:
        return NOT_ENOUGH_INFORMATION
    delta = float(current_pick) - pool_rank
    if delta <= -8:
        return "Too early"
    if delta <= -4:
        return "Reach"
    if delta <= -2:
        return "Slight reach"
    if delta >= 10:
        return "Steal"
    if delta >= 3:
        return "Value"
    return "Fair"


def _pool_adp_pick(value: object) -> str:
    try:
        rank = int(float(str(value).strip()))
    except ValueError:
        return NOT_ENOUGH_INFORMATION
    if rank <= 0:
        return NOT_ENOUGH_INFORMATION
    return f"{((rank - 1) // 10) + 1}.{((rank - 1) % 10) + 1:02d}"


def _filter_cheat_sheet_frame(
    pool: pd.DataFrame,
    *,
    runtime_state: dict[str, object],
    selected_positions: list[str],
    search: str,
    show_drafted: bool,
    show_pdf: bool,
    show_kdst: bool,
    manual_review_only: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    state = runtime_state.get("workflow_state", {"assignments": []})
    frame = (
        with_workflow_columns(pool, state)
        if show_drafted
        else available_board_frame(pool, state)
    )
    unfiltered = frame.copy()
    if not show_pdf and "source_group" in frame.columns:
        frame = frame.loc[~frame["source_group"].astype(str).eq("LVE PDF Free Agent")].copy()
    if not show_kdst and "position" in frame.columns:
        frame = frame.loc[~frame["position"].astype(str).str.upper().isin({"K", "DST"})].copy()
    if selected_positions and "position" in frame.columns:
        frame = frame.loc[frame["position"].astype(str).isin(selected_positions)].copy()
    if manual_review_only and "needs_manual_review" in frame.columns:
        frame = frame.loc[
            frame["needs_manual_review"].astype(str).str.lower().isin({"true", "yes", "1"})
        ].copy()
    if search and "player" in frame.columns:
        frame = frame.loc[
            frame["player"].astype(str).str.contains(search, case=False, na=False)
        ].copy()
    return frame, unfiltered


def _render_status_strip(
    *,
    pool: pd.DataFrame,
    frame: pd.DataFrame,
    runtime_state: dict[str, object],
    pick_frame: pd.DataFrame,
    current_label: str,
) -> None:
    state = runtime_state.get("workflow_state", {"assignments": []})
    summary = workflow_summary(pool, pick_frame, state) if not pick_frame.empty else None
    drafted_count = int(summary.drafted_count) if summary else len(state.get("assignments", []))
    available_count = int(frame.shape[0])
    chips = [
        f"Current pick: {current_label}",
        f"Drafted: {drafted_count}",
        f"Shown: {available_count}",
        "Source: Frozen Baseline + approved overlays",
        "ADP/market: display-only",
    ]
    st.caption(" | ".join(chips))


def _render_tiered_board(
    frame: pd.DataFrame,
    *,
    density: str,
    note_mode: str,
    show_drafted_context: bool,
    current_pick: int | None,
) -> None:
    if frame.empty:
        st.warning(
            "No players match the current cheat-sheet filters. Use Search, Show drafted, "
            "or Show PDF free agents to widen the view."
        )
        return
    tier_column = "dynasty_asset_tier" if "dynasty_asset_tier" in frame.columns else "final_tier"
    if tier_column not in frame.columns:
        st.dataframe(
            _display_cheat_sheet(
                frame,
                density=density,
                note_mode=note_mode,
                show_drafted_context=show_drafted_context,
                current_pick=current_pick,
            ),
            use_container_width=True,
            hide_index=True,
        )
        return

    for tier, tier_frame in frame.groupby(frame[tier_column].fillna(NOT_ENOUGH_INFORMATION)):
        label = str(tier or NOT_ENOUGH_INFORMATION)
        st.markdown(f"#### {label} · {len(tier_frame)} players")
        st.dataframe(
            _display_cheat_sheet(
                tier_frame,
                density=density,
                note_mode=note_mode,
                show_drafted_context=show_drafted_context,
                current_pick=current_pick,
            ),
            use_container_width=True,
            hide_index=True,
        )


def _all_positions(pool: pd.DataFrame) -> list[str]:
    if "position" not in pool.columns:
        return []
    return sorted(
        value
        for value in pool["position"].astype(str).unique().tolist()
        if value and value.upper() not in {"K", "DST"}
    )


def _query_flag(name: str) -> bool:
    values: list[object] = []
    try:
        values.extend(st.query_params.get_all(name))
    except AttributeError:
        pass
    value = st.query_params.get(name)
    if value is not None:
        values.append(value)
    return any(str(item or "").lower() in {"1", "true", "yes"} for item in values)


def _query_value(name: str) -> str:
    values: list[object] = []
    try:
        values.extend(st.query_params.get_all(name))
    except AttributeError:
        pass
    value = st.query_params.get(name)
    if value is not None:
        values.append(value)
    return str(values[0] if values else "").strip().lower()


def _runtime_mode_from_query() -> str:
    mode = _query_value("session_type") or _query_value("mode")
    return "mock" if mode in {"mock", "practice", "mock_practice"} else "live"


bundle = load_frozen_board()
pool = load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else bundle.frame
runtime_mode = _runtime_mode_from_query()
runtime_state = load_runtime_state(mode=runtime_mode)
pick_frame, pick_path = load_lane_prop_file("mock_draft", "mock_pick_context.csv")
effective_pick_frame = apply_trade_events_to_pick_frame(pick_frame, runtime_state)
workflow_state = runtime_state.get("workflow_state", {"assignments": []})
current_pick = (
    current_pick_number(effective_pick_frame, workflow_state)
    if not effective_pick_frame.empty
    else None
)
current_label = (
    current_pick_label(effective_pick_frame, workflow_state)
    if not effective_pick_frame.empty
    else NOT_ENOUGH_INFORMATION
)

page_header(
    "Cheat Sheets",
    eyebrow="Draft-Day App V2",
    description=(
        "Overall-first tiered board for fast draft decisions. Position filters are secondary; "
        "rank, tier, and source-truth assignments are unchanged."
    ),
    status_items=(
        ("Overall-first", "safe"),
        ("Tiered", "safe"),
        ("Display only", "review"),
    ),
)
st.info(
    "Compatibility route: Cheat Sheets is a secondary tier-board view. The primary "
    "draft-day tier scan now lives inside Draft Cockpit and Dynasty Rankings."
)
if runtime_mode == "mock":
    st.warning("Practice state only — does not affect live draft.")
render_frozen_baseline_badge(bundle)
stop_if_board_blocked(bundle)

show_drafted_default = _query_flag("show_drafted")
show_kdst_default = _query_flag("show_kdst")

control_cols = st.columns([1.05, 1.1, 1.05, 1.05, 1.05])
view = control_cols[0].selectbox(
    "View",
    ["Overall Ranking", "By Position", "Manual Review"],
    key="cheat_sheet_view",
)
search = control_cols[1].text_input(
    "Search",
    key="cheat_sheet_search",
    placeholder="Find a player",
)
density = control_cols[2].selectbox(
    "Density",
    ["Compact", "Standard", "Detailed"],
    index=1,
    key="cheat_sheet_density",
)
note_mode = control_cols[3].selectbox(
    "Notes",
    ["Summary notes", "Detailed notes", "Data-health warnings"],
    key="cheat_sheet_note_mode",
)
limit = control_cols[4].number_input(
    "Players",
    min_value=10,
    max_value=300,
    value=80,
    step=10,
    key="cheat_sheet_limit",
)

filter_cols = st.columns([1.35, 0.95, 0.9, 1, 0.85, 1])
positions = _all_positions(pool)
selected_positions = filter_cols[0].multiselect(
    "Position filters",
    positions,
    default=positions,
    key="cheat_sheet_positions",
)
drafted_rows_mode = filter_cols[1].selectbox(
    "Drafted rows",
    ["Hide drafted", "Show drafted"],
    index=1 if show_drafted_default else 0,
    key="cheat_sheet_drafted_rows_mode",
)
show_drafted_toggle = filter_cols[2].toggle(
    "Show drafted",
    value=show_drafted_default,
    key="cheat_sheet_show_drafted",
)
show_drafted = (
    show_drafted_default
    or show_drafted_toggle
    or drafted_rows_mode == "Show drafted"
)
show_pdf = filter_cols[3].toggle(
    "Show PDF free agents",
    value=True,
    key="cheat_sheet_show_pdf",
)
show_kdst_toggle = filter_cols[4].toggle(
    "Show K/DST",
    value=show_kdst_default,
    key="cheat_sheet_show_kdst",
)
show_kdst = show_kdst_default or show_kdst_toggle
manual_review_only = filter_cols[5].toggle(
    "Manual review only",
    value=view == "Manual Review",
    key="cheat_sheet_manual_review_only",
)

filtered, workflow_frame = _filter_cheat_sheet_frame(
    pool,
    runtime_state=runtime_state,
    selected_positions=selected_positions,
    search=search,
    show_drafted=show_drafted,
    show_pdf=show_pdf,
    show_kdst=show_kdst,
    manual_review_only=manual_review_only,
)
filtered = sort_workflow_frame(filtered, "Dynasty Asset Tier/Rank").head(int(limit))

_render_status_strip(
    pool=pool,
    frame=filtered,
    runtime_state=runtime_state,
    pick_frame=effective_pick_frame,
    current_label=current_label,
)
st.caption(
    "Candidate/Dynasty Rank is review-only. Final Board Rank remains the frozen baseline. "
    "ADP/range/current-pick context is display-only and does not sort this page by default."
)

if search and filtered.empty:
    st.info(
        "No on-table match found. Try broadening filters or open `/player-compare` for "
        "off-table lookup."
    )

if view == "By Position":
    for position in selected_positions:
        position_frame = filtered.loc[filtered["position"].astype(str).eq(position)].copy()
        if position_frame.empty:
            continue
        st.markdown(f"### {position}")
        _render_tiered_board(
            position_frame,
            density=density,
            note_mode=note_mode,
            show_drafted_context=show_drafted,
            current_pick=current_pick,
        )
else:
    _render_tiered_board(
        filtered,
        density=density,
        note_mode=note_mode,
        show_drafted_context=show_drafted,
        current_pick=current_pick,
    )

with st.expander("Search / off-table path", expanded=bool(search and filtered.empty)):
    st.caption(
        "Use the search box above for this cheat sheet. For deeper off-table review, open "
        "`/player-compare` or the Search tab inside `/drafting-mode`."
    )
    st.caption(
        "Browser-safe toggles: add `?show_drafted=1` or `?show_kdst=1` to this page "
        "for deterministic preview states."
    )
    search_columns = [
        column
        for column in ("draft_status", "player", "position", "nfl_team", "final_board_rank")
        if column in workflow_frame.columns
    ]
    if search and search_columns:
        search_rows = workflow_frame.loc[
            workflow_frame["player"].astype(str).str.contains(search, case=False, na=False),
            search_columns,
        ].head(20)
        if search_rows.empty:
            st.write(NOT_ENOUGH_INFORMATION)
        else:
            st.dataframe(
                search_rows.fillna(NOT_ENOUGH_INFORMATION).rename(columns=_column_labels()),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.code("/player-compare")

with st.expander("Source / guardrails", expanded=False):
    st.caption(
        "Cheat Sheets V2 uses the frozen board plus existing app overlay context. It does not "
        "change Final Board Rank, Dynasty Rank, tier assignments, latest files, "
        "or pinned snapshots."
    )
    st.caption(f"Rows available before filters: {len(pool)}")
    st.caption(
        f"{runtime_mode.title()} runtime assignments: "
        f"{len(workflow_state.get('assignments', []))}"
    )
    st.caption(f"Pick source: {pick_path or NOT_ENOUGH_INFORMATION}")
    st.caption(
        "Missing data must stay as Not enough information. Market, ADP, DynastyProcess, "
        "projection, and vendor context are display-only where shown."
    )
