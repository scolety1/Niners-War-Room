from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    load_expanded_draftable_player_pool,
    load_frozen_board,
)
from src.services.draft_day_runtime_state_service import (
    export_runtime_state,
    load_latest_runtime_state,
    preview_runtime_state_import,
    restore_runtime_state_from_json_if_confirmed,
    runtime_paths,
)
from src.services.post_draft_mode_service import (
    MARKET_DISPLAY_ONLY_LABEL,
    NOT_ENOUGH_INFORMATION,
    RUNTIME_SOURCE_LABEL,
    build_post_draft_summary,
    post_draft_summary_export,
)

page_header(
    "Post-Draft Mode",
    eyebrow="Draft-Day App V2",
    description=(
        "Recap local draft picks, manually recorded trades, value context, and follow-up "
        "work. Runtime state is audit/display data, not official source truth."
    ),
    status_items=(
        ("Runtime audit", "review"),
        ("Market display-only", "safe"),
        ("No rank mutation", "safe"),
    ),
)
st.markdown(
    '<a href="/drafting-mode" target="_self">Back to Drafting Mode</a>',
    unsafe_allow_html=True,
)
st.caption(
    "Deep tool: runtime audit and recap. Runtime state is not official source truth and does "
    "not mutate ranks, tiers, or latest files."
)

mode = st.radio("Draft session", ["Live", "Mock"], horizontal=True, key="post_draft_mode")
runtime_mode = mode.lower()

if st.button("Load latest draft state", key="post_draft_load_latest"):
    st.session_state[f"post_draft_state_{runtime_mode}"] = load_latest_runtime_state(
        mode=runtime_mode
    )
    st.success("Loaded latest local runtime state.")

state_key = f"post_draft_state_{runtime_mode}"
if state_key not in st.session_state:
    st.session_state[state_key] = load_latest_runtime_state(mode=runtime_mode)

uploaded = st.file_uploader(
    "Upload/import draft state JSON",
    type=["json"],
    key=f"post_draft_upload_{runtime_mode}",
)
if uploaded is not None:
    payload = uploaded.getvalue()
    preview = preview_runtime_state_import(payload, mode=runtime_mode)
    if preview.valid:
        st.caption("Import preview. Confirm restore before overwriting local runtime state.")
        st.dataframe(
            pd.DataFrame([preview.summary]),
            use_container_width=True,
            hide_index=True,
            key=f"post_draft_import_preview_{runtime_mode}",
        )
        for warning in preview.warnings:
            st.warning(warning)
    else:
        for warning in preview.warnings:
            st.error(warning)
    confirm_import = st.checkbox(
        "Confirm restore imported JSON",
        key=f"post_draft_confirm_import_{runtime_mode}",
        help="Required before imported JSON overwrites local runtime state.",
    )
    try:
        if st.button("Restore imported JSON", key=f"post_draft_restore_{runtime_mode}"):
            st.session_state[state_key] = restore_runtime_state_from_json_if_confirmed(
                payload,
                confirmed=confirm_import,
                current_state=st.session_state[state_key],
                root=None,
                draft_id=str(
                    st.session_state[state_key].get("draft_session_id")
                    or st.session_state[state_key].get("draft_id")
                    or "draft_day_v2"
                ),
                mode=runtime_mode,
            )
            if not confirm_import:
                st.warning("Check Confirm restore imported JSON before overwriting local state.")
            else:
                st.success("Imported draft state JSON into local runtime state.")
    except (ValueError, TypeError, OSError) as exc:
        st.error(f"Could not import draft state JSON: {exc}")

bundle = load_frozen_board()
player_context = (
    load_expanded_draftable_player_pool(bundle.frame) if bundle.loaded else pd.DataFrame()
)
summary = build_post_draft_summary(
    st.session_state[state_key],
    player_context=player_context,
    include_market_context=True,
)

metric_cols = st.columns(5)
metric_cols[0].metric("Drafted", summary.metrics["drafted_count"])
metric_cols[1].metric("Trades", summary.metrics["trade_count"])
metric_cols[2].metric("Events", summary.metrics["event_count"])
metric_cols[3].metric("Mode", summary.metrics["mode"])
metric_cols[4].metric("Last updated", summary.metrics["last_updated"] or "Not loaded")

st.caption(
    f"{RUNTIME_SOURCE_LABEL}. {MARKET_DISPLAY_ONLY_LABEL}. "
    "Confirm all picks and trades against official league history before model/backtest use."
)

control_cols = st.columns([1, 1, 2])
if control_cols[0].button("Export runtime log", key="post_draft_export_runtime"):
    exports = export_runtime_state(st.session_state[state_key])
    st.success("Exported: " + " | ".join(str(path) for path in exports.values()))

control_cols[1].download_button(
    "Download post-draft summary JSON",
    data=post_draft_summary_export(summary),
    file_name=f"nwr_post_draft_summary_{runtime_mode}.json",
    mime="application/json",
    key="post_draft_summary_download",
)
control_cols[2].caption(
    "Downloads and runtime exports are local review artifacts. They do not mutate ranks, "
    "tier assignments, latest files, or source-truth artifacts."
)

st.subheader("Draft Recap")
if summary.draft_recap.empty:
    st.info("No pick events recorded for this draft session yet.")
else:
    st.dataframe(
        summary.draft_recap.astype(str),
        use_container_width=True,
        hide_index=True,
        key="post_draft_pick_recap",
    )

st.subheader("Trade Recap")
if summary.trade_recap.empty:
    st.info("No trade events recorded for this draft session yet.")
else:
    st.dataframe(
        summary.trade_recap.astype(str),
        use_container_width=True,
        hide_index=True,
        key="post_draft_trade_recap",
    )

st.subheader("Value / Audit Cards")
if summary.value_audit.empty:
    st.warning(NOT_ENOUGH_INFORMATION)
else:
    audit_cols = st.columns(min(3, len(summary.value_audit)))
    for index, row in enumerate(summary.value_audit.to_dict("records")):
        with audit_cols[index % len(audit_cols)]:
            st.markdown(f"**{row.get('Audit Item', '')}**")
            st.write(row.get("Result") or NOT_ENOUGH_INFORMATION)
            st.caption(row.get("Guardrail") or "")

st.subheader("Roster Outcome / Position Shape")
st.caption(
    "Position shape is based on this runtime draft session only. "
    "Roster context is not treated as loaded unless a separate roster source is wired."
)
st.dataframe(
    summary.position_shape.astype(str),
    use_container_width=True,
    hide_index=True,
    key="post_draft_position_shape",
)

st.subheader("Lessons / Next Actions")
for action in summary.next_actions:
    st.markdown(f"- {action}")

with st.expander("Missing data warnings", expanded=bool(summary.missing_data_warnings)):
    if summary.missing_data_warnings:
        for warning in summary.missing_data_warnings:
            st.warning(warning)
    else:
        st.success("No missing-data warnings from the post-draft summary builder.")

with st.expander("Event log", expanded=False):
    if summary.event_log.empty:
        st.info("No runtime events recorded yet.")
    else:
        st.dataframe(
            summary.event_log.astype(str),
            use_container_width=True,
            hide_index=True,
            key="post_draft_event_log",
        )

with st.expander("Runtime paths / display-only guardrails", expanded=False):
    paths = runtime_paths()
    st.caption(f"Runtime root: {paths.root}")
    st.caption(f"State directory: {paths.state_dir}")
    st.caption(f"Export directory: {paths.export_dir}")
    st.caption("Runtime JSON is local-only under C:\\NWR_SHARED_DATA and must not be tracked.")
    st.caption("Market baseline context, when matched, is display-only and not model input.")
    st.caption("Frozen board is a baseline checkpoint only.")
