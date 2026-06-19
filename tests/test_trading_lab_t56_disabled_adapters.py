from src.trading_lab.trade_lab_adapters import (
    DisabledNwrValueProvider,
    DisabledPublicMarketProvider,
    DisabledRookieMockContextProvider,
    DisabledRosterContextProvider,
    disabled_provider_status_labels,
)
from src.trading_lab.trade_lab_component import DISABLED_PROVIDER_STATUS_LABELS


def test_disabled_providers_return_not_wired_status() -> None:
    providers = (
        DisabledNwrValueProvider(),
        DisabledPublicMarketProvider(),
        DisabledRosterContextProvider(),
        DisabledRookieMockContextProvider(),
    )

    for provider in providers:
        status = provider.status()
        assert status.is_available is False
        assert status.status_label == "missing-placeholder"
        assert status.is_real_integration is False
        assert "not wired" in status.note


def test_disabled_providers_do_not_return_fixture_values() -> None:
    assert DisabledNwrValueProvider().get_asset_values() == ()
    assert DisabledPublicMarketProvider().get_public_value("target-player") is None


def test_disabled_providers_do_not_read_files_or_call_apis() -> None:
    provider = DisabledNwrValueProvider()

    for blocked in ("read", "load", "fetch", "connect", "api", "path"):
        assert not hasattr(provider, blocked)


def test_ui_can_display_disabled_provider_status() -> None:
    labels = disabled_provider_status_labels()

    assert labels
    assert set(DISABLED_PROVIDER_STATUS_LABELS) == {"missing-placeholder"}
