from __future__ import annotations

from pathlib import Path

from src.services.unified_research_preview_service import (
    AUTHORITY,
    BLOCKED_STATUS,
    EXPECTED_BOARD_SHA256,
    EXPECTED_NEIGHBORHOODS_SHA256,
    RANKED_STATUS,
    file_sha256,
    load_unified_research_preview,
    research_context_for_assets,
)

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_preview_hashes_and_population_contract() -> None:
    preview = load_unified_research_preview()
    packet = ROOT / "docs/hq/model/nwr_unified_research_preview_v1_20260808"
    assert (
        file_sha256(packet / "UNIFIED_DYNASTY_RESEARCH_PREVIEW.csv")
        == EXPECTED_BOARD_SHA256
    )
    assert (
        file_sha256(packet / "ROOKIE_VETERAN_NEIGHBORHOODS.csv")
        == EXPECTED_NEIGHBORHOODS_SHA256
    )
    assert len(preview.board) == 320
    assert len(preview.ranked) == 304
    assert len(preview.blocked) == 16
    assert preview.ranked["asset_type"].value_counts().to_dict() == {"VETERAN": 231, "ROOKIE": 73}
    assert len(preview.neighborhoods) == 73
    assert set(preview.board["authority"]) == {AUTHORITY}


def test_blocked_assets_are_visible_but_never_ranked() -> None:
    preview = load_unified_research_preview()
    assert set(preview.ranked["status"]) == {RANKED_STATUS}
    assert set(preview.blocked["status"]) == {BLOCKED_STATUS}
    assert preview.blocked["research_rank"].isna().all()
    assert int(preview.blocked["position"].eq("K").sum()) == 8
    assert int(preview.blocked["asset_type"].eq("ROOKIE").sum()) == 7
    assert int(preview.blocked["asset_type"].eq("VETERAN").sum()) == 9


def test_context_lookup_preserves_caller_order_and_does_not_invent_rows() -> None:
    preview = load_unified_research_preview()
    assets = preview.ranked["source_asset_id"].astype(str).head(2).tolist()[::-1]
    context = research_context_for_assets(preview, [*assets, "current:not-real"])
    assert context["source_asset_id"].astype(str).tolist() == assets


def test_preview_has_no_production_or_recommendation_columns() -> None:
    columns = set(load_unified_research_preview().board.columns)
    prohibited = {"recommendation", "trade_verdict", "production_rank", "fair_value"}
    assert not prohibited.intersection(columns)


def test_product_surfaces_preserve_authority_and_defaults() -> None:
    rankings = (ROOT / "app/pages/20_final_board_v1.py").read_text(encoding="utf-8")
    compare = (ROOT / "app/pages/22_player_compare_v1.py").read_text(encoding="utf-8")
    explorer = (ROOT / "app/pages/47_asset_explorer_v1.py").read_text(encoding="utf-8")
    trading = (ROOT / "app/pages/23_trading_lab_v1.py").read_text(encoding="utf-8")
    assert rankings.index('"Finished V1 — Production"') < rankings.index(
        '"Unified Dynasty Preview — Research Only"'
    )
    assert "index=0" in rankings
    assert "RESEARCH ONLY — NOT PRODUCTION AUTHORITY" in rankings
    assert "Unified Research Context" in compare
    assert "No common production scale" in compare
    assert '"Show Unified Research Rank (Research Only)"' in explorer
    assert "value=False" in explorer
    assert "current_board_path=current_board_path" in explorer
    assert "Trading Lab remains MANUAL_DESCRIPTIVE_ONLY" in trading
    assert trading.index("trade_item_rows(") < trading.index("load_unified_research_preview()")
