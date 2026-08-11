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
    render_future_tool_gate_badges,
    render_guardrails,
    render_roadmap_warning,
)
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Future Tools",
    eyebrow="Advanced / Roadmap",
    description=(
        "Ideas-only parking lot for tools that are not active yet. Owner planning tools live "
        "in Trades & Team or Draft Tools instead."
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

section_label("Gate Badge Matrix")
render_future_tool_gate_badges(statuses)

section_label("What Is Not Active Here")
render_guardrails()

section_label("Graduated Planning Tools")
st.markdown(
    "Roster Planner, Future Pick Planner, Keeper Prep, "
    "Drop Prep, and Trade Deadline Prep live in **Trades & Team**. "
    "Upcoming Draft Prep lives in **Draft Tools**. Technical research and gate detail "
    "remains in [Research Tools](/development-lab)."
)
