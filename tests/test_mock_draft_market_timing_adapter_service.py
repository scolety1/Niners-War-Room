from __future__ import annotations

import json

from src.services.mock_draft_market_timing_adapter_service import (
    DEFAULT_FAKE_MARKET_TIMING_FIXTURE,
    behavior_only_market_context_rows,
    build_and_write_fake_market_timing_dry_run,
    build_fake_market_timing_dry_run,
    read_fake_market_timing_rows,
    validate_fake_market_timing_rows,
)


def test_fake_fixture_rows_validate_as_behavior_only_without_real_market_data() -> None:
    rows = read_fake_market_timing_rows()

    validation = validate_fake_market_timing_rows(rows)

    assert len(rows) == 3
    assert {row["source_name"] for row in validation} == {"fake_contract_fixture"}
    assert {row["source_type"] for row in validation} == {"synthetic_market_timing"}
    assert sum(1 for row in validation if row["allowed_for_behavior"]) == 2
    assert any("market_score_fields_ignored" in row["review_flags"] for row in validation)
    assert any(
        "market_timing_missing_pick_value_review_required" in row["review_flags"]
        for row in validation
    )


def test_invalid_market_columns_are_flagged_and_excluded_from_behavior_context() -> None:
    rows = [
        {
            "asset_id": "rookie:alpha_wr",
            "player": "Alpha WR",
            "source_name": "real_vendor",
            "source_type": "real_adp",
            "market_adp": "1.0",
            "private_value": "99",
            "nwr_quality_score": "99",
        }
    ]

    validation = validate_fake_market_timing_rows(rows)
    behavior_rows = behavior_only_market_context_rows(rows)

    assert validation[0]["allowed_for_behavior"] is False
    assert "private_value" in validation[0]["disallowed_columns_flagged"]
    assert "nwr_quality_score" in validation[0]["blocked_score_fields_ignored"]
    assert "non_fake_market_source_rejected" in validation[0]["review_flags"]
    assert behavior_rows == ()


def test_dry_run_changes_behavior_but_preserves_guidance_value_flags_and_scores() -> None:
    dry_run = build_fake_market_timing_dry_run()

    checks = {row["check_name"]: row for row in dry_run.contamination_checks}
    assert dry_run.fixture_path == DEFAULT_FAKE_MARKET_TIMING_FIXTURE
    assert dry_run.fixture_row_count == 3
    assert dry_run.manifest["fixture_policy"] == "fake_fixture_only_no_real_market_data_imported"
    assert dry_run.manifest["behavior_only_rows"] == 2
    assert dry_run.manifest["contamination_checks_passed"] == len(
        dry_run.contamination_checks
    )
    assert checks["opponent_behavior_changed"]["passed"] is True
    assert checks["rookie_guidance_unchanged"]["passed"] is True
    assert checks["no_numeric_nwr_score_created"]["passed"] is True
    assert checks["value_neutral_flags_preserved"]["passed"] is True
    assert checks["market_behavior_only"]["passed"] is True
    assert checks["no_real_market_data_required"]["passed"] is True
    assert any(row["availability_changed"] for row in dry_run.behavior_notes)


def test_write_fake_market_timing_dry_run_artifacts_are_local_only(tmp_path) -> None:
    dry_run = build_and_write_fake_market_timing_dry_run(
        output_root=tmp_path / "fake_market_timing_dry_run_20260616"
    )

    assert dry_run.artifact_paths["validation_rows"].exists()
    assert dry_run.artifact_paths["behavior_notes"].exists()
    assert dry_run.artifact_paths["contamination_check"].exists()
    assert dry_run.artifact_paths["manifest"].exists()
    manifest = json.loads(dry_run.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert manifest["fixture_rows"] == 3
    assert manifest["behavior_only_rows"] == 2
    assert manifest["promotion_status"] == (
        "local_dry_run_output_only_not_app_wired_not_promoted"
    )
