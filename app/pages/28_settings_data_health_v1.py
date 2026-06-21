from __future__ import annotations

# ruff: noqa: E402
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    render_lane_status_table,
    render_source_of_truth_badge,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import (
    APP_PROP_ROOT,
    DISPLAY_ONLY_COLUMNS,
    EXPECTED_PINNED_MANIFEST_HASH,
    LOCAL_FROZEN_BOARD_ROOT,
    PINNED_SNAPSHOT_MANIFEST,
    draft_day_status_rows,
    load_frozen_board,
    pinned_manifest_hash,
)

bundle = load_frozen_board()

page_header(
    "Settings / Data Health",
    eyebrow="Draft-Day App V1",
    description="Local source paths, guardrails, lane status, and no-deploy access instructions.",
    status_items=(("Local only", "safe"), ("No deploy", "safe"), ("Vendor hold", "review")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

try:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    commit = "unknown"

st.subheader("App Status")
status_rows = draft_day_status_rows(bundle)
status_rows.append({"check": "Repo commit", "status": "INFO", "detail": commit})
status_rows.append(
    {
        "check": "Pinned expected hash",
        "status": "INFO",
        "detail": EXPECTED_PINNED_MANIFEST_HASH,
    }
)
status_rows.append(
    {
        "check": "Pinned observed hash",
        "status": "GREEN"
        if pinned_manifest_hash() == EXPECTED_PINNED_MANIFEST_HASH
        else "YELLOW-HOLD",
        "detail": pinned_manifest_hash() or "missing",
    }
)
st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)

st.subheader("Lane Prop Status")
render_lane_status_table()

st.subheader("Source Paths")
st.code(
    "\n".join(
        [
            f"Frozen package: {LOCAL_FROZEN_BOARD_ROOT}",
            f"App prop root: {APP_PROP_ROOT}",
            f"Pinned manifest: {PINNED_SNAPSHOT_MANIFEST}",
        ]
    )
)

st.subheader("Display-Only Context")
st.dataframe(
    pd.DataFrame({"display_only_field": [field for field in DISPLAY_ONLY_COLUMNS]}),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Local Access")
st.markdown(
    """
    - Use `streamlit run app/main.py` for the connected local app.
    - Use the repo-safe static export only as a fallback.
    - No hosted deployment, public access, or GitHub Pages is enabled by this app contract.
    - Vendor research remains YELLOW-HOLD and is not a safe board signal.
    """
)
