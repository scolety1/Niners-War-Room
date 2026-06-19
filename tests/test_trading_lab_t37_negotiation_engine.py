from src.trading_lab.trade_negotiation import (
    build_counteroffer_notes,
    build_do_not_include_assets,
    build_negotiation_ladder,
)
from src.trading_lab.trade_package_builder import (
    build_trade_for_candidates,
    rank_candidate_packages,
)


def best_fake_review():
    return rank_candidate_packages(build_trade_for_candidates())[0]


def test_ladder_has_opening_fair_max_and_walkaway() -> None:
    ladder = build_negotiation_ladder(best_fake_review())

    assert ladder.opening_offer
    assert ladder.fair_offer
    assert ladder.max_offer
    assert ladder.walk_away


def test_do_not_include_assets_exist() -> None:
    protected = build_do_not_include_assets(best_fake_review())

    assert protected


def test_counteroffer_notes_exist() -> None:
    notes = build_counteroffer_notes(best_fake_review())

    assert notes
    assert "fake package" in " ".join(notes)


def test_high_nwr_gain_package_gets_sensible_fake_ladder() -> None:
    review = best_fake_review()
    ladder = build_negotiation_ladder(review)

    assert review.score.nwr_delta > 0
    assert "Player A" in ladder.fair_offer or "Player B" in ladder.fair_offer
    assert "positive" in ladder.if_ask_for_more


def test_no_automated_submit_or_send_language() -> None:
    text = repr(build_negotiation_ladder(best_fake_review())).lower()

    for blocked in ("auto-submit", "send offer", "submit trade", "execute"):
        assert blocked not in text
