"""Synthetic display-only fixture for trust-strip state rendering."""

from app.components.decision_trust_strip import render_decision_trust_strips
from src.services.decision_trust_strip_service import build_decision_trust_strip

FIXTURES = (
    (
        "Valid / current",
        {
            "source_status": "Available",
            "freshness_status": "GREEN_CURRENT",
            "player_id": "fixture-valid",
            "missing_evidence": "Complete",
        },
        True,
    ),
    (
        "Stale",
        {
            "source_status": "Available",
            "freshness_status": "YELLOW_STALE",
            "player_id": "fixture-stale",
        },
        True,
    ),
    (
        "Missing",
        {
            "source_status": "missing receipt",
            "player_id": "fixture-missing",
            "missing_evidence": "Missing evidence: 1",
        },
        False,
    ),
    ("Gated", {"source_status": "gated / not admitted", "player_id": "fixture-gated"}, False),
    (
        "Unavailable",
        {"source_status": "source unavailable", "player_id": "fixture-unavailable"},
        False,
    ),
    (
        "Identity exception",
        {"source_status": "Available", "identity_join_status": "identity review required"},
        True,
    ),
    (
        "Source exception",
        {
            "source_status": "review-only source restriction",
            "player_id": "fixture-source",
            "warnings": "source caveat",
        },
        True,
    ),
)

render_decision_trust_strips(
    [
        build_decision_trust_strip(
            row,
            surface="Synthetic review fixture",
            entity_label=label,
            receipt_label="Synthetic existing-receipt path",
            receipt_available=receipt_available,
        )
        for label, row, receipt_available in FIXTURES
    ],
    heading="Synthetic trust-strip render review",
)
