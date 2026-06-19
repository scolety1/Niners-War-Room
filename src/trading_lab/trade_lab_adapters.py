from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.trading_lab.trade_lab_fixtures import (
    asset_by_name,
    fixture_assets,
    fixture_team_contexts,
)
from src.trading_lab.trade_value_contracts import FantasyAsset, TeamContext


@dataclass(frozen=True)
class ProviderStatus:
    provider_name: str
    is_available: bool
    status_label: str
    note: str
    is_real_integration: bool = False


class ValueProvider(Protocol):
    def get_asset_values(self) -> tuple[FantasyAsset, ...]: ...

    def status(self) -> ProviderStatus: ...


class PublicMarketProvider(Protocol):
    def get_public_value(self, asset_id: str) -> float | None: ...

    def status(self) -> ProviderStatus: ...


class RosterContextProvider(Protocol):
    def get_roster_context(self) -> str: ...

    def status(self) -> ProviderStatus: ...


class DropPressureProvider(Protocol):
    def get_drop_pressure_tag(self, asset_id: str) -> str: ...

    def status(self) -> ProviderStatus: ...


class RookieContextProvider(Protocol):
    def get_rookie_context(self, asset_id: str) -> str: ...

    def status(self) -> ProviderStatus: ...


class MockDraftContextProvider(Protocol):
    def get_mock_draft_context(self) -> str: ...

    def status(self) -> ProviderStatus: ...


class OpponentContextProvider(Protocol):
    def get_opponent_contexts(self) -> tuple[TeamContext, ...]: ...

    def status(self) -> ProviderStatus: ...


def fixture_provider_status(provider_name: str) -> ProviderStatus:
    return ProviderStatus(
        provider_name=provider_name,
        is_available=True,
        status_label="fixture-only",
        note="Fixture provider; real integration not wired.",
        is_real_integration=False,
    )


def missing_provider_status(provider_name: str) -> ProviderStatus:
    return ProviderStatus(
        provider_name=provider_name,
        is_available=False,
        status_label="missing-placeholder",
        note="Provider unavailable; future integration not wired.",
        is_real_integration=False,
    )


class FixtureValueProvider:
    def get_asset_values(self) -> tuple[FantasyAsset, ...]:
        return fixture_assets()

    def status(self) -> ProviderStatus:
        return fixture_provider_status("FixtureValueProvider")


class FixturePublicMarketProvider:
    def get_public_value(self, asset_id: str) -> float | None:
        for asset in fixture_assets():
            if asset.asset_id == asset_id:
                return asset.public_market_value
        return None

    def status(self) -> ProviderStatus:
        return fixture_provider_status("FixturePublicMarketProvider")


class FixtureRosterContextProvider:
    def get_roster_context(self) -> str:
        return "Fixture roster context only; real roster integration not wired."

    def status(self) -> ProviderStatus:
        return fixture_provider_status("FixtureRosterContextProvider")


class FixtureDropPressureProvider:
    def get_drop_pressure_tag(self, asset_id: str) -> str:
        for asset in fixture_assets():
            if asset.asset_id == asset_id:
                return asset.drop_pressure_tag
        return "missing"

    def status(self) -> ProviderStatus:
        return fixture_provider_status("FixtureDropPressureProvider")


class FixtureRookieContextProvider:
    def get_rookie_context(self, asset_id: str) -> str:
        return asset_by_name("2026 2nd").rookie_pick_context if asset_id else "missing"

    def status(self) -> ProviderStatus:
        return fixture_provider_status("FixtureRookieContextProvider")


class PlaceholderMockDraftContextProvider:
    def get_mock_draft_context(self) -> str:
        return "Mock draft context placeholder; not wired."

    def status(self) -> ProviderStatus:
        return missing_provider_status("PlaceholderMockDraftContextProvider")


class FixtureOpponentContextProvider:
    def get_opponent_contexts(self) -> tuple[TeamContext, ...]:
        return fixture_team_contexts()

    def status(self) -> ProviderStatus:
        return fixture_provider_status("FixtureOpponentContextProvider")


class DisabledNwrValueProvider:
    def get_asset_values(self) -> tuple[FantasyAsset, ...]:
        return ()

    def status(self) -> ProviderStatus:
        return missing_provider_status("DisabledNwrValueProvider")


class DisabledPublicMarketProvider:
    def get_public_value(self, asset_id: str) -> None:
        return None

    def status(self) -> ProviderStatus:
        return missing_provider_status("DisabledPublicMarketProvider")


class DisabledRosterContextProvider:
    def get_roster_context(self) -> str:
        return "Roster context not wired."

    def status(self) -> ProviderStatus:
        return missing_provider_status("DisabledRosterContextProvider")


class DisabledRookieMockContextProvider:
    def get_rookie_context(self, asset_id: str) -> str:
        return "Rookie context not wired."

    def get_mock_draft_context(self) -> str:
        return "Mock draft context not wired."

    def status(self) -> ProviderStatus:
        return missing_provider_status("DisabledRookieMockContextProvider")


def disabled_provider_status_labels() -> tuple[str, ...]:
    return (
        DisabledNwrValueProvider().status().status_label,
        DisabledPublicMarketProvider().status().status_label,
        DisabledRosterContextProvider().status().status_label,
        DisabledRookieMockContextProvider().status().status_label,
    )
