from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_drafted_only_nflverse_feature_gate_evidence_v1_20260630 import (
    MATRIX_COLUMNS,
    OUTPUT_ROOT,
    VERDICT,
)

ROOT = Path(__file__).resolve().parents[1]


def test_feature_gate_matrix_schema_and_approval_invariants() -> None:
    rows = _rows("rookie_feature_gate_matrix.csv")

    assert set(rows[0]) == set(MATRIX_COLUMNS)
    assert len(rows) == 21
    assert {row["allowed_for_model_now"] for row in rows} == {"no"}
    assert {row["allowed_for_training_now"] for row in rows} == {"no"}
    assert {row["allowed_for_source_truth_now"] for row in rows} == {"no"}


def test_drafted_only_admission_is_positive_draft_picks_only() -> None:
    rows = _rows("rookie_feature_gate_matrix.csv")
    by_feature = {row["feature_family"]: row for row in rows}

    drafted = by_feature["draft_picks drafted admission"]
    assert drafted["drafted_only_admission_allowed"] == "yes_positive_draft_picks_only"
    assert drafted["allowed_for_display_now"] == "yes_review_only"
    assert "absence is not UDFA" in drafted["notes"]

    assert by_feature["draft round"]["drafted_only_admission_allowed"] == "component_only"
    assert "no fake round 8" in by_feature["draft round"]["missingness_rule"]
    assert by_feature["fake/synthetic draft capital"]["current_review_status"] == (
        "BLOCKED_QUARANTINE"
    )
    assert by_feature["fake/synthetic draft capital"]["allowed_for_display_now"] == (
        "quarantine_status_only"
    )


def test_post_draft_context_and_label_sources_are_blocked_from_features() -> None:
    rows = _rows("rookie_feature_gate_matrix.csv")
    by_feature = {row["feature_family"]: row for row in rows}

    assert by_feature["player_stats"]["allowed_as_label_source_now"] == (
        "future_sidecar_only_no_truth"
    )
    assert "Future NFL production" in by_feature["player_stats"]["notes"]
    assert by_feature["depth_charts"]["drafted_only_admission_allowed"] == "no"
    assert by_feature["depth_charts"]["leakage_risk"] == "high_current_role_leakage"
    assert by_feature["injury reports"]["blocker_reason"].startswith("Cannot become")
    assert by_feature["schedule context"]["allowed_for_display_now"] == (
        "no_current_future_safe_rows"
    )
    assert by_feature["Outcome V2 labels"]["allowed_as_label_source_now"] == (
        "review_only_label_target_not_feature"
    )


def test_udfa_cfbd_and_ff_rankings_remain_blocked() -> None:
    rows = _rows("rookie_feature_gate_matrix.csv")
    by_feature = {row["feature_family"]: row for row in rows}

    assert by_feature["UDFA status"]["current_review_status"] == "BLOCKED_FOR_MODELING"
    assert "Draft absence is not confirmed UDFA" in by_feature["UDFA status"][
        "missingness_rule"
    ]
    assert by_feature["likely_udfa_needs_review"]["current_review_status"] == (
        "BLOCKED_REVIEW_REQUIRED"
    )
    assert by_feature["CFBD joins"]["current_review_status"] == (
        "BLOCKED_REVIEW_ONLY_CANDIDATE"
    )
    assert by_feature["ff_rankings"]["current_review_status"] == "BLOCKED_VENDOR_OR_PRIVATE"


def test_required_docs_preserve_gate_e_f_g_and_guardrails() -> None:
    summary = (OUTPUT_ROOT / "drafted_only_feature_gate_summary.md").read_text(
        encoding="utf-8"
    )
    gates = (OUTPUT_ROOT / "gate_e_f_g_status_after_policy_gate.md").read_text(
        encoding="utf-8"
    )
    blockers = (OUTPUT_ROOT / "udfa_cfbd_blocker_reaudit.md").read_text(encoding="utf-8")
    safety = (OUTPUT_ROOT / "merge_safety_report.md").read_text(encoding="utf-8")

    assert VERDICT in summary
    assert "Gate G remains blocked" in gates
    assert "No Rankings" in gates
    assert "Confirmed historical UDFA rows: `0`" in blockers
    assert "CFBD model/training input remains blocked" in blockers
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
