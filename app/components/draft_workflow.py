from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.services.draft_day_runtime_state_service import (
    apply_trade_events_to_pick_frame,
    create_runtime_backup,
    event_rows,
    export_runtime_state,
    export_runtime_state_json,
    load_latest_runtime_state,
    load_runtime_state,
    record_trade_event,
    reset_runtime_state_if_confirmed,
    restore_runtime_state_from_json,
    runtime_paths,
    save_runtime_state,
    update_workflow_state,
)
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
    player_key_from_row,
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
    runtime_mode = _runtime_mode_from_session_key(session_key)
    runtime_state_key = f"{session_key}_runtime_state"
    if runtime_state_key not in st.session_state:
        st.session_state[runtime_state_key] = load_runtime_state(
            mode=runtime_mode,
            source_checkpoint=source_caption,
        )
    if session_key not in st.session_state:
        st.session_state[session_key] = st.session_state[runtime_state_key].get(
            "workflow_state",
            empty_workflow_state(),
        )
    st.session_state[session_key] = copy_state(st.session_state[session_key])
    st.session_state[runtime_state_key]["workflow_state"] = st.session_state[session_key]
    state = st.session_state[session_key]
    effective_pick_frame = apply_trade_events_to_pick_frame(
        pick_frame,
        st.session_state[runtime_state_key],
    )

    summary = workflow_summary(board_frame, effective_pick_frame, state)
    current_owner = f" - {summary.current_pick_owner}" if summary.current_pick_owner else ""
    frozen_rows = _non_pdf_row_count(board_frame)
    pdf_rows = _pdf_row_count(board_frame)
    st.caption(
        " | ".join(
            (
                "Source: Frozen Baseline + verified PDF free-agent overlay",
                f"Frozen rows: {frozen_rows}",
                f"PDF FAs: {pdf_rows}",
                f"Draftable rows: {len(board_frame)}",
                f"Drafted: {summary.drafted_count}",
                f"Available: {summary.available_count}",
                f"Current pick: {summary.current_pick_label}{current_owner}",
            )
        )
    )

    current_pick = current_pick_number(effective_pick_frame, state)
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
        pick_frame=effective_pick_frame,
        current_pick=current_pick,
        session_key=session_key,
        runtime_state_key=runtime_state_key,
    )

    _render_trade_events(
        pick_frame=effective_pick_frame,
        session_key=session_key,
        runtime_state_key=runtime_state_key,
    )

    st.subheader("Draft Board")
    board_rows = draft_board_frame(
        effective_pick_frame,
        nwr_picks_frame,
        st.session_state[session_key],
    )
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

    _render_runtime_state_controls(
        session_key=session_key,
        runtime_state_key=runtime_state_key,
        source_caption=source_caption,
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
                "Frozen Baseline Rank",
                "ADP / Price Context",
            ],
            key=f"{session_key}_view_sort_mode",
        )
        sort_default = {
            "Dynasty Asset Tiers": "Dynasty Asset Tier/Rank",
            "Candidate Best Available": "Candidate Rank",
            "Frozen Baseline Rank": "Final Board Rank",
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
    runtime_state_key: str,
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
            next_state = assign_player_to_pick(
                st.session_state[session_key],
                board=board_frame,
                pick_frame=pick_frame,
                player_key=player_options[player_label],
                overall_pick=pick_options[pick_label],
            )
            player_row = _row_for_player_key(board_frame, player_options[player_label])
            pick_row = _row_for_pick(pick_frame, pick_options[pick_label])
            assigned_player = (
                player_row.get("player", player_label) if player_row else player_label
            )
            assigned_pick = pick_row.get("pick_label", pick_label) if pick_row else pick_label
            runtime_state = update_workflow_state(
                st.session_state[runtime_state_key],
                next_state,
                event_type="pick_assigned",
                event_detail={
                    "player": assigned_player,
                    "player_id": player_options[player_label],
                    "position": player_row.get("position", "") if player_row else "",
                    "pick_label": assigned_pick,
                    "overall_pick": pick_options[pick_label],
                    "pick_owner": pick_row.get("current_owner", "") if pick_row else "",
                    "selecting_team": pick_row.get("current_owner", "") if pick_row else "",
                },
            )
            st.session_state[runtime_state_key] = runtime_state
            st.session_state[session_key] = runtime_state["workflow_state"]
            st.session_state[f"{session_key}_sync_pick_to_current"] = True
            st.success(f"Assigned {player_label} to {pick_label}.")
            st.rerun()
        except DraftWorkflowError as exc:
            st.error(str(exc))
    if cols[3].button("Undo Last", key=f"{session_key}_undo", use_container_width=True):
        next_state, message = undo_last_pick(st.session_state[session_key])
        runtime_state = update_workflow_state(
            st.session_state[runtime_state_key],
            next_state,
            event_type="pick_undone",
            event_detail={"message": message},
        )
        st.session_state[runtime_state_key] = runtime_state
        st.session_state[session_key] = runtime_state["workflow_state"]
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
        next_state, message = remove_pick_assignment(
            st.session_state[session_key],
            pick_options[remove_pick_label],
        )
        runtime_state = update_workflow_state(
            st.session_state[runtime_state_key],
            next_state,
            event_type="pick_removed",
            event_detail={
                "pick_label": remove_pick_label,
                "overall_pick": pick_options[remove_pick_label],
                "message": message,
            },
        )
        st.session_state[runtime_state_key] = runtime_state
        st.session_state[session_key] = runtime_state["workflow_state"]
        st.session_state[f"{session_key}_sync_pick_to_current"] = True
        st.info(message)
        st.rerun()


def _render_trade_events(
    *,
    pick_frame: pd.DataFrame,
    session_key: str,
    runtime_state_key: str,
) -> None:
    with st.expander("Record Trade", expanded=False):
        st.caption(
            "Record pick-ownership events during the draft. This updates local runtime board "
            "context only; no trade calculator, model value, rank, or source truth is changed."
        )
        cols = st.columns(2)
        team_a = cols[0].text_input(
            "Team A",
            key=f"{session_key}_trade_team_a",
            value="NWR",
            placeholder="Team A",
        )
        team_b = cols[1].text_input(
            "Team B",
            key=f"{session_key}_trade_team_b",
            placeholder="Team B",
        )
        asset_cols = st.columns(2)
        team_a_sends = asset_cols[0].text_area(
            "Team A sends",
            key=f"{session_key}_trade_team_a_sends",
            placeholder="Example: 2026 1.04",
        )
        team_b_sends = asset_cols[1].text_area(
            "Team B sends",
            key=f"{session_key}_trade_team_b_sends",
            placeholder="Example: 2026 2.03, 2028 1st",
        )
        notes = st.text_area(
            "Notes",
            key=f"{session_key}_trade_notes",
            placeholder="Optional context. No final trade advice.",
        )
        if st.button("Record trade", key=f"{session_key}_record_trade"):
            st.session_state[runtime_state_key] = record_trade_event(
                st.session_state[runtime_state_key],
                team_a=team_a,
                team_b=team_b,
                team_a_sends=team_a_sends,
                team_b_sends=team_b_sends,
                notes=notes,
            )
            st.success("Trade event recorded in local draft runtime state.")
            st.rerun()

        trades = st.session_state[runtime_state_key].get("trade_events", [])
        if trades:
            st.dataframe(
                pd.DataFrame(trades).astype(str),
                use_container_width=True,
                hide_index=True,
                key=f"{session_key}_trade_events",
            )
        else:
            st.caption("No trade events recorded yet.")

        if not pick_frame.empty:
            st.caption("Current pick ownership after local trade events:")
            st.dataframe(
                pick_frame.astype(str).head(30),
                use_container_width=True,
                hide_index=True,
                key=f"{session_key}_trade_adjusted_picks",
            )


def _render_runtime_state_controls(
    *,
    session_key: str,
    runtime_state_key: str,
    source_caption: str,
) -> None:
    with st.expander("Runtime draft state / export / reset", expanded=False):
        paths = runtime_paths()
        st.caption(
            f"Autosave path: {paths.state_dir}. Runtime files are local-only under "
            "C:\\NWR_SHARED_DATA and must not be committed."
        )
        state_cols = st.columns(3)
        if state_cols[0].button("Save draft state", key=f"{session_key}_manual_save"):
            st.session_state[runtime_state_key] = save_runtime_state(
                st.session_state[runtime_state_key],
                event_type="manual_save",
                event_detail={"source": "manual_button"},
            )
            st.success("Draft state saved.")
        if state_cols[1].button("Load latest draft state", key=f"{session_key}_load_latest"):
            latest = load_latest_runtime_state(
                mode=str(st.session_state[runtime_state_key].get("mode") or "live"),
                draft_id=str(
                    st.session_state[runtime_state_key].get("draft_session_id")
                    or st.session_state[runtime_state_key].get("draft_id")
                    or "draft_day_v2"
                ),
                source_checkpoint=source_caption,
            )
            st.session_state[runtime_state_key] = save_runtime_state(
                latest,
                event_type="state_loaded",
                event_detail={"source": "latest_runtime_state"},
            )
            st.session_state[session_key] = st.session_state[runtime_state_key][
                "workflow_state"
            ]
            st.success("Latest draft state loaded.")
            st.rerun()
        if state_cols[2].button("Create backup", key=f"{session_key}_create_backup"):
            backup_path = create_runtime_backup(
                st.session_state[runtime_state_key],
                reason="manual_button",
            )
            st.session_state[runtime_state_key] = save_runtime_state(
                st.session_state[runtime_state_key],
                event_type="backup_created",
                event_detail={"path": str(backup_path)},
                create_backup=False,
            )
            st.success(f"Backup created: {backup_path}")

        export_cols = st.columns(2)
        if export_cols[0].button("Export JSON", key=f"{session_key}_export_json"):
            exports = export_runtime_state(st.session_state[runtime_state_key])
            st.session_state[runtime_state_key] = save_runtime_state(
                st.session_state[runtime_state_key],
                event_type="export_created",
                event_detail={label: str(path) for label, path in exports.items()},
            )
            st.success("Exported: " + " | ".join(str(path) for path in exports.values()))
        export_cols[1].download_button(
            "Download JSON",
            data=export_runtime_state_json(st.session_state[runtime_state_key]),
            file_name=f"{session_key}_draft_state.json",
            mime="application/json",
            key=f"{session_key}_download_json",
        )

        uploaded = st.file_uploader(
            "Import JSON",
            type=["json"],
            key=f"{session_key}_import_json",
            help="Restore a previously exported draft state JSON file.",
        )
        if uploaded is not None and st.button(
            "Restore imported JSON",
            key=f"{session_key}_restore_imported_json",
        ):
            try:
                st.session_state[runtime_state_key] = restore_runtime_state_from_json(
                    uploaded.getvalue(),
                    mode=str(st.session_state[runtime_state_key].get("mode") or "live"),
                    draft_id=str(
                        st.session_state[runtime_state_key].get("draft_session_id")
                        or st.session_state[runtime_state_key].get("draft_id")
                        or "draft_day_v2"
                    ),
                )
                st.session_state[session_key] = st.session_state[runtime_state_key][
                    "workflow_state"
                ]
                st.success("Imported draft state restored.")
                st.rerun()
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                st.error(f"Could not import draft JSON: {exc}")

        reset_col, status_col = st.columns([1, 2])
        confirm = reset_col.checkbox(
            "Confirm reset draft state",
            key=f"{session_key}_confirm_reset",
            help="Required before clearing local runtime picks/trades for this mode.",
        )
        if reset_col.button("Reset draft state", key=f"{session_key}_reset_state"):
            if not confirm:
                st.warning("Check Confirm reset before clearing local runtime state.")
            else:
                st.session_state[runtime_state_key] = reset_runtime_state_if_confirmed(
                    st.session_state[runtime_state_key],
                    confirmed=True,
                    reason=f"User reset from {source_caption[:160]}",
                )
                st.session_state[session_key] = st.session_state[runtime_state_key][
                    "workflow_state"
                ]
                st.success("Local runtime state reset.")
                st.rerun()
        status_col.caption(f"State path: {paths.state_dir}")
        status_col.caption(f"Backup path: {paths.backup_dir}")

    with st.expander("Event log", expanded=False):
        events = event_rows(st.session_state[runtime_state_key])
        st.caption(f"Events recorded: {len(events)}")
        if events:
            st.dataframe(
                pd.DataFrame(events),
                use_container_width=True,
                hide_index=True,
                key=f"{session_key}_runtime_events",
            )
        else:
            st.caption("No draft events recorded yet.")


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


def _runtime_mode_from_session_key(session_key: str) -> str:
    if "mock" in session_key:
        return "mock"
    if "live" in session_key:
        return "live"
    return session_key


def _row_for_player_key(frame: pd.DataFrame, player_key: str) -> dict[str, object] | None:
    for _index, row in frame.iterrows():
        if player_key_from_row(row) == player_key:
            return row.to_dict()
    return None


def _row_for_pick(frame: pd.DataFrame, overall_pick: int) -> dict[str, object] | None:
    if "overall_pick" not in frame.columns:
        return None
    matches = frame.loc[pd.to_numeric(frame["overall_pick"], errors="coerce") == overall_pick]
    if matches.empty:
        return None
    return matches.iloc[0].to_dict()
