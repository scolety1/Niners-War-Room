from __future__ import annotations

import pandas as pd
import pytest

from app.components.decision_trust_strip import _summary_part
from src.services import draft_day_app_v1_service
from src.services.decision_trust_strip_service import (
    GATED,
    IDENTITY_EXCEPTION,
    MISSING,
    NOT_ENOUGH_INFORMATION,
    SOURCE_EXCEPTION,
    STALE,
    UNAVAILABLE,
    VALID_CURRENT,
    build_decision_trust_strip,
    state_from_existing_status,
)


@pytest.mark.parametrize(
    ("value", "field", "expected"),
    (
        ("not current", "as_of_freshness", NOT_ENOUGH_INFORMATION),
        ("not valid", "evidence_source", NOT_ENOUGH_INFORMATION),
        ("not ready", "evidence_source", NOT_ENOUGH_INFORMATION),
        ("not scored", "missingness_completeness", NOT_ENOUGH_INFORMATION),
        ("unmatched", "identity_join", IDENTITY_EXCEPTION),
        ("not available", "evidence_source", UNAVAILABLE),
        ("not currently available", "evidence_source", UNAVAILABLE),
        ("NOT CURRENT", "as_of_freshness", NOT_ENOUGH_INFORMATION),
        ("not-current", "as_of_freshness", NOT_ENOUGH_INFORMATION),
        ("not_current", "as_of_freshness", NOT_ENOUGH_INFORMATION),
        ("available but not reviewed", "evidence_source", NOT_ENOUGH_INFORMATION),
        ({"current": False}, "evidence_source", NOT_ENOUGH_INFORMATION),
        ("current but failed", "as_of_freshness", NOT_ENOUGH_INFORMATION),
    ),
)
def test_negated_statuses_never_become_valid_current(
    value: object,
    field: str,
    expected: str,
) -> None:
    state = state_from_existing_status(value, field=field)

    assert state == expected
    assert state != VALID_CURRENT


@pytest.mark.parametrize(
    ("value", "field"),
    (
        ("Available", "evidence_source"),
        ("Available: synthetic-source.csv", "evidence_source"),
        ("GREEN_CURRENT", "as_of_freshness"),
        ("Matched", "identity_join"),
        ("Exact", "identity_join"),
        ("Ready", "evidence_source"),
        ("Scored", "missingness_completeness"),
        ("full dynasty source", "evidence_source"),
        ("admitted identifier present", "identity_join"),
    ),
)
def test_canonical_positive_statuses_remain_valid_current(value: str, field: str) -> None:
    assert state_from_existing_status(value, field=field) == VALID_CURRENT


@pytest.mark.parametrize(
    ("value", "field", "expected"),
    (
        ("YELLOW_STALE", "as_of_freshness", STALE),
        ("missing receipt", "evidence_source", MISSING),
        ("gated / not admitted", "evidence_source", GATED),
        ("source unavailable", "evidence_source", UNAVAILABLE),
        ("review-only source restriction", "evidence_source", SOURCE_EXCEPTION),
    ),
)
def test_canonical_nonpositive_states_remain_mechanically_distinct(
    value: str,
    field: str,
    expected: str,
) -> None:
    assert state_from_existing_status(value, field=field) == expected


def test_frozen_board_negations_fail_closed_through_collapsed_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = []
    for rank in range(1, draft_day_app_v1_service.EXPECTED_ROW_COUNT + 1):
        rows.append(
            {
                "final_board_rank": rank,
                "final_tier": "Synthetic tier",
                "position_rank": rank,
                "model_posture_used": "Synthetic review-only posture",
                "candidate_status": "Synthetic candidate",
                "risk_notes": "Synthetic fixture only",
                "needs_manual_review": True,
                "player": f"Synthetic Player {rank}",
            }
        )
    rows[0].update(
        {
            "source_status": "not ready",
            "freshness_status": "not current",
            "identity_join_status": "unmatched",
            "missing_evidence": "not scored",
            "warnings": "not valid",
        }
    )
    rows[1].update(
        {
            "source_status": {"current": False},
            "freshness_status": "current but failed",
        }
    )
    frame = pd.DataFrame(rows)
    assert draft_day_app_v1_service.validate_frozen_board(frame) == ()
    monkeypatch.setattr(
        draft_day_app_v1_service,
        "enrich_display_age_from_roster_context",
        lambda normalized, *, name_column: normalized,
    )
    normalized = draft_day_app_v1_service.normalize_board_frame(frame)
    selected = normalized.iloc[0].to_dict()

    strip = build_decision_trust_strip(
        selected,
        surface="Synthetic Player Compare fixture",
        entity_label="Synthetic Player 1",
        receipt_label="Synthetic disclosure",
        receipt_available=False,
    )

    assert tuple(field.state for field in strip.fields[:-1]) == (
        NOT_ENOUGH_INFORMATION,
        NOT_ENOUGH_INFORMATION,
        IDENTITY_EXCEPTION,
        NOT_ENOUGH_INFORMATION,
        NOT_ENOUGH_INFORMATION,
    )
    for field in strip.fields[:-1]:
        assert field.value in _summary_part(field)

    contradictory = build_decision_trust_strip(
        normalized.iloc[1].to_dict(),
        surface="Synthetic Player Compare fixture",
        entity_label="Synthetic Player 2",
        receipt_label="Synthetic disclosure",
        receipt_available=False,
    )

    assert contradictory.field("evidence_source").state == NOT_ENOUGH_INFORMATION
    assert contradictory.field("as_of_freshness").state == NOT_ENOUGH_INFORMATION
    for key in ("evidence_source", "as_of_freshness"):
        field = contradictory.field(key)
        assert field.value in _summary_part(field)
