from __future__ import annotations

from src.services.legacy_label_quarantine_service import (
    legacy_label_is_trusted_decision,
    quarantine_legacy_label,
)


def test_legacy_action_labels_are_review_only_during_v4_freeze() -> None:
    assert quarantine_legacy_label("Core Holds", active=True) == (
        "Review-only legacy core holds"
    )
    assert quarantine_legacy_label("bubble", active=True) == "Review-only legacy bubble"
    assert quarantine_legacy_label("Shop", active=True) == "Review-only legacy shop"
    assert quarantine_legacy_label("Release", active=True) == "Review-only legacy release"


def test_ready_labels_are_quarantined_during_v4_freeze() -> None:
    assert quarantine_legacy_label("Decision Ready", active=True) == "Review Only"
    assert quarantine_legacy_label("Roster Decisions Ready", active=True) == (
        "Roster Decisions Review Only"
    )
    assert quarantine_legacy_label("Draft Ready", active=True) == "Draft Review Only"


def test_quarantined_labels_are_not_trusted_decisions_during_v4_freeze() -> None:
    for label in (
        "Core Hold",
        "Bubble",
        "Shop",
        "Release",
        "Decision Ready",
        "Roster Decisions Ready",
        "Draft Ready",
    ):
        assert legacy_label_is_trusted_decision(label, active=True) is False


def test_legacy_labels_return_unchanged_when_freeze_is_inactive() -> None:
    assert quarantine_legacy_label("Shop", active=False) == "Shop"
    assert quarantine_legacy_label("Roster Decisions Ready", active=False) == (
        "Roster Decisions Ready"
    )
    assert legacy_label_is_trusted_decision("Shop", active=False) is True
