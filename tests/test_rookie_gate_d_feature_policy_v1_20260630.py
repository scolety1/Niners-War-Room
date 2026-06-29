from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = (
    ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_d_feature_policy_v1_20260630"
    / "rookie_feature_policy_matrix_v1.csv"
)
DECISION_PATH = (
    ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_d_feature_policy_v1_20260630"
    / "01_GATE_D_FEATURE_POLICY_DECISION.md"
)


def test_feature_policy_matrix_schema_and_flags_are_closed() -> None:
    rows = _rows()
    required = {
        "feature_family",
        "feature_name",
        "source",
        "availability_status",
        "approval_status",
        "allowed_for_review_only_model_rd",
        "allowed_for_display_context",
        "model_use_allowed",
        "training_allowed",
        "review_only",
        "leakage_risk",
        "missingness_risk",
        "blocker_reason",
        "required_next_gate",
        "notes",
    }

    assert rows
    assert required.issubset(rows[0])
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["review_only"] for row in rows} == {"true"}


def test_allowed_features_are_limited_to_non_leaky_review_only_rd_set() -> None:
    allowed = {
        row["feature_name"]
        for row in _rows()
        if row["allowed_for_review_only_model_rd"] == "true"
    }

    assert allowed == {
        "draft_round",
        "draft_pick",
        "draft_capital_bucket",
        "draft_year",
        "rookie_class_year",
        "position",
    }


def test_blocked_and_leakage_features_are_not_allowed() -> None:
    rows = _rows()
    blocked = [
        row
        for row in rows
        if row["approval_status"] in {"blocked", "leakage_risk"}
        or row["availability_status"] == "blocked"
    ]
    leakage = [row for row in rows if row["leakage_risk"] == "high"]

    assert blocked
    assert leakage
    assert {row["allowed_for_review_only_model_rd"] for row in blocked} == {"false"}
    assert {row["allowed_for_review_only_model_rd"] for row in leakage} == {"false"}


def test_market_adp_dynastyprocess_vendor_gmail_are_blocked() -> None:
    rows_by_name = {row["feature_name"]: row for row in _rows()}

    for feature_name in (
        "market_adp_dynastyprocess",
        "rotowire_gmail_fantasypros_news",
        "rookie_projection_or_analyst_rank",
    ):
        row = rows_by_name[feature_name]
        assert row["approval_status"] == "blocked"
        assert row["allowed_for_review_only_model_rd"] == "false"
        assert row["allowed_for_display_context"] == "false"


def test_cfbd_features_remain_review_only_or_need_human_approval() -> None:
    cfbd_rows = [
        row
        for row in _rows()
        if row["feature_family"].startswith("cfbd")
        or "CFBD" in row["source"]
        or "CFBD" in row["notes"]
    ]

    assert cfbd_rows
    assert {row["allowed_for_review_only_model_rd"] for row in cfbd_rows} == {"false"}
    assert all(
        row["approval_status"] in {"needs_human_approval", "review_only_context", "missing"}
        for row in cfbd_rows
    )


def test_decision_doc_does_not_create_model_probabilities_or_rankings_wiring() -> None:
    text = DECISION_PATH.read_text(encoding="utf-8")

    assert "PARTIAL_FEATURES_ALLOWED_FOR_REVIEW_ONLY_MODEL_RD" in text
    assert "must not create production probabilities" in text
    assert "Rankings wiring" in text
    assert "model_use_allowed=false" in text
    assert "training_allowed=false" in text


def test_shared_data_outputs_are_not_tracked() -> None:
    tracked = subprocess.check_output(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
    )

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "rookie_outcomes/historical_labels_v1" not in tracked
    assert "local_exports" not in tracked


def test_lane_does_not_reference_protected_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("rookie_gate_d_feature_policy" not in path for path in protected_paths)


def _rows() -> list[dict[str, str]]:
    with MATRIX_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
