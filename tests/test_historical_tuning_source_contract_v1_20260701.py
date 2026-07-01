from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_source_contract_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "historical_tuning_source_contract_summary.md",
    "allowed_review_only_feature_contract_v1.csv",
    "null_fenced_feature_contract_v1.csv",
    "blocked_feature_contract_v1.csv",
    "source_lineage_contract_v1.csv",
    "zero_semantics_contract_v1.csv",
    "future_tuning_gate_requirements.md",
    "formula_tuning_not_ready_reason.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}

NULL_FENCED_FEATURES = {
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
}

BLOCKED_FEATURES = {
    "red_zone_targets",
    "red_zone_carries",
    "red_zone_pass_attempts",
    "ambiguous_rz_att",
    "routes_tprr_yprr_family",
    "market_fields",
    "adp_fields",
    "vendor_fields",
    "projection_fields",
    "rank_fields",
    "current_roster_status_injury_depth_schedule_fields",
}


def test_required_source_contract_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (CONTRACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (CONTRACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_allowed_review_only_contract_has_18_non_production_features():
    allowed = pd.read_csv(CONTRACT_DIR / "allowed_review_only_feature_contract_v1.csv")

    assert len(allowed) == 18
    assert set(allowed["contract_decision"]) == {"ALLOW_REVIEW_ONLY"}
    assert not set(allowed["feature"]).intersection(NULL_FENCED_FEATURES)
    for column in [
        "production_approved",
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "formula_search_allowed_now",
    ]:
        assert not allowed[column].any()


def test_null_fenced_contract_marks_exact_four_optional_fields():
    fenced = pd.read_csv(CONTRACT_DIR / "null_fenced_feature_contract_v1.csv")

    assert len(fenced) == 4
    assert set(fenced["feature"]) == NULL_FENCED_FEATURES
    assert set(fenced["contract_decision"]) == {"ALLOW_REVIEW_ONLY_WITH_NULL_FENCE"}
    assert set(fenced["null_fenced_by"]) == {"snap_pct_missing", "air_yards_missing"}
    assert fenced["required_handling"].str.contains("do_not_fill_missing_with_zero").all()
    assert not fenced["production_approved"].any()
    assert not fenced["formula_search_allowed_now"].any()


def test_blocked_contract_keeps_forbidden_and_source_truth_families_blocked():
    blocked = pd.read_csv(CONTRACT_DIR / "blocked_feature_contract_v1.csv")

    assert set(blocked["feature"]) == BLOCKED_FEATURES
    decisions = dict(zip(blocked["feature"], blocked["contract_decision"]))
    assert decisions["ambiguous_rz_att"] == "BLOCKED_FORBIDDEN"
    assert decisions["routes_tprr_yprr_family"] == "BLOCKED_FORBIDDEN"
    for feature in [
        "market_fields",
        "adp_fields",
        "vendor_fields",
        "projection_fields",
        "rank_fields",
    ]:
        assert decisions[feature] == "BLOCKED_AS_SOURCE_TRUTH"
    assert not blocked["production_approved"].any()
    assert not blocked["formula_search_allowed_now"].any()


def test_source_lineage_and_zero_contract_require_readiness_gate():
    lineage = pd.read_csv(CONTRACT_DIR / "source_lineage_contract_v1.csv")
    zero = pd.read_csv(CONTRACT_DIR / "zero_semantics_contract_v1.csv")

    assert len(lineage) == 22
    assert lineage["formula_readiness_gate_required"].all()
    assert not lineage["production_approved"].any()
    assert not lineage["model_use_allowed"].any()
    assert not lineage["training_allowed"].any()
    assert not lineage["source_truth_allowed"].any()

    assert len(zero) == 27
    assert zero["future_formula_tuning_gate_required"].all()
    assert not zero["formula_search_allowed_now"].any()
    assert not zero["production_approved"].any()


def test_source_contract_reports_next_phase_and_not_ready_state():
    summary = (CONTRACT_DIR / "historical_tuning_source_contract_summary.md").read_text(
        encoding="utf-8"
    )
    gate = (CONTRACT_DIR / "future_tuning_gate_requirements.md").read_text(
        encoding="utf-8"
    )
    not_ready = (CONTRACT_DIR / "formula_tuning_not_ready_reason.md").read_text(
        encoding="utf-8"
    )
    handoff = (CONTRACT_DIR / "next_phase_handoff.md").read_text(encoding="utf-8")

    assert "Historical Formula Tuning Readiness Gate V1" in summary
    assert "not another substrate expansion" in summary
    assert "Future formula tuning is still not production-viable" in summary
    assert "Routes, TPRR, YPRR, and route proxy families remain blocked" in gate
    assert "Ambiguous `rz_att` remains blocked" in gate
    assert "Future formula tuning is still not production-viable" in not_ready
    assert "Do not run another substrate expansion" in handoff
