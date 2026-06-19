from src.trading_lab import (
    TRADE_PACKAGE_REQUIRED_FIELDS,
    prohibited_field_names_in,
    schema_for_artifact,
)


def test_trade_package_schema_contains_required_fields() -> None:
    schema = schema_for_artifact("trade_package")

    assert schema is not None
    assert schema.required_fields == TRADE_PACKAGE_REQUIRED_FIELDS
    assert "NWR value delta" in schema.purpose


def test_schema_registry_blocks_wall_street_field_names() -> None:
    blocked = prohibited_field_names_in(
        ["target_player", "stock_symbol", "broker_account", "api_key"]
    )

    assert blocked == ("api_key", "broker_account", "stock_symbol")
