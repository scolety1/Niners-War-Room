from __future__ import annotations

import json

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
    usage_stability_lens_good_parts_rows,
    usage_stability_lens_parking_rows,
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
from src.services.display_only_ngs_context_service import (
    REVIEW_ONLY_WARNING,
    blocked_ngs_metric_rows,
    development_lab_ngs_rows,
)
from src.services.draft_day_runtime_state_service import load_runtime_state_with_status
from src.services.future_tools_rd_service import (
    FutureToolStatus,
    append_manual_csv_row,
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
from src.utils.spreadsheet_safe import spreadsheet_safe_rows

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
    "roster_weakness_tracker": "Roster Planner",
    "future_pick_planning": "Future Pick Planner",
    "upcoming_draft_prep": "Upcoming Draft Prep",
    "keeper_deadline_prep": "Keeper Deadline Prep",
    "drop_deadline_prep": "Drop Deadline Prep",
    "trade_deadline_prep": "Trade Deadline Prep",
}


def load_statuses() -> list[FutureToolStatus]:
    return load_future_tools_status_matrix()


def render_lab_warning() -> None:
    st.warning(LAB_WARNING)


def render_planner_note() -> None:
    st.caption(
        "This workspace saves only your local planning notes. It never changes NWR "
        "rankings, projections, or league data."
    )


def _guided_manual_entry(
    *,
    storage_key: str,
    form_key: str,
    fields: tuple[tuple[str, str, str, tuple[str, ...]], ...],
    required_field: str,
    paste_label: str,
    paste_help: str,
) -> str:
    """Render an approachable one-row form while retaining bulk-paste compatibility."""

    values: dict[str, str] = {}
    with st.form(form_key, clear_on_submit=True):
        columns = st.columns(min(len(fields), 3))
        for index, (field_key, label, placeholder, options) in enumerate(fields):
            container = columns[index % len(columns)]
            if options:
                values[field_key] = container.selectbox(
                    label,
                    options,
                    key=f"{form_key}_{field_key}",
                )
            else:
                values[field_key] = container.text_input(
                    label,
                    placeholder=placeholder,
                    key=f"{form_key}_{field_key}",
                )
        submitted = st.form_submit_button("Add to plan", type="primary")
    if submitted:
        if not values.get(required_field, "").strip():
            st.warning(f"Enter {required_field.replace('_', ' ')} before adding this row.")
        else:
            current = str(st.session_state.get(storage_key, "") or "")
            ordered = tuple(values[field_key] for field_key, *_rest in fields)
            st.session_state[storage_key] = append_manual_csv_row(current, ordered)
            st.rerun()

    with st.expander("Paste or edit several rows", expanded=False):
        return st.text_area(
            paste_label,
            key=storage_key,
            help=paste_help,
        )


def _owner_table(
    rows: list[dict[str, object]],
    columns: tuple[tuple[str, str], ...],
) -> None:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return
    selected = [source for source, _label in columns if source in frame.columns]
    labels = {source: label for source, label in columns}
    st.dataframe(
        frame[selected].rename(columns=labels),
        width="stretch",
        hide_index=True,
    )


def _interactive_checklist(
    rows: list[dict[str, str]],
    *,
    task_column: str,
    storage_key: str,
    widget_prefix: str,
) -> list[dict[str, str]]:
    try:
        completed = set(json.loads(str(st.session_state.get(storage_key, "[]") or "[]")))
    except (TypeError, ValueError, json.JSONDecodeError):
        completed = set()
    updated: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        task = str(row.get(task_column, ""))
        is_done = st.checkbox(
            task,
            value=task in completed,
            key=f"{widget_prefix}_{index}",
        )
        next_row = dict(row)
        next_row["status"] = "Done" if is_done else "To do"
        updated.append(next_row)
        if is_done:
            completed.add(task)
        else:
            completed.discard(task)
    st.session_state[storage_key] = json.dumps(sorted(completed))
    done = sum(row["status"] == "Done" for row in updated)
    st.progress(done / len(updated) if updated else 0.0, text=f"{done} of {len(updated)} complete")
    return updated


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


def render_usage_stability_lens_parking_panel() -> None:
    st.caption(
        "Review-only usage/stability lens. Not a ranking system. Does not affect the "
        "main board. Candidate status: HOLD. Production promotion and main-formula "
        "readiness are not approved."
    )
    _tool_table(usage_stability_lens_parking_rows())
    st.caption(
        "Use only to review where usage/stability evidence is warmer or colder than "
        "baseline. The optional static packet path is manual only; the app does not "
        "open it, score it, regenerate it, or fail if it is missing."
    )
    with st.expander("Reusable good parts extracted from the held lens", expanded=False):
        _tool_table(usage_stability_lens_good_parts_rows())


def render_display_only_ngs_context_panel() -> None:
    st.caption(
        "Review-only NGS context. Display-only context. Not used in rankings. "
        "Not a model score. NGS public thresholds may exclude low-volume players."
    )
    _tool_table(development_lab_ngs_rows())
    st.caption(
        "The rows above are position-scoped context fields only. They do not create a "
        "score, recommendation, verdict, boost, hidden sort, or ranking effect."
    )
    with st.expander("Blocked advanced metrics kept out of this UI lane", expanded=False):
        _tool_table(blocked_ngs_metric_rows())
        st.caption(REVIEW_ONLY_WARNING)


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
        ("Roster Planner", "/roster-weakness-tracker"),
        ("Future Pick Planner", "/future-pick-planning"),
        ("Upcoming Draft Prep", "/upcoming-draft-prep"),
        ("Keeper Deadline Prep", "/keeper-deadline-prep"),
        ("Drop Deadline Prep", "/drop-deadline-prep"),
        ("Trade Deadline Prep", "/trade-deadline-prep"),
        ("Future Tools ideas", "/future-tools"),
    )
    for index, (label, path) in enumerate(links):
        with link_cols[index % 3]:
            st.link_button(label, path, width="stretch")


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
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
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
        width="stretch",
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
    render_planner_note()
    fields = {"manual_roster_rows": "development_lab_roster_weakness_tracker_rows"}
    _hydrate_local_lab_state("roster_weakness_tracker", fields)
    st.subheader("Add a roster player")
    roster_text = _guided_manual_entry(
        storage_key="development_lab_roster_weakness_tracker_rows",
        form_key="roster_planner_add_player",
        fields=(
            ("player", "Player", "Player name", ()),
            ("position", "Position", "", ("QB", "RB", "WR", "TE", "K", "DST")),
            ("age", "Age (optional)", "Example: 24", ()),
            ("dynasty_rank", "Dynasty rank (optional)", "Example: 18", ()),
            ("notes", "Notes (optional)", "Role, injury, or roster context", ()),
            ("nwr_player_id", "NWR player ID (advanced)", "Optional exact ID", ()),
        ),
        required_field="player",
        paste_label="Roster rows",
        paste_help=(
            "One player per line: Player, Position, Age, Dynasty Rank, Notes, NWR Player ID. "
            "Quoted commas are supported."
        ),
    )
    rows = parse_manual_roster_text(roster_text)
    if not rows:
        st.info(
            "Add your first player to see position depth, age balance, and dynasty-rank bands."
        )
        with st.expander("Advanced data details", expanded=False):
            _render_roster_status_context(())
        _render_lab_state_controls("roster_weakness_tracker", fields)
        return
    section = st.container()
    with section:
        st.subheader("Your roster plan")
        _owner_table(
            rows,
            (
                ("player", "Player"),
                ("position", "Pos"),
                ("age", "Age"),
                ("dynasty_rank", "Dynasty Rank"),
                ("notes", "Notes"),
            ),
        )
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Position depth")
        _owner_table(
            roster_position_summary(rows),
            (
                ("position", "Pos"),
                ("player_count", "Players"),
                ("starter_threshold", "Starter Need"),
                ("coverage_note", "What to review"),
            ),
        )
        st.subheader("Age balance")
        _owner_table(
            roster_age_bucket_summary(rows),
            (("age_bucket", "Age Band"), ("player_count", "Players")),
        )
    with col_b:
        st.subheader("Dynasty asset bands")
        _owner_table(
            roster_dynasty_rank_bucket_summary(rows),
            (("dynasty_rank_bucket", "Rank Band"), ("player_count", "Players")),
        )
        csv_download(
            "Download roster plan",
            rows,
            "nwr_roster_weakness_tracker_v0_display_only.csv",
        )
    with st.expander("Advanced data details", expanded=False):
        _render_roster_status_context(manual_nwr_player_ids(rows))
    _render_lab_state_controls("roster_weakness_tracker", fields)


def render_future_pick_planning() -> None:
    render_planner_note()
    fields = {"manual_future_pick_notes": "development_lab_future_pick_planning_rows"}
    _hydrate_local_lab_state("future_pick_planning", fields)
    live_state_result = load_runtime_state_with_status(mode="live")
    runtime_rows = future_pick_ledger_from_runtime_state(live_state_result.state)
    st.subheader("Add a future pick")
    manual_text = _guided_manual_entry(
        storage_key="development_lab_future_pick_planning_rows",
        form_key="future_pick_planner_add_pick",
        fields=(
            ("pick_year", "Year", "Example: 2028", ()),
            ("pick_round", "Round", "", ("1st", "2nd", "3rd", "4th", "Other")),
            (
                "direction",
                "Ownership status",
                "",
                ("Owned", "Acquired", "Sent", "Swap rights", "Uncertain"),
            ),
            ("counterparty", "From / to (optional)", "Team or manager", ()),
            ("notes", "Notes (optional)", "Conditions or verification needed", ()),
        ),
        required_field="pick_year",
        paste_label="Future pick rows",
        paste_help=(
            "One pick per line: Year, Round, Ownership Status, From/To, Notes. "
            "Quoted commas are supported."
        ),
    )
    manual_rows = parse_manual_future_pick_text(manual_text)
    combined = [*runtime_rows, *manual_rows]
    st.subheader("Pick inventory")
    if combined:
        _owner_table(
            combined,
            (
                ("pick_year", "Year"),
                ("pick_round", "Round"),
                ("direction", "Status"),
                ("counterparty", "From / To"),
                ("notes", "Notes"),
                ("source", "Source"),
            ),
        )
    else:
        st.info("Add a pick or record one in a saved trade scenario to begin your inventory.")
    csv_download(
        "Download pick inventory",
        combined,
        "nwr_future_pick_planning_v0_display_only.csv",
    )
    with st.expander("Advanced data details", expanded=False):
        st.caption(f"Local draft-event status: {live_state_result.status}")
        _render_draft_capital_context()
    _render_lab_state_controls("future_pick_planning", fields)


def render_upcoming_draft_prep() -> None:
    render_planner_note()
    fields = {
        "setup_notes": "development_lab_upcoming_draft_setup_notes",
        "setup_completed": "development_lab_upcoming_draft_setup_completed",
        "roster_need_rows": "development_lab_upcoming_roster_needs",
        "pick_inventory_rows": "development_lab_upcoming_pick_inventory",
        "watchlist_rows": "development_lab_upcoming_watchlist",
        "scenario_rows": "development_lab_upcoming_mock_scenarios",
        "question_notes": "development_lab_upcoming_question_notes",
        "questions_completed": "development_lab_upcoming_questions_completed",
        "readiness_notes": "development_lab_upcoming_readiness_notes",
        "readiness_completed": "development_lab_upcoming_readiness_completed",
    }
    _hydrate_local_lab_state("upcoming_draft_prep", fields)

    st.subheader("1. Draft setup")
    setup_notes = st.text_area(
        "Setup notes (optional)",
        key="development_lab_upcoming_draft_setup_notes",
        help="Optional manual note. Save local lab state to preserve it across reloads.",
    )
    setup_rows = _interactive_checklist(
        upcoming_draft_setup_checklist(notes=setup_notes),
        task_column="task",
        storage_key="development_lab_upcoming_draft_setup_completed",
        widget_prefix="upcoming_draft_setup_check",
    )
    csv_download(
        "Download setup checklist",
        setup_rows,
        "nwr_draft_setup_checklist_v0.csv",
    )

    st.subheader("2. Roster needs")
    roster_need_text = _guided_manual_entry(
        storage_key="development_lab_upcoming_roster_needs",
        form_key="upcoming_draft_add_roster_need",
        fields=(
            ("position", "Position", "", ("QB", "RB", "WR", "TE", "K", "DST")),
            ("short_term_need", "Short-term need", "Example: starter depth", ()),
            ("long_term_need", "Long-term need", "Example: aging room", ()),
            ("depth_concern_notes", "Depth concern", "What is thin?", ()),
            ("watch_notes", "Draft note", "What should you watch?", ()),
        ),
        required_field="position",
        paste_label="Roster need rows",
        paste_help=(
            "One need per line: Position, Short-term Need, Long-term Need, "
            "Depth Concern, Draft Note."
        ),
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
    if roster_need_rows:
        _owner_table(
            roster_need_rows,
            (
                ("position", "Pos"),
                ("short_term_need", "Now"),
                ("long_term_need", "Later"),
                ("depth_concern_notes", "Depth Concern"),
                ("watch_notes", "Draft Note"),
            ),
        )
    else:
        st.info("Add the position rooms you want to improve in this draft.")
    csv_download(
        "Download roster needs CSV",
        roster_need_rows,
        "nwr_upcoming_draft_roster_needs_v0.csv",
    )

    st.subheader("3. Pick inventory")
    live_state_result = load_runtime_state_with_status(mode="live")
    runtime_rows = future_pick_ledger_from_runtime_state(live_state_result.state)
    pick_text = _guided_manual_entry(
        storage_key="development_lab_upcoming_pick_inventory",
        form_key="upcoming_draft_add_pick",
        fields=(
            ("year", "Year", "Example: 2027", ()),
            ("round_pick", "Round / pick", "Example: 1.08", ()),
            ("status", "Status", "", ("Owned", "Acquired", "Sent", "Uncertain")),
            ("source_note", "Source / note", "Where did this come from?", ()),
            ("action_needed", "Next action", "Verify, hold, shop, or package", ()),
        ),
        required_field="year",
        paste_label="Pick inventory rows",
        paste_help="One pick per line: Year, Round/Pick, Status, Source/Note, Next Action.",
    )
    pick_rows = parse_manual_table_text(
        pick_text,
        ("year", "round_pick", "status", "source_note", "action_needed"),
        source="Manual input / display-only",
        guardrail="Planning ledger only; no pick/trade math.",
    )
    combined_picks = [*runtime_rows, *pick_rows]
    if combined_picks:
        display_picks = [
            {
                "year": row.get("year") or row.get("pick_year"),
                "round_pick": row.get("round_pick") or row.get("pick_round"),
                "status": row.get("status") or row.get("direction"),
                "source_note": row.get("source_note") or row.get("notes"),
                "action_needed": row.get("action_needed", ""),
            }
            for row in combined_picks
        ]
        _owner_table(
            display_picks,
            (
                ("year", "Year"),
                ("round_pick", "Round / Pick"),
                ("status", "Status"),
                ("source_note", "Source / Note"),
                ("action_needed", "Next Action"),
            ),
        )
    else:
        st.info("Add the picks you expect to control on draft day.")
    csv_download(
        "Download pick inventory CSV",
        combined_picks,
        "nwr_upcoming_draft_pick_inventory_v0.csv",
    )

    st.subheader("4. Rookie watchlist")
    watchlist_text = _guided_manual_entry(
        storage_key="development_lab_upcoming_watchlist",
        form_key="upcoming_draft_add_watchlist",
        fields=(
            ("player_name", "Player", "Prospect name", ()),
            ("school_team", "School / team", "Optional", ()),
            ("position", "Position", "", ("QB", "RB", "WR", "TE", "Other")),
            ("note", "Why watch?", "Your scouting question", ()),
            ("source_note", "Source note", "Optional", ()),
            ("review_status", "Status", "", ("Need review", "Watching", "Done")),
        ),
        required_field="player_name",
        paste_label="Watchlist rows",
        paste_help="One player per line: Player, School/Team, Position, Why Watch, Source, Status.",
    )
    watchlist_rows = parse_manual_table_text(
        watchlist_text,
        ("player_name", "school_team", "position", "note", "source_note", "review_status"),
        source="Manual input / display-only",
        guardrail="Manual watchlist only; no CFBD promotion, rank change, or model output.",
    )
    if watchlist_rows:
        _owner_table(
            watchlist_rows,
            (
                ("player_name", "Player"),
                ("school_team", "School / Team"),
                ("position", "Pos"),
                ("note", "Why Watch"),
                ("review_status", "Status"),
            ),
        )
    else:
        st.info("Add prospects you want to investigate before the draft.")
    csv_download(
        "Download rookie watchlist CSV",
        watchlist_rows,
        "nwr_upcoming_draft_manual_watchlist_v0.csv",
    )

    st.subheader("5. Draft scenarios")
    st.link_button("Open Mock Drafts", "/mock-draft", width="content")
    scenario_text = _guided_manual_entry(
        storage_key="development_lab_upcoming_mock_scenarios",
        form_key="upcoming_draft_add_scenario",
        fields=(
            ("scenario_name", "Scenario", "Example: RB run before 1.08", ()),
            ("before_my_pick", "Before my pick", "What happens?", ()),
            ("trade_down_scenario", "Trade-down option", "Optional", ()),
            ("position_run_scenario", "Position run", "Optional", ()),
            ("if_player_x_is_gone", "Fallback", "What if your target is gone?", ()),
        ),
        required_field="scenario_name",
        paste_label="Draft scenario rows",
        paste_help=(
            "One scenario per line: Scenario, Before My Pick, Trade-down Option, "
            "Position Run, Fallback."
        ),
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
    if scenario_rows:
        _owner_table(
            scenario_rows,
            (
                ("scenario_name", "Scenario"),
                ("before_my_pick", "Before My Pick"),
                ("trade_down_scenario", "Trade-down"),
                ("position_run_scenario", "Position Run"),
                ("if_player_x_is_gone", "Fallback"),
            ),
        )
    else:
        st.info("Add the draft-board situations you want to rehearse.")
    csv_download(
        "Download mock scenario CSV",
        scenario_rows,
        "nwr_upcoming_draft_mock_scenarios_v0.csv",
    )

    st.subheader("6. Questions to answer")
    question_notes = st.text_area(
        "Open question notes",
        key="development_lab_upcoming_question_notes",
    )
    question_rows = _interactive_checklist(
        upcoming_draft_questions_checklist(notes=question_notes),
        task_column="question",
        storage_key="development_lab_upcoming_questions_completed",
        widget_prefix="upcoming_draft_question_check",
    )
    csv_download(
        "Download draft questions CSV",
        question_rows,
        "nwr_upcoming_draft_questions_v0.csv",
    )

    st.subheader("7. Final readiness")
    readiness_notes = st.text_area(
        "Data readiness notes",
        key="development_lab_upcoming_readiness_notes",
    )
    readiness_rows = _interactive_checklist(
        upcoming_draft_data_readiness_checklist(notes=readiness_notes),
        task_column="check",
        storage_key="development_lab_upcoming_readiness_completed",
        widget_prefix="upcoming_draft_readiness_check",
    )
    csv_download(
        "Download data readiness CSV",
        readiness_rows,
        "nwr_upcoming_draft_data_readiness_v0.csv",
    )
    with st.expander("Advanced data details", expanded=False):
        st.caption(f"Local draft-event status: {live_state_result.status}")
        _render_draft_capital_context()
    _render_lab_state_controls("upcoming_draft_prep", fields)


def render_deadline_prep(tool_id: str, title: str) -> None:
    render_planner_note()
    fields = {
        "manual_deadline_date": f"development_lab_{tool_id}_date",
        "manual_notes": f"development_lab_{tool_id}_notes",
        "completed_tasks": f"development_lab_{tool_id}_completed",
    }
    _hydrate_local_lab_state(tool_id, fields)
    st.subheader("Deadline and plan")
    date_text = st.text_input(
        "League deadline",
        placeholder="YYYY-MM-DD, time, or league note",
        key=f"development_lab_{tool_id}_date",
    )
    notes = st.text_area(
        "Plan notes",
        key=f"development_lab_{tool_id}_notes",
        help="Record the decisions, questions, and people you need to follow up with.",
    )
    st.subheader("Checklist")
    rows = _interactive_checklist(
        deadline_checklist(
            tool_id,
            date_text=date_text,
            notes=notes,
        )[:-1],
        task_column="task",
        storage_key=f"development_lab_{tool_id}_completed",
        widget_prefix=f"{tool_id}_check",
    )
    csv_download(
        "Download checklist",
        rows,
        f"nwr_{tool_id}_v0_manual_checklist.csv",
    )
    with st.expander("Advanced data details", expanded=False):
        _render_deadline_status_context()
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


def render_planning_advanced_details() -> None:
    with st.expander("Advanced data details and safety", expanded=False):
        render_guardrails()


def csv_download(label: str, rows: list[dict[str, object]], filename: str) -> None:
    if not rows:
        return
    data = pd.DataFrame(spreadsheet_safe_rows(rows)).to_csv(index=False)
    st.download_button(label, data=data, file_name=filename, mime="text/csv")


def _tool_table(rows: list[dict[str, str]]) -> None:
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _render_optional_manual_table(rows: list[dict[str, str]], empty_message: str) -> None:
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
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
        st.caption(f"Saved plan loaded. Last updated: {state.saved_at_utc}.")
    elif state.status == "MISSING":
        st.caption("No saved plan yet. Add your notes, then save below.")
    else:
        st.warning(state.message)


def _render_lab_state_controls(tool_key: str, fields: dict[str, str]) -> None:
    st.divider()
    st.subheader("Save your plan")
    st.caption("Saved locally on this computer. Your NWR rankings and league data stay unchanged.")
    payload = _payload_from_session(fields)
    col_save, col_export = st.columns(2)
    if col_save.button(
        "Save this plan",
        key=f"development_lab_{tool_key}_save_state",
        width="stretch",
    ):
        result = save_tool_state(tool_key, payload)
        if result.backup_path:
            st.success(f"Saved. Previous state backed up to {result.backup_path.name}.")
        else:
            st.success("Plan saved locally.")
    col_export.download_button(
        "Download backup",
        data=export_tool_state_json(tool_key, payload),
        file_name=f"nwr_development_lab_{tool_key}_state.json",
        mime="application/json",
        key=f"development_lab_{tool_key}_export_state",
        width="stretch",
    )

    with st.expander("Advanced backup, import, or reset", expanded=False):
        uploaded = st.file_uploader(
            "Import a planning backup",
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
                        _clear_planning_check_widgets(tool_key)
                        st.success("Planning backup imported.")
                        st.rerun()
                    else:
                        st.warning(result.message)
            else:
                st.warning(preview.message)

        confirm_reset = st.checkbox(
            "Confirm reset of this saved plan",
            key=f"development_lab_{tool_key}_confirm_reset",
        )
        if st.button(
            "Reset this plan",
            key=f"development_lab_{tool_key}_reset_state",
        ):
            result = reset_tool_state(tool_key, confirmed=confirm_reset)
            if result.status == "RESET":
                for widget_key in fields.values():
                    st.session_state[widget_key] = ""
                _clear_planning_check_widgets(tool_key)
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


def _clear_planning_check_widgets(tool_key: str) -> None:
    prefixes = (
        f"{tool_key}_check_",
        "upcoming_draft_setup_check_",
        "upcoming_draft_question_check_",
        "upcoming_draft_readiness_check_",
    )
    for key in list(st.session_state):
        if any(str(key).startswith(prefix) for prefix in prefixes):
            st.session_state.pop(key, None)


def _local_state_status_label(state: DevelopmentLabToolState) -> str:
    if state.status == "LOADED":
        return "Saved locally"
    if state.status == "MISSING":
        return "No saved notes"
    return state.status.replace("_", " ").title()
