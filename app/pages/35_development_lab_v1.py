from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.development_lab import (  # noqa: E402
    load_statuses,
    render_blocked_tools_table,
    render_bulk_lab_state_controls,
    render_development_lab_readiness,
    render_future_tool_gate_badges,
    render_guardrails,
    render_lab_links,
    render_lab_warning,
    render_local_lab_state_status,
    render_refresh_health_waiting_panel,
    render_safe_v0_table,
    render_tool_status_metrics,
)
from app.components.ui_framework import page_header, section_label  # noqa: E402

page_header(
    "Lab Home",
    eyebrow="Development Lab",
    description=(
        "Control board for Safe V0 manual/display tools, blocked gates, and future-only ideas. "
        "Everything here is display-only/manual, not model truth or source truth."
    ),
    status_items=(
        ("Safe V0 only", "review"),
        ("No model input", "safe"),
        ("No source truth", "safe"),
    ),
)

render_lab_warning()

statuses = load_statuses()
render_tool_status_metrics(statuses)

section_label("Safe V0 Tools In The Lab")
render_safe_v0_table(statuses)
render_lab_links()

section_label("Manual Readiness / Saved State")
render_development_lab_readiness(statuses)

section_label("NFLVerse Display Context Status")
render_refresh_health_waiting_panel()

section_label("Local Lab State")
render_local_lab_state_status()
render_bulk_lab_state_controls()

section_label("Future Tool Gate Badges")
render_future_tool_gate_badges(statuses)

section_label("Blocked / Gated Tools")
render_blocked_tools_table(statuses)

section_label("Guardrails")
render_guardrails()
