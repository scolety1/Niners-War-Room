from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

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

registry = load_governed_asset_registry(repo_root=ROOT)
assets = {row["asset_id"]: row for row in registry.rows}
asset_types = {key: row["asset_type"] for key, row in assets.items()}
saved = load_store("saved_scenarios")

page_header(
    "Saved Scenarios",
    eyebrow="Local workspace context",
    description=(
        "Save manual trade, compare, draft, and Asset Explorer context "
        "without a verdict or canonical mutation."
    ),
    status_items=(
        ("Restart-safe", "safe"),
        ("No automatic verdict", "safe"),
        ("Local backup", "review"),
    ),
)

section_label("Save a scenario")
with st.form("saved-scenario-create"):
    kind = st.selectbox(
        "Scenario type", ("trading_lab", "player_compare", "draft", "asset_explorer")
    )
    title = st.text_input("Scenario title")
    selected = st.multiselect(
        "Governed assets",
        sorted(assets),
        format_func=lambda key: f"{assets[key]['asset_name']} · {assets[key]['asset_type']}",
    )
    notes = st.text_area("Your notes", max_chars=20_000)
    team_window = st.selectbox(
        "Team-window context", ("Contending", "Balanced", "Rebuilding", "Custom/Unspecified")
    )
    filter_json = st.text_area("Optional filters / queue JSON", value="{}")
    submitted = st.form_submit_button("Save scenario", type="primary")

if submitted:
    try:
        payload = json.loads(filter_json)
        payload.update({"notes": notes, "team_window": team_window})
        result = save_scenario(
            {
                "scenario_id": f"scenario-{uuid4()}",
                "scenario_type": kind,
                "title": title,
                "assets": selected,
                "source_versions": registry.source_hashes,
                "payload": payload,
            },
            asset_registry=asset_types,
        )
        st.success(f"Scenario saved locally: {result.record_id}")
    except (json.JSONDecodeError, WorkspaceValidationError) as exc:
        st.error(f"Scenario blocked: {exc}")

section_label("Saved scenarios")
st.dataframe(
    pd.DataFrame(
        {
            "Title": row.get("title"),
            "Type": row.get("scenario_type"),
            "Assets": ", ".join(row.get("assets", [])),
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

with st.expander("Backup and restore dry-run"):
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
