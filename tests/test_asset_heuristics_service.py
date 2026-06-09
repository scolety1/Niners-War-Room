from __future__ import annotations

import pytest

from src.services.asset_heuristics_service import (
    load_asset_heuristics,
    pick_equivalent_label,
    pick_optionality_bonus,
    pick_year_discount,
    stud_tax,
    stud_tax_rate,
)


def test_asset_heuristics_load_pick_and_package_config() -> None:
    heuristics = load_asset_heuristics()

    assert heuristics.picks.year_discounts[0] == pytest.approx(1.0)
    assert heuristics.picks.year_discounts[1] == pytest.approx(0.90)
    assert heuristics.picks.strong_pick_optionality_bonus == pytest.approx(4.0)
    assert heuristics.packages.extra_roster_spot_cost == pytest.approx(4.0)
    assert heuristics.packages.consolidation_gap_rate == pytest.approx(0.15)


def test_pick_heuristic_helpers_are_config_backed() -> None:
    assert pick_year_discount(2026) == pytest.approx(1.0)
    assert pick_year_discount(2027) == pytest.approx(0.90)
    assert pick_year_discount(2031) == pytest.approx(0.72)
    assert pick_optionality_bonus(70) == pytest.approx(4.0)
    assert pick_optionality_bonus(69.9) == pytest.approx(2.0)
    assert pick_equivalent_label(95) == "1.01-1.03"
    assert pick_equivalent_label(52) == "5.02-5.10"
    assert pick_equivalent_label(51.9) == "UDFA"


def test_package_stud_tax_uses_configured_tiers() -> None:
    assert stud_tax_rate(65) == pytest.approx(0.0)
    assert stud_tax_rate(75) == pytest.approx(0.15)
    assert stud_tax_rate(85) == pytest.approx(0.25)
    assert stud_tax_rate(95) == pytest.approx(0.35)
    assert stud_tax(90, extra_asset_count=1) == pytest.approx(34.5)
    assert stud_tax(90, extra_asset_count=0) == pytest.approx(0.0)
