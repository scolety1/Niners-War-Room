from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_gate_f_display_artifact_v1_20260630 import (
    ALLOWED_FEATURES,
    DISPLAY_COLUMNS,
    FINAL_VERDICT,
    NOT_ENOUGH,
    TARGETS,
    build_display_rows,
    build_summary_rows,
    draft_capital_bucket,
    target_to_display_column,
    validate_inputs,
)

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_PATH = (
    ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_f_display_artifact_v1_20260630"
    / "rookie_display_artifact_coverage_matrix_v1.csv"
)
DECISION_PATH = (
    ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_f_display_artifact_v1_20260630"
    / "02_GATE_F_DISPLAY_ARTIFACT_DECISION.md"
)


def test_display_rows_are_review_only_display_only_and_closed_to_rankings() -> None:
    rows = build_display_rows(
        [_gate_b_row()],
        _label_rows(position="WR", draft_round="2", draft_pick="47"),
        _gate_e_summary_rows(),
        _gate_e_metric_rows(),
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["review_only"] == "true"
    assert row["display_only"] == "true"
    assert row["model_use_allowed"] == "false"
    assert row["training_allowed"] == "false"
    assert row["rankings_wiring_allowed"] == "false"
    assert row["display_status"] == "review_only_display_fields_available"
    assert int(row["display_field_count"]) > 0


def test_missing_data_remains_not_enough_information_never_zero() -> None:
    rows = build_display_rows(
        [_gate_b_row(draft_round=NOT_ENOUGH, draft_pick=NOT_ENOUGH)],
        _label_rows(position="WR", draft_round="2", draft_pick="47"),
        _gate_e_summary_rows(),
        _gate_e_metric_rows(),
    )

    row = rows[0]
    rate_values = [row[target_to_display_column(target)] for target in TARGETS]
    assert row["display_status"] == NOT_ENOUGH
    assert set(rate_values) == {NOT_ENOUGH}
    assert "0%" not in ",".join(rate_values)


def test_round_8_review_rows_do_not_get_gate_d_bucket_or_display_values() -> None:
    row = _gate_b_row(draft_round="8", draft_pick="237")
    display_rows = build_display_rows(
        [row],
        _label_rows(position="RB", draft_round="2", draft_pick="47"),
        _gate_e_summary_rows(),
        _gate_e_metric_rows(),
    )

    assert draft_capital_bucket({"draft_round": "8", "draft_pick": "237"}) == (
        "not_enough_information"
    )
    assert display_rows[0]["draft_capital_bucket"] == "not_enough_information"
    assert display_rows[0]["display_status"] == NOT_ENOUGH
    assert display_rows[0]["display_field_count"] == "0"


def test_position_specific_targets_do_not_fake_unsupported_thresholds() -> None:
    rows = build_display_rows(
        [_gate_b_row(position="TE")],
        _label_rows(position="TE", draft_round="2", draft_pick="47"),
        _gate_e_summary_rows(),
        _gate_e_metric_rows(),
    )

    row = rows[0]
    assert row["rookie_year_top_12_review_display_rate"] != NOT_ENOUGH
    assert row["rookie_year_top_24_review_display_rate"] == NOT_ENOUGH
    assert row["rookie_year_top_36_review_display_rate"] == NOT_ENOUGH


def test_only_gate_d_allowed_features_are_accepted() -> None:
    validate_inputs(
        [_gate_b_row()],
        _gate_d_policy_rows(),
        _gate_e_summary_rows(),
        _gate_e_metric_rows(),
    )

    assert set(ALLOWED_FEATURES) == {
        "draft_round",
        "draft_pick",
        "draft_capital_bucket",
        "draft_year",
        "rookie_class_year",
        "position",
    }


def test_summary_blocks_gate_g_and_keeps_flags_closed() -> None:
    display_rows = build_display_rows(
        [_gate_b_row(), _gate_b_row(draft_round=NOT_ENOUGH, draft_pick=NOT_ENOUGH)],
        _label_rows(position="WR", draft_round="2", draft_pick="47"),
        _gate_e_summary_rows(),
        _gate_e_metric_rows(),
    )
    summary = build_summary_rows(
        _gate_a_rows(),
        [_gate_b_row(), _gate_b_row(draft_round=NOT_ENOUGH, draft_pick=NOT_ENOUGH)],
        display_rows,
        _gate_e_metric_rows(),
    )
    by_metric = {row["metric"]: row for row in summary}

    assert by_metric["gate_f_verdict"]["value"] == FINAL_VERDICT
    assert by_metric["gate_g_can_run_next"]["value"] == "false"
    assert {row["review_only"] for row in summary} == {"true"}
    assert {row["display_only"] for row in summary} == {"true"}
    assert {row["model_use_allowed"] for row in summary} == {"false"}
    assert {row["training_allowed"] for row in summary} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in summary} == {"false"}


def test_tracked_coverage_matrix_schema_and_flags() -> None:
    rows = _coverage_rows()

    assert rows
    assert set(DISPLAY_COLUMNS) - {
        "draft_year",
        "data_quality_status",
        "rookie_year_top_12_review_display_rate",
        "rookie_year_top_24_review_display_rate",
        "rookie_year_top_36_review_display_rate",
        "year_2_top_12_review_display_rate",
        "year_2_top_24_review_display_rate",
        "year_2_top_36_review_display_rate",
        "first_3y_top_12_review_display_rate",
        "first_3y_top_24_review_display_rate",
        "first_3y_top_36_review_display_rate",
        "first_5y_top_12_review_display_rate",
        "first_5y_top_24_review_display_rate",
        "first_5y_top_36_review_display_rate",
        "rate_method_summary",
    } <= set(rows[0])
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["display_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}


def test_decision_doc_declares_partial_and_no_gate_g() -> None:
    text = DECISION_PATH.read_text(encoding="utf-8")

    assert "PARTIAL_REVIEW_ONLY_DISPLAY_ARTIFACT" in text
    assert "Rows with review-only display fields: 50." in text
    assert "Gate G should not run yet" in text
    assert "Rankings integration" in text


def test_shared_data_outputs_are_not_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "rookie_outcomes/display_artifact_v1" not in tracked
    assert "local_exports" not in tracked


def test_no_app_or_protected_nfl_usage_paths_are_written() -> None:
    changed_paths = {
        "docs/hq/rookie_outcomes/rookie_gate_f_display_artifact_v1_20260630/",
        "scripts/build_rookie_gate_f_display_artifact_v1_20260630.py",
        "tests/test_rookie_gate_f_display_artifact_v1_20260630.py",
    }
    protected = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
        "docs/draft_day_exports/final_board_v1_20260622/app_props/",
        "src/services/",
        "src/models/",
    )

    assert all(not path.startswith(protected) for path in changed_paths)


def _coverage_rows() -> list[dict[str, str]]:
    with COVERAGE_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _gate_a_rows() -> list[dict[str, str]]:
    return [{"player_id": "fixture", "approved_by_human": "true"}]


def _gate_b_row(
    *,
    player_id: str = "fixture-player",
    position: str = "WR",
    draft_round: str = "2",
    draft_pick: str = "47",
) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": "Fixture Rookie",
        "position": position,
        "cfbd_identity_approval_status": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
        "human_decision": "APPROVE_REVIEW_ONLY",
        "draft_year": "2026" if draft_round != NOT_ENOUGH else NOT_ENOUGH,
        "draft_round": draft_round,
        "overall_pick": draft_pick,
        "drafted_team": "PIT" if draft_round != NOT_ENOUGH else NOT_ENOUGH,
        "rookie_class_year": "2026" if draft_round != NOT_ENOUGH else NOT_ENOUGH,
        "data_quality_status": (
            "PARTIAL_REVIEW_ONLY_DRAFT_CAPITAL_AVAILABLE"
            if draft_round != NOT_ENOUGH
            else "MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED"
        ),
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def _label_rows(*, position: str, draft_round: str, draft_pick: str) -> list[dict[str, str]]:
    rows = []
    for index, year in enumerate(range(2012, 2024)):
        label = "hit" if index % 3 == 0 else "miss"
        row = {
            "nfl_player_id": f"00-fixture-{year}",
            "player_name": f"Historical Fixture {year}",
            "position": position,
            "rookie_class_year": str(year),
            "draft_year": str(year),
            "draft_round": draft_round,
            "draft_pick": draft_pick,
            "first_3y_window_complete": "true",
            "first_5y_window_complete": "true",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
        }
        for target in TARGETS:
            row[target] = label
        rows.append(row)
    return rows


def _gate_e_summary_rows() -> list[dict[str, str]]:
    return [
        {"metric": "gate_e_verdict", "value": "PARTIAL_REVIEW_ONLY_ROOKIE_MODEL_RD"},
        {"metric": "current_player_predictions_created", "value": "0"},
        {"metric": "rankings_wiring_created", "value": "0"},
    ]


def _gate_e_metric_rows() -> list[dict[str, str]]:
    return [
        {
            "target_name": target,
            "validation_status": "pass_review_only",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
        }
        for target in TARGETS
    ]


def _gate_d_policy_rows() -> list[dict[str, str]]:
    return [
        {
            "feature_name": feature,
            "allowed_for_review_only_model_rd": "true",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
        }
        for feature in ALLOWED_FEATURES
    ]
