#!/usr/bin/env python3
"""Validate the terminal NWR Golden Release packet and state."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.navigation import ALL_NAVIGATION_PAGES  # noqa: E402

PACKET = Path("docs/hq/master/nwr_golden_release_acceptance_v1_20260801")
GOLDEN = Path("docs/hq/master/nwr_golden_lane_v1_20260731")


def canonical(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def write_manifest(packet: Path) -> None:
    files = {}
    for path in sorted(packet.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json":
            name = path.relative_to(packet).as_posix()
            body = canonical(path)
            files[name] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    value = {
        "files": files,
        "hash_representation": "UTF8_LF_CANONICAL_BYTES",
        "manifest_excludes_self": True,
        "packet": PACKET.as_posix(),
        "required_file_count": len(files) + 1,
        "schema_version": "NWR_GOLDEN_RELEASE_ACCEPTANCE_MANIFEST_V1",
    }
    (packet / "MANIFEST.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def validate(root: Path) -> dict[str, object]:
    packet = root / PACKET
    golden = root / GOLDEN
    routes = ALL_NAVIGATION_PAGES
    if len(routes) != 61 or len({route.url_path for route in routes}) != 61:
        raise AssertionError("dynamic registered-route inventory changed")
    with (packet / "VIEWPORT_ACCEPTANCE.csv").open(encoding="utf-8", newline="") as handle:
        viewports = list(csv.DictReader(handle))
    if len(viewports) != 3 or sum(int(row["completed_checks"]) for row in viewports) != 183:
        raise AssertionError("viewport matrix is incomplete")
    failure_fields = (
        "page_not_found",
        "visible_traceback",
        "uncaught_exception",
        "root_overflow",
        "console_errors",
    )
    if any(int(row[field]) for row in viewports for field in failure_fields):
        raise AssertionError("viewport matrix contains a release failure")
    screenshots = tuple((packet / "screenshots").glob("*.png"))
    if len(screenshots) != 9 or any(path.stat().st_size < 10_000 for path in screenshots):
        raise AssertionError("screenshot atlas is incomplete")
    status = json.loads((golden / "GOLDEN_LANE_STATUS.json").read_text(encoding="utf-8"))
    state = json.loads((golden / "GOLDEN_LANE_AUTOPILOT_STATE.json").read_text(encoding="utf-8"))
    if (
        status["active_phase"] != "GOLDEN_RELEASE_COMPLETE"
        or status["next_authorized_lane"] != "NONE"
    ):
        raise AssertionError("Golden Release terminal status is not set")
    if status["phase_gates_passed"] != 10 or status["final_completion_percentage"] != 100:
        raise AssertionError("Golden Release arithmetic changed")
    if state["dispatch_status"] != "COMPLETE" or state["next_phase"] != "NONE":
        raise AssertionError("Autopilot terminal state is not set")
    prompt = (golden / "NEXT_AUTHORIZED_LANE_PROMPT.md").read_text(encoding="utf-8")
    if prompt.strip() != "NO_FURTHER_NWR_LANE_AUTHORIZED_GOLDEN_RELEASE_COMPLETE":
        raise AssertionError("terminal prompt changed")
    manifest = json.loads((packet / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, receipt in manifest["files"].items():
        body = canonical(packet / name)
        if receipt != {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}:
            raise AssertionError(f"manifest mismatch: {name}")
    return {"registered_routes": 61, "route_viewports": 183, "screenshots": 9, "valid": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.write_manifest:
        write_manifest(root / PACKET)
        print('{"manifest_written":true}')
    else:
        print(json.dumps(validate(root), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
