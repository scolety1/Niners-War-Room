from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main(argv: list[str] | None = None) -> int:
    from src.services.mock_draft_input_contract import READINESS_RED
    from src.services.mock_draft_lane_exchange_validator import (
        DEFAULT_EXCHANGE_HUB,
        DEFAULT_REGISTRY_PATH,
        validate_lane_exchange_readiness,
    )

    parser = argparse.ArgumentParser(
        description="Read-only Mock Draft Lane Exchange V0 readiness check.",
        epilog=(
            "Validates latest_approved manifests only. No data is copied, no "
            "manifest is created, and no simulation is run."
        ),
    )
    parser.add_argument("--hub-root", default=str(DEFAULT_EXCHANGE_HUB))
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH))
    args = parser.parse_args(argv)

    report = validate_lane_exchange_readiness(
        hub_root=args.hub_root,
        registry_path=args.registry_path,
    )

    print("Mock Draft Lane Exchange V0 readiness: READ ONLY")
    print("No simulations run. No files are written.")
    print("latest_approved.json only; latest_candidate is never accepted.")
    print(report.market_policy)
    print(f"Overall readiness: {report.readiness}")
    print(f"Registry readiness: {report.registry_readiness}")
    print(f"Hub root: {report.hub_root}")
    print(f"Registry: {report.registry_path}")
    if report.errors:
        print("Registry errors:")
        for error in report.errors:
            print(f"- {error}")
    if report.warnings:
        print("Registry warnings:")
        for warning in report.warnings:
            print(f"- {warning}")
    print("Packages:")
    for package in report.package_reports:
        requirement = "required" if package.required else "optional"
        print(f"- {package.readiness}: {package.package_name} ({requirement})")
        if package.manifest_path:
            print(f"  manifest: {package.manifest_path}")
        if package.data_file_path:
            print(f"  data_file: {package.data_file_path}")
        if package.row_count_expected is not None or package.row_count_actual is not None:
            print(
                "  row_count: "
                f"expected={package.row_count_expected} actual={package.row_count_actual}"
            )
        for error in package.errors:
            print(f"  error: {error}")
        for warning in package.warnings:
            print(f"  warning: {warning}")
    return 1 if report.readiness == READINESS_RED else 0


if __name__ == "__main__":
    raise SystemExit(main())
