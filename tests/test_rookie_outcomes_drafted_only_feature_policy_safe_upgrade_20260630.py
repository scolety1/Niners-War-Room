from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_outcomes_drafted_only_feature_policy_safe_upgrade_20260630 import (
    ADMISSION_COLUMNS,
    FEATURE_COLUMNS,
    LABEL_COLUMNS,
    OUTPUT_ROOT,
    STATUS_COLUMNS,
    WAIT,
)

ROOT = Path(__file__).resolve().parents[1]


def test_status_matrix_classifies_required_deep_research_findings() -> None:
    rows = _rows("rookie_outcomes_safe_upgrade_status_matrix.csv")
    by_id = {row["finding_id"]: row for row in rows}

    assert set(rows[0]) == set(STATUS_COLUMNS)
    assert set(by_id) == {f"RO-{index:03d}" for index in range(1, 11)}
    assert by_id["RO-001"]["classification"] == "SAFE_NOW"
    assert by_id["RO-002"]["classification"] == "SAFE_NOW"
    assert by_id["RO-003"]["classification"] == WAIT
    assert by_id["RO-007"]["classification"] == "BLOCKED"
    assert by_id["RO-008"]["classification"] == "BLOCKED"
    assert by_id["RO-010"]["classification"] == "BLOCKED"
    assert "rankings" in by_id["RO-010"]["recommendation"].lower()


def test_admission_contract_blocks_udfa_inference_and_fake_rounds() -> None:
    rows = _rows("drafted_only_admission_gate_contract.csv")
    by_rule = {row["rule_id"]: row for row in rows}

    assert set(rows[0]) == set(ADMISSION_COLUMNS)
    assert by_rule["DAG-001"]["source"] == "nflverse draft_picks"
    assert by_rule["DAG-003"]["rule_name"] == "draft_absence_not_udfa"
    assert "Cannot become confirmed_udfa" in by_rule["DAG-003"]["blocked_result"]
    assert "Round 8" in by_rule["DAG-004"]["blocked_result"]
    assert {row["missing_data_behavior"] for row in rows} == {"Not enough information"}
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_gate_e_manifest_names_six_features_and_downgrades_replay_contract() -> None:
    rows = _rows("gate_e_feature_policy_manifest.csv")
    by_feature = {row["feature_name"]: row for row in rows}
    approved = {
        row["feature_name"]
        for row in rows
        if row["approved_in_gate_e_six_feature_cap"] == "yes"
    }
    replay_features = [
        "draft_capital_score",
        "age_trajectory_score",
        "production_score",
        "efficiency_score",
        "target_earning_score",
        "rushing_profile_score",
        "receiving_role_score",
        "athleticism_score",
        "lve_position_fit_score",
    ]

    assert set(rows[0]) == set(FEATURE_COLUMNS)
    assert approved == {
        "draft_year",
        "draft_round",
        "draft_pick",
        "draft_capital_bucket",
        "rookie_class_year",
        "position",
    }
    assert all(by_feature[name]["appears_in_replay_contract"] == "yes" for name in replay_features)
    assert all(
        by_feature[name]["approved_in_gate_e_six_feature_cap"] == "no"
        for name in replay_features
    )
    assert by_feature["Outcome V2 labels"]["blocked_leakage"] == "yes"
    assert by_feature["player_stats"]["required_gate"] == WAIT
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_label_partition_keeps_labels_out_of_features_and_training() -> None:
    rows = _rows("label_source_partition_matrix.csv")
    by_family = {row["label_family"]: row for row in rows}

    assert set(rows[0]) == set(LABEL_COLUMNS)
    assert by_family["Outcome V2 exact verified first-down labels"][
        "allowed_as_label_target"
    ] == "historical_review_only"
    assert by_family["Outcome V2 exact verified first-down labels"][
        "allowed_as_feature"
    ] == "false"
    assert by_family["model_v4 RotoWire-derived labels"]["display_only"] == "true"
    assert by_family["nflverse player_stats-derived sidecar labels"][
        "refresh_dependency"
    ] == WAIT
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_docs_keep_gate_f_gate_g_and_depth_chart_refresh_closed() -> None:
    depth = (OUTPUT_ROOT / "depth_chart_source_reaudit.md").read_text(encoding="utf-8")
    gate_f = (OUTPUT_ROOT / "gate_f_display_artifact_policy.md").read_text(encoding="utf-8")
    gate_g = (OUTPUT_ROOT / "gate_g_blocker_policy.md").read_text(encoding="utf-8")
    blocker = (OUTPUT_ROOT / "udfa_cfbd_blocker_update.md").read_text(encoding="utf-8")

    assert "no approved tracked populated depth-chart rows" in depth
    assert WAIT in depth
    assert "no active T12/T24/T36 outputs are approved" in gate_f
    assert "Gate G remains closed" in gate_g
    assert "Draft absence cannot confirm UDFA" in blocker
    assert "CFBD remains review-only" in blocker


def test_no_probabilities_source_truth_or_forbidden_paths_in_packet() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in OUTPUT_ROOT.iterdir()
        if path.suffix.lower() in {".md", ".csv"}
    )

    assert "model_use_allowed,true" not in combined
    assert "training_allowed,true" not in combined
    assert "source_truth_allowed,true" not in combined
    assert "rankings_wiring_allowed,true" not in combined
    assert "active rookie probabilities" in combined
    assert "fake T12/T24/T36" in combined
    assert "round 8" in combined.lower()
    assert "local_exports/" not in combined
    assert "C:\\NWR_LOCAL_SECRETS" not in combined
    assert "C:\\NWR_SHARED_DATA\\public_sources" not in combined


def test_no_protected_or_app_paths_changed() -> None:
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    normalized_status = status.replace("\\", "/")

    assert "app/" not in normalized_status
    assert "src/services/" not in normalized_status
    assert "latest_candidate" not in normalized_status
    assert "latest_approved" not in normalized_status
    assert "final_board" not in normalized_status.lower()
    assert "Dynasty Rank" not in normalized_status
    assert "Candidate Rank" not in normalized_status
    assert "local_exports" not in tracked
    assert "C:\\NWR_LOCAL_SECRETS" not in tracked
    assert "C:\\NWR_SHARED_DATA" not in tracked


def _rows(name: str) -> list[dict[str, str]]:
    with (OUTPUT_ROOT / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
