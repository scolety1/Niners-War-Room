from datetime import datetime, timedelta, timezone

from src.services.league_lifecycle_service import resolve_league_lifecycle


def test_archived_profile_is_offseason_regardless_of_draft_state():
    resolution = resolve_league_lifecycle(
        archived=True, draft_configured=True, drafted_count=180,
        total_draft_picks=180, current_pick=None,
    )
    assert resolution.lifecycle == "OFFSEASON"
    assert "archived" in resolution.basis.lower()


def test_never_configured_is_pre_draft():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=False, drafted_count=0,
        total_draft_picks=180, current_pick=None,
    )
    assert resolution.lifecycle == "PRE_DRAFT"


def test_configured_with_zero_drafted_is_pre_draft():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=0,
        total_draft_picks=180, current_pick=None,
    )
    assert resolution.lifecycle == "PRE_DRAFT"


def test_partial_with_active_pick_pointer_is_live_draft():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=42,
        total_draft_picks=180, current_pick=43,
    )
    assert resolution.lifecycle == "LIVE_DRAFT"


def test_partial_with_no_pick_pointer_is_still_live_draft_not_in_season():
    # Real, disclosed conservative default: never assume IN_SEASON from an
    # ambiguous partial draft board -- see the function's own docstring.
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=42,
        total_draft_picks=180, current_pick=None,
    )
    assert resolution.lifecycle == "LIVE_DRAFT"


def test_fully_drafted_is_in_season():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=180,
        total_draft_picks=180, current_pick=None,
    )
    assert resolution.lifecycle == "IN_SEASON"


def test_fully_drafted_even_with_stale_current_pick_is_in_season():
    # Completion (drafted_count >= total) takes priority over a leftover
    # current_pick pointer -- a real state a draft board can be in right
    # after its final pick before the pointer is cleared.
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=180,
        total_draft_picks=180, current_pick=180,
    )
    assert resolution.lifecycle == "IN_SEASON"


def test_overdrafted_count_still_counts_as_in_season():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=181,
        total_draft_picks=180, current_pick=None,
    )
    assert resolution.lifecycle == "IN_SEASON"


# --- 2026-09-17 fix: real provider evidence over local draft-board activity ---
# Real repro shapes: a Sleeper league drafted on Sleeper itself never gets
# local draft-board activity (would otherwise be stuck in PRE_DRAFT forever
# despite deep in-season real standings/matchups -- the real "Fantasy
# Gamers" bug found while investigating the owner's report); a real,
# complete, one-time ESPN import can finish with fewer local picks than
# `team_count * draft.rounds` (the real "KHA High Stakes" / "403 N 18th and
# friends" shapes: 157/192 and 118/128, K/DST rounds resolved outside the
# live pick stream) and has no live re-sync path in this app at all.


def test_provider_status_in_season_overrides_zero_local_draft_activity():
    # Real "Fantasy Gamers" shape: drafted entirely on Sleeper, zero local
    # draft-board rows, but Sleeper's own league.status says in_season.
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=False, drafted_count=0,
        total_draft_picks=120, current_pick=None,
        provider_status="in_season", live_sync_capable=True,
    )
    assert resolution.lifecycle == "IN_SEASON"
    assert "provider" in resolution.basis.lower()


def test_provider_status_pre_draft_is_honored_not_forced_in_season():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=False, drafted_count=0,
        total_draft_picks=120, current_pick=None,
        provider_status="pre_draft", live_sync_capable=True,
    )
    assert resolution.lifecycle == "PRE_DRAFT"


def test_provider_status_drafting_maps_to_live_draft():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=12,
        total_draft_picks=120, current_pick=13,
        provider_status="drafting", live_sync_capable=True,
    )
    assert resolution.lifecycle == "LIVE_DRAFT"


def test_provider_status_complete_maps_to_offseason():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=120,
        total_draft_picks=120, current_pick=None,
        provider_status="complete", live_sync_capable=True,
    )
    assert resolution.lifecycle == "OFFSEASON"


def test_unrecognized_provider_status_falls_back_to_local_draft_board():
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=False, drafted_count=0,
        total_draft_picks=120, current_pick=None,
        provider_status="some_future_unknown_value", live_sync_capable=True,
    )
    assert resolution.lifecycle == "PRE_DRAFT"


def test_stale_non_live_syncable_partial_draft_is_in_season():
    # Real "KHA High Stakes" shape: 157 of a configured 192 (16 teams * 12
    # rounds), no live re-sync path (ESPN), last real pick over 2 weeks ago.
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=157,
        total_draft_picks=192, current_pick=None,
        live_sync_capable=False,
        draft_last_activity_utc="2026-09-03T04:28:00+00:00",
        now_utc=now,
    )
    assert resolution.lifecycle == "IN_SEASON"
    assert "no live draft-sync path" in resolution.basis


def test_stale_non_live_syncable_partial_draft_403_shape_is_in_season():
    # Real "403 N 18th and friends" shape: 118 of a configured 128 (8 teams
    # * 16 rounds).
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=118,
        total_draft_picks=128, current_pick=None,
        live_sync_capable=False,
        draft_last_activity_utc="2026-09-08T02:50:29+00:00",
        now_utc=now,
    )
    assert resolution.lifecycle == "IN_SEASON"


def test_recent_non_live_syncable_partial_draft_stays_live_draft():
    # A genuinely still-active, currently-being-recorded ESPN draft (last
    # pick 2 hours ago) must NOT be treated as complete just because it has
    # no live re-sync path -- staleness, not provider alone, is the signal.
    now = datetime(2026, 9, 7, 22, 0, 0, tzinfo=timezone.utc)
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=40,
        total_draft_picks=128, current_pick=None,
        live_sync_capable=False,
        draft_last_activity_utc="2026-09-07T20:00:00+00:00",
        now_utc=now,
    )
    assert resolution.lifecycle == "LIVE_DRAFT"


def test_stale_but_live_syncable_partial_draft_is_not_forced_in_season():
    # A Sleeper profile (live_sync_capable=True) with a stale timestamp
    # should NOT hit the ESPN-style staleness fallback -- Sleeper has its
    # own real completion signal (provider_status / exact count), so an
    # actually-stalled live draft correctly stays LIVE_DRAFT rather than
    # being silently marked done.
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=42,
        total_draft_picks=180, current_pick=None,
        live_sync_capable=True,
        draft_last_activity_utc="2026-09-01T00:00:00+00:00",
        now_utc=now,
    )
    assert resolution.lifecycle == "LIVE_DRAFT"


def test_stale_threshold_boundary_just_under_is_still_live_draft():
    now = datetime(2026, 9, 17, 0, 0, 0, tzinfo=timezone.utc)
    last_activity = now - timedelta(hours=23, minutes=59)
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=100,
        total_draft_picks=128, current_pick=None,
        live_sync_capable=False,
        draft_last_activity_utc=last_activity.isoformat(),
        now_utc=now,
    )
    assert resolution.lifecycle == "LIVE_DRAFT"


def test_stale_threshold_boundary_at_exactly_24h_is_in_season():
    now = datetime(2026, 9, 17, 0, 0, 0, tzinfo=timezone.utc)
    last_activity = now - timedelta(hours=24)
    resolution = resolve_league_lifecycle(
        archived=False, draft_configured=True, drafted_count=100,
        total_draft_picks=128, current_pick=None,
        live_sync_capable=False,
        draft_last_activity_utc=last_activity.isoformat(),
        now_utc=now,
    )
    assert resolution.lifecycle == "IN_SEASON"
