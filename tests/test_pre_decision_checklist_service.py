from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import src.services.pre_decision_checklist_service as service
from src.services.final_calibration_gate_service import (
    CalibrationGateCheck,
    FinalCalibrationGateReport,
)
from src.services.pre_decision_checklist_service import (
    build_pre_decision_checklist,
    pre_decision_checklist_rows,
    pre_decision_checklist_summary_row,
)
from src.services.roster_decision_readiness_service import (
    RosterDecisionReadinessReport,
    RosterReadinessCheck,
)


def test_pre_decision_checklist_reports_all_ready(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        service,
        "build_final_calibration_gate",
        lambda *_args, **_kwargs: _final_report(status="ready"),
    )
    monkeypatch.setattr(
        service,
        "build_roster_decision_readiness",
        lambda *_args, **_kwargs: _roster_report(status="ready"),
    )
    _patch_my_team_receipts(monkeypatch, receipt_player_ids=["p1", "p2"])

    report = build_pre_decision_checklist("pack", veteran_model_dir=tmp_path)
    summary = pre_decision_checklist_summary_row(report)
    rows = pre_decision_checklist_rows(report)

    assert report.final_money_ready is True
    assert report.draft_ready is True
    assert report.roster_decisions_ready is True
    assert summary["Final Money Decisions Ready"] == "Decision Ready"
    assert {row["check"] for row in rows} == {
        "Roster data",
        "League ranks",
        "Lifecycle audit",
        "Source coverage",
        "Identity audit",
        "Young bridge receipts",
        "Named sanity fixtures",
        "Outlier review",
        "My team receipt review",
    }
    assert all(row["status"] == "ready" for row in rows)


def test_pre_decision_checklist_blocks_final_money_when_gate_blocks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        service,
        "build_final_calibration_gate",
        lambda *_args, **_kwargs: _final_report(
            status="blocked",
            blocked_gate="source_coverage_thresholds",
        ),
    )
    monkeypatch.setattr(
        service,
        "build_roster_decision_readiness",
        lambda *_args, **_kwargs: _roster_report(status="blocked"),
    )
    _patch_my_team_receipts(monkeypatch, receipt_player_ids=["p1", "p2"])

    report = build_pre_decision_checklist("pack", veteran_model_dir=tmp_path)
    rows = {
        row["check"]: row
        for row in pre_decision_checklist_rows(report)
    }

    assert report.final_money_ready is False
    assert report.final_money_badge == "Needs Data"
    assert rows["Source coverage"]["status"] == "blocked"
    assert rows["Source coverage"]["go_to"] == "Model Lab > Coverage"


def test_pre_decision_checklist_marks_missing_my_team_receipts_review(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        service,
        "build_final_calibration_gate",
        lambda *_args, **_kwargs: _final_report(status="ready"),
    )
    monkeypatch.setattr(
        service,
        "build_roster_decision_readiness",
        lambda *_args, **_kwargs: _roster_report(status="ready"),
    )
    _patch_my_team_receipts(monkeypatch, receipt_player_ids=["p1"])

    report = build_pre_decision_checklist("pack", veteran_model_dir=tmp_path)
    rows = {
        row["check"]: row
        for row in pre_decision_checklist_rows(report)
    }

    assert report.review_count == 1
    assert rows["My team receipt review"]["status"] == "review"
    assert "do not have visible receipt rows" in rows["My team receipt review"]["detail"]


def test_pre_decision_checklist_matches_my_team_receipts_by_name_when_ids_differ(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        service,
        "build_final_calibration_gate",
        lambda *_args, **_kwargs: _final_report(status="ready"),
    )
    monkeypatch.setattr(
        service,
        "build_roster_decision_readiness",
        lambda *_args, **_kwargs: _roster_report(status="ready"),
    )
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda *_args, **_kwargs: SimpleNamespace(
            has_errors=False,
            rows_by_table={
                "rosters": [
                    _roster_row("sleeper_btj", "Brian Thomas", "WR"),
                    _roster_row("sleeper_luther", "Luther Burden", "WR"),
                    _roster_row("sleeper_oronde", "Oronde Gadsden", "TE"),
                ]
            },
        ),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                _receipt_row("gsis_btj", "Brian Thomas Jr.", "WR"),
                _receipt_row("gsis_luther", "Luther Burden III", "WR"),
                _receipt_row("gsis_oronde", "Oronde Gadsden II", "TE"),
            ],
        ),
    )

    report = build_pre_decision_checklist("pack", veteran_model_dir=tmp_path)
    rows = {
        row["check"]: row
        for row in pre_decision_checklist_rows(report)
    }

    assert rows["My team receipt review"]["status"] == "ready"
    assert "3 selected-roster players have visible receipt rows" in (
        rows["My team receipt review"]["detail"]
    )


def _patch_my_team_receipts(monkeypatch, receipt_player_ids: list[str]) -> None:
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda *_args, **_kwargs: SimpleNamespace(
            has_errors=False,
            rows_by_table={
                "rosters": [
                    _roster_row("p1", "Player One", "WR"),
                    _roster_row("p2", "Player Two", "RB"),
                ]
            },
        ),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            issues=[],
            rows=[
                {
                    "player_id": player_id,
                    "player": f"Player {player_id}",
                    "position": "WR",
                    "formula_feature_name": "weighted_recent_lve_ppg_score",
                }
                for player_id in receipt_player_ids
            ],
        ),
    )


def _final_report(
    *,
    status: str,
    blocked_gate: str | None = None,
) -> FinalCalibrationGateReport:
    checks = tuple(
        CalibrationGateCheck(
            gate=gate,
            status="blocked" if gate == blocked_gate else "ready",
            severity="error" if gate == blocked_gate else "info",
            detail=f"{gate} detail",
            next_action=f"{gate} action",
        )
        for gate in (
            "source_coverage_thresholds",
            "identity_audit_pass",
            "lifecycle_model_separation",
            "sanity_fixture_pass",
            "ranking_outlier_review",
        )
    )
    blocked = sum(1 for check in checks if check.status == "blocked")
    ready = len(checks) - blocked
    return FinalCalibrationGateReport(
        status=status,
        badge="Model Calibration Passed" if status == "ready" else "Model Calibration Blocked",
        decision_badge="Decision Ready" if status == "ready" else "Needs Data",
        passed=status == "ready",
        blocked_count=blocked,
        review_count=0,
        ready_count=ready,
        checks=checks,
        pre_declaration_passed=status == "ready",
        pre_declaration_badge=(
            "Roster Decisions Ready" if status == "ready" else "Roster Decisions Need Data"
        ),
        draft_passed=status == "ready",
        draft_badge="Draft Ready" if status == "ready" else "Draft Needs Data",
    )


def _roster_report(*, status: str) -> RosterDecisionReadinessReport:
    checks = tuple(
        RosterReadinessCheck(
            gate=gate,
            requirement=requirement,
            status="ready" if status == "ready" else "blocked",
            severity="info" if status == "ready" else "error",
            detail=f"{requirement} detail",
            next_action=f"{requirement} action",
        )
        for gate, requirement in (
            ("current_rosters_loaded", "Current rosters loaded"),
            ("league_ranks_loaded", "League ranks loaded"),
            ("young_bridge_receipts_visible", "Young bridge receipts visible"),
        )
    )
    blocked = sum(1 for check in checks if check.status == "blocked")
    ready = len(checks) - blocked
    return RosterDecisionReadinessReport(
        status=status,
        badge="Roster Decisions Ready" if status == "ready" else "Roster Decisions Need Data",
        passed=status == "ready",
        blocked_count=blocked,
        review_count=0,
        ready_count=ready,
        checks=checks,
        my_team_id="niners",
        my_team_name="Niners",
    )


def _roster_row(player_id: str, player: str, position: str) -> dict[str, object]:
    return {
        "team_id": "niners",
        "team_name": "Niners",
        "player_id": player_id,
        "player_name": player,
        "position": position,
    }


def _receipt_row(player_id: str, player: str, position: str) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player": player,
        "position": position,
        "formula_feature_name": "weighted_recent_lve_ppg_score",
    }
