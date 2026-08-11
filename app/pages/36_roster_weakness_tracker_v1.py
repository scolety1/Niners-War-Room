from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_planning_advanced_details,
    render_roster_weakness_tracker,
)
from app.components.ui_framework import page_header  # noqa: E402

page_header(
    "Roster Planner",
    eyebrow="Team Planning",
    description=(
        "Add your roster to see where you are thin by position, age, and dynasty value. "
        "Use the result to set priorities before trades, waivers, or the draft."
    ),
    status_items=(
        ("Guided roster entry", "safe"),
        ("Saves locally", "safe"),
        ("You make the decision", "review"),
    ),
)

render_roster_weakness_tracker()
render_planning_advanced_details()
