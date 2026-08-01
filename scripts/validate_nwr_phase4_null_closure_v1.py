#!/usr/bin/env python3
"""Validate the Phase 4 truthful-null formula closure and optional-lane dispositions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

PACKET_RELATIVE = Path("docs/hq/master/nwr_formula_decision_null_closure_v1_20260801")
PHASE3_RELATIVE = Path("docs/hq/master/nwr_open_role_availability_lifecycle_gauntlet_v1_20260801")
GOLDEN_RELATIVE = Path("docs/hq/master/nwr_golden_lane_v1_20260731")
FAMILIES = {
    "PRODUCTION_PERSISTENCE_2Y",
    "ROLE_OPPORTUNITY_VOLUME",
    "ROLE_TRAJECTORY_DELTA",
    "RB_HIGH_LEVERAGE_RUSHING",
    "QB_RUSHING_OPPORTUNITY",
}


def canonical_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
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
        "schema_version": "NWR_PHASE_4_NULL_CLOSURE_MANIFEST_V1",
    }
    (packet / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    packet = root / PACKET_RELATIVE
    phase3 = root / PHASE3_RELATIVE
    golden = root / GOLDEN_RELATIVE

    summary = json.loads((phase3 / "GAUNTLET_SUMMARY.json").read_text(encoding="utf-8"))
    if summary["overall_verdict"] != "NULL_NO_FAMILY_PASSED":
        raise AssertionError("Phase 3 is not a truthful null")
    if summary["families_passed"] or summary["production_changes"] != 0:
        raise AssertionError("Phase 3 unexpectedly promoted a family or changed production")

    phase3_decisions = read_csv(phase3 / "FAMILY_DECISIONS.csv")
    if {row["family_id"] for row in phase3_decisions} != FAMILIES:
        raise AssertionError("Phase 3 family universe changed")
    if any(row["decision"] != "NULL_NOT_PROMOTED" for row in phase3_decisions):
        raise AssertionError("a Phase 3 family is not closed")

    formula = read_csv(packet / "FORMULA_DECISION.csv")
    if len(formula) != 1 or formula[0] != {
        "decision_id": "PHASE4_NULL_001",
        "phase3_verdict": "NULL_NO_FAMILY_PASSED",
        "passing_families": "0",
        "decision": "CLOSE_FORMULA_RESEARCH_RETAIN_EXISTING_AUTHORITIES",
        "retained_authority": "Finished V1",
        "production_change": "NONE",
        "owner_decision_required": "NO",
    }:
        raise AssertionError("formula decision contract changed")

    dispositions = read_csv(packet / "FEATURE_FAMILY_DISPOSITION.csv")
    if {row["family_id"] for row in dispositions} != FAMILIES:
        raise AssertionError("Phase 4 family disposition universe changed")
    if any(
        row["phase3_decision"] != "NULL_NOT_PROMOTED"
        or row["formula_use"] != "NOT_AUTHORIZED"
        or row["ranking_use"] != "NOT_AUTHORIZED"
        for row in dispositions
    ):
        raise AssertionError("Phase 4 promoted a closed family")

    optional = {row["phase"]: row for row in read_csv(packet / "OPTIONAL_LANE_DISPOSITION.csv")}
    if optional["PHASE_5"]["disposition"] != "NOT_REQUIRED_NO_PROVEN_GAP":
        raise AssertionError("Phase 5 disposition changed")
    if optional["PHASE_6"]["disposition"] != "NOT_REQUIRED_NO_ADMITTED_MARKET_AUTHORITY":
        raise AssertionError("Phase 6 disposition changed")
    if any(
        row["work_executed"] != "NO" or row["owner_decision_required"] != "NO"
        for row in optional.values()
    ):
        raise AssertionError("optional lane was executed or requires an owner decision")

    status = json.loads((golden / "GOLDEN_LANE_STATUS.json").read_text(encoding="utf-8"))
    if status["active_phase"] != "PHASE_7_PRODUCT_COMPLETION_CONTRACTED_ONLY":
        raise AssertionError("Phase 7 is not the active next phase")
    if status["phase_gates_passed"] != 8 or status["final_completion_percentage"] != 80:
        raise AssertionError("Phase 4-to-6 gate arithmetic changed")
    if status["owner_decisions_required"] != 0 or status["hard_stop_ids"]:
        raise AssertionError("unexpected owner decision or hard stop")

    gates = {row["gate"]: row for row in read_csv(golden / "PHASE_GATE_MATRIX.csv")}
    if any(gates[phase]["status"] != "PASS" for phase in ("PHASE_4", "PHASE_5", "PHASE_6")):
        raise AssertionError("Phase 4-to-6 dispositions are not passed")
    if gates["PHASE_7"]["status"] != "ACTIVE":
        raise AssertionError("Phase 7 gate is not active")

    manifest = json.loads((packet / "MANIFEST.json").read_text(encoding="utf-8"))
    if manifest["required_file_count"] != len(manifest["files"]) + 1:
        raise AssertionError("manifest count mismatch")
    for name, receipt in manifest["files"].items():
        body = canonical_bytes(packet / name)
        if receipt != {"bytes": len(body), "sha256": sha256_bytes(body)}:
            raise AssertionError(f"manifest mismatch: {name}")

    return {
        "families_closed": len(dispositions),
        "next_phase": status["active_phase"],
        "optional_lanes_not_required": len(optional),
        "production_changes": 0,
        "schema_version": "NWR_PHASE_4_NULL_CLOSURE_VALIDATION_V1",
        "valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    if args.write_manifest:
        write_manifest(args.repo_root.resolve() / PACKET_RELATIVE)
        print('{"manifest_written":true}')
        return 0
    print(json.dumps(validate(args.repo_root), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
