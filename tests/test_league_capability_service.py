from __future__ import annotations

from src.services.espn_flaim_snapshot_service import (
    EspnFlaimSnapshot,
    EspnFlaimSnapshotError,
    EspnRosterPlayer,
    EspnScoringSetting,
    parse_espn_flaim_snapshot,
)
from src.services.league_capability_service import (
    NO_CAPABILITIES,
    capabilities_for_profile,
    capabilities_from_espn_flaim_snapshot,
    capabilities_from_sleeper_receipt,
)


# ---------------------------------------------------------------------------
# capabilities_for_profile dispatch (provider-agnostic entry point)
# ---------------------------------------------------------------------------


def test_no_receipt_and_no_snapshot_returns_no_capabilities_never_a_guess() -> None:
    result = capabilities_for_profile()
    assert result == NO_CAPABILITIES
    assert result.has_verified_identity is False
    assert result.has_roster_data is False
    assert result.has_scoring_settings == "UNKNOWN"
    assert result.has_available_player_pool == "NONE"
    assert result.transaction_direction == "NOT_ENABLED"


def test_dispatch_does_not_inspect_a_provider_string_at_all() -> None:
    """The whole point: no `profile.provider == "sleeper"` check anywhere.

    This test asserts the dispatcher's signature has no `provider`
    parameter at all -- capability checks are computed strictly from real
    receipt/snapshot presence, never from a provider label.
    """

    import inspect

    sig = inspect.signature(capabilities_for_profile)
    assert "provider" not in sig.parameters


# ---------------------------------------------------------------------------
# Sleeper receipt-derived capabilities
# ---------------------------------------------------------------------------


def _minimal_sleeper_receipt(**overrides: object) -> dict:
    base = {
        "league": {"league_id": "123", "name": "Test League", "season": 2026},
        "owner": {"roster_id": 1, "user_id": "u1", "username": "tester"},
        "roster_positions": ["QB", "RB", "WR", "BN", "BN"],
        "roster_snapshot": {
            "players": [
                {
                    "player_name": "Real Player",
                    "position": "QB",
                    "sleeper_player_id": "1",
                    "starter": True,
                    "team": "SF",
                }
            ],
            "roster_id": 1,
            "synced_at_utc": "2026-09-19T12:00:00+00:00",
        },
        "scoring_reconciliation": [{"nwr_setting": "reception", "sleeper_setting": "rec", "status": "exact", "value": 1.0}],
        "unsupported_scoring": [],
    }
    base.update(overrides)
    return base


def test_real_shaped_sleeper_receipt_has_identity_roster_and_lineup() -> None:
    caps = capabilities_from_sleeper_receipt(_minimal_sleeper_receipt())
    assert caps.has_verified_identity is True
    assert caps.has_roster_data is True
    assert caps.has_lineup_eligibility is True
    assert caps.has_scoring_settings == "COMPLETE"
    assert caps.retrieved_at_utc == "2026-09-19T12:00:00+00:00"
    # A Sleeper receipt file never carries the free-agent pool (that's a
    # separate live fetch path this function does not model) -- must be
    # honestly NONE, not fabricated as available.
    assert caps.has_available_player_pool == "NONE"
    assert caps.has_standings == "NONE"
    assert caps.transaction_direction == "NOT_ENABLED"


def test_sleeper_receipt_with_unsupported_scoring_is_partial_not_complete() -> None:
    receipt = _minimal_sleeper_receipt(unsupported_scoring=["fgm_50p", "kr_yd"])
    caps = capabilities_from_sleeper_receipt(receipt)
    assert caps.has_scoring_settings == "PARTIAL"
    assert any("2 scoring setting" in d for d in caps.disclosures)


def test_sleeper_receipt_missing_league_block_has_no_verified_identity() -> None:
    receipt = _minimal_sleeper_receipt()
    del receipt["league"]
    caps = capabilities_from_sleeper_receipt(receipt)
    assert caps.has_verified_identity is False


def test_sleeper_receipt_with_empty_roster_players_has_no_roster_or_lineup() -> None:
    receipt = _minimal_sleeper_receipt()
    receipt["roster_snapshot"]["players"] = []
    caps = capabilities_from_sleeper_receipt(receipt)
    assert caps.has_roster_data is False
    # Lineup eligibility requires a real roster too, even if
    # roster_positions is present.
    assert caps.has_lineup_eligibility is False


def test_sleeper_receipt_with_no_scoring_reconciliation_at_all_is_unknown() -> None:
    receipt = _minimal_sleeper_receipt()
    del receipt["scoring_reconciliation"]
    del receipt["unsupported_scoring"]
    caps = capabilities_from_sleeper_receipt(receipt)
    assert caps.has_scoring_settings == "UNKNOWN"


def test_capabilities_for_profile_prefers_sleeper_receipt_when_both_present() -> None:
    sleeper_caps = capabilities_for_profile(sleeper_receipt=_minimal_sleeper_receipt())
    dispatched = capabilities_for_profile(
        sleeper_receipt=_minimal_sleeper_receipt(),
        espn_snapshot=_minimal_espn_snapshot(),
    )
    assert dispatched == sleeper_caps


# ---------------------------------------------------------------------------
# ESPN/Flaim snapshot-derived capabilities
# ---------------------------------------------------------------------------


def _minimal_espn_snapshot_dict(**overrides: object) -> dict:
    base = {
        "profile_id": "synthetic-profile-id",
        "provider_league_id": "999999",
        "league_name": "SYNTHETIC TEST LEAGUE — not real ESPN data",
        "season": 2026,
        "team_count": 10,
        "owner_team_id": "5",
        "owner_team_name": "Synthetic Team",
        "roster": [
            {
                "provider_player_id": "espn-1",
                "player_name": "Synthetic Starter",
                "position": "QB",
                "team": "SF",
                "slot": "STARTER",
            },
            {
                "provider_player_id": "espn-2",
                "player_name": "Synthetic Bench Player",
                "position": "RB",
                "team": "KC",
                "slot": "BENCH",
            },
        ],
        "scoring_settings": [
            {"espn_setting_name": "receptions", "value": 1.0, "nwr_setting": "reception"},
        ],
        "scoring_completeness": "PARTIAL",
        "available_player_pool": [],
        "available_player_pool_coverage": "NONE",
        "available_player_pool_bound_description": None,
        "retrieved_at_utc": "2026-09-19T18:00:00+00:00",
        "provider_as_of_utc": None,
    }
    base.update(overrides)
    return base


def _minimal_espn_snapshot(**overrides: object) -> EspnFlaimSnapshot:
    return parse_espn_flaim_snapshot(_minimal_espn_snapshot_dict(**overrides))


def test_synthetic_espn_snapshot_loader_round_trips_the_documented_schema() -> None:
    snapshot = _minimal_espn_snapshot()
    assert snapshot.profile_id == "synthetic-profile-id"
    assert len(snapshot.roster) == 2
    assert snapshot.roster[0].slot == "STARTER"
    assert snapshot.scoring_completeness == "PARTIAL"


def test_espn_snapshot_loader_rejects_missing_required_field() -> None:
    raw = _minimal_espn_snapshot_dict()
    del raw["provider_league_id"]
    try:
        parse_espn_flaim_snapshot(raw)
        assert False, "expected EspnFlaimSnapshotError"
    except EspnFlaimSnapshotError as exc:
        assert "provider_league_id" in str(exc)


def test_espn_snapshot_loader_rejects_invalid_roster_slot() -> None:
    raw = _minimal_espn_snapshot_dict()
    raw["roster"][0]["slot"] = "STARTING_LINEUP"  # not a valid slot literal
    try:
        parse_espn_flaim_snapshot(raw)
        assert False, "expected EspnFlaimSnapshotError"
    except EspnFlaimSnapshotError as exc:
        assert "slot" in str(exc)


def test_espn_snapshot_loader_rejects_complete_player_pool_coverage() -> None:
    """A Flaim-sourced pool can never legitimately claim COMPLETE coverage.

    Per the July 2026 audit's own finding (free-agent retrieval was
    "capped, alphabetic, noisy, incomplete"), this is treated as a data
    error, not a legitimate state, absent a new, explicit reentry
    decision.
    """

    raw = _minimal_espn_snapshot_dict(available_player_pool_coverage="COMPLETE")
    try:
        parse_espn_flaim_snapshot(raw)
        assert False, "expected EspnFlaimSnapshotError"
    except EspnFlaimSnapshotError as exc:
        assert "COMPLETE" in str(exc)


def test_espn_snapshot_derived_capabilities_reflect_partial_scoring_and_no_standings() -> None:
    snapshot = _minimal_espn_snapshot()
    caps = capabilities_from_espn_flaim_snapshot(snapshot)
    assert caps.has_verified_identity is True
    assert caps.has_roster_data is True
    assert caps.has_lineup_eligibility is True
    assert caps.has_scoring_settings == "PARTIAL"
    assert caps.has_available_player_pool == "NONE"
    # Standings are never modeled as present from an ESPN/Flaim snapshot in
    # this schema -- always NONE, not merely display-constrained.
    assert caps.has_standings == "NONE"
    assert caps.transaction_direction == "NOT_ENABLED"
    assert caps.retrieved_at_utc == "2026-09-19T18:00:00+00:00"
    assert caps.provider_as_of_utc is None
    assert any("PARTIAL" in d for d in caps.disclosures)


def test_espn_snapshot_with_bounded_player_pool_surfaces_the_bound_description() -> None:
    snapshot = _minimal_espn_snapshot(
        available_player_pool_coverage="BOUNDED",
        available_player_pool_bound_description=(
            "First 200 free agents alphabetically; not exhaustive."
        ),
        available_player_pool=[
            {
                "provider_player_id": "espn-fa-1",
                "player_name": "Synthetic Free Agent",
                "position": "WR",
                "team": "DAL",
            }
        ],
    )
    caps = capabilities_from_espn_flaim_snapshot(snapshot)
    assert caps.has_available_player_pool == "BOUNDED"
    assert "First 200 free agents" in " ".join(caps.disclosures)


def test_espn_snapshot_with_empty_roster_has_no_roster_or_lineup_capability() -> None:
    snapshot = _minimal_espn_snapshot(roster=[])
    caps = capabilities_from_espn_flaim_snapshot(snapshot)
    assert caps.has_roster_data is False
    assert caps.has_lineup_eligibility is False


def test_capabilities_for_profile_dispatches_to_espn_snapshot_when_no_sleeper_receipt() -> None:
    caps = capabilities_for_profile(espn_snapshot=_minimal_espn_snapshot())
    assert caps.has_verified_identity is True
    assert caps.has_roster_data is True
