from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.draft_day_runtime_state_service import load_runtime_state_with_status
from src.services.future_tools_rd_service import (
    FutureToolStatus,
    blocked_tools,
    deadline_checklist,
    future_pick_ledger_from_runtime_state,
    future_tools_summary,
    load_future_tools_status_matrix,
    parse_manual_future_pick_text,
    parse_manual_roster_text,
    roster_age_bucket_summary,
    roster_dynasty_rank_bucket_summary,
    roster_position_summary,
    safe_v0_tools,
)

LAB_WARNING = (
    "Development Lab tool. Safe V0 / display-only / manual workflow. Not model input. "
    "Not source truth."
)

ROADMAP_WARNING = (
    "Roadmap only. Not active. Requires future data, approval, or model gate."
)


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
    _tool_table(
        [
            {
                "Tool": row.tool_name,
                "Route": _route_for_tool(row.tool_id),
                "Mode": "Safe V0 display/manual",
                "Data used": row.required_data_summary,
                "Why safe": row.notes,
                "Next approval": row.blocker_next_gate,
            }
            for row in safe_v0_tools(statuses)
        ]
    )


def render_blocked_tools_table(statuses: list[FutureToolStatus]) -> None:
    _tool_table(
        [
            {
                "Tool": row.tool_name,
                "Status": row.decision,
                "Why blocked": row.blocker_next_gate,
                "Missing data / gate": row.required_data_summary,
                "Next step": row.next_step,
                "Active output": row.active_output_allowed,
                "Model input": row.model_input_allowed,
            }
            for row in blocked_tools(statuses)
        ]
    )


def render_lab_links() -> None:
    link_cols = st.columns(3)
    links = (
        ("Roster Weakness Tracker", "/roster-weakness-tracker"),
        ("Future Pick Planning", "/future-pick-planning"),
        ("Keeper Deadline Prep", "/keeper-deadline-prep"),
        ("Drop Deadline Prep", "/drop-deadline-prep"),
        ("Trade Deadline Prep", "/trade-deadline-prep"),
        ("Future Tools ideas", "/future-tools"),
    )
    for index, (label, path) in enumerate(links):
        with link_cols[index % 3]:
            st.link_button(label, path, use_container_width=True)


def render_roster_weakness_tracker() -> None:
    render_lab_warning()
    st.caption("Display-only roster structure. Not a recommendation. Not model input.")
    roster_text = st.text_area(
        "Manual roster rows",
        value="",
        placeholder="Player, Position, Age, Dynasty Rank, Notes",
        key="development_lab_roster_weakness_tracker_rows",
        help=(
            "Optional manual input. This is not stored by the app. Missing age/rank stays "
            "Not enough information."
        ),
    )
    rows = parse_manual_roster_text(roster_text)
    if not rows:
        st.info(
            "Enter manual roster rows to generate display-only counts. "
            "No roster recommendation is generated."
        )
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
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


def render_future_pick_planning() -> None:
    render_lab_warning()
    st.caption("Planning ledger only. No pick valuation, no trade valuation, no class strength.")
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
        value="",
        placeholder="2028, 1st, acquired, WhoDat, confirm against Sleeper later",
        key="development_lab_future_pick_planning_rows",
        help="Optional manual notes. This is not stored by the app.",
    )
    manual_rows = parse_manual_future_pick_text(manual_text)
    if manual_rows:
        st.dataframe(pd.DataFrame(manual_rows), use_container_width=True, hide_index=True)
    csv_download(
        "Download future pick planning CSV",
        [*runtime_rows, *manual_rows],
        "nwr_future_pick_planning_v0_display_only.csv",
    )


def render_deadline_prep(tool_id: str, title: str) -> None:
    render_lab_warning()
    st.caption("Manual checklist only. Not a decision engine. Not model input.")
    date_text = st.text_input(
        f"{title} manual deadline date",
        value="",
        placeholder="YYYY-MM-DD or league note",
        key=f"development_lab_{tool_id}_date",
    )
    notes = st.text_area(
        f"{title} manual notes",
        value="",
        key=f"development_lab_{tool_id}_notes",
        help="Optional manual note for export. This is not stored by the app.",
    )
    rows = deadline_checklist(tool_id, date_text=date_text, notes=notes)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    csv_download(
        f"Download {title} checklist CSV",
        rows,
        f"nwr_{tool_id}_v0_manual_checklist.csv",
    )


def render_guardrails() -> None:
    st.caption(
        "All active-output and model-input flags in the status matrix are no. There are no "
        "fake rankings, fake projections, fake waiver recommendations, fake start/sit advice, "
        "fake trade targets, or fake rookie class evaluations."
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


def _route_for_tool(tool_id: str) -> str:
    return {
        "roster_weakness_tracker": "/roster-weakness-tracker",
        "future_pick_planning": "/future-pick-planning",
        "keeper_deadline_prep": "/keeper-deadline-prep",
        "drop_deadline_prep": "/drop-deadline-prep",
        "trade_deadline_prep": "/trade-deadline-prep",
    }.get(tool_id, "/development-lab")
