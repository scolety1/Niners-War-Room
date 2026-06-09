from __future__ import annotations

from src.services.warning_language_service import (
    NO_ACTIVE_WARNING,
    confidence_explanation,
    confidence_label,
    warning_phrase,
    warning_summary,
)


def test_warning_phrase_translates_core_review_codes() -> None:
    assert warning_phrase("data_warning") == "source data needs review"
    assert (
        warning_phrase("data_warning_stale_sources")
        == "stale source: imported NFL stats stop before current snapshot"
    )
    assert warning_phrase("data_warning_missing_inputs") == "missing core football inputs"
    assert warning_phrase("model_warning") == "model output needs review"
    assert warning_phrase("model_warning_role_or_keeper_fragility") == "role or keeper fragility"
    assert warning_phrase("review_needed_low_confidence") == "low confidence"
    assert warning_phrase("using_stale_sources") == "stale source"
    assert warning_phrase("missing_projection") == "missing projection"
    assert warning_phrase("role_imputed") == "imputed role"
    assert warning_phrase("identity_ambiguous") == "identity review"
    assert warning_phrase("low_confidence") == "low confidence"
    assert warning_phrase("one_feature_driven_rank") == "one-feature-driven rank"
    assert warning_phrase("market_disagreement") == "market disagreement"
    assert warning_phrase("rb_workload_injury_fragility") == "RB workload/injury fragility"
    assert warning_phrase("replaceable_no_premium_te") == (
        "replaceable TE in no-premium scoring"
    )
    assert warning_phrase("local_baseline_projection_not_independent") == (
        "projection is a local baseline, not forecast"
    )
    assert warning_phrase("missing_participation_proxy") == (
        "missing route/participation data; using proxy role evidence"
    )
    assert warning_phrase("stale_lve_scoring_source") == "stale production source"
    assert warning_phrase("accepted_source_gap_confidence_drag") == (
        "accepted optional source gap; confidence penalty retained"
    )


def test_warning_summary_dedupes_and_hides_ready_codes() -> None:
    assert warning_summary("ready", "", None) == NO_ACTIVE_WARNING
    assert warning_summary(
        "data_warning|using_stale_sources|data_warning_market_source_stale",
        "market_gap",
    ) == "source data needs review; stale source; market disagreement"


def test_warning_summary_keeps_unknown_codes_readable_without_raw_underscores() -> None:
    assert warning_summary("injury_source_missing_for_test", default="") == (
        "injury source missing for test"
    )
    assert warning_summary("formula_proxy_from_role_security", default="") == (
        "uses role security proxy"
    )


def test_confidence_label_and_explanation_use_plain_english() -> None:
    assert confidence_label(90) == "strong"
    assert confidence_label(80) == "usable"
    assert confidence_label(70) == "review"
    assert confidence_label(50) == "weak"
    assert confidence_label(30) == "blocked"

    explanation = confidence_explanation(62, "missing_participation_proxy")

    assert "Weak confidence" in explanation
    assert "Score 62.0" in explanation
    assert "missing route/participation data" in explanation
