from __future__ import annotations

from src.services.rankings_display_text_service import safe_data_needed_items


def test_safe_data_needed_items_hides_raw_identity_join_diagnostics() -> None:
    raw = (
        "('missing model v4 current player row', "
        "'unmatched identity join key', "
        "'unmatched identity join key')"
    )

    items = safe_data_needed_items(raw)

    assert items == ["Needs data", "Identity match needed"]
    assert "unmatched identity join key" not in " | ".join(items).lower()


def test_safe_data_needed_items_keeps_plain_user_facing_notes() -> None:
    assert safe_data_needed_items("Need scouting confirmation.") == [
        "Need scouting confirmation."
    ]


def test_safe_data_needed_items_summarizes_source_diagnostics() -> None:
    items = safe_data_needed_items(
        "missing_score_disclosure_fields|unmatched_identity_join_key"
    )

    assert items == ["Data review", "Identity match needed"]
