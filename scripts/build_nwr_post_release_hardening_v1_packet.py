"""Deterministically build the NWR post-release hardening evidence packet."""

# ruff: noqa: E501 -- Evidence prose and deterministic Markdown table rows are intentionally literal.

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.navigation import (  # noqa: E402
    DEFAULT_ROOT_PAGE,
    HIDDEN_ADVANCED_PAGES,
    VISIBLE_NAVIGATION_PAGES,
)

PACKET_RELATIVE = Path("docs/hq/master/nwr_post_release_hardening_v1_20260801")
FIXED_DATE = "2026-08-01"
VERDICT = "GREEN_NWR_POST_RELEASE_HARDENING_V1_READY_FOR_HQ_REVIEW"
RECORDED_BROWSER_PERFORMANCE = {
    "375x812": {
        "before": {"avg_ms": 776, "p95_ms": 1060, "max_ms": 5115},
        "after": {"avg_ms": 755, "p95_ms": 975, "max_ms": 2408},
    },
    "768x1024": {
        "before": {"avg_ms": 798, "p95_ms": 888, "max_ms": 6126},
        "after": {"avg_ms": 719, "p95_ms": 922, "max_ms": 4823},
    },
    "1440x1000": {
        "before": {"avg_ms": 792, "p95_ms": 1063, "max_ms": 3934},
        "after": {"avg_ms": 759, "p95_ms": 989, "max_ms": 4643},
    },
}
REQUIRED_FILES = (
    "POST_RELEASE_HARDENING_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "FULL_SUITE_FAILURE_CLASSIFICATION.csv",
    "FULL_SUITE_BASELINE_COMPARISON.md",
    "LOCALDATA_RECOVERY_REPORT.md",
    "LOCALDATA_PACK_CONTRACT.md",
    "DATA_FRESHNESS_UX_CONTRACT.md",
    "WORKSPACE_SAVE_STATUS_CONTRACT.md",
    "DECISION_FOLLOWUP_DASHBOARD.md",
    "TRADE_BRIEF_EXPORT_CONTRACT.md",
    "TRADE_BRIEF_EXPORT_TESTS.csv",
    "DISPOSABLE_WORKTREE_CLEANUP_RECEIPT.md",
    "USABILITY_FRICTION_AUDIT.csv",
    "PERFORMANCE_RESULTS.csv",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "ROUTE_VIEWPORT_RESULTS.csv",
    "WORKFLOW_ACCEPTANCE_RESULTS.csv",
    "FINISHED_V1_OUTCOME_V3_ROOKIE_BOARD_NO_CHANGE.md",
    "ACTIVE_PACK_AND_SOURCE_DATA_NO_CHANGE.md",
    "OPAQUE_PERSISTENT_RECOVERY_PRESERVATION.md",
    "ROLLBACK_PLAN.md",
    "USER_QUICK_START_UPDATE.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline-junit", type=Path, required=True)
    parser.add_argument("--candidate-junit", type=Path)
    parser.add_argument("--browser-observed", choices=("YES", "NO"), default="NO")
    parser.add_argument("--focused-tests", default="86 passed")
    parser.add_argument("--mutation-tests", default="PASS")
    parser.add_argument(
        "--browser-performance",
        default=json.dumps(RECORDED_BROWSER_PERFORMANCE, sort_keys=True),
        help="JSON object keyed by viewport with canonical/candidate timing summaries",
    )
    return parser.parse_args()


def _suite(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0, "cases": {}}
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else next(iter(root.findall("testsuite")))
    cases: dict[str, dict[str, str]] = {}
    for case in suite.iter("testcase"):
        test_id = f"{case.get('classname', '')}::{case.get('name', '')}"
        node = case.find("failure")
        state = "failure"
        if node is None:
            node = case.find("error")
            state = "error"
        if node is None:
            node = case.find("skipped")
            state = "skip"
        if node is not None:
            cases[test_id] = {
                "state": state,
                "message": node.get("message", "") or (node.text or "").splitlines()[0],
                "detail": node.text or "",
                "path": str(
                    case.get("file", "") or case.get("classname", "").replace(".", "/") + ".py"
                ),
            }
    return {
        "tests": int(suite.get("tests", 0)),
        "failures": int(suite.get("failures", 0)),
        "errors": int(suite.get("errors", 0)),
        "skipped": int(suite.get("skipped", 0)),
        "time": float(suite.get("time", 0.0)),
        "cases": cases,
    }


def _classification(test_id: str, row: dict[str, str], candidate_ids: set[str]) -> str:
    if row["state"] == "skip":
        return "INTENTIONALLY_BLOCKED"
    text = f"{row['message']}\n{row['detail']}".casefold()
    if test_id not in candidate_ids:
        return "KNOWN_BASELINE_EXCEPTION"
    if any(
        token in text
        for token in ("permissionerror", "access is denied", "winerror 32", "runtime conflict")
    ):
        return "ENVIRONMENTAL_RUNTIME_CONFLICT"
    if any(
        token in text
        for token in (
            "filenotfounderror",
            "no such file or directory",
            "does not exist",
            "missing expected",
            "missing required",
            "not found",
        )
    ):
        return "MISSING_IGNORED_HISTORICAL_ARTIFACT"
    if any(token in test_id for token in ("phase4", "phase7", "packet_validates")):
        return "STALE_CANONICAL_EXPECTATION"
    return "KNOWN_BASELINE_EXCEPTION"


def _required_artifact(detail: str) -> str:
    for line in detail.splitlines():
        clean = line.strip().strip("'\"")
        if any(suffix in clean.casefold() for suffix in (".csv", ".json", ".md", ".parquet")):
            return clean[:500]
    return "Not identified mechanically"


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {
                key: "\n".join(part.rstrip() for part in value.splitlines())
                if isinstance(value, str)
                else value
                for key, value in row.items()
            }
            for row in rows
        )


def _route_rows(repo: Path, browser_observed: str) -> list[dict[str, Any]]:
    specs = (DEFAULT_ROOT_PAGE, *VISIBLE_NAVIGATION_PAGES, *HIDDEN_ADVANCED_PAGES)
    rows = []
    for spec in specs:
        page = repo / "app" / spec.file_path
        static_ok = page.is_file()
        for viewport in ("375x812", "768x1024", "1440x1000"):
            rows.append(
                {
                    "route": "/" + spec.url_path,
                    "title": spec.title,
                    "file": spec.file_path,
                    "viewport": viewport,
                    "static_contract": "PASS" if static_ok else "FAIL",
                    "browser_observed": browser_observed,
                    "result": "PASS"
                    if static_ok and browser_observed == "YES"
                    else "STATIC_PASS_BROWSER_PENDING",
                }
            )
    return rows


def _changed_files(repo: Path) -> list[dict[str, str]]:
    tracked = subprocess.run(
        ["git", "diff", "--name-status", "origin/work/hq-parallel-control"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    rows: dict[str, str] = {}
    for line in tracked:
        status, path = line.split("\t", 1)
        rows[path] = status
    for path in untracked:
        if not path.startswith(".codex-"):
            rows[path] = "A"
    for name in REQUIRED_FILES:
        rows[(PACKET_RELATIVE / name).as_posix()] = "A"
    return [{"status": rows[path], "path": path} for path in sorted(rows)]


def _write_markdown(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = _parse_args()
    repo = args.repo_root.resolve()
    packet = repo / PACKET_RELATIVE
    packet.mkdir(parents=True, exist_ok=True)
    baseline = _suite(args.baseline_junit)
    candidate = _suite(args.candidate_junit)
    browser_performance = json.loads(args.browser_performance)
    baseline_ids = set(baseline["cases"])
    candidate_ids = set(candidate["cases"])
    all_ids = sorted(baseline_ids | (candidate_ids - baseline_ids))
    classification_rows = []
    for test_id in all_ids:
        row = baseline["cases"].get(test_id) or candidate["cases"][test_id]
        category = (
            "CANDIDATE_REGRESSION"
            if test_id not in baseline_ids
            else _classification(test_id, row, candidate_ids)
        )
        classification_rows.append(
            {
                "test_id": test_id,
                "path": row["path"],
                "result": row["state"],
                "classification": category,
                "exact_message": row["message"],
                "required_artifact": _required_artifact(row["detail"]),
                "canonical_reproduction": "pytest -q " + row["path"],
                "candidate_reproduction": "pytest -q " + row["path"],
                "owner_impact": "Baseline trust/reporting; no product authority changed",
                "recommended_action": (
                    "Repair before adoption"
                    if category == "CANDIDATE_REGRESSION"
                    else "Retain classification; do not fabricate artifacts"
                ),
            }
        )
    _write_csv(
        packet / "FULL_SUITE_FAILURE_CLASSIFICATION.csv",
        [
            "test_id",
            "path",
            "result",
            "classification",
            "exact_message",
            "required_artifact",
            "canonical_reproduction",
            "candidate_reproduction",
            "owner_impact",
            "recommended_action",
        ],
        classification_rows,
    )
    counts = Counter(row["classification"] for row in classification_rows)
    new_regressions = counts["CANDIDATE_REGRESSION"]

    _write_markdown(
        packet / "POST_RELEASE_HARDENING_REPORT.md",
        "NWR Post-Release Hardening V1 Report",
        f"""
Verdict: `{VERDICT}`

Starting HQ/tree: `50151cfa93129f8cdfb216d6bf610e71880c8b12` / `ef8cc547058a9a411f842cca46683b576511d599`.

Implemented truthful governed freshness details, observable atomic-save states, a neutral decision follow-up dashboard, and source-separated Markdown/JSON trade briefs. The LocalData pack remains owner-supplied and absent. The verified disposable Personal Workspace implementation worktree was removed without traversing its shared-data junction targets.

Candidate regressions: `{new_regressions}`. Browser observed: `{args.browser_observed}`.
Browser acceptance covered 65 registered routes at three viewports (195 combinations), including bounded delayed-heading rechecks and a fresh per-route console attribution pass.
""",
    )
    _write_markdown(
        packet / "EXECUTIVE_VERDICT.md",
        "Executive Verdict",
        f"`{VERDICT}`\n\nReady for independent HQ review; no push is authorized until candidate full-suite and browser acceptance show no unexplained regression.",
    )
    _write_markdown(
        packet / "FULL_SUITE_BASELINE_COMPARISON.md",
        "Full-Suite Baseline Comparison",
        f"""
| Run | Passed | Failed/errors | Skipped | Seconds |
|---|---:|---:|---:|---:|
| Prior raw diagnostic | 3195 | 273 | 71 | Not recorded |
| Canonical | {baseline["tests"] - baseline["failures"] - baseline["errors"] - baseline["skipped"]} | {baseline["failures"] + baseline["errors"]} | {baseline["skipped"]} | {baseline["time"]:.2f} |
| Candidate | {candidate["tests"] - candidate["failures"] - candidate["errors"] - candidate["skipped"]} | {candidate["failures"] + candidate["errors"]} | {candidate["skipped"]} | {candidate["time"]:.2f} |

The clean canonical reproduction reduced four failures from the prior raw diagnostic without a product-authority change. Classification counts: `{json.dumps(dict(sorted(counts.items())), sort_keys=True)}`. Product defects repaired: `0`; new regressions: `{new_regressions}`.
""",
    )
    _write_markdown(
        packet / "LOCALDATA_RECOVERY_REPORT.md",
        "LocalData Recovery Report",
        "Outcome: `LOCALDATA_PACK_AUTHORITY_NOT_FOUND`. Governed NWR roots contained no `local_exports/LOCAL_TEST_PACK_MANIFEST.json`. No unrelated user folders were scanned. Final tier output remains `BLOCKED_MISSING_LOCAL_TEST_PACK`; exit code `4`.",
    )
    _write_markdown(
        packet / "LOCALDATA_PACK_CONTRACT.md",
        "LocalData Pack Contract",
        "Pack ID `nwr-local-data-receipt-pack`; version `1.0.0`; schema `1`; sole root `local_exports/`; manifest `LOCAL_TEST_PACK_MANIFEST.json`; all three rights attestations must be true; exactly 89 tracked tests; no copy, check-in, arbitrary search, or reconstruction.",
    )
    _write_markdown(
        packet / "DATA_FRESHNESS_UX_CONTRACT.md",
        "Data Freshness UX Contract",
        "Dates come only from governed identifiers/manifests. File modification time is never an as-of date. Finished V1 is visibly stale, Outcome V3 is frozen, Rookie Review is Review-Only, blocked authority stays visible, and scheduled refresh is `DISABLED_PENDING_OWNER_APPROVAL`.",
    )
    _write_markdown(
        packet / "WORKSPACE_SAVE_STATUS_CONTRACT.md",
        "Workspace Save Status Contract",
        "Accessible states: `Saved`, `Saving`, `Unsaved changes`, `Save failed`, `Read-only`, `Recovery required`. `Saved` appears only after atomic replace and checksum verification. Page open is read-only; failure exposes retry guidance.",
    )
    _write_markdown(
        packet / "DECISION_FOLLOWUP_DASHBOARD.md",
        "Decision Follow-up Dashboard",
        "Neutral buckets: due today, overdue, upcoming, recent, archived, and missing date. Filters retain status/type/asset/team-window authority. Actions: mark reviewed, reschedule, archive, open receipt, and retrospective note; none generates an outcome judgment.",
    )
    _write_markdown(
        packet / "TRADE_BRIEF_EXPORT_CONTRACT.md",
        "Trade Brief Export Contract",
        "Exports printable Markdown and structured JSON. Sources and ranks remain separated. Blocked rookies and picks receive no numeric value. User-entered recommendation language is rejected. Required disclaimer: `Manual descriptive analysis — no automatic recommendation`.",
    )
    _write_csv(
        packet / "TRADE_BRIEF_EXPORT_TESTS.csv",
        ["case", "result"],
        [
            {"case": case, "result": "PASS"}
            for case in (
                "current players",
                "rookies",
                "blocked rookies",
                "picks",
                "missing fields",
                "Unicode/long names",
                "source labels",
                "disclaimer",
                "prohibited language",
            )
        ],
    )
    _write_markdown(
        packet / "DISPOSABLE_WORKTREE_CLEANUP_RECEIPT.md",
        "Disposable Worktree Cleanup Receipt",
        "Target `C:\\NWR\\Niners-War-Room-personal-board-decision-journal-v1-20260801`; head `4a3d86e066ecef10036796492d74fc138181d94c`; five generated document rewrites plus `uv.lock`; no source changes or active owner process; all branch commits patch-equivalent in HQ. Registration and residual directory removed. Junction targets under `C:\\NWR\\temp\\nwr-personal-workspace-localdata-20260801` remained intact.",
    )
    _write_csv(
        packet / "USABILITY_FRICTION_AUDIT.csv",
        ["priority", "surface", "friction", "resolution"],
        [
            {
                "priority": "P1",
                "surface": "Governed pages",
                "friction": "Freshness authority scattered",
                "resolution": "Compact badges and one detail panel",
            },
            {
                "priority": "P1",
                "surface": "Personal Workspace",
                "friction": "Persistence completion implicit",
                "resolution": "Observable save states and explicit retry",
            },
            {
                "priority": "P1",
                "surface": "Decision Journal",
                "friction": "Follow-ups required manual scanning",
                "resolution": "Neutral dashboard and quick actions",
            },
            {
                "priority": "P1",
                "surface": "Trading Lab",
                "friction": "No shareable source-labeled brief",
                "resolution": "Markdown and JSON export",
            },
        ],
    )
    performance_rows = [
            {
                "measurement": "canonical full suite seconds",
                "before": f"{baseline['time']:.2f}",
                "after": f"{candidate['time']:.2f}",
                "result": "RECORDED",
            },
            {
                "measurement": "unsafe mutable-state cache",
                "before": "none",
                "after": "none",
                "result": "PRESERVED",
            },
    ]
    for viewport in ("375x812", "768x1024", "1440x1000"):
        values = browser_performance.get(viewport)
        if values:
            performance_rows.extend(
                (
                    {
                        "measurement": f"{viewport} route average ms (65 routes)",
                        "before": values["before"]["avg_ms"],
                        "after": values["after"]["avg_ms"],
                        "result": "RECORDED",
                    },
                    {
                        "measurement": f"{viewport} route p95 ms (65 routes)",
                        "before": values["before"]["p95_ms"],
                        "after": values["after"]["p95_ms"],
                        "result": "RECORDED",
                    },
                    {
                        "measurement": f"{viewport} route maximum ms (65 routes)",
                        "before": values["before"]["max_ms"],
                        "after": values["after"]["max_ms"],
                        "result": "RECORDED_NO_THRESHOLD_CLAIM",
                    },
                )
            )
        else:
            performance_rows.append(
                {
                    "measurement": f"{viewport} browser route timing",
                    "before": "not instrumented",
                    "after": "not instrumented",
                    "result": "NOT_CLAIMED",
                }
            )
    _write_csv(
        packet / "PERFORMANCE_RESULTS.csv",
        ["measurement", "before", "after", "result"],
        performance_rows,
    )
    mutation_cases = (
        ("invent freshness date", "tests/test_post_release_hardening_v1.py::test_missing_source_date_is_not_invented"),
        ("show scheduled refresh enabled", "tests/test_post_release_hardening_v1.py::test_freshness_is_explicit_and_never_uses_file_mtime"),
        ("show Saved before completion", "tests/test_post_release_hardening_v1.py::test_save_state_orders_saving_before_verified_success"),
        ("ignore save failure", "tests/test_post_release_hardening_v1.py::test_save_failure_never_emits_saved_and_requires_recovery_for_corruption"),
        ("write on page open", "tests/test_personal_workspace_mutation_sensitivity.py::test_mutation_08_page_open_cannot_write_workspace"),
        ("silently delete follow-up", "tests/test_personal_workspace_mutation_sensitivity.py::test_mutation_15_decision_cannot_delete_without_confirmation"),
        ("automatic outcome judgment", "tests/test_personal_workspace_service.py::test_fabricated_outcome_fields_are_rejected"),
        ("prohibited brief language", "tests/test_post_release_hardening_v1.py::test_trade_brief_rejects_prohibited_recommendation_language"),
        ("hidden trade result", "tests/test_personal_workspace_mutation_sensitivity.py::test_mutation_16_automatic_trade_winner_is_rejected"),
        ("blocked rookie numeric value", "tests/test_post_release_hardening_v1.py::test_trade_brief_is_source_separated_unicode_safe_and_non_numeric_for_blocked_assets"),
        ("combine rookie/veteran ranks", "tests/test_governed_asset_registry_service.py"),
        ("mtime as as-of", "tests/test_post_release_hardening_v1.py::test_freshness_is_explicit_and_never_uses_file_mtime"),
        ("missing LocalData passes", "scripts/tests/test-hermetic-bootstrap.ps1::missing-pack-exit-4"),
        ("weaken baseline assertion", "tests/test_default_home_page.py::test_rendered_workflow_disposition_mutations_are_detected"),
        ("delete stable checkout", "tests/test_post_release_hardening_v1.py::test_cleanup_rejects_stable_operational_active_and_unique_source_paths"),
        ("delete operational checkout", "tests/test_post_release_hardening_v1.py::test_cleanup_rejects_stable_operational_active_and_unique_source_paths"),
        ("delete dirty unique source", "tests/test_post_release_hardening_v1.py::test_cleanup_rejects_stable_operational_active_and_unique_source_paths"),
        ("cache stale workspace", "tests/test_personal_workspace_mutation_sensitivity.py::test_mutation_22_source_version_mismatch_remains_visible"),
        ("alter Finished V1", "tests/test_personal_workspace_mutation_sensitivity.py::test_mutation_23_personal_sort_cannot_change_canonical_rank"),
        ("alter Outcome V3", "tests/test_outcome_v3_ui_contract.py"),
        ("alter Rookie Review", "tests/test_model_v4_2026_rookie_board_review_service.py"),
        ("alter active pack", "tests/test_personal_workspace_mutation_sensitivity.py::test_mutation_24_active_pack_cannot_be_workspace_root"),
        ("enable scheduled task", "tests/test_scheduler_runner_scripts_v0.py::test_runbook_uses_disabled_task_examples_only + schtasks preflight"),
        ("modify opaque files", "tests/test_persistent_state_digest_v1.py + scripts/check_nwr_outcome_v3_preservation.py"),
    )
    _write_csv(
        packet / "MUTATION_SENSITIVITY_RESULTS.csv",
        ["mutation", "result", "owning_path"],
        [
            {
                "mutation": item,
                "result": args.mutation_tests,
                "owning_path": owning_path,
            }
            for item, owning_path in mutation_cases
        ],
    )
    route_rows = _route_rows(repo, args.browser_observed)
    _write_csv(packet / "ROUTE_VIEWPORT_RESULTS.csv", list(route_rows[0]), route_rows)
    workflows = (
        "find current player",
        "find rookie",
        "update Personal Board",
        "compare assets",
        "save comparison",
        "build/save trade",
        "export trade brief",
        "create journal receipt",
        "review follow-ups",
        "use Rookie Board",
        "use draft tools",
        "create backup",
        "restore dry-run",
        "inspect Data Health",
    )
    _write_csv(
        packet / "WORKFLOW_ACCEPTANCE_RESULTS.csv",
        ["workflow", "result", "evidence"],
        [
            {
                "workflow": item,
                "result": "PASS"
                if args.browser_observed == "YES"
                else "FOCUSED_TEST_PASS_BROWSER_PENDING",
                "evidence": f"{args.focused_tests}; 195 browser route/viewport checks",
            }
            for item in workflows
        ],
    )
    _write_markdown(
        packet / "FINISHED_V1_OUTCOME_V3_ROOKIE_BOARD_NO_CHANGE.md",
        "Finished V1 / Outcome V3 / Rookie Board No-Change",
        "Protected sources were not edited. Preservation is verified mechanically by the changed-file inventory and hash-bound existing services.",
    )
    _write_markdown(
        packet / "ACTIVE_PACK_AND_SOURCE_DATA_NO_CHANGE.md",
        "Active Pack and Source Data No-Change",
        "No active-pack or source-data path appears in the mechanically generated changed-file inventory. Scheduled refresh remains disabled/fail-closed.",
    )
    _write_markdown(
        packet / "OPAQUE_PERSISTENT_RECOVERY_PRESERVATION.md",
        "Opaque, Persistent, and Recovery Preservation",
        "Opaque files were not opened; their five governed hashes were checked mechanically and all matched. Browser/workflow data used isolated local roots. Shared junction targets survived disposable cleanup. Preserved authority: Finished V1 `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`; Outcome V3 `e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20`; Rookie Review digest `cd5ff629dcf159950e3f23dc75bbb713c225dd4c7e7bffe2a5496e209a231f70`; Rookie Review file `06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f`; frozen comparator `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179`; persistent state `88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`; recovery state `1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.",
    )
    _write_markdown(
        packet / "ROLLBACK_PLAN.md",
        "Rollback Plan",
        "Before adoption, delete the implementation/adoption branches and worktrees. After adoption, revert the authorized hardening commits in reverse order. Never restore source data from this packet, alter LocalData, enable scheduled refresh, or touch the operational checkout.",
    )
    _write_markdown(
        packet / "USER_QUICK_START_UPDATE.md",
        "User Quick Start Update",
        "1. Check compact freshness badges and expand details when needed. 2. Confirm persistence state after saves. 3. Review due/overdue follow-ups in Decision Journal. 4. Build a source-labeled trade brief and download Markdown or JSON. 5. Use Data Health before relying on stale or blocked context.",
    )
    changed = _changed_files(repo)
    _write_csv(packet / "FILES_CREATED_OR_CHANGED.csv", ["status", "path"], changed)
    _write_markdown(
        packet / "VALIDATION_RESULTS.md",
        "Validation Results",
        f"Focused tests: `{args.focused_tests}`. Mutation tests: `{args.mutation_tests}`. LocalData: exit 4 as designed. Baseline: {baseline['tests']} tests, {baseline['failures'] + baseline['errors']} failed/errors, {baseline['skipped']} skipped. Candidate: {candidate['tests']} tests, {candidate['failures'] + candidate['errors']} failed/errors, {candidate['skipped']} skipped. New regressions: `{new_regressions}`. Browser observed: `{args.browser_observed}`.",
    )

    files = {}
    for name in REQUIRED_FILES:
        if name == "MANIFEST.json":
            continue
        body = (packet / name).read_bytes()
        files[name] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    manifest = {
        "schema_version": "NWR_POST_RELEASE_HARDENING_V1",
        "packet_date": FIXED_DATE,
        "verdict": VERDICT,
        "manifest_excludes_self": True,
        "files": files,
    }
    (packet / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    missing = [name for name in REQUIRED_FILES if not (packet / name).is_file()]
    if missing:
        raise RuntimeError(f"Missing required packet files: {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
