from __future__ import annotations

from src.services.nfl_usage_schema_fingerprint_service import (
    fingerprint_registry_row,
    fingerprint_rows,
    schema_changed,
)
from src.services.nfl_usage_validation_service import validate_usage_rows


def test_schema_fingerprint_is_stable_and_detects_change() -> None:
    rows = [{"season": "2025", "week": "1", "player_id": "p1", "targets": "4"}]
    first = fingerprint_rows("player_stats", rows, required_fields={"season", "week"})
    second = fingerprint_rows("player_stats", rows, required_fields={"season", "week"})
    changed = fingerprint_rows(
        "player_stats",
        [dict(rows[0], receptions="3")],
        required_fields={"season", "week"},
    )

    assert first["schema_fingerprint"] == second["schema_fingerprint"]
    assert schema_changed(first, changed)
    assert fingerprint_registry_row(first)["model_input_allowed"] == "no"


def test_validation_quarantines_blocked_missing_duplicate_and_permission_issues() -> None:
    rows = [
        {
            "source_family": "player_stats",
            "season": "2025",
            "week": "1",
            "player_id": "p1",
            "targets": "8",
            "market_value": "99",
            "model_input_allowed": "yes",
            "app_wiring_allowed": "no",
        },
        {
            "source_family": "player_stats",
            "season": "2025",
            "week": "1",
            "player_id": "p1",
            "targets": "8",
            "market_value": "99",
            "model_input_allowed": "no",
            "app_wiring_allowed": "no",
        },
    ]

    result = validate_usage_rows(
        "player_stats",
        rows,
        required_fields={"season", "week", "player_id", "receptions"},
        allowed_fields={
            "source_family",
            "season",
            "week",
            "player_id",
            "targets",
            "model_input_allowed",
            "app_wiring_allowed",
        },
    )
    reasons = "|".join(row["reason"] for row in result.quarantine_rows)

    assert result.status == "RED"
    assert "missing_required_fields:receptions" in reasons
    assert "blocked_fields_present:market_value" in reasons
    assert "duplicate_player_week_source_rows" in reasons
    assert "model_permission_violation" in reasons


def test_validation_quarantines_stale_metadata_and_missing_attribution() -> None:
    result = validate_usage_rows(
        "participation",
        [
            {
                "source_family": "participation",
                "season": "2025",
                "week": "1",
                "player_id": "p1",
                "participation_proxy": "1",
                "model_input_allowed": "no",
                "app_wiring_allowed": "no",
            }
        ],
        required_fields={"season", "week", "player_id"},
        allowed_fields={
            "source_family",
            "season",
            "week",
            "player_id",
            "participation_proxy",
            "model_input_allowed",
            "app_wiring_allowed",
        },
        metadata={
            "source_family": "participation",
            "source_updated_at": "2000-01-01T00:00:00+00:00",
            "max_age_days": 30,
        },
    )
    reasons = "|".join(row["reason"] for row in result.quarantine_rows)

    assert "stale_source_metadata" in reasons
    assert "license_attribution_missing" in reasons


def test_validation_blocks_route_truth_overclaim() -> None:
    result = validate_usage_rows(
        "participation",
        [
            {
                "source_family": "participation",
                "season": "2025",
                "week": "1",
                "player_id": "p1",
                "field_name": "true TPRR",
                "notes": "true routes run",
                "model_input_allowed": "no",
                "app_wiring_allowed": "no",
            }
        ],
        required_fields={"season", "week", "player_id"},
        allowed_fields={
            "source_family",
            "season",
            "week",
            "player_id",
            "field_name",
            "notes",
            "model_input_allowed",
            "app_wiring_allowed",
        },
    )

    assert any(
        row["reason"] == "unsupported_route_truth_claim"
        for row in result.quarantine_rows
    )
