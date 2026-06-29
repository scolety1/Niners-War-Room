from __future__ import annotations

from scripts.build_rookie_historical_label_source_policy_v1_20260630 import (
    GATE_C_DECISION,
    NOT_ENOUGH,
    TARGET_SOURCE_GATE,
    build_bridge_rows,
    build_coverage_rows,
    censoring_status,
    horizon_hit,
    label_hit,
    validate_bridge_rows,
    validate_review_rows,
    window_complete,
)


def test_threshold_map_and_missing_finishes_are_not_probabilities() -> None:
    assert label_hit("QB", "6", 6) == "hit"
    assert label_hit("QB", "7", 6) == "miss"
    assert label_hit("RB", "24", 24) == "hit"
    assert label_hit("TE", "24", 24) == "not_applicable"
    assert label_hit("WR", "", 12) == NOT_ENOUGH
    assert label_hit("WR", "", 12) != "0%"


def test_horizon_hit_respects_complete_windows_and_missing_data() -> None:
    assert horizon_hit(["miss", "hit", "miss"], window_complete=True) == "hit"
    assert horizon_hit(["miss", "miss"], window_complete=True) == "miss"
    assert horizon_hit(["miss", NOT_ENOUGH], window_complete=True) == NOT_ENOUGH
    assert horizon_hit(["hit"], window_complete=False) == NOT_ENOUGH
    assert horizon_hit(["not_applicable"], window_complete=True) == "not_applicable"


def test_censoring_rules_for_three_and_five_year_windows() -> None:
    assert window_complete(2020, 5, latest_label_season=2024) is True
    assert window_complete(2021, 5, latest_label_season=2024) is False
    assert censoring_status(2020, 5, latest_label_season=2024) == "complete"
    assert censoring_status(2021, 5, latest_label_season=2024) == "right_censored"


def test_bridge_rows_remain_review_only_and_do_not_link_current_2026_rows() -> None:
    rows = build_bridge_rows(
        approved_rows=_approval_rows(),
        draft_by_player_id=_draft_rows_with_partial_current_context(),
        outcome_player_ids={"00-0039999"},
    )

    validate_bridge_rows(rows)
    assert len(rows) == 157
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["approved_by_human"] for row in rows} == {"true"}
    assert {
        row["nfl_outcome_label_link_status"]
        for row in rows
    } == {
        "not_linked_current_2026_outside_2012_2024_outcome_window",
        "not_linked_missing_draft_class_and_nfl_id",
    }


def test_bridge_validation_rejects_model_or_training_promotion() -> None:
    rows = build_bridge_rows(
        approved_rows=_approval_rows(),
        draft_by_player_id=_draft_rows_with_partial_current_context(),
        outcome_player_ids=set(),
    )
    rows[0]["model_use_allowed"] = "true"

    try:
        validate_bridge_rows(rows)
    except ValueError as exc:
        assert "model_use_allowed=false" in str(exc)
    else:
        raise AssertionError("Expected validation to reject model-use promotion")


def test_coverage_rows_report_blocked_gate_c_and_keep_flags_closed() -> None:
    bridge_rows = build_bridge_rows(
        approved_rows=_approval_rows(),
        draft_by_player_id=_draft_rows_with_partial_current_context(),
        outcome_player_ids=set(),
    )
    coverage = build_coverage_rows(
        bridge_rows=bridge_rows,
        outcome_status={
            "anchor_rows_count": 7440,
            "season_rows_count": 7440,
            "complete_5y_rows": 1064,
            "positions": {},
            "scoring_mode": "exact_verified_first_downs",
        },
    )

    validate_review_rows(coverage)
    metric_values = {row["metric"]: row["value"] for row in coverage}
    assert metric_values["bridge_rows_linked_to_outcome_labels"] == "0"
    assert metric_values["historical_rookie_label_rows_built"] == "0"
    assert metric_values["gate_c_decision"] == GATE_C_DECISION
    assert TARGET_SOURCE_GATE == "GREEN_REVIEW_ONLY_NFL_OUTCOME_TARGET_SOURCE"


def test_lane_code_does_not_reference_protected_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("rookie_historical_label_source_policy" not in path for path in protected_paths)


def _approval_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(157):
        rows.append(
            {
                "player_id": str(13000 + index),
                "player_name": f"Player {index}",
                "position": "WR" if index % 2 else "RB",
                "college_team": "Example",
                "cfbd_candidate_id": str(4700000 + index),
                "gate_a_status": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
                "ambiguity_flags": "none",
            }
        )
    return rows


def _draft_rows_with_partial_current_context() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for index in range(54):
        player_id = str(13000 + index)
        rows[player_id] = {
            "player_id": player_id,
            "draft_year": "2026",
            "rookie_class_year": "2026",
            "data_quality_status": "PARTIAL_REVIEW_ONLY_DRAFT_CAPITAL_AVAILABLE",
        }
    return rows
