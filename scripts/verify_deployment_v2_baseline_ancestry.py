from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BaselineResult:
    verdict: str
    baseline: str
    current_head: str
    current_head_short: str
    ancestor: bool | None
    clean_required: bool
    clean_status: bool | None
    status_short: str
    reasons: list[str]


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def verify_baseline(repo: Path, baseline: str, require_clean: bool = False) -> BaselineResult:
    reasons: list[str] = []
    baseline = baseline.strip()
    if not baseline:
        return BaselineResult(
            verdict="YELLOW",
            baseline=baseline,
            current_head="",
            current_head_short="",
            ancestor=None,
            clean_required=require_clean,
            clean_status=None,
            status_short="",
            reasons=["baseline commit was not supplied"],
        )

    head = run_git(repo, "rev-parse", "HEAD")
    head_short = run_git(repo, "rev-parse", "--short", "HEAD")
    if head.returncode != 0 or head_short.returncode != 0:
        return BaselineResult(
            verdict="RED",
            baseline=baseline,
            current_head=head.stdout.strip(),
            current_head_short=head_short.stdout.strip(),
            ancestor=None,
            clean_required=require_clean,
            clean_status=None,
            status_short="",
            reasons=[(head.stderr or head_short.stderr or "could not read HEAD").strip()],
        )

    baseline_exists = run_git(repo, "cat-file", "-e", f"{baseline}^{{commit}}")
    if baseline_exists.returncode != 0:
        return BaselineResult(
            verdict="YELLOW",
            baseline=baseline,
            current_head=head.stdout.strip(),
            current_head_short=head_short.stdout.strip(),
            ancestor=None,
            clean_required=require_clean,
            clean_status=None,
            status_short="",
            reasons=[f"baseline commit not found: {baseline}"],
        )

    ancestor = run_git(repo, "merge-base", "--is-ancestor", baseline, "HEAD")
    is_ancestor = ancestor.returncode == 0
    verdict = "GREEN" if is_ancestor else "RED"
    if is_ancestor:
        reasons.append("current HEAD descends from baseline")
    else:
        reasons.append("current HEAD does not descend from baseline")

    status_short = ""
    clean_status: bool | None = None
    if require_clean:
        status = run_git(repo, "status", "--short")
        status_short = status.stdout.strip()
        clean_status = status.returncode == 0 and not status_short
        if not clean_status:
            verdict = "RED"
            reasons.append("clean status required but git status is not clean")

    return BaselineResult(
        verdict=verdict,
        baseline=baseline,
        current_head=head.stdout.strip(),
        current_head_short=head_short.stdout.strip(),
        ancestor=is_ancestor,
        clean_required=require_clean,
        clean_status=clean_status,
        status_short=status_short,
        reasons=reasons,
    )


def result_to_dict(result: BaselineResult) -> dict[str, object]:
    return {
        "verdict": result.verdict,
        "baseline": result.baseline,
        "current_head": {
            "full": result.current_head,
            "short": result.current_head_short,
        },
        "ancestor": result.ancestor,
        "clean_required": result.clean_required,
        "clean_status": result.clean_status,
        "status_short": result.status_short,
        "reasons": result.reasons,
    }


def print_result(result: BaselineResult) -> None:
    print(f"Deployment V2 baseline ancestry verdict: {result.verdict}")
    for reason in result.reasons:
        print(f"- {reason}")
    print(f"- baseline: {result.baseline}")
    print(f"- current HEAD: {result.current_head_short} ({result.current_head})")
    if result.clean_required:
        clean_text = "clean" if result.clean_status else result.status_short or "not clean"
        print(f"- clean status: {clean_text}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify current Deployment V2 HEAD descends from an expected baseline."
    )
    parser.add_argument("baseline", help="Expected baseline commit hash.")
    parser.add_argument(
        "--repo",
        default=".",
        help="Deployment V2 repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Require git status --short to be clean.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON validation output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = verify_baseline(Path(args.repo), args.baseline, args.require_clean)
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
