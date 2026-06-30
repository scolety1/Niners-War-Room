from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Draft Prep Compatibility",
    eyebrow="Compatibility Route",
    description=(
        "Draft Prep has been split into clearer destinations. Use Upcoming Draft Prep for "
        "manual next-draft planning, Draft Cockpit for real draft state, Mock Drafts for practice, "
        "and Dynasty Rankings for the approved rankings view."
    ),
    status_items=(
        ("Compatibility", "review"),
        ("No source truth", "safe"),
        ("No model input", "safe"),
    ),
)

st.warning(
    "Compatibility page only. This route does not create rookie rankings, class grades, "
    "player recommendations, or model outputs."
)

section_label("Go To")
cols = st.columns(4)
cols[0].link_button("Upcoming Draft Prep", "/upcoming-draft-prep", use_container_width=True)
cols[1].link_button("Draft Cockpit", "/draft-cockpit", use_container_width=True)
cols[2].link_button("Mock Drafts", "/mock-draft", use_container_width=True)
cols[3].link_button("Dynasty Rankings", "/rankings", use_container_width=True)

section_label("Compatibility Notes")
st.caption(
    "The legacy `/draft-room` route remains available for old planning surfaces. The new "
    "`/draft-prep` route is a pointer to the Safe V0 manual planning page and core draft tools."
)
