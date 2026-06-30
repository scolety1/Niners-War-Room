from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import render_deadline_prep, render_guardrails  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Trade Deadline Prep",
    eyebrow="Development Lab / Safe V0",
    description=(
        "Manual trade-deadline checklist and notes with links to existing review tools. "
        "It records factual/manual context only."
    ),
    status_items=(
        ("Checklist only", "review"),
        ("Manual notes", "safe"),
        ("Display-only", "safe"),
    ),
)

render_deadline_prep("trade_deadline_prep", "Trade Deadline Prep")

section_label("Related Review Pages")

cols = st.columns(2)
cols[0].link_button("Open Trading Lab", "/trading-lab", use_container_width=True)
cols[1].link_button("Open Player Compare", "/player-compare", use_container_width=True)

section_label("Guardrails")
render_guardrails()
