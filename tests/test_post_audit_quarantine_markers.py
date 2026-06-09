from pathlib import Path


def test_legacy_quarantine_markers_exist_on_compatibility_lanes() -> None:
    trade_service = Path("src/services/trade_service.py").read_text(encoding="utf-8")
    asset_board_service = Path("src/services/asset_board_service.py").read_text(
        encoding="utf-8"
    )
    external_asset_service = Path(
        "src/services/model_v4_sprint14c_trade_review_service.py"
    ).read_text(encoding="utf-8")

    assert "LEGACY_TRADE_SERVICE_COMPATIBILITY_QUARANTINE_NOTE" in trade_service
    assert "Compatibility-only API names retained" in trade_service
    assert "primary_review_score remains blank" in trade_service
    assert "legacy_active_pack_score" in trade_service

    assert "LEGACY_ACTIVE_PACK_SCORE_QUARANTINE_NOTE" in asset_board_service
    assert "primary_review_score stays blank" in asset_board_service
    assert "Legacy active-pack score disclosure only" in asset_board_service

    assert "Compatibility-only alias" in external_asset_service
    assert "External Asset" in external_asset_service
    assert "trade-for recommendations" in external_asset_service
