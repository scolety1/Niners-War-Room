from pathlib import Path

INVENTORY_PATH = Path(
    "docs/model_v4/POST_AUDIT_LEGACY_COMPATIBILITY_INVENTORY_20260531.md"
)


def test_post_audit_legacy_inventory_classifies_known_compatibility_lanes() -> None:
    text = INVENTORY_PATH.read_text(encoding="utf-8")

    for classification in (
        "active_repaired",
        "compatibility_only",
        "deprecated",
        "needs_later_quarantine",
    ):
        assert classification in text

    for path in (
        "src/services/review_score_envelope_service.py",
        "src/services/player_board_score_service.py",
        "src/services/market_gap_service.py",
        "src/services/model_v4_sprint14c_trade_review_service.py",
        "src/services/trade_service.py",
        "app/pages/04_trade_central.py",
        "app/pages/05_rankings.py",
        "src/config/constants.py",
    ):
        assert path in text


def test_post_audit_legacy_inventory_names_guarded_terms_and_limits() -> None:
    text = INVENTORY_PATH.read_text(encoding="utf-8")

    for compatibility_term in (
        "private_score",
        "legacy_active_pack_score",
        "checkpoint_review_score",
        "market_display_only",
        "market_edge",
        "sell_rows",
        "buy_rows",
        "buy_signals",
        "trade_for_rows",
        "TRADE_FOR_HEADER",
        "External Asset",
    ):
        assert compatibility_term in text

    for guardrail in (
        "Inventory only",
        "do not delete",
        "Do not tune formulas",
        "cannot populate primary review score",
        "must not become primary model value",
    ):
        assert guardrail in text
