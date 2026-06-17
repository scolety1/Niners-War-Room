from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_pick_order_validator_service import (
    pick_order_issues_as_dicts,
    simulator_ready_picks_as_dicts,
    validate_pick_order,
)

FIXTURE_DIR = Path("tests/fixtures/mock_draft/pick_order_validator")


def test_valid_fake_pick_order_is_green_and_simulator_ready() -> None:
    result = validate_pick_order(FIXTURE_DIR / "draft_order_valid_2026.csv")

    assert result.review_only is True
    assert result.full_simulation_ready is True
    assert result.summary["simulator_ready_pick_rows"] == 4
    assert result.excluded_placeholder_picks == ()
    assert result.issues == ()
    assert [pick.pick_label for pick in result.simulator_ready_picks] == [
        "1.01",
        "1.02",
        "1.03",
        "1.04",
    ]


def test_placeholder_picks_are_excluded_and_review_flagged() -> None:
    result = validate_pick_order(FIXTURE_DIR / "draft_order_review_flags.csv")

    assert "1.00" in result.excluded_placeholder_picks
    assert all(pick.pick_label != "1.00" for pick in result.simulator_ready_picks)
    issues = {issue.issue_type: issue for issue in result.issues}
    assert issues["future_placeholder_picks"].review_flag == (
        "future_placeholder_pick_review_required"
    )
    assert result.full_simulation_ready is False


def test_duplicate_invalid_and_missing_owner_pick_rows_are_flagged() -> None:
    result = validate_pick_order(FIXTURE_DIR / "draft_order_review_flags.csv")

    issues = {issue.issue_type: issue for issue in result.issues}
    assert issues["duplicate_pick_labels"].review_flag == (
        "duplicate_pick_review_required"
    )
    assert issues["invalid_pick_labels"].review_flag == "pick_label_review_required"
    assert issues["missing_owner"].review_flag == "pick_owner_review_required"
    assert issues["missing_manager"].review_flag == "pick_manager_review_required"
    assert issues["wrong_season"].review_flag == "draft_season_review_required"


def test_missing_required_columns_are_red(tmp_path) -> None:
    draft_file = tmp_path / "draft_order.csv"
    draft_file.write_text("pick_label\n1.01\n", encoding="utf-8")

    result = validate_pick_order(draft_file)

    assert any(
        issue.issue_type == "missing_draft_order_columns"
        and issue.status == "RED"
        for issue in result.issues
    )
    assert result.full_simulation_ready is False


def test_pick_order_serializers_are_report_ready() -> None:
    result = validate_pick_order(FIXTURE_DIR / "draft_order_valid_2026.csv")

    issue_rows = pick_order_issues_as_dicts(result)
    pick_rows = simulator_ready_picks_as_dicts(result)
    assert issue_rows == []
    assert pick_rows[0]["pick_label"] == "1.01"
    assert result.summary["market_policy"] == (
        "Pick order validation does not read or apply ADP/market."
    )
    assert result.summary["nwr_score_policy"] == (
        "Pick order validation does not invent numeric NWR scores."
    )
