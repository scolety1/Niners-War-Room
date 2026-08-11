from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.post_release_status import render_source_freshness
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_dynasty_rankings
from src.services.outcome_v3_display_service import (
    load_outcome_v3_display,
    outcome_v3_player_matrix,
)
from src.services.post_release_usability_service import freshness_for_sources

page_header(
    "Dynasty Outcomes",
    eyebrow="One player · one row · all applicable V3 outcomes",
    description=(
        "See the governed chance of position-specific finishes across 2026, 2027, "
        "2028, and multi-year windows. These probabilities explain possible paths; "
        "they never change Finished V1 ranks."
    ),
    status_items=(
        ("Outcome V3", "safe"),
        ("Display-only", "review"),
        ("No invented values", "safe"),
    ),
)
render_source_freshness(freshness_for_sources(("Outcome V3", "Finished V1")))

board = load_dynasty_rankings()
outcomes = load_outcome_v3_display()
if not board.loaded:
    st.error("Finished V1 rankings are unavailable, so player identities cannot be joined.")
    for error in board.errors:
        st.caption(error)
    st.stop()
if not outcomes.loaded:
    st.error("Outcome V3 is unavailable. No fallback probabilities are shown.")
    for error in outcomes.errors:
        st.caption(error)
    st.stop()

position = st.segmented_control(
    "Position",
    ("QB", "RB", "WR", "TE"),
    default="QB",
    selection_mode="single",
)
position = position or "QB"
matrix, coverage, details = outcome_v3_player_matrix(
    board.frame,
    outcomes.frame,
    position=position,
)

metrics = st.columns(3)
metrics[0].metric("Players", len(matrix))
metrics[1].metric("Numeric outcomes", f"{coverage.numeric:,} / {coverage.applicable:,}")
metrics[2].metric("Applicable coverage", f"{coverage.percent:.1f}%")
st.caption(
    "A dash means NWR does not have an admitted probability for that exact player/outcome. "
    "Wrong-position fields are excluded from the denominator."
)

query = st.text_input("Find player", placeholder="e.g. Josh Allen")
shown = matrix
if query.strip():
    shown = matrix.loc[
        matrix["Player"].astype(str).str.contains(query.strip(), case=False, regex=False)
    ]
st.dataframe(shown, hide_index=True, use_container_width=True)

with st.expander("Why are some values unavailable?", expanded=False):
    if coverage.classifications:
        st.dataframe(
            pd.DataFrame(
                {
                    "Missing-value class": label,
                    "Fields": count,
                }
                for label, count in coverage.classifications
            ),
            hide_index=True,
            use_container_width=True,
        )
    selected_name = st.selectbox(
        "Inspect one player's missing fields",
        matrix["Player"].tolist(),
    )
    selected_details = details.loc[
        details["Player"].astype(str).eq(str(selected_name))
        & details["Value"].astype(str).eq("—")
    ]
    if selected_details.empty:
        st.success("All applicable Outcome V3 fields are numeric for this player.")
    else:
        st.dataframe(
            selected_details[
                ["Outcome", "Classification", "Why unavailable", "Evidence"]
            ],
            hide_index=True,
            use_container_width=True,
        )

with st.expander("Advanced authority details", expanded=False):
    st.write(
        {
            "release": outcomes.release_identifier,
            "source_hash": outcomes.source_hash,
            "source_rows": outcomes.row_count,
            "source_players": outcomes.player_count,
            "rank_use_allowed": False,
        }
    )
