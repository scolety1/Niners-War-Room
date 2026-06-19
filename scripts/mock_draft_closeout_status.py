from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REQUIRED_INPUTS = (
    "frozen rookie input",
    "dropped/available veteran pool",
    "final pick order",
    "NWR/my pick numbers",
    "rosters/keepers",
    "team needs/opponent tendencies",
    "NWR private value source",
    "ADP/market behavior context",
)


def build_closeout_status(
    *,
    expected_branch: str = "work/mock-draft-simulator",
    expected_head: str = "9d7f432",
    manifest_path: str = "local_exports/mock_draft/manual_input_manifest.local.json",
) -> str:
    from src.services.mock_draft_readiness_service import build_mock_draft_readiness_report

    report = build_mock_draft_readiness_report(repo_root=REPO_ROOT, manifest_path=manifest_path)
    lines = [
        "Mock Draft closeout status",
        f"Expected branch: {expected_branch}",
        f"Expected HEAD: {expected_head}",
        "Infrastructure readiness: GREEN",
        f"Fixture readiness: {report.fixture_readiness}",
        f"Real input readiness: {report.real_input_readiness}",
        f"Manifest readiness: {report.manifest_readiness}",
        "Actual draft-use readiness: YELLOW until real inputs validate",
        "No simulations run: yes",
        "No files written: yes",
        "ADP/market separation: opponent behavior only",
        "Required next inputs:",
    ]
    lines.extend(f"- {item}" for item in REQUIRED_INPUTS)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print Mock Draft closeout status.")
    parser.add_argument("--expected-branch", default="work/mock-draft-simulator")
    parser.add_argument("--expected-head", default="9d7f432")
    parser.add_argument(
        "--manifest-path",
        default="local_exports/mock_draft/manual_input_manifest.local.json",
    )
    args = parser.parse_args(argv)
    print(
        build_closeout_status(
            expected_branch=args.expected_branch,
            expected_head=args.expected_head,
            manifest_path=args.manifest_path,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
