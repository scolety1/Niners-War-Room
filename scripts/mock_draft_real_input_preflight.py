from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_MANIFEST_PATH = Path("local_exports/mock_draft/manual_input_manifest.local.json")


def main(argv: list[str] | None = None) -> int:
    from src.services.mock_draft_input_contract import READINESS_RED
    from src.services.mock_draft_input_manifest import validate_input_manifest
    from src.services.mock_draft_manifest_bootstrap import build_manifest_skeleton

    parser = argparse.ArgumentParser(description="Read-only Mock Draft real input preflight.")
    parser.add_argument("manifest_path", nargs="?", default=str(DEFAULT_MANIFEST_PATH))
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest_path)
    print("Mock Draft real input preflight: REVIEW ONLY")
    print("No simulations run. No files are written.")
    print("ADP/market is opponent behavior, availability, and pick timing only.")
    print(f"Manifest path: {manifest_path}")

    if not (REPO_ROOT / manifest_path).exists() and not manifest_path.is_absolute():
        build_manifest_skeleton(destination=manifest_path)
        print("Overall readiness: YELLOW")
        print(f"Manifest missing: {manifest_path}")
        print("Expected local-only path: local_exports/mock_draft/manual_input_manifest.local.json")
        print(
            "Required roles: rookie_input, veteran_pool, pick_order, my_picks, "
            "rosters_keepers, team_needs, nwr_private_values, market_context"
        )
        return 0

    report = validate_input_manifest(manifest_path, repo_root=REPO_ROOT)
    print(f"Overall readiness: {report.readiness}")
    for warning in report.warnings:
        print(f"YELLOW: {warning}")
    for error in report.errors:
        print(f"RED: {error}")
    if report.input_report is not None:
        for row in report.input_report.rows:
            print(f"{row.readiness}: {row.label} rows={row.row_count}")
    return 1 if report.readiness == READINESS_RED else 0


if __name__ == "__main__":
    raise SystemExit(main())
