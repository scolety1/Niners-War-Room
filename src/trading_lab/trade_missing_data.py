from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.trade_lab_ui import empty_state_message, safe_packages_for_review

MISSING_NWR_VALUE_LABEL = "Missing NWR value placeholder"
MISSING_PUBLIC_MARKET_VALUE_LABEL = "Missing public fantasy market value placeholder"
MISSING_ROSTER_CONTEXT_LABEL = "Missing roster context placeholder"
MISSING_DROP_PRESSURE_LABEL = "Missing drop pressure placeholder"
MISSING_ROOKIE_MOCK_CONTEXT_LABEL = "Missing rookie/mock context placeholder"
MISSING_OPPONENT_CONTEXT_LABEL = "Missing opponent context placeholder"
UNSUPPORTED_MODE_FALLBACK_LABEL = "Unsupported mode fallback uses Trade For Player fixtures"
ALL_ASSETS_EXCLUDED_LABEL = "All assets excluded; no fixture packages available"


@dataclass(frozen=True)
class MissingDataState:
    field_name: str
    label: str
    note: str
    can_continue: bool
    claims_real_integration: bool = False


def missing_nwr_value_state() -> MissingDataState:
    return MissingDataState(
        field_name="nwr_value",
        label=MISSING_NWR_VALUE_LABEL,
        note="Use manual review; real NWR integration not wired.",
        can_continue=True,
    )


def missing_public_market_value_state() -> MissingDataState:
    return MissingDataState(
        field_name="public_market_value",
        label=MISSING_PUBLIC_MARKET_VALUE_LABEL,
        note="Market fairness becomes placeholder review, not a blocker.",
        can_continue=True,
    )


def missing_context_states() -> tuple[MissingDataState, ...]:
    return (
        MissingDataState("roster_context", MISSING_ROSTER_CONTEXT_LABEL, "Show placeholder.", True),
        MissingDataState("drop_pressure", MISSING_DROP_PRESSURE_LABEL, "Show placeholder.", True),
        MissingDataState(
            "rookie_mock_context",
            MISSING_ROOKIE_MOCK_CONTEXT_LABEL,
            "Show placeholder.",
            True,
        ),
        MissingDataState(
            "opponent_context",
            MISSING_OPPONENT_CONTEXT_LABEL,
            "Show placeholder and require manual review.",
            True,
        ),
    )


def safe_public_market_delta(get_value: float | None, give_value: float | None) -> float | None:
    if get_value is None or give_value is None:
        return None
    return round(get_value - give_value, 2)


def missing_public_market_fairness_label(get_value: float | None, give_value: float | None) -> str:
    delta = safe_public_market_delta(get_value, give_value)
    if delta is None:
        return MISSING_PUBLIC_MARKET_VALUE_LABEL
    if abs(delta) <= 5:
        return "market-fair"
    return "manual market review"


def no_package_fallback_message(mode: str) -> str:
    return empty_state_message(mode)


def unsupported_mode_fallback_message(mode: str) -> str:
    packages = safe_packages_for_review(mode)
    return (
        UNSUPPORTED_MODE_FALLBACK_LABEL
        if packages
        else f"No fallback fixture packages for {mode}."
    )


def all_assets_excluded_message() -> str:
    return ALL_ASSETS_EXCLUDED_LABEL
