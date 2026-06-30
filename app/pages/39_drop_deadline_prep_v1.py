from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import render_deadline_prep, render_guardrails  # noqa: E402
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Drop Deadline Prep",
    eyebrow="Development Lab / Safe V0",
    description=(
        "Manual drop-deadline checklist and review notes. It records missing data and "
        "human-review status only."
    ),
    status_items=(
        ("Checklist only", "review"),
        ("Manual notes", "safe"),
        ("Human review", "safe"),
    ),
)

render_deadline_prep("drop_deadline_prep", "Drop Deadline Prep")

section_label("Guardrails")
render_guardrails()
