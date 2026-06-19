from src.trading_lab.trade_lab_component import (
    CENTER_SECTION_LABELS,
    LEFT_CONTROL_LABELS,
    RIGHT_CONTEXT_LABELS,
    ROUTE_WIRING_STATUS,
    TRAINING_MODE_LABELS,
    trade_lab_label_text,
    trade_lab_sections,
)
from src.trading_lab.trade_lab_ui import demo_trade_packages, format_package_summary


def test_ui_component_exports_expected_sections_and_labels() -> None:
    section_names = {section.name for section in trade_lab_sections()}

    assert "Header" in section_names
    assert "Left control panel" in section_names
    assert "Center results" in section_names
    assert "Right context panel" in section_names
    assert "Training Mode" in section_names
    assert "Target player" in LEFT_CONTROL_LABELS
    assert "Best trade" in CENTER_SECTION_LABELS
    assert "Roster aftermath" in RIGHT_CONTEXT_LABELS
    assert "Negotiation quality" in TRAINING_MODE_LABELS


def test_ui_labels_are_fantasy_football_oriented() -> None:
    text = trade_lab_label_text()

    assert "Trade Lab" in text
    assert "NWR private value placeholder" in text
    assert "Public fantasy market value placeholder" in text
    assert "Drop pressure placeholder" in text
    assert "Rookie/draft context placeholder" in text


def test_no_old_domain_product_language_in_ui_labels() -> None:
    text = trade_lab_label_text().lower()

    for term in ("stock", "broker", "crypto", "equity", "order execution"):
        assert term not in text


def test_demo_packages_render_through_helper_functions() -> None:
    summaries = [format_package_summary(package) for package in demo_trade_packages()]

    assert summaries
    assert all("NWR value" in summary for summary in summaries)


def test_route_wiring_status_is_documented() -> None:
    assert ROUTE_WIRING_STATUS == "isolated_streamlit_page"
