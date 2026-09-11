from dataclasses import replace

from src.services.league_workspace_context_service import (
    build_league_workspace_context,
    compute_league_snapshot_id,
    compute_roster_state_hash,
    compute_scoring_profile_hash,
)
from src.services.redraft_engine_v1_service import builtin_presets


def _profile():
    return replace(builtin_presets()[0], profile_id="test-profile-1")


def test_scoring_profile_hash_is_stable_for_identical_rules():
    profile_a = _profile()
    profile_b = replace(
        _profile(), profile_id="a-totally-different-id", league_name="Different Name"
    )
    assert compute_scoring_profile_hash(profile_a) == compute_scoring_profile_hash(profile_b)


def test_scoring_profile_hash_changes_with_a_real_rule_edit():
    profile = _profile()
    edited = replace(profile, team_count=profile.team_count + 1)
    assert compute_scoring_profile_hash(profile) != compute_scoring_profile_hash(edited)


def test_roster_state_hash_is_none_without_a_real_roster_read():
    assert compute_roster_state_hash(None) is None


def test_roster_state_hash_is_order_independent_but_content_sensitive():
    a = compute_roster_state_hash(["100", "200", "300"])
    b = compute_roster_state_hash(["300", "100", "200"])
    c = compute_roster_state_hash(["100", "200", "999"])
    assert a == b
    assert a != c


def test_league_snapshot_id_changes_when_roster_state_changes():
    scoring_hash = compute_scoring_profile_hash(_profile())
    snap_before = compute_league_snapshot_id(
        scoring_profile_hash=scoring_hash,
        roster_state_hash=compute_roster_state_hash(["1", "2"]),
        week=1,
    )
    snap_after = compute_league_snapshot_id(
        scoring_profile_hash=scoring_hash,
        roster_state_hash=compute_roster_state_hash(["1", "3"]),
        week=1,
    )
    assert snap_before != snap_after


def test_league_snapshot_id_changes_when_week_changes():
    scoring_hash = compute_scoring_profile_hash(_profile())
    roster_hash = compute_roster_state_hash(["1", "2"])
    week1 = compute_league_snapshot_id(
        scoring_profile_hash=scoring_hash, roster_state_hash=roster_hash, week=1
    )
    week2 = compute_league_snapshot_id(
        scoring_profile_hash=scoring_hash, roster_state_hash=roster_hash, week=2
    )
    assert week1 != week2


def test_build_league_workspace_context_pre_draft():
    context = build_league_workspace_context(
        profile=_profile(), draft_configured=False, drafted_count=0,
        total_draft_picks=180, current_pick=None, current_week=None,
        roster_player_ids=None, sync_status="NOT_APPLICABLE", sync_as_of=None,
    )
    assert context.lifecycle == "PRE_DRAFT"
    assert context.roster_state_hash is None
    assert context.league_snapshot_id  # always populated, never blank
    payload = context.to_dict()
    assert payload["profileId"] == "test-profile-1"
    assert payload["lifecycle"] == "PRE_DRAFT"
    assert "leagueSnapshotId" in payload


def test_build_league_workspace_context_in_season_with_live_roster():
    context = build_league_workspace_context(
        profile=_profile(), draft_configured=True, drafted_count=180,
        total_draft_picks=180, current_pick=None, current_week=3,
        roster_player_ids=["10", "20", "30"], sync_status="LIVE",
        sync_as_of="2026-09-10T00:00:00+00:00",
        issues=["Current NFL week is not automatically sourced."],
    )
    assert context.lifecycle == "IN_SEASON"
    assert context.roster_state_hash is not None
    assert context.sync_status == "LIVE"
    assert context.issues == ("Current NFL week is not automatically sourced.",)
