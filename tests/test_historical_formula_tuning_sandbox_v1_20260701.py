from __future__ import annotations

import csv
from pathlib import Path


ARTIFACT_DIR = Path("docs/hq/experiments/historical_formula_tuning_sandbox_v1_20260701")

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "overnight_run_log.md",
    "historical_formula_tuning_summary.md",
    "baseline_formula_inventory.md",
    "available_historical_data_inventory.csv",
    "target_outcome_definition.md",
    "train_validation_holdout_policy.md",
    "feature_admission_matrix.csv",
    "candidate_formula_variants.csv",
    "baseline_accuracy_report.csv",
    "candidate_accuracy_report.csv",
    "position_level_results.csv",
    "season_level_results.csv",
    "redzone_incremental_value_report.md",
    "overfit_and_leakage_report.md",
    "limited_data_warning.md",
    "candidate_formula_recommendation_packet.md",
    "blocked_or_deferred_feature_report.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}


def read_csv_rows(name: str) -> list[dict[str, str]]:
    with (ARTIFACT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_artifacts_exist() -> None:
    missing = sorted(name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).is_file())
    assert missing == []


def test_candidate_variants_remain_candidate_only_and_bounded() -> None:
    rows = read_csv_rows("candidate_formula_variants.csv")

    assert 1 <= len(rows) <= 40
    assert {row["candidate_only"] for row in rows} == {"True"}
    assert {row["production_approved"] for row in rows} == {"False"}
    assert {row["rank_logic_allowed"] for row in rows} == {"False"}
    assert {row["hidden_sort_allowed"] for row in rows} == {"False"}
    assert {row["recommendation_allowed"] for row in rows} == {"False"}


def test_blocked_fields_are_not_admitted() -> None:
    rows = read_csv_rows("feature_admission_matrix.csv")
    by_name = {row["feature_name"]: row for row in rows}

    for field in ["routes", "routes_run", "route_participation", "tprr", "yprr", "rz_att"]:
        assert by_name[field]["candidate_review_allowed"] == "False"
        assert by_name[field]["blocked_reason"] == "BLOCKED_PACKET_GUARDRAIL"

    admitted_rows = [row for row in rows if row["candidate_review_allowed"] == "True"]
    admitted_names = {row["feature_name"].lower() for row in admitted_rows}
    assert not {"routes", "routes_run", "route_participation", "tprr", "yprr", "rz_att"} & admitted_names
    assert {row["source_truth_allowed"] for row in admitted_rows} == {"False"}
    assert {row["training_allowed"] for row in admitted_rows} == {"False"}


def test_candidate_accuracy_report_has_candidate_only_no_production_approval() -> None:
    rows = read_csv_rows("candidate_accuracy_report.csv")

    assert rows
    assert {row["candidate_only"] for row in rows} == {"True"}
    assert {row["production_approved"] for row in rows} == {"False"}
    assert {"validation", "holdout", "eval_all"} <= {row["split"] for row in rows}


def test_summary_declines_production_tuning() -> None:
    summary = (ARTIFACT_DIR / "historical_formula_tuning_summary.md").read_text(encoding="utf-8")
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")

    assert "YELLOW_NO_TUNING_READY_CANDIDATE_REVIEW_ONLY" in summary
    assert "No candidate is tuning-ready" in summary
    assert "Production formula changes: none" in guardrail
    assert "Ambiguous `rz_att`: absent" in guardrail
