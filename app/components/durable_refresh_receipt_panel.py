from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from app.components.refresh_recovery_panel import render_refresh_recovery_panel
from src.services.refresh_receipt_store_service import (
    CORRUPT,
    MISSING,
    OVERSIZED,
    UNSUPPORTED_SCHEMA,
    RefreshReceiptLoadResult,
)
from src.services.refresh_recovery_presentation_service import (
    build_refresh_recovery_presentations,
    build_run_recovery_summary,
)

LIFECYCLE_COLUMNS = (
    "source_id",
    "dataset_id",
    "action_type",
    "status",
    "execution_status",
    "freshness_status",
    "retained_data_status",
    "latest_successful_receipt_id",
    "last_known_good_receipt_id",
    "failure_context",
)


def render_durable_refresh_receipt_panel(
    load: RefreshReceiptLoadResult,
    *,
    title: str = "Durable refresh receipt",
) -> None:
    st.markdown(f"### {title}")
    st.caption(
        "Local metadata durability only. This view does not refresh, retry, promote, "
        "or change any source, freshness rule, ranking, or retained dataset."
    )
    if load.has_valid_latest:
        _render_valid_receipt(load.latest_receipt or {}, role="Latest refresh attempt")
        return

    message = {
        MISSING: "Latest refresh receipt is missing. No current outcome is inferred.",
        CORRUPT: "Latest refresh receipt is corrupt. It is not used as current truth.",
        OVERSIZED: "Latest refresh receipt exceeds the supported bound and is not trusted.",
        UNSUPPORTED_SCHEMA: (
            "Latest refresh receipt uses an unsupported schema and is not trusted."
        ),
    }.get(load.load_status, "Latest refresh receipt is not trustworthy.")
    if load.load_status == MISSING:
        st.info(message)
    else:
        st.error(message)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "receipt_role": "Latest refresh attempt",
                    "load_status": load.load_status,
                    "receipt_id": "Not available",
                    "outcome": "NOT_ENOUGH_INFORMATION",
                    "detail": load.detail,
                }
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    if load.maintenance_required:
        st.caption(
            "Read-only inspection made no storage change. Explicit maintenance is required "
            "before any quarantine or recovery mutation."
        )
    if load.has_valid_backup:
        st.warning(
            "A validated prior receipt is available below. It is not the latest attempt "
            "and does not by itself prove that its data is still retained or current."
        )
        _render_valid_receipt(
            load.backup_receipt or {},
            role="Validated prior receipt (not latest)",
        )
    else:
        render_refresh_recovery_panel((), title="Refresh receipt recovery details")


def _render_valid_receipt(receipt: dict[str, Any], *, role: str) -> None:
    st.success(
        f"{role} metadata passed schema and integrity validation. "
        "This validation does not declare every source healthy or current."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "receipt_role": role,
                    "receipt_id": receipt.get("receipt_id") or "Not recorded",
                    "refresh_action_id": receipt.get("refresh_action_id") or "Not recorded",
                    "loader_mode": receipt.get("loader_mode") or "Not recorded",
                    "recorded_outcome": receipt.get("overall_status") or "Not recorded",
                    "refresh_started": receipt.get("started_at_utc") or "Not recorded",
                    "refresh_finished": receipt.get("finished_at_utc") or "Not recorded",
                    "receipt_created": receipt.get("created_at_utc") or "Not recorded",
                    "integrity": "VALID",
                }
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    rows = [row for row in receipt.get("results", []) if isinstance(row, dict)]
    recovery_rows = [_receipt_recovery_row(row) for row in rows]
    recovery = (
        build_run_recovery_summary(
            recovery_rows,
            finished_at=str(receipt.get("finished_at_utc") or ""),
        ),
        *build_refresh_recovery_presentations(recovery_rows),
    )
    render_refresh_recovery_panel(recovery, title=f"{role} recovery details")

    with st.expander(f"{role} source lifecycle details", expanded=True):
        if not rows:
            st.info("Not enough information - no source receipt rows are available.")
            return
        display_rows = []
        for row in rows:
            display = dict(row)
            display["failure_context"] = _first_text(
                row,
                "user_explanation",
                "user_message",
                "last_result",
                "caveat",
                "error_summary",
            )
            display_rows.append(display)
        display = pd.DataFrame(display_rows).reindex(columns=LIFECYCLE_COLUMNS).fillna("")
        st.dataframe(display, width="stretch", hide_index=True)
        st.caption(
            "Latest successful receipt is historical success evidence. Last-known-good is "
            "shown only when explicit retained-data evidence and a validated matching prior "
            "receipt both exist. Blank means not established."
        )


def _first_text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return "No trustworthy failure context recorded."


def _receipt_recovery_row(row: dict[str, Any]) -> dict[str, Any]:
    adapted = dict(row)
    adapted["user_explanation"] = row.get("error_summary") or ""
    adapted["last_success_at"] = row.get("source_as_of_utc") or ""
    return adapted
