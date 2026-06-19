from src.trading_lab.trade_explanations import build_trade_explanation
from src.trading_lab.trade_lab_ui import packages_for_mode
from src.trading_lab.trade_package_builder import (
    build_trade_for_candidates,
    rank_candidate_packages,
)


def fake_review():
    return rank_candidate_packages(build_trade_for_candidates())[0]


def test_explanations_include_trust_and_provenance_labels() -> None:
    explanation = build_trade_explanation(fake_review())

    assert "Fixture-only caveat" in explanation.trust_labels
    assert any("Why NWR likes this" in label for label in explanation.trust_labels)
    assert any("Why the other team might accept" in label for label in explanation.trust_labels)


def test_explanations_separate_nwr_from_public_market_values() -> None:
    explanation = build_trade_explanation(fake_review())

    assert "NWR value and public fantasy market value are separate" in explanation.trust_labels
    assert "public fantasy value is separate" in " ".join(explanation.trust_labels)


def test_manual_review_required_label_appears() -> None:
    explanation = build_trade_explanation(fake_review())

    assert "Manual review required" in explanation.trust_labels
    assert "manual review required" in " ".join(explanation.trust_labels).lower()


def test_ui_packages_carry_trust_labels() -> None:
    package = packages_for_mode("Trade For Player")[0]

    assert "Fixture-only caveat" in package.trust_labels
    assert "Manual review required" in package.trust_labels


def test_no_auto_decision_wording_appears() -> None:
    text = repr(build_trade_explanation(fake_review())).lower()

    for blocked in ("auto-decision", "automatic decision", "submit trade", "send offer"):
        assert blocked not in text
