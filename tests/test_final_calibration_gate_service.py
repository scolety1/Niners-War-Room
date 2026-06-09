from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.services import final_calibration_gate_service as gate_service
from src.services.final_calibration_gate_service import (
    build_final_calibration_gate,
    final_calibration_gate_rows,
    final_calibration_gate_summary_row,
)

BRIDGE_EXPLANATION = "This player is being treated as a young NFL bridge asset because..."


def test_final_calibration_gate_blocks_current_sample_until_audits_clear() -> None:
    report = build_final_calibration_gate("sample_data/2026_pre_declaration")
    summary = final_calibration_gate_summary_row(report)
    rows = final_calibration_gate_rows(report)

    assert report.passed is False
    assert summary["decision_ready_gate"] == "hold"
    assert summary["final_decision_badge"] in {
        "Needs Data",
        "Calibration Needs Review",
        "Review Only",
    }
    assert summary["final_decision_badge"] != "Decision Ready"
    assert summary["calibration_badge"] in {
        "Model Calibration Blocked",
        "Model Calibration Needs Review",
    }
    assert {row["gate"] for row in rows} == {
        "model_v4_rebuild_freeze",
        "real_draft_pool_loaded",
        "source_coverage_thresholds",
        "identity_audit_pass",
        "lifecycle_model_separation",
        "sanity_fixture_pass",
        "ranking_outlier_review",
        "rookie_replay_no_leakage_pass",
        "final_ui_smoke_pass",
        "draft_ux_smoke_pass",
    }
    assert {row["requirement"] for row in rows} == {
        "Model v4 Rebuild Freeze",
        "Draft Pool Loaded",
        "Source Coverage Clear",
        "Identity Audit Pass",
        "Lifecycle/Model Separation Pass",
        "Named Sanity Fixtures Pass",
        "Outlier Review Accepted/Resolved",
        "Rookie Replay No-Leakage Pass",
        "Core App Pages Load",
        "Draft UX Smoke Pass",
    }
    assert next(row for row in rows if row["gate"] == "real_draft_pool_loaded")[
        "status"
    ] in {"ready", "blocked"}
    assert next(row for row in rows if row["gate"] == "source_coverage_thresholds")[
        "status"
    ] in {"ready", "review", "blocked"}
    assert next(row for row in rows if row["gate"] == "identity_audit_pass")[
        "status"
    ] in {"ready", "review", "blocked"}
    assert next(row for row in rows if row["gate"] == "lifecycle_model_separation")[
        "status"
    ] in {"ready", "blocked"}
    assert next(row for row in rows if row["gate"] == "ranking_outlier_review")[
        "status"
    ] in {"review", "blocked"}
    assert next(row for row in rows if row["gate"] == "rookie_replay_no_leakage_pass")[
        "status"
    ] == "ready"


def test_final_calibration_gate_blocks_missing_rookie_replay_contract(
    tmp_path: Path,
) -> None:
    report = build_final_calibration_gate(
        "sample_data/2026_pre_declaration",
        historical_rookie_predraft_path=tmp_path / "missing_predraft.csv",
    )
    rows = final_calibration_gate_rows(report)

    rookie_gate = next(
        row for row in rows if row["gate"] == "rookie_replay_no_leakage_pass"
    )
    assert report.passed is False
    assert rookie_gate["status"] == "blocked"
    assert rookie_gate["blocker"] == "Blocked: Rookie Replay No-Leakage Pass."
    assert "without future NFL stats" in rookie_gate["why_it_matters"]
    assert "Missing historical rookie predraft" in rookie_gate["detail"]


def test_final_calibration_gate_blocks_missing_visible_ui_page(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    (app_root / "pages").mkdir(parents=True)

    report = build_final_calibration_gate(
        "sample_data/2026_pre_declaration",
        app_dir=app_root,
    )
    rows = final_calibration_gate_rows(report)
    ui_gate = next(row for row in rows if row["gate"] == "final_ui_smoke_pass")

    assert ui_gate["status"] == "blocked"
    assert "Missing visible app pages" in ui_gate["detail"]


def test_final_calibration_gate_blocks_missing_real_draft_pool(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_draft_room",
        lambda *_args, **_kwargs: SimpleNamespace(
            available_pool_source_rows=[
                {
                    "source": "rookies",
                    "status": "missing_required",
                    "required": True,
                    "review_only": False,
                },
                {
                    "source": "released veterans",
                    "status": "loaded",
                    "required": True,
                    "review_only": False,
                },
            ],
            available_pool_warnings=["Review needed: no rookies are loaded."],
            rookie_rows=[],
            released_veteran_rows=[{"asset_type": "released_veteran"}],
            manual_draftable_rows=[],
        ),
    )

    check = gate_service._real_draft_pool_gate("pack")

    assert check.status == "blocked"
    assert check.severity == "error"
    assert "missing required pool sources: rookies" in check.detail


def test_missing_released_veterans_holds_draft_ready_not_roster_declaration(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_draft_room",
        lambda *_args, **_kwargs: SimpleNamespace(
            available_pool_source_rows=[
                {
                    "source": "rookies",
                    "status": "loaded",
                    "required": True,
                    "review_only": False,
                },
                {
                    "source": "released veterans",
                    "status": "missing_required",
                    "required": True,
                    "review_only": False,
                },
                {
                    "source": "free agents",
                    "status": "loaded",
                    "required": True,
                    "review_only": False,
                },
            ],
            available_pool_warnings=[
                "Draft warning: no released veterans are loaded yet."
            ],
            rookie_rows=[{"asset_type": "rookie"}],
            released_veteran_rows=[{"asset_type": "free_agent"}],
            manual_draftable_rows=[],
        ),
    )

    check = gate_service._real_draft_pool_gate("pack")

    assert check.status == "review"
    assert check.severity == "warning"
    assert "Roster-declaration drop/shop decisions" in check.detail
    assert "mixed offline draft board is not draft-ready" in check.detail


def test_final_calibration_gate_blocks_unresolved_high_outliers(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_model_outlier_report",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                {
                    "bucket": "True Ranking Weirdness",
                    "severity": "high",
                    "player_id": "player_one",
                    "outlier_type": "ranking_gap",
                    "component": "",
                    "source_feature": "",
                }
            ],
        ),
    )

    check = gate_service._ranking_outlier_gate("pack", Path("sources"))

    assert check.status == "blocked"
    assert check.severity == "error"
    assert "high-severity" in check.detail


def test_final_calibration_gate_allows_accepted_high_outliers(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_model_outlier_report",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            invalid_acceptance_rows=[],
            rows=[
                {
                    "bucket": "True Ranking Weirdness",
                    "severity": "high",
                    "player_id": "player_one",
                    "outlier_type": "ranking_gap",
                    "component": "",
                    "source_feature": "",
                    "acceptance_status": "accepted",
                }
            ],
        ),
    )

    check = gate_service._ranking_outlier_gate("pack", Path("sources"))

    assert check.status == "ready"
    assert check.severity == "info"
    assert "1 outliers have audited acceptance rows" in check.detail


def test_final_calibration_gate_blocks_invalid_outlier_acceptances(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_model_outlier_report",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            invalid_acceptance_rows=[
                {
                    "player_id": "player_one",
                    "validation_errors": "accepted_reason is required",
                }
            ],
            rows=[],
        ),
    )

    check = gate_service._ranking_outlier_gate("pack", Path("sources"))

    assert check.status == "blocked"
    assert check.severity == "error"
    assert "acceptance rows are invalid" in check.detail
    assert "model_outlier_acceptances.csv" in check.next_action


def test_final_calibration_gate_blocks_failed_sanity_fixture(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_stats_first_calibration_report",
        lambda *_args, **_kwargs: SimpleNamespace(
            scenario_rows=[{"scenario_id": "brian_thomas_jr_over_luther_burden"}],
            sensitivity_rows=[],
            preview_rows=[],
            summary_rows=[],
        ),
    )
    monkeypatch.setattr(
        gate_service,
        "stats_first_calibration_readiness_rows",
        lambda _report: [
            {
                "area": "stats_first_scenarios",
                "status": "review",
                "value": "0/1",
                "meaning": "At least one stats-first fixture needs formula review.",
            }
        ],
    )

    check = gate_service._sanity_fixture_gate("preview_root")

    assert check.status == "blocked"
    assert check.severity == "error"
    assert "stats_first_scenarios" in check.detail
    assert "Fix failed sanity fixtures" in check.next_action


def test_sanity_fixture_gate_does_not_blame_blocked_preview_replay(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_stats_first_calibration_report",
        lambda *_args, **_kwargs: SimpleNamespace(
            scenario_rows=[
                {"scenario_id": "brian_thomas_jr_over_luther_burden", "passed": True}
            ],
            sensitivity_rows=[],
            preview_rows=[{"blocked_rows": 12}],
            summary_rows=[],
        ),
    )
    monkeypatch.setattr(
        gate_service,
        "stats_first_calibration_readiness_rows",
        lambda _report: [
            {
                "area": "stats_first_scenarios",
                "status": "ready",
                "value": "1/1",
                "meaning": "Stats-first fixtures behave as expected.",
            },
            {
                "area": "stats_first_sensitivity",
                "status": "ready",
                "value": 0,
                "meaning": "Tested input perturbations are not highly volatile.",
            },
            {
                "area": "preview_replay",
                "status": "review",
                "value": 12,
                "meaning": "Blocked preview rows must be fixed before apply.",
            },
        ],
    )

    check = gate_service._sanity_fixture_gate("preview_root")

    assert check.status == "ready"
    assert "Preview replay rows are handled as preview/apply review" in check.detail


def test_lifecycle_gate_blocks_missing_young_bridge_receipts(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_draft_room",
        lambda *_args, **_kwargs: SimpleNamespace(
            rookie_rows=[
                {
                    "asset_type": "rookie",
                    "asset_lifecycle": "incoming_rookie",
                    "source": "fact_rookie_draftables.csv",
                }
            ]
        ),
    )
    monkeypatch.setattr(
        gate_service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                {
                    "player": "Luther Burden",
                    "asset_lifecycle": "young_nfl_bridge",
                    "asset_lifecycle_label": "Young NFL Bridge",
                    "receipt_section_label": "NFL Production",
                    "formula_feature_name": "weighted_recent_lve_ppg_score",
                    "lifecycle_explanation": "",
                    "feature_weight": 20,
                    "contribution": 10,
                }
            ],
        ),
    )

    check = gate_service._lifecycle_model_separation_gate("pack", Path("sources"))

    assert check.status == "blocked"
    assert check.severity == "error"
    assert "young NFL bridge players lack bridge receipts" in check.detail
    assert "Keep rankings review-only" in check.next_action


def test_lifecycle_gate_blocks_established_veteran_draft_capital_prior(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_draft_room",
        lambda *_args, **_kwargs: SimpleNamespace(rookie_rows=[]),
    )
    monkeypatch.setattr(
        gate_service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                {
                    "player": "Established Star",
                    "asset_lifecycle": "established_veteran",
                    "asset_lifecycle_label": "Established Veteran",
                    "receipt_section_label": "Young-Player Bridge Prior",
                    "formula_feature_name": "draft_capital_prior_score",
                    "lifecycle_explanation": "",
                    "feature_weight": 5,
                    "contribution": 4,
                },
                {
                    "player": "Established Star",
                    "asset_lifecycle": "established_veteran",
                    "asset_lifecycle_label": "Established Veteran",
                    "receipt_section_label": "NFL Production",
                    "formula_feature_name": "weighted_recent_lve_ppg_score",
                    "lifecycle_explanation": "",
                    "feature_weight": 20,
                    "contribution": 12,
                },
            ],
        ),
    )

    check = gate_service._lifecycle_model_separation_gate("pack", Path("sources"))

    assert check.status == "blocked"
    assert "established veteran receipt rows still use draft-capital prior" in check.detail


def test_lifecycle_gate_passes_rookie_bridge_and_veteran_separation(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_draft_room",
        lambda *_args, **_kwargs: SimpleNamespace(
            rookie_rows=[
                {
                    "asset_type": "rookie",
                    "asset_lifecycle": "incoming_rookie",
                    "source": "fact_rookie_draftables.csv",
                }
            ]
        ),
    )
    monkeypatch.setattr(
        gate_service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                {
                    "player": "Luther Burden",
                    "asset_lifecycle": "young_nfl_bridge",
                    "asset_lifecycle_label": "Young NFL Bridge",
                    "receipt_section_label": "Young-Player Bridge Prior",
                    "formula_feature_name": "draft_capital_prior_score",
                    "lifecycle_explanation": BRIDGE_EXPLANATION,
                    "feature_weight": 0,
                    "contribution": 0,
                },
                {
                    "player": "Luther Burden",
                    "asset_lifecycle": "young_nfl_bridge",
                    "asset_lifecycle_label": "Young NFL Bridge",
                    "receipt_section_label": "Young-Player Bridge Prior",
                    "formula_feature_name": "young_nfl_bridge_decay_weight",
                    "lifecycle_explanation": BRIDGE_EXPLANATION,
                    "feature_weight": 0,
                    "contribution": 0,
                },
                {
                    "player": "Luther Burden",
                    "asset_lifecycle": "young_nfl_bridge",
                    "asset_lifecycle_label": "Young NFL Bridge",
                    "receipt_section_label": "Young-Player Bridge Prior",
                    "formula_feature_name": "young_nfl_bridge_nfl_evidence_weight",
                    "lifecycle_explanation": BRIDGE_EXPLANATION,
                    "feature_weight": 0,
                    "contribution": 0,
                },
                {
                    "player": "Luther Burden",
                    "asset_lifecycle": "young_nfl_bridge",
                    "asset_lifecycle_label": "Young NFL Bridge",
                    "receipt_section_label": "Young-Player Bridge Prior",
                    "formula_feature_name": "young_nfl_bridge_prior",
                    "lifecycle_explanation": BRIDGE_EXPLANATION,
                    "feature_weight": 15,
                    "contribution": 8,
                },
                {
                    "player": "Established Star",
                    "asset_lifecycle": "established_veteran",
                    "asset_lifecycle_label": "Established Veteran",
                    "receipt_section_label": "NFL Production",
                    "formula_feature_name": "weighted_recent_lve_ppg_score",
                    "lifecycle_explanation": "",
                    "feature_weight": 20,
                    "contribution": 12,
                },
            ],
        ),
    )

    check = gate_service._lifecycle_model_separation_gate("pack", Path("sources"))

    assert check.status == "ready"
    assert "young NFL bridge players show bridge receipts" in check.detail


def test_source_coverage_gate_blocks_age_bio_critical_gaps(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            player_rows=[{"coverage_status": "review_coverage"}],
            missing_critical_rows=[{"bucket": "age/bio"}],
            review_gap_rows=[],
            accepted_review_gap_rows=[],
        ),
    )

    check = gate_service._source_coverage_gate("pack", Path("sources"))

    assert check.status == "blocked"
    assert check.severity == "error"
    assert "critical source bucket gaps" in check.detail


def test_source_coverage_gate_blocks_missing_football_stat_gaps(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            player_rows=[],
            missing_critical_rows=[{"bucket": "production"}],
            review_gap_rows=[],
            accepted_review_gap_rows=[],
        ),
    )

    check = gate_service._source_coverage_gate("pack", Path("sources"))

    assert check.status == "blocked"
    assert check.severity == "error"
    assert "critical source bucket gaps" in check.detail


def test_source_coverage_gate_explains_nonblocking_gaps(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            player_rows=[{"coverage_status": "review_coverage"}],
            missing_critical_rows=[],
            review_gap_rows=[
                {
                    "bucket": "projections",
                    "decision_blocking_bucket": False,
                    "coverage_pct": 0,
                },
                {
                    "bucket": "injury",
                    "decision_blocking_bucket": False,
                    "coverage_pct": 50,
                },
            ],
            accepted_review_gap_rows=[],
            bucket_rows=[
                {
                    "bucket": "projections",
                    "decision_blocking_bucket": False,
                    "coverage_pct": 0,
                },
                {
                    "bucket": "injury",
                    "decision_blocking_bucket": False,
                    "coverage_pct": 50,
                },
                {
                    "bucket": "production",
                    "decision_blocking_bucket": True,
                    "coverage_pct": 100,
                },
            ],
        ),
    )

    check = gate_service._source_coverage_gate("pack", Path("sources"))

    assert check.status == "review"
    assert check.severity == "warning"
    assert "unaccepted review-only source gaps" in check.detail
    assert "injury: 1" in check.detail
    assert "projections: 1" in check.detail
    assert "audited acceptance" in check.next_action


def test_source_coverage_gate_passes_accepted_optional_gaps(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            player_rows=[
                {
                    "coverage_status": "ready_with_confidence_drag",
                    "critical_review_count": 0,
                }
            ],
            missing_critical_rows=[],
            review_gap_rows=[],
            accepted_review_gap_rows=[
                {
                    "bucket": "injury",
                    "decision_blocking_bucket": False,
                    "coverage_pct": 0,
                    "confidence_penalty": 6,
                }
            ],
            invalid_gap_acceptance_rows=[],
            bucket_rows=[
                {
                    "bucket": "injury",
                    "decision_blocking_bucket": False,
                    "coverage_pct": 0,
                    "gap_acceptance_status": "accepted",
                }
            ],
        ),
    )

    check = gate_service._source_coverage_gate("pack", Path("sources"))

    assert check.status == "ready"
    assert "1 optional gaps have audited acceptance rows" in check.detail
    assert "still retain confidence penalties" in check.detail


def test_source_coverage_gate_keeps_imputed_critical_visible_without_blocking(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            player_rows=[
                {
                    "coverage_status": "review_coverage",
                    "critical_review_count": 1,
                    "critical_review_inputs": "production",
                }
            ],
            missing_critical_rows=[],
            review_gap_rows=[],
            accepted_review_gap_rows=[
                {
                    "bucket": "projections",
                    "decision_blocking_bucket": False,
                    "confidence_penalty": 6,
                }
            ],
            invalid_gap_acceptance_rows=[],
        ),
    )

    check = gate_service._source_coverage_gate("pack", Path("sources"))

    assert check.status == "ready"
    assert "imputed-but-present critical coverage" in check.detail
    assert "keep confidence penalties" in check.detail


def test_source_coverage_gate_blocks_invalid_gap_acceptance_rows(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_source_coverage_audit",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            player_rows=[],
            missing_critical_rows=[],
            review_gap_rows=[],
            accepted_review_gap_rows=[],
            invalid_gap_acceptance_rows=[
                {"validation_errors": "confidence_penalty_retained must be true"}
            ],
        ),
    )

    check = gate_service._source_coverage_gate("pack", Path("sources"))

    assert check.status == "blocked"
    assert "source gap acceptance rows are invalid" in check.detail
    assert "confidence_penalty_retained=true" in check.next_action


def test_draft_ux_smoke_blocks_incomplete_pick_grid(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_service,
        "build_draft_ux_contract",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            page_rows=[
                {"route": "rankings"},
                {"route": "draft-board"},
            ],
            pick_grid_rows=[],
            best_option_rows=[],
            my_pick_rows=[],
        ),
    )

    check = gate_service._draft_ux_smoke_gate("pack")

    assert check.status == "blocked"
    assert "pick grid" in check.detail.lower()


def test_final_decision_badge_requires_every_gate_ready() -> None:
    ready_checks = (
        gate_service.CalibrationGateCheck("real_draft_pool_loaded", "ready", "info", "", ""),
        gate_service.CalibrationGateCheck("source_coverage_thresholds", "ready", "info", "", ""),
    )
    needs_data_checks = (
        gate_service.CalibrationGateCheck("real_draft_pool_loaded", "blocked", "error", "", ""),
    )
    review_checks = (
        gate_service.CalibrationGateCheck("ranking_outlier_review", "review", "warning", "", ""),
    )

    assert gate_service._decision_badge("ready", ready_checks) == "Review Only"
    assert gate_service._decision_badge("blocked", needs_data_checks) == "Needs Data"
    assert (
        gate_service._decision_badge("review", review_checks)
        == "Calibration Needs Review"
    )


def test_final_gate_rows_use_plain_english_blocker_messages() -> None:
    report = gate_service.FinalCalibrationGateReport(
        status="blocked",
        badge="Model Calibration Blocked",
        decision_badge="Needs Data",
        passed=False,
        blocked_count=1,
        review_count=1,
        ready_count=1,
        checks=(
            gate_service.CalibrationGateCheck(
                "source_coverage_thresholds",
                "blocked",
                "error",
                "fixture detail",
                "fixture action",
            ),
            gate_service.CalibrationGateCheck(
                "ranking_outlier_review",
                "review",
                "warning",
                "fixture detail",
                "fixture action",
            ),
            gate_service.CalibrationGateCheck(
                "draft_ux_smoke_pass",
                "ready",
                "info",
                "fixture detail",
                "fixture action",
            ),
        ),
    )

    rows = final_calibration_gate_rows(report)

    assert rows[0]["requirement"] == "Source Coverage Clear"
    assert rows[0]["blocker"] == "Blocked: Source Coverage Clear."
    assert "fake confidence" in rows[0]["why_it_matters"]
    assert rows[1]["blocker"] == "Needs review: Outlier Review Accepted/Resolved."
    assert rows[2]["blocker"] == "No blocker."
    assert final_calibration_gate_summary_row(report)["summary_badge"] == "Needs Data"


def test_final_calibration_gate_stays_review_only_during_model_v4_freeze(
    monkeypatch,
) -> None:
    ready_checks = {
        "_real_draft_pool_gate": "real_draft_pool_loaded",
        "_source_coverage_gate": "source_coverage_thresholds",
        "_identity_audit_gate": "identity_audit_pass",
        "_lifecycle_model_separation_gate": "lifecycle_model_separation",
        "_sanity_fixture_gate": "sanity_fixture_pass",
        "_ranking_outlier_gate": "ranking_outlier_review",
        "_rookie_replay_no_leakage_gate": "rookie_replay_no_leakage_pass",
        "_final_ui_smoke_gate": "final_ui_smoke_pass",
        "_draft_ux_smoke_gate": "draft_ux_smoke_pass",
    }
    for function_name, gate_name in ready_checks.items():
        monkeypatch.setattr(
            gate_service,
            function_name,
            lambda *_args, gate_name=gate_name, **_kwargs: gate_service.CalibrationGateCheck(
                gate=gate_name,
                status="ready",
                severity="info",
                detail="fixture ready",
                next_action="fixture ready",
            ),
        )

    report = build_final_calibration_gate("pack")
    summary = final_calibration_gate_summary_row(report)

    assert report.passed is False
    assert report.status == "review"
    assert report.decision_badge == "Review Only"
    assert summary["final_decision_badge"] == "Review Only"
    assert summary["decision_ready_gate"] == "hold"
    assert summary["pre_declaration_decision_badge"] == "Roster Decisions Need Review"
    assert summary["draft_decision_badge"] == "Draft Needs Review"
    assert any(check.gate == "model_v4_rebuild_freeze" for check in report.checks)


def test_pre_declaration_ready_can_pass_before_released_veterans_are_loaded(
    monkeypatch,
) -> None:
    ready_gates = {
        "_source_coverage_gate": "source_coverage_thresholds",
        "_identity_audit_gate": "identity_audit_pass",
        "_lifecycle_model_separation_gate": "lifecycle_model_separation",
        "_sanity_fixture_gate": "sanity_fixture_pass",
        "_ranking_outlier_gate": "ranking_outlier_review",
        "_rookie_replay_no_leakage_gate": "rookie_replay_no_leakage_pass",
        "_final_ui_smoke_gate": "final_ui_smoke_pass",
        "_draft_ux_smoke_gate": "draft_ux_smoke_pass",
    }
    for function_name, gate_name in ready_gates.items():
        monkeypatch.setattr(
            gate_service,
            function_name,
            lambda *_args, gate_name=gate_name, **_kwargs: gate_service.CalibrationGateCheck(
                gate=gate_name,
                status="ready",
                severity="info",
                detail="fixture ready",
                next_action="fixture ready",
            ),
        )
    monkeypatch.setattr(
        gate_service,
        "_real_draft_pool_gate",
        lambda *_args, **_kwargs: gate_service.CalibrationGateCheck(
            gate="real_draft_pool_loaded",
            status="review",
            severity="warning",
            detail="Official released veterans are not loaded yet.",
            next_action="Import released veterans later.",
        ),
    )

    report = build_final_calibration_gate("pack")
    summary = final_calibration_gate_summary_row(report)

    assert report.passed is False
    assert report.pre_declaration_passed is False
    assert report.draft_passed is False
    assert summary["pre_declaration_decision_badge"] == "Roster Decisions Need Review"
    assert summary["draft_decision_badge"] == "Needs Released Veterans"
    assert summary["final_decision_badge"] != "Decision Ready"
