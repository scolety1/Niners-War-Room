from __future__ import annotations

from collections import Counter

import pytest

from src.services import decision_bundle_live_service
from src.services.decision_bundle_live_service import build_live_decision_bundle
from src.services.score_provenance_service import build_score_provenance
from tests.fixtures.test18_redraft_fixture import (
    TEST18_WR_MAXIMUM,
    captured_candidate_bundle,
    make_test18_adp,
    make_test18_profile,
    make_test18_ranking,
    make_test18_room_state_at_14_06,
)


def _provenance():
    return build_score_provenance(
        league_profile_hash="test18-profile",
        roster_state_hash="test18-r14",
        available_player_hash="test18-available",
        universe_hash="test18-fixture",
        projection_model_version="fixture",
        market_snapshot_hash="none",
        feature_set_version="fixture",
        team_score_version="fixture",
        championship_equity_version="fixture",
        pick_score_version="fixture",
        optimizer_version="fixture",
        seed=20260908,
        simulation_count=1,
        timestamp_utc="2026-09-09T00:00:00-06:00",
    )


def _capture_live_candidates(monkeypatch: pytest.MonkeyPatch, profile):
    ranking = make_test18_ranking(profile)
    captured: list[str] = []

    def fake_build_decision_bundle(**kwargs):
        captured.extend(kwargs["candidate_player_ids"])
        return captured_candidate_bundle(list(kwargs["candidate_player_ids"]))

    monkeypatch.setattr(
        decision_bundle_live_service,
        "build_decision_bundle",
        fake_build_decision_bundle,
    )
    build_live_decision_bundle(
        profile,
        ranking,
        [],
        make_test18_adp(profile),
        make_test18_room_state_at_14_06(),
        comparable_leagues=[],
        provenance=_provenance(),
        max_candidates=5,
        include_cost_of_waiting=False,
        trials=1,
        seasons=1,
    )
    return captured


def test_forensic_reproduction_unconfigured_test18_profile_recommends_illegal_wrs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reproduces the observed defect before the league maximum is wired.

    The roster has the verified eight WRs.  With the desktop's historical
    empty ``roster_limits`` state, Franklin and Doubs are still rows 1-2.
    """
    profile = make_test18_profile(wr_maximum=None)
    state = make_test18_room_state_at_14_06()
    owner_positions = Counter(
        pick["position"]
        for pick in state["picks"]
        if pick["team_slot"] == profile.draft.draft_slot
    )
    assert owner_positions == Counter({"WR": 8, "QB": 2, "RB": 2, "TE": 1})

    candidates = _capture_live_candidates(monkeypatch, profile)

    assert candidates[:2] == ["troy-franklin", "romeo-doubs"]


def test_r14_acceptance_excludes_franklin_and_doubs_at_wr_eight_of_eight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Permanent Test 18 acceptance fixture for the top-N legal slate."""
    profile = make_test18_profile(wr_maximum=TEST18_WR_MAXIMUM)

    candidates = _capture_live_candidates(monkeypatch, profile)

    assert "troy-franklin" not in candidates
    assert "romeo-doubs" not in candidates
    assert candidates
    assert candidates[0] == "kyler-murray"
