from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.trading_lab.trading_lab_lane_exchange import (
    DEFAULT_HUB_ROOT,
    DEFAULT_REGISTRY_PATH,
    LANE_ID,
    LATEST_APPROVED,
    LaneExchangeError,
    load_registry,
    trading_lab_role,
    validate_latest_approved_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check Trading Lab local lane exchange readiness."
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--hub-root", type=Path, default=DEFAULT_HUB_ROOT)
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        help="Package id to validate, for example source_lane/package_name.",
    )
    parser.add_argument("--allowed-use", default=None)
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    return parser


def readiness_report(
    *,
    registry_path: Path,
    hub_root: Path,
    package_ids: list[str],
    allowed_use: str | None,
) -> dict[str, object]:
    registry = load_registry(registry_path)
    role = trading_lab_role(registry)
    validations: list[dict[str, object]] = []

    for package_id in package_ids:
        source_lane, package_name = _split_package_id(package_id)
        result = validate_latest_approved_manifest(
            hub_root=hub_root,
            source_lane=source_lane,
            package_name=package_name,
            allowed_use=allowed_use,
            pointer_name=LATEST_APPROVED,
        )
        validations.append(
            {
                "package_name": result.package_name,
                "manifest_path": str(result.manifest_path),
                "row_count": result.row_count,
                "approval_status": result.approval_status,
                "allowed_use": list(result.allowed_use),
            }
        )

    return {
        "lane": LANE_ID,
        "owned_packages": list(role.owned_packages),
        "consumed_packages": list(role.consumed_packages),
        "requires_explicit_publish_approval": role.requires_explicit_publish_approval,
        "validations": validations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = readiness_report(
            registry_path=args.registry,
            hub_root=args.hub_root,
            package_ids=args.package,
            allowed_use=args.allowed_use,
        )
    except LaneExchangeError as exc:
        if args.json:
            print(json.dumps({"status": "RED", "error": str(exc)}, indent=2))
        else:
            print(f"RED: {exc}")
        return 1

    if args.json:
        print(json.dumps({"status": "GREEN", **report}, indent=2))
    else:
        print("GREEN: Trading Lab lane exchange readiness check passed.")
        print(f"Owned packages: {', '.join(report['owned_packages']) or 'none'}")
        print(f"Consumed packages: {', '.join(report['consumed_packages']) or 'none'}")
        print(
            "Explicit publish approval required: "
            f"{report['requires_explicit_publish_approval']}"
        )
        print(f"Approved package validations: {len(report['validations'])}")
    return 0


def _split_package_id(package_id: str) -> tuple[str, str]:
    parts = package_id.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise LaneExchangeError(f"Invalid package id: {package_id}")
    return parts[0], parts[1]


if __name__ == "__main__":
    raise SystemExit(main())
