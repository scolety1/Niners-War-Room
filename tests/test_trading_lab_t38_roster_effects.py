from src.trading_lab.trade_package_builder import (
    build_drop_pressure_candidates,
    build_trade_for_candidates,
    rank_candidate_packages,
)
from src.trading_lab.trade_roster_effects import (
    REAL_ROSTER_INTEGRATION_WIRED,
    ROSTER_INTEGRATION_STATUS,
    build_roster_aftermath,
    estimate_drop_pressure_impact,
    estimate_keeper_impact,
    estimate_position_depth_impact,
    estimate_rookie_pick_context,
)


def fake_review():
    return rank_candidate_packages(build_trade_for_candidates())[0]


def test_keeper_impact_generated() -> None:
    impact = estimate_keeper_impact(fake_review())

    assert impact
    assert "Keeper" in impact


def test_drop_pressure_before_after_generated() -> None:
    review = rank_candidate_packages(build_drop_pressure_candidates())[0]
    before, after, label = estimate_drop_pressure_impact(review)

    assert before
    assert after
    assert label in {"improves", "worsens", "neutral"}


def test_positional_depth_impact_generated() -> None:
    before, after, label = estimate_position_depth_impact(fake_review())

    assert "Before:" in before
    assert "After:" in after
    assert label


def test_rookie_mock_context_placeholder_generated() -> None:
    context = estimate_rookie_pick_context(fake_review())

    assert context
    assert "pick" in context.lower() or "placeholder" in context.lower()


def test_real_integration_status_remains_false_and_not_wired() -> None:
    aftermath = build_roster_aftermath(fake_review())

    assert REAL_ROSTER_INTEGRATION_WIRED is False
    assert "not wired" in ROSTER_INTEGRATION_STATUS
    assert "not wired" in aftermath.needs_real_integration_note
