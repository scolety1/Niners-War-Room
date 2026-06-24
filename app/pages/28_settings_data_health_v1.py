from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.data_health_dashboard_service import (
    HealthDashboardReport,
    build_data_health_dashboard,
    compact_status_cards,
)

STATUS_STYLES = {
    "GREEN": ("safe", "Ready"),
    "YELLOW": ("review", "Review"),
    "RED": ("blocked", "Blocked"),
    "INFO": ("", "Info"),
}


def _status_label(status: str) -> str:
    return STATUS_STYLES.get(status, ("review", status))[1]


def _status_kind(status: str) -> str:
    return STATUS_STYLES.get(status, ("review", status))[0]


def _render_warning_summary(report: HealthDashboardReport) -> None:
    if report.warnings.empty:
        return
    with st.expander("Warning summary", expanded=True):
        st.dataframe(
            _display_frame(report.warnings),
            use_container_width=True,
            hide_index=True,
        )


def _render_section(title: str, frame: pd.DataFrame, *, expanded: bool = False) -> None:
    with st.expander(title, expanded=expanded):
        if frame.empty:
            st.info("Not enough information")
            return
        st.dataframe(_display_frame(frame), use_container_width=True, hide_index=True)


def _display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    display = frame.copy()
    if "status" in display.columns:
        display["status"] = display["status"].map(
            lambda value: f"{value} - {_status_label(str(value))}"
        )
    return display


report = build_data_health_dashboard()

page_header(
    "Settings / Data Health",
    eyebrow="Draft-Day App V2",
    description=(
        "One place to check source freshness, runtime state, market baseline status, "
        "evidence buckets, and guardrails before trusting the app."
    ),
    status_items=(
        (f"Overall {_status_label(report.overall_status)}", _status_kind(report.overall_status)),
        ("Local runtime only", "review"),
        ("Market display-only", "safe"),
    ),
)

st.caption(
    "What this means: GREEN is usable, YELLOW means review the caveat before acting, "
    "and RED means do not trust that area until repaired."
)

cards = compact_status_cards(report)
columns = st.columns(3)
for index, card in enumerate(cards):
    with columns[index % 3]:
        st.metric(
            card["label"],
            _status_label(card["status"]),
            help=card["detail"],
        )

if not report.warnings.empty:
    warning_count = len(report.warnings)
    st.warning(
        f"{warning_count} data-health item(s) need review. Open the warning summary below."
    )
else:
    st.success("No data-health warnings found by the dashboard checks.")

_render_warning_summary(report)
_render_section("App / Version Status", report.app_status, expanded=True)
_render_section("Board Health", report.board_health, expanded=True)
_render_section("Market Baseline Health", report.market_health)
_render_section("Runtime Draft State Health", report.runtime_health)
_render_section("Historical / Model Evidence Health", report.evidence_health)
_render_section("Missing-Data Health", report.missing_data_health)
_render_section("Guardrail Checklist", report.guardrails, expanded=True)

st.markdown("### What This Dashboard Does Not Do")
st.markdown(
    """
    - It does not change NWR ranks, model values, or tier assignments.
    - It does not promote DynastyProcess, ADP, or market data into model truth.
    - It does not create or mutate runtime draft state when opened.
    - It does not make the frozen baseline board the only source of truth.
    """
)
