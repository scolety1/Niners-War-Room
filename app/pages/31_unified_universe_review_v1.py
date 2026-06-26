from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.unified_player_universe_review_page_service import (
    BLOCKER_TABLE_COLUMNS,
    CONSOLIDATION_TABLE_COLUMNS,
    REVIEW_TABLE_COLUMNS,
    export_csv,
    filter_blockers,
    filter_review_table,
    load_unified_universe_review_data,
    options_for,
    table_columns,
)


def _metric_grid(summary: dict[str, object]) -> None:
    cards = [
        ("Consolidated Rows", summary["consolidated_row_count"]),
        ("Veterans", summary["veteran_count"]),
        ("Rookies / Prospects", summary["rookie_prospect_count"]),
        ("PDF FA", summary["pdf_fa_count"]),
        ("Blockers", summary["blocker_count"]),
        ("Missing player_id", summary["missing_player_id_count"]),
        ("Missing age", summary["missing_age_count"]),
        ("Review-needed", summary["review_needed_count"]),
        ("App wiring allowed", summary["app_wiring_allowed"]),
        ("Model input allowed", summary["model_input_allowed"]),
    ]
    columns = st.columns(5)
    for index, (label, value) in enumerate(cards):
        with columns[index % 5]:
            st.metric(label, value)


data = load_unified_universe_review_data()

page_header(
    "Unified Universe Review",
    eyebrow="Review-only Artifact",
    description=(
        "Inspect the consolidated unified player universe artifact, blocker rows, "
        "and duplicate-handling decisions without approving app wiring."
    ),
    status_items=(
        ("Review-only", "review"),
        ("Not model input", "safe"),
        ("App wiring blocked", "blocked"),
    ),
)

st.markdown(
    '<a href="/live-draft-room" target="_self">Back to Live Draft</a>',
    unsafe_allow_html=True,
)
st.warning("Review-only. Not used by rankings, model, or Drafting Mode.")
st.caption(
    "This page is for inspection only. It does not change rankings. "
    "It does not change model inputs. It does not approve app wiring. "
    "Market data remains display-only. "
    "Missing Outcome means Not enough information, not low probability."
)

_metric_grid(data.summary)

st.markdown("### Filters")
filter_row_1 = st.columns(4)
with filter_row_1[0]:
    player_types = st.multiselect(
        "Player type",
        options_for(data.consolidated, "player_type"),
    )
with filter_row_1[1]:
    source_layers = st.multiselect(
        "Source layer",
        options_for(data.consolidated, "source_layers"),
    )
with filter_row_1[2]:
    positions = st.multiselect("Position", options_for(data.consolidated, "position"))
with filter_row_1[3]:
    review_statuses = st.multiselect(
        "Review status",
        options_for(data.consolidated, "review_status"),
    )

filter_row_2 = st.columns(5)
with filter_row_2[0]:
    blocker_types = st.multiselect("Blocker type", options_for(data.blockers, "blocker_type"))
with filter_row_2[1]:
    missing_player_id = st.selectbox(
        "Missing player_id",
        ["All", "Missing only", "Has player_id"],
    )
with filter_row_2[2]:
    missing_age = st.selectbox("Missing age", ["All", "Missing only", "Has age"])
with filter_row_2[3]:
    market_statuses = st.multiselect(
        "Market match status",
        options_for(data.consolidated, "market_match_status"),
    )
with filter_row_2[4]:
    outcome_statuses = st.multiselect(
        "Outcome status",
        options_for(data.consolidated, "outcome_status"),
    )

manual_review_flags = st.multiselect(
    "Manual review flag",
    options_for(data.consolidated, "manual_review_flag"),
)

filtered_review = filter_review_table(
    data.consolidated,
    player_types=player_types,
    source_layers=source_layers,
    positions=positions,
    review_statuses=review_statuses,
    missing_player_id=missing_player_id,
    missing_age=missing_age,
    market_statuses=market_statuses,
    outcome_statuses=outcome_statuses,
    manual_review_flags=manual_review_flags,
)
filtered_blockers = filter_blockers(data.blockers, blocker_types=blocker_types)

st.markdown("### Main Review Table")
st.caption(
    f"Showing {len(filtered_review)} of {len(data.consolidated)} consolidated review rows."
)
review_display = table_columns(filtered_review, REVIEW_TABLE_COLUMNS)
st.dataframe(review_display, use_container_width=True, hide_index=True)
st.download_button(
    "Download filtered review CSV",
    data=export_csv(review_display),
    file_name="unified_player_universe_filtered_review.csv",
    mime="text/csv",
)

st.markdown("### App-Wiring Blockers")
st.caption(
    f"Showing {len(filtered_blockers)} of {len(data.blockers)} blocker rows. "
    "Every blocker still prevents app wiring until reviewed."
)
st.dataframe(
    table_columns(filtered_blockers, BLOCKER_TABLE_COLUMNS),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### Duplicate / Consolidation Decisions")
st.caption(
    "All current duplicate groups are expected multi-layer same-player cases; "
    "they are collapsed only in this review artifact."
)
st.dataframe(
    table_columns(data.consolidation_decisions, CONSOLIDATION_TABLE_COLUMNS),
    use_container_width=True,
    hide_index=True,
)

with st.expander("Source summary and validation report", expanded=False):
    st.dataframe(data.source_summary, use_container_width=True, hide_index=True)
    st.dataframe(data.validation_report, use_container_width=True, hide_index=True)
