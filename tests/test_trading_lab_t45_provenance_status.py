from src.trading_lab.trade_lab_component import (
    PROVENANCE_STATUS_LABELS,
    trade_lab_label_text,
)
from src.trading_lab.trade_provenance import (
    FIXTURE_DEMO_LABEL,
    MANUAL_REVIEW_REQUIRED_LABEL,
    PUBLIC_MARKET_NOT_WIRED_LABEL,
    REAL_NWR_NOT_WIRED_LABEL,
    fixture_value_provenance,
    future_integration_provenance,
    missing_value_provenance,
    ui_data_status_labels,
)


def test_fixture_values_are_marked_fixture_demo() -> None:
    provenance = fixture_value_provenance()

    assert provenance.status == "fixture-demo"
    assert provenance.note == FIXTURE_DEMO_LABEL
    assert provenance.is_real_integration is False


def test_no_fixture_value_claims_to_be_real() -> None:
    text = repr(fixture_value_provenance()).lower()

    assert "real integration" not in text
    assert "fixture" in text


def test_missing_and_future_integration_labels_exist() -> None:
    missing = missing_value_provenance("NWR value", "private value")
    future = future_integration_provenance("Public value", "public market")

    assert missing.status == "missing"
    assert future.status == "future-integration"
    assert future.is_real_integration is False


def test_ui_data_status_labels_are_explicit() -> None:
    labels = ui_data_status_labels()

    assert FIXTURE_DEMO_LABEL in labels
    assert REAL_NWR_NOT_WIRED_LABEL in labels
    assert PUBLIC_MARKET_NOT_WIRED_LABEL in labels
    assert MANUAL_REVIEW_REQUIRED_LABEL in labels
    assert PROVENANCE_STATUS_LABELS == labels


def test_ui_label_text_contains_provenance_labels() -> None:
    text = trade_lab_label_text()

    for label in ui_data_status_labels():
        assert label in text
