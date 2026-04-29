from __future__ import annotations

import pytest

from src.models.pick_values import (
    BRIEF_PICK_VALUE_CURVE_1000,
    PickValueConfig,
    base_pick_value_1000,
    do_not_draft_before_pick,
    future_discount,
    overall_pick,
    parse_pick_label,
    pick_value,
    pick_value_from_label,
    trade_down_surplus,
    trade_up_cost,
)


def test_pick_value_curve_required_anchor_points() -> None:
    assert len(BRIEF_PICK_VALUE_CURVE_1000) == 50
    assert base_pick_value_1000(overall_pick(1, 1)) == 1000.0
    assert base_pick_value_1000(overall_pick(1, 4)) == 630.0
    assert base_pick_value_1000(overall_pick(1, 5)) == 560.0
    assert base_pick_value_1000(overall_pick(2, 4)) == 200.0
    assert base_pick_value_1000(overall_pick(5, 4)) == 18.0
    assert base_pick_value_1000(overall_pick(5, 10)) == 12.0


def test_pick_value_calculates_overall_pick_and_label() -> None:
    result = pick_value(2026, 2, 4)

    assert result.overall_pick == 14
    assert result.pick_label == "2026 2.04"
    assert result.base_value_1000 == 200.0
    assert result.future_discount == 1.0
    assert result.certainty_adjustment == 1.0
    assert result.declaration_adjustment == 0.0
    assert result.final_pick_value == 200.0
    assert result.bucket == "round-2"


def test_2027_known_pick_gets_future_discount_without_certainty_penalty() -> None:
    result = pick_value(2027, 1, 4, certainty="known")

    assert result.base_value_1000 == 630.0
    assert result.future_discount == pytest.approx(0.80)
    assert result.certainty_adjustment == 1.0
    assert result.final_pick_value == pytest.approx(504.0)
    assert result.bucket == "future-round-1"


def test_projected_future_pick_applies_certainty_adjustment() -> None:
    result = pick_value(2027, 1, 4, certainty="projected")

    assert result.future_discount == pytest.approx(0.80)
    assert result.certainty_adjustment == pytest.approx(0.9)
    assert result.final_pick_value == pytest.approx(453.6)


def test_future_discount_compounds_by_pick_year() -> None:
    config = PickValueConfig(current_pick_year=2026, annual_future_discount=0.82)

    assert future_discount(2026, config) == 1.0
    assert future_discount(2027, config) == pytest.approx(0.82)
    assert future_discount(2028, config) == pytest.approx(0.6724)


def test_future_discount_allows_only_brief_framework_range() -> None:
    PickValueConfig(annual_future_discount=0.80)
    PickValueConfig(annual_future_discount=0.82)

    with pytest.raises(ValueError, match="Annual future discount"):
        PickValueConfig(annual_future_discount=0.79)

    with pytest.raises(ValueError, match="Annual future discount"):
        PickValueConfig(annual_future_discount=0.83)


def test_pick_label_parsing_and_value_lookup() -> None:
    assert parse_pick_label("2026 1.04") == (2026, 1, 4)
    assert parse_pick_label("1.04", default_pick_year=2026) == (2026, 1, 4)

    result = pick_value_from_label("2026 1.04")

    assert result.overall_pick == 4
    assert result.final_pick_value == 630.0


def test_trade_up_and_trade_down_helpers_return_net_value() -> None:
    assert trade_up_cost(630.0, [200.0, 175.0]) == 255.0
    assert trade_down_surplus(630.0, [300.0, 200.0, 175.0]) == 45.0


def test_do_not_draft_before_returns_first_pick_at_or_below_player_value() -> None:
    assert do_not_draft_before_pick(630.0) == "2026 1.04"
    assert do_not_draft_before_pick(200.0) == "2026 2.04"
    assert do_not_draft_before_pick(18.0) == "2026 5.04"
    assert do_not_draft_before_pick(12.0) == "2026 5.10"


def test_do_not_draft_before_defaults_to_configured_current_pick_year() -> None:
    config = PickValueConfig(current_pick_year=2027)

    assert do_not_draft_before_pick(630.0, config=config) == "2027 1.04"
