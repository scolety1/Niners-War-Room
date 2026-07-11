from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from src.services.decision_trust_strip_service import (
    STATE_LABELS,
    VALID_CURRENT,
    DecisionTrustStrip,
)

_STATE_MARKERS = {
    "VALID_CURRENT": "✓",
    "STALE": "◷",
    "MISSING": "—",
    "GATED": "⊘",
    "UNAVAILABLE": "×",
    "IDENTITY_EXCEPTION": "!",
    "SOURCE_EXCEPTION": "!",
    "NOT_ENOUGH_INFORMATION": "?",
}


def render_decision_trust_strips(
    strips: Sequence[DecisionTrustStrip],
    *,
    heading: str = "Evidence trust",
    expanded: bool = False,
) -> None:
    if not strips:
        return
    st.markdown(f"**{heading}**")
    st.caption(
        "Display-only evidence status. These labels do not change rank, score, value, "
        "eligibility, sorting, filters, or recommendations."
    )
    for strip in strips:
        summary = " · ".join(_summary_part(field) for field in strip.fields[:-1])
        st.caption(f"{strip.entity_label} — {summary}")
        with st.expander(
            f"Evidence details — {strip.entity_label}",
            expanded=expanded,
        ):
            st.caption(
                "Keyboard-accessible disclosure using existing Streamlit interaction. "
                "Status meaning is always shown as text and never by color alone."
            )
            st.dataframe(
                [
                    {
                        "Field": field.label,
                        "State": STATE_LABELS[field.state],
                        "Existing value": field.value,
                        "Detail": field.detail,
                    }
                    for field in strip.fields
                ],
                use_container_width=True,
                hide_index=True,
            )


def _summary_part(field) -> str:
    marker = _STATE_MARKERS.get(field.state, "?")
    state = STATE_LABELS[field.state]
    value = field.value if field.state != VALID_CURRENT else state
    return f"{marker} {field.label}: {value}"
