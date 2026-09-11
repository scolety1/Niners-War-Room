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
