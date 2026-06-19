from src.trading_lab.trade_lab_component import NEGOTIATION_LADDER_LABELS, trade_lab_label_text
from src.trading_lab.trade_lab_ui import (
    format_negotiation_ladder,
    generate_fake_trade_packages,
)


def test_every_package_has_ladder_fields() -> None:
    for package in generate_fake_trade_packages():
        ladder = package.negotiation_ladder

        assert ladder.opening_offer
        assert ladder.fair_offer
        assert ladder.max_offer
        assert ladder.walk_away
        assert ladder.do_not_include
        assert ladder.counteroffer_ideas
        assert ladder.if_reject
        assert ladder.if_ask_for_more


def test_ladder_labels_render() -> None:
    text = trade_lab_label_text()

    for label in NEGOTIATION_LADDER_LABELS:
        assert label in text


def test_walkaway_and_do_not_include_assets_exist() -> None:
    ladder = generate_fake_trade_packages()[0].negotiation_ladder
    lines = format_negotiation_ladder(ladder)

    assert any("Walk-away line" in line for line in lines)
    assert any("Do-not-include assets" in line for line in lines)


def test_counteroffer_ideas_exist() -> None:
    ladder = generate_fake_trade_packages()[0].negotiation_ladder
    lines = format_negotiation_ladder(ladder)

    assert any("Counteroffer ideas" in line for line in lines)
    assert any("If they reject" in line for line in lines)
    assert any("If they ask for more" in line for line in lines)


def test_no_automated_sending_submission_or_decisioning_language() -> None:
    text = " ".join(
        " ".join(format_negotiation_ladder(package.negotiation_ladder))
        for package in generate_fake_trade_packages()
    ).lower()

    for blocked in ("auto-send", "submit trade", "automated decision", "auto-accept"):
        assert blocked not in text
