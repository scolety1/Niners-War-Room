from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_outcomes_nflverse_green_rerun_20260630 import (
    ADMISSION_COLUMNS,
    DATASET_RECEIPT_COLUMNS,
    FEATURE_COLUMNS,
    OUTPUT_ROOT,
    SIDECAR_COLUMNS,
    TARGET_DATASETS,
    VERDICT,
    WATCHLIST_COLUMNS,
)

ROOT = Path(__file__).resolve().parents[1]


def test_dataset_receipts_are_available_but_not_model_or_training() -> None:
    rows = _rows("nflverse_dataset_receipt_matrix.csv")
    by_dataset = {row["dataset_name"]: row for row in rows}

    assert set(rows[0]) == set(DATASET_RECEIPT_COLUMNS)
    assert set(by_dataset) == set(TARGET_DATASETS)
    assert {row["available_now"] for row in rows} == {"yes"}
    assert {row["approved_for_review"] for row in rows} == {"yes"}
    assert {row["approved_for_model_use"] for row in rows} == {"no"}
    assert {row["approved_for_training"] for row in rows} == {"no"}
    assert by_dataset["draft_picks"]["row_count"] == "514"
    assert by_dataset["combine"]["row_count"] == "650"
    assert by_dataset["depth_charts"]["row_count"] == "591527"
    assert by_dataset["player_stats"]["allowed_as_label_source"] == (
        "future_review_sidecar_only_requires_label_gate"
    )
    assert by_dataset["player_stats"]["allowed_as_feature_source"] == "no"


def test_drafted_only_admission_audit_is_review_only_and_real_rounds() -> None:
    rows = _rows("drafted_only_admission_gate_refresh_audit.csv")

    assert set(rows[0]) == set(ADMISSION_COLUMNS)
    assert len(rows) == 1999
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert all(row["admission_status"] == "drafted_admitted_review_only" for row in rows)
    assert all(1 <= int(row["draft_round"]) <= 7 for row in rows)
    assert not any(row["draft_round"] == "8" for row in rows)


def test_player_stats_sidecar_is_future_review_only_not_truth() -> None:
    rows = _rows("nflverse_player_stats_sidecar_feasibility.csv")

    assert set(rows[0]) == set(SIDECAR_COLUMNS)
    assert rows
    assert any(row["season_or_year"] == "2024" for row in rows)
    assert any(row["feasible_for_review_sidecar"] == "partial_future_lane" for row in rows)
    assert all("no label truth" in row["blocker_reason"].lower() for row in rows)
    assert all("Not enough information" in row["missing_match_count"] for row in rows)


def test_depth_chart_watchlist_remains_review_only_feasibility() -> None:
    rows = _rows("depth_chart_nondrafted_watchlist_refresh_feasibility.csv")

    assert set(rows[0]) == set(WATCHLIST_COLUMNS)
    assert rows
    assert sum(int(row["likely_udfa_or_nondrafted_count"]) for row in rows) == 28
    assert all(
        "cannot confirm UDFA" in row["blocker_reason"]
        or "cannot confirm udfa" in row["blocker_reason"].lower()
        for row in rows
    )
    allowed_statuses = {"partial_review_only", "blocked_no_depth_match"}
    assert all(row["feasible_for_review_watchlist"] in allowed_statuses for row in rows)


def test_gate_e_feature_manifest_keeps_context_out_of_model_use() -> None:
    rows = _rows("gate_e_feature_policy_refresh_manifest.csv")
    by_feature = {row["feature_name"]: row for row in rows}

    assert set(rows[0]) == set(FEATURE_COLUMNS)
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["review_only"] for row in rows} == {"true"}
    assert by_feature["depth_chart_rank"]["blocked_leakage"] == "yes"
    assert by_feature["injury_report_status"]["blocked_leakage"] == "yes"
    assert by_feature["player_stats"]["blocked_leakage"] == "yes"
    assert by_feature["ff_rankings"]["required_gate"] == "Blocked"


def test_required_docs_keep_gate_g_and_udfa_cfbd_blocked() -> None:
    summary = (OUTPUT_ROOT / "nflverse_green_rerun_summary.md").read_text(encoding="utf-8")
    gate = (OUTPUT_ROOT / "gate_f_gate_g_refresh_decision.md").read_text(encoding="utf-8")
    blocker = (OUTPUT_ROOT / "cfbd_udfa_blocker_refresh_status.md").read_text(encoding="utf-8")
    quarantine = (OUTPUT_ROOT / "synthetic_draft_capital_refresh_quarantine.md").read_text(
        encoding="utf-8"
    )
    manifest = (OUTPUT_ROOT / "artifact_manifest.md").read_text(encoding="utf-8")

    assert VERDICT in manifest
    assert "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN" in summary
    assert "Gate G remains blocked" in gate
    assert "Rankings/app wiring is not approved" in gate
    assert "Confirmed UDFA rows: `0`" in blocker
    assert "CFBD approved historical model/training join count: `0`" in blocker
    assert "No fake round 8" in quarantine
    assert "not confirmed UDFA" in quarantine


def test_no_protected_or_forbidden_paths_changed() -> None:
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    normalized_status = status.replace("\\", "/")

    assert "app/" not in normalized_status
    assert "src/services/" not in normalized_status
    assert "latest_candidate" not in normalized_status
    assert "latest_approved" not in normalized_status
    assert "final_board" not in normalized_status.lower()
    assert "pinned" not in normalized_status.lower()
    assert "local_exports" not in tracked
    assert "C:\\NWR_LOCAL_SECRETS" not in tracked
    assert "C:\\NWR_SHARED_DATA" not in tracked


def _rows(name: str) -> list[dict[str, str]]:
    with (OUTPUT_ROOT / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
