from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_planning_advanced_details,
    render_upcoming_draft_prep,
)
from app.components.ui_framework import page_header  # noqa: E402

page_header(
    "Upcoming Draft Prep",
    eyebrow="Draft Tools",
    description=(
        "Build your draft plan in order: confirm the setup, identify roster needs, inventory "
        "your picks, create a watchlist, and rehearse the scenarios that could reach you."
    ),
    status_items=(
        ("Guided seven-step plan", "safe"),
        ("Saved locally", "safe"),
        ("Links to Mock Drafts", "review"),
    ),
)

render_upcoming_draft_prep()
render_planning_advanced_details()
