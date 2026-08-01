from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_nwr_outcome_baseline_contract_v1.py"
SPEC = importlib.util.spec_from_file_location("phase_2_contract", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_canonical_phase_2_contract_is_valid() -> None:
    result = MODULE.validate(ROOT)
    assert result["valid"] is True
    assert result["persistence"]["protected_state_write_count"] == 0


def test_future_label_and_nonchronological_fold_fail_closed() -> None:
    with pytest.raises(AssertionError, match="future label leakage"):
        MODULE.validate_temporal_cutoff("2026-03-02", "2026-03-01")
    with pytest.raises(AssertionError, match="nonchronological fold"):
        MODULE.validate_fold(
            train_label_available_dates=["2025-03-01"],
            decision_cutoff="2026-03-01",
            validation_anchor=2026,
            test_anchor=2026,
        )


def test_identity_source_and_position_mutations_fail_closed() -> None:
    with pytest.raises(AssertionError, match="name-only identity"):
        MODULE.validate_identity({"player_id": "name:Player", "position": "QB"})
    with pytest.raises(AssertionError, match="unsupported position"):
        MODULE.validate_identity({"player_id": "00-1", "position": "K"})
    with pytest.raises(AssertionError, match="blocked source"):
        MODULE.validate_source_use("BLOCKED_FAIL_CLOSED", "MODEL")


def test_target_drift_and_insufficient_support_fail_closed() -> None:
    rows = MODULE.read_csv(ROOT / MODULE.PACKET_RELATIVE / "TARGET_CONTRACT.csv")
    mutated = [dict(row) for row in rows]
    mutated[0]["event_offsets"] = "1"
    with pytest.raises(AssertionError, match="target definition drift"):
        MODULE.validate_target_rows(mutated)
    with pytest.raises(AssertionError, match="insufficient support"):
        MODULE.require_support(rows=99, positives=20, negatives=20, seasons=5)


def test_replacement_ties_are_semantic_and_undersized_pools_fail_closed() -> None:
    rows = [
        {"player_id": "p1", "position": "QB", "season": 2025, "nwr_points": 10},
        {"player_id": "p2", "position": "QB", "season": 2025, "nwr_points": 9},
        {"player_id": "p3", "position": "QB", "season": 2025, "nwr_points": 9},
    ]
    with pytest.raises(AssertionError, match="missing replacement reference"):
        MODULE.build_replacement_baselines(rows)
    assert MODULE.classify_against_replacement(9, 9) == "AT_REPLACEMENT"
    assert MODULE.classify_against_replacement(10, 9) == "ABOVE_REPLACEMENT"


def test_disposable_persistence_is_two_root_deterministic(tmp_path: Path) -> None:
    packet = ROOT / MODULE.PACKET_RELATIVE
    spec = json.loads((packet / "PERSISTENCE_FIXTURE.json").read_text(encoding="utf-8"))
    first = MODULE.materialize_persistence_fixture(spec, tmp_path / "a", ROOT)
    second = MODULE.materialize_persistence_fixture(spec, tmp_path / "b", ROOT)
    assert first == second
    assert first["round_trip"] == "PASS"


def test_production_and_existing_roots_are_refused(tmp_path: Path) -> None:
    packet = ROOT / MODULE.PACKET_RELATIVE
    spec = json.loads((packet / "PERSISTENCE_FIXTURE.json").read_text(encoding="utf-8"))
    with pytest.raises(AssertionError, match="repository output root refused"):
        MODULE.materialize_persistence_fixture(spec, ROOT / "generated", ROOT)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(AssertionError, match="must not already exist"):
        MODULE.materialize_persistence_fixture(spec, existing, ROOT)


def test_malformed_persisted_baseline_fails_closed(tmp_path: Path) -> None:
    malformed = tmp_path / "baseline.json"
    malformed.write_text("{not-json", encoding="utf-8")
    with pytest.raises(AssertionError, match="unreadable"):
        MODULE.read_persisted_baseline(malformed)
