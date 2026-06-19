from src.trading_lab.trade_lab_component import (
    CENTER_SECTION_LABELS,
    DESKTOP_SECTION_LABELS,
    LEFT_CONTROL_LABELS,
    NEGOTIATION_LADDER_LABELS,
    RESULT_CARD_LABELS,
    RIGHT_CONTEXT_LABELS,
    UNWIRED_INTEGRATION_NOTICE,
    trade_lab_label_text,
)
from src.trading_lab.trade_lab_ui import TRADE_LAB_MODES, demo_payload_text


def test_desktop_sections_are_exposed() -> None:
    assert DESKTOP_SECTION_LABELS == (
        "Build the trade",
        "Review candidate packages",
        "Understand roster aftermath",
    )
    assert "Trade question" in LEFT_CONTROL_LABELS
    assert "Package constraints" in LEFT_CONTROL_LABELS
    assert "Preference controls" in LEFT_CONTROL_LABELS
    assert "Best trade" in CENTER_SECTION_LABELS
    assert "Roster aftermath" in RIGHT_CONTEXT_LABELS


def test_trade_for_and_trade_away_modes_exist() -> None:
    assert "Trade For Player" in TRADE_LAB_MODES
    assert "Trade Away Player" in TRADE_LAB_MODES


def test_best_trade_card_labels_exist() -> None:
    assert "Package summary" in RESULT_CARD_LABELS
    assert "NWR value gain" in RESULT_CARD_LABELS
    assert "Public fantasy market fairness" in RESULT_CARD_LABELS
    assert "Manual review verdict" in RESULT_CARD_LABELS


def test_negotiation_ladder_labels_exist() -> None:
    for label in (
        "Opening offer",
        "Fair offer",
        "Max offer",
        "Walk-away line",
    ):
        assert label in NEGOTIATION_LADDER_LABELS


def test_bad_trade_warning_and_context_labels_exist() -> None:
    text = trade_lab_label_text()

    assert "Bad trade warnings" in text
    assert "Keeper impact" in text
    assert "Drop pressure impact" in text
    assert "Rookie/mock draft context" in text
    assert "Data status / needs data" in text


def test_fake_demo_payloads_remain_fantasy_football_oriented() -> None:
    text = demo_payload_text()

    assert "NWR value" in text
    assert "Public fantasy market value placeholder" in text
    assert "Target Player" in text
    assert "Team Alpha" in text


def test_no_old_product_language_in_active_ui_labels() -> None:
    text = trade_lab_label_text().lower()

    for term in ("stock", "broker", "api", "crypto", "equity", "order execution"):
        assert term not in text


def test_placeholders_clearly_say_real_integrations_are_not_wired() -> None:
    assert "not wired yet" in UNWIRED_INTEGRATION_NOTICE
    assert "Real NWR value" in UNWIRED_INTEGRATION_NOTICE
    assert "public fantasy market value" in UNWIRED_INTEGRATION_NOTICE
