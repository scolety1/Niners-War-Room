from __future__ import annotations

import inspect

import pytest

from src.services.prospective_outcome_draft_foundation_v1_service import (
    DRAFT_EVALUATION_METHOD_DEFERRED,
    DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT,
    DraftPickOutcomeDetail,
    ProspectiveDraftOutcomeError,
    build_draft_pick_outcome_detail,
    draft_outcome_ready_for_season_long_evaluation,
)
from src.services import prospective_outcome_draft_foundation_v1_service as draft_module


# ---------------------------------------------------------------------------
# Work Unit 11 -- the directive's own required tests.
# ---------------------------------------------------------------------------


def test_full_recommendation_time_context_yields_deferred_not_insufficient():
    result = build_draft_pick_outcome_detail(
        pick_number=12,
        round_number=1,
        actual_chosen_player_id="p_actual",
        recommended_player_id="p_reco",
        recommendation_time_candidate_set_ids=["p_reco", "p_alt1", "p_alt2"],
    )
    assert result.evaluation_method == DRAFT_EVALUATION_METHOD_DEFERRED
    assert result.recommended_player_id == "p_reco"
    assert result.recommendation_time_candidate_set_ids == ("p_reco", "p_alt1", "p_alt2")
    # Season-long dimensions stay honestly None this cycle -- no forced
    # 2026 season-long conclusion.
    assert result.season_points is None
    assert result.starts is None
    assert result.weeks_usable is None
    assert result.roster_utility is None
    assert result.replacement_value is None


def test_no_recorded_candidate_set_is_insufficient_decision_context():
    """The directive's own required test: a pick with no recorded
    recommendation-time context must be INSUFFICIENT_DECISION_CONTEXT, not
    backfilled with a guess."""

    result = build_draft_pick_outcome_detail(
        actual_chosen_player_id="p_actual",
        recommended_player_id="p_reco_guess",  # caller supplies a guess anyway
        recommendation_time_candidate_set_ids=(),  # but never genuinely recorded
    )
    assert result.evaluation_method == DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT
    # The guess must NEVER leak into recommended_player_id -- this is the
    # "never retroactively reconstruct" rule, proven directly.
    assert result.recommended_player_id is None
    assert result.recommendation_time_candidate_set_ids == ()


def test_no_recommended_player_id_with_a_real_candidate_set_is_still_insufficient_context():
    result = build_draft_pick_outcome_detail(
        actual_chosen_player_id="p_actual",
        recommended_player_id=None,
        recommendation_time_candidate_set_ids=["p_alt1", "p_alt2"],
    )
    assert result.evaluation_method == DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT
    assert result.recommended_player_id is None


def test_recommended_player_not_a_genuine_candidate_set_member_is_insufficient_context():
    """A 'recommended' id that was never actually a recorded candidate is
    not a genuine recommendation-time fact -- never trusted at face value."""

    result = build_draft_pick_outcome_detail(
        actual_chosen_player_id="p_actual",
        recommended_player_id="p_not_a_real_candidate",
        recommendation_time_candidate_set_ids=["p_alt1", "p_alt2"],
    )
    assert result.evaluation_method == DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT
    assert result.recommended_player_id is None
    # The real, genuinely-captured candidate set is still preserved/visible
    # even though the claimed recommendation didn't match it.
    assert result.recommendation_time_candidate_set_ids == ("p_alt1", "p_alt2")


# ---------------------------------------------------------------------------
# Injury must be a SEPARATE dimension -- never proof of a bad decision.
# ---------------------------------------------------------------------------


def test_injury_is_recorded_as_a_separate_field_from_decision_quality():
    healthy = build_draft_pick_outcome_detail(
        actual_chosen_player_id="p_actual",
        recommended_player_id="p_actual",
        recommendation_time_candidate_set_ids=["p_actual", "p_alt"],
        injury_designation=None,
        weeks_missed_to_injury=None,
    )
    injured = build_draft_pick_outcome_detail(
        actual_chosen_player_id="p_actual",
        recommended_player_id="p_actual",
        recommendation_time_candidate_set_ids=["p_actual", "p_alt"],
        injury_designation="IR",
        weeks_missed_to_injury=9,
    )
    # A genuine injury-luck fact never changes evaluation_method or any
    # other decision-quality-relevant field -- only its own two fields
    # differ between an otherwise-identical healthy/injured pick.
    assert healthy.evaluation_method == injured.evaluation_method == DRAFT_EVALUATION_METHOD_DEFERRED
    assert healthy.recommended_player_id == injured.recommended_player_id
    assert healthy.recommendation_time_candidate_set_ids == injured.recommendation_time_candidate_set_ids
    assert healthy.injury_designation is None
    assert injured.injury_designation == "IR"
    assert injured.weeks_missed_to_injury == 9


def test_injury_alone_on_insufficient_context_pick_does_not_upgrade_it():
    """An injured player with no recorded recommendation-time context is
    still INSUFFICIENT_DECISION_CONTEXT -- injury data can never substitute
    for missing decision-quality context, in either direction."""

    result = build_draft_pick_outcome_detail(
        actual_chosen_player_id="p_actual",
        recommendation_time_candidate_set_ids=(),
        injury_designation="OUT",
        weeks_missed_to_injury=17,
    )
    assert result.evaluation_method == DRAFT_EVALUATION_METHOD_INSUFFICIENT_CONTEXT
    assert result.injury_designation == "OUT"


def test_module_source_never_asserts_injury_proves_a_bad_decision():
    """Structural (not just promised) proof: scan this module's own source
    text for the forbidden claim pattern -- injury language must never
    appear alongside a 'proves'/'proof of'/'means the pick was bad' claim."""

    source = inspect.getsource(draft_module).lower()
    assert "injury" in source  # sanity: the module does discuss injury at all
    forbidden_pairs = [
        ("injury", "proof of a bad"),
        ("injury", "proves the pick"),
        ("injury bust", "bad decision"),
        ("injured", "bad pick"),
    ]
    for first, second in forbidden_pairs:
        assert not (first in source and second in source), (
            f"Forbidden co-occurring phrase pattern found: {first!r} / {second!r}"
        )
    # The one explicit, allowed phrasing: injury is documented as SEPARATE
    # from / never proof of decision quality.
    assert "never" in source


# ---------------------------------------------------------------------------
# Hard boundary -- never touches marginal_roster_utility_v2 or any draft
# recommendation-generation logic.
# ---------------------------------------------------------------------------


def test_module_never_imports_any_hard_boundary_dependency():
    """The module docstring DISCLOSES `marginal_roster_utility_v2` (it must
    -- explaining why it's not touched is the whole point), so this checks
    real `import` statements, not prose mentions."""

    import_lines = [
        line.strip()
        for line in inspect.getsource(draft_module).splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]
    for forbidden in (
        "marginal_roster_utility_v2",
        "shadow_numeric_authorities_service",
        "league_workspace_context_service",
        "lifecycle_resolver",
        "player_availability_status",
    ):
        assert not any(forbidden in line.lower() for line in import_lines), (
            f"Forbidden hard-boundary import found: {forbidden!r}"
        )


# ---------------------------------------------------------------------------
# Structural validation / schema shape
# ---------------------------------------------------------------------------


def test_actual_chosen_player_id_is_required():
    with pytest.raises(ProspectiveDraftOutcomeError):
        build_draft_pick_outcome_detail(actual_chosen_player_id="")


def test_direct_construction_rejects_unknown_evaluation_method():
    with pytest.raises(ProspectiveDraftOutcomeError):
        DraftPickOutcomeDetail(
            pick_number=1, round_number=1, actual_chosen_player_id="p1",
            recommended_player_id=None, recommendation_time_candidate_set_ids=(),
            evaluation_method="NOT_A_REAL_METHOD",
            season_points=None, starts=None, weeks_usable=None, roster_utility=None,
            replacement_value=None, injury_designation=None, weeks_missed_to_injury=None, notes="",
        )


def test_direct_construction_rejects_recommended_id_outside_candidate_set():
    with pytest.raises(ProspectiveDraftOutcomeError):
        DraftPickOutcomeDetail(
            pick_number=1, round_number=1, actual_chosen_player_id="p1",
            recommended_player_id="not_in_set", recommendation_time_candidate_set_ids=("p_a", "p_b"),
            evaluation_method=DRAFT_EVALUATION_METHOD_DEFERRED,
            season_points=None, starts=None, weeks_usable=None, roster_utility=None,
            replacement_value=None, injury_designation=None, weeks_missed_to_injury=None, notes="",
        )


def test_to_detail_dict_shape():
    result = build_draft_pick_outcome_detail(
        pick_number=5, round_number=1, actual_chosen_player_id="p1",
        recommended_player_id="p1", recommendation_time_candidate_set_ids=["p1", "p2"],
        injury_designation="QUESTIONABLE", weeks_missed_to_injury=1, notes="test",
    )
    payload = result.to_detail_dict()
    assert payload["kind"] == "DRAFT_PICK_V1"
    assert payload["actualChosenPlayerId"] == "p1"
    assert payload["recommendedPlayerId"] == "p1"
    assert payload["recommendationTimeCandidateSetIds"] == ["p1", "p2"]
    assert payload["evaluationMethod"] == DRAFT_EVALUATION_METHOD_DEFERRED
    assert payload["injuryDesignation"] == "QUESTIONABLE"
    assert payload["weeksMissedToInjury"] == 1
    assert payload["seasonPoints"] is None
    assert payload["rosterUtility"] is None


def test_draft_outcome_ready_for_season_long_evaluation_is_always_false_this_cycle():
    assert draft_outcome_ready_for_season_long_evaluation(season=2026, current_season=2026) is False
    assert draft_outcome_ready_for_season_long_evaluation(season=2020, current_season=2026) is False
