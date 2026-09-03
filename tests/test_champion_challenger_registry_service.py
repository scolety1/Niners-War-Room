"""Tests for the Champion/Challenger registry (section 28)."""

from __future__ import annotations

import pytest

from src.services.champion_challenger_registry_service import (
    ChallengerRegistration,
    ChampionChallengerRegistryError,
    PromotionDecision,
    current_status,
    list_registered_challengers,
    load_registration,
    read_promotion_decisions,
    record_promotion_decision,
    register_challenger,
)


def _registration(challenger_id: str = "rookie-market-blend-v1") -> ChallengerRegistration:
    return ChallengerRegistration(
        challenger_id=challenger_id,
        champion_name="NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1",
        challenger_name="rookie-market-blend-challenger-v1",
        challenger_module="src.services.rookie_market_blend_challenger_service",
        hypothesis=(
            "The champion is a backward-looking historical-outcomes-by-draft-round prior "
            "with no current-year market signal; blending it toward real-time ESPN ADP "
            "should reduce error on rookies whose real-year role diverges from the "
            "historical pattern."
        ),
        evaluation_summary={
            "sample": "12 real-recap-matched KHA rookies",
            "champion_mean_abs_error": 54.67,
            "challenger_mean_abs_error": 35.19,
            "improved_count": 7,
            "worsened_count": 5,
        },
        registered_at_utc="2026-09-03T00:00:00+00:00",
        registered_by="codex-agent",
    )


def test_register_challenger_persists_and_reloads(tmp_path) -> None:
    register_challenger(tmp_path, _registration())
    loaded = load_registration(tmp_path, "rookie-market-blend-v1")
    assert loaded is not None
    assert loaded.champion_name == "NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1"
    assert loaded.evaluation_summary["improved_count"] == 7
    assert list_registered_challengers(tmp_path) == ("rookie-market-blend-v1",)
    assert current_status(tmp_path, "rookie-market-blend-v1") == "REGISTERED"


def test_register_challenger_refuses_a_duplicate_id(tmp_path) -> None:
    register_challenger(tmp_path, _registration())
    with pytest.raises(ChampionChallengerRegistryError, match="already registered"):
        register_challenger(tmp_path, _registration())


def test_register_challenger_requires_a_real_hypothesis_and_evidence(tmp_path) -> None:
    with pytest.raises(ChampionChallengerRegistryError, match="hypothesis"):
        register_challenger(tmp_path, _registration_with(hypothesis="   "))
    with pytest.raises(ChampionChallengerRegistryError, match="evaluation_summary"):
        register_challenger(tmp_path, _registration_with(evaluation_summary={}))


def _registration_with(**overrides) -> ChallengerRegistration:
    from dataclasses import replace

    return replace(_registration(), **overrides)


def test_current_status_is_unregistered_when_never_registered(tmp_path) -> None:
    assert current_status(tmp_path, "never-heard-of-it") == "UNREGISTERED"


def test_promotion_decision_requires_prior_registration(tmp_path) -> None:
    with pytest.raises(ChampionChallengerRegistryError, match="no registration"):
        record_promotion_decision(
            tmp_path,
            PromotionDecision(
                challenger_id="rookie-market-blend-v1",
                decided_at_utc="2026-09-03T01:00:00+00:00",
                decision="PROMOTED",
                decided_by="owner",
                reason="Backtest shows a real net improvement.",
            ),
        )


def test_promotion_decision_requires_a_non_empty_reason(tmp_path) -> None:
    register_challenger(tmp_path, _registration())
    with pytest.raises(ChampionChallengerRegistryError, match="non-empty"):
        record_promotion_decision(
            tmp_path,
            PromotionDecision(
                challenger_id="rookie-market-blend-v1",
                decided_at_utc="2026-09-03T01:00:00+00:00",
                decision="REJECTED",
                decided_by="owner",
                reason="   ",
            ),
        )


def test_promotion_decision_rejects_an_automated_decider(tmp_path) -> None:
    register_challenger(tmp_path, _registration())
    with pytest.raises(ChampionChallengerRegistryError, match="human identity"):
        record_promotion_decision(
            tmp_path,
            PromotionDecision(
                challenger_id="rookie-market-blend-v1",
                decided_at_utc="2026-09-03T01:00:00+00:00",
                decision="PROMOTED",
                decided_by="system",
                reason="Looks good.",
            ),
        )


def test_promotion_decision_rejects_an_unknown_decision_value(tmp_path) -> None:
    register_challenger(tmp_path, _registration())
    with pytest.raises(ChampionChallengerRegistryError, match="Unknown decision"):
        record_promotion_decision(
            tmp_path,
            PromotionDecision(
                challenger_id="rookie-market-blend-v1",
                decided_at_utc="2026-09-03T01:00:00+00:00",
                decision="MAYBE_LATER",
                decided_by="owner",
                reason="Not sure yet.",
            ),
        )


def test_full_lifecycle_register_reject_then_a_later_challenger_gets_promoted(tmp_path) -> None:
    register_challenger(tmp_path, _registration())
    assert current_status(tmp_path, "rookie-market-blend-v1") == "REGISTERED"

    record_promotion_decision(
        tmp_path,
        PromotionDecision(
            challenger_id="rookie-market-blend-v1",
            decided_at_utc="2026-09-03T01:00:00+00:00",
            decision="REJECTED",
            decided_by="owner",
            reason="Only a single draft's worth of backtest data; want more real seasons first.",
        ),
    )
    assert current_status(tmp_path, "rookie-market-blend-v1") == "REJECTED"
    decisions = read_promotion_decisions(tmp_path, "rookie-market-blend-v1")
    assert len(decisions) == 1
    assert decisions[0]["decision"] == "REJECTED"

    # A distinct challenger_id (v2, a new hypothesis) can be registered and
    # promoted independently -- rejecting v1 never blocks v2, and nothing
    # about v1's own history is rewritten.
    v2 = _registration_with(
        challenger_id="rookie-market-blend-v2",
        hypothesis="v2: a lower, backtest-selected blend weight to reduce the v1 regression.",
    )
    register_challenger(tmp_path, v2)
    record_promotion_decision(
        tmp_path,
        PromotionDecision(
            challenger_id="rookie-market-blend-v2",
            decided_at_utc="2026-09-10T01:00:00+00:00",
            decision="PROMOTED",
            decided_by="owner",
            reason="Backtested against 3 additional real drafts with a consistent improvement.",
        ),
    )
    assert current_status(tmp_path, "rookie-market-blend-v2") == "PROMOTED"
    assert current_status(tmp_path, "rookie-market-blend-v1") == "REJECTED"  # untouched
    assert set(list_registered_challengers(tmp_path)) == {
        "rookie-market-blend-v1",
        "rookie-market-blend-v2",
    }
