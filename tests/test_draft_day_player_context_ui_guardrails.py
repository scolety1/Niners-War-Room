from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_draft_day_context_pages_do_not_read_raw_shared_nflverse_data() -> None:
    for path in (
        "app/components/draft_day_player_context.py",
        "src/services/draft_day_player_context_service.py",
        "src/services/nflverse_schedule_context_display_service.py",
        "app/pages/21_live_draft_room_v1.py",
        "app/pages/24_mock_draft_v1.py",
        "app/pages/29_post_draft_mode_v2.py",
    ):
        text = _text(path)
        assert "scheduled_ingest" not in text
        assert "vendor_spikes" not in text
        assert "nflreadpy" not in text


def test_draft_day_context_service_uses_tracked_artifact_only() -> None:
    text = "\n".join(
        _text(path)
        for path in (
            "src/services/draft_day_player_context_service.py",
            "src/services/nflverse_schedule_context_display_service.py",
        )
    )

    assert "NFLVERSE_PLAYER_CONTEXT_DISPLAY_PATH" in text
    assert "NFLVERSE_PLAYER_CONTEXT_SCHEMA_MANIFEST_PATH" in text
    assert "C:\\NWR_SHARED_DATA" not in text
    assert "load_runtime_state" not in text
    assert "save_runtime_state" not in text


def test_context_ui_has_required_display_only_language() -> None:
    text = _text("app/components/draft_day_player_context.py")

    assert "Display-only" in text
    assert "Review-only context" in text
    assert "Not model input" in text
    assert "Not enough information" in text
    assert "Needs identity review" in text


def test_context_ui_does_not_add_active_recommendation_language() -> None:
    combined = "\n".join(
        _text(path)
        for path in (
            "app/components/draft_day_player_context.py",
            "src/services/draft_day_player_context_service.py",
        )
    ).lower()

    forbidden = (
        "should draft",
        "best available",
        "grade",
        "winner",
        "loser",
        "surplus",
        "steal",
        "reach",
        "value pick",
        "trade target",
        "injury risk",
        "durability score",
        "medical projection",
    )
    for phrase in forbidden:
        assert phrase not in combined
