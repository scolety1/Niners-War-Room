from __future__ import annotations

from src.services.league_lifecycle_context_service import build_league_lifecycle_context


def _context(**overrides):
    values = {
        "league_type": "REDRAFT",
        "season_year": 2026,
        "archived": False,
        "draft_configured": False,
        "drafted_count": 0,
        "total_draft_picks": 150,
        "current_pick": None,
        "provider_status": "in_season",
        "current_week": 4,
        "season_type": "regular",
        "playoffs_start": 15,
        "raw_waiver_type": 1,
        "live_sync_capable": True,
    }
    values.update(overrides)
    return build_league_lifecycle_context(**values)


def test_regular_season_uses_provider_status_and_real_week() -> None:
    context = _context()
    assert context.season_phase == "REGULAR_SEASON"
    assert context.draft_status == "COMPLETE"
    assert context.is_regular_season is True
    assert context.waiver_type == "WAIVER_PRIORITY"
    assert context.faab_enabled is False


def test_playoff_phases_are_relative_to_league_playoff_start() -> None:
    assert _context(current_week=12).season_phase == "PLAYOFF_PUSH"
    playoffs = _context(current_week=15)
    assert playoffs.season_phase == "FANTASY_PLAYOFFS"
    assert playoffs.is_playoffs is True


def test_faab_and_draft_day_are_provider_driven() -> None:
    context = _context(
        league_type="DYNASTY",
        provider_status="drafting",
        current_week=None,
        season_type="pre",
        raw_waiver_type=2,
    )
    assert context.season_phase == "DRAFT_DAY"
    assert context.is_draft_season is True
    assert context.waiver_type == "FAAB"
    assert context.faab_enabled is True


def test_complete_provider_status_is_season_complete() -> None:
    context = _context(provider_status="complete", season_type="regular")
    assert context.season_phase == "SEASON_COMPLETE"
    assert context.is_offseason is True


def test_unknown_rules_stay_unknown_not_defaulted() -> None:
    context = _context(raw_waiver_type=None, current_week=None, playoffs_start=None)
    assert context.current_week is None
    assert context.waiver_type == "UNKNOWN"
    assert context.faab_enabled is None
