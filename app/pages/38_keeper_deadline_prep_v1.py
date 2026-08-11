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
    "Keeper Deadline Prep",
    eyebrow="Team Planning",
    description=(
        "Record the league deadline, work through the keeper checklist, and save the "
        "questions you need answered before locking your choices."
    ),
    status_items=(
        ("Trackable checklist", "safe"),
        ("Saved locally", "safe"),
        ("You lock the choices", "review"),
    ),
)

render_deadline_prep("keeper_deadline_prep", "Keeper Deadline Prep")
render_planning_advanced_details()
