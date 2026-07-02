from __future__ import annotations

from pathlib import Path

from app.navigation import ALL_NAVIGATION_PAGES
from src.services.evidence_review_hub_service import (
    artifact_index_rows,
    current_decision_board_rows,
    guardrail_summary_rows,
    phase_timeline_rows,
    review_queue_rows,
    safe_next_action_rows,
    summary_metrics,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evidence_review_hub_service_indexes_current_hq_artifacts() -> None:
    metrics = summary_metrics()
    artifacts = {row["Artifact"]: row for row in artifact_index_rows()}

    assert metrics["production_approved"] == "no"
    assert metrics["shadow_review_approved"] == "no"
    assert artifacts["NFLVerse Core Usage Review Dataset V1"]["Rows / counts"] == "76804"
    assert artifacts["Red-zone sidecar V1"]["Rows / counts"] == "6424"
    assert artifacts["Historical Tuning substrate V3"]["Rows / counts"] == "5518"
    assert artifacts["Source Contract V1"]["Rows / counts"] == (
        "18 allowed / 4 null-fenced / 11 blocked"
    )
    assert artifacts["Cutline Safe Refinement V1"]["Rows / counts"] == (
        "5 remaining cutline rows"
    )
    assert artifacts["Targeted Redesign V1"]["Rows / counts"] == (
        "12 fixed redesign variants / 2 remaining concern rows"
    )
    assert all(row["Path"].startswith("docs/hq/") for row in artifacts.values())


def test_evidence_review_hub_timeline_and_decision_board_are_hold_only() -> None:
    timeline = {row["Phase"]: row for row in phase_timeline_rows()}
    decision = {row["Item"]: row for row in current_decision_board_rows()}

    assert timeline["NFLVerse phase"]["Status"] == "CLOSED"
    assert timeline["Core Usage Dataset V1"]["Status"] == "MERGED_REVIEW_ONLY"
    assert timeline["Historical substrate V1"]["Status"] == "MERGED_REVIEW_ONLY"
    assert timeline["Historical substrate V2"]["Status"] == "MERGED_REVIEW_ONLY"
    assert timeline["Historical substrate V3"]["Status"] == "MERGED_REVIEW_ONLY"
    assert timeline["Targeted Redesign"]["Status"] == "MERGED_HUMAN_REVIEW_ONLY"
    assert timeline["Current candidate status"]["Status"] == "usage_opportunity_volume HOLD"
    assert decision["usage_opportunity_volume"]["Status"] == "HOLD"
    assert decision["qb_guard_soft_blend"]["Status"] == "USEFUL_RESCUE"
    assert decision["rb_wr_cutline_safe_blend"]["Status"] == "PARTIAL_REFINEMENT"
    assert decision["wr_boundary_breakout_sensitivity_guard"]["Status"] == "HUMAN_REVIEW_ONLY"
    assert decision["Shadow review"]["Status"] == "NOT_APPROVED"
    assert decision["Production"]["Status"] == "NOT_APPROVED"


def test_evidence_review_hub_guardrails_and_queue_are_review_only() -> None:
    guardrails = "\n".join(str(row) for row in guardrail_summary_rows())
    queue = {row["Queue item"]: row for row in review_queue_rows()}
    actions = safe_next_action_rows()

    assert "NO_CHANGE" in guardrails
    assert "Routes, TPRR, YPRR" in guardrails
    assert "NOT_WIRED" in guardrails
    assert queue["Remaining cutline players"]["Status"] == "5 rows open"
    assert queue["Targeted redesign result"]["Status"] == "PRESENT"
    assert "targeted_redesign_summary.md" in queue["Targeted redesign result"]["Evidence"]
    assert queue["UI alternatives result"]["Status"] == "Not present in current HQ"
    assert queue["Development Lab review upgrade"]["Status"] == "NOT_PRESENT_ON_THIS_BASE"
    assert {row["Status"] for row in actions} == {"SAFE_REVIEW_ONLY"}


def test_evidence_review_hub_route_is_visible_and_read_only() -> None:
    route = next(page for page in ALL_NAVIGATION_PAGES if page.url_path == "evidence-review-hub")
    page_text = (REPO_ROOT / "app" / route.file_path).read_text(encoding="utf-8")

    assert route.visible is True
    assert route.title == "Evidence Review Hub"
    assert route.file_path == "pages/45_evidence_review_hub_v1.py"
    assert '"Evidence Review Hub"' in page_text
    assert "Phase Timeline" in page_text
    assert "Current Decision Board" in page_text
    assert "Artifact Index" in page_text
    assert "Guardrail Summary" in page_text
    assert "Review Queue" in page_text
    assert "Safe Next Actions" in page_text
    assert "normal decision surfaces" in page_text
    assert "NWR_SHARED_DATA" not in page_text


def test_evidence_review_hub_app_text_has_no_active_decision_terms() -> None:
    paths = [
        Path("app/pages/45_evidence_review_hub_v1.py"),
        Path("src/services/evidence_review_hub_service.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    blocked_phrase_parts = (
        ("valu", "ation"),
        ("model ", "score"),
        ("hidden ", "decision logic"),
        ("source-truth ", "promotion"),
        ("trade ", "target"),
        ("waiver ", "rank"),
    )

    for phrase in ("".join(parts) for parts in blocked_phrase_parts):
        assert phrase not in text
    assert "review-only" in text
    assert "not_approved" in text
