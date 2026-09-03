from src.services.decision_bundle_explanation_service import (
    INSUFFICIENT_EVIDENCE,
    explain_decision_bundle,
    verify_explanation_matches_bundle,
)
from src.services.decision_bundle_service import CandidateBundle, DecisionBundle
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import (
    ChampionshipEquityAssumptions,
    ChampionshipEquityResult,
    TeamScoreResult,
)


def _provenance():
    return build_score_provenance(
        league_profile_hash="lp", roster_state_hash="rs", available_player_hash="ap",
        universe_hash="uh", projection_model_version="proj-v1", market_snapshot_hash="mk",
        feature_set_version="fs-v1", team_score_version="ts-v1",
        championship_equity_version="ce-v1", pick_score_version="ps-v1",
        optimizer_version="opt-v1", seed=7, simulation_count=10,
        timestamp_utc="2026-09-03T12:00:00Z",
    )


def _team_score(percentile: float) -> TeamScoreResult:
    return TeamScoreResult(
        percentile=percentile, roster_value=100.0, population_size=50,
        population_mean=50.0, population_median=50.0, population_stdev=10.0,
    )


def _equity(win_probability: float, se: float = 0.01) -> ChampionshipEquityResult:
    return ChampionshipEquityResult(
        win_probability=win_probability, standard_error=se, seasons_simulated=200,
        league_size=10, assumptions=ChampionshipEquityAssumptions(),
    )


def _bundle(candidates: tuple[CandidateBundle, ...]) -> DecisionBundle:
    return DecisionBundle(
        version="decision-bundle-v1",
        current_team_score=_team_score(50.0),
        current_championship_equity=_equity(0.1),
        candidates=candidates,
        provenance=_provenance(),
        latency_seconds=0.01,
        simulation_metadata={"trials": 2, "seasons": 20, "base_seed": 1},
    )


def _candidate(player_id: str, **overrides) -> CandidateBundle:
    defaults = dict(
        player_id=player_id, player_score=None, team_score_after=60.0,
        team_score_delta=5.0, championship_equity_after=0.15, equity_gain=0.05,
        cost_of_waiting=2.0, make_it_back_probability=0.6, raw_decision_utility=10.0,
        team_score_utility_component=5.0, equity_utility_component=5.0,
        pick_score=80.0, action="TAKE_NOW", warnings=(),
        uncertainty="LOW_MODEL_UNCERTAINTY (SE=0.0100)",
    )
    defaults.update(overrides)
    return CandidateBundle(**defaults)


def test_explanation_says_insufficient_evidence_when_no_candidates_exist() -> None:
    explanation = explain_decision_bundle(_bundle(()))
    assert explanation.has_evidence is False
    assert INSUFFICIENT_EVIDENCE in explanation.text


def test_explanation_names_the_real_top_candidate_and_cites_real_reasons() -> None:
    top = _candidate("RB-1", pick_score=90.0, team_score_delta=8.0, equity_gain=0.06)
    runner_up = _candidate("WR-2", pick_score=70.0, team_score_delta=2.0, equity_gain=0.01)
    explanation = explain_decision_bundle(_bundle((top, runner_up)))
    assert explanation.top_player_id == "RB-1"
    assert "RB-1" in explanation.text
    assert any("Team Score" in reason for reason in explanation.primary_reasons)


def test_explanation_surfaces_the_directives_own_worked_example_shape() -> None:
    # Runner-up has a HIGHER standalone Player Score but the top pick still
    # wins because it adds more Team Score -- the explanation must say so.
    top = _candidate("A", player_score=70.0, team_score_delta=8.0, pick_score=90.0)
    runner_up = _candidate("B", player_score=75.0, team_score_delta=2.0, pick_score=70.0)
    explanation = explain_decision_bundle(_bundle((top, runner_up)))
    assert explanation.runner_up_note is not None
    assert "higher standalone Player Score" in explanation.runner_up_note
    assert "B" in explanation.runner_up_note


def test_explanation_includes_warnings_as_caveats() -> None:
    top = _candidate("A", warnings=("No standalone Player Score supplied for this candidate.",))
    explanation = explain_decision_bundle(_bundle((top,)))
    assert "Caveats:" in explanation.text
    assert explanation.caveats == top.warnings


def test_verify_explanation_matches_bundle_finds_no_contradiction_for_a_real_explanation() -> None:
    top = _candidate("A", pick_score=90.0)
    runner_up = _candidate("B", pick_score=70.0)
    bundle = _bundle((top, runner_up))
    explanation = explain_decision_bundle(bundle)
    assert verify_explanation_matches_bundle(explanation, bundle) == ()


def test_verify_explanation_matches_bundle_detects_a_fabricated_top_player() -> None:
    top = _candidate("A", pick_score=90.0)
    bundle = _bundle((top,))
    real_explanation = explain_decision_bundle(bundle)
    fabricated = real_explanation.__class__(
        has_evidence=True, top_player_id="SOMEONE_ELSE",
        top_pick_score=real_explanation.top_pick_score,
        primary_reasons=real_explanation.primary_reasons,
        runner_up_player_id=None, runner_up_note=None,
        caveats=(), text="fabricated text",
    )
    contradictions = verify_explanation_matches_bundle(fabricated, bundle)
    assert len(contradictions) >= 1
    assert any("top_player_id" in c for c in contradictions)
