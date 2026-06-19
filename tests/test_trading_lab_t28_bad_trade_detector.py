from src.trading_lab.trade_lab_component import WARNING_SYSTEM_LABELS, trade_lab_label_text
from src.trading_lab.trade_lab_ui import (
    WARNING_LABELS,
    WARNING_SEVERITIES,
    bad_trade_warning_details,
    generate_fake_trade_packages,
)


def test_warning_labels_exist() -> None:
    assert "Market fair but NWR negative" in WARNING_LABELS
    assert "NWR positive but unrealistic" in WARNING_LABELS
    assert "Worse drop pressure" in WARNING_LABELS
    assert "No real integration yet" in WARNING_LABELS


def test_warning_severity_labels_exist() -> None:
    assert WARNING_SEVERITIES == ("info", "review", "caution", "walk-away")


def test_warnings_map_to_fake_packages() -> None:
    for package in generate_fake_trade_packages():
        warnings = bad_trade_warning_details(package)

        assert warnings
        assert all(warning.label in WARNING_LABELS for warning in warnings)
        assert all(warning.severity in WARNING_SEVERITIES for warning in warnings)


def test_warning_labels_render_in_component_metadata() -> None:
    text = trade_lab_label_text()

    for label in ("No real integration yet", "Worse drop pressure"):
        assert label in text
    for severity in WARNING_SEVERITIES:
        assert severity in WARNING_SYSTEM_LABELS


def test_no_old_wall_street_warning_language() -> None:
    text = trade_lab_label_text().lower()

    for term in ("stock", "broker", "equity", "crypto", "order execution"):
        assert term not in text


def test_no_automated_recommendation_or_submission_language() -> None:
    text = " ".join(
        warning.message
        for package in generate_fake_trade_packages()
        for warning in bad_trade_warning_details(package)
    ).lower()

    for blocked in ("auto-submit", "auto-accept", "automated decision", "submit offer"):
        assert blocked not in text
