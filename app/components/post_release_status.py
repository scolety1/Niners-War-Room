"""Compact Streamlit presentation for governed freshness and persistence state."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import streamlit as st

from src.services.post_release_usability_service import SaveStatus, SourceFreshness


def render_source_freshness(rows: Iterable[SourceFreshness]) -> None:
    values = tuple(rows)
    if not values:
        return
    badges = st.columns(min(len(values), 4))
    for index, row in enumerate(values):
        badges[index % len(badges)].caption(f"{row.source_name}: {row.state} · {row.authority}")
    with st.expander("Source freshness details", expanded=False):
        st.dataframe(
            pd.DataFrame(
                {
                    "Source": row.source_name,
                    "Version": row.source_version,
                    "Snapshot / as-of": row.snapshot_date,
                    "Last verified": row.last_verified_date,
                    "State": row.state,
                    "Refresh": row.refresh_status,
                    "Authority": row.authority,
                }
                for row in values
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Scheduled refresh: DISABLED_PENDING_OWNER_APPROVAL")


def render_save_status(status: SaveStatus) -> None:
    message = f"{status.state}: {status.message}"
    if status.state == "Saved":
        st.success(message)
    elif status.state in {"Save failed", "Recovery required"}:
        st.error(message)
        st.caption("Retry explicitly after resolving the lock, checksum, or storage error.")
    elif status.state == "Saving":
        st.info(message)
    else:
        st.warning(message)
