#!/usr/bin/env python3
"""Validate the exact Phase 1B baseline registry without mutating raw sources."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, Iterable


PACKET_RELATIVE = Path("docs/hq/master/nwr_canonical_baseline_health_v1_20260731")
BUNDLE_DEFAULT = Path(r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260721_204727")
OUTCOME_RELATIVE = Path(
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/"
    "OUTCOME_V3_INTEGRATION_PACK.csv"
)
OUTCOME_BYTES = 4_511_262
OUTCOME_SHA256 = "e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20"
OUTCOME_KNOWN_CRLF_BYTES = 4_528_543
OUTCOME_KNOWN_CRLF_SHA256 = "a8b468c13a68c8c2feecaf55440982615099019cde8c1963e48068eed01a87cb"
PROVIDER_IDS = (
    "cbs_id", "cfbref_id", "espn_id", "fantasy_data_id", "fantasypros_id",
    "fleaflicker_id", "gsis_id", "ktc_id", "mfl_id", "nfl_id", "pff_id",
    "pfr_id", "rotowire_id", "rotoworld_id", "sleeper_id", "sportradar_id",
    "stats_global_id", "stats_id", "swish_id", "yahoo_id",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_file_receipt(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> None:
    if not path.is_file():
        raise AssertionError(f"missing source: {label}")
    if path.stat().st_size != expected_bytes:
        raise AssertionError(f"changed byte size: {label}")
    if sha256_file(path) != expected_sha256:
        raise AssertionError(f"changed hash: {label}")


def restore_known_crlf(
    path: Path,
    *,
    expected_bytes: int,
    expected_sha256: str,
    known_crlf_bytes: int,
    known_crlf_sha256: str,
) -> str:
    """Restore only a byte-exact known CRLF checkout to governed LF bytes."""
    if path.is_symlink() or not path.is_file():
        raise AssertionError("Outcome V3 restoration target is missing or unsafe")
    current_bytes = path.stat().st_size
    current_sha256 = sha256_file(path)
    if current_bytes == expected_bytes and current_sha256 == expected_sha256:
        return "ALREADY_AUTHORITATIVE"
    if current_bytes != known_crlf_bytes or current_sha256 != known_crlf_sha256:
        raise AssertionError("Outcome V3 restoration refused unknown bytes")
    restored = path.read_bytes().replace(b"\r\n", b"\n")
    if len(restored) != expected_bytes or hashlib.sha256(restored).hexdigest() != expected_sha256:
        raise AssertionError("Outcome V3 restoration did not reproduce authority")
    temporary = path.with_name(path.name + ".phase1b-lf.tmp")
    if temporary.exists():
        raise AssertionError("Outcome V3 restoration temporary path already exists")
    try:
        with temporary.open("xb") as handle:
            handle.write(restored)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()
    validate_file_receipt(path, expected_bytes, expected_sha256, "Outcome V3 restored checkout")
    return "RESTORED_KNOWN_CRLF_TO_AUTHORITATIVE_LF"


def restore_outcome_checkout(repo_root: Path) -> str:
    root = repo_root.resolve()
    path = (root / OUTCOME_RELATIVE).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise AssertionError("Outcome V3 restoration target escapes repository") from exc
    return restore_known_crlf(
        path,
        expected_bytes=OUTCOME_BYTES,
        expected_sha256=OUTCOME_SHA256,
        known_crlf_bytes=OUTCOME_KNOWN_CRLF_BYTES,
        known_crlf_sha256=OUTCOME_KNOWN_CRLF_SHA256,
    )


def validate_registry_policy(record: dict[str, str]) -> None:
    if not record.get("temporal_policy"):
        raise AssertionError(f"missing temporal policy: {record.get('dataset', 'unknown')}")
    if "UNKNOWN" in record.get("rights_status", "") and record.get("model_eligible", "").lower() != "false":
        raise AssertionError(f"missing rights admitted: {record.get('dataset', 'unknown')}")
    if record.get("model_eligible", "").lower() != "false":
        raise AssertionError(f"unauthorized eligibility: {record.get('dataset', 'unknown')}")


def validate_temporal_cutoff(available_at: str, cutoff: str) -> None:
    if available_at > cutoff:
        raise AssertionError("future leakage")


def header_sha256(header: list[str]) -> str:
    body = json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def validate_packet_manifest(packet: Path) -> None:
    manifest = json.loads((packet / "MANIFEST.json").read_text(encoding="utf-8"))
    files = {path.name for path in packet.iterdir() if path.is_file() and path.name != "MANIFEST.json"}
    if set(manifest.get("files", {})) != files:
        raise AssertionError("packet manifest file set changed")
    if manifest.get("required_file_count") != len(files) + 1:
        raise AssertionError("packet manifest count changed")
    for name, receipt in manifest["files"].items():
        body = (packet / name).read_bytes().replace(b"\r\n", b"\n")
        if len(body) != receipt["bytes"] or hashlib.sha256(body).hexdigest() != receipt["sha256"]:
            raise AssertionError(f"packet manifest receipt changed: {name}")


def safe_source(bundle_root: Path, relative: str) -> Path:
    normalized = relative.replace("\\", "/")
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:", normalized)
        or any(part in {"", ".", ".."} for part in normalized.split("/"))
    ):
        raise AssertionError(f"unsafe source path: {relative}")
    root = bundle_root.resolve()
    path = root.joinpath(*normalized.split("/")).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise AssertionError(f"source escapes bundle root: {relative}") from exc
    if not path.is_file():
        raise AssertionError(f"missing source: {relative}")
    return path


def _key_digest(values: Iterable[str]) -> bytes:
    return hashlib.sha256("\x1f".join(values).encode("utf-8")).digest()[:16]


def _csv_row_bytes(row: list[str]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerow(row)
    return output.getvalue().encode("utf-8")


def _standard_metrics(
    reader: csv.reader,
    header: list[str],
    columns: list[str],
    *,
    expected_width: int,
    identity_column: str | None = None,
) -> dict[str, int]:
    indices = [header.index(name) for name in columns]
    identity_index = header.index(identity_column) if identity_column else None
    seen: set[bytes] = set()
    rows = duplicates = blank_identity = 0
    for row in reader:
        rows += 1
        if len(row) != expected_width:
            raise AssertionError(f"row {rows + 1} has width {len(row)}, expected {expected_width}")
        key = _key_digest(row[index] for index in indices)
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
        if identity_index is not None and not row[identity_index]:
            blank_identity += 1
    return {"rows": rows, "duplicate_keys": duplicates, "blank_identity_rows": blank_identity}


def _weekly_metrics(
    reader: csv.reader,
    header: list[str],
    derived_output: Path | None,
) -> dict[str, Any]:
    split = header.index("player_id", 1)
    left_header, right_header = header[:split], header[split:]
    if left_header[: len(right_header)] != right_header or left_header[-1] != "summary_level":
        raise AssertionError("weekly duplicated schema shape changed")
    key_columns = ["player_id", "season", "week", "season_type", "game_id", "team", "summary_level"]
    indices = [left_header.index(name) for name in key_columns]
    player_index = left_header.index("player_id")
    seen: set[bytes] = set()
    rows = duplicates = blank_identity = unequal_blocks = 0
    derived_hash = hashlib.sha256()
    derived_bytes = 0
    output_handle = None
    if derived_output is not None:
        destination = derived_output.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        output_handle = destination.open("xb")
    try:
        encoded = _csv_row_bytes(left_header)
        derived_hash.update(encoded)
        derived_bytes += len(encoded)
        if output_handle:
            output_handle.write(encoded)
        for row in reader:
            rows += 1
            if len(row) != len(header):
                raise AssertionError(f"weekly row {rows + 1} has invalid width")
            left, right = row[:split], row[split:]
            if left[: len(right)] != right:
                unequal_blocks += 1
            key = _key_digest(left[index] for index in indices)
            if key in seen:
                duplicates += 1
            else:
                seen.add(key)
            if not left[player_index]:
                blank_identity += 1
            encoded = _csv_row_bytes(left)
            derived_hash.update(encoded)
            derived_bytes += len(encoded)
            if output_handle:
                output_handle.write(encoded)
    finally:
        if output_handle:
            output_handle.close()
    return {
        "rows": rows,
        "duplicate_keys": duplicates,
        "blank_identity_rows": blank_identity,
        "unequal_duplicate_blocks": unequal_blocks,
        "derived_columns": len(left_header),
        "derived_header_sha256": header_sha256(left_header),
        "derived_bytes": derived_bytes,
        "derived_sha256": derived_hash.hexdigest(),
    }


def _depth_metrics(reader: csv.reader, header: list[str]) -> dict[str, int]:
    nfl_columns = ["season", "club_code", "week", "game_type", "formation", "gsis_id", "depth_position", "depth_team", "full_name"]
    espn_columns = ["dt", "team", "player_name", "espn_id", "pos_grp_id", "pos_id", "pos_slot", "pos_rank"]
    nfl_indices = [header.index(name) for name in nfl_columns]
    espn_indices = [header.index(name) for name in espn_columns]
    season_index = header.index("season")
    espn_name_index = header.index("player_name")
    nfl_seen: set[bytes] = set()
    espn_seen: set[bytes] = set()
    rows = duplicates = blank_identity = 0
    for row in reader:
        rows += 1
        if len(row) != len(header):
            raise AssertionError(f"depth row {rows + 1} has invalid width")
        if row[season_index]:
            key = _key_digest(row[index] for index in nfl_indices)
            target = nfl_seen
        else:
            key = _key_digest(row[index] for index in espn_indices)
            target = espn_seen
            if not row[espn_name_index]:
                blank_identity += 1
        if key in target:
            duplicates += 1
        else:
            target.add(key)
    return {"rows": rows, "duplicate_keys": duplicates, "blank_identity_rows": blank_identity}


def _crosswalk_metrics(path: Path) -> dict[str, Any]:
    values: dict[str, dict[str, set[str]]] = {
        provider: defaultdict(set) for provider in PROVIDER_IDS
    }
    blank_gsis = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, row in enumerate(csv.DictReader(handle), start=2):
            gsis = (row.get("gsis_id") or "").strip()
            if not gsis:
                blank_gsis += 1
            token = gsis or f"row:{line_number}"
            for provider in PROVIDER_IDS:
                value = (row.get(provider) or "").strip()
                if value:
                    values[provider][value].add(token)
    providers = {
        provider: {
            "nonblank_values": len(mapping),
            "collision_values": sum(len(tokens) > 1 for tokens in mapping.values()),
            "collision_rows": sum(len(tokens) for tokens in mapping.values() if len(tokens) > 1),
        }
        for provider, mapping in values.items()
    }
    return {"blank_gsis_rows": blank_gsis, "providers": providers}


def validate(repo_root: Path, bundle_root: Path, derived_output: Path | None = None) -> dict[str, Any]:
    packet = repo_root.resolve() / PACKET_RELATIVE
    validate_packet_manifest(packet)
    with (packet / "BASELINE_REGISTRY.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        registry = list(csv.DictReader(handle))
    if len(registry) != 14:
        raise AssertionError("baseline registry must contain exactly 14 rows")
    results: list[dict[str, Any]] = []
    crosswalk_path: Path | None = None
    for record in registry:
        path = safe_source(bundle_root, record["source_relative_path"])
        validate_file_receipt(path, int(record["bytes"]), record["sha256"], record["dataset"])
        validate_registry_policy(record)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            if len(header) != int(record["columns"]):
                raise AssertionError(f"schema width changed: {record['dataset']}")
            if header_sha256(header) != record["header_sha256"]:
                raise AssertionError(f"schema changed: {record['dataset']}")
            strategy = record["grain_strategy"]
            if strategy == "WEEKLY_DUPLICATED_HORIZONTAL_SCHEMA":
                metrics = _weekly_metrics(reader, header, derived_output)
            elif strategy == "DEPTH_DUAL_GRAIN":
                metrics = _depth_metrics(reader, header)
            elif strategy == "MIXED_HORIZONTAL_JOIN_QUARANTINE":
                rows = 0
                for row in reader:
                    rows += 1
                    if len(row) != len(header):
                        raise AssertionError(f"mixed-schema row {rows + 1} has invalid width")
                metrics = {"rows": rows, "duplicate_keys": 0, "blank_identity_rows": rows}
            else:
                identity = {
                    "player_stats_weekly": "player_id",
                    "rosters": "gsis_id",
                    "weekly_rosters": "gsis_id",
                }.get(record["dataset"])
                metrics = _standard_metrics(
                    reader,
                    header,
                    record["grain_key"].split("|"),
                    expected_width=len(header),
                    identity_column=identity,
                )
                if record["dataset"] == "ftn_charting":
                    metrics["blank_identity_rows"] = metrics["rows"]
        if metrics["rows"] != int(record["rows"]):
            raise AssertionError(f"row count changed: {record['dataset']}")
        if metrics["duplicate_keys"] != int(record["expected_duplicate_keys"]):
            raise AssertionError(f"grain result changed: {record['dataset']}")
        if metrics["blank_identity_rows"] != int(record["expected_blank_identity_rows"]):
            raise AssertionError(f"identity result changed: {record['dataset']}")
        if record["dataset"] == "ff_playerids":
            crosswalk_path = path
        results.append({"dataset": record["dataset"], **metrics})

    if crosswalk_path is None:
        raise AssertionError("crosswalk source missing from registry")
    collision_expected = json.loads((packet / "CROSSWALK_COLLISION_RECEIPT.json").read_text(encoding="utf-8"))
    collision_actual = _crosswalk_metrics(crosswalk_path)
    if collision_actual["blank_gsis_rows"] != collision_expected["blank_gsis_rows"] or collision_actual["providers"] != collision_expected["providers"]:
        raise AssertionError("crosswalk collision receipt changed")

    weekly = next(result for result in results if result["dataset"] == "player_stats_weekly")
    derived_receipt = json.loads((packet / "PLAYER_STATS_WEEKLY_HYGIENE_RECEIPT.json").read_text(encoding="utf-8"))
    if (
        weekly["unequal_duplicate_blocks"] != 0
        or weekly["derived_columns"] != derived_receipt["derived_columns"]
        or weekly["derived_bytes"] != derived_receipt["derived_bytes_utf8_lf_csv"]
        or weekly["derived_sha256"] != derived_receipt["derived_sha256_utf8_lf_csv"]
    ):
        raise AssertionError("weekly derived hygiene receipt changed")

    outcome = repo_root.resolve() / OUTCOME_RELATIVE
    validate_file_receipt(outcome, OUTCOME_BYTES, OUTCOME_SHA256, "Outcome V3 authoritative checkout bytes")
    return {
        "schema_version": "NWR_CANONICAL_BASELINE_HEALTH_VALIDATION_V1",
        "baseline_count": len(results),
        "datasets": results,
        "crosswalk": collision_actual,
        "outcome_v3_sha256": OUTCOME_SHA256,
        "valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--bundle-root", type=Path, default=BUNDLE_DEFAULT)
    parser.add_argument("--derived-output", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--restore-outcome-checkout", action="store_true")
    args = parser.parse_args()
    if args.restore_outcome_checkout:
        print(restore_outcome_checkout(args.repo_root))
    result = validate(args.repo_root, args.bundle_root, args.derived_output)
    body = json.dumps(result, sort_keys=True, separators=(",", ":"))
    if args.json_output:
        args.json_output.write_text(body + "\n", encoding="utf-8", newline="\n")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
