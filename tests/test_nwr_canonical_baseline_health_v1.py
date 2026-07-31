from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_nwr_canonical_baseline_health_v1.py"
SPEC = importlib.util.spec_from_file_location("phase_1b", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_canonical_fourteen_snapshot_registry_passes() -> None:
    result = MODULE.validate(ROOT, MODULE.BUNDLE_DEFAULT)
    assert result["valid"] is True
    assert result["baseline_count"] == 14


def test_weekly_horizontal_duplicate_repair_is_exact(tmp_path: Path) -> None:
    left = ["player_id", "season", "week", "season_type", "game_id", "team", "summary_level"]
    header = left + left[:-1]
    first = ["gsis-1", "2025", "1", "REG", "g1", "SF", "week"]
    second = ["", "2025", "2", "REG", "g2", "SF", "week"]
    reader = csv.reader(io.StringIO("\n".join([
        ",".join(first + first[:-1]),
        ",".join(second + second[:-1]),
    ])))
    output = tmp_path / "derived.csv"
    result = MODULE._weekly_metrics(reader, header, output)
    assert result["rows"] == 2
    assert result["unequal_duplicate_blocks"] == 0
    assert result["blank_identity_rows"] == 1
    assert output.read_text(encoding="utf-8").splitlines()[0] == ",".join(left)


def test_source_path_and_receipt_mutations_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="unsafe source path"):
        MODULE.safe_source(tmp_path, "../owner-state.csv")
    with pytest.raises(AssertionError, match="missing source"):
        MODULE.safe_source(tmp_path, "missing.csv")
    source = tmp_path / "source.csv"
    source.write_bytes(b"a,b\n1,2\n")
    with pytest.raises(AssertionError, match="changed hash"):
        MODULE.validate_file_receipt(source, source.stat().st_size, "0" * 64, "fixture")


def test_schema_grain_and_crosswalk_mutations_are_detected(tmp_path: Path) -> None:
    assert MODULE.header_sha256(["a", "drifted"]) != MODULE.header_sha256(["a", "b"])
    rows = csv.reader(io.StringIO("1,x\n1,y\n"))
    metrics = MODULE._standard_metrics(rows, ["id", "value"], ["id"], expected_width=2)
    assert metrics["duplicate_keys"] == 1
    crosswalk = tmp_path / "crosswalk.csv"
    crosswalk.write_text("gsis_id,pfr_id\ng1,p1\ng2,p1\n", encoding="utf-8")
    collision = MODULE._crosswalk_metrics(crosswalk)
    assert collision["providers"]["pfr_id"]["collision_values"] == 1


def test_rights_eligibility_temporal_and_line_endings_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="missing rights admitted"):
        MODULE.validate_registry_policy({
            "dataset": "unknown-rights",
            "rights_status": "UNKNOWN_REQUIRES_OWNER_OR_SOURCE_CONFIRMATION",
            "temporal_policy": "POST_GAME_ONLY",
            "model_eligible": "true",
        })
    with pytest.raises(AssertionError, match="unauthorized eligibility"):
        MODULE.validate_registry_policy({
            "dataset": "unauthorized",
            "rights_status": "VERIFIED",
            "temporal_policy": "POST_GAME_ONLY",
            "model_eligible": "true",
        })
    with pytest.raises(AssertionError, match="future leakage"):
        MODULE.validate_temporal_cutoff("2025-12-31", "2025-09-01")
    outcome = tmp_path / "outcome.csv"
    canonical = b"a,b\n1,2\n"
    outcome.write_bytes(canonical.replace(b"\n", b"\r\n"))
    with pytest.raises(AssertionError, match="changed byte size"):
        MODULE.validate_file_receipt(outcome, len(canonical), hashlib.sha256(canonical).hexdigest(), "Outcome")


def test_known_crlf_restoration_is_exact_and_rejects_unknown_bytes(tmp_path: Path) -> None:
    path = tmp_path / "outcome.csv"
    canonical = b"a,b\n1,2\n"
    crlf = canonical.replace(b"\n", b"\r\n")
    path.write_bytes(crlf)
    status = MODULE.restore_known_crlf(
        path,
        expected_bytes=len(canonical),
        expected_sha256=hashlib.sha256(canonical).hexdigest(),
        known_crlf_bytes=len(crlf),
        known_crlf_sha256=hashlib.sha256(crlf).hexdigest(),
    )
    assert status == "RESTORED_KNOWN_CRLF_TO_AUTHORITATIVE_LF"
    assert path.read_bytes() == canonical
    assert MODULE.restore_known_crlf(
        path,
        expected_bytes=len(canonical),
        expected_sha256=hashlib.sha256(canonical).hexdigest(),
        known_crlf_bytes=len(crlf),
        known_crlf_sha256=hashlib.sha256(crlf).hexdigest(),
    ) == "ALREADY_AUTHORITATIVE"
    path.write_bytes(b"unknown")
    with pytest.raises(AssertionError, match="refused unknown bytes"):
        MODULE.restore_known_crlf(
            path,
            expected_bytes=len(canonical),
            expected_sha256=hashlib.sha256(canonical).hexdigest(),
            known_crlf_bytes=len(crlf),
            known_crlf_sha256=hashlib.sha256(crlf).hexdigest(),
        )
