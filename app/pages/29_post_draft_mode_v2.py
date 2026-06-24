from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.draft_day_runtime_state_service import (
    event_rows,
    export_runtime_state,
    load_runtime_state,
    runtime_paths,
)

live_state = load_runtime_state(mode="live")
mock_state = load_runtime_state(mode="mock")

page_header(
    "Post-Draft Mode",
    eyebrow="Draft-Day App V2",
    description=(
        "Review local draft runtime picks, trades, selected/passed context, and next-action "
        "triage. This page reads local runtime state only and does not mutate source truth."
    ),
    status_items=(
        ("Runtime review", "safe"),
        ("No source mutation", "safe"),
        ("Human follow-up", "review"),
    ),
)

mode = st.radio("Runtime mode", ["Live", "Mock"], horizontal=True, key="post_draft_mode")
state = live_state if mode == "Live" else mock_state

summary_cols = st.columns(4)
summary_cols[0].metric("Picks made", len(state["workflow_state"]["assignments"]))
summary_cols[1].metric("Trades recorded", len(state["trade_events"]))
summary_cols[2].metric("Events", len(event_rows(state)))
summary_cols[3].metric("Mode", str(state["mode"]).title())

st.subheader("Picks Made")
assignments = state["workflow_state"]["assignments"]
if assignments:
    st.dataframe(pd.DataFrame(assignments).astype(str), use_container_width=True, hide_index=True)
else:
    st.info("No picks recorded for this mode.")

st.subheader("Trades Made")
if state["trade_events"]:
    st.dataframe(
        pd.DataFrame(state["trade_events"]).astype(str),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No trades recorded for this mode.")

st.subheader("Event Log")
rows = event_rows(state)
if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No runtime events recorded yet.")

st.subheader("Next-Actions Triage")
st.markdown(
    """
    - Confirm picks and trades against the final league draft log.
    - Review players passed at NWR pick windows manually.
    - Check whether any in-draft trade changed future pick inventory.
    - Do not promote post-draft conclusions into source truth without a separate approval lane.
    """
)

if st.button("Export Post-Draft Runtime Log", key="post_draft_export"):
    exports = export_runtime_state(state)
    st.success("Exported: " + " | ".join(str(path) for path in exports.values()))

with st.expander("Runtime paths / guardrails", expanded=False):
    paths = runtime_paths()
    st.caption(f"Runtime root: {paths.root}")
    st.caption(
        "Local runtime exports are written under C:\\NWR_SHARED_DATA and are not tracked by Git."
    )
