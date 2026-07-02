from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_alternatives_preview import (  # noqa: E402
    render_alternative_a,
    render_alternative_b,
    render_alternative_c,
    render_current_ui_reference_notes,
    render_future_page_scope,
    render_preview_banner,
    render_preview_styles,
    render_side_by_side_comparison,
)
from app.components.ui_framework import page_header  # noqa: E402

render_preview_styles()

page_header(
    "UI Alternatives Preview",
    eyebrow="Review-only UI branch / NWR UI Alternatives Preview V1",
    description=(
        "Side-by-side static preview of possible UI upgrades for Tim to inspect. "
        "This route is additive and reversible; it does not change rankings, models, "
        "source truth, runtime data, or default page behavior."
    ),
    status_items=(
        ("Review-only", "review"),
        ("No rank logic changes", "safe"),
        ("No model/source-truth changes", "safe"),
    ),
)

render_preview_banner()
render_current_ui_reference_notes()
render_alternative_a()
render_alternative_b()
render_alternative_c()
render_side_by_side_comparison()
render_future_page_scope()
