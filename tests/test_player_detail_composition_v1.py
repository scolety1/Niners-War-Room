from __future__ import annotations

import py_compile
from pathlib import Path

PAGE = Path("app/pages/53_player_detail_v1.py")


def test_player_detail_composes_existing_governed_sources_without_writes() -> None:
    text = PAGE.read_text(encoding="utf-8")
    py_compile.compile(str(PAGE), doraise=True)

    for contract in (
        "load_governed_asset_registry",
        "load_dynasty_rankings",
        "load_unified_research_preview",
        "load_outcome_v3_display",
        "join_market_to_players",
        "build_player_detail_card_payload",
        "load_store(\"personal_board\")",
        "Advanced Data Details",
        "Exact weighted contribution percentages are not admitted",
    ):
        assert contract in text
    for mutation in ("save_scenario(", "upsert_personal_asset(", "perform_workspace_write("):
        assert mutation not in text


def test_player_detail_keeps_missing_and_cross_authority_states_explicit() -> None:
    text = PAGE.read_text(encoding="utf-8")
    assert "Research Only · not production authority" in text
    assert "no value is inferred" in text
    assert "never a model input, rank, or trade value" in text
    assert "No Finished V1 score receipts apply" in text
