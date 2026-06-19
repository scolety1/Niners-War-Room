from src.trading_lab.trade_lab_component import (
    PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS,
    UNWIRED_INTEGRATION_NOTICE,
    trade_lab_label_text,
)


def test_placeholder_boundary_labels_are_explicit() -> None:
    assert PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS

    for label in PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS:
        if "integration" in label.lower():
            assert "placeholder only" in label
            assert "not wired" in label
            assert "needs approval" in label


def test_future_integration_words_are_approval_gated() -> None:
    text = " ".join(PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS)

    for expected in (
        "NWR private value integration",
        "Public fantasy market value integration",
        "Roster context integration",
        "Drop pressure integration",
        "Rookie board integration",
        "Mock draft integration",
    ):
        assert expected in text

    assert text.count("needs approval") >= 6
    assert "not wired" in UNWIRED_INTEGRATION_NOTICE


def test_no_placeholder_claims_real_integration_exists() -> None:
    text = trade_lab_label_text().lower()

    for blocked in (
        "real integration is wired",
        "live integration",
        "connected to outcome",
        "connected to rookie",
        "connected to mock draft",
        "connected to drop decision",
        "automatic trade submission enabled",
    ):
        assert blocked not in text


def test_generated_outputs_and_automatic_decisioning_remain_blocked() -> None:
    text = " ".join(PLACEHOLDER_INTEGRATION_BOUNDARY_LABELS)

    assert "No generated outputs." in text
    assert "No automated trade submission or automatic decisioning." in text
