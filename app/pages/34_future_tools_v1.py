from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    load_statuses,
    render_blocked_tools_table,
    render_guardrails,
    render_roadmap_warning,
)
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Future Tools",
    eyebrow="Development Lab / Roadmap Ideas",
    description=(
        "Ideas-only parking lot for tools that are not active yet. Safe V0 lab tools now "
        "live on their own Development Lab pages."
    ),
    status_items=(
        ("Roadmap only", "review"),
        ("No fake outputs", "safe"),
        ("No model input", "safe"),
    ),
)

render_roadmap_warning()

statuses = load_statuses()

section_label("Blocked / Needs Gate")
render_blocked_tools_table(statuses)

section_label("What Is Not Active Here")
render_guardrails()

section_label("Safe V0 Lab Tools Moved")
st_link = '<a href="/development-lab" target="_self">Open Development Lab</a>'

st.markdown(
    (
        "Roster Weakness Tracker, Future Pick Planning, Keeper Deadline Prep, "
        "Drop Deadline Prep, and Trade Deadline Prep are now split into their own "
        f"Safe V0 lab pages. {st_link}"
    ),
    unsafe_allow_html=True,
)
