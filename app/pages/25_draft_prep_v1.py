from __future__ import annotations

# ruff: noqa: E402
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
    LOCAL_APP_PROP_ROOT,
    LOCAL_FROZEN_BOARD_ROOT,
    REPO_SAFE_APP_PROP_ROOT,
    REPO_SAFE_FROZEN_BOARD_PATH,
    draft_day_status_rows,
    load_frozen_board,
)

bundle = load_frozen_board()

page_header(
    "Draft Prep",
    eyebrow="Draft-Day App V1",
    description="Tomorrow checklist, source paths, fallback files, and lane prop readiness.",
    status_items=(("Checklist", "safe"), ("Lane props can be YELLOW-HOLD", "review")),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

st.subheader("Readiness Checklist")
st.dataframe(pd.DataFrame(draft_day_status_rows(bundle)), use_container_width=True, hide_index=True)

st.subheader("Lane Prop Status")
render_lane_status_table()

st.subheader("What To Use Tomorrow")
st.markdown(
    """
    - Use the frozen Final Draft Board V1 only as a protected baseline/checkpoint.
    - Use the expanded draftable pool and runtime draft state for on-clock availability.
    - Use Draft Cockpit session marking only as a local taken-list aid.
    - Treat missing lane prop pages as YELLOW-HOLD, not blockers to using the board.
    - Do not use vendor research hold fields as safe board signals.
    """
)

st.subheader("Local Paths")
st.code(
    "\n".join(
        [
            f"Local frozen package: {LOCAL_FROZEN_BOARD_ROOT}",
            f"Repo-safe frozen copy: {REPO_SAFE_FROZEN_BOARD_PATH}",
            "Static fallback: docs/draft_day_exports/final_board_v1_20260622/OPEN_THIS_FIRST.html",
            "Frozen zip fallback: C:\\NWR_SHARED_DATA\\draft_day_exports"
            "\\nwr_final_draft_board_v1_frozen_20260622.zip",
            "Local Streamlit URL: http://127.0.0.1:8501/rankings",
            "Env override data root: NWR_DRAFT_DAY_DATA_ROOT",
            "Env override prop root: NWR_DRAFT_DAY_APP_PROPS_ROOT",
            f"Local app prop root: {LOCAL_APP_PROP_ROOT}",
            f"Repo app prop fallback: {REPO_SAFE_APP_PROP_ROOT}",
        ]
    )
)
