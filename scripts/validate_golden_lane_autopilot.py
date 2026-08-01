#!/usr/bin/env python3
"""Fail-closed validation for the canonical Golden Lane autopilot packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

PACKET_RELATIVE = Path("docs/hq/master/nwr_golden_lane_v1_20260731")
REQUIRED_FILES = {
    "GOLDEN_LANE_AUTOPILOT_POLICY.md",
    "GOLDEN_LANE_AUTOPILOT_RUNBOOK.md",
    "GOLDEN_LANE_AUTOPILOT_RESUME_PROMPT.md",
    "GOLDEN_LANE_AUTOPILOT_STATE.json",
    "GOLDEN_LANE_HARD_STOP_REGISTRY.csv",
    "GOLDEN_LANE_STATUS.json",
    "PHASE_GATE_MATRIX.csv",
    "NEXT_AUTHORIZED_LANE.md",
    "NEXT_AUTHORIZED_LANE_PROMPT.md",
    "NWR_GOLDEN_LANE_MASTER_PLAN.md",
    "MANIFEST.json",
}
ALLOWLIST = {
    "PHASE_1B_CANONICAL_BASELINE_HEALTH",
    "PHASE_2_NWR_OUTCOME_AND_BASELINE_CONTRACT",
    "PHASE_3_OPEN_ROLE_AVAILABILITY_AND_LIFECYCLE_GAUNTLET",
    "PHASE_4_FORMULA_DECISION_NULL_OR_RECORD_ONLY",
    "PHASE_7_PRODUCT_COMPLETION_CONTRACTED_ONLY",
    "PHASE_8_GOLDEN_RELEASE_ACCEPTANCE",
}


def canonical_bytes(path: Path) -> bytes:
    """Return repository-canonical bytes, stable across CRLF checkout policy."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(packet: Path) -> list[str]:
    errors: list[str] = []
    missing = sorted(name for name in REQUIRED_FILES if not (packet / name).is_file())
    if missing:
        return [f"missing required file: {name}" for name in missing]

    try:
        state = read_json(packet / "GOLDEN_LANE_AUTOPILOT_STATE.json")
        status = read_json(packet / "GOLDEN_LANE_STATUS.json")
        manifest = read_json(packet / "MANIFEST.json")
        gates = read_csv(packet / "PHASE_GATE_MATRIX.csv")
        hard_stops = read_csv(packet / "GOLDEN_LANE_HARD_STOP_REGISTRY.csv")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    if state.get("schema_version") != "NWR_GOLDEN_LANE_AUTOPILOT_STATE_V1":
        errors.append("unsupported autopilot state schema")
    if state.get("mode") != "BOUNDED_CONTINUOUS_AUTOPILOT":
        errors.append("autopilot mode is not BOUNDED_CONTINUOUS_AUTOPILOT")
    if status.get("schema_version") != "NWR_GOLDEN_LANE_STATUS_V2":
        errors.append("Golden Lane status is not schema V2")
    if status.get("execution_mode") != state.get("mode"):
        errors.append("status execution mode does not match autopilot state")
    if state.get("active_phase") != status.get("active_phase"):
        errors.append("active phase differs between status and autopilot state")
    if state.get("next_phase") != status.get("next_authorized_lane"):
        errors.append("next phase differs between status and autopilot state")
    if state.get("owner_decisions_required") != 0:
        errors.append("autopilot state has owner decisions required")
    if status.get("owner_decisions_required") != 0:
        errors.append("Golden Lane status has owner decisions required")
    if state.get("open_fail_closed_controls") != status.get("open_fail_closed_controls"):
        errors.append("open fail-closed controls differ between status and state")
    if set(state.get("automatic_execution_allowlist", [])) != ALLOWLIST:
        errors.append("automatic execution allowlist differs from canonical policy")
    terminal = state.get("next_phase") == "NONE"
    if not terminal and state.get("next_phase") not in ALLOWLIST:
        errors.append("next phase is not automatically allowlisted")
    if terminal and (
        state.get("active_phase") != "GOLDEN_RELEASE_COMPLETE"
        or status.get("active_phase") != "GOLDEN_RELEASE_COMPLETE"
    ):
        errors.append("terminal lane requires GOLDEN_RELEASE_COMPLETE")
    if state.get("maximum_correction_cycles_per_phase") != 1:
        errors.append("bounded correction limit must equal one")
    if state.get("correction_cycles_used", 0) > 1:
        errors.append("bounded correction limit exceeded")
    for flag in (
        "operational_checkout_update_allowed",
        "scheduled_refresh_change_allowed",
        "force_push_allowed",
    ):
        if state.get(flag) is not False:
            errors.append(f"{flag} must be false")

    active_stops = sorted(
        row.get("stop_id", "") for row in hard_stops if row.get("active", "").upper() == "YES"
    )
    if active_stops != sorted(state.get("hard_stop_ids", [])):
        errors.append("hard-stop registry and autopilot state differ")
    if active_stops and state.get("dispatch_status") != "HARD_STOP":
        errors.append("active hard stop requires HARD_STOP dispatch status")
    if not active_stops and not terminal and state.get("dispatch_status") != "READY":
        errors.append("dispatch status must be READY when no hard stop is active")
    if terminal and state.get("dispatch_status") != "COMPLETE":
        errors.append("terminal lane requires COMPLETE dispatch status")

    prompt = packet / "NEXT_AUTHORIZED_LANE_PROMPT.md"
    if state.get("next_prompt_sha256") != sha256(prompt):
        errors.append("next prompt SHA-256 does not match autopilot state")
    prompt_upper = prompt.read_text(encoding="utf-8").upper()
    phase_words = state.get("next_phase", "").replace("PHASE_", "").split("_")[:2]
    if (
        terminal
        and prompt_upper.strip() != "NO_FURTHER_NWR_LANE_AUTHORIZED_GOLDEN_RELEASE_COMPLETE"
    ):
        errors.append("terminal prompt is not exact")
    elif not terminal and (
        not phase_words or not all(word in prompt_upper for word in phase_words)
    ):
        errors.append("next prompt does not identify the configured next phase")

    passed = sum(1 for row in gates if row.get("status") == "PASS")
    if len(gates) != status.get("phase_gates_total"):
        errors.append("phase gate total does not equal matrix row count")
    if passed != status.get("phase_gates_passed"):
        errors.append("phase gate pass count does not equal matrix")
    expected_percentage = passed * 100 // len(gates) if gates else -1
    if status.get("final_completion_percentage") != expected_percentage:
        errors.append("mechanical completion percentage is incorrect")

    manifest_files = manifest.get("files", {})
    packet_files = {
        path.name for path in packet.iterdir() if path.is_file() and path.name != "MANIFEST.json"
    }
    if set(manifest_files) != packet_files:
        errors.append("manifest file set does not match packet")
    if manifest.get("required_file_count") != len(packet_files) + 1:
        errors.append("manifest required_file_count is incorrect")
    for name, receipt in manifest_files.items():
        path = packet / name
        if not path.is_file():
            continue
        if receipt.get("bytes") != len(canonical_bytes(path)) or receipt.get("sha256") != sha256(
            path
        ):
            errors.append(f"manifest receipt mismatch: {name}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    packet = args.repo_root.resolve() / PACKET_RELATIVE
    errors = validate(packet)
    result = {
        "mode": "BOUNDED_CONTINUOUS_AUTOPILOT",
        "packet": str(packet),
        "valid": not errors,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    elif errors:
        for error in errors:
            print(f"FAIL: {error}")
    else:
        print("PASS: Golden Lane bounded continuous autopilot packet is valid")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
