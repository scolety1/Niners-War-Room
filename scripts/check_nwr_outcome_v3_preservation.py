"""Hash-only preservation checkpoint for the Outcome Columns V3 lane."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

PERSISTENT_DIGEST = "88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987"
RECOVERY_DIGEST = "1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835"
BOARD_HASH = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
FROZEN_HASH = "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179"
OPAQUE_HASHES = {
    "dp_freshness_report.csv": (
        "f34b88e4d0486ec7e34a6e74e1e8953147f91a7b67237062bac0e451eb180e59"
    ),
    "dp_market_baseline_context.csv": (
        "a477c6742e14ac4fd6a892b1f56807a0475c62254f632097a03198b303909bbf"
    ),
    "dp_nwr_join_coverage.csv": (
        "3164bb9a2c69f4b116d22363861b1cce33f903f45e4421af60f0d3d68e37f8a3"
    ),
    "dp_pick_value_context.csv": (
        "c312dd985d78a6edfeeffcba8cf11a56cf729f68ac8eba8c5037b28066184763"
    ),
    "dp_playerid_crosswalk_audit.csv": (
        "31178980fd269c660c815cfbeadc214177252742e4fb3df00e5adeae03c754e2"
    ),
}


@dataclass(frozen=True)
class Record:
    path: str
    bytes: int
    sha256: str


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=root)
    parser.add_argument(
        "--operational-root",
        type=Path,
        default=Path(r"C:\NWR\Niners-War-Room"),
    )
    parser.add_argument(
        "--persistent-root",
        type=Path,
        default=Path(os.environ.get("LOCALAPPDATA", ""))
        / "NinersWarRoom"
        / "data",
    )
    parser.add_argument(
        "--recovery-root",
        type=Path,
        default=Path(os.environ.get("LOCALAPPDATA", ""))
        / "NinersWarRoom"
        / "recovery"
        / "data-health",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inventory_path = (
        args.repo_root
        / "docs"
        / "hq"
        / "master"
        / "nwr_post_v1_assertion_harness_digest_revision_v1_20260722"
        / "PERSISTENT_STATE_DIGEST_REPRODUCTION.csv"
    )
    persistent = _live_records(inventory_path, "persistent", args.persistent_root)
    recovery = _live_records(inventory_path, "recovery", args.recovery_root)
    persistent_digest = _digest(persistent, family="persistent")
    recovery_digest = _digest(recovery, family="recovery")

    opaque_root = (
        args.operational_root
        / "docs"
        / "hq"
        / "parallel_lanes"
        / "dynastyprocess_market_baseline_20260622"
    )
    opaque_matches = sum(
        _sha256(opaque_root / name) == expected
        for name, expected in OPAQUE_HASHES.items()
    )
    board = (
        args.operational_root
        / "local_exports"
        / "model_v4"
        / "current_value"
        / "latest"
        / "full_player_board_value_review_rows.csv"
    )
    frozen = (
        args.repo_root
        / "docs"
        / "hq"
        / "model"
        / "formula_temporal_validation_framework_prospective_2026_"
        "challenger_freeze_v1_20260710"
        / "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
    )
    result = {
        "board_hash_match": _sha256(board) == BOARD_HASH,
        "frozen_hash_match": _sha256(frozen) == FROZEN_HASH,
        "opaque_hash_matches": f"{opaque_matches}/5",
        "persistent_files": len(persistent),
        "persistent_bytes": sum(record.bytes for record in persistent),
        "persistent_digest": persistent_digest,
        "persistent_digest_match": persistent_digest == PERSISTENT_DIGEST,
        "recovery_files": len(recovery),
        "recovery_bytes": sum(record.bytes for record in recovery),
        "recovery_digest": recovery_digest,
        "recovery_digest_match": recovery_digest == RECOVERY_DIGEST,
    }
    print(json.dumps(result, sort_keys=True))
    if result != {
        "board_hash_match": True,
        "frozen_hash_match": True,
        "opaque_hash_matches": "5/5",
        "persistent_files": 14,
        "persistent_bytes": 542801,
        "persistent_digest": PERSISTENT_DIGEST,
        "persistent_digest_match": True,
        "recovery_files": 7,
        "recovery_bytes": 172878,
        "recovery_digest": RECOVERY_DIGEST,
        "recovery_digest_match": True,
    }:
        raise AssertionError("Outcome V3 preservation checkpoint failed")
    return 0


def _live_records(inventory_path: Path, family: str, root: Path) -> tuple[Record, ...]:
    rows: list[Record] = []
    with inventory_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("record_type") != "INVENTORY" or row.get("family") != family:
                continue
            relative = _normalize_path(str(row["path"]))
            path = root.joinpath(*relative.split("/"))
            rows.append(
                Record(
                    path=relative,
                    bytes=path.stat().st_size,
                    sha256=_sha256(path),
                )
            )
    return tuple(sorted(rows, key=lambda record: record.path))


def _normalize_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise AssertionError(f"unsafe preservation inventory path: {value}")
    return normalized


def _digest(records: tuple[Record, ...], *, family: str) -> str:
    document = {
        "version": "PERSISTENT_STATE_DIGEST_V1",
        "serializer": "nwr-persistent-state-json-v1",
        "family": family,
        "records": [
            {
                "path": record.path,
                "bytes": record.bytes,
                "sha256": record.sha256,
            }
            for record in records
        ],
    }
    body = json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
