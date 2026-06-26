from __future__ import annotations

from pathlib import Path

from app.navigation import ALL_NAVIGATION_PAGES
from src.services.evidence_integration_review_service import (
    REGISTRY_PATH,
    load_evidence_integration_review_data,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evidence_integration_review_service_loads_committed_registry_only() -> None:
    data = load_evidence_integration_review_data()

    assert len(data.registry) >= 13
    assert data.summary["model_input_enabled"] == "no"
    assert data.summary["app_wiring_enabled"] == "no"
    assert data.summary["training_enabled"] == "no"
    assert data.summary["raw_data_tracked"] == "no"
    assert data.guardrails["status"].astype(str).eq("GREEN").all()
    assert str(REGISTRY_PATH).endswith(
        "docs\\hq\\integration\\evidence_status_registry_v1_20260626.csv"
    )
    assert "NWR_SHARED_DATA" not in str(REGISTRY_PATH)


def test_evidence_integration_review_route_is_hidden_and_read_only() -> None:
    route = next(
        page for page in ALL_NAVIGATION_PAGES if page.url_path == "evidence-integration-review"
    )
    page_text = (REPO_ROOT / "app" / route.file_path).read_text(encoding="utf-8")

    assert route.visible is False
    assert route.file_path == "pages/33_evidence_integration_review_v1.py"
    assert "Review-only. This page does not feed rankings" in page_text
    assert "load_evidence_integration_review_data" in page_text
    assert "NWR_SHARED_DATA" not in page_text
