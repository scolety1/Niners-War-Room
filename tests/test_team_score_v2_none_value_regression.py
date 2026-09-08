"""NWR post-draft overnight (phase 1): regression test for a real,
reproduced crash -- Team Score V2's raw-features builder previously did
`float(pool[pid]["replacement_adjusted_value"])` unconditionally, which
raised `TypeError` for any manual/unmodeled roster asset (K/DST, or a
skill-position player NWR's ranking excludes but keeps searchable via the
manual pool) since those always carry `replacement_adjusted_value = None`
by design. Reproduced live against the real 403 profile while running the
RAV/DQ candidate-budget study (redraft_decision_bundle_v2 against a roster
containing a manual K/DST asset). Fixed by reusing the same
None-becomes-0.0 semantic `shadow_numeric_authorities_service._roster_players`
already established for this exact gap.

A dedicated test module for team_score_v2_multi_league_service.py does not
otherwise exist in this worktree (git history shows one existed upstream,
`tests/test_team_score_v2_multi_league_service.py`, but it isn't present
here -- a real, disclosed, pre-existing test-coverage gap, not something
this fix attempts to backfill). This file is scoped narrowly to the one
real bug found and fixed this pass.
"""

from src.services.team_score_v2_multi_league_service import _pool_value


def test_pool_value_is_zero_for_an_unmodeled_asset() -> None:
    """K/DST and any manual-pool-only skill player carry
    replacement_adjusted_value=None by design -- never a crash, never a
    fabricated nonzero value."""
    entry = {"position": "K", "replacement_adjusted_value": None}
    assert _pool_value(entry) == 0.0


def test_pool_value_passes_through_a_real_modeled_value() -> None:
    entry = {"position": "RB", "replacement_adjusted_value": 123.45}
    assert _pool_value(entry) == 123.45


def test_pool_value_handles_a_missing_key_the_same_as_none() -> None:
    entry = {"position": "DST"}
    assert _pool_value(entry) == 0.0
