from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.player_detail_card_service import PlayerDetailCardPayload


def render_player_detail_card(payload: PlayerDetailCardPayload) -> None:
    st.markdown(f"### {payload.player}")
    _render_header(payload)

    st.markdown("**Why this row appears here**")
    st.write(payload.why_text)

    st.markdown("**NWR / private model context**")
    if payload.private_model_metrics:
        st.dataframe(
            _metrics_frame(payload.private_model_metrics),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No private component rows are available for this player.")

    if payload.context == "rankings":
        st.markdown("**Rankings context**")
        st.caption(payload.display_only_note)
        st.dataframe(
            _metrics_frame(payload.ranking_context_metrics),
            use_container_width=True,
            hide_index=True,
        )
        st.info(payload.outcome_status)
    elif payload.context == "draft_prep":
        st.markdown("**Draft Prep context**")
        st.caption(payload.display_only_note)
        if payload.draft_prep_context_metrics:
            st.dataframe(
                _metrics_frame(payload.draft_prep_context_metrics),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("Draft Prep context is not available from current source rows.")
        if payload.user_context_metrics:
            st.markdown("**User / history context**")
            st.caption(
                "Prior draft history and spreadsheet highlight context are display-only "
                "and do not change NWR Draft Value or private player value."
            )
            st.dataframe(
                _metrics_frame(payload.user_context_metrics),
                use_container_width=True,
                hide_index=True,
            )
    elif payload.context == "live_draft_room":
        st.markdown("**Live Draft Room context**")
        st.caption(payload.display_only_note)
        if payload.live_draft_room_context_metrics:
            st.dataframe(
                _metrics_frame(payload.live_draft_room_context_metrics),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("Live Draft Room context is not available from current source rows.")
        st.info("Draft state is session/local mock state and does not mutate source data.")

    st.markdown("**Trust, warnings, and data needed**")
    st.write(f"Trust: {payload.trust_status}")
    st.write(f"Warnings: {payload.warning_summary}")
    if payload.warning_messages:
        for warning in payload.warning_messages[:8]:
            st.write(f"- {warning}")
    else:
        st.write("No active warning is flagged for this row.")
    if payload.data_needed:
        st.markdown("Data needed:")
        for item in payload.data_needed[:8]:
            st.write(f"- {item}")
    else:
        st.write("No missing evidence is flagged for this row.")

    if payload.legacy_comparison_score:
        st.markdown("**Legacy / context disclosure**")
        st.caption(payload.legacy_note)
        st.write(f"Legacy active-pack score: {payload.legacy_comparison_score}")

    with st.expander("Advanced source receipts", expanded=False):
        if payload.receipts:
            st.dataframe(
                pd.DataFrame(
                    {"Receipt": receipt.label, "Value": receipt.value}
                    for receipt in payload.receipts
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("Source receipt unavailable from current row.")

    st.markdown("**Notes**")
    st.caption("No persistent manual notes are written from this card.")


def _render_header(payload: PlayerDetailCardPayload) -> None:
    header_cols = st.columns(4)
    header_cols[0].metric("Rank", payload.nwr_rank)
    header_cols[1].metric("Pos", payload.position)
    header_cols[2].metric("Age", payload.age)
    header_cols[3].metric("Team", payload.team)
    badges = [
        payload.roster_status,
        payload.trust_status,
        payload.source_type,
    ]
    st.caption(" | ".join(badge for badge in badges if badge and badge != "-"))


def _metrics_frame(metrics: tuple[object, ...]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Context": metric.label,
                "Value": metric.value,
                "Note": metric.note or "-",
            }
            for metric in metrics
        ]
    )
