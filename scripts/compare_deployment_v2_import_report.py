from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile

DEPLOYMENT_REPORT_NAME = "05_DEPLOYMENT_V2.md"


@dataclass(frozen=True)
class ImportReport:
    repo_path: str
    expected_branch: str
    current_branch: str
    head_full: str
    head_short: str
    commit_subject: str
    dirty_files_exist: str
    untracked_files_exist: str
    diff_check_passed: str
    verdict: str


@dataclass(frozen=True)
class CurrentState:
    repo_path: Path
    branch: str
    head_full: str
    head_short: str
    commit_subject: str
    status_short: str
    diff_check_output: str
    report_head_is_ancestor: bool | None


@dataclass(frozen=True)
class ComparisonResult:
    verdict: str
    messages: list[str]
    report: ImportReport | None
    current: CurrentState | None


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def current_state(repo: Path, report_head_full: str | None = None) -> CurrentState:
    branch = run_git(repo, "branch", "--show-current")
    head_full = run_git(repo, "rev-parse", "HEAD")
    head_short = run_git(repo, "rev-parse", "--short", "HEAD")
    subject = run_git(repo, "log", "-1", "--pretty=%s")
    status = run_git(repo, "status", "--short")
    diff_check = run_git(repo, "diff", "--check")

    report_head_is_ancestor: bool | None = None
    if report_head_full:
        ancestor = run_git(repo, "merge-base", "--is-ancestor", report_head_full, "HEAD")
        report_head_is_ancestor = ancestor.returncode == 0

    return CurrentState(
        repo_path=repo.resolve(),
        branch=branch.stdout.strip(),
        head_full=head_full.stdout.strip(),
        head_short=head_short.stdout.strip(),
        commit_subject=subject.stdout.strip(),
        status_short=status.stdout.strip(),
        diff_check_output=diff_check.stdout.strip(),
        report_head_is_ancestor=report_head_is_ancestor,
    )


def read_deployment_report(zip_path: Path) -> tuple[ImportReport | None, str | None]:
    if not zip_path.exists():
        return None, f"zip file missing: {zip_path}"

    try:
        with ZipFile(zip_path) as zip_file:
            if DEPLOYMENT_REPORT_NAME not in zip_file.namelist():
                return None, f"missing {DEPLOYMENT_REPORT_NAME}"
            text = zip_file.read(DEPLOYMENT_REPORT_NAME).decode("utf-8-sig", errors="replace")
    except BadZipFile:
        return None, f"invalid zip file: {zip_path}"

    fields = parse_report_fields(text)
    required = {
        "Repo path",
        "Expected branch",
        "Current branch",
        "HEAD full",
        "HEAD short",
        "Commit subject",
        "Dirty files exist",
        "Untracked files exist",
        "Diff check passed",
        "Verdict",
    }
    missing = sorted(required - set(fields))
    if missing:
        return None, f"incomplete {DEPLOYMENT_REPORT_NAME}: missing {', '.join(missing)}"

    return (
        ImportReport(
            repo_path=fields["Repo path"],
            expected_branch=fields["Expected branch"],
            current_branch=fields["Current branch"],
            head_full=fields["HEAD full"],
            head_short=fields["HEAD short"],
            commit_subject=fields["Commit subject"],
            dirty_files_exist=fields["Dirty files exist"],
            untracked_files_exist=fields["Untracked files exist"],
            diff_check_passed=fields["Diff check passed"],
            verdict=fields["Verdict"],
        ),
        None,
    )


def parse_report_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def compare(
    report: ImportReport | None,
    current: CurrentState | None,
    error: str | None,
) -> ComparisonResult:
    messages: list[str] = []
    verdict = "GREEN"

    if error:
        return ComparisonResult("YELLOW", [error], report, current)
    if report is None or current is None:
        return ComparisonResult("YELLOW", ["report or current state unavailable"], report, current)

    if report.verdict != "GREEN":
        verdict = "YELLOW"
        messages.append(f"import report verdict is {report.verdict}")

    expected_branch = report.expected_branch or report.current_branch
    if current.branch != expected_branch:
        verdict = "RED"
        messages.append(f"branch mismatch: current {current.branch}, expected {expected_branch}")

    if current.status_short:
        verdict = "RED"
        messages.append("current git status is not clean")

    if current.diff_check_output:
        verdict = "RED"
        messages.append("current git diff --check produced output")

    if report.diff_check_passed != "True":
        verdict = "YELLOW" if verdict == "GREEN" else verdict
        messages.append("import report diff check was not clean")

    if report.dirty_files_exist != "False" or report.untracked_files_exist != "False":
        verdict = "YELLOW" if verdict == "GREEN" else verdict
        messages.append("import report recorded dirty or untracked files")

    if current.head_full == report.head_full:
        messages.append("current HEAD matches import report")
    elif current.report_head_is_ancestor:
        messages.append("current HEAD is a clean descendant of import report HEAD")
    else:
        verdict = "RED"
        messages.append("current HEAD does not match or descend from import report HEAD")

    if not messages:
        messages.append("current lane state matches import report")

    return ComparisonResult(verdict, messages, report, current)


def print_result(result: ComparisonResult) -> None:
    print(f"Deployment V2 import report comparison verdict: {result.verdict}")
    for message in result.messages:
        print(f"- {message}")
    if result.report is not None:
        print(f"- report HEAD: {result.report.head_short} {result.report.commit_subject}")
    if result.current is not None:
        print(f"- current HEAD: {result.current.head_short} {result.current.commit_subject}")


def result_to_dict(result: ComparisonResult) -> dict[str, object]:
    return {
        "verdict": result.verdict,
        "reasons": result.messages,
        "report_head": None
        if result.report is None
        else {
            "full": result.report.head_full,
            "short": result.report.head_short,
            "subject": result.report.commit_subject,
            "verdict": result.report.verdict,
        },
        "current_head": None
        if result.current is None
        else {
            "full": result.current.head_full,
            "short": result.current.head_short,
            "subject": result.current.commit_subject,
        },
        "ancestor_or_match": None
        if result.current is None
        else (
            result.report is not None
            and (
                result.current.head_full == result.report.head_full
                or bool(result.current.report_head_is_ancestor)
            )
        ),
        "clean_status": None
        if result.current is None
        else {
            "clean": not bool(result.current.status_short),
            "status_short": result.current.status_short,
        },
        "diff_check": None
        if result.current is None
        else {
            "clean": not bool(result.current.diff_check_output),
            "output": result.current.diff_check_output,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare current Deployment V2 branch state to a Master import zip report."
    )
    parser.add_argument("zip_path", help="Path to a Master import verification zip bundle.")
    parser.add_argument(
        "--repo",
        default=".",
        help="Deployment V2 repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON comparison output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo = Path(args.repo)
    report, error = read_deployment_report(Path(args.zip_path))
    current = current_state(repo, report.head_full if report is not None else None)
    result = compare(report, current, error)
    if args.json:
        print(json.dumps(result_to_dict(result), indent=2, sort_keys=True))
    else:
        print_result(result)
    if result.verdict == "GREEN":
        return 0
    if result.verdict == "YELLOW":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
