from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_guardrails,
    render_roster_weakness_tracker,
)
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Roster Weakness Tracker",
    eyebrow="Development Lab / Safe V0",
    description=(
        "Manual roster structure view for position counts, starter/depth coverage, and "
        "display-only notes. Decisions remain human/manual outside this page."
    ),
    status_items=(
        ("Display-only", "review"),
        ("Manual workflow", "safe"),
        ("Manual decisions", "safe"),
    ),
)

render_roster_weakness_tracker()

section_label("Guardrails")
render_guardrails()
