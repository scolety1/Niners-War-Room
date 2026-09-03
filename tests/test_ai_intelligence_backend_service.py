"""Tests for the AI Intelligence backend skeleton (sections 19-21)."""

from __future__ import annotations

import pytest

from src.services.ai_intelligence_backend_service import (
    AiIntelligenceError,
    ImpactHypothesis,
    NewsEvent,
    PickExplanationInputs,
    append_news_event,
    explain_pick_recommendation,
    generate_beneficiary_hypotheses,
    generate_direct_impact_hypothesis,
    read_news_events,
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
