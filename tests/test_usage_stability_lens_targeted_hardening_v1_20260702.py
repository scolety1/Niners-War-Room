from pathlib import Path
import csv


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs" / "hq" / "experiments" / "usage_stability_lens_targeted_hardening_v1_20260702"


REQUIRED_FILES = {
    "artifact_manifest.md",
    "usage_stability_lens_hardening_summary.md",
    "fixed_hardening_variant_definitions.csv",
    "historical_validation_metric_comparison.csv",
    "historical_holdout_metric_comparison.csv",
    "current_board_key_player_comparison.csv",
    "cornerstone_stability_casebook.md",
    "injury_context_watchlist_policy.md",
    "garrett_wilson_watchlist_decision.md",
    "nabers_watchlist_decision.md",
    "ceedee_jefferson_bowers_stability_report.md",
    "usage_lens_vs_rank_replacement_decision.md",
    "selected_hardening_decision.md",
    "remaining_risk_report.md",
    "human_review_update.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (PACKET / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_artifacts_exist() -> None:
    assert PACKET.exists()
    assert REQUIRED_FILES == {path.name for path in PACKET.iterdir() if path.is_file()}


def test_decision_is_usage_lens_only() -> None:
    decision = (PACKET / "selected_hardening_decision.md").read_text(encoding="utf-8")
    assert "Decision label: `KEEP_AS_USAGE_LENS_ONLY_NO_RANK_VARIANT`" in decision
    assert "Selected review posture: `usage_lens_with_cornerstone_warning_flags`" in decision
    assert "No rank-changing hardening variant is selected" in decision


def test_fixed_variants_and_no_search_invariants() -> None:
    rows = read_csv("fixed_hardening_variant_definitions.csv")
    assert {row["variant_id"] for row in rows} == {
        "current_usage_stability_lens",
        "proven_cornerstone_stability_guard",
        "injury_context_discount_preserver",
        "young_wr_te_stability_selective_guard",
        "usage_lens_with_cornerstone_warning_flags",
        "lens_only_no_rank_replacement",
    }
    for row in rows:
        assert row["formula_search_run"] == "false"
        assert row["holdout_used_for_selection"] == "false"
        assert row["market_source_truth_used"] == "false"
        assert row["player_name_exception_used"] == "false"
        assert row["blocked_feature_used"] == "false"


def test_metric_reports_load_and_holdout_not_used_for_selection() -> None:
    for name in [
        "historical_validation_metric_comparison.csv",
        "historical_holdout_metric_comparison.csv",
    ]:
        rows = read_csv(name)
        assert len(rows) == 6
        assert {row["holdout_used_for_selection"] for row in rows} == {"false"}
        assert all(row["rows"] for row in rows)
        assert all(row["mae"] for row in rows)
        assert all(row["spearman"] for row in rows)


def test_current_board_review_cases_are_classified_without_formula_exceptions() -> None:
    rows = read_csv("current_board_key_player_comparison.csv")
    by_name = {row["player_name"]: row for row in rows}
    for name in [
        "Justin Jefferson",
        "CeeDee Lamb",
        "Brock Bowers",
        "Malik Nabers",
        "Garrett Wilson",
        "DeVonta Smith",
        "Jaylen Waddle",
        "DK Metcalf",
        "Emeka Egbuka",
        "Tony Pollard",
    ]:
        assert name in by_name
        assert by_name[name]["production_rank_change_allowed"] == "false"
        assert by_name[name]["market_source_truth_used"] == "false"
        assert by_name[name]["player_name_exception_used"] == "false"
    assert by_name["Malik Nabers"]["watchlist_label"] == "INJURY_TIMELINE_DISCOUNT_WATCHLIST"
    assert by_name["Garrett Wilson"]["watchlist_label"] == "EXPLAINABLE_WATCHLIST"
    assert by_name["CeeDee Lamb"]["watchlist_label"] == "DYNASTY_STABILITY_PROTECTION_CASE"
    assert by_name["Justin Jefferson"]["watchlist_label"] == "DYNASTY_STABILITY_PROTECTION_CASE"
    assert by_name["Brock Bowers"]["watchlist_label"] == "DYNASTY_STABILITY_PROTECTION_CASE"


def test_guardrail_report_keeps_approvals_closed() -> None:
    text = (PACKET / "guardrail_report.md").read_text(encoding="utf-8")
    for flag in [
        "production_formula_approved: `false`",
        "model_training_approved: `false`",
        "rank_behavior_change_approved: `false`",
        "app_wiring_approved: `false`",
        "hidden_sort_approved: `false`",
        "recommendations_approved: `false`",
        "source_truth_promotion_approved: `false`",
        "candidate_output_wired: `false`",
    ]:
        assert flag in text


def test_blocked_feature_language_is_blocked_or_absent() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in PACKET.iterdir() if path.is_file())
    assert "market_source_truth_used,true" not in combined.lower()
    assert "market source truth approved" not in combined.lower()
    assert "production_promotion_approved,true" not in combined.lower()
    assert "production_promotion_approved: `true`" not in combined.lower()
    assert "route/TPRR/YPRR" in combined or "routes, TPRR, YPRR" in combined
    assert "`rz_att`" in combined
