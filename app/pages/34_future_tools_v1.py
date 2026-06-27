from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header, section_label
from src.services.future_tools_rd_service import (
    future_tools_summary,
    group_future_tools,
    load_future_tools_status_matrix,
)

WARNING_TEXT = (
    "Roadmap and R&D only. These are not active model outputs, projections, rankings, "
    "start/sit recommendations, waiver recommendations, trade targets, or source-truth "
    "decisions unless explicitly marked as a safe display-only scaffold."
)


def _tool_table(rows: list[dict[str, str]]) -> None:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_framework_scaffold(tool_name: str) -> None:
    st.caption(f"{tool_name} is safe only as a framework/checklist shell.")
    st.markdown(
        "- Confirm required source status\n"
        "- List missing fields as Not enough information\n"
        "- Capture human notes\n"
        "- Do not produce recommendations, values, ranks, or hidden sort"
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
    "The only safe near-term work is status, docs, and framework-only checklists. "
    "Blocked tools remain visible so their missing data and approval gates are explicit."
)

for group_name, group_rows in group_future_tools(statuses).items():
    section_label(group_name)
    _tool_table(
        [
            {
                "Tool": row.tool_name,
                "Decision": row.decision,
                "Output type": row.output_type,
                "Scaffold": row.scaffold_status,
                "Blocker / next gate": row.blocker_next_gate,
                "Active output": row.active_output_allowed,
                "Model input": row.model_input_allowed,
            }
            for row in group_rows
        ]
    )
    with st.expander(f"{group_name} details", expanded=False):
        for row in group_rows:
            st.markdown(f"**{row.tool_name}**")
            st.caption(f"NWR coverage: {row.nwr_coverage_summary}")
            st.caption(f"Required data: {row.required_data_summary}")
            st.caption(f"Next step: {row.next_step}")
            if row.is_framework_only:
                _render_framework_scaffold(row.tool_name)
            else:
                st.caption("Status: blocked roadmap item. No active output is available.")

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
