from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.evidence_review_hub_service import (  # noqa: E402
    artifact_index_rows,
    current_decision_board_rows,
    guardrail_summary_rows,
    phase_timeline_rows,
    review_queue_rows,
    safe_next_action_rows,
    summary_metrics,
)


def _table(rows: list[dict[str, str]]) -> None:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


page_header(
    "Evidence Review Hub",
    eyebrow="Review-only hub",
    description=(
        "Central navigation and evidence-status cockpit for merged review packets. "
        "This page is status display only and does not feed normal decision surfaces."
    ),
    status_items=(
        ("Review-only", "review"),
        ("No production approval", "blocked"),
        ("No source truth", "safe"),
    ),
)

st.warning(
    "Review-only evidence hub. It does not change formulas, models, ranks, source truth, "
    "hidden sort, production config, or normal app behavior."
)
st.caption(
    "The hub reads tracked docs/CSV artifacts only. It does not read raw shared/cache/local "
    "exports or secrets."
)

metrics = summary_metrics()
metric_cols = st.columns(5)
metric_cols[0].metric("Artifacts indexed", metrics["artifacts_indexed"])
metric_cols[1].metric("Review-only artifacts", metrics["review_only_artifacts"])
metric_cols[2].metric("Production gate", metrics["production_approved"])
metric_cols[3].metric("Shadow review approved", metrics["shadow_review_approved"])
metric_cols[4].metric("Open review items", metrics["open_review_items"])

section_label("Phase Timeline")
_table(phase_timeline_rows())

section_label("Current Decision Board")
_table(current_decision_board_rows())

section_label("Artifact Index")
_table(artifact_index_rows())

section_label("Guardrail Summary")
_table(guardrail_summary_rows())

section_label("Review Queue")
_table(review_queue_rows())

section_label("Safe Next Actions")
_table(safe_next_action_rows())
