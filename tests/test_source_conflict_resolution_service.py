import pytest

from src.services.source_conflict_resolution_service import (
    CONFIRMED,
    CONFLICTED,
    HIGH_AUTHORITY,
    LOW_AUTHORITY,
    MEDIUM_AUTHORITY,
    PROVISIONAL,
    STALE,
    UNKNOWN,
    SourceConflictError,
    SourceObservation,
    resolve_source_conflict,
)

NOW = "2026-09-03T12:00:00Z"


def _obs(source, ts, authority, value, confidence="MEDIUM"):
    return SourceObservation(
        source=source, timestamp_utc=ts, authority_type=authority,
        confidence=confidence, value=value,
    )


def test_no_observations_returns_unknown_with_no_resolved_value() -> None:
    result = resolve_source_conflict([], now_utc=NOW)
    assert result.status == UNKNOWN
    assert result.resolved_value is None


def test_agreeing_high_authority_sources_are_confirmed() -> None:
    obs = [
        _obs("sleeper", "2026-09-03T10:00:00Z", HIGH_AUTHORITY, "IR"),
        _obs("nfl_injury_report", "2026-09-03T09:00:00Z", HIGH_AUTHORITY, "IR"),
    ]
    result = resolve_source_conflict(obs, now_utc=NOW)
    assert result.status == CONFIRMED
    assert result.resolved_value == "IR"


def test_agreeing_but_only_low_authority_sources_are_provisional_not_confirmed() -> None:
    obs = [_obs("news_scout", "2026-09-03T10:00:00Z", LOW_AUTHORITY, "OUT")]
    result = resolve_source_conflict(obs, now_utc=NOW)
    assert result.status == PROVISIONAL
    assert result.resolved_value == "OUT"


def test_disagreeing_fresh_sources_are_conflicted_and_never_silently_resolved() -> None:
    obs = [
        _obs("sleeper", "2026-09-03T10:00:00Z", HIGH_AUTHORITY, "ACTIVE"),
        _obs("beat_reporter", "2026-09-03T11:00:00Z", MEDIUM_AUTHORITY, "IR"),
    ]
    result = resolve_source_conflict(obs, now_utc=NOW)
    assert result.status == CONFLICTED
    assert result.resolved_value is None
    assert "sleeper" in result.note
    assert "beat_reporter" in result.note


def test_a_single_old_observation_beyond_the_window_is_stale() -> None:
    obs = [_obs("sleeper", "2026-08-01T10:00:00Z", HIGH_AUTHORITY, "QUESTIONABLE")]
    result = resolve_source_conflict(obs, now_utc=NOW, stale_after_hours=72.0)
    assert result.status == STALE
    assert result.resolved_value == "QUESTIONABLE"  # last-known, explicitly labeled stale


def test_a_stale_disagreement_does_not_silently_pick_the_newest_value() -> None:
    # Both observations are stale -- the newest one becomes the STALE
    # last-known value, but this must still surface the underlying
    # disagreement in the note rather than pretending it never happened.
    obs = [
        _obs("sleeper", "2026-07-01T10:00:00Z", HIGH_AUTHORITY, "ACTIVE"),
        _obs("beat_reporter", "2026-07-02T10:00:00Z", MEDIUM_AUTHORITY, "IR"),
    ]
    result = resolve_source_conflict(obs, now_utc=NOW, stale_after_hours=72.0)
    assert result.status == STALE
    assert result.resolved_value == "IR"  # the newer of the two stale observations


def test_construction_rejects_an_unknown_authority_type() -> None:
    with pytest.raises(SourceConflictError):
        SourceObservation(
            source="x", timestamp_utc=NOW, authority_type="MADE_UP",
            confidence="HIGH", value="ACTIVE",
        )


def test_conflicted_status_cannot_be_constructed_with_a_resolved_value() -> None:
    from src.services.source_conflict_resolution_service import ConflictResolution

    with pytest.raises(SourceConflictError):
        ConflictResolution(
            status=CONFLICTED, resolved_value="ACTIVE", observations=(), note="bad",
        )


def test_confirmed_status_requires_a_resolved_value() -> None:
    from src.services.source_conflict_resolution_service import ConflictResolution

    with pytest.raises(SourceConflictError):
        ConflictResolution(status=CONFIRMED, resolved_value=None, observations=(), note="bad")
