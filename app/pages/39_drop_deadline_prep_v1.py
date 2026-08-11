from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_deadline_prep,
    render_planning_advanced_details,
)
from app.components.ui_framework import page_header  # noqa: E402

page_header(
    "Drop Deadline Prep",
    eyebrow="Team Planning",
    description=(
        "Capture the deadline, list the roster questions that still matter, and complete "
        "the final checks before making any cuts."
    ),
    status_items=(
        ("Trackable checklist", "safe"),
        ("Saved locally", "safe"),
        ("You make the cuts", "review"),
    ),
)

render_deadline_prep("drop_deadline_prep", "Drop Deadline Prep")
render_planning_advanced_details()
