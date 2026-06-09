from __future__ import annotations

from pathlib import Path

PLAN = Path("docs/model_v4/LIVE_DRAFT_ROOM_PAGE_PLAN_20260609.md")


def test_live_draft_room_plan_exists_and_separates_draft_prep() -> None:
    text = PLAN.read_text(encoding="utf-8")

    assert "Live Draft Room is the future draft-day surface" in text
    assert "Draft Prep remains the planning page" in text
    assert "Draft Prep should not mutate mock/live draft state." in text
    assert "50-pick grid" in text
    assert "Current pick / on-clock indicator" in text
    assert "Legal Pool Pending" in text


def test_live_draft_room_plan_reuses_existing_services() -> None:
    text = PLAN.read_text(encoding="utf-8")

    for service in (
        "app/components/draft_session.py",
        "src/services/draft_service.py",
        "src/services/draft_state_service.py",
        "src/services/draft_ux_service.py",
        "src/services/real_draft_pool_preview_service.py",
    ):
        assert service in text


def test_live_draft_room_plan_preserves_guardrails() -> None:
    text = PLAN.read_text(encoding="utf-8")

    assert "Never write draft picks or drafted-player state back into active data packs." in text
    assert "Do not tune formulas." in text
    assert "Do not invent legal draftable status." in text
    assert "Do not invent a baseline for `2026 5.04`." in text
    assert "Decision Board remains untouched." in text
