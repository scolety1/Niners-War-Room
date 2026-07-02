from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.development_lab_nflverse_context_service import (
    dataset_readiness_rows,
    deadline_status_context_rows,
    development_lab_context_status_rows,
    draft_capital_context_rows,
    identity_review_status_rows,
    manual_nwr_player_ids,
    player_context_artifact_status_rows,
    roster_status_context_rows,
    schedule_context_display_rows,
)
from src.services.development_lab_review_upgrade_service import (
    artifact_manifest_rows,
    candidate_review_panel_rows,
    current_stats_review_improvement_rows,
    dataset_browser_rows,
    guardrail_ledger_rows,
    lab_status_board_rows,
    next_lane_idea_rows,
)
from src.services.development_lab_state_service import (
    DevelopmentLabToolState,
    export_all_tool_states_json,
    export_tool_state_json,
    import_all_tool_states,
    import_tool_state,
    list_saved_tool_states,
    load_tool_state,
    preview_import_all_tool_states,
    preview_import_tool_state,
    reset_tool_state,
    save_tool_state,
)
from src.services.draft_day_runtime_state_service import load_runtime_state_with_status
from src.services.future_tools_rd_service import (
    FutureToolStatus,
    blocked_tools,
    deadline_checklist,
    development_lab_readiness_rows,
    future_pick_ledger_from_runtime_state,
    future_tool_gate_badge,
    future_tool_gate_badge_rows,
    future_tools_summary,
    load_future_tools_status_matrix,
    parse_manual_future_pick_text,
    parse_manual_roster_text,
    parse_manual_table_text,
    roster_age_bucket_summary,
    roster_dynasty_rank_bucket_summary,
    roster_position_summary,
    upcoming_draft_data_readiness_checklist,
    upcoming_draft_questions_checklist,
    upcoming_draft_setup_checklist,
)

LAB_WARNING = (
    "Development Lab tool. Safe V0 / display-only / manual workflow. Not model input. "
    "Not source truth."
)

ROADMAP_WARNING = (
    "Roadmap only. Not active. Requires future data, approval, or model gate."
)

UPCOMING_DRAFT_PREP_WARNING = (
    "Development Lab tool. Safe V0 / manual planning workflow. Not model input. "
    "Not source truth. Rookie/prospect context stays manual until approved gates clear."
)

TOOL_LABELS = {
    "roster_weakness_tracker": "Roster Weakness Tracker",
    "future_pick_planning": "Future Pick Planning",
    "upcoming_draft_prep": "Upcoming Draft Prep",
    "keeper_deadline_prep": "Keeper Deadline Prep",
    "drop_deadline_prep": "Drop Deadline Prep",
    "trade_deadline_prep": "Trade Deadline Prep",
}


def load_statuses() -> list[FutureToolStatus]:
    return load_future_tools_status_matrix()


def render_lab_warning() -> None:
    st.warning(LAB_WARNING)


def render_roadmap_warning() -> None:
    st.warning(ROADMAP_WARNING)


def render_tool_status_metrics(statuses: list[FutureToolStatus]) -> None:
    summary = future_tools_summary(statuses)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Tools tracked", summary["total_tools"])
    metric_cols[1].metric("Safe V0 tools", summary["safe_v0_candidates"])
    metric_cols[2].metric("Blocked / gated", summary["blocked"])
    metric_cols[3].metric("Model inputs", summary["model_inputs"])


def render_safe_v0_table(statuses: list[FutureToolStatus]) -> None:
    _tool_table(development_lab_readiness_rows(statuses))


def render_blocked_tools_table(statuses: list[FutureToolStatus]) -> None:
    _tool_table(
        [
            {
                "Tool": row.tool_name,
                "Status": row.decision,
                "Gate badge": future_tool_gate_badge(row),
                "Missing data display": "Not enough information",
                "Scaffold": row.scaffold_status,
                "Active output": row.active_output_allowed,
                "Model input": row.model_input_allowed,
            }
            for row in blocked_tools(statuses)
        ]
    )


def render_development_lab_readiness(statuses: list[FutureToolStatus]) -> None:
    state_by_tool = {
        state.tool_key: _local_state_status_label(state) for state in list_saved_tool_states()
    }
    _tool_table(development_lab_readiness_rows(statuses, local_state_by_tool=state_by_tool))
    st.caption(
        "Readiness is manual/display-only. NFLVerse context uses tracked display artifacts; "
        "missing or unapproved context stays Not enough information."
    )


def render_review_upgrade_status_board() -> None:
    st.caption(
        "Review cockpit for current tracked experiment evidence. Display-only/manual; "
        "no production formula, rank, source-truth, hidden-sort, model, or default app change."
    )
    _tool_table(lab_status_board_rows())


def render_review_upgrade_dataset_browser() -> None:
    st.caption(
        "Tracked artifact summaries only. Raw shared/cache/local exports are not loaded here."
    )
    _tool_table(dataset_browser_rows())
    with st.expander("Tracked artifact paths", expanded=False):
        _tool_table(artifact_manifest_rows())


def render_review_upgrade_candidate_panel() -> None:
    st.caption(
        "Candidate evidence remains on HOLD for human review. Variants are labels for "
        "review packets only and are not wired into normal product behavior."
    )
    _tool_table(candidate_review_panel_rows())


def render_review_upgrade_guardrail_ledger() -> None:
    _tool_table(guardrail_ledger_rows())


def render_review_upgrade_current_stats_options() -> None:
    st.caption("These are safe review-only summaries that current tracked stats can support.")
    _tool_table(current_stats_review_improvement_rows())


def render_review_upgrade_next_lane_ideas() -> None:
    st.caption("Ideas only. Nothing here starts an action or promotes evidence.")
    _tool_table(next_lane_idea_rows())


def render_refresh_health_waiting_panel() -> None:
    st.info(
        "NFLVerse refresh health and player context are available as tracked "
        "display-only artifacts. Development Lab pages consume only those repo artifacts, "
        "not raw shared/cache files."
    )
    st.caption("Player-context artifact status")
    _tool_table(player_context_artifact_status_rows())
    st.caption("Development Lab context status")
    _tool_table(development_lab_context_status_rows())
    st.caption("Dataset readiness / source policy")
    _tool_table(dataset_readiness_rows())
    st.caption("Schedule context / display-only")
    _tool_table(schedule_context_display_rows(limit=10))


def render_future_tool_gate_badges(statuses: list[FutureToolStatus]) -> None:
    _tool_table(future_tool_gate_badge_rows(statuses))
    st.caption(
        "Active output and model input flags remain no. Safe manual siblings are separate "
        "Development Lab pages; all other rows are inactive roadmap ideas."
    )


def render_lab_links() -> None:
    link_cols = st.columns(3)
    links = (
        ("Roster Weakness Tracker", "/roster-weakness-tracker"),
        ("Future Pick Planning", "/future-pick-planning"),
        ("Upcoming Draft Prep", "/upcoming-draft-prep"),
        ("Keeper Deadline Prep", "/keeper-deadline-prep"),
        ("Drop Deadline Prep", "/drop-deadline-prep"),
        ("Trade Deadline Prep", "/trade-deadline-prep"),
        ("Future Tools ideas", "/future-tools"),
    )
    for index, (label, path) in enumerate(links):
        with link_cols[index % 3]:
            st.link_button(label, path, use_container_width=True)


def render_local_lab_state_status() -> None:
    rows: list[dict[str, str]] = []
    for state in list_saved_tool_states():
        rows.append(
            {
                "Tool": TOOL_LABELS.get(state.tool_key, state.tool_key),
                "Saved state": _local_state_status_label(state),
                "Last updated": state.saved_at_utc or "Not saved",
                "Path": str(state.path),
                "Guardrail": "Local lab notes only; not model input or source truth.",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Saved Development Lab notes use the configured local manual-state root and are not "
        "tracked by git. Export JSON before major review sessions if you want a portable copy."
    )


def render_bulk_lab_state_controls() -> None:
    st.caption(
        "Bulk package covers all six local/manual Development Lab note files. It does not "
        "include auto-filled context, source truth, model input, ranks, or draft runtime state."
    )
    st.download_button(
        "Export all local lab notes JSON",
        data=export_all_tool_states_json(),
        file_name="nwr_development_lab_all_manual_state.json",
        mime="application/json",
        key="development_lab_bulk_export_state",
        use_container_width=True,
    )
    with st.expander("Import all local lab notes", expanded=False):
        uploaded = st.file_uploader(
            "Import Development Lab bulk state JSON",
            type=["json"],
            key="development_lab_bulk_import_file",
            help="Preview first; import is blocked until explicitly confirmed.",
        )
        if uploaded is None:
            st.caption(
                "Waiting for a JSON package. Missing package data is Not enough information."
            )
            return
        raw = uploaded.getvalue()
        preview = preview_import_all_tool_states(raw)
        if not preview.valid:
            st.warning(preview.message)
            return
        st.write(
            {
                "exported_at_utc": preview.exported_at_utc or "Not provided",
                "tools": list(preview.tool_keys),
                "fields": {
                    tool_key: sorted(payload.keys())
                    for tool_key, payload in preview.payloads.items()
                },
            }
        )
        confirm_import = st.checkbox(
            "Confirm import overwrite for all local lab notes",
            key="development_lab_bulk_confirm_import",
        )
        if st.button(
            "Import confirmed local lab notes package",
            key="development_lab_bulk_import_confirmed",
        ):
            result = import_all_tool_states(raw, confirmed=confirm_import)
            if result.status == "SAVED":
                st.success(
                    "Imported all local Development Lab manual notes. "
                    f"Backups created: {len(result.backup_paths)}."
                )
                st.rerun()
            else:
                st.warning(result.message)


def render_roster_weakness_tracker() -> None:
    render_lab_warning()
    st.caption(
        "Display-only roster structure. Not model input. Local lab notes can be saved "
        "and reloaded."
    )
    fields = {"manual_roster_rows": "development_lab_roster_weakness_tracker_rows"}
    _hydrate_local_lab_state("roster_weakness_tracker", fields)
    roster_text = st.text_area(
        "Manual roster rows",
        placeholder="Player, Position, Age, Dynasty Rank, Notes, NWR Player ID",
        key="development_lab_roster_weakness_tracker_rows",
        help=(
            "Optional manual input. Save local lab state to preserve it across reloads. "
            "Add NWR Player ID to join display-only NFLVerse context. Missing values stay "
            "Not enough information."
        ),
    )
    rows = parse_manual_roster_text(roster_text)
    if not rows:
        _render_roster_status_context(())
        st.info(
            "Enter manual roster rows to generate display-only counts. "
            "Only manual/display-only summaries are shown."
        )
        _render_lab_state_controls("roster_weakness_tracker", fields)
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    _render_roster_status_context(manual_nwr_player_ids(rows))
    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("Position coverage versus simple starter-count thresholds")
        st.dataframe(pd.DataFrame(roster_position_summary(rows)), use_container_width=True)
        st.caption("Age buckets")
        st.dataframe(pd.DataFrame(roster_age_bucket_summary(rows)), use_container_width=True)
    with col_b:
        st.caption("Dynasty Rank buckets, if manually provided")
        st.dataframe(
            pd.DataFrame(roster_dynasty_rank_bucket_summary(rows)),
            use_container_width=True,
        )
        csv_download(
            "Download roster structure CSV",
            rows,
            "nwr_roster_weakness_tracker_v0_display_only.csv",
        )
    _render_lab_state_controls("roster_weakness_tracker", fields)


def render_future_pick_planning() -> None:
    render_lab_warning()
    st.caption(
        "Planning ledger only. Pick and trade context stays descriptive/manual. "
        "Local manual notes can be saved and reloaded."
    )
    _render_draft_capital_context()
    fields = {"manual_future_pick_notes": "development_lab_future_pick_planning_rows"}
    _hydrate_local_lab_state("future_pick_planning", fields)
    live_state_result = load_runtime_state_with_status(mode="live")
    runtime_rows = future_pick_ledger_from_runtime_state(live_state_result.state)
    st.caption(
        f"Live runtime state status: {live_state_result.status}. Runtime events are manual/local "
        "and not official source truth."
    )
    if runtime_rows:
        st.dataframe(pd.DataFrame(runtime_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No future picks found in the live runtime trade event log.")
    manual_text = st.text_area(
        "Manual future pick notes",
        placeholder="2028, 1st, acquired, WhoDat, confirm against Sleeper later",
        key="development_lab_future_pick_planning_rows",
        help="Optional manual notes. Save local lab state to preserve them across reloads.",
    )
    manual_rows = parse_manual_future_pick_text(manual_text)
    if manual_rows:
        st.dataframe(pd.DataFrame(manual_rows), use_container_width=True, hide_index=True)
    csv_download(
        "Download future pick planning CSV",
        [*runtime_rows, *manual_rows],
        "nwr_future_pick_planning_v0_display_only.csv",
    )
    _render_lab_state_controls("future_pick_planning", fields)


def render_upcoming_draft_prep() -> None:
    st.warning(UPCOMING_DRAFT_PREP_WARNING)
    st.info(
        "Local lab notes only. Save to preserve manual inputs across reloads. "
        "This is not model input, source truth, or draft-room runtime state."
    )
    _render_draft_capital_context()
    fields = {
        "setup_notes": "development_lab_upcoming_draft_setup_notes",
        "roster_need_rows": "development_lab_upcoming_roster_needs",
        "pick_inventory_rows": "development_lab_upcoming_pick_inventory",
        "watchlist_rows": "development_lab_upcoming_watchlist",
        "scenario_rows": "development_lab_upcoming_mock_scenarios",
        "question_notes": "development_lab_upcoming_question_notes",
        "readiness_notes": "development_lab_upcoming_readiness_notes",
    }
    _hydrate_local_lab_state("upcoming_draft_prep", fields)

    st.subheader("Draft Setup Checklist")
    setup_notes = st.text_area(
        "Draft setup notes",
        key="development_lab_upcoming_draft_setup_notes",
        help="Optional manual note. Save local lab state to preserve it across reloads.",
    )
    setup_rows = upcoming_draft_setup_checklist(notes=setup_notes)
    st.dataframe(pd.DataFrame(setup_rows), use_container_width=True, hide_index=True)
    csv_download(
        "Download draft setup checklist CSV",
        setup_rows,
        "nwr_draft_setup_checklist_v0.csv",
    )

    st.subheader("Roster Needs Snapshot")
    st.caption("Manual/display-only planning area. No position target plan is generated.")
    roster_need_text = st.text_area(
        "Roster need rows",
        placeholder="Position, short-term need, long-term need, depth concern notes, watch notes",
        key="development_lab_upcoming_roster_needs",
    )
    roster_need_rows = parse_manual_table_text(
        roster_need_text,
        (
            "position",
            "short_term_need",
            "long_term_need",
            "depth_concern_notes",
            "watch_notes",
        ),
        source="Manual input / display-only",
        guardrail="Planning notes only; no position target plan.",
    )
    _render_optional_manual_table(roster_need_rows, "No roster need notes entered.")
    csv_download(
        "Download roster needs CSV",
        roster_need_rows,
        "nwr_upcoming_draft_roster_needs_v0.csv",
    )

    st.subheader("Pick Inventory / Asset Prep")
    st.caption(
        "Planning ledger only. Pick context stays descriptive; no class-strength labels "
        "or trade calculator."
    )
    live_state_result = load_runtime_state_with_status(mode="live")
    runtime_rows = future_pick_ledger_from_runtime_state(live_state_result.state)
    st.caption(
        f"Live runtime state status: {live_state_result.status}. Future picks from the event log "
        "are manual/local context only."
    )
    _render_optional_manual_table(
        runtime_rows,
        "No future picks found in the live runtime event log.",
    )
    pick_text = st.text_area(
        "Manual pick inventory rows",
        placeholder="Year, round/pick, owned/sent/acquired/uncertain, source/note, action needed",
        key="development_lab_upcoming_pick_inventory",
    )
    pick_rows = parse_manual_table_text(
        pick_text,
        ("year", "round_pick", "status", "source_note", "action_needed"),
        source="Manual input / display-only",
        guardrail="Planning ledger only; no pick/trade math.",
    )
    _render_optional_manual_table(pick_rows, "No manual pick inventory rows entered.")
    csv_download(
        "Download pick inventory CSV",
        [*runtime_rows, *pick_rows],
        "nwr_upcoming_draft_pick_inventory_v0.csv",
    )

    st.subheader("Rookie / Prospect Watchlist Placeholder")
    st.caption(
        "Manual watchlist only. CFBD/prospect data remains review-only unless separately approved."
    )
    watchlist_text = st.text_area(
        "Manual rookie/prospect watchlist rows",
        placeholder="Player name, school/team, position, note, source note, review status",
        key="development_lab_upcoming_watchlist",
    )
    watchlist_rows = parse_manual_table_text(
        watchlist_text,
        ("player_name", "school_team", "position", "note", "source_note", "review_status"),
        source="Manual input / display-only",
        guardrail="Manual watchlist only; no CFBD promotion, rank change, or model output.",
    )
    _render_optional_manual_table(watchlist_rows, "No manual watchlist rows entered.")
    csv_download(
        "Download rookie watchlist CSV",
        watchlist_rows,
        "nwr_upcoming_draft_manual_watchlist_v0.csv",
    )

    st.subheader("Mock Draft Scenario Prep")
    st.caption("Manual scenario notes only. Use Mock Drafts for experiments.")
    st.link_button("Open Mock Drafts", "/mock-draft", use_container_width=False)
    scenario_text = st.text_area(
        "Manual mock draft scenario rows",
        placeholder=(
            "Scenario name, what happens before my pick, trade-down scenario, "
            "position run scenario, if player X is gone"
        ),
        key="development_lab_upcoming_mock_scenarios",
    )
    scenario_rows = parse_manual_table_text(
        scenario_text,
        (
            "scenario_name",
            "before_my_pick",
            "trade_down_scenario",
            "position_run_scenario",
            "if_player_x_is_gone",
        ),
        source="Manual input / display-only",
        guardrail="Scenario prep only; no automated mock simulation or active output.",
    )
    _render_optional_manual_table(scenario_rows, "No manual mock draft scenarios entered.")
    csv_download(
        "Download mock scenario CSV",
        scenario_rows,
        "nwr_upcoming_draft_mock_scenarios_v0.csv",
    )

    st.subheader("Questions to Answer Before Draft")
    question_notes = st.text_area(
        "Open question notes",
        key="development_lab_upcoming_question_notes",
    )
    question_rows = upcoming_draft_questions_checklist(notes=question_notes)
    st.dataframe(pd.DataFrame(question_rows), use_container_width=True, hide_index=True)
    csv_download(
        "Download draft questions CSV",
        question_rows,
        "nwr_upcoming_draft_questions_v0.csv",
    )

    st.subheader("Data Readiness Checklist")
    st.caption("Manual/status checklist only. This is not a refresh button or data promotion tool.")
    readiness_notes = st.text_area(
        "Data readiness notes",
        key="development_lab_upcoming_readiness_notes",
    )
    readiness_rows = upcoming_draft_data_readiness_checklist(notes=readiness_notes)
    st.dataframe(pd.DataFrame(readiness_rows), use_container_width=True, hide_index=True)
    csv_download(
        "Download data readiness CSV",
        readiness_rows,
        "nwr_upcoming_draft_data_readiness_v0.csv",
    )
    _render_lab_state_controls("upcoming_draft_prep", fields)


def render_deadline_prep(tool_id: str, title: str) -> None:
    render_lab_warning()
    st.caption(
        "Manual checklist only. Not a decision engine. Not model input. "
        "Local lab notes can be saved and reloaded."
    )
    _render_deadline_status_context()
    fields = {
        "manual_deadline_date": f"development_lab_{tool_id}_date",
        "manual_notes": f"development_lab_{tool_id}_notes",
    }
    _hydrate_local_lab_state(tool_id, fields)
    date_text = st.text_input(
        f"{title} manual deadline date",
        placeholder="YYYY-MM-DD or league note",
        key=f"development_lab_{tool_id}_date",
    )
    notes = st.text_area(
        f"{title} manual notes",
        key=f"development_lab_{tool_id}_notes",
        help="Optional manual note. Save local lab state to preserve it across reloads.",
    )
    rows = deadline_checklist(tool_id, date_text=date_text, notes=notes)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    csv_download(
        f"Download {title} checklist CSV",
        rows,
        f"nwr_{tool_id}_v0_manual_checklist.csv",
    )
    _render_lab_state_controls(tool_id, fields)


def render_guardrails() -> None:
    st.caption(
        "All active-output and model-input flags in the status matrix are no. Blocked future "
        "tool ideas stay inactive until HQ approves the required gates."
    )
    st.caption(
        "Development Lab pages do not promote CFBD, NFL usage, Gmail, vendor, proxy, "
        "Outcome, DynastyProcess, ADP, or market data to model input."
    )
    st.caption(
        "No rank, tier, Dynasty Rank, Final Board Rank, pinned snapshot, latest candidate, "
        "latest approved, source-truth, or model logic is changed by these pages."
    )


def csv_download(label: str, rows: list[dict[str, str]], filename: str) -> None:
    if not rows:
        return
    data = pd.DataFrame(rows).to_csv(index=False)
    st.download_button(label, data=data, file_name=filename, mime="text/csv")


def _tool_table(rows: list[dict[str, str]]) -> None:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_optional_manual_table(rows: list[dict[str, str]], empty_message: str) -> None:
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


def _render_roster_status_context(player_ids: tuple[str, ...]) -> None:
    st.subheader("NFLVerse Player Context")
    st.caption(
        "Tracked artifact context only. Joins use NWR Player ID; rows needing identity "
        "review do not show player-context details."
    )
    _tool_table(roster_status_context_rows(player_ids=player_ids))
    _render_schedule_context(player_ids)
    _render_identity_review_status()


def _render_draft_capital_context() -> None:
    st.subheader("NFLVerse Draft Capital Context")
    st.caption(
        "Factual NFL draft labels from the tracked display artifact only. Fantasy pick "
        "ownership remains manual/runtime context."
    )
    rows = draft_capital_context_rows()
    if rows:
        _tool_table(rows)
    else:
        st.info("NFL draft capital context is Not enough information.")
    _render_schedule_context(())
    _render_identity_review_status()


def _render_deadline_status_context() -> None:
    st.subheader("NFLVerse Roster / Status Context")
    st.caption(
        "Display-only roster/status labels for manual checklist support. Missing context "
        "does not imply health, role, safety, or priority."
    )
    _tool_table(deadline_status_context_rows())
    _render_schedule_context(())
    _render_identity_review_status()


def _render_schedule_context(player_ids: tuple[str, ...]) -> None:
    st.caption("Schedule context / display-only")
    _tool_table(schedule_context_display_rows(player_ids=player_ids, limit=10))


def _render_identity_review_status() -> None:
    with st.expander("Identity review rows", expanded=False):
        st.caption(
            "Rows needing identity review show status only. Proposed identity matches are "
            "not approved joins."
        )
        _tool_table(identity_review_status_rows(limit=10))


def _hydrate_local_lab_state(tool_key: str, fields: dict[str, str]) -> None:
    state = load_tool_state(tool_key)
    if state.status == "LOADED":
        for payload_key, widget_key in fields.items():
            if widget_key not in st.session_state and payload_key in state.payload:
                st.session_state[widget_key] = state.payload[payload_key]
        st.caption(f"Local lab state loaded. Last updated: {state.saved_at_utc}.")
    elif state.status == "MISSING":
        st.caption("Local lab state: no saved notes yet.")
    else:
        st.warning(state.message)


def _render_lab_state_controls(tool_key: str, fields: dict[str, str]) -> None:
    st.divider()
    st.subheader("Local Lab State")
    st.caption(
        "Local lab notes only. Not model input. Not source truth. Not draft-room runtime state."
    )
    payload = _payload_from_session(fields)
    col_save, col_export = st.columns(2)
    if col_save.button(
        "Save local lab state",
        key=f"development_lab_{tool_key}_save_state",
        use_container_width=True,
    ):
        result = save_tool_state(tool_key, payload)
        if result.backup_path:
            st.success(f"Saved. Previous state backed up to {result.backup_path.name}.")
        else:
            st.success("Saved local lab state.")
    col_export.download_button(
        "Export state JSON",
        data=export_tool_state_json(tool_key, payload),
        file_name=f"nwr_development_lab_{tool_key}_state.json",
        mime="application/json",
        key=f"development_lab_{tool_key}_export_state",
        use_container_width=True,
    )

    with st.expander("Import / reset local lab state", expanded=False):
        uploaded = st.file_uploader(
            "Import Development Lab state JSON",
            type=["json"],
            key=f"development_lab_{tool_key}_import_file",
            help="Preview first; import is blocked until explicitly confirmed.",
        )
        if uploaded is not None:
            raw = uploaded.getvalue()
            preview = preview_import_tool_state(raw)
            if preview.valid:
                st.write(
                    {
                        "tool_key": preview.tool_key,
                        "saved_at_utc": preview.saved_at_utc or "Not provided",
                        "fields": sorted((preview.payload or {}).keys()),
                    }
                )
                confirm_import = st.checkbox(
                    "Confirm import overwrite",
                    key=f"development_lab_{tool_key}_confirm_import",
                )
                if st.button(
                    "Import confirmed state",
                    key=f"development_lab_{tool_key}_import_confirmed",
                ):
                    result = import_tool_state(
                        tool_key,
                        raw,
                        confirmed=confirm_import,
                    )
                    if result.status == "SAVED" and preview.payload:
                        for payload_key, widget_key in fields.items():
                            st.session_state[widget_key] = preview.payload.get(payload_key, "")
                        st.success("Imported local lab state.")
                        st.rerun()
                    else:
                        st.warning(result.message)
            else:
                st.warning(preview.message)

        confirm_reset = st.checkbox(
            "Confirm reset saved local state",
            key=f"development_lab_{tool_key}_confirm_reset",
        )
        if st.button(
            "Reset saved local state",
            key=f"development_lab_{tool_key}_reset_state",
        ):
            result = reset_tool_state(tool_key, confirmed=confirm_reset)
            if result.status == "RESET":
                for widget_key in fields.values():
                    st.session_state[widget_key] = ""
                if result.backup_path:
                    st.success(f"Reset complete. Backup created: {result.backup_path.name}.")
                else:
                    st.success("Reset complete. No prior saved state existed.")
                st.rerun()
            else:
                st.warning(result.message)


def _payload_from_session(fields: dict[str, str]) -> dict[str, str]:
    return {
        payload_key: str(st.session_state.get(widget_key, "") or "")
        for payload_key, widget_key in fields.items()
    }


def _local_state_status_label(state: DevelopmentLabToolState) -> str:
    if state.status == "LOADED":
        return "Saved locally"
    if state.status == "MISSING":
        return "No saved notes"
    return state.status.replace("_", " ").title()
