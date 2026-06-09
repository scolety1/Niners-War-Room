from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.trust_status import render_page_trust_banner
from app.components.ui_framework import (
    WorkflowTile,
    page_header,
    render_workflow_tiles,
    section_label,
)
from src.config.settings import get_settings
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.final_calibration_gate_service import build_final_calibration_gate
from src.services.ranking_readiness_service import ranking_readiness_from_calibration

FINAL_REVIEW_BRIEF = Path("docs/model_v4/MODEL_V4_6_FINAL_HUMAN_REVIEW_BRIEF.md")


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
health = _load_health(active_data_pack, active_fingerprint)
calibration = build_final_calibration_gate(active_data_pack)
ranking_readiness = ranking_readiness_from_calibration(calibration)

page_header(
    "Review Workflow",
    eyebrow="Niners Dynasty War Room",
    description=(
        "Use this page as the map, not the model. Start with the roster deadline, "
        "then rookie picks, then specific player checks. Advanced audit and data "
        "tools stay out of the way unless you need them."
    ),
    status_items=(
        ("Review-only", "review"),
        ("No final recommendations", "blocked"),
        (f"Active pack: {Path(active_data_pack).name}", "safe"),
    ),
)

render_page_trust_banner(
    health,
    calibration_passed=ranking_readiness.calibration_passed,
    review_only_message=ranking_readiness.message if ranking_readiness.review_only else "",
    review_only_detail=(
        "This app organizes review surfaces. It does not make the final cut, keep, "
        "trade, defer, or draft decision for you."
    ),
    compact=True,
)

section_label("Start Here")
render_workflow_tiles(
    (
        WorkflowTile(
            "1. Decision Board",
            "Deadline",
            "Top-five rule slot, roster pressure, cut cost, and June 15 review.",
            "/decision-board",
            "Open Decision Board",
        ),
        WorkflowTile(
            "2. Draft Room",
            "Rookie Picks",
            "Pick Decision Lab, Prospect Board, Why This Review Order, and Evidence & Risk.",
            "/draft-room",
            "Open Draft Room",
        ),
        WorkflowTile(
            "3. Player Board",
            "Player Check",
            "Search any player, inspect model value, trust, warnings, and receipts.",
            "/player-board",
            "Open Player Board",
        ),
        WorkflowTile(
            "4. External Asset Reviews",
            "Context",
            "Review roster and external-asset context after roster and pick questions are clear.",
            "/trade-review",
            "Open External Asset Reviews",
        ),
    )
)

st.info(
    "Tonight's shortest path: Decision Board -> Draft Room -> Player Board. "
    "Only open External Asset Reviews if a roster or pick question needs extra context."
)

section_label("What Each Page Answers")
st.markdown(
    """
    - **Decision Board:** Who is under roster pressure, what is the top-five rule slot,
      and what would it cost to cut someone?
    - **Draft Room:** Which rookie/pick clusters deserve review at 1.03, 1.04, 2.04,
      2.08, and manual-only 5.04?
    - **Player Board:** Why does the model value a specific player the way it does?
    - **External Asset Reviews:** Is there context worth discussing, without creating an offer?
    - **Settings:** Is the active data pack healthy? Advanced imports live there.
    """
)

with st.expander("Advanced orientation docs", expanded=False):
    st.caption("Open only if you want the written review brief or audit trail.")
    st.write(f"Final human review brief: `{FINAL_REVIEW_BRIEF}`")
