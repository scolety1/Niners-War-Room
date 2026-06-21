from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.draft_day_v1 import (
    filter_board_frame,
    render_board_metrics,
    render_final_board_table,
    render_source_of_truth_badge,
    stop_if_board_blocked,
)
from app.components.ui_framework import page_header
from src.services.draft_day_app_v1_service import load_frozen_board

bundle = load_frozen_board()

page_header(
    "Final Board / Dynasty Rankings",
    eyebrow="Draft-Day App V1",
    description=(
        "Frozen Final Draft Board V1 is the source of truth. Old dynasty ranking "
        "surfaces are YELLOW-HOLD and cannot override final_board_rank."
    ),
    status_items=(
        ("Frozen board source of truth", "safe"),
        ("No hidden sort", "safe"),
        ("Legacy rankings hold", "review"),
    ),
)
render_source_of_truth_badge(bundle)
stop_if_board_blocked(bundle)

render_board_metrics(bundle.frame)
filtered = filter_board_frame(bundle.frame, key_prefix="final_board_v1")
render_final_board_table(filtered, key="final_board_v1_table")

st.caption(
    "Display-only context columns remain display-only. The visible final_board_rank, "
    "final_tier, and position_rank columns are the board order for tomorrow."
)
