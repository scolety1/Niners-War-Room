from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_deadline_prep,
    render_planning_advanced_details,
)
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Trade Deadline Prep",
    eyebrow="Team Planning",
    description=(
        "Set your deadline plan, finish the checks that matter, then move directly into "
        "trade analysis or a player comparison."
    ),
    status_items=(
        ("Trackable checklist", "safe"),
        ("Saved locally", "safe"),
        ("No automatic transaction", "review"),
    ),
)

render_deadline_prep("trade_deadline_prep", "Trade Deadline Prep")

section_label("Continue your decision")

cols = st.columns(2)
cols[0].link_button("Analyze a trade", "/trading-lab", width="stretch")
cols[1].link_button("Compare players", "/player-compare", width="stretch")

render_planning_advanced_details()
