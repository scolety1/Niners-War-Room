from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_future_pick_planning,
    render_planning_advanced_details,
)
from app.components.ui_framework import page_header  # noqa: E402

page_header(
    "Future Pick Planner",
    eyebrow="Team Planning",
    description=(
        "Keep one clear inventory of the future picks you own, acquired, sent, or still "
        "need to verify before building a trade or draft plan."
    ),
    status_items=(
        ("Guided pick entry", "safe"),
        ("Saved locally", "safe"),
        ("No automatic price", "review"),
    ),
)

render_future_pick_planning()
render_planning_advanced_details()
