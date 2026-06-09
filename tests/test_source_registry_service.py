from __future__ import annotations

from src.services.source_registry_service import (
    display_only_sources,
    load_source_registry_rows,
    private_value_sources,
    source_registry_firewall_issues,
)


def test_source_registry_loads_expected_sources() -> None:
    rows = load_source_registry_rows()
    source_pairs = {(row["source_name"], row["source_table"]) for row in rows}

    assert ("nflverse", "player_stats") in source_pairs
    assert ("sleeper", "rosters") in source_pairs
    assert ("rotowire", "projections") in source_pairs
    assert ("fantasypros", "adp") in source_pairs
    assert ("collegefootballdata", "player_stats") in source_pairs


def test_source_registry_firewall_has_no_private_market_projection_leaks() -> None:
    assert source_registry_firewall_issues() == ()


def test_source_registry_separates_private_and_display_only_sources() -> None:
    private_rows = private_value_sources()
    display_rows = display_only_sources()

    assert private_rows
    assert display_rows
    assert all(row["display_only"] == "false" for row in private_rows)
    assert all(row["private_value_allowed"] == "false" for row in display_rows)
    assert any(row["default_admissibility"] == "DISPLAY_MARKET" for row in display_rows)
    assert any(row["default_admissibility"] == "DISPLAY_PROJECTION" for row in display_rows)
