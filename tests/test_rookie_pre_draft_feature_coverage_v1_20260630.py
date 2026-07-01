from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_pre_draft_feature_coverage_v1_20260630 import (
    FEATURE_COLUMNS,
    OUTPUT_ROOT,
    UNIVERSE_COLUMNS,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[1]


def test_pre_draft_feature_matrix_schema_and_closed_approval_flags() -> None:
    rows = _rows("rookie_pre_draft_feature_coverage_matrix.csv")

    assert list(rows[0]) == list(FEATURE_COLUMNS)
    assert len(rows) == 21
    assert {row["experiment_safe_now"] for row in rows} == {"false"}
    assert {row["allowed_for_model_now"] for row in rows} == {"false"}
    assert {row["allowed_for_training_now"] for row in rows} == {"false"}
    assert {row["allowed_for_source_truth_now"] for row in rows} == {"false"}


def test_drafted_only_universe_schema_and_review_only_flags() -> None:
    rows = _rows("drafted_only_universe_coverage.csv")

    assert list(rows[0]) == list(UNIVERSE_COLUMNS)
    assert len(rows) == 5
    by_slice = {row["coverage_slice"]: row for row in rows}
    assert by_slice["ALL_QB_RB_WR_TE"]["drafted_player_count"] == "1999"
    assert by_slice["ALL_QB_RB_WR_TE"]["draft_capital_complete_count"] == "1999"
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["source_truth_allowed"] for row in rows} == {"false"}


def test_positive_draft_picks_support_review_but_not_experiment() -> None:
    rows = _rows("rookie_pre_draft_feature_coverage_matrix.csv")
    by_feature = {row["feature_family"]: row for row in rows}

    drafted = by_feature["draft_picks drafted admission"]
    assert drafted["pre_draft_allowed_candidate"] == "true_review_admission_only"
    assert drafted["post_draft_only"] == "false"
    assert drafted["as_of_safe_now"] == "true_for_review_admission_only"
    assert drafted["experiment_safe_now"] == "false"
    assert "drafted-only review only" in drafted["notes"]

    assert by_feature["draft round"]["pre_draft_allowed_candidate"] == (
        "true_candidate_component"
    )
    assert "No fake round 8" in by_feature["draft round"]["blocker_reason"]
    assert by_feature["fake/synthetic draft capital"]["experiment_safe_now"] == "false"
    assert "No fake round 8" in by_feature["fake/synthetic draft capital"][
        "blocker_reason"
    ]


def test_pre_draft_candidates_require_asof_and_replay_gates() -> None:
    rows = _rows("rookie_pre_draft_feature_coverage_matrix.csv")
    by_feature = {row["feature_family"]: row for row in rows}

    combine = by_feature["combine"]
    assert combine["pre_draft_allowed_candidate"] == (
        "true_candidate_pending_coverage_gate"
    )
    assert combine["as_of_safe_now"] == "false"
    assert combine["replay_safe_now"] == "false"
    assert combine["experiment_safe_now"] == "false"

    age = by_feature["age"]
    assert age["pre_draft_allowed_candidate"] == (
        "true_candidate_pending_birthdate_asof_gate"
    )
    assert age["experiment_safe_now"] == "false"


def test_post_draft_and_label_contexts_are_not_pre_draft_features() -> None:
    rows = _rows("rookie_pre_draft_feature_coverage_matrix.csv")
    by_feature = {row["feature_family"]: row for row in rows}
    post_draft_features = (
        "rosters",
        "weekly_rosters",
        "snap_counts",
        "player_stats",
        "depth_charts",
        "injury reports",
        "schedule context",
        "contracts",
    )

    for feature_name in post_draft_features:
        row = by_feature[feature_name]
        assert row["pre_draft_allowed_candidate"] == "false"
        assert row["post_draft_only"] == "true"
        assert row["experiment_safe_now"] == "false"

    assert "Future NFL production" in by_feature["player_stats"]["blocker_reason"]
    assert by_feature["Outcome V2 labels"]["post_draft_only"] == "true_label_target_only"
    assert "never input features" in by_feature["Outcome V2 labels"]["blocker_reason"]


def test_udfa_cfbd_and_ff_rankings_remain_blocked() -> None:
    rows = _rows("rookie_pre_draft_feature_coverage_matrix.csv")
    by_feature = {row["feature_family"]: row for row in rows}

    assert by_feature["UDFA status"]["coverage_rows"] == "0"
    assert "draft absence is not confirmed UDFA" in by_feature["UDFA status"][
        "blocker_reason"
    ]
    assert by_feature["CFBD joins"]["drafted_player_match_count"] == (
        "0 approved model/training joins"
    )
    assert "CFBD model/training input remains blocked" in by_feature["CFBD joins"][
        "blocker_reason"
    ]
    assert by_feature["ff_rankings"]["coverage_rows"] == "blocked"


def test_required_docs_preserve_gate_status_and_guardrails() -> None:
    summary = (OUTPUT_ROOT / "pre_draft_feature_coverage_summary.md").read_text(
        encoding="utf-8"
    )
    gates = (OUTPUT_ROOT / "gate_e_f_g_recommendations.md").read_text(encoding="utf-8")
    leakage = (OUTPUT_ROOT / "leakage_and_asof_guardrail_report.md").read_text(
        encoding="utf-8"
    )
    safety = (OUTPUT_ROOT / "merge_safety_report.md").read_text(encoding="utf-8")

    assert VERDICT in summary
    assert "Experiment-safe feature count: `0`" in summary
    assert "Gate G remains blocked" in gates
    assert "Do not wire Rankings" in gates
    assert "Missing values remain `Not enough information`" in leakage
    assert "no app files changed" in safety
    assert "allowed_for_model_now=false" in safety


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
