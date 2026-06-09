from __future__ import annotations

from src.services.model_v4_evidence_gate_service import model_v4_evidence_gate


def test_team_status_warning_forces_manual_decision() -> None:
    gate = model_v4_evidence_gate(
        {"warning_flags": "team_mismatch_or_missing_model_team"}
    )

    assert gate.stale_team_or_status is True
    assert gate.manual_decision_required is True
    assert "stale_team_or_status_evidence" in gate.warning_flags


def test_explicit_team_mismatch_forces_manual_decision() -> None:
    gate = model_v4_evidence_gate({"nfl_team": "LAC", "authoritative_team": "CHI"})

    assert gate.stale_team_or_status is True
    assert gate.manual_decision_required is True


def test_unknown_roster_status_forces_manual_decision() -> None:
    gate = model_v4_evidence_gate({"roster_status": "UNKNOWN"})

    assert gate.stale_team_or_status is True
    assert gate.manual_decision_required is True


def test_missing_role_warning_forces_manual_decision() -> None:
    gate = model_v4_evidence_gate(
        {"warning_flags": "missing_or_review_route_target_snap_evidence"}
    )

    assert gate.missing_role_evidence is True
    assert gate.manual_decision_required is True
    assert "missing_role_evidence_gate" in gate.warning_flags


def test_licensed_route_unavailable_requires_alternate_role_evidence() -> None:
    missing_gate = model_v4_evidence_gate(
        {"warning_flags": "licensed_route_metrics_not_available"}
    )
    admitted_gate = model_v4_evidence_gate(
        {
            "warning_flags": "licensed_route_metrics_not_available",
            "snap_evidence_status": "ADMITTED",
        }
    )

    assert missing_gate.missing_role_evidence is True
    assert missing_gate.manual_decision_required is True
    assert admitted_gate.missing_role_evidence is False
    assert admitted_gate.manual_decision_required is False


def test_clean_evidence_passes_without_manual_decision() -> None:
    gate = model_v4_evidence_gate(
        {
            "nfl_team": "LAC",
            "authoritative_team": "LAC",
            "roster_status": "ACTIVE",
            "snap_evidence_status": "ADMITTED",
        }
    )

    assert gate.stale_team_or_status is False
    assert gate.missing_role_evidence is False
    assert gate.partial_or_quarantined_contribution is False
    assert gate.manual_decision_required is False
    assert gate.warning_flags == ()


def test_partial_contribution_warning_forces_manual_decision() -> None:
    gate = model_v4_evidence_gate({"warning_flags": "partial_first_down_confidence_cap"})

    assert gate.partial_or_quarantined_contribution is True
    assert gate.manual_decision_required is True
    assert "partial_or_quarantined_join_evidence" in gate.warning_flags


def test_quarantined_join_status_forces_manual_decision() -> None:
    gate = model_v4_evidence_gate({"source_join_status": "QUARANTINED"})

    assert gate.partial_or_quarantined_contribution is True
    assert gate.manual_decision_required is True


def test_partial_or_quarantined_gate_does_not_hide_other_warning_flags() -> None:
    gate = model_v4_evidence_gate(
        {
            "warning_flags": (
                "team_mismatch_or_missing_model_team|"
                "missing_or_review_route_target_snap_evidence|"
                "source_limited_evidence_cap"
            )
        }
    )

    assert gate.stale_team_or_status is True
    assert gate.missing_role_evidence is True
    assert gate.partial_or_quarantined_contribution is True
    assert gate.warning_flags == (
        "stale_team_or_status_evidence",
        "missing_role_evidence_gate",
        "partial_or_quarantined_join_evidence",
    )
