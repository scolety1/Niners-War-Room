from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.stdout, result.stderr
    return json.loads(result.stdout)


def test_local_only_guard_report_schema() -> None:
    output = _run_json([sys.executable, "scripts/validate_local_only_surface_guard.py", "--report"])

    assert {
        "verdict",
        "root",
        "checked_path_count",
        "checked_categories",
        "blocked_surface_count",
        "reason_summary",
        "violations",
    } <= set(output)


def test_readiness_runner_json_schema() -> None:
    output = _run_json([sys.executable, "scripts/run_deployment_v2_readiness_checks.py", "--json"])

    assert {
        "verdict",
        "branch",
        "head",
        "clean_status",
        "diff_check",
        "local_only_guard",
        "guard_report",
        "import_report",
        "baseline_ancestry",
        "docs_audit",
        "checks",
    } <= set(output)


def test_import_helper_json_schema_for_missing_zip(tmp_path: Path) -> None:
    output = _run_json(
        [
            sys.executable,
            "scripts/compare_deployment_v2_import_report.py",
            str(tmp_path / "missing.zip"),
            "--json",
        ]
    )

    assert {
        "verdict",
        "reasons",
        "report_head",
        "current_head",
        "ancestor_or_match",
        "clean_status",
        "diff_check",
    } <= set(output)


def test_docs_audit_json_schema() -> None:
    output = _run_json([sys.executable, "scripts/audit_deployment_v2_docs_consistency.py", "--json"])

    assert {
        "verdict",
        "required_phrases",
        "missing_phrases",
        "notes",
        "blocked_language_hits",
        "historical_path_notes",
        "findings",
    } <= set(output)


def test_transcript_json_schema() -> None:
    output = _run_json([sys.executable, "scripts/print_deployment_v2_operator_transcript.py", "--json"])

    assert {
        "lane",
        "readiness_verdict",
        "final_verdict",
        "branch",
        "head",
        "baseline_ancestry",
        "readiness",
        "docs_consistency",
        "hosted_deployment",
        "remaining_blockers",
        "deploy_surface_added",
        "other_lane_touched",
    } <= set(output)


def test_baseline_ancestry_json_schema() -> None:
    output = _run_json(
        [
            sys.executable,
            "scripts/verify_deployment_v2_baseline_ancestry.py",
            "a459044e049befc3d5fef5fcd9e147fc271c168e",
            "--json",
        ]
    )

    assert {
        "verdict",
        "baseline",
        "current_head",
        "ancestor",
        "clean_required",
        "clean_status",
        "status_short",
        "reasons",
    } <= set(output)
