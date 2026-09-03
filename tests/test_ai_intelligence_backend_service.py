"""Tests for the AI Intelligence backend skeleton (sections 19-21)."""

from __future__ import annotations

import pytest

from src.services.ai_intelligence_backend_service import (
    AiIntelligenceError,
    ImpactHypothesis,
    NewsEvent,
    PickExplanationInputs,
    RosterContext,
    append_news_event,
    explain_pick_recommendation,
    generate_beneficiary_hypotheses,
    generate_direct_impact_hypothesis,
    generate_role_uncertainty_hypotheses,
    read_news_events,
    run_impact_pipeline,
    validate_news_event,
)


def _event(**overrides) -> NewsEvent:
    base = dict(
        event_id="evt-1",
        player_id="p1",
        player_name="Star Runner",
        position="RB",
        team="SEA",
        event_type="INJURY",
        severity="HIGH",
        headline="Star Runner suffers high ankle sprain in practice",
        source="Beat Writer",
        source_url="https://example.test/article",
        published_at_utc="2026-08-16T12:00:00+00:00",
        ingested_at_utc="2026-08-16T12:05:00+00:00",
    )
    base.update(overrides)
    return NewsEvent(**base)


# --- News Scout -----------------------------------------------------------


def test_validate_news_event_accepts_a_well_formed_event() -> None:
    validate_news_event(_event())  # does not raise


@pytest.mark.parametrize(
    "overrides,match",
    [
        ({"event_id": " "}, "event_id"),
        ({"player_id": ""}, "player_id"),
        ({"event_type": "ALIEN_ABDUCTION"}, "event_type"),
        ({"severity": "CATASTROPHIC"}, "severity"),
        ({"headline": ""}, "headline"),
        ({"source": ""}, "source"),
        ({"published_at_utc": "not-a-date"}, "published_at_utc"),
    ],
)
def test_validate_news_event_rejects_malformed_fields(overrides, match) -> None:
    with pytest.raises(AiIntelligenceError, match=match):
        validate_news_event(_event(**overrides))


def test_append_and_read_news_events_round_trip(tmp_path) -> None:
    append_news_event(tmp_path, "profile-1", _event())
    append_news_event(tmp_path, "profile-1", _event(event_id="evt-2", player_id="p2"))
    all_events = read_news_events(tmp_path, "profile-1")
    assert len(all_events) == 2
    filtered = read_news_events(tmp_path, "profile-1", player_id="p2")
    assert len(filtered) == 1
    assert filtered[0].event_id == "evt-2"


def test_append_news_event_refuses_a_duplicate_event_id(tmp_path) -> None:
    append_news_event(tmp_path, "profile-1", _event())
    with pytest.raises(AiIntelligenceError, match="already recorded"):
        append_news_event(tmp_path, "profile-1", _event())


def test_read_news_events_is_empty_for_an_unknown_profile(tmp_path) -> None:
    assert read_news_events(tmp_path, "no-such-profile") == ()


# --- Impact Analyst ---------------------------------------------------------


def test_generate_direct_impact_hypothesis_for_a_known_rule() -> None:
    hypothesis = generate_direct_impact_hypothesis(_event())
    assert hypothesis.subject_player_id == "p1"
    assert hypothesis.direction == "NEGATIVE"
    assert hypothesis.confidence == "HIGH"
    assert "Star Runner" in hypothesis.hypothesis_text
    assert hypothesis.evidence_event_ids == ("evt-1",)
    assert hypothesis.requires_owner_review is False  # HIGH confidence, non-UNCERTAIN direction


def test_generate_direct_impact_hypothesis_degrades_safely_for_an_unmapped_combination() -> None:
    hypothesis = generate_direct_impact_hypothesis(_event(event_type="OTHER", severity="LOW"))
    assert hypothesis.direction == "UNCERTAIN"
    assert hypothesis.confidence == "LOW"
    assert hypothesis.requires_owner_review is True
    assert "not modeled" in hypothesis.hypothesis_text


def test_generate_direct_impact_hypothesis_rejects_a_malformed_event() -> None:
    with pytest.raises(AiIntelligenceError):
        generate_direct_impact_hypothesis(_event(event_type="NOT_REAL"))


def test_generate_beneficiary_hypotheses_for_a_high_severity_injury() -> None:
    teammates = [("p2", "Backup Runner"), ("p3", "Third String Runner")]
    hypotheses = generate_beneficiary_hypotheses(
        _event(), same_team_same_position_teammates=teammates
    )
    assert len(hypotheses) == 2
    assert {h.subject_player_id for h in hypotheses} == {"p2", "p3"}
    for hypothesis in hypotheses:
        assert hypothesis.direction == "POSITIVE"
        assert hypothesis.confidence == "LOW"
        assert hypothesis.requires_owner_review is True
        assert hypothesis.evidence_event_ids == ("evt-1",)


def test_generate_beneficiary_hypotheses_excludes_the_injured_player_themselves() -> None:
    teammates = [("p1", "Star Runner"), ("p2", "Backup Runner")]
    hypotheses = generate_beneficiary_hypotheses(
        _event(), same_team_same_position_teammates=teammates
    )
    assert {h.subject_player_id for h in hypotheses} == {"p2"}


def test_generate_beneficiary_hypotheses_is_empty_for_an_uncertain_event() -> None:
    # DEPTH_CHART_CHANGE/MEDIUM is UNCERTAIN, not NEGATIVE -- no
    # beneficiary inference should be generated from an ambiguous signal.
    event = _event(event_type="DEPTH_CHART_CHANGE", severity="MEDIUM")
    hypotheses = generate_beneficiary_hypotheses(
        event, same_team_same_position_teammates=[("p2", "Backup Runner")]
    )
    assert hypotheses == ()


def test_generate_beneficiary_hypotheses_is_empty_for_a_low_severity_injury() -> None:
    event = _event(severity="LOW")
    hypotheses = generate_beneficiary_hypotheses(
        event, same_team_same_position_teammates=[("p2", "Backup Runner")]
    )
    assert hypotheses == ()


def test_generate_beneficiary_hypotheses_is_empty_for_a_non_eligible_event_type() -> None:
    event = _event(event_type="TRADE", severity="MEDIUM")
    hypotheses = generate_beneficiary_hypotheses(
        event, same_team_same_position_teammates=[("p2", "Backup Runner")]
    )
    assert hypotheses == ()


# --- Explanation layer -------------------------------------------------------


def _explanation_inputs(**overrides) -> PickExplanationInputs:
    base = dict(
        player_id="p1",
        player_name="Star Runner",
        position="RB",
        overall_rank=12,
        replacement_adjusted_value=45.6,
        roster_position_count=1,
        position_max=4,
        adp_expected_pick=15.0,
        current_pick_number=12,
    )
    base.update(overrides)
    return PickExplanationInputs(**base)


def test_explain_pick_recommendation_includes_rank_and_value() -> None:
    explanation = explain_pick_recommendation(_explanation_inputs())
    assert "Star Runner" in explanation
    assert "#12" in explanation
    assert "45.6" in explanation


def test_explain_pick_recommendation_flags_when_market_says_it_will_last() -> None:
    explanation = explain_pick_recommendation(
        _explanation_inputs(adp_expected_pick=20.0, current_pick_number=12)
    )
    assert "lasts roughly" in explanation


def test_explain_pick_recommendation_flags_when_market_says_it_is_already_gone() -> None:
    explanation = explain_pick_recommendation(
        _explanation_inputs(adp_expected_pick=5.0, current_pick_number=12)
    )
    assert "already gone" in explanation


def test_explain_pick_recommendation_omits_adp_clause_when_unavailable() -> None:
    explanation = explain_pick_recommendation(_explanation_inputs(adp_expected_pick=None))
    assert "Market ADP" not in explanation


def test_explain_pick_recommendation_includes_impact_hypotheses_and_review_flag() -> None:
    hypothesis = ImpactHypothesis(
        hypothesis_id="direct:evt-1",
        subject_player_id="p1",
        direction="NEGATIVE",
        confidence="MEDIUM",
        hypothesis_text="Star Runner (injury, medium severity) -- possible missed game(s).",
        evidence_event_ids=("evt-1",),
        requires_owner_review=True,
        generated_at_utc="2026-08-16T12:05:00+00:00",
    )
    explanation = explain_pick_recommendation(
        _explanation_inputs(impact_hypotheses=(hypothesis,))
    )
    assert "possible missed game" in explanation
    assert "needs owner review" in explanation


# --- Sections 15-16: fixture-driven end-to-end pipeline + consequence
# chains. Every event below is a deterministic, offline fixture -- no
# live API call is required or made to prove this architecture.


def _fixture_event(**overrides) -> NewsEvent:
    base = dict(
        event_id="evt-fixture", player_id="rb1", player_name="RB One", position="RB",
        team="SEA", event_type="IR", severity="HIGH",
        headline="RB One placed on injured reserve",
        source="Beat Writer", source_url="https://example.test/a",
        published_at_utc="2026-09-10T12:00:00+00:00",
        ingested_at_utc="2026-09-10T12:05:00+00:00",
    )
    base.update(overrides)
    return NewsEvent(**base)


def test_rb1_to_ir_consequence_chain_has_all_three_real_tiers() -> None:
    """The directive's own worked example: RB1 -> IR should produce
    RB1: AVAILABILITY_DOWN (direction=NEGATIVE), Backup: OPPORTUNITY_UP
    (direction=POSITIVE), Other backfield: ROLE_UNCERTAINTY_UP
    (direction=UNCERTAIN) -- confidence/horizon/reason explicit on all
    three, not left implicit."""
    event = _fixture_event()
    context = RosterContext(
        primary_beneficiary=("rb2", "Backup Runner"),
        other_same_position_players=(
            ("rb2", "Backup Runner"), ("rb3", "Third String"), ("rb4", "Fourth String"),
        ),
    )
    hypotheses = run_impact_pipeline(event, roster_context=context)
    by_subject = {h.subject_player_id: h for h in hypotheses}

    assert by_subject["rb1"].direction == "NEGATIVE"  # AVAILABILITY_DOWN
    assert by_subject["rb1"].confidence == "HIGH"
    assert by_subject["rb1"].horizon == "REST_OF_SEASON"

    assert by_subject["rb2"].direction == "POSITIVE"  # OPPORTUNITY_UP
    assert by_subject["rb2"].confidence == "LOW"
    assert by_subject["rb2"].horizon == "REST_OF_SEASON"

    for backfield_id in ("rb3", "rb4"):
        assert by_subject[backfield_id].direction == "UNCERTAIN"  # ROLE_UNCERTAINTY_UP
        assert by_subject[backfield_id].confidence == "LOW"
        assert by_subject[backfield_id].requires_owner_review is True

    # Every hypothesis traces back to the one real event -- no invented source.
    assert all(h.evidence_event_ids == ("evt-fixture",) for h in hypotheses)
    assert len(hypotheses) == 4  # rb1 direct + rb2 beneficiary + rb3/rb4 role-uncertainty


@pytest.mark.parametrize(
    "event_kwargs,expected_direction,expected_horizon",
    [
        pytest.param(
            {"event_type": "IR", "severity": "HIGH"}, "NEGATIVE", "REST_OF_SEASON", id="IR",
        ),
        pytest.param(
            {"event_type": "SUSPENSION", "severity": "HIGH"}, "NEGATIVE", "IMMEDIATE",
            id="suspension",
        ),
        pytest.param(
            {"event_type": "TRADE", "severity": "MEDIUM"}, "UNCERTAIN", "REST_OF_SEASON",
            id="trade",
        ),
        pytest.param(
            {
                "event_type": "ROLE_CHANGE", "severity": "HIGH", "position": "QB",
                "headline": "Starting QB change announced",
            },
            "UNCERTAIN", "REST_OF_SEASON", id="starting-qb-change",
        ),
        pytest.param(
            {
                "event_type": "DEPTH_CHART_CHANGE", "severity": "MEDIUM", "position": "WR",
                "headline": "Rookie WR promoted on depth chart",
            },
            "UNCERTAIN", "REST_OF_SEASON", id="rookie-role-promotion",
        ),
        pytest.param(
            {"event_type": "INJURY", "severity": "MEDIUM", "position": "WR"}, "NEGATIVE",
            "IMMEDIATE", id="wr-injury",
        ),
    ],
)
def test_direct_hypothesis_fixtures_cover_real_world_event_shapes(
    event_kwargs, expected_direction, expected_horizon
) -> None:
    event = _fixture_event(**event_kwargs)
    hypothesis = generate_direct_impact_hypothesis(event)
    assert hypothesis.direction == expected_direction
    assert hypothesis.horizon == expected_horizon
    assert hypothesis.confidence in {"LOW", "MEDIUM", "HIGH"}
    assert hypothesis.hypothesis_text  # a real, non-empty reason every time


def test_run_impact_pipeline_with_no_roster_context_returns_only_the_direct_hypothesis() -> None:
    event = _fixture_event()
    hypotheses = run_impact_pipeline(event)
    assert len(hypotheses) == 1
    assert hypotheses[0].subject_player_id == "rb1"


def test_run_impact_pipeline_rejects_a_malformed_event_before_generating_anything() -> None:
    with pytest.raises(AiIntelligenceError):
        run_impact_pipeline(_fixture_event(event_type="NOT_A_REAL_TYPE"))


def test_pipeline_output_is_directly_consumable_by_explain_pick_recommendation() -> None:
    """"Downstream explanation availability" (section 15): the pipeline's
    own hypotheses feed explain_pick_recommendation with no adapter step."""
    event = _fixture_event(
        event_type="INJURY", severity="MEDIUM", player_id="wr1",
        player_name="Star Wideout", position="WR",
    )
    hypotheses = run_impact_pipeline(event)
    explanation = explain_pick_recommendation(
        PickExplanationInputs(
            player_id="wr1", player_name="Star Wideout", position="WR", overall_rank=20,
            replacement_adjusted_value=60.0, roster_position_count=1, position_max=4,
            adp_expected_pick=None, current_pick_number=20, impact_hypotheses=hypotheses,
        )
    )
    assert "Star Wideout" in explanation
    assert "possible missed game" in explanation or "monitor" in explanation


def test_role_uncertainty_hypotheses_exclude_the_event_subject() -> None:
    event = _fixture_event()
    others = generate_role_uncertainty_hypotheses(
        event,
        other_same_position_players=(
            ("rb1", "RB One"), ("rb2", "Backup Runner"), ("rb3", "Third String"),
        ),
    )
    subjects = {h.subject_player_id for h in others}
    # never generates a hypothesis about the event's own subject via this path
    assert "rb1" not in subjects
    assert subjects == {"rb2", "rb3"}


def test_generate_role_uncertainty_hypotheses_is_empty_for_a_low_severity_event() -> None:
    event = _fixture_event(severity="LOW")
    others = generate_role_uncertainty_hypotheses(
        event, other_same_position_players=(("rb3", "Third String"),)
    )
    assert others == ()
