from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.draft_day_workflow_service import (
    DraftWorkflowError,
    assign_player_to_pick,
    available_board_frame,
    copy_state,
    current_pick_number,
    display_draft_board_frame,
    display_ranking_frame,
    draft_board_frame,
    empty_workflow_state,
    pick_select_options,
    player_select_options,
    remove_pick_assignment,
    sort_workflow_frame,
    undo_last_pick,
    validate_no_duplicate_assignments,
    with_workflow_columns,
    workflow_summary,
)


def render_draft_workflow(
    *,
    mode_label: str,
    board_frame: pd.DataFrame,
    pick_frame: pd.DataFrame,
    nwr_picks_frame: pd.DataFrame,
    session_key: str,
    source_caption: str,
) -> None:
    if session_key not in st.session_state:
        st.session_state[session_key] = empty_workflow_state()
    st.session_state[session_key] = copy_state(st.session_state[session_key])
    state = st.session_state[session_key]

    summary = workflow_summary(board_frame, pick_frame, state)
    st.caption(
        "Pick a player from the table, assign to current pick or a chosen pick slot, "
        "undo if needed. This is session-only draft tracking and does not mutate source data."
    )
    st.caption(source_caption)
    current_owner = f" - {summary.current_pick_owner}" if summary.current_pick_owner else ""
    st.caption(
        " | ".join(
            (
                f"Frozen board rows: {len(board_frame)}",
                f"Drafted: {summary.drafted_count}",
                f"Available: {summary.available_count}",
                f"Current pick: {summary.current_pick_label}{current_owner}",
            )
        )
    )
    st.caption(
        "Default order is Final Board Rank ascending. Visible Score uses mixed source bases "
        "(rookie board score vs dropped-veteran candidate value), so rank and asset type are "
        "the safer live-draft reading."
    )

    filtered = _render_filters(board_frame, state, session_key=session_key)
    st.subheader("Main Ranking Table")
    st.dataframe(
        display_ranking_frame(filtered),
        use_container_width=True,
        hide_index=True,
        key=f"{session_key}_ranking_table",
    )

    _render_pick_controls(
        mode_label=mode_label,
        filtered_frame=filtered,
        board_frame=board_frame,
        pick_frame=pick_frame,
        session_key=session_key,
    )

    st.subheader("Draft Board")
    board_rows = draft_board_frame(pick_frame, nwr_picks_frame, st.session_state[session_key])
    st.dataframe(
        display_draft_board_frame(board_rows),
        use_container_width=True,
        hide_index=True,
        key=f"{session_key}_draft_board",
    )

    issues = validate_no_duplicate_assignments(st.session_state[session_key])
    if issues:
        for issue in issues:
            st.error(issue)

    with st.expander("Draft history / edit view", expanded=False):
        assigned = board_rows.loc[board_rows["pick_status"].astype(str) == "Drafted"]
        if assigned.empty:
            st.caption("No picks have been assigned in this session.")
        else:
            st.dataframe(
                display_draft_board_frame(assigned),
                use_container_width=True,
                hide_index=True,
                key=f"{session_key}_history",
            )


def _render_filters(
    board_frame: pd.DataFrame,
    state: dict[str, list[dict[str, object]]],
    *,
    session_key: str,
) -> pd.DataFrame:
    frame = with_workflow_columns(board_frame, state)
    with st.container():
        filter_cols = st.columns([1, 1, 1, 1, 1, 1])
        status_filter = filter_cols[0].selectbox(
            "Draft status",
            ["Available only", "All", "Drafted only"],
            key=f"{session_key}_draft_status",
        )
        position_values = _values(frame, "position")
        position = filter_cols[1].selectbox(
            "Position",
            ["All", *position_values],
            key=f"{session_key}_position",
        )
        tier_values = _values(frame, "final_tier")
        tier = filter_cols[2].selectbox("Tier", ["All", *tier_values], key=f"{session_key}_tier")
        asset_values = _values(frame, "asset_type")
        asset_type = filter_cols[3].selectbox(
            "Asset Type",
            ["All", *asset_values],
            key=f"{session_key}_asset_type",
        )
        action_values = _values(frame, "draft_action_display_only")
        action = filter_cols[4].selectbox(
            "Target/watch/avoid",
            ["All", *action_values],
            key=f"{session_key}_action",
        )
        manual_only = filter_cols[5].checkbox(
            "Manual review",
            key=f"{session_key}_manual_review",
        )

        sort_cols = st.columns([1, 1, 2])
        sort_by = sort_cols[0].selectbox(
            "Sort by",
            [
                "Final Board Rank",
                "Player",
                "Position",
                "Tier",
                "Visible Board Score",
                "Draft Status",
            ],
            key=f"{session_key}_sort_by",
        )
        ascending = sort_cols[1].toggle("Ascending", value=True, key=f"{session_key}_ascending")
        search = sort_cols[2].text_input("Search player", key=f"{session_key}_search")

    if status_filter == "Available only":
        frame = available_board_frame(board_frame, state)
    elif status_filter == "Drafted only":
        frame = frame.loc[frame["draft_status"] == "Drafted"].copy()
    if position != "All" and "position" in frame.columns:
        frame = frame.loc[frame["position"].astype(str) == position].copy()
    if tier != "All" and "final_tier" in frame.columns:
        frame = frame.loc[frame["final_tier"].astype(str) == tier].copy()
    if asset_type != "All" and "asset_type" in frame.columns:
        frame = frame.loc[frame["asset_type"].astype(str) == asset_type].copy()
    if action != "All" and "draft_action_display_only" in frame.columns:
        frame = frame.loc[frame["draft_action_display_only"].astype(str) == action].copy()
    if manual_only and "needs_manual_review" in frame.columns:
        frame = frame.loc[
            frame["needs_manual_review"].astype(str).str.lower().isin({"true", "yes", "1"})
        ].copy()
    if search and "player" in frame.columns:
        frame = frame.loc[
            frame["player"].astype(str).str.contains(search, case=False, na=False)
        ].copy()
    return sort_workflow_frame(frame, sort_by, ascending=ascending)


def _render_pick_controls(
    *,
    mode_label: str,
    filtered_frame: pd.DataFrame,
    board_frame: pd.DataFrame,
    pick_frame: pd.DataFrame,
    session_key: str,
) -> None:
    st.subheader("Pick Selection")
    st.caption(
        f"{mode_label}: manual selection only. No simulator pick algorithm or automatic "
        "recommendation is running."
    )
    player_options = player_select_options(filtered_frame)
    pick_options = pick_select_options(pick_frame)
    if not player_options or not pick_options:
        st.warning("Player or pick context is missing, so picks cannot be assigned.")
        return
    _sync_pick_slot_selectbox(session_key, pick_options, pick_frame)

    cols = st.columns([2, 2, 1, 1])
    player_label = cols[0].selectbox(
        "Player from current table",
        list(player_options),
        key=f"{session_key}_selected_player",
    )
    pick_label = cols[1].selectbox(
        "Pick slot",
        list(pick_options),
        key=f"{session_key}_selected_pick",
    )
    if cols[2].button("Assign Pick", key=f"{session_key}_assign", use_container_width=True):
        try:
            st.session_state[session_key] = assign_player_to_pick(
                st.session_state[session_key],
                board=board_frame,
                pick_frame=pick_frame,
                player_key=player_options[player_label],
                overall_pick=pick_options[pick_label],
            )
            st.session_state[f"{session_key}_sync_pick_to_current"] = True
            st.success(f"Assigned {player_label} to {pick_label}.")
            st.rerun()
        except DraftWorkflowError as exc:
            st.error(str(exc))
    if cols[3].button("Undo Last", key=f"{session_key}_undo", use_container_width=True):
        st.session_state[session_key], message = undo_last_pick(st.session_state[session_key])
        st.session_state[f"{session_key}_sync_pick_to_current"] = True
        st.info(message)
        st.rerun()

    edit_cols = st.columns([2, 1])
    remove_pick_label = edit_cols[0].selectbox(
        "Edit/remove assigned pick",
        list(pick_options),
        key=f"{session_key}_remove_pick",
    )
    if edit_cols[1].button(
        "Remove Player",
        key=f"{session_key}_remove_assignment",
        use_container_width=True,
    ):
        st.session_state[session_key], message = remove_pick_assignment(
            st.session_state[session_key],
            pick_options[remove_pick_label],
        )
        st.session_state[f"{session_key}_sync_pick_to_current"] = True
        st.info(message)
        st.rerun()


def _values(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame.columns:
        return []
    return sorted(value for value in frame[column].astype(str).unique().tolist() if value)


def _sync_pick_slot_selectbox(
    session_key: str,
    pick_options: dict[str, int],
    pick_frame: pd.DataFrame,
) -> None:
    selected_pick_key = f"{session_key}_selected_pick"
    sync_flag_key = f"{session_key}_sync_pick_to_current"
    current = current_pick_number(pick_frame, st.session_state[session_key])
    if current is None:
        return
    current_label = next(
        (label for label, overall in pick_options.items() if overall == current),
        next(iter(pick_options)),
    )
    selected_label = st.session_state.get(selected_pick_key)
    assigned_picks = {
        int(row.get("overall_pick", 0))
        for row in st.session_state[session_key].get("assignments", [])
        if row.get("overall_pick") is not None
    }
    selected_overall = pick_options.get(str(selected_label), None)
    should_sync = (
        bool(st.session_state.pop(sync_flag_key, False))
        or selected_label not in pick_options
        or selected_overall in assigned_picks
    )
    if should_sync:
        st.session_state[selected_pick_key] = current_label
