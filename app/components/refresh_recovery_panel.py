from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import streamlit as st

from src.services.refresh_recovery_presentation_service import (
    STATE_LABELS,
    RefreshRecoveryPresentation,
)


def render_refresh_recovery_panel(
    items: Iterable[RefreshRecoveryPresentation], *, title: str = "Refresh recovery guidance"
) -> None:
    rows = tuple(items)
    with st.expander(title, expanded=False):
        st.caption(
            "Passive guidance only. Opening this disclosure does not refresh, retry, repair, "
            "promote, or change any source."
        )
        if not rows:
            st.info("Not enough information — no refresh status record is available.")
            return
        display = pd.DataFrame(item.as_ordered_row() for item in rows)
        display["refresh_state"] = display["refresh_state"].map(
            lambda value: f"{value} — {STATE_LABELS[value]}"
        )
        st.dataframe(display, width="stretch", hide_index=True)
        st.caption(
            "AVAILABLE_ACTION means an existing approved control may be chosen separately; "
            "REVIEW_LINK means review or escalation only; INFORMATION_ONLY performs nothing; "
            "UNAVAILABLE_ACTION explains why no safe action is offered."
        )
