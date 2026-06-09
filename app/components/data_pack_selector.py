from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import Settings
from src.services.data_pack_catalog_service import (
    DataPackCatalogEntry,
    applied_pack_notice_for_path,
    catalog_rows,
    discover_data_packs,
)
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.trust_status_service import trust_status_from_health

SESSION_KEY = "active_data_pack_path"


def selected_data_pack(settings: Settings) -> str:
    return str(st.session_state.get(SESSION_KEY) or settings.active_data_pack)


def render_data_pack_selector(settings: Settings) -> str:
    entries = discover_data_packs(
        project_root=settings.project_root,
        default_data_pack=settings.active_data_pack,
    )
    default_path = str(settings.active_data_pack)
    current_path = str(st.session_state.get(SESSION_KEY) or default_path)
    labels = {_entry_label(entry): str(entry.path) for entry in entries}
    label_by_path = {str(entry.path): _entry_label(entry) for entry in entries}
    selected_label = label_by_path.get(current_path)
    if selected_label is None and entries:
        selected_label = _entry_label(entries[0])
        current_path = str(entries[0].path)

    with st.sidebar:
        st.header("Active Snapshot")
        if not entries:
            st.warning("No data packs found.")
            st.session_state[SESSION_KEY] = default_path
            return default_path

        selected = st.selectbox(
            "Active snapshot",
            list(labels.keys()),
            index=list(labels.keys()).index(selected_label),
        )
        current_path = labels[selected]
        st.session_state[SESSION_KEY] = current_path
        _render_applied_pack_notice(entries, current_path)
        try:
            health = build_data_pack_health_report(current_path)
            st.metric("Data Health", health.readiness.upper())
            trust = trust_status_from_health(health)
            st.caption(f"Review status: {trust.title}")
        except Exception:
            st.metric("Data Health", "BLOCKED")
            st.caption("Review status: Blocked. Open Settings.")
        with st.expander("Pack Details", expanded=False):
            st.caption(f"Selected path: `{current_path}`")
            st.dataframe(
                pd.DataFrame(catalog_rows(entries)),
                use_container_width=True,
                hide_index=True,
            )

    return current_path


def _entry_label(entry: DataPackCatalogEntry) -> str:
    applied = (
        f" | applied {entry.applied_pack_status}"
        if entry.applied_pack_status
        else ""
    )
    return (
        f"{entry.name} | {entry.source_group} | "
        f"{entry.snapshot_date or 'unknown'} | "
        f"{entry.error_count} errors/{entry.warning_count} warnings"
        f"{applied}"
    )


def _render_applied_pack_notice(
    entries: list[DataPackCatalogEntry],
    current_path: str,
) -> None:
    notice = applied_pack_notice_for_path(entries, current_path)
    if notice is None:
        return
    message = f"{notice['reason']} {notice['next_action']}"
    status = str(notice["applied_pack_status"])
    if status == "ready":
        st.success(message)
    elif status == "review":
        st.warning(message)
    else:
        st.error(message)
