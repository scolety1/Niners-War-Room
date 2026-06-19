from src.trading_lab.trade_lab_component import (
    CENTER_SECTION_LABELS,
    NEGOTIATION_LADDER_LABELS,
    RESULT_CARD_LABELS,
    RIGHT_CONTEXT_LABELS,
    trade_lab_label_text,
)
from src.trading_lab.trade_lab_ui import TRADE_LAB_MODES, TRADE_LAB_SUBTITLE, TRADE_LAB_TITLE


def test_trade_lab_title_and_subtitle_are_correct() -> None:
    assert TRADE_LAB_TITLE == "Trade Lab"
    assert (
        TRADE_LAB_SUBTITLE
        == "Find realistic fantasy trades where market says fair, but NWR says we win."
    )


def test_modes_are_correct() -> None:
    assert TRADE_LAB_MODES == (
        "Trade For Player",
        "Trade Away Player",
        "Upgrade Position",
        "Consolidate Depth",
        "Pick Conversion",
        "Drop-Pressure Trade",
        "Opponent-Fit Trade",
        "Training Mode",
    )


def test_result_card_labels_are_correct() -> None:
    assert "Best trade" in CENTER_SECTION_LABELS
    assert "Package summary" in RESULT_CARD_LABELS
    assert "NWR value gain" in RESULT_CARD_LABELS
    assert "Public fantasy market fairness" in RESULT_CARD_LABELS
    assert "Manual review verdict" in RESULT_CARD_LABELS


def test_negotiation_ladder_labels_are_correct() -> None:
    for label in (
        "Opening offer",
        "Fair offer",
        "Max offer",
        "Walk-away line",
    ):
        assert label in NEGOTIATION_LADDER_LABELS


def test_roster_aftermath_labels_are_correct() -> None:
    assert "Roster aftermath" in RIGHT_CONTEXT_LABELS
    assert "Keeper impact" in RIGHT_CONTEXT_LABELS
    assert "Drop pressure impact" in RIGHT_CONTEXT_LABELS
    assert "Rookie/mock draft context" in RIGHT_CONTEXT_LABELS


def test_no_old_wall_street_product_purpose_language() -> None:
    text = trade_lab_label_text().lower()

    for term in ("stock", "equity", "crypto", "forex", "investment"):
        assert term not in text


def test_no_broker_api_execution_affordances() -> None:
    text = trade_lab_label_text().lower()

    for term in ("broker", "api", "order execution", "auto-execute", "submit trade"):
        assert term not in text
