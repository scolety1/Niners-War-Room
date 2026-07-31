from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_golden_lane_autopilot.py"
SPEC = importlib.util.spec_from_file_location("golden_lane_autopilot", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_canonical_autopilot_packet_is_valid() -> None:
    assert MODULE.validate(ROOT / MODULE.PACKET_RELATIVE) == []


def test_prompt_hash_mutation_fails_closed(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(ROOT / MODULE.PACKET_RELATIVE, packet)
    prompt = packet / "NEXT_AUTHORIZED_LANE_PROMPT.md"
    prompt.write_text(prompt.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
    errors = MODULE.validate(packet)
    assert "next prompt SHA-256 does not match autopilot state" in errors


def test_owner_decision_fails_closed(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(ROOT / MODULE.PACKET_RELATIVE, packet)
    state_path = packet / "GOLDEN_LANE_AUTOPILOT_STATE.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["owner_decisions_required"] = 1
    state_path.write_text(json.dumps(state), encoding="utf-8")
    assert "autopilot state has owner decisions required" in MODULE.validate(packet)


def test_active_stop_requires_hard_stop_dispatch(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(ROOT / MODULE.PACKET_RELATIVE, packet)
    registry = packet / "GOLDEN_LANE_HARD_STOP_REGISTRY.csv"
    registry.write_text(registry.read_text(encoding="utf-8").replace("HS_PROVIDER,provider_financial,Payment trial contract enterprise access billing or API-tier action required,NO,", "HS_PROVIDER,provider_financial,Payment trial contract enterprise access billing or API-tier action required,YES,"), encoding="utf-8")
    errors = MODULE.validate(packet)
    assert "hard-stop registry and autopilot state differ" in errors
    assert "active hard stop requires HARD_STOP dispatch status" in errors
