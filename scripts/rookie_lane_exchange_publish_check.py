from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from src.services.rookie_lane_exchange import (
    DEFAULT_EXCHANGE_ROOT,
    publish_rookie_exchange_snapshot,
)


def _git_value(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish a Rookie-owned Lane Exchange candidate snapshot."
    )
    parser.add_argument("data_file", help="CSV or JSON snapshot file to publish.")
    parser.add_argument(
        "--package-name",
        default="rookie_hq/frozen_rookie_mock_input",
        help="Owned exchange package. Non-Rookie packages are refused.",
    )
    parser.add_argument("--exchange-root", default=str(DEFAULT_EXCHANGE_ROOT))
    parser.add_argument("--schema-version", default="rookie_frozen_mock_input_v1")
    parser.add_argument("--snapshot-label")
    parser.add_argument("--source-repo", default=r"C:\NWR\Niners-War-Room-rookies")
    parser.add_argument("--source-branch")
    parser.add_argument("--source-head")
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Also write latest_approved.json. Omit for candidate-only publishing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.source_repo)
    source_branch = args.source_branch or _git_value(repo, "branch", "--show-current")
    source_head = args.source_head or _git_value(repo, "rev-parse", "HEAD")

    result = publish_rookie_exchange_snapshot(
        data_file=args.data_file,
        package_name=args.package_name,
        exchange_root=args.exchange_root,
        schema_version=args.schema_version,
        snapshot_label=args.snapshot_label,
        approve=args.approve,
        source_branch=source_branch,
        source_head=source_head,
        source_repo=str(repo),
        notes=args.notes,
    )
    print(
        json.dumps(
            {
                "snapshot_dir": str(result.snapshot_dir),
                "manifest_path": str(result.manifest_path),
                "latest_candidate": str(result.pointer_path),
                "latest_approved": (
                    str(result.approved_pointer_path) if result.approved_pointer_path else None
                ),
                "approval_status": result.manifest["approval_status"],
                "row_count": result.manifest["row_count"],
                "sha256": result.manifest["sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
