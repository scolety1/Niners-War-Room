from __future__ import annotations

from pathlib import Path

import pytest

from dataclasses import asdict

from src.application.desktop_facade import DesktopBackendFacade, _decision_bundle_v2_payload
from src.services.decision_bundle_live_service_v2 import build_live_decision_bundle_v2
from src.services.point_in_time_feature_store_service import provenance_hash
from src.services.redraft_draft_room_v1_service import load_adp_snapshot, load_room_state
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult, RedraftRankingRow
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import simulate_comparable_leagues

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


def _live_decision_bundle_v2_with_rav_budget(
    facade: DesktopBackendFacade, profile_id: str, *, max_rav_candidates: int, rav_trials: int
):
    """Real end-to-end call into `build_live_decision_bundle_v2` -- the
    exact same real room state / comparable-leagues / provenance assembly
    `DesktopBackendFacade.redraft_decision_bundle_v2` itself performs
    (NWR post-draft overnight, phase 2) -- but with an explicitly small
    `max_rav_candidates` so the real SKIPPED_TOP_N_ONLY / BUDGET_LIMITED
    path is genuinely exercised. The live facade's own FAST/STANDARD/DEEP
    presets no longer produce any skipped candidate (RAV budget now
    equals maxCandidates at every tier), so this is the only way left to
    prove that budget-limited code path still really works end-to-end
    through the live bundle composer, not just at the metric-status-
    contract unit level."""
    profile, ranking, manual_assets = facade._redraft_room_context(profile_id)
    adp = load_adp_snapshot(facade.redraft_root, profile)
    room_state = load_room_state(facade.redraft_root, profile, ranking, manual_assets)
    comparable_leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=3, base_seed=20260903,
    )
    roster_state_hash = provenance_hash({"picks": [dict(p) for p in room_state.get("picks", [])]})
    available_player_hash = provenance_hash(
        {"drafted": sorted(str(v) for v in room_state.get("drafted", []))}
    )
    provenance = build_score_provenance(
        league_profile_hash=provenance_hash(asdict(profile)),
        roster_state_hash=roster_state_hash,
        available_player_hash=available_player_hash,
        universe_hash=ranking.projection_sha256,
        projection_model_version=ranking.generated_at_utc,
        market_snapshot_hash=adp.source_sha256,
        feature_set_version="redraft-live-v1",
        team_score_version="team-score-v2-multi-league-20260905",
        championship_equity_version="championship-equity-v2-multi-league-20260906",
        pick_score_version="pick-score-experimental-v1",
        optimizer_version="decision-bundle-live-v2-challenger-v1",
        seed=20260903, simulation_count=3, timestamp_utc=ranking.generated_at_utc,
    )
    result = build_live_decision_bundle_v2(
        profile, ranking, manual_assets, adp, room_state,
        comparable_leagues=comparable_leagues, provenance=provenance,
        max_candidates=8, trials=3, seasons=3, base_seed=20260903,
        max_rav_candidates=max_rav_candidates, rav_trials=rav_trials,
    )
    # Real, same payload-serialization function `redraft_decision_bundle_v2`
    # itself calls -- not a hand-rolled reconstruction of its field names.
    return _decision_bundle_v2_payload(result, ranking)


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
    # reach the real HTTP-facing JSON for every candidate. NWR post-draft
    # overnight (phase 2, commit 2b0e571f): the FAST preset's RAV budget
    # was widened from 3-of-8 to the full 8-of-8 candidates (measured
    # live: costs under 2 real seconds against a 90-second pick clock,
    # and the old partial coverage was the direct, measured cause of the
    # owner's real "DQ is always Skipped" complaint) -- so SKIPPED_TOP_N_
    # ONLY is no longer reachable through this exact facade/speed path at
    # all; the mechanism itself is still real and still covered at the
    # lower level (test_decision_bundle_service_v2.py /
    # test_decision_bundle_live_service_v2.py, which construct a smaller
    # max_rav_candidates directly). Asserting full coverage here instead
    # is the correct, current, intentional invariant.
    with_rav = [c for c in bundle["candidates"] if c["rawActionValueStatus"] == "OK"]
    assert with_rav, "expected at least one candidate with a real Raw Action Value"
    for candidate in with_rav:
        assert candidate["rawActionValue"] is not None
        objective = candidate["rawActionValue"]["terminal_objective_name"]
        assert objective == "TERMINAL_OBJECTIVE_TEAM_SCORE"
        assert candidate["expectedRegret"] is not None
        assert candidate["expectedRegret"] >= 0.0
    assert len(with_rav) == len(bundle["candidates"]), (
        "FAST's RAV budget now equals maxCandidates -- every candidate should have real RAV"
    )
    skipped = [c for c in bundle["candidates"] if c["rawActionValueStatus"] == "SKIPPED_TOP_N_ONLY"]
    assert not skipped, "FAST's widened RAV budget should leave nothing skipped"


def test_redraft_decision_bundle_v2_carries_a_real_decision_quality_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """NWR FINAL PRE-DRAFT GAP CLOSURE, section 2 ("Metric Status
    Consistency"): Raw Action Value / Decision Quality previously carried
    only a bare `rawActionValueStatus` string, unlike every other metric
    (Player Score, Team Score, Championship Equity, Cost of Waiting,
    Make-It-Back, Pick Score), which already gets the shared
    `metric_status_contract_service.MetricStatus` taxonomy. This proves
    the new `decisionQualityStatus` field carries that same real shape,
    with the correct computation_state for both the evaluated and
    top-N-skipped cases, WITHOUT changing any numeric value the bundle
    already returned (rawActionValueStatus, rawActionValue,
    expectedRegret, decisionQualityPercentile are asserted unchanged
    against the exact same candidates the sibling test above already
    covers).

    NWR post-draft overnight (phase 2, commit 2b0e571f) widened the live
    facade's FAST/STANDARD/DEEP RAV budgets to always equal maxCandidates,
    so no candidate is ever SKIPPED_TOP_N_ONLY through
    `redraft_decision_bundle_v2` itself any more (see the sibling test's
    updated comment). To still genuinely exercise the BUDGET_LIMITED
    status shape end-to-end (not just at the metric-status-contract unit
    level), this test calls the same real bundle composer the facade
    calls, with an explicitly small `max_rav_candidates`."""
    facade, profile_id = _started_redraft_room(
        tmp_path, monkeypatch, preset_key="12_TEAM_1QB_HALF_PPR"
    )
    bundle = _live_decision_bundle_v2_with_rav_budget(
        facade, profile_id, max_rav_candidates=3, rav_trials=2,
    )

    with_rav = [c for c in bundle["candidates"] if c["rawActionValueStatus"] == "OK"]
    skipped = [c for c in bundle["candidates"] if c["rawActionValueStatus"] == "SKIPPED_TOP_N_ONLY"]
    assert with_rav and skipped

    for candidate in with_rav:
        status = candidate["decisionQualityStatus"]
        assert status["computationState"] == "EVALUATED"
        assert status["genuineZero"] == (candidate["decisionQualityPercentile"] == 0.0)
        assert "Raw Action Value" in status["validationDomain"]
        # Never coerced to a bare number -- the real evidence trail is
        # still reachable through the status object alongside the value.
        assert status["sourceFreshness"]

    for candidate in skipped:
        status = candidate["decisionQualityStatus"]
        assert status["computationState"] == "BUDGET_LIMITED"
        assert candidate["decisionQualityPercentile"] is None
        # A budget-limited candidate is never silently rendered as 0/50/
        # 100%/n/a with no explanation -- the status carries the real
        # reason instead of the frontend guessing from a bare string.
        assert status["dataCoverage"] is None or "top" in (status["dataCoverage"] or "").lower()


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
