from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.evidence_integration_review_service import (
    BLOCKER_TABLE_COLUMNS,
    DOC_REFERENCE_COLUMNS,
    NEXT_GATE_TABLE_COLUMNS,
    NOT_ALLOWED_COLUMNS,
    REGISTRY_TABLE_COLUMNS,
    SAFE_NOW_COLUMNS,
    export_csv,
    load_evidence_integration_review_data,
    table_columns,
)


def _metric_grid(summary: dict[str, object]) -> None:
    cards = [
        ("Evidence lanes", summary["evidence_lanes"]),
        ("Review-only lanes", summary["review_only_lanes"]),
        ("Model input enabled", summary["model_input_enabled"]),
        ("App wiring enabled", summary["app_wiring_enabled"]),
        ("Training enabled", summary["training_enabled"]),
        ("Raw data tracked", summary["raw_data_tracked"]),
        ("Blocked lanes", summary["blocked_lanes"]),
        ("Display-only lanes", summary["display_only_lanes"]),
    ]
    columns = st.columns(4)
    for index, (label, value) in enumerate(cards):
        with columns[index % 4]:
            st.metric(label, value)


data = load_evidence_integration_review_data()

page_header(
    "Evidence Integration Review",
    eyebrow="Hidden Review Route",
    description=(
        "Summarize committed CFBD, NFL usage, unified universe, market, Outcome, "
        "and league-history evidence status without feeding decision pages."
    ),
    status_items=(
        ("Review-only", "review"),
        ("Model input: no", "safe"),
        ("Decision wiring: no", "blocked"),
    ),
)

st.warning(
    "Review-only. This page does not feed rankings, Drafting Mode, Player Compare, "
    "Trading Lab, Post-Draft, or model features."
)
st.caption(
    "This page reads committed registry/status artifacts only. It does not load raw "
    "CFBD, nflverse, play-by-play, snap, NGS, FTN, PFR, local runtime, or shared-cache payloads."
)

_metric_grid(data.summary)

st.markdown("### What Is Safe Now")
st.dataframe(
    table_columns(data.safe_now, SAFE_NOW_COLUMNS),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### What Is Not Allowed Yet")
st.dataframe(
    table_columns(data.not_allowed, NOT_ALLOWED_COLUMNS),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Evidence Lane Table")
registry_display = table_columns(data.registry, REGISTRY_TABLE_COLUMNS)
st.dataframe(registry_display, use_container_width=True, hide_index=True)
st.download_button(
    "Download evidence registry CSV",
    data=export_csv(registry_display),
    file_name="evidence_status_registry_review.csv",
    mime="text/csv",
)

st.markdown("### Blockers")
st.caption(
    "These blockers prevent model input, training, or app decision wiring until a "
    "later explicit gate."
)
st.dataframe(
    table_columns(data.blockers, BLOCKER_TABLE_COLUMNS),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Next Gates")
st.dataframe(
    table_columns(data.next_gates, NEXT_GATE_TABLE_COLUMNS),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Main Evidence Artifact References")
st.dataframe(
    table_columns(data.registry, DOC_REFERENCE_COLUMNS),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Guardrail Checklist")
st.dataframe(data.guardrails, use_container_width=True, hide_index=True)

with st.expander("Source registry details", expanded=False):
    st.dataframe(data.registry, use_container_width=True, hide_index=True)
