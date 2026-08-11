from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.components.owner_mode import owner_intro  # noqa: E402
from app.components.ui_framework import page_header  # noqa: E402

page_header(
    "Redraft is a separate app",
    eyebrow="Current season · separate from Dynasty",
    description=(
        "League profiles, projections, and draft state live in the dedicated Redraft surface."
    ),
    status_items=(("Dynasty board unchanged", "safe"), ("Separate local state", "safe")),
)
owner_intro(
    "Do not mix current-season and long-term decisions.",
    "Launch Redraft on its own port when you need league-specific rankings, tiers, "
    "comparison, or draft tools.",
)
st.link_button("Open Redraft at localhost:8512", "http://127.0.0.1:8512", use_container_width=True)
st.code("powershell -File scripts/start_redraft_app.ps1", language="powershell")
st.caption("If the link does not open, run the command from the repository root first.")
st.link_button("Return to Dynasty Owner Mode", "/owner-home")
