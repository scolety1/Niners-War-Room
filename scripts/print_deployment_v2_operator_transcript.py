from __future__ import annotations

import argparse
import json
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
    report = build_transcript_report(repo, python_executable, import_zip)
    readiness = report["readiness"]
    lines = [
        "LANE: Deployment V2",
        f"BRANCH: {readiness['branch']['status']} - {readiness['branch']['detail']}",
        f"HEAD: {readiness['head']['status']} - {readiness['head']['detail']}",
        f"STATUS: {readiness['status']['status']} - {readiness['status']['detail']}",
        f"DIFF CHECK: {readiness['diff_check']['status']} - {readiness['diff_check']['detail']}",
        (
            "LOCAL-ONLY GUARD: "
            f"{readiness['local_only_guard']['status']} - {readiness['local_only_guard']['detail']}"
        ),
        (
            "REPORT MODE: "
            f"{readiness['local_only_guard_report']['status']} - "
            f"{readiness['local_only_guard_report']['detail']}"
        ),
        f"READINESS RUNNER: {report['readiness_verdict']}",
        f"DOCS CONSISTENCY: {report['docs_consistency']['verdict']}",
        "HOSTED DEPLOYMENT: BLOCKED",
        "V1 LOCAL-ONLY: local_only",
        "DEPLOY SURFACE ADDED: no",
        "OTHER LANE TOUCHED: no",
        "REMAINING HOSTED BLOCKERS:",
    ]
    lines.extend(f"- {blocker}" for blocker in HOSTED_BLOCKERS)
    lines.append(f"FINAL VERDICT: {report['final_verdict']}")
    return "\n".join(lines) + "\n"


def build_transcript_report(
    repo: Path,
    python_executable: str,
    import_zip: str | None = None,
) -> dict[str, object]:
    readiness_results = run_readiness_checks(repo, python_executable, import_zip)
    docs_findings = audit_docs(repo / "docs" / "hq" / "parallel_lanes")
    readiness = {
        result.name: {
            "status": result.status,
            "detail": result.detail,
        }
        for result in readiness_results
    }
    final = overall_verdict(readiness_results)
    return {
        "lane": "Deployment V2",
        "readiness_verdict": final,
        "final_verdict": final,
        "branch": readiness.get("branch", {}),
        "head": readiness.get("head", {}),
        "readiness": readiness,
        "docs_consistency": {
            "verdict": docs_verdict(docs_findings),
            "findings": [
                {
                    "status": finding.status,
                    "check": finding.check,
                    "detail": finding.detail,
                }
                for finding in docs_findings
            ],
        },
        "hosted_deployment": "BLOCKED",
        "remaining_blockers": HOSTED_BLOCKERS,
        "deploy_surface_added": False,
        "other_lane_touched": False,
    }


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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON transcript.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    final_verdict = ""
    if args.json:
        report = build_transcript_report(Path(args.repo), args.python, args.import_zip)
        final_verdict = str(report.get("final_verdict", ""))
        transcript = json.dumps(report, indent=2, sort_keys=True) + "\n"
    else:
        transcript = build_transcript(Path(args.repo), args.python, args.import_zip)
        final_verdict = "GREEN" if "FINAL VERDICT: GREEN" in transcript else ""
    if args.output:
        Path(args.output).write_text(transcript, encoding="utf-8")
    else:
        print(transcript, end="")
    return 0 if final_verdict == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
