from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header

page_header(
    "Drafting Mode moved into Live Draft",
    eyebrow="Compatibility Route",
    description=(
        "The draft cockpit is now the Live Draft page. This route stays available so old "
        "links do not break, but it no longer acts as a separate main workspace."
    ),
    status_items=(
        ("Live Draft is primary", "safe"),
        ("Mock Drafts are practice", "review"),
        ("No model/rank mutation", "safe"),
    ),
)

st.warning(
    "Drafting Mode is no longer a separate main nav item. Use Live Draft for the live "
    "command center, runtime state, trade events, export/import, and pick-by-pick workflow."
)

cols = st.columns(3)
cols[0].link_button("Open Live Draft", "/live-draft-room", use_container_width=True)
cols[1].link_button("Open Mock Drafts", "/mock-draft", use_container_width=True)
cols[2].link_button("Open Dynasty Rankings", "/rankings", use_container_width=True)

st.markdown("### What Changed")
st.markdown(
    """
    - **Live Draft** is now the command-center draft room.
    - **Mock Drafts** uses the same draft-room workflow with a practice state scope.
    - **Cheat Sheets / Tier Board** remain available by direct URL and will be demoted into
      Live Draft and Dynasty Rankings views.
    """
)

with st.expander("Guardrails", expanded=False):
    st.caption("This compatibility page does not load or mutate runtime draft state.")
    st.caption("No rankings, tiers, Dynasty Rank, Final Board Rank, or model values are changed.")
    st.caption("No market/ADP/DynastyProcess values are used as trade valuation.")
