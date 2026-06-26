from __future__ import annotations

from pathlib import Path

from app.navigation import ALL_NAVIGATION_PAGES
from src.services.nfl_usage_evidence_review_page_service import (
    LIVE_SMOKE_PATH,
    REVIEW_ROOT,
    load_nfl_usage_evidence_review_data,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_nfl_usage_review_service_loads_summary_artifacts_only() -> None:
    data = load_nfl_usage_evidence_review_data()

    assert data.summary["sources_inventoried"] >= 8
    assert data.summary["raw_data_loaded"] == "no"
    assert data.summary["app_wiring_allowed"] == "no"
    assert data.summary["model_input_allowed"] == "no"
    assert data.summary["promotion_display_approved"] >= 1
    assert data.summary["promotion_backtest_status"] == "BACKTEST_BLOCKED_INSUFFICIENT_COVERAGE"
    assert data.promotion_decision_matrix["model_input_allowed"].astype(str).eq("no").all()
    assert data.promotion_decision_matrix["app_wiring_allowed"].astype(str).eq("no").all()
    assert str(REVIEW_ROOT).endswith("docs\\hq\\data_sources\\nfl_usage\\review_artifacts")
    assert "NWR_SHARED_DATA" not in str(LIVE_SMOKE_PATH)


def test_nfl_usage_review_route_is_hidden_and_read_only() -> None:
    route = next(
        page for page in ALL_NAVIGATION_PAGES if page.url_path == "nfl-usage-evidence-review"
    )
    page_text = (REPO_ROOT / "app" / route.file_path).read_text(encoding="utf-8")

    assert route.visible is False
    assert route.file_path == "pages/32_nfl_usage_evidence_review.py"
    assert "Review-only. This page does not feed rankings" in page_text
    assert "Promotion status shown here does not feed rankings" in page_text
    assert "load_nfl_usage_evidence_review_data" in page_text
    assert "NWR_SHARED_DATA" not in page_text
