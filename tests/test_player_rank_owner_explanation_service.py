from __future__ import annotations

from src.services.player_rank_owner_explanation_service import (
    owner_rank_explanation,
    owner_rank_reason_bullets,
)


def test_owner_rank_receipts_classify_help_hurt_neutral_and_missing() -> None:
    _summary, receipts, _caveat = owner_rank_explanation(
        {
            "player_name": "Test Player",
            "nwr_rank": "10",
            "nwr_dynasty_score": "90",
            "candidate_adjustment": "-1.5",
            "candidate_evidence_fields_used": (
                "positive_vorp_points|lifecycle_modifier_review|role_archetype|warning_flags"
            ),
            "positive_vorp_points": "2.0",
            "lifecycle_modifier_review": "0.8",
            "role_archetype": "Outside receiver",
            "warning_flags": "",
        },
        total_ranked=240,
    )

    effects = set(receipts["Effect"])
    assert {"HELPS", "HURTS", "NEUTRAL", "MISSING"} <= effects


def test_no_extra_lift_reason_stays_neutral_even_when_it_mentions_elite() -> None:
    row = {
        "player_name": "Puka Nacua",
        "nwr_rank": "1",
        "nwr_dynasty_score": "99",
        "candidate_reason_codes": "elite_wr_already_supported_no_extra_lift",
    }

    _summary, receipts, _caveat = owner_rank_explanation(row, total_ranked=240)
    bullets = owner_rank_reason_bullets(row)

    assert receipts.iloc[0]["Effect"] == "NEUTRAL"
    assert bullets == ("Gate context: Elite WR already supported no extra lift.",)


def test_reason_codes_explain_caps_and_exceptions_without_named_tuning() -> None:
    bullets = owner_rank_reason_bullets(
        {
            "candidate_reason_codes": (
                "partial_first_down_confidence_cap|"
                "no_premium_te_small_gap_cap|"
                "te_upper_band_guard_v2_elite_exception"
            )
        },
        limit=10,
    )

    assert any("Partial first-down coverage caps confidence" in value for value in bullets)
    assert any("No-premium TE discipline caps" in value for value in bullets)
    assert any("clears the upper-band exception" in value for value in bullets)
