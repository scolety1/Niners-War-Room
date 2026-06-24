from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.data_refresh_orchestrator_service import (
    build_refresh_registry,
    refresh_results_table,
    run_data_refresh,
    validate_refresh_result_schema,
)


def _display_results(rows: list[dict[str, object]]) -> pd.DataFrame:
    columns = [
        "source_name",
        "status",
        "refreshed",
        "user_message",
        "timestamp",
        "artifact_updated",
        "caveat",
    ]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=columns)
    return frame.loc[:, columns].rename(
        columns={
            "source_name": "source",
            "user_message": "message",
            "artifact_updated": "artifact updated",
        }
    )


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    refreshed = [row for row in rows if row.get("refreshed") is True]
    skipped = [
        row
        for row in rows
        if str(row.get("status")) in {"SKIPPED", "NOT_CONFIGURED", "BLOCKED"}
    ]
    failed = [row for row in rows if row.get("status") == "RED"]
    return [
        {"metric": "sources refreshed", "value": len(refreshed)},
        {"metric": "sources skipped / not configured / blocked", "value": len(skipped)},
        {"metric": "failed sources", "value": len(failed)},
    ]


page_header(
    "Refresh Data",
    eyebrow="Source Refresh",
    description=(
        "Pull current data from configured safe sources and show exactly what was "
        "refreshed, skipped, blocked, or left manual."
    ),
    status_items=(
        ("No model/rank changes", "safe"),
        ("Manual sources stay manual", "review"),
        ("Local ignored status", "safe"),
    ),
)

st.caption(
    "Refresh Data does not auto-run. It does not mutate ranks, tiers, frozen board files, "
    "latest_candidate/latest_approved, pinned snapshots, or runtime draft picks."
)

include_slow = st.checkbox(
    "Include slow nflverse scheduled runner",
    value=False,
    help="Uses the existing local nflverse runner without candidate writes.",
)

registry = build_refresh_registry(include_slow_sources=include_slow)
with st.expander("Source registry", expanded=False):
    st.dataframe(
        pd.DataFrame([entry.__dict__ for entry in registry]),
        use_container_width=True,
        hide_index=True,
    )

if st.button("Refresh Data", type="primary", use_container_width=False):
    with st.spinner("Refreshing configured safe sources..."):
        run = run_data_refresh(include_slow_sources=include_slow)
    rows = refresh_results_table(run)
    validate_refresh_result_schema(rows)
    st.session_state["refresh_data_last_run"] = {
        "overall_status": run.overall_status,
        "rows": rows,
        "summary": _summary_rows(rows),
        "finished_at_utc": run.finished_at_utc,
    }

last_run = st.session_state.get("refresh_data_last_run")
if last_run:
    st.subheader("Freshness Summary")
    st.metric("Overall", str(last_run["overall_status"]))
    st.dataframe(
        pd.DataFrame(last_run["summary"]),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Per-Source Results")
    st.dataframe(
        _display_results(list(last_run["rows"])),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No manual Refresh Data run has been started in this session.")
