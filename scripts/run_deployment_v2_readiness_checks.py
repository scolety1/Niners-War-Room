from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

EXPECTED_BRANCH = "work/deployment-v2-discovery"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def run_command(repo: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def status_rank(status: str) -> int:
    return {
        "GREEN": 0,
        "PASS": 0,
        "SKIPPED": 0,
        "YELLOW": 1,
        "BLOCKED": 2,
        "RED": 2,
        "FAIL": 2,
    }.get(status, 1)


def overall_verdict(results: list[CheckResult]) -> str:
    worst = max((status_rank(result.status) for result in results), default=0)
    if worst >= 2:
        return "RED"
    if worst == 1:
        return "YELLOW"
    return "GREEN"


def check_branch(repo: Path) -> CheckResult:
    result = run_command(repo, ["git", "branch", "--show-current"])
    branch = result.stdout.strip()
    if result.returncode != 0:
        return CheckResult("branch", "RED", result.stderr.strip() or "git branch failed")
    if branch != EXPECTED_BRANCH:
        return CheckResult("branch", "RED", f"current branch {branch}, expected {EXPECTED_BRANCH}")
    return CheckResult("branch", "GREEN", branch)


def check_head(repo: Path) -> CheckResult:
    full = run_command(repo, ["git", "rev-parse", "HEAD"])
    short = run_command(repo, ["git", "rev-parse", "--short", "HEAD"])
    subject = run_command(repo, ["git", "log", "-1", "--pretty=%s"])
    if full.returncode != 0 or short.returncode != 0 or subject.returncode != 0:
        return CheckResult("head", "RED", "could not read HEAD")
    return CheckResult(
        "head",
        "GREEN",
        f"{short.stdout.strip()} {subject.stdout.strip()} ({full.stdout.strip()})",
    )


def check_status(repo: Path) -> CheckResult:
    result = run_command(repo, ["git", "status", "--short"])
    output = result.stdout.strip()
    if result.returncode != 0:
        return CheckResult("status", "RED", result.stderr.strip() or "git status failed")
    if output:
        return CheckResult("status", "RED", output)
    return CheckResult("status", "GREEN", "clean")


def check_diff(repo: Path) -> CheckResult:
    result = run_command(repo, ["git", "diff", "--check"])
    output = result.stdout.strip()
    if result.returncode != 0 or output:
        detail = output or result.stderr.strip() or "diff check failed"
        return CheckResult("diff_check", "RED", detail)
    return CheckResult("diff_check", "GREEN", "clean")


def check_local_guard_text(repo: Path, python_executable: str) -> CheckResult:
    result = run_command(
        repo,
        [python_executable, "scripts/validate_local_only_surface_guard.py"],
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        return CheckResult("local_only_guard", "RED", output)
    return CheckResult("local_only_guard", "GREEN", output)


def check_local_guard_report(repo: Path, python_executable: str) -> CheckResult:
    result = run_command(
        repo,
        [python_executable, "scripts/validate_local_only_surface_guard.py", "--report"],
    )
    output = result.stdout.strip()
    if result.returncode != 0:
        return CheckResult("local_only_guard_report", "RED", (output + result.stderr).strip())
    try:
        report = json.loads(output)
    except json.JSONDecodeError as exc:
        return CheckResult("local_only_guard_report", "RED", f"invalid JSON report: {exc}")
    if report.get("verdict") != "GREEN" or report.get("blocked_surface_count") != 0:
        return CheckResult("local_only_guard_report", "RED", output)
    return CheckResult(
        "local_only_guard_report",
        "GREEN",
        (
            f"verdict={report.get('verdict')} "
            f"blocked_surface_count={report.get('blocked_surface_count')}"
        ),
    )


def check_import_report(
    repo: Path,
    python_executable: str,
    import_zip: str | None,
) -> CheckResult:
    if not import_zip:
        return CheckResult("import_report_comparison", "SKIPPED", "no import zip supplied")

    result = run_command(
        repo,
        [
            python_executable,
            "scripts/compare_deployment_v2_import_report.py",
            import_zip,
        ],
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return CheckResult("import_report_comparison", "GREEN", output)
    if result.returncode == 2:
        return CheckResult("import_report_comparison", "YELLOW", output)
    return CheckResult("import_report_comparison", "RED", output)


def check_docs_audit(repo: Path, python_executable: str) -> CheckResult:
    result = run_command(
        repo,
        [python_executable, "scripts/audit_deployment_v2_docs_consistency.py"],
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        return CheckResult("docs_consistency_audit", "GREEN", output)
    if result.returncode == 2:
        return CheckResult("docs_consistency_audit", "YELLOW", output)
    return CheckResult("docs_consistency_audit", "RED", output)


def run_readiness_checks(
    repo: Path,
    python_executable: str,
    import_zip: str | None = None,
) -> list[CheckResult]:
    return [
        check_branch(repo),
        check_head(repo),
        check_status(repo),
        check_diff(repo),
        check_local_guard_text(repo, python_executable),
        check_local_guard_report(repo, python_executable),
        check_import_report(repo, python_executable, import_zip),
        check_docs_audit(repo, python_executable),
    ]


def print_human_report(results: list[CheckResult]) -> None:
    verdict = overall_verdict(results)
    print(f"Deployment V2 readiness verdict: {verdict}")
    for result in results:
        print(f"- {result.name}: {result.status} - {result.detail}")


def print_json_report(results: list[CheckResult]) -> None:
    print(json.dumps(readiness_json_report(results), indent=2, sort_keys=True))


def readiness_json_report(results: list[CheckResult]) -> dict[str, object]:
    by_name = {result.name: result for result in results}
    skipped = [result.name for result in results if result.status == "SKIPPED"]
    blockers = [result.detail for result in results if result.status in {"BLOCKED", "RED"}]
    violations = [
        {
            "check": result.name,
            "status": result.status,
            "detail": result.detail,
        }
        for result in results
        if status_rank(result.status) >= 2
    ]

    return {
        "verdict": overall_verdict(results),
        "branch": check_to_dict(by_name.get("branch")),
        "head": check_to_dict(by_name.get("head")),
        "clean_status": check_to_dict(by_name.get("status")),
        "diff_check": check_to_dict(by_name.get("diff_check")),
        "local_only_guard": check_to_dict(by_name.get("local_only_guard")),
        "guard_report": check_to_dict(by_name.get("local_only_guard_report")),
        "import_report": check_to_dict(by_name.get("import_report_comparison")),
        "docs_audit": check_to_dict(by_name.get("docs_consistency_audit")),
        "skipped_checks": skipped,
        "blockers": blockers,
        "violations": violations,
        "checks": [check_to_dict(result) for result in results],
    }


def check_to_dict(result: CheckResult | None) -> dict[str, str]:
    if result is None:
        return {
            "name": "",
            "status": "SKIPPED",
            "detail": "check not available",
        }
    return {
        "name": result.name,
        "status": result.status,
        "detail": result.detail,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run read-only Deployment V2 readiness checks."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Deployment V2 repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--import-zip",
        help="Optional Master import verification zip for comparison.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run local validation helpers.",
    )
    parser.add_argument(
        "--report",
        choices=["text", "json"],
        default="text",
        help="Output format for the readiness report.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Shortcut for --report json.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results = run_readiness_checks(Path(args.repo), args.python, args.import_zip)
    if args.json or args.report == "json":
        print_json_report(results)
    else:
        print_human_report(results)
    verdict = overall_verdict(results)
    if verdict == "GREEN":
        return 0
    if verdict == "YELLOW":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
