#!/usr/bin/env python3
"""Validate the contracted Phase 7 product-completion result."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.navigation import VISIBLE_NAVIGATION_PAGES  # noqa: E402
from src.services.governed_asset_registry_service import (  # noqa: E402
    load_governed_asset_registry,
)

PACKET_RELATIVE = Path("docs/hq/master/nwr_product_completion_v1_20260801")
GOLDEN_RELATIVE = Path("docs/hq/master/nwr_golden_lane_v1_20260731")
EXPECTED_COUNTS = {
    "Current Player": 240,
    "Rookie Review": 73,
    "Blocked Rookie": 7,
    "Draft Pick": 50,
}


def canonical_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_manifest(packet: Path) -> None:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(packet.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "MANIFEST.json":
            body = canonical_bytes(path)
            files[path.name] = {"bytes": len(body), "sha256": sha256_bytes(body)}
    manifest = {
        "files": files,
        "hash_representation": "UTF8_LF_CANONICAL_BYTES",
        "manifest_excludes_self": True,
        "packet": PACKET_RELATIVE.as_posix(),
        "required_file_count": len(files) + 1,
        "schema_version": "NWR_PHASE_7_PRODUCT_COMPLETION_MANIFEST_V1",
    }
    (packet / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate(repo_root: Path, current_board_path: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    packet = root / PACKET_RELATIVE
    golden = root / GOLDEN_RELATIVE
    registry = load_governed_asset_registry(
        repo_root=root,
        current_board_path=current_board_path.resolve(),
    )
    if registry.errors:
        raise AssertionError("; ".join(registry.errors))
    if registry.counts != EXPECTED_COUNTS or len(registry.rows) != 370:
        raise AssertionError("governed asset universe changed")
    if len({row["asset_id"] for row in registry.rows}) != 370:
        raise AssertionError("governed asset identity is not exact")
    if any("recommendation" in row for row in registry.rows):
        raise AssertionError("registry introduced recommendation output")

    authorities = {row["asset_type"]: row for row in read_csv(packet / "AUTHORITY_CONTRACT.csv")}
    if set(authorities) != set(EXPECTED_COUNTS):
        raise AssertionError("authority contract universe changed")
    if any(row["recommendation_behavior"] != "NONE" for row in authorities.values()):
        raise AssertionError("authority contract introduced recommendation behavior")

    routes = {f"/{spec.url_path}" for spec in VISIBLE_NAVIGATION_PAGES}
    if not {"/asset-explorer", "/rookie-board"}.issubset(routes):
        raise AssertionError("Phase 7 routes are not visible")
    explorer = (root / "app/pages/47_asset_explorer_v1.py").read_text(encoding="utf-8")
    rookie = (root / "app/pages/48_rookie_board_review_v1.py").read_text(encoding="utf-8")
    prohibited = ("accept trade", "reject trade", "winner", "loser", "automatic counteroffer")
    if any(term in (explorer + rookie).casefold() for term in prohibited):
        raise AssertionError("new pages introduced prohibited recommendation copy")

    status = json.loads((golden / "GOLDEN_LANE_STATUS.json").read_text(encoding="utf-8"))
    if status["active_phase"] != "PHASE_8_GOLDEN_RELEASE_ACCEPTANCE":
        raise AssertionError("Phase 8 is not the active next phase")
    if status["phase_gates_passed"] != 9 or status["final_completion_percentage"] != 90:
        raise AssertionError("Phase 7 gate arithmetic changed")
    if status["owner_decisions_required"] != 0 or status["hard_stop_ids"]:
        raise AssertionError("unexpected owner decision or hard stop")

    manifest = json.loads((packet / "MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["required_file_count"] != len(manifest["files"]) + 1:
        raise AssertionError("manifest count mismatch")
    for name, receipt in manifest["files"].items():
        body = canonical_bytes(packet / name)
        if receipt != {"bytes": len(body), "sha256": sha256_bytes(body)}:
            raise AssertionError(f"manifest mismatch: {name}")

    return {
        "asset_counts": registry.counts,
        "next_phase": status["active_phase"],
        "production_changes": 0,
        "recommendations_created": 0,
        "schema_version": "NWR_PHASE_7_PRODUCT_COMPLETION_VALIDATION_V1",
        "valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--current-board-path", type=Path)
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.write_manifest:
        write_manifest(root / PACKET_RELATIVE)
        print('{"manifest_written":true}')
        return 0
    if args.current_board_path is None:
        parser.error("--current-board-path is required for fail-closed validation")
    print(
        json.dumps(
            validate(root, args.current_board_path),
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
