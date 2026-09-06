from __future__ import annotations

from pathlib import Path

import pytest

from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult, RedraftRankingRow

REPO_ROOT = Path(__file__).resolve().parents[1]


def _synthetic_ranking_for(profile: LeagueProfile) -> RankingResult:
    """Mirrors test_desktop_application_api.py's own `_synthetic_ranking_for`
    helper -- 240 synthetic ranked players, comfortably covering any real
    preset's team_count x rounds."""
    rows: list[RedraftRankingRow] = []
    for position, count in (("QB", 30), ("RB", 80), ("WR", 100), ("TE", 30)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank, index + 1, f"{position}-{index}", f"{position} {index}", position,
                    "TST", 400 - rank, 0, 400 - rank, 0,
                    "HIGH" if index < 5 else "MEDIUM", 1 + (rank - 1) // 10,
                    "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-08-17", False,
                    position_tier=1 + index // 6,
                )
            )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _started_redraft_room(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, preset_key: str):
    from src.services.redraft_engine_v1_service import load_profile

    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    created = facade.create_redraft_profile(
        preset_key=preset_key, league_name="V2 Facade Test League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    monkeypatch.setattr(
        facade, "_redraft_ranking_for_profile", lambda _pid: _synthetic_ranking_for(profile)
    )
    facade.start_redraft_draft_room(
        profile_id=profile_id, owner_slot=9, seed=20260906, speed="FAST", mode="MOCK"
    )
    return facade, profile_id


def test_redraft_decision_bundle_v2_returns_a_real_challenger_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, profile_id = _started_redraft_room(
        tmp_path, monkeypatch, preset_key="12_TEAM_1QB_HALF_PPR"
    )
    result = facade.redraft_decision_bundle_v2(profile_id=profile_id, speed="FAST")
    bundle = result.data["decisionBundleV2"]

    assert bundle["available"] is True
    assert bundle["v2Status"] == "OK"
    assert bundle["teamCount"] == 12
    assert bundle["currentTeamScoreV2"] is not None
    assert bundle["evidenceContext"]["team_count"] == 12
    assert len(bundle["candidates"]) == 8  # FAST preset's maxCandidates
    for candidate in bundle["candidates"]:
        assert candidate["v2Status"] == "OK"
        assert candidate["teamScoreV2"] is not None
        assert candidate["championshipEquityV2"] is not None
    # The full, unmodified V1 payload rides along underneath, unaffected.
    assert bundle["v1"]["candidates"]
    assert len(bundle["v1"]["candidates"]) == 8

    # Raw Action Value / expected regret / decision-quality percentile
    # reach the real HTTP-facing JSON for the top candidates (top-N cost
    # control -- not every one of the 8 candidates is expected to have it).
    with_rav = [c for c in bundle["candidates"] if c["rawActionValueStatus"] == "OK"]
    assert with_rav, "expected at least one candidate with a real Raw Action Value"
    for candidate in with_rav:
        assert candidate["rawActionValue"] is not None
        objective = candidate["rawActionValue"]["terminal_objective_name"]
        assert objective == "TERMINAL_OBJECTIVE_TEAM_SCORE"
        assert candidate["expectedRegret"] is not None
        assert candidate["expectedRegret"] >= 0.0
    skipped = [c for c in bundle["candidates"] if c["rawActionValueStatus"] == "SKIPPED_TOP_N_ONLY"]
    assert skipped, "expected some candidates beyond max_rav_candidates to be explicitly skipped"


def test_redraft_decision_bundle_v2_degrades_gracefully_for_unsupported_team_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 10_TEAM_1QB_STANDARD is 10-team, which IS supported -- use a league
    # shape outside {8,10,12,16} instead by building a custom profile.
    from src.services.redraft_engine_v1_service import (
        DraftContext,
        RosterSettings,
        ScoringSettings,
        create_profile,
    )

    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    template = LeagueProfile(
        "template", "6-Team Off-Grid League", 2026, 6,
        RosterSettings(k=1, dst=1, bench_size=3), ScoringSettings(reception=1.0),
        DraftContext(rounds=8),
    )
    profile = create_profile(store, template)
    facade.activate_redraft_profile(profile.profile_id)
    monkeypatch.setattr(
        facade, "_redraft_ranking_for_profile", lambda _pid: _synthetic_ranking_for(profile)
    )
    facade.start_redraft_draft_room(
        profile_id=profile.profile_id, owner_slot=1, seed=1, speed="FAST", mode="MOCK"
    )

    result = facade.redraft_decision_bundle_v2(profile_id=profile.profile_id, speed="FAST")
    bundle = result.data["decisionBundleV2"]

    assert bundle["available"] is True
    assert bundle["v2Status"].startswith("DEGRADED")
    # V1 rides along fully intact regardless.
    assert bundle["v1"]["candidates"]


def test_redraft_decision_bundle_v1_and_v2_are_both_still_reachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Confirms adding the V2 endpoint changed nothing about the existing
    V1 endpoint's behavior -- both are independently callable side by
    side."""
    facade, profile_id = _started_redraft_room(
        tmp_path, monkeypatch, preset_key="12_TEAM_1QB_HALF_PPR"
    )
    v1 = facade.redraft_decision_bundle(profile_id=profile_id, speed="FAST")
    v2 = facade.redraft_decision_bundle_v2(profile_id=profile_id, speed="FAST")

    assert v1.data["decisionBundle"]["available"] is True
    assert v2.data["decisionBundleV2"]["available"] is True
    v1_ids = {c["playerId"] for c in v1.data["decisionBundle"]["candidates"]}
    v2_ids = {c["playerId"] for c in v2.data["decisionBundleV2"]["candidates"]}
    assert v1_ids == v2_ids
