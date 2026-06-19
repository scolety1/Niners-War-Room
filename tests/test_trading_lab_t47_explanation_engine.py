from src.trading_lab.trade_explanations import build_trade_explanation
from src.trading_lab.trade_lab_ui import packages_for_mode
from src.trading_lab.trade_package_builder import (
    build_trade_for_candidates,
    rank_candidate_packages,
)


def fake_review():
    return rank_candidate_packages(build_trade_for_candidates())[0]


def test_explanations_include_nwr_edge() -> None:
    explanation = build_trade_explanation(fake_review())

    assert "NWR edge" in explanation.nwr_edge


def test_explanations_include_market_fairness() -> None:
    explanation = build_trade_explanation(fake_review())

    assert "Market fairness" in explanation.market_fairness
    assert "public fantasy" in explanation.market_fairness


def test_explanations_include_opponent_fit() -> None:
    explanation = build_trade_explanation(fake_review())

    assert "Opponent fit" in explanation.opponent_fit


def test_explanations_include_roster_aftermath() -> None:
    explanation = build_trade_explanation(fake_review())

    assert "Roster impact" in explanation.roster_impact


def test_explanations_include_risk_notes() -> None:
    explanation = build_trade_explanation(fake_review())

    assert explanation.risk_notes
    assert "Manual review" in " ".join(explanation.risk_notes)


def test_ui_packages_include_explanation_summary() -> None:
    package = packages_for_mode("Trade For Player")[0]

    assert package.explanation_summary.startswith("Review note only")


def test_no_automated_decision_or_submission_language() -> None:
    text = repr(build_trade_explanation(fake_review())).lower()

    for blocked in ("auto-submit", "submit trade", "send offer", "automatic decision"):
        assert blocked not in text
