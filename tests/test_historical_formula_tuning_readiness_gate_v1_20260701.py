from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_tuning_readiness_gate_v1_20260701"
)
V3_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
)
CONTRACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_source_contract_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "historical_formula_tuning_readiness_summary.md",
    "readiness_decision.md",
    "substrate_readiness_matrix.csv",
    "position_coverage_readiness_report.csv",
    "season_split_feasibility_report.csv",
    "target_outcome_readiness_report.csv",
    "feature_contract_readiness_report.csv",
    "null_fenced_feature_use_policy.md",
    "allowed_candidate_formula_family_matrix.csv",
    "blocked_formula_family_report.md",
    "recommended_train_validation_holdout_policy.md",
    "baseline_rerun_requirement.md",
    "candidate_search_scope_v1.md",
    "stop_conditions_for_formula_search.md",
    "leakage_and_overfit_gate_report.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}


def read_text(name: str) -> str:
    return (ARTIFACT_DIR / name).read_text(encoding="utf-8")


def test_required_readiness_artifacts_exist_and_are_nonempty() -> None:
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_readiness_decision_is_exact_and_review_only() -> None:
    decision = read_text("readiness_decision.md")
    guardrail = read_text("guardrail_report.md")

    assert "GO_LIMITED_FORMULA_SEARCH_REVIEW_ONLY" in decision
    assert "No formula search was run" in guardrail
    assert "No production formula changes were made" in guardrail
    assert "All outputs remain review-only" in guardrail


def test_readiness_gate_matches_v3_substrate_facts() -> None:
    substrate = pd.read_parquet(
        V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
    )
    matrix = pd.read_csv(ARTIFACT_DIR / "substrate_readiness_matrix.csv")
    split = pd.read_csv(ARTIFACT_DIR / "season_split_feasibility_report.csv")
    position = pd.read_csv(ARTIFACT_DIR / "position_coverage_readiness_report.csv")

    assert len(substrate) == 5518
    assert substrate["feature_season"].min() == 2012
    assert substrate["feature_season"].max() == 2024
    assert substrate["target_season"].min() == 2013
    assert substrate["target_season"].max() == 2025
    assert (substrate["target_season"] == substrate["feature_season"] + 1).all()
    assert "GO_LIMITED_FORMULA_SEARCH_REVIEW_ONLY" in set(matrix["gate_status"])
    assert split.set_index("split").loc["train", "rows"] == 3716
    assert split.set_index("split").loc["validation", "rows"] == 912
    assert split.set_index("split").loc["holdout", "rows"] == 890
    assert position.set_index("position").loc["ALL", "total_rows"] == 5518


def test_source_contract_counts_and_blocked_families_are_preserved() -> None:
    allowed = pd.read_csv(CONTRACT_DIR / "allowed_review_only_feature_contract_v1.csv")
    fenced = pd.read_csv(CONTRACT_DIR / "null_fenced_feature_contract_v1.csv")
    blocked = pd.read_csv(CONTRACT_DIR / "blocked_feature_contract_v1.csv")
    readiness = pd.read_csv(ARTIFACT_DIR / "feature_contract_readiness_report.csv")

    assert len(allowed) == 18
    assert len(fenced) == 4
    assert len(blocked) == 11
    assert "BLOCKED" in set(readiness["readiness_status"])
    assert {"routes_tprr_yprr_family", "ambiguous_rz_att"}.issubset(
        set(blocked["feature"])
    )
    for frame in [allowed, fenced, blocked]:
        for column in [
            "production_approved",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
            "formula_search_allowed_now",
        ]:
            assert not frame[column].any()


def test_null_fenced_policy_and_candidate_scope_block_forbidden_fields() -> None:
    null_policy = read_text("null_fenced_feature_use_policy.md")
    blocked = read_text("blocked_formula_family_report.md")
    scope = pd.read_csv(ARTIFACT_DIR / "allowed_candidate_formula_family_matrix.csv")

    assert "Do not fill missing values with zero" in null_policy
    assert "sensitivity-only" in null_policy.lower()
    blocked_lower = blocked.lower()
    for token in ["routes", "tprr", "yprr", "route proxies", "rz_att"]:
        assert token in blocked_lower
    assert set(scope["allowed_next_phase"]) == {True}
    assert "sensitivity" in set(scope["primary_or_sensitivity"])


def test_no_production_or_runtime_path_claims_are_opened() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ARTIFACT_DIR.iterdir()
        if path.suffix in {".md", ".csv"}
    )

    forbidden_positive_claims = [
        "production approved",
        "app wiring is approved",
        "rankings changes are approved",
        "source-truth promotion is approved",
    ]
    for phrase in forbidden_positive_claims:
        assert phrase not in combined.lower()

    assert "No production formula changes" in combined
    assert "No app wiring" in combined
    assert "No rankings" in combined
