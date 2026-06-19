from __future__ import annotations

from src.services.mock_draft_header_aliases import canonicalize_headers


def test_safe_identity_aliases_map_correctly() -> None:
    report = canonicalize_headers(
        ["player_name", "player_id", "pos", "team"],
        schema_key="veteran_pool",
    )

    assert report.readiness == "GREEN"
    assert report.canonical_headers == ("player", "asset_id", "position", "nfl_team")


def test_market_alias_in_private_source_is_rejected() -> None:
    report = canonicalize_headers(["player", "adp"], schema_key="nwr_private_values")

    assert report.readiness == "RED"
    assert "adp" in report.rejected_aliases


def test_private_alias_in_market_source_is_rejected() -> None:
    report = canonicalize_headers(["player", "private_score"], schema_key="market_context")

    assert report.readiness == "RED"
    assert "private_score" in report.rejected_aliases


def test_ambiguous_alias_requires_manual_mapping() -> None:
    report = canonicalize_headers(["value"], schema_key="veteran_pool")

    assert report.readiness == "RED"
    assert "value" in report.rejected_aliases


def test_aliases_do_not_create_ranked_or_simulated_output() -> None:
    report = canonicalize_headers(["name"], schema_key="frozen_rookie_input")

    assert report.no_rankings_created is True
    assert report.no_simulations_run is True
