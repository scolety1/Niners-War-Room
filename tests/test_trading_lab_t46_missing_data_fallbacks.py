from src.trading_lab.trade_missing_data import (
    ALL_ASSETS_EXCLUDED_LABEL,
    MISSING_PUBLIC_MARKET_VALUE_LABEL,
    all_assets_excluded_message,
    missing_context_states,
    missing_nwr_value_state,
    missing_public_market_fairness_label,
    missing_public_market_value_state,
    no_package_fallback_message,
    unsupported_mode_fallback_message,
)


def test_missing_nwr_value_produces_clear_placeholder() -> None:
    state = missing_nwr_value_state()

    assert state.label == "Missing NWR value placeholder"
    assert state.can_continue is True
    assert state.claims_real_integration is False


def test_missing_public_market_value_does_not_break_scoring() -> None:
    state = missing_public_market_value_state()

    assert state.can_continue is True
    assert missing_public_market_fairness_label(None, 10.0) == MISSING_PUBLIC_MARKET_VALUE_LABEL


def test_missing_context_states_exist() -> None:
    labels = {state.label for state in missing_context_states()}

    assert "Missing roster context placeholder" in labels
    assert "Missing drop pressure placeholder" in labels
    assert "Missing rookie/mock context placeholder" in labels
    assert "Missing opponent context placeholder" in labels


def test_no_package_fallback_renders() -> None:
    assert "No fixture-backed packages available" in no_package_fallback_message("Trade For Player")


def test_unsupported_mode_fallback_renders() -> None:
    assert "Unsupported mode fallback" in unsupported_mode_fallback_message("Unknown Mode")


def test_all_assets_excluded_fallback_renders() -> None:
    assert all_assets_excluded_message() == ALL_ASSETS_EXCLUDED_LABEL


def test_no_real_integration_is_claimed() -> None:
    text = repr((missing_nwr_value_state(), missing_context_states())).lower()

    assert "real integration is wired" not in text
    assert "connected to" not in text
