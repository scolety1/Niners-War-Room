from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import render_deadline_prep, render_guardrails  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Keeper Deadline Prep",
    eyebrow="Development Lab / Safe V0",
    description=(
        "Manual keeper-deadline checklist and notes. It does not produce automatic keeper "
        "recommendations or model-derived keep/drop advice."
    ),
    status_items=(
        ("Checklist only", "review"),
        ("Manual notes", "safe"),
        ("No keeper advice", "safe"),
    ),
)

render_deadline_prep("keeper_deadline_prep", "Keeper Deadline Prep")

section_label("Guardrails")
render_guardrails()
