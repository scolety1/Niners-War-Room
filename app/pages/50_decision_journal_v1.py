from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.components.post_release_status import render_save_status  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.governed_asset_registry_service import load_governed_asset_registry  # noqa: E402
from src.services.outcome_v3_display_service import load_outcome_v3_display  # noqa: E402
from src.services.personal_workspace_service import (  # noqa: E402
    DECISION_STATUSES,
    DECISION_TYPES,
    WorkspaceValidationError,
    archive_decision,
    create_decision,
    delete_decision,
    load_store,
    mark_decision_reviewed,
    reschedule_decision_followup,
    update_decision,
)
from src.services.post_release_usability_service import (  # noqa: E402
    build_followup_dashboard,
    initial_save_status,
    perform_workspace_write,
)

registry = load_governed_asset_registry(repo_root=ROOT)
assets = {row["asset_id"]: row for row in registry.rows}
asset_types = {key: row["asset_type"] for key, row in assets.items()}
personal = {row["asset_id"]: row for row in load_store("personal_board").records}
journal = load_store("decision_journal")
outcome = load_outcome_v3_display()

page_header(
    "Decision Tracker",
    eyebrow="Track moves and learn from the outcome",
    description=(
        "Record trades, draft choices, and add/drop decisions alongside NWR's advice and "
        "your final choice, then revisit the result later. NWR never performs the move."
    ),
    status_items=(
        ("Local-only", "safe"),
        ("Immutable source snapshot", "safe"),
        ("No fabricated result", "review"),
    ),
)
render_save_status(initial_save_status(journal.status, journal.updated_at_utc))

section_label("Follow-up dashboard")
dashboard = build_followup_dashboard(journal.records)
followup_metrics = st.columns(6)
for column, label, value in zip(
    followup_metrics,
    ("Due today", "Overdue", "Upcoming", "Recent", "Archived", "Missing date"),
    (
        len(dashboard.due_today),
        len(dashboard.overdue),
        len(dashboard.upcoming),
        len(dashboard.recent),
        len(dashboard.archived),
        len(dashboard.missing_date),
    ),
    strict=True,
):
    column.metric(label, value)

all_decisions = list(journal.records)
if all_decisions:
    with st.form("decision-followup-action"):
        action_id = st.selectbox(
            "Decision receipt",
            [row["decision_id"] for row in all_decisions],
        )
        action = st.selectbox(
            "Follow-up action",
            ("Mark reviewed", "Reschedule", "Archive", "Open receipt", "Create retrospective note"),
        )
        new_follow_up = st.date_input("New follow-up date", value=None)
        retrospective = st.text_area("Retrospective note", max_chars=20_000)
        confirm_action = st.checkbox("Confirm archive when Archive is selected")
        run_action = st.form_submit_button("Apply follow-up action")
    if run_action:
        selected_receipt = next(row for row in all_decisions if row["decision_id"] == action_id)
        if action == "Open receipt":
            st.json(selected_receipt)
        else:

            def _write_followup_action():
                if action == "Mark reviewed":
                    return mark_decision_reviewed(action_id)
                if action == "Reschedule":
                    if new_follow_up is None:
                        raise WorkspaceValidationError("Choose a new follow-up date.")
                    return reschedule_decision_followup(action_id, new_follow_up.isoformat())
                if action == "Archive":
                    return archive_decision(action_id, confirmed=confirm_action)
                if not retrospective.strip():
                    raise WorkspaceValidationError("Enter a retrospective note.")
                return update_decision(action_id, {"retrospective_notes": retrospective})

            followup_status = perform_workspace_write(
                _write_followup_action,
                observer=render_save_status,
            )
            if followup_status.state == "Saved":
                st.caption("Follow-up receipt updated without an outcome judgment.")

dashboard_tabs = st.tabs(("Due today", "Overdue", "Upcoming", "Missing date", "Recent", "Archived"))
for tab, subset in zip(
    dashboard_tabs,
    (
        dashboard.due_today,
        dashboard.overdue,
        dashboard.upcoming,
        dashboard.missing_date,
        dashboard.recent,
        dashboard.archived,
    ),
    strict=True,
):
    with tab:
        st.dataframe(
            pd.DataFrame(
                {
                    "Decision ID": row.get("decision_id"),
                    "Type": row.get("decision_type"),
                    "Status": row.get("status"),
                    "Assets": ", ".join(row.get("assets", [])),
                    "Team Window": row.get("team_window"),
                    "Follow-up": row.get("follow_up_date"),
                    "Last reviewed": row.get("last_reviewed_at_utc"),
                }
                for row in subset
            ),
            hide_index=True,
            use_container_width=True,
        )

section_label("Create a decision receipt")
with st.form("decision-journal-create"):
    decision_type = st.selectbox("Decision type", sorted(DECISION_TYPES))
    status = st.selectbox("Status", sorted(DECISION_STATUSES - {"Archived"}))
    selected = st.multiselect(
        "Governed assets",
        sorted(assets),
        format_func=lambda key: f"{assets[key]['asset_name']} · {assets[key]['asset_type']}",
    )
    rationale = st.text_area("Your rationale", max_chars=20_000)
    expected = st.text_area("Your expected outcome", max_chars=20_000)
    confidence = st.selectbox("Your confidence", ("Unspecified", "Low", "Medium", "High"))
    team_window = st.selectbox(
        "Team-window context", ("Contending", "Balanced", "Rebuilding", "Custom/Unspecified")
    )
    occurred = st.date_input("Occurred date (optional)", value=None)
    follow_up = st.date_input("Follow-up date", value=None)
    submitted = st.form_submit_button("Save decision receipt", type="primary")

if submitted:

    def _source_version(key: str) -> str:
        asset = assets[key]
        if asset["asset_type"] == "Current Player":
            return registry.source_hashes.get("Finished V1", "governed-context")
        if asset["asset_type"] == "Blocked Rookie":
            return registry.source_hashes.get("Blocked Rookies", "governed-context")
        if asset["asset_type"] == "Rookie Review":
            return registry.source_hashes.get("Rookie Review", "governed-context")
        return "frozen-draft-context"

    snapshot = {
        key: {
            "asset_type": assets[key]["asset_type"],
            "source_label": assets[key]["source_label"],
            "authority_status": assets[key]["authority_status"],
            "visible_rank": assets[key]["rank_value"],
            "visible_score": assets[key]["score_value"],
            "warnings": assets[key]["warnings"],
            "source_version": _source_version(key),
            "outcome_v3": (
                outcome.frame.loc[
                    outcome.frame["player_id"].astype(str).eq(key.removeprefix("current:")),
                    [
                        "field_id",
                        "horizon",
                        "probability_display",
                        "confidence",
                        "evidence_state",
                        "reason_code",
                    ],
                ].to_dict("records")
                if outcome.loaded and key.startswith("current:")
                else []
            ),
        }
        for key in selected
    }
    personal_snapshot = {key: personal.get(key, {}) for key in selected}
    try:
        write_status = perform_workspace_write(
            lambda: create_decision(
                {
                    "decision_id": f"decision-{uuid4()}",
                    "decision_type": decision_type,
                    "status": status,
                    "assets": selected,
                    "source_snapshot": snapshot,
                    "personal_snapshot": personal_snapshot,
                    "rationale": rationale,
                    "expected_outcome": expected,
                    "confidence": confidence,
                    "team_window": team_window,
                    "occurred_at": occurred.isoformat() if occurred else "",
                    "follow_up_date": follow_up.isoformat() if follow_up else "",
                    "retrospective_notes": "",
                },
                asset_registry=asset_types,
            ),
            observer=render_save_status,
        )
        if write_status.state == "Saved":
            st.caption(f"Receipt ID: {write_status.result.record_id}")
    except WorkspaceValidationError as exc:
        st.error(f"Receipt blocked: {exc}")

section_label("Decision history")
rows = list(journal.records)
filter_columns = st.columns(4)
status_filter = filter_columns[0].multiselect(
    "Filter status", sorted(DECISION_STATUSES), default=sorted(DECISION_STATUSES)
)
type_filter = filter_columns[1].multiselect(
    "Filter decision type", sorted(DECISION_TYPES), default=sorted(DECISION_TYPES)
)
asset_query = filter_columns[2].text_input("Asset ID or tag contains")
team_filter = filter_columns[3].multiselect(
    "Team window",
    sorted({str(row.get("team_window", "")) for row in rows if row.get("team_window")}),
)
followups_due = st.checkbox("Follow-ups due only")
show_archived = st.checkbox("Show archived receipts", value=False)
rows = [
    row
    for row in rows
    if row.get("status") in status_filter
    and row.get("decision_type") in type_filter
    and (not team_filter or row.get("team_window") in team_filter)
]
if asset_query.strip():
    needle = asset_query.casefold().strip()
    rows = [row for row in rows if needle in str(row).casefold()]
if followups_due:
    today = pd.Timestamp.now(tz="UTC").date().isoformat()
    rows = [row for row in rows if row.get("follow_up_date") and row["follow_up_date"] <= today]
if not show_archived:
    rows = [row for row in rows if row.get("status") != "Archived"]
st.dataframe(
    pd.DataFrame(
        {
            "Decision ID": row.get("decision_id"),
            "Type": row.get("decision_type"),
            "Status": row.get("status"),
            "Created": row.get("created_at_utc"),
            "Assets": ", ".join(row.get("assets", [])),
            "Team Window": row.get("team_window"),
            "Follow-up": row.get("follow_up_date"),
            "Rationale": row.get("rationale"),
        }
        for row in rows
    ),
    hide_index=True,
    use_container_width=True,
)
if rows:
    archive_id = st.selectbox("Decision to archive", [row["decision_id"] for row in rows])
    confirm = st.checkbox("Confirm archive; the receipt remains preserved")
    if st.button("Archive decision"):
        result = archive_decision(archive_id, confirmed=confirm)
        if result.status == "UPDATED":
            st.success("Decision archived without deleting its receipt.")
        else:
            st.warning("Archive requires explicit confirmation.")

archived = [row for row in journal.records if row.get("status") == "Archived"]
with st.expander("Permanent deletion of an archived receipt"):
    st.warning("Permanent deletion cannot be undone. A backup is created before the write.")
    delete_id = st.selectbox(
        "Archived decision to delete",
        [row["decision_id"] for row in archived],
        disabled=not archived,
    )
    confirm_delete = st.checkbox("Confirm permanent deletion of this archived receipt")
    if st.button("Permanently delete archived receipt", disabled=not archived):
        result = delete_decision(delete_id, confirmed=confirm_delete)
        if result.status == "DELETED":
            st.success("Archived receipt permanently deleted after backup.")
        else:
            st.warning("Permanent deletion requires explicit confirmation.")
