from src.trading_lab import (
    FANTASY_SOURCE_CATEGORIES,
    FantasySourceMetadata,
    validate_fantasy_source_metadata,
)


def test_allowed_fantasy_source_categories_are_accepted() -> None:
    for category in FANTASY_SOURCE_CATEGORIES:
        source = FantasySourceMetadata(
            source_id=f"SRC-{category}",
            source_name="Manual fantasy source",
            source_category=category,
            allowed_use="Display or comparison for fantasy trade review.",
            prohibited_use="Do not overwrite NWR private value.",
            attribution="Manual operator note",
        )

        assert validate_fantasy_source_metadata(source) == ()


def test_prohibited_stock_market_source_category_is_rejected() -> None:
    source = FantasySourceMetadata(
        source_id="SRC-STOCK",
        source_name="Stock market API",
        source_category="stock_market_api",
        allowed_use="none",
        prohibited_use="Wrong domain",
        attribution="none",
    )

    codes = {issue.code for issue in validate_fantasy_source_metadata(source)}

    assert "prohibited_source_category" in codes
    assert "prohibited_wall_street_language" in codes


def test_unknown_source_category_is_rejected() -> None:
    source = FantasySourceMetadata(
        source_id="SRC-UNKNOWN",
        source_name="Unknown source",
        source_category="unknown_source",
        allowed_use="manual review",
        prohibited_use="none",
        attribution="manual",
    )

    assert "unknown_source_category" in {
        issue.code for issue in validate_fantasy_source_metadata(source)
    }


def test_secrets_are_rejected_in_source_config() -> None:
    source = FantasySourceMetadata(
        source_id="SRC-NWR",
        source_name="NWR private value output",
        source_category="nwr_private_value_outputs",
        allowed_use="Core NWR value signal.",
        prohibited_use="Do not expose private scoring internals.",
        attribution="NWR",
        config={"api_key": "not allowed"},
    )

    assert "secret_like_language" in {
        issue.code for issue in validate_fantasy_source_metadata(source)
    }
