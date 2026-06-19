from pathlib import Path

from src.trading_lab.trade_lab_component import (
    FAKE_DATA_DISCLAIMER,
    ROUTE_WIRING_STATUS,
    UNWIRED_INTEGRATION_NOTICE,
    trade_lab_label_text,
)
from src.trading_lab.trade_lab_ui import TRADE_LAB_SUBTITLE, TRADE_LAB_TITLE

PAGE_PATH = Path("app/pages/11_trade_lab.py")


def test_isolated_trade_lab_page_exists() -> None:
    assert PAGE_PATH.exists()


def test_page_uses_isolated_component_without_app_shell_wiring() -> None:
    page_text = PAGE_PATH.read_text(encoding="utf-8")

    assert "render_trade_lab_page" in page_text
    assert "src.trading_lab.trade_lab_component" in page_text
    assert "app.navigation" not in page_text
    assert "st.Page" not in page_text
    assert ROUTE_WIRING_STATUS == "isolated_streamlit_page"


def test_page_title_copy_is_available_through_component() -> None:
    label_text = trade_lab_label_text()

    assert TRADE_LAB_TITLE == "Trade Lab"
    assert TRADE_LAB_TITLE in label_text
    assert TRADE_LAB_SUBTITLE in label_text
    assert "fantasy trades" in TRADE_LAB_SUBTITLE


def test_desktop_review_labels_are_present() -> None:
    label_text = trade_lab_label_text()

    for expected in (
        "Build the trade",
        "Review candidate packages",
        "Understand roster aftermath",
        "Best trade",
        "Ranked packages",
        "Negotiation ladder",
        "Bad trade warnings",
        "Training Mode",
    ):
        assert expected in label_text


def test_fake_data_and_not_wired_notices_are_present() -> None:
    assert "fake in-memory examples only" in FAKE_DATA_DISCLAIMER
    assert "not wired yet" in FAKE_DATA_DISCLAIMER
    assert "not wired yet" in UNWIRED_INTEGRATION_NOTICE


def test_no_old_domain_product_language_in_route_smoke_labels() -> None:
    text = " ".join(
        (
            PAGE_PATH.read_text(encoding="utf-8"),
            trade_lab_label_text(),
            FAKE_DATA_DISCLAIMER,
            UNWIRED_INTEGRATION_NOTICE,
        )
    ).lower()

    for blocked in (
        "stock",
        "broker",
        "crypto",
        "equity",
        "order execution",
        "market-data api",
    ):
        assert blocked not in text
