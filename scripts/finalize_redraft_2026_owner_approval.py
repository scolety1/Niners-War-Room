from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

APPROVED_SCOPE = "REDRAFT_2026_VETERAN_PROJECTIONS"
EXPECTED_PENDING_SOURCE = "GOVERNANCE_PENDING"
EXPECTED_PENDING_EVIDENCE = "MODEL_VALIDATED_REVIEW_ONLY"
FINAL_SOURCE = "GOVERNED"
FINAL_EVIDENCE = "ADMITTED_CURRENT_SEASON"
ALLOWED_POSITIONS = {"QB", "RB", "WR", "TE"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return document


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finalize(packet: Path) -> dict[str, Any]:
    candidate_path = packet / "CANDIDATE_PROJECTION_SNAPSHOT.csv"
    approval_path = packet / "OWNER_APPROVAL.json"
    governed_path = packet / "GOVERNED_PROJECTION_SNAPSHOT.csv"
    governance_path = packet / "NWR_DATA_GOVERNANCE.json"
    derivation_path = packet / "GOVERNANCE_FINALIZATION_RECEIPT.json"
    approval = _read_json(approval_path)
    candidate_sha = _sha256(candidate_path)
    if approval.get("approved_candidate_sha256") != candidate_sha:
        raise ValueError("Owner approval does not bind the candidate projection bytes.")
    if approval.get("approval_scope") != APPROVED_SCOPE:
        raise ValueError("Owner approval scope is not the veteran Redraft projection scope.")
    if not str(approval.get("authority") or "").strip():
        raise ValueError("Owner approval identity is missing.")
    source_as_of = date.fromisoformat(str(approval["source_as_of"]))
    with candidate_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or ())
        rows = list(reader)
    required = {
        "player_id",
        "position",
        "source_as_of",
        "source_status",
        "evidence_status",
        "rookie",
    }
    missing = sorted(required.difference(fieldnames))
    if missing:
        raise ValueError("Candidate is missing finalization columns: " + ", ".join(missing))
    seen: set[str] = set()
    changed_cells = 0
    for row in rows:
        player_id = str(row["player_id"]).strip()
        if not player_id or player_id in seen:
            raise ValueError("Candidate player IDs must be present and unique.")
        seen.add(player_id)
        if row["position"] not in ALLOWED_POSITIONS:
            raise ValueError("Owner approval does not include K, DST, or unsupported positions.")
        if str(row["rookie"]).strip().casefold() in {"1", "true", "yes"}:
            raise ValueError("Owner approval does not include rookie projections.")
        if row["source_as_of"] != source_as_of.isoformat():
            raise ValueError("Candidate source_as_of differs from the owner approval.")
        if row["source_status"] != EXPECTED_PENDING_SOURCE:
            raise ValueError("Candidate source status is not governance-pending.")
        if row["evidence_status"] != EXPECTED_PENDING_EVIDENCE:
            raise ValueError("Candidate evidence status is not review-only.")
        row["source_status"] = FINAL_SOURCE
        row["evidence_status"] = FINAL_EVIDENCE
        changed_cells += 2
    with governed_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    governed_sha = _sha256(governed_path)
    prior_governance = _read_json(governance_path)
    permitted_uses = list(approval["approved_use"])
    prohibited_uses = list(approval["prohibited_use"])
    governance = {
        **prior_governance,
        "authority": "NWR_DATA_GOVERNANCE",
        "approval_status": "APPROVED_FOR_REDRAFT_V1",
        "admission_scope": APPROVED_SCOPE,
        "engine_contract_scope": "REDRAFT_2026_PROJECTIONS",
        "source_sha256": governed_sha,
        "approved_candidate_sha256": candidate_sha,
        "generated_at": "2026-08-09T05:53:00Z",
        "approved_by": approval["authority"],
        "approver_identity": approval["authority"],
        "approved_at_utc": approval["approval_timestamp"],
        "permitted_uses": permitted_uses,
        "prohibited_uses": prohibited_uses,
        "limitations": [
            "Veteran-only prior-season persistence forecast.",
            "All rookies remain blocked pending separate governed workload admission.",
            "K and DST remain blocked.",
            "No dynasty, scheduled refresh, provider/API, or proprietary-source use.",
        ],
        "finalization_contract": {
            "input_sha256": candidate_sha,
            "output_sha256": governed_sha,
            "row_count": len(rows),
            "changed_columns": ["source_status", "evidence_status"],
            "changed_cells": changed_cells,
            "other_changed_cells": 0,
            "source_status_transform": f"{EXPECTED_PENDING_SOURCE} -> {FINAL_SOURCE}",
            "evidence_status_transform": (f"{EXPECTED_PENDING_EVIDENCE} -> {FINAL_EVIDENCE}"),
        },
    }
    _write_json(governance_path, governance)
    derivation = {
        "schema_version": 1,
        "status": "DETERMINISTIC_OWNER_AUTHORIZED_GOVERNANCE_FINALIZATION",
        "owner_approval_sha256": _sha256(approval_path),
        "approved_candidate_sha256": candidate_sha,
        "governed_projection_sha256": governed_sha,
        "row_count": len(rows),
        "changed_columns": ["source_status", "evidence_status"],
        "changed_cells": changed_cells,
        "other_changed_cells": 0,
        "rookie_rows": 0,
        "k_dst_rows": 0,
    }
    _write_json(derivation_path, derivation)
    return derivation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--packet",
        type=Path,
        default=Path("docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808"),
    )
    args = parser.parse_args()
    print(json.dumps(finalize(args.packet.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
