from pathlib import Path

import pytest

from src.services.owner_test_instrumentation_service import (
    OwnerTestDiagnosticEvent,
    OwnerTestInstrumentationError,
    append_owner_test_event,
    build_decision_bundle_diagnostic_event,
    build_draft_state_change_event,
    read_owner_test_events,
)


def test_append_and_read_round_trips_events_in_order(tmp_path: Path) -> None:
    event_one = build_draft_state_change_event(
        profile_id="p1", timestamp_utc="2026-09-03T00:00:00Z",
        change_kind="OWNER_PICK", pick_number=1,
    )
    event_two = build_decision_bundle_diagnostic_event(
        profile_id="p1", timestamp_utc="2026-09-03T00:00:01Z", speed="FAST",
        bundle_available=True, latency_seconds=0.42,
        top_candidate_player_ids=("RB-0", "WR-0"), selected_player_id="RB-0",
        team_score_before=51.2, championship_equity_before=0.081,
    )
    append_owner_test_event(tmp_path, event_one)
    append_owner_test_event(tmp_path, event_two)

    events = read_owner_test_events(tmp_path, "p1")
    assert len(events) == 2
    assert events[0]["event_type"] == "DRAFT_STATE_CHANGED"
    assert events[0]["draft_state_change_kind"] == "OWNER_PICK"
    assert events[0]["pick_number"] == 1
    assert events[1]["event_type"] == "DECISION_BUNDLE_CALCULATED"
    assert events[1]["latency_seconds"] == 0.42
    assert events[1]["top_candidate_player_ids"] == ["RB-0", "WR-0"]
    assert events[1]["selected_player_id"] == "RB-0"


def test_read_returns_empty_list_when_no_events_have_ever_been_written(tmp_path: Path) -> None:
    assert read_owner_test_events(tmp_path, "never-started") == []


def test_events_for_different_profiles_never_mix(tmp_path: Path) -> None:
    append_owner_test_event(
        tmp_path,
        build_draft_state_change_event(
            profile_id="p1", timestamp_utc="2026-09-03T00:00:00Z",
            change_kind="OWNER_PICK", pick_number=1,
        ),
    )
    append_owner_test_event(
        tmp_path,
        build_draft_state_change_event(
            profile_id="p2", timestamp_utc="2026-09-03T00:00:00Z",
            change_kind="OWNER_PICK", pick_number=1,
        ),
    )
    assert len(read_owner_test_events(tmp_path, "p1")) == 1
    assert len(read_owner_test_events(tmp_path, "p2")) == 1


def test_decision_bundle_blocked_event_carries_the_real_reason_never_a_placeholder_score() -> None:
    event = build_decision_bundle_diagnostic_event(
        profile_id="p1", timestamp_utc="2026-09-03T00:00:00Z", speed="FAST",
        bundle_available=False, blocked_reason="It is not currently the owner's turn.",
    )
    assert event.event_type == "DECISION_BUNDLE_BLOCKED"
    assert event.blocked_reason == "It is not currently the owner's turn."
    assert event.latency_seconds is None
    assert event.top_candidate_player_ids == ()


def test_decision_bundle_error_event_carries_the_real_error_message() -> None:
    event = build_decision_bundle_diagnostic_event(
        profile_id="p1", timestamp_utc="2026-09-03T00:00:00Z", speed="FAST",
        bundle_available=False, error_message="simulated disk failure",
    )
    assert event.event_type == "DECISION_BUNDLE_ERROR"
    assert event.error_message == "simulated disk failure"


def test_unknown_event_type_is_rejected_outright() -> None:
    with pytest.raises(OwnerTestInstrumentationError, match="Unknown event_type"):
        OwnerTestDiagnosticEvent(
            profile_id="p1", timestamp_utc="2026-09-03T00:00:00Z", event_type="NOT_A_REAL_TYPE",
        )


def test_draft_state_changed_requires_a_named_change_kind() -> None:
    with pytest.raises(OwnerTestInstrumentationError, match="DRAFT_STATE_CHANGED requires"):
        OwnerTestDiagnosticEvent(
            profile_id="p1", timestamp_utc="2026-09-03T00:00:00Z",
            event_type="DRAFT_STATE_CHANGED", draft_state_change_kind="NOT_A_REAL_KIND",
        )


def test_every_draft_state_change_kind_the_directive_names_is_accepted() -> None:
    # Owner pick, correction (all four correction types), Catch-Up, Sleeper
    # sync -- section 15's own named list, plus the CPU auto-advance picks
    # that accompany them in FAST/MOCK mode.
    for kind in (
        "OWNER_PICK", "CPU_PICK", "CORRECTION_REPLACE", "CORRECTION_CLEAR",
        "CORRECTION_FILL_GAP", "CORRECTION_UNDO", "CATCH_UP_APPLIED", "SLEEPER_SYNC_APPLIED",
    ):
        event = build_draft_state_change_event(
            profile_id="p1", timestamp_utc="2026-09-03T00:00:00Z", change_kind=kind,
        )
        assert event.draft_state_change_kind == kind
