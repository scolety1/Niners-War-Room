from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header, section_label

page_header(
    "Future Tools",
    eyebrow="Roadmap / Ideas Only",
    description=(
        "Future Tools is a planning page for in-season and future draft-prep ideas. "
        "These tools are not active yet and do not feed the model, rankings, draft rooms, "
        "or trade decisions."
    ),
    status_items=(
        ("Roadmap only", "review"),
        ("No model input", "safe"),
        ("No data pull", "safe"),
    ),
)

st.warning(
    "Not active yet. This page is a roadmap placeholder only; it does not run models, "
    "pull data, change ranks, or create recommendations."
)

section_label("In-Season Tools - Ideas Only")
st.markdown(
    """
    - Who Should I Start?
    - In-Season Rankings
    - Waiver Wire Rankings
    - Trade Targets
    - Roster Weakness Tracker
    - Playoff Push Planner
    """
)

section_label("Future Draft Prep - Ideas Only")
st.markdown(
    """
    - Upcoming rookie class preview
    - Strong or weak future draft class scouting
    - Position strength by future class
    - Future pick planning
    - What positions to target in future draft years
    - Upcoming college/rookie watchlist, review-only
    """
)

section_label("League Strategy - Ideas Only")
st.markdown(
    """
    - Keeper deadline prep
    - Drop deadline prep
    - Trade deadline prep
    - Opponent roster tendencies
    - Team needs by opponent
    """
)

with st.expander("Guardrails", expanded=True):
    st.caption(
        "Future Tools is not app decision wiring. It does not promote CFBD, NFL usage, "
        "Gmail, vendor, proxy, Outcome, DynastyProcess, ADP, or market data to model input."
    )
    st.caption(
        "No rank, tier, Dynasty Rank, Final Board Rank, pinned snapshot, latest candidate, "
        "latest approved, source-truth, or model logic is changed by this page."
    )
