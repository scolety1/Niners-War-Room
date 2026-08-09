from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.finalize_redraft_2026_owner_approval import finalize


def _write_candidate(path: Path, *, rookie: str = "False") -> str:
    fields = [
        "player_id",
        "player_name",
        "position",
        "team",
        "season",
        "source_as_of",
        "source_status",
        "evidence_status",
        "rookie",
        "passing_yards",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerow(
            {
                "player_id": "00-1",
                "player_name": "Veteran",
                "position": "QB",
                "team": "SF",
                "season": 2026,
                "source_as_of": "2026-08-08",
                "source_status": "GOVERNANCE_PENDING",
                "evidence_status": "MODEL_VALIDATED_REVIEW_ONLY",
                "rookie": rookie,
                "passing_yards": 4000,
            }
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _packet(tmp_path: Path, *, rookie: str = "False") -> Path:
    candidate = tmp_path / "CANDIDATE_PROJECTION_SNAPSHOT.csv"
    candidate_sha = _write_candidate(candidate, rookie=rookie)
    (tmp_path / "OWNER_APPROVAL.json").write_text(
        json.dumps(
            {
                "authority": "NWR Owner",
                "approval_timestamp": "2026-08-08T23:53:00-06:00",
                "approved_candidate_sha256": candidate_sha,
                "source_as_of": "2026-08-08",
                "approval_scope": "REDRAFT_2026_VETERAN_PROJECTIONS",
                "approved_use": ["Redraft"],
                "prohibited_use": ["Dynasty"],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "NWR_DATA_GOVERNANCE.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "season": 2026,
                "source_id": "test",
                "valid_until": "2026-09-07",
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def test_finalization_changes_only_governance_status_columns(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    result = finalize(packet)
    governed = list(
        csv.DictReader(
            (packet / "GOVERNED_PROJECTION_SNAPSHOT.csv").open("r", encoding="utf-8", newline="")
        )
    )
    receipt = json.loads((packet / "NWR_DATA_GOVERNANCE.json").read_text())
    assert result["changed_cells"] == 2
    assert result["other_changed_cells"] == 0
    assert governed[0]["source_status"] == "GOVERNED"
    assert governed[0]["evidence_status"] == "ADMITTED_CURRENT_SEASON"
    assert governed[0]["passing_yards"] == "4000"
    assert receipt["approval_status"] == "APPROVED_FOR_REDRAFT_V1"
    assert receipt["source_sha256"] == result["governed_projection_sha256"]


def test_finalization_rejects_rookies(tmp_path: Path) -> None:
    packet = _packet(tmp_path, rookie="True")
    with pytest.raises(ValueError, match="rookie"):
        finalize(packet)


def test_finalization_rejects_unbound_candidate(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    approval = json.loads((packet / "OWNER_APPROVAL.json").read_text())
    approval["approved_candidate_sha256"] = "0" * 64
    (packet / "OWNER_APPROVAL.json").write_text(json.dumps(approval), encoding="utf-8")
    with pytest.raises(ValueError, match="does not bind"):
        finalize(packet)
