from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.components.owner_mode import decision_cards, owner_intro  # noqa: E402
from app.components.post_release_status import render_save_status  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402
from src.services.governed_asset_registry_service import load_governed_asset_registry  # noqa: E402
from src.services.personal_workspace_service import (  # noqa: E402
    WorkspaceValidationError,
    create_workspace_backup,
    load_store,
    preview_workspace_restore,
    restore_workspace,
    save_scenario,
    scenario_source_status,
)
from src.services.post_release_usability_service import (  # noqa: E402
    initial_save_status,
    perform_workspace_write,
)

registry = load_governed_asset_registry(repo_root=ROOT)
assets = {row["asset_id"]: row for row in registry.rows}
asset_types = {key: row["asset_type"] for key, row in assets.items()}
saved = load_store("saved_scenarios")

page_header(
    "Scenario Playground",
    eyebrow="Save and compare hypothetical moves",
    description=(
        "Explore 'what if' trades, player comparisons, acquisitions, and alternate "
        "roster ideas. Save multiple versions without changing rankings or your real roster."
    ),
    status_items=(
        ("Restart-safe", "safe"),
        ("No automatic verdict", "safe"),
        ("Local backup", "review"),
    ),
)
owner_intro(
    "Pressure-test a move before it becomes a decision.",
    "Save alternate versions, name the team window, and compare what each option is "
    "trying to accomplish.",
)
decision_cards(
    (
        ("Contender swap", "Exchange future value for points or lineup certainty."),
        ("Rebuild pivot", "Exchange fragile or aging value for a longer runway."),
        ("Player fork", "Keep two plausible choices separate until the evidence changes."),
    )
)
render_save_status(initial_save_status(saved.status, saved.updated_at_utc))

section_label("Create a what-if scenario")
with st.form("saved-scenario-create"):
    kind = st.selectbox(
        "Scenario type",
        ("Trade idea", "Player choice", "Draft idea", "Asset research"),
    )
    title = st.text_input("Scenario title")
    selected = st.multiselect(
        "Governed assets",
        sorted(assets),
        format_func=lambda key: f"{assets[key]['asset_name']} · {assets[key]['asset_type']}",
    )
    notes = st.text_area("What would make this scenario work?", max_chars=20_000)
    team_window = st.selectbox(
        "Team-window context", ("Contending", "Balanced", "Rebuilding", "Custom/Unspecified")
    )
    submitted = st.form_submit_button("Save scenario", type="primary")

if submitted:
    try:
        payload = {}
        kind_key = {
            "Trade idea": "trading_lab",
            "Player choice": "player_compare",
            "Draft idea": "draft",
            "Asset research": "asset_explorer",
        }[kind]
        payload.update({"notes": notes, "team_window": team_window})
        write_status = perform_workspace_write(
            lambda: save_scenario(
                {
                    "scenario_id": f"scenario-{uuid4()}",
                    "scenario_type": kind_key,
                    "title": title,
                    "assets": selected,
                    "source_versions": registry.source_hashes,
                    "payload": payload,
                },
                asset_registry=asset_types,
            ),
            observer=render_save_status,
        )
        if write_status.state == "Saved":
            st.caption(f"Scenario ID: {write_status.result.record_id}")
            current_count = sum(assets[key]["asset_type"] == "Current Player" for key in selected)
            future_count = len(selected) - current_count
            if team_window == "Contending":
                effect = (
                    f"Composition check: {current_count} current players and {future_count} "
                    "rookie/pick assets. Test whether the move adds lineup certainty without "
                    "overpaying in future value."
                )
            elif team_window == "Rebuilding":
                effect = (
                    f"Composition check: {current_count} current players and {future_count} "
                    "rookie/pick assets. Test whether the move lengthens the asset window and "
                    "reduces fragile value."
                )
            else:
                effect = (
                    f"Composition check: {current_count} current players and {future_count} "
                    "rookie/pick assets. Compare the exact sides in Analyze Trade before using "
                    "this scenario as a recommendation."
                )
            st.info(effect)
    except WorkspaceValidationError as exc:
        st.error(f"Scenario blocked: {exc}")

section_label("Saved what-if scenarios")
st.dataframe(
    pd.DataFrame(
        {
            "Title": row.get("title"),
            "Type": row.get("scenario_type"),
            "Assets": ", ".join(
                assets.get(key, {}).get("asset_name", key) for key in row.get("assets", [])
            ),
            "Created": row.get("created_at_utc"),
            "Modified": row.get("modified_at_utc"),
            "Source Versions": len(row.get("source_versions", {})),
            "Source Status": (
                "Current"
                if scenario_source_status(row, registry.source_hashes) == "CURRENT"
                else "Stale or changed - review"
            ),
        }
        for row in saved.records
    ),
    hide_index=True,
    use_container_width=True,
)

with st.expander("Advanced workspace backup and restore"):
    if st.button("Create workspace backup"):
        backup = create_workspace_backup()
        st.success(f"Backup created: {backup.path} ({backup.file_count} stores)")
    backup_path = st.text_input("Existing backup folder for restore dry-run")
    if st.button("Run restore dry-run", disabled=not backup_path.strip()):
        preview = preview_workspace_restore(backup_path)
        (st.success if preview.valid else st.error)(preview.message)
    confirm_restore = st.checkbox(
        "Confirm restore of Personal Workspace stores from this verified backup"
    )
    if st.button("Restore Personal Workspace", disabled=not backup_path.strip()):
        result = restore_workspace(backup_path, confirmed=confirm_restore)
        if result.status == "RESTORED":
            st.success(
                "Personal Workspace restored after a safety backup. "
                "Canonical source data was not in restore scope."
            )
        else:
            st.error(f"Restore blocked: {result.message or result.status}")
