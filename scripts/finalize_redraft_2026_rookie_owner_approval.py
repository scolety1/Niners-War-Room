from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

APPROVED_SCOPE = "REDRAFT_2026_ROOKIE_PROJECTIONS"
EXPECTED_ROOKIE_SHA = "c62a47ffa3ed8746675225225be473da0dbe7f1313842c769dafbcd6709499bc"
EXPECTED_COMBINED_REVIEW_SHA = (
    "218eb5068b30e4441ae6426967f7ea5ce2a47ed3c81686663d5bd155bc45e31f"
)
EXPECTED_VETERAN_SHA = "6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63"
EXPECTED_PENDING_SOURCE = "GOVERNANCE_PENDING"
EXPECTED_PENDING_EVIDENCE = "MODEL_VALIDATED_REVIEW_ONLY"
FINAL_SOURCE = "GOVERNED"
FINAL_EVIDENCE = "ADMITTED_CURRENT_SEASON"
ALLOWED_POSITIONS = {"QB", "RB", "WR", "TE"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return document


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or ()), list(reader)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_manifest(packet: Path) -> None:
    rows = []
    for path in sorted(packet.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name == "MANIFEST.csv":
            continue
        rows.append(
            {
                "file": path.name,
                "bytes": str(path.stat().st_size),
                "sha256": _sha256(path),
            }
        )
    _write_csv(packet / "MANIFEST.csv", ["file", "bytes", "sha256"], rows)


def _is_true(value: object) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes"}


def finalize(packet: Path, veteran_path: Path) -> dict[str, Any]:
    packet = packet.resolve()
    veteran_path = veteran_path.resolve()
    rookie_candidate_path = packet / "ROOKIE_PROJECTION_CANDIDATE.csv"
    combined_review_path = packet / "COMBINED_608_REVIEW_CANDIDATE.csv"
    approval_path = packet / "OWNER_APPROVAL.json"
    governed_rookie_path = packet / "GOVERNED_ROOKIE_PROJECTION_SNAPSHOT.csv"
    governed_combined_path = packet / "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv"
    governance_path = packet / "NWR_DATA_GOVERNANCE.json"
    receipt_path = packet / "GOVERNANCE_FINALIZATION_RECEIPT.json"

    approval = _read_json(approval_path)
    rookie_sha = _sha256(rookie_candidate_path)
    combined_review_sha = _sha256(combined_review_path)
    veteran_sha = _sha256(veteran_path)
    expected_bindings = {
        "approved_candidate_sha256": rookie_sha,
        "approved_combined_review_sha256": combined_review_sha,
        "approved_veteran_sha256": veteran_sha,
    }
    for field, observed in expected_bindings.items():
        if approval.get(field) != observed:
            raise ValueError(f"Owner approval does not bind {field}.")
    if rookie_sha != EXPECTED_ROOKIE_SHA:
        raise ValueError("Rookie candidate differs from the owner-approved exact SHA.")
    if combined_review_sha != EXPECTED_COMBINED_REVIEW_SHA:
        raise ValueError("Combined review candidate differs from the owner-approved exact SHA.")
    if veteran_sha != EXPECTED_VETERAN_SHA:
        raise ValueError("Veteran input differs from the previously approved governed SHA.")
    if approval.get("approval_scope") != APPROVED_SCOPE:
        raise ValueError("Owner approval scope is not the rookie Redraft projection scope.")
    if approval.get("authority") != "NWR Owner":
        raise ValueError("Owner approval identity is missing or unexpected.")
    source_as_of = date.fromisoformat(str(approval["source_as_of"]))

    veteran_fields, veteran_rows = _read_csv(veteran_path)
    rookie_fields, rookie_rows = _read_csv(rookie_candidate_path)
    review_fields, review_rows = _read_csv(combined_review_path)
    if rookie_fields != veteran_fields or review_fields != veteran_fields:
        raise ValueError("Rookie, veteran, and combined review schemas differ.")
    if len(veteran_rows) != 530 or len(rookie_rows) != 78 or len(review_rows) != 608:
        raise ValueError("Approved row counts are not 530 veterans + 78 rookies = 608.")
    try:
        assert_frame_equal(
            pd.read_csv(combined_review_path),
            pd.concat(
                [pd.read_csv(veteran_path), pd.read_csv(rookie_candidate_path)],
                ignore_index=True,
            ),
            check_dtype=False,
            check_exact=True,
        )
    except AssertionError as exc:
        raise ValueError(
            "Combined review values are not the exact veteran-plus-rookie inputs."
        ) from exc

    required = {
        "player_id",
        "position",
        "source_as_of",
        "source_status",
        "evidence_status",
        "rookie",
    }
    missing = sorted(required.difference(rookie_fields))
    if missing:
        raise ValueError("Candidate is missing finalization columns: " + ", ".join(missing))

    veteran_ids: set[str] = set()
    for row in veteran_rows:
        player_id = str(row["player_id"]).strip()
        if not player_id or player_id in veteran_ids:
            raise ValueError("Veteran player IDs must be present and unique.")
        veteran_ids.add(player_id)
        if _is_true(row["rookie"]):
            raise ValueError("Approved veteran input contains a rookie row.")
        if row["source_status"] != FINAL_SOURCE or row["evidence_status"] != FINAL_EVIDENCE:
            raise ValueError("Approved veteran input is not fully governed.")
        if row["position"] not in ALLOWED_POSITIONS:
            raise ValueError("Approved veteran input contains K/DST or an unsupported position.")

    governed_rookie_rows: list[dict[str, str]] = []
    rookie_ids: set[str] = set()
    changed_cells = 0
    for source_row in rookie_rows:
        row = dict(source_row)
        player_id = str(row["player_id"]).strip()
        if not player_id or player_id in rookie_ids or player_id in veteran_ids:
            raise ValueError("Rookie player IDs must be present, unique, and veteran-disjoint.")
        rookie_ids.add(player_id)
        if row["position"] not in ALLOWED_POSITIONS:
            raise ValueError("Rookie approval does not include K/DST or unsupported positions.")
        if not _is_true(row["rookie"]):
            raise ValueError("Rookie candidate contains a non-rookie row.")
        if row["source_as_of"] != source_as_of.isoformat():
            raise ValueError("Rookie source_as_of differs from the owner approval.")
        if row["source_status"] != EXPECTED_PENDING_SOURCE:
            raise ValueError("Rookie source status is not governance-pending.")
        if row["evidence_status"] != EXPECTED_PENDING_EVIDENCE:
            raise ValueError("Rookie evidence status is not review-only.")
        row["source_status"] = FINAL_SOURCE
        row["evidence_status"] = FINAL_EVIDENCE
        changed_cells += 2
        governed_rookie_rows.append(row)

    _write_csv(governed_rookie_path, rookie_fields, governed_rookie_rows)
    veteran_bytes = veteran_path.read_bytes()
    governed_rookie_bytes = governed_rookie_path.read_bytes()
    if not veteran_bytes.endswith(b"\n") or b"\r\n" in veteran_bytes:
        raise ValueError("Approved veteran CSV must be canonical LF bytes ending in newline.")
    if b"\r\n" in governed_rookie_bytes:
        raise ValueError("Governed rookie CSV must use canonical LF bytes.")
    rookie_header_end = governed_rookie_bytes.find(b"\n")
    if rookie_header_end < 0:
        raise ValueError("Governed rookie CSV header is invalid.")
    governed_combined_bytes = veteran_bytes + governed_rookie_bytes[rookie_header_end + 1 :]
    governed_combined_path.write_bytes(governed_combined_bytes)
    if not governed_combined_bytes.startswith(veteran_bytes):
        raise ValueError(
            "Combined governed snapshot does not preserve veteran bytes as its prefix."
        )

    combined_fields, combined_rows = _read_csv(governed_combined_path)
    if combined_fields != veteran_fields or combined_rows != veteran_rows + governed_rookie_rows:
        raise ValueError("Governed combined snapshot differs outside the authorized rookie cells.")
    governed_rookie_sha = _sha256(governed_rookie_path)
    governed_combined_sha = _sha256(governed_combined_path)
    permitted_uses = list(approval["approved_use"])
    prohibited_uses = list(approval["prohibited_use"])
    governance = {
        "schema_version": 1,
        "authority": "NWR_DATA_GOVERNANCE",
        "approval_status": "APPROVED_FOR_REDRAFT_V1",
        "admission_scope": "REDRAFT_2026_VETERAN_AND_ROOKIE_PROJECTIONS",
        "engine_contract_scope": "REDRAFT_2026_PROJECTIONS",
        "season": 2026,
        "source_id": "NWR_REDRAFT_2026_VETERAN_PLUS_ROOKIE_COMBINED_V1",
        "source_authority": "Separately governed NWR veteran and rookie Redraft projection layers",
        "source_sha256": governed_combined_sha,
        "approved_by": approval["authority"],
        "approver_identity": approval["authority"],
        "approved_at_utc": approval["approval_timestamp"],
        "valid_from": "2026-08-09",
        "valid_until": "2026-08-29",
        "source_as_of": source_as_of.isoformat(),
        "component_sources_as_of": {"veterans": "2026-08-08", "rookies": source_as_of.isoformat()},
        "approved_candidate_sha256": rookie_sha,
        "approved_combined_review_sha256": combined_review_sha,
        "approved_veteran_sha256": veteran_sha,
        "governed_rookie_sha256": governed_rookie_sha,
        "permitted_uses": permitted_uses,
        "prohibited_uses": prohibited_uses,
        "player_counts": {"veterans": 530, "rookies": 78, "total": 608},
        "limitations": [
            "Rookie projections are LOW-confidence position-plus-draft-round cohort medians.",
            "No structured 2026 depth chart was available; none was invented.",
            "Max Bredeson and Riley Nowakowski remain blocked for position conflicts.",
            "K and DST remain blocked.",
            (
                "No dynasty, Trading Lab automation, scheduled refresh, provider/API, "
                "or proprietary-source use."
            ),
        ],
        "finalization_contract": {
            "rookie_input_sha256": rookie_sha,
            "rookie_output_sha256": governed_rookie_sha,
            "combined_review_input_sha256": combined_review_sha,
            "combined_governed_output_sha256": governed_combined_sha,
            "veteran_input_sha256": veteran_sha,
            "veteran_bytes_preserved_as_combined_prefix": True,
            "rookie_row_count": len(governed_rookie_rows),
            "changed_columns": ["source_status", "evidence_status"],
            "changed_cells": changed_cells,
            "other_changed_cells": 0,
        },
    }
    _write_json(governance_path, governance)
    receipt = {
        "schema_version": 1,
        "status": "DETERMINISTIC_OWNER_AUTHORIZED_ROOKIE_GOVERNANCE_FINALIZATION",
        "owner_approval_sha256": _sha256(approval_path),
        "approved_rookie_candidate_sha256": rookie_sha,
        "approved_combined_review_sha256": combined_review_sha,
        "approved_veteran_sha256": veteran_sha,
        "governed_rookie_sha256": governed_rookie_sha,
        "governed_combined_sha256": governed_combined_sha,
        "veteran_bytes_preserved_as_combined_prefix": True,
        "veteran_rows": len(veteran_rows),
        "rookie_rows": len(governed_rookie_rows),
        "combined_rows": len(combined_rows),
        "changed_columns": ["source_status", "evidence_status"],
        "changed_cells": changed_cells,
        "other_changed_cells": 0,
        "k_dst_rows": 0,
    }
    _write_json(receipt_path, receipt)
    _write_manifest(packet)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--packet",
        type=Path,
        default=Path(
            "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
        ),
    )
    parser.add_argument(
        "--veteran-path",
        type=Path,
        default=Path(
            "docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808/"
            "GOVERNED_PROJECTION_SNAPSHOT.csv"
        ),
    )
    args = parser.parse_args()
    print(
        json.dumps(
            finalize(args.packet.resolve(), args.veteran_path.resolve()),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
