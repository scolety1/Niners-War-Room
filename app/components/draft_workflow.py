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
    current_owner = f" - {summary.current_pick_owner}" if summary.current_pick_owner else ""
    frozen_rows = _non_pdf_row_count(board_frame)
    pdf_rows = _pdf_row_count(board_frame)
    st.caption(
        " | ".join(
            (
                "Source: Frozen Board + verified PDF free-agent overlay",
                f"Frozen rows: {frozen_rows}",
                f"PDF FAs: {pdf_rows}",
                f"Draftable rows: {len(board_frame)}",
                f"Drafted: {summary.drafted_count}",
                f"Available: {summary.available_count}",
                f"Current pick: {summary.current_pick_label}{current_owner}",
            )
        )
    )

    current_pick = current_pick_number(pick_frame, state)
    filtered, show_drafted_players = _render_filters(
        board_frame,
        state,
        session_key=session_key,
    )
    st.caption(
        "How to use: Dynasty Asset Tier/Rank = emergency review-only decision aid | "
        "Final Board Rank = frozen baseline | Candidate Rank = tuned model context | "
        "Startup ADP / Pool ADP Pick = display-only timing context | "
        "Outcome/Horizon = partial display-only context."
    )
    on_clock_watch = _on_clock_watch_caption(board_frame)
    if on_clock_watch:
        st.caption(on_clock_watch)
    st.subheader("Main Ranking Table")
    st.dataframe(
        display_ranking_frame(
            filtered,
            show_drafted_context=show_drafted_players,
            current_pick=current_pick,
        ),
        use_container_width=True,
        hide_index=True,
        key=f"{session_key}_ranking_table",
    )

    _render_pick_controls(
        mode_label=mode_label,
        filtered_frame=filtered,
        board_frame=board_frame,
        pick_frame=pick_frame,
        current_pick=current_pick,
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

    with st.expander("Source / diagnostics", expanded=False):
        st.caption(source_caption)
        st.caption(
            "Picked-player state is session-only and does not mutate the frozen board. "
            "Picked players are hidden by default so the main table stays focused on available "
            "players."
        )
        st.caption(
            "Visible Score is intentionally hidden from the default table because rookies and "
            "dropped veterans use different score bases. ADP/range/current-pick value are "
            "display-only context and do not drive sorting, model value, or rankings."
        )


def _render_filters(
    board_frame: pd.DataFrame,
    state: dict[str, list[dict[str, object]]],
    *,
    session_key: str,
) -> tuple[pd.DataFrame, bool]:
    frame = with_workflow_columns(board_frame, state)
    with st.container():
        filter_cols = st.columns([1.35, 0.9, 0.9, 1.1, 0.9, 0.9, 0.9])
        search = filter_cols[0].text_input(
            "Search player",
            key=f"{session_key}_search",
            placeholder="Type a player",
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
        show_drafted_players = filter_cols[4].toggle(
            "Show drafted players",
            value=False,
            key=f"{session_key}_show_drafted_players",
        )
        show_pdf_free_agents = filter_cols[5].toggle(
            "Show PDF free agents",
            value=True,
            key=f"{session_key}_show_pdf_free_agents",
        )
        show_kickers_dst = filter_cols[6].toggle(
            "Show K/DST",
            value=False,
            key=f"{session_key}_show_kickers_dst",
        )

        sort_cols = st.columns([1.25, 1, 1, 1])
        manual_only = sort_cols[0].checkbox(
            "Manual review",
            key=f"{session_key}_manual_review",
        )
        view_mode = sort_cols[1].selectbox(
            "View / sort mode",
            [
                "Dynasty Asset Tiers",
                "Candidate Best Available",
                "Frozen Board Rank",
                "ADP / Price Context",
            ],
            key=f"{session_key}_view_sort_mode",
        )
        sort_default = {
            "Dynasty Asset Tiers": "Dynasty Asset Tier/Rank",
            "Candidate Best Available": "Candidate Rank",
            "Frozen Board Rank": "Final Board Rank",
            "ADP / Price Context": "Available-Pool ADP Rank",
        }[view_mode]
        sort_options = [
            "Dynasty Asset Tier/Rank",
            "Dynasty Asset Rank",
            "Dynasty Asset Score",
            "Candidate Rank",
            "Final Board Rank",
            "Available-Pool ADP Rank",
            "Candidate Value",
            "Player",
            "Position",
            "Position Rank",
            "Tier",
        ]
        sort_by = sort_cols[2].selectbox(
            "Sort by",
            sort_options,
            index=sort_options.index(sort_default),
            key=f"{session_key}_sort_by",
        )
        ascending_default = sort_by not in {"Candidate Value", "Dynasty Asset Score"}
        ascending = sort_cols[3].toggle(
            "Ascending",
            value=ascending_default,
            key=f"{session_key}_ascending",
        )

    if not show_drafted_players:
        frame = available_board_frame(board_frame, state)
    if not show_pdf_free_agents and "source_group" in frame.columns:
        frame = frame.loc[
            ~frame["source_group"].astype(str).eq("LVE PDF Free Agent")
        ].copy()
    if not show_kickers_dst and "position" in frame.columns:
        frame = frame.loc[
            ~frame["position"].astype(str).str.upper().isin({"K", "DST"})
        ].copy()
    if position != "All" and "position" in frame.columns:
        frame = frame.loc[frame["position"].astype(str) == position].copy()
    if tier != "All" and "final_tier" in frame.columns:
        frame = frame.loc[frame["final_tier"].astype(str) == tier].copy()
    if asset_type != "All" and "asset_type" in frame.columns:
        frame = frame.loc[frame["asset_type"].astype(str) == asset_type].copy()
    if manual_only and "needs_manual_review" in frame.columns:
        frame = frame.loc[
            frame["needs_manual_review"].astype(str).str.lower().isin({"true", "yes", "1"})
        ].copy()
    if search and "player" in frame.columns:
        frame = frame.loc[
            frame["player"].astype(str).str.contains(search, case=False, na=False)
        ].copy()
    return sort_workflow_frame(frame, sort_by, ascending=ascending), show_drafted_players


def _render_pick_controls(
    *,
    mode_label: str,
    filtered_frame: pd.DataFrame,
    board_frame: pd.DataFrame,
    pick_frame: pd.DataFrame,
    current_pick: int | None,
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
        index=_adp_timing_suggestion_index(filtered_frame, list(player_options), current_pick),
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


def _adp_timing_suggestion_index(
    frame: pd.DataFrame,
    option_labels: list[str],
    current_pick: int | None,
) -> int:
    if current_pick is None or frame.empty or "available_pool_adp_rank" not in frame.columns:
        return 0
    best: tuple[float, float, int] | None = None
    for index, (_row_index, row) in enumerate(frame.iterrows()):
        if index >= len(option_labels):
            break
        try:
            pool_rank = float(str(row.get("available_pool_adp_rank") or "").strip())
        except ValueError:
            continue
        candidate = (abs(pool_rank - float(current_pick)), pool_rank, index)
        if best is None or candidate < best:
            best = candidate
    return best[2] if best is not None else 0


def _pdf_row_count(frame: pd.DataFrame) -> int:
    if "source_group" not in frame.columns:
        return 0
    return int(frame["source_group"].astype(str).eq("LVE PDF Free Agent").sum())


def _non_pdf_row_count(frame: pd.DataFrame) -> int:
    if "source_group" not in frame.columns:
        return int(frame.shape[0])
    return int((~frame["source_group"].astype(str).eq("LVE PDF Free Agent")).sum())


def _on_clock_watch_caption(frame: pd.DataFrame) -> str:
    if "player" not in frame.columns:
        return ""
    targets = frame.loc[
        frame["player"]
        .astype(str)
        .isin(["Drake Maye", "Tyreek Hill", "Zay Flowers", "Chris Olave"])
    ].copy()
    if targets.empty:
        return ""
    parts: list[str] = []
    for name in ["Drake Maye", "Tyreek Hill", "Zay Flowers", "Chris Olave"]:
        row = targets.loc[targets["player"].astype(str).eq(name)]
        if row.empty:
            continue
        record = row.iloc[0]
        parts.append(
            f"{name}: Dynasty Asset {record.get('dynasty_asset_rank', 'Not enough information')} "
            f"({record.get('dynasty_asset_tier', 'Not enough information')}; "
            f"{record.get('main_risk', 'review-only')})"
        )
    if not parts:
        return ""
    return (
        "Dynasty asset watch: "
        + " | ".join(parts)
        + " Startup ADP is display-only and weak for this rookie/free-agent draft."
    )


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
