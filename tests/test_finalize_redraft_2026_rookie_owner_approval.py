from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.finalize_redraft_2026_rookie_owner_approval import finalize

PACKET = Path(
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
)
VETERAN = Path(
    "docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808/"
    "GOVERNED_PROJECTION_SNAPSHOT.csv"
)


def _approval() -> dict[str, object]:
    return {
        "schema_version": 1,
        "authority": "NWR Owner",
        "approval_timestamp": "2026-08-09T01:52:00-06:00",
        "approval_scope": "REDRAFT_2026_ROOKIE_PROJECTIONS",
        "source_as_of": "2026-07-30",
        "approved_candidate_sha256": (
            "c62a47ffa3ed8746675225225be473da0dbe7f1313842c769dafbcd6709499bc"
        ),
        "approved_combined_review_sha256": (
            "218eb5068b30e4441ae6426967f7ea5ce2a47ed3c81686663d5bd155bc45e31f"
        ),
        "approved_veteran_sha256": (
            "6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63"
        ),
        "approved_use": ["NWR Redraft V1 current-season rookie calculations"],
        "prohibited_use": ["dynasty ranking changes", "K/DST projections"],
    }


def _packet_copy(tmp_path: Path) -> Path:
    packet = tmp_path / "packet"
    packet.mkdir()
    for name in ["ROOKIE_PROJECTION_CANDIDATE.csv", "COMBINED_608_REVIEW_CANDIDATE.csv"]:
        shutil.copyfile(PACKET / name, packet / name)
    (packet / "OWNER_APPROVAL.json").write_text(
        json.dumps(_approval(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return packet


def test_finalization_binds_exact_hashes_and_preserves_veteran_bytes(tmp_path: Path) -> None:
    packet = _packet_copy(tmp_path)
    receipt = finalize(packet, VETERAN)
    combined = (packet / "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv").read_bytes()
    veteran = VETERAN.read_bytes()
    governed_rookie = (packet / "GOVERNED_ROOKIE_PROJECTION_SNAPSHOT.csv").read_text(
        encoding="utf-8"
    )
    governance = json.loads((packet / "NWR_DATA_GOVERNANCE.json").read_text())
    assert combined.startswith(veteran)
    assert receipt["veteran_bytes_preserved_as_combined_prefix"] is True
    assert receipt["changed_cells"] == 156
    assert receipt["other_changed_cells"] == 0
    assert "GOVERNANCE_PENDING" not in governed_rookie
    assert governed_rookie.count("GOVERNED") == 78
    assert governance["source_sha256"] == receipt["governed_combined_sha256"]
    assert governance["valid_until"] == "2026-08-29"
    manifest = (packet / "MANIFEST.csv").read_text(encoding="utf-8")
    assert "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv" in manifest
    for row in manifest.splitlines()[1:]:
        name, size, digest = row.split(",")
        data = (packet / name).read_bytes()
        assert len(data) == int(size)
        assert hashlib.sha256(data).hexdigest() == digest


def test_finalization_stops_if_approved_rookie_bytes_change(tmp_path: Path) -> None:
    packet = _packet_copy(tmp_path)
    candidate = packet / "ROOKIE_PROJECTION_CANDIDATE.csv"
    candidate.write_bytes(candidate.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="does not bind|differs"):
        finalize(packet, VETERAN)


def test_finalization_stops_if_combined_review_bytes_change(tmp_path: Path) -> None:
    packet = _packet_copy(tmp_path)
    combined = packet / "COMBINED_608_REVIEW_CANDIDATE.csv"
    combined.write_bytes(combined.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="does not bind|differs"):
        finalize(packet, VETERAN)
