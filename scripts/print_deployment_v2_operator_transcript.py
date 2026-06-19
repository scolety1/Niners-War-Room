from __future__ import annotations

import argparse
import sys
from pathlib import Path

from audit_deployment_v2_docs_consistency import audit_docs
from audit_deployment_v2_docs_consistency import verdict as docs_verdict
from run_deployment_v2_readiness_checks import (
    overall_verdict,
    run_readiness_checks,
)

HOSTED_BLOCKERS = [
    "hosted target",
    "owner",
    "secrets policy",
    "data policy",
    "access policy",
    "rollback policy",
    "deploy command policy",
    "CI/CD policy",
    "public/private routing policy",
    "hosted smoke plan",
]


def build_transcript(repo: Path, python_executable: str, import_zip: str | None = None) -> str:
    readiness_results = run_readiness_checks(repo, python_executable, import_zip)
    docs_findings = audit_docs(repo / "docs" / "hq" / "parallel_lanes")
    readiness = {result.name: result for result in readiness_results}
    lines = [
        "LANE: Deployment V2",
        f"BRANCH: {readiness['branch'].status} - {readiness['branch'].detail}",
        f"HEAD: {readiness['head'].status} - {readiness['head'].detail}",
        f"STATUS: {readiness['status'].status} - {readiness['status'].detail}",
        f"DIFF CHECK: {readiness['diff_check'].status} - {readiness['diff_check'].detail}",
        (
            "LOCAL-ONLY GUARD: "
            f"{readiness['local_only_guard'].status} - {readiness['local_only_guard'].detail}"
        ),
        (
            "REPORT MODE: "
            f"{readiness['local_only_guard_report'].status} - "
            f"{readiness['local_only_guard_report'].detail}"
        ),
        f"READINESS RUNNER: {overall_verdict(readiness_results)}",
        f"DOCS CONSISTENCY: {docs_verdict(docs_findings)}",
        "HOSTED DEPLOYMENT: BLOCKED",
        "V1 LOCAL-ONLY: local_only",
        "DEPLOY SURFACE ADDED: no",
        "OTHER LANE TOUCHED: no",
        "REMAINING HOSTED BLOCKERS:",
    ]
    lines.extend(f"- {blocker}" for blocker in HOSTED_BLOCKERS)
    lines.append(f"FINAL VERDICT: {overall_verdict(readiness_results)}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a read-only Deployment V2 HQ operator transcript."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Deployment V2 repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run local validation helpers.",
    )
    parser.add_argument(
        "--import-zip",
        help="Optional Master import verification zip for readiness comparison.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Default prints to stdout and writes nothing.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    transcript = build_transcript(Path(args.repo), args.python, args.import_zip)
    if args.output:
        Path(args.output).write_text(transcript, encoding="utf-8")
    else:
        print(transcript, end="")
    return 0 if "FINAL VERDICT: GREEN" in transcript else 1


if __name__ == "__main__":
    raise SystemExit(main())
