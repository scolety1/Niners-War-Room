from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header, section_label


def _roadmap_table(rows: list[tuple[str, str]]) -> None:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Tool": name,
                    "Purpose": purpose,
                    "Status": "Future / Not active",
                    "Guardrail": "Roadmap only - no model output or source-truth decision.",
                }
                for name, purpose in rows
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

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
    "Roadmap only. These tools are not active model outputs, projections, rankings, "
    "or source-truth decisions yet."
)

section_label("In-Season Tools")
_roadmap_table(
    [
        ("Who Should I Start?", "Weekly lineup help."),
        ("Waiver Wire Rankings", "Best adds by roster need."),
        ("In-Season Rankings", "Rest-of-season / dynasty-adjusted movement."),
        ("Trade Targets", "Buy/sell/watch list."),
        ("Roster Weakness Tracker", "Where the team is thin."),
    ]
)

section_label("Future Draft Prep")
_roadmap_table(
    [
        ("Upcoming Rookie Class Preview", "Early look at future rookies."),
        ("Draft Class Strength", "Which future draft years look strong or weak."),
        ("Position Strength by Class", "RB/WR/QB/TE class quality by year."),
        ("Future Pick Planning", "What future years/rounds to value."),
        ("Position Target Plan", "What positions to target in future drafts."),
    ]
)

section_label("League Calendar Tools")
_roadmap_table(
    [
        ("Keeper Deadline Prep", "Review-only preparation for keeper deadlines."),
        ("Drop Deadline Prep", "Review-only preparation for drop deadlines."),
        ("Trade Deadline Prep", "Review-only preparation for trade deadlines."),
        ("Playoff Push Planner", "Future planning shell for playoff-window decisions."),
    ]
)

with st.expander("Guardrails", expanded=True):
    st.caption(
        "All rows on this page are marked Future / Not active. There are no fake rankings, "
        "fake projections, fake waiver recommendations, fake start/sit advice, or fake "
        "rookie class evaluations. This page does not run models."
    )
    st.caption(
        "Future Tools is not app decision wiring. It does not promote CFBD, NFL usage, "
        "Gmail, vendor, proxy, Outcome, DynastyProcess, ADP, or market data to model input."
    )
    st.caption(
        "No rank, tier, Dynasty Rank, Final Board Rank, pinned snapshot, latest candidate, "
        "latest approved, source-truth, or model logic is changed by this page."
    )
