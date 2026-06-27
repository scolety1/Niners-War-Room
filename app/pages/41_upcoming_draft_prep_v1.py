from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_guardrails,
    render_upcoming_draft_prep,
)
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Upcoming Draft Prep",
    eyebrow="Development Lab / Safe V0",
    description=(
        "Manual planning workspace for the next draft: setup checks, roster need notes, pick "
        "inventory, watchlist placeholders, mock scenarios, open questions, and data readiness."
    ),
    status_items=(
        ("Manual planning", "review"),
        ("No rookie ranks", "safe"),
        ("No recommendations", "safe"),
    ),
)

render_upcoming_draft_prep()

section_label("Guardrails")
render_guardrails()
