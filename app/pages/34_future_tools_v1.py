from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header, section_label
from src.services.draft_day_runtime_state_service import load_runtime_state_with_status
from src.services.future_tools_rd_service import (
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

WARNING_TEXT = (
    "Roadmap and R&D only. These are not active model outputs, projections, rankings, "
    "start/sit recommendations, waiver recommendations, trade targets, or source-truth "
    "decisions unless explicitly marked as a safe display-only scaffold."
)


def _tool_table(rows: list[dict[str, str]]) -> None:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _csv_download(label: str, rows: list[dict[str, str]], filename: str) -> None:
    if not rows:
        return
    data = pd.DataFrame(rows).to_csv(index=False)
    st.download_button(label, data=data, file_name=filename, mime="text/csv")


def _render_roster_weakness_tracker() -> None:
    st.markdown("**Roster Weakness Tracker V0**")
    st.caption("Display-only roster structure. Not a recommendation. Not model input.")
    roster_text = st.text_area(
        "Manual roster rows",
        value="",
        placeholder="Player, Position, Age, Dynasty Rank, Notes",
        key="future_tools_safe_v0_roster_rows",
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
        _csv_download(
            "Download roster structure CSV",
            rows,
            "nwr_roster_weakness_tracker_v0_display_only.csv",
        )


def _render_future_pick_planning() -> None:
    st.markdown("**Future Pick Planning V0**")
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
        key="future_tools_safe_v0_future_pick_rows",
        help="Optional manual notes. This is not stored by the app.",
    )
    manual_rows = parse_manual_future_pick_text(manual_text)
    if manual_rows:
        st.dataframe(pd.DataFrame(manual_rows), use_container_width=True, hide_index=True)
    _csv_download(
        "Download future pick planning CSV",
        [*runtime_rows, *manual_rows],
        "nwr_future_pick_planning_v0_display_only.csv",
    )


def _render_deadline_prep(tool_id: str, title: str) -> None:
    st.markdown(f"**{title} V0**")
    st.caption("Manual checklist only. Not a decision engine. Not model input.")
    date_text = st.text_input(
        f"{title} manual deadline date",
        value="",
        placeholder="YYYY-MM-DD or league note",
        key=f"future_tools_safe_v0_{tool_id}_date",
    )
    notes = st.text_area(
        f"{title} manual notes",
        value="",
        key=f"future_tools_safe_v0_{tool_id}_notes",
        help="Optional manual note for export. This is not stored by the app.",
    )
    rows = deadline_checklist(tool_id, date_text=date_text, notes=notes)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    _csv_download(
        f"Download {title} checklist CSV",
        rows,
        f"nwr_{tool_id}_v0_manual_checklist.csv",
    )


page_header(
    "Future Tools",
    eyebrow="Roadmap / R&D Control Board",
    description=(
        "Future Tools tracks the research gate for in-season, future draft-prep, and "
        "league-calendar ideas without launching active recommendations."
    ),
    status_items=(
        ("R&D only", "review"),
        ("No model input", "safe"),
        ("No data pull", "safe"),
    ),
)

st.warning(WARNING_TEXT)

statuses = load_future_tools_status_matrix()
summary = future_tools_summary(statuses)

metric_cols = st.columns(4)
metric_cols[0].metric("Tools tracked", summary["total_tools"])
metric_cols[1].metric("Blocked / gated", summary["blocked"])
metric_cols[2].metric("Framework-only shells", summary["framework_only"])
metric_cols[3].metric("Active model outputs", summary["model_inputs"])

st.caption(
    "Safe V0 tools below are manual/display-only. They do not write source truth, run a "
    "model, value picks, create rankings, or produce advice."
)

safe_rows = safe_v0_tools(statuses)
blocked_rows = blocked_tools(statuses)

section_label("Safe V0 Tools")
_tool_table(
    [
        {
            "Tool": row.tool_name,
            "Mode": "Safe V0 display/manual",
            "Data used": row.required_data_summary,
            "Why safe": row.notes,
            "Next approval": row.blocker_next_gate,
        }
        for row in safe_rows
    ]
)

with st.expander("Roster Weakness Tracker", expanded=False):
    _render_roster_weakness_tracker()

with st.expander("Future Pick Planning", expanded=False):
    _render_future_pick_planning()

with st.expander("Deadline Prep Toolkit", expanded=False):
    deadline_tabs = st.tabs(
        ["Keeper Deadline Prep", "Drop Deadline Prep", "Trade Deadline Prep"]
    )
    with deadline_tabs[0]:
        _render_deadline_prep("keeper_deadline_prep", "Keeper Deadline Prep")
    with deadline_tabs[1]:
        _render_deadline_prep("drop_deadline_prep", "Drop Deadline Prep")
    with deadline_tabs[2]:
        _render_deadline_prep("trade_deadline_prep", "Trade Deadline Prep")

section_label("Blocked / Needs Gate")
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
        for row in blocked_rows
    ]
)

with st.expander("Guardrails", expanded=True):
    st.caption(
        "All active-output and model-input flags in the status matrix are no. There are no "
        "fake rankings, fake projections, fake waiver recommendations, fake start/sit advice, "
        "fake trade targets, or fake rookie class evaluations. This page does not run models."
    )
    st.caption(
        "Future Tools is not app decision wiring. It does not promote CFBD, NFL usage, "
        "Gmail, vendor, proxy, Outcome, DynastyProcess, ADP, or market data to model input."
    )
    st.caption(
        "No rank, tier, Dynasty Rank, Final Board Rank, pinned snapshot, latest candidate, "
        "latest approved, source-truth, or model logic is changed by this page."
    )
