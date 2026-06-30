from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    render_future_pick_planning,
    render_guardrails,
)
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Future Pick Planning",
    eyebrow="Development Lab / Safe V0",
    description=(
        "Future pick and asset ledger for planning notes. It may read manual Draft Cockpit "
        "trade events, while keeping pick/trade context descriptive and manual."
    ),
    status_items=(
        ("Planning ledger", "review"),
        ("Display-only", "safe"),
        ("Manual context", "safe"),
    ),
)

render_future_pick_planning()

section_label("Guardrails")
render_guardrails()
