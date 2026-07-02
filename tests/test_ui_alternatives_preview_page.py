from __future__ import annotations

import py_compile
from pathlib import Path

from app.navigation import ALL_NAVIGATION_PAGES

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
PAGE_PATH = APP_DIR / "pages" / "45_ui_alternatives_preview_v1.py"
COMPONENT_PATH = APP_DIR / "components" / "ui_alternatives_preview.py"


def test_ui_alternatives_preview_route_is_visible_review_page() -> None:
    route = next(
        page for page in ALL_NAVIGATION_PAGES if page.url_path == "ui-alternatives-preview"
    )
    page_text = PAGE_PATH.read_text(encoding="utf-8")

    assert route.visible is True
    assert route.title == "UI Alternatives Preview"
    assert route.file_path == "pages/45_ui_alternatives_preview_v1.py"
    assert "NWR UI Alternatives Preview V1" in page_text
    assert "Review-only" in page_text
    assert "No rank logic changes" in page_text
    assert "No model/source-truth changes" in page_text


def test_ui_alternatives_preview_page_and_component_compile() -> None:
    py_compile.compile(str(PAGE_PATH), doraise=True)
    py_compile.compile(str(COMPONENT_PATH), doraise=True)


def test_ui_alternatives_preview_contains_required_sections() -> None:
    component_text = COMPONENT_PATH.read_text(encoding="utf-8")

    for section in (
        "Current UI reference notes",
        "Alternative A: Compact Review Cards",
        "Alternative B: Evidence-First Layout",
        "Alternative C: Lab Console Layout",
        "Side-by-side comparison",
    ):
        assert section in component_text

    assert component_text.count("PreviewAlternative(") == 3
    for title in (
        'title="Compact Review Cards"',
        'title="Evidence-First Layout"',
        'title="Lab Console Layout"',
        '"Alternative": "A: Compact Review Cards"',
        '"Alternative": "B: Evidence-First Layout"',
        '"Alternative": "C: Lab Console Layout"',
    ):
        assert title in component_text


def test_ui_alternatives_preview_guardrails_are_static_and_isolated() -> None:
    combined_text = "\n".join(
        [
            PAGE_PATH.read_text(encoding="utf-8"),
            COMPONENT_PATH.read_text(encoding="utf-8"),
        ]
    )

    for phrase in (
        "No production formula changes.",
        "No model training or tuning.",
        "No rankings logic changes and no hidden sort.",
        "No recommendations and no source-truth promotion.",
        "No runtime data source changes.",
        "No candidate formula output is wired into production pages.",
    ):
        assert phrase in combined_text

    for forbidden_import in (
        "from src.models",
        "from src.services",
        "from src.data",
        "load_dynasty_rankings",
        "display_unified_player_board_frame",
        "sort_values(",
        "latest_candidate",
        "latest_approved",
        "NWR_SHARED_DATA",
    ):
        assert forbidden_import not in combined_text


def test_ui_alternatives_preview_names_future_candidate_pages_only() -> None:
    component_text = COMPONENT_PATH.read_text(encoding="utf-8")

    for page in (
        "Rankings",
        "Player Compare",
        "Trading Lab",
        "Development Lab",
        "Settings / Data Health",
        "Draft Room review sections",
    ):
        assert page in component_text
