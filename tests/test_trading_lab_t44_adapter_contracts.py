from src.trading_lab.trade_lab_adapters import (
    FixtureDropPressureProvider,
    FixtureOpponentContextProvider,
    FixturePublicMarketProvider,
    FixtureRosterContextProvider,
    FixtureValueProvider,
    PlaceholderMockDraftContextProvider,
    missing_provider_status,
)


def test_fixture_value_provider_satisfies_expected_contract() -> None:
    provider = FixtureValueProvider()
    assets = provider.get_asset_values()

    assert assets
    assert provider.status().status_label == "fixture-only"
    assert provider.status().is_real_integration is False


def test_contracts_expose_expected_fantasy_fields() -> None:
    asset = FixtureValueProvider().get_asset_values()[0]

    assert asset.asset_id
    assert asset.display_name
    assert hasattr(asset, "nwr_value")
    assert hasattr(asset, "public_market_value")
    assert hasattr(asset, "keeper_status")
    assert hasattr(asset, "drop_pressure_tag")


def test_public_market_provider_returns_fixture_value_only() -> None:
    value = FixturePublicMarketProvider().get_public_value("target-player")

    assert value == 70.0


def test_context_providers_return_fixture_or_placeholder_status() -> None:
    assert "fixture" in FixtureRosterContextProvider().get_roster_context().lower()
    assert FixtureDropPressureProvider().get_drop_pressure_tag("player-d") == "high"
    assert FixtureOpponentContextProvider().get_opponent_contexts()
    assert "not wired" in PlaceholderMockDraftContextProvider().get_mock_draft_context()


def test_real_integration_methods_are_not_implemented() -> None:
    provider = FixtureValueProvider()

    for blocked in ("load_real_data", "fetch", "connect", "write", "save"):
        assert not hasattr(provider, blocked)


def test_unavailable_provider_returns_explicit_missing_status() -> None:
    status = missing_provider_status("FutureProvider")

    assert status.is_available is False
    assert status.status_label == "missing-placeholder"
    assert status.is_real_integration is False
    assert "not wired" in status.note
