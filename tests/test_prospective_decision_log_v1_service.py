import pytest

from src.services.prospective_decision_log_v1_service import (
    EVENT_OWNER_ACTION_RECORDED,
    EVENT_RECOMMENDATION_LOGGED,
    ProspectiveCandidateSnapshot,
    ProspectiveDecisionLogError,
    ProspectiveDecisionRecord,
    append_prospective_decision,
    build_owner_action_record,
    build_recommendation_record,
    read_prospective_decisions,
)


def _candidate(player_id: str, pick_score: float) -> ProspectiveCandidateSnapshot:
    return ProspectiveCandidateSnapshot(
        player_id=player_id, player_name=player_id, position="RB",
        player_score=88.0, team_score_after=71.0, team_score_delta=13.0,
        team_score_v2_after=64.0, team_score_v2_delta=9.0,
        team_score_v2_evidence_level="TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED",
        championship_equity_after=0.15, championship_equity_v2_after=0.14,
        championship_equity_v2_evidence_level="TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED",
        cost_of_waiting=2.5, make_it_back_probability=0.07, pick_score=pick_score,
        action="TAKE_NOW", evidence_status="OK",
    )


def test_recommendation_record_is_written_and_read_back(tmp_path) -> None:
    record = build_recommendation_record(
        profile_id="p1", timestamp_utc="2026-09-06T00:00:00Z", source_as_of="2026-09-05",
        league_config_summary={"team_count": 12}, pick_number=5, draft_slot=3,
        owner_roster_before=["RB-0"], available_pool_size=300,
        candidates=[_candidate("RB-1", 92.0), _candidate("WR-0", 79.0)],
        model_versions={"team_score_v2": "team-score-v2-multi-league-20260905"},
    )
    append_prospective_decision(tmp_path, record)

    rows = read_prospective_decisions(tmp_path, "p1")
    assert len(rows) == 1
    assert rows[0]["event_type"] == EVENT_RECOMMENDATION_LOGGED
    assert rows[0]["nwr_recommended_player_id"] == "RB-1"
    assert rows[0]["pick_number"] == 5


def test_owner_action_record_tracks_whether_owner_followed_the_recommendation(tmp_path) -> None:
    rec = build_recommendation_record(
        profile_id="p1", timestamp_utc="2026-09-06T00:00:00Z", source_as_of="2026-09-05",
        league_config_summary={"team_count": 12}, pick_number=1, draft_slot=1,
        owner_roster_before=[], available_pool_size=300,
        candidates=[_candidate("RB-1", 92.0)], model_versions={},
    )
    append_prospective_decision(tmp_path, rec)

    followed = build_owner_action_record(
        profile_id="p1", timestamp_utc="2026-09-06T00:05:00Z",
        resolves_decision_id=rec.decision_id, nwr_recommended_player_id="RB-1",
        owner_actual_player_id="RB-1",
    )
    overridden = build_owner_action_record(
        profile_id="p1", timestamp_utc="2026-09-06T00:06:00Z",
        resolves_decision_id=rec.decision_id, nwr_recommended_player_id="RB-1",
        owner_actual_player_id="WR-9", override_reason="gut feeling",
    )
    append_prospective_decision(tmp_path, followed)
    append_prospective_decision(tmp_path, overridden)

    rows = read_prospective_decisions(tmp_path, "p1")
    assert len(rows) == 3
    assert rows[1]["owner_followed_recommendation"] is True
    assert rows[2]["owner_followed_recommendation"] is False
    assert rows[2]["override_reason"] == "gut feeling"
    # The original recommendation row is never rewritten.
    assert rows[0]["event_type"] == EVENT_RECOMMENDATION_LOGGED


def test_owner_action_record_requires_resolves_decision_id() -> None:
    with pytest.raises(ProspectiveDecisionLogError):
        ProspectiveDecisionRecord(
            decision_id="x", profile_id="p1", event_type=EVENT_OWNER_ACTION_RECORDED,
            timestamp_utc="2026-09-06T00:00:00Z", source_as_of="", league_config_summary={},
            pick_number=0, draft_slot=0, owner_roster_before=(), available_pool_size=0,
            candidates=(), nwr_recommended_player_id=None, model_versions={},
            resolves_decision_id=None,
        )


def test_reading_a_profile_with_no_log_yet_returns_empty(tmp_path) -> None:
    assert read_prospective_decisions(tmp_path, "never-drafted") == []
