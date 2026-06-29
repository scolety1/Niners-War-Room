from __future__ import annotations

import pandas as pd

from src.services.injury_context_source_gate_service import (
    APPROVE_REVIEW_ONLY,
    BLOCKED_FIELD_COVERAGE,
    BLOCKED_IDENTITY_JOIN,
    BLOCKED_NO_LOADER,
    BLOCKED_SOURCE_POLICY,
    audit_injury_context_source,
)


def test_missing_loader_blocks_when_no_local_data() -> None:
    decision, audit_rows, manifest_rows = audit_injury_context_source(
        None,
        loader_available=False,
        loader_notes="missing",
    )

    assert decision == BLOCKED_NO_LOADER
    assert audit_rows[0]["loader_available"] == "false"
    assert manifest_rows[0]["model_use_allowed"] == "false"


def test_source_policy_blocks_even_with_rows() -> None:
    decision, _audit_rows, manifest_rows = audit_injury_context_source(
        _valid_injury_rows(),
        loader_available=True,
        loader_notes="available",
        source_policy_status="blocked_vendor_medical_source",
    )

    assert decision == BLOCKED_SOURCE_POLICY
    assert manifest_rows[0]["source_policy_status"] == "blocked_vendor_medical_source"
    assert manifest_rows[0]["medical_inference_allowed"] == "false"


def test_missing_identity_blocks_approval() -> None:
    frame = _valid_injury_rows().drop(columns=["gsis_id"])
    decision, audit_rows, _manifest_rows = audit_injury_context_source(
        frame,
        loader_available=True,
        loader_notes="available",
    )

    assert decision == BLOCKED_IDENTITY_JOIN
    assert audit_rows[0]["identity_fields_present"] == ""


def test_medical_score_fields_are_rejected() -> None:
    frame = _valid_injury_rows()
    frame["injury_risk_score"] = 0.7
    decision, audit_rows, _manifest_rows = audit_injury_context_source(
        frame,
        loader_available=True,
        loader_notes="available",
    )

    assert decision == BLOCKED_FIELD_COVERAGE
    assert audit_rows[0]["medical_score_fields_present"] == "injury_risk_score"


def test_nflverse_injury_context_approves_review_only_not_model_use() -> None:
    decision, audit_rows, manifest_rows = audit_injury_context_source(
        _valid_injury_rows(),
        loader_available=True,
        loader_notes="nflreadpy 0.1.5 load_injuries available",
    )

    assert decision == APPROVE_REVIEW_ONLY
    assert audit_rows[0]["gsis_coverage_rate"] == 1.0
    assert audit_rows[0]["display_only"] == "true"
    assert audit_rows[0]["review_only"] == "true"
    assert audit_rows[0]["medical_inference_allowed"] == "false"
    assert manifest_rows[0]["source_truth_allowed"] == "false"
    assert manifest_rows[0]["app_wiring_allowed"] == "false"


def _valid_injury_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "season": 2024,
                "game_type": "REG",
                "team": "SF",
                "week": 1,
                "gsis_id": "00-0030001",
                "position": "RB",
                "full_name": "Example Back",
                "report_primary_injury": "hamstring",
                "report_secondary_injury": "",
                "report_status": "Questionable",
                "practice_primary_injury": "hamstring",
                "practice_secondary_injury": "",
                "practice_status": "Limited",
                "date_modified": "2024-09-01",
            }
        ]
    )
