from __future__ import annotations

from pathlib import Path

COMPONENT = Path("app/components/player_detail_card.py")
RANKINGS_PAGE = Path("app/pages/05_rankings.py")


def test_component_uses_shared_payload_sections_without_forbidden_actions() -> None:
    text = COMPONENT.read_text(encoding="utf-8")

    for required in (
        "Why this row appears here",
        "NWR / private model context",
        "Rankings context",
        "Draft Prep context",
        "Live Draft Room context",
        "Trust, warnings, and data needed",
        "User / history context",
        "Legacy / context disclosure",
        "Advanced source receipts",
        "Draft state is session/local mock state and does not mutate source data.",
        "Roster/team tags are display-only context and do not affect private score.",
    ):
        assert required in text

    for forbidden in (
        "Draft this player",
        "Target",
        "Buy",
        "Sell",
        "Cut",
        "Defer",
    ):
        assert forbidden not in text


def test_rankings_page_is_wired_to_shared_player_detail_card() -> None:
    text = RANKINGS_PAGE.read_text(encoding="utf-8")

    assert "from app.components.player_detail_card import render_player_detail_card" in text
    assert (
        "from src.services.player_detail_card_service import "
        "build_player_detail_card_payload"
    ) in text
    assert 'build_player_detail_card_payload(row.to_dict(), context="rankings")' in text
    assert "render_player_detail_card(payload)" in text
