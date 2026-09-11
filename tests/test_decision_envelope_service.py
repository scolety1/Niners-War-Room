import pytest

from src.services.decision_envelope_service import build_decision_envelope


def test_build_decision_envelope_basic_shape():
    envelope = build_decision_envelope(
        task="START_SIT",
        profile_id="p1",
        league_snapshot_id="snap-abc",
        primary_recommendation={"slotType": "FLEX", "summary": "Start X over Y"},
        rationale="X projects higher this week.",
        confidence_state="NOMINAL",
        confidence_basis="Both players have a live weekly projection.",
        alternatives=[{"slotType": "WR", "summary": "Start Z"}],
        data_health={"provider": "Sleeper"},
        trace_id="trace-123",
        issues=["Weekly projections are STALE."],
    )
    payload = envelope.to_dict()
    assert payload["task"] == "START_SIT"
    assert payload["profileId"] == "p1"
    assert payload["leagueSnapshotId"] == "snap-abc"
    assert payload["primaryRecommendation"]["slotType"] == "FLEX"
    assert payload["alternatives"] == [{"slotType": "WR", "summary": "Start Z"}]
    assert payload["confidenceState"] == "NOMINAL"
    assert payload["traceId"] == "trace-123"
    assert payload["issues"] == ["Weekly projections are STALE."]
    assert payload["generatedAtUtc"]  # always stamped


def test_build_decision_envelope_rejects_unknown_confidence_state():
    with pytest.raises(ValueError):
        build_decision_envelope(
            task="WAIVER", profile_id="p1", league_snapshot_id=None,
            primary_recommendation=None, rationale="", confidence_state="VERY_SURE",
            confidence_basis="",
        )


def test_build_decision_envelope_allows_no_primary_recommendation():
    # A real "nothing to recommend" state (e.g. lineup already optimal)
    # must be expressible without a fabricated placeholder recommendation.
    envelope = build_decision_envelope(
        task="START_SIT", profile_id="p1", league_snapshot_id="snap-1",
        primary_recommendation=None, rationale="Lineup already matches NWR's optimal.",
        confidence_state="HIGH", confidence_basis="No swaps found.",
    )
    assert envelope.primary_recommendation is None
    assert envelope.alternatives == ()
