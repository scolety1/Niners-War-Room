from pathlib import Path

from src.trading_lab.trade_away_board import trade_away_target_board_labels
from src.trading_lab.trade_for_board import trade_for_offer_board_labels
from src.trading_lab.trade_lab_component import trade_lab_label_text

SCRIPT_PATH = Path("docs/trading_lab/TRADING_LAB_DESKTOP_HUMAN_REVIEW_SCRIPT_20260618.md")


def test_review_script_exists_in_docs() -> None:
    assert SCRIPT_PATH.exists()


def test_core_review_sections_are_named() -> None:
    text = " ".join(
        (
            SCRIPT_PATH.read_text(encoding="utf-8"),
            trade_lab_label_text(),
            " ".join(trade_away_target_board_labels()),
            " ".join(trade_for_offer_board_labels()),
        )
    )

    for expected in (
        "Best trade",
        "Negotiation ladder",
        "Trade-Away Board",
        "Trade-For Board",
        "Roster aftermath",
        "Training Mode",
    ):
        assert expected in text


def test_no_real_integration_claim_appears() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8").lower()

    for blocked in (
        "real nwr data is currently wired",
        "public fantasy sources are currently wired",
        "saved review queue is currently wired",
        "automated fantasy trade submission is enabled",
    ):
        assert blocked not in text
