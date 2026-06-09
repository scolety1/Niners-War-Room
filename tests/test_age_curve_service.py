from __future__ import annotations

from src.services.age_curve_service import age_curve_profile


def test_age_curve_profile_marks_rb_cliff_and_fragility() -> None:
    profile = age_curve_profile(
        "RB",
        29.0,
        workload_score=88.0,
        injury_score=62.0,
    )

    assert profile.age_bucket == "cliff_risk_window"
    assert profile.age_curve_score < 70
    assert profile.age_warning == "age_cliff_risk_window"
    assert "rb_age_injury_workload_fragility" in profile.age_interaction_flags
    assert profile.source_status == "derived_real_data"


def test_age_curve_profile_keeps_qb_prime_from_being_penalized() -> None:
    profile = age_curve_profile("QB", 29.0)

    assert profile.age_bucket == "prime_window"
    assert profile.age_curve_score >= 90
    assert profile.age_warning == ""


def test_age_curve_profile_marks_missing_age_as_neutral_imputation() -> None:
    profile = age_curve_profile("WR", None)

    assert profile.age_bucket == "age_not_available"
    assert profile.age_curve_score == 50.0
    assert profile.age_warning == "age_not_available"
    assert profile.source_status == "neutral_imputation"
