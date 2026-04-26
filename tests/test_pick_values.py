from __future__ import annotations

import pytest

from src.models.pick_values import (
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
    assert base_pick_value_1000(overall_pick(1, 1)) == 1000.0
    assert base_pick_value_1000(overall_pick(1, 4)) == 760.0
    assert base_pick_value_1000(overall_pick(2, 4)) == 360.0
    assert base_pick_value_1000(overall_pick(5, 4)) == 60.0


def test_pick_value_calculates_overall_pick_and_label() -> None:
    result = pick_value(2026, 2, 4)

    assert result.overall_pick == 14
    assert result.pick_label == "2026 2.04"
    assert result.base_value_1000 == 360.0
    assert result.future_discount == 1.0
    assert result.certainty_adjustment == 1.0
    assert result.declaration_adjustment == 0.0
    assert result.final_pick_value == 360.0
    assert result.bucket == "round-2"


def test_2027_known_pick_gets_future_discount_without_certainty_penalty() -> None:
    result = pick_value(2027, 1, 4, certainty="known")

    assert result.base_value_1000 == 760.0
    assert result.future_discount == pytest.approx(0.85)
    assert result.certainty_adjustment == 1.0
    assert result.final_pick_value == pytest.approx(646.0)
    assert result.bucket == "future-round-1"


def test_projected_future_pick_applies_certainty_adjustment() -> None:
    result = pick_value(2027, 1, 4, certainty="projected")

    assert result.future_discount == pytest.approx(0.85)
    assert result.certainty_adjustment == pytest.approx(0.9)
    assert result.final_pick_value == pytest.approx(581.4)


def test_future_discount_compounds_by_pick_year() -> None:
    config = PickValueConfig(current_pick_year=2026, annual_future_discount=0.85)

    assert future_discount(2026, config) == 1.0
    assert future_discount(2027, config) == pytest.approx(0.85)
    assert future_discount(2028, config) == pytest.approx(0.7225)


def test_pick_label_parsing_and_value_lookup() -> None:
    assert parse_pick_label("2026 1.04") == (2026, 1, 4)
    assert parse_pick_label("1.04", default_pick_year=2026) == (2026, 1, 4)

    result = pick_value_from_label("2026 1.04")

    assert result.overall_pick == 4
    assert result.final_pick_value == 760.0


def test_trade_up_and_trade_down_helpers_return_net_value() -> None:
    assert trade_up_cost(760.0, [360.0, 200.0]) == 200.0
    assert trade_down_surplus(760.0, [360.0, 250.0, 200.0]) == 50.0


def test_do_not_draft_before_returns_first_pick_at_or_below_player_value() -> None:
    assert do_not_draft_before_pick(760.0) == "2026 1.04"
    assert do_not_draft_before_pick(360.0) == "2026 2.04"
    assert do_not_draft_before_pick(59.0) == "2026 5.05"


def test_do_not_draft_before_defaults_to_configured_current_pick_year() -> None:
    config = PickValueConfig(current_pick_year=2027)

    assert do_not_draft_before_pick(760.0, config=config) == "2027 1.04"
