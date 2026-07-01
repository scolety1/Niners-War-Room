from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_pre_draft_asof_coverage_builder_v1_20260630 import (
    ADMISSION_COLUMNS,
    ASOF_COLUMNS,
    OUTPUT_ROOT,
    PLAYER_COLUMNS,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[1]


def test_asof_matrix_schema_and_approval_invariants() -> None:
    rows = _rows("rookie_pre_draft_asof_coverage_matrix.csv")

    assert list(rows[0]) == list(ASOF_COLUMNS)
    assert len(rows) == 23
    assert {row["experiment_ready_now"] for row in rows} == {"false"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["source_truth_allowed"] for row in rows} == {"false"}


def test_player_level_coverage_schema_and_review_only_flags() -> None:
    rows = _rows("drafted_only_player_feature_coverage.csv")

    assert list(rows[0]) == list(PLAYER_COLUMNS)
    assert len(rows) == 1999
    assert {row["draft_pick_evidence_present"] for row in rows} == {"true"}
    assert {row["review_required"] for row in rows} == {"true"}
    assert {row["as_of_safe_now"] for row in rows} == {"false"}
    assert {row["experiment_ready_now"] for row in rows} == {"false"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["source_truth_allowed"] for row in rows} == {"false"}
    assert {row["combine_row_present"] for row in rows} == {"Not enough information"}
    assert {row["prospect_age_present"] for row in rows} == {"Not enough information"}
    assert {row["college_present"] for row in rows} == {"Not enough information"}


def test_drafted_admission_manifest_is_review_only_admission_not_model_use() -> None:
    rows = _rows("rookie_drafted_admission_manifest.csv")

    assert list(rows[0]) == list(ADMISSION_COLUMNS)
    assert len(rows) == 1999
    assert {row["positive_draft_picks_evidence"] for row in rows} == {"true"}
    assert {row["review_admission_status"] for row in rows} == {
        "drafted_only_review_admission"
    }
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["source_truth_allowed"] for row in rows} == {"false"}
    assert all("not confirmed UDFA" in row["missingness_rule"] for row in rows)


def test_draft_event_and_candidate_features_are_not_experiment_ready() -> None:
    by_feature = _by_feature()

    drafted = by_feature["positive draft_picks evidence"]
    assert drafted["draft_event_feature"] == "true"
    assert drafted["as_of_safe_now"] == "true_for_review_admission_only"
    assert drafted["experiment_ready_now"] == "false"

    assert by_feature["draft round"]["draft_event_feature"] == "true"
    assert "No fake round 8" in by_feature["draft round"]["blocker_reason"]
    assert by_feature["combine"]["candidate_pre_draft_feature"] == "true"
    assert by_feature["combine"]["as_of_safe_now"] == "false"
    assert by_feature["prospect age"]["candidate_pre_draft_feature"] == "true"
    assert by_feature["prospect age"]["as_of_safe_now"] == "false"
    assert by_feature["college/school"]["missing_count"] == "1999"


def test_post_draft_current_and_label_contexts_are_blocked_as_pre_draft_features() -> None:
    by_feature = _by_feature()
    blocked_post_draft = (
        "rosters",
        "weekly_rosters",
        "injuries",
        "depth charts",
        "snap_counts",
        "player_stats",
        "schedules",
        "contracts",
        "current team/status",
        "Outcome V2 labels",
    )

    for feature_name in blocked_post_draft:
        row = by_feature[feature_name]
        assert row["candidate_pre_draft_feature"] == "false"
        assert row["post_draft_only"] == "true"
        assert row["experiment_ready_now"] == "false"

    assert "Future NFL production" in by_feature["player_stats"]["blocker_reason"]
    assert "Current team/status is post-draft context" in by_feature["current team/status"][
        "blocker_reason"
    ]
    assert "never pre-draft features" in by_feature["Outcome V2 labels"][
        "blocker_reason"
    ]


def test_udfa_cfbd_and_ff_rankings_remain_blocked() -> None:
    by_feature = _by_feature()

    assert by_feature["UDFA status"]["row_count"] == "0"
    assert "draft absence is not confirmed UDFA" in by_feature["UDFA status"][
        "blocker_reason"
    ]
    assert by_feature["CFBD joins"]["drafted_player_match_count"] == (
        "0 approved model/training joins"
    )
    assert "CFBD model/training input remains blocked" in by_feature["CFBD joins"][
        "blocker_reason"
    ]
    assert by_feature["ff_rankings"]["row_count"] == "blocked"


def test_required_docs_preserve_non_activation_posture() -> None:
    summary = (OUTPUT_ROOT / "rookie_pre_draft_asof_build_summary.md").read_text(
        encoding="utf-8"
    )
    gates = (OUTPUT_ROOT / "gate_e_f_g_status.md").read_text(encoding="utf-8")
    leakage = (OUTPUT_ROOT / "leakage_guardrail_report.md").read_text(encoding="utf-8")
    safety = (OUTPUT_ROOT / "merge_safety_report.md").read_text(encoding="utf-8")

    assert VERDICT in summary
    assert "Feature-family experiment-ready rows: `0`" in summary
    assert "Player-level experiment-ready rows: `0`" in summary
    assert "Gate G remains blocked" in gates
    assert "No Rankings" in gates
    assert "Missing values remain `Not enough information`" in leakage
    assert "no app files changed" in safety


def test_no_forbidden_or_protected_paths_changed() -> None:
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


def _by_feature() -> dict[str, dict[str, str]]:
    return {
        row["feature_family"]: row
        for row in _rows("rookie_pre_draft_asof_coverage_matrix.csv")
    }
