from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.draft_day_player_context_service import (
    OUTCOME_NOT_ENOUGH_INFORMATION,
    build_player_context_options,
    draft_day_player_context_for_player,
)


def render_nflverse_player_context_expander(
    player_frame: pd.DataFrame,
    *,
    key: str,
    title: str = "NFLVerse player context",
) -> None:
    with st.expander(title, expanded=False):
        st.caption("Display-only. Review-only context. Not model input.")
        st.caption(
            "Missing joins or missing fields remain Not enough information and never change "
            "draft workflow, ranks, tiers, sorting, pick state, or event logs."
        )
        options = build_player_context_options(player_frame)
        if not options:
            st.info(OUTCOME_NOT_ENOUGH_INFORMATION)
            return

        selected_label = st.selectbox(
            "Player context row",
            list(options),
            key=f"{key}_nflverse_player_context_player",
            help="Manual context lookup by NWR player id. This does not write draft state.",
        )
        result = draft_day_player_context_for_player(options[selected_label])
        st.caption(f"Source: {result.source}")
        st.caption(f"As of: {result.as_of}")
        st.caption(f"Status: {result.message}")
        if result.status == "needs_identity_review":
            st.warning("Needs identity review")
        elif not result.available:
            st.info(OUTCOME_NOT_ENOUGH_INFORMATION)
        for error in result.errors:
            st.warning(error)

        for section in result.sections:
            st.markdown(f"#### {section.title}")
            st.dataframe(
                pd.DataFrame(section.rows, columns=["Field", "Display-only value"]),
                width="stretch",
                hide_index=True,
                key=f"{key}_{section.title.lower().replace(' ', '_').replace('/', '_')}",
            )
