from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.ui_framework import (  # noqa: E402
    WorkflowTile,
    page_header,
    render_workflow_tiles,
    section_label,
)

page_header(
    "Niners War Room",
    eyebrow="Start Here",
    description=(
        "Choose the decision surface that matches the job in front of you. "
        "The accepted dynasty board stays read-only; draft actions remain explicit and local."
    ),
    status_items=(
        ("10-team · 1QB · non-PPR", "safe"),
        ("First-down scoring", "safe"),
        ("Private local runtime", "safe"),
    ),
)

section_label("Choose a workflow")
render_workflow_tiles(
    (
        WorkflowTile(
            "Dynasty Rankings",
            "Canonical board",
            "Scan the accepted 240-player board, tiers, confidence, and evidence warnings.",
            "/rankings",
            "Open Rankings",
        ),
        WorkflowTile(
            "Player Compare",
            "Read-only",
            "Compare specific players without changing rankings or draft state.",
            "/player-compare",
            "Compare Players",
        ),
        WorkflowTile(
            "Trading Lab",
            "Manual decision aid",
            "Review player and pick value context; no trade is submitted automatically.",
            "/trading-lab",
            "Open Trading Lab",
        ),
        WorkflowTile(
            "Draft Cockpit",
            "Live local state",
            "Use explicit controls for a real draft session. Mock Drafts stay separate.",
            "/draft-cockpit",
            "Open Draft Cockpit",
        ),
    )
)

st.info(
    "Recommended first visit: confirm Data Health, then open Dynasty Rankings. "
    "Enter Draft Cockpit only when you intend to manage live local draft state."
)

section_label("Know what can change")
read_only, stateful = st.columns(2)
with read_only:
    st.markdown("**Read-only decision surfaces**")
    st.write(
        "Rankings, Player Compare, and Trading Lab present accepted local evidence. "
        "Opening them does not change the canonical board."
    )
with stateful:
    st.markdown("**Explicit or gated actions**")
    st.write(
        "Draft Cockpit changes local session state only through its controls. "
        "Refresh and recovery actions remain in Admin with confirmation and status details."
    )

health, workflow = st.columns(2)
health.link_button(
    "Check Data Health",
    "/settings-data-health",
    use_container_width=True,
)
workflow.link_button(
    "Open the Review Workflow",
    "/review-workflow",
    use_container_width=True,
)

catalog, rookies = st.columns(2)
catalog.link_button("Search Asset Explorer", "/asset-explorer", use_container_width=True)
rookies.link_button("Open 2026 Rookie Board", "/rookie-board", use_container_width=True)
