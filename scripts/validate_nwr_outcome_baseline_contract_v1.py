#!/usr/bin/env python3
"""Validate the Phase 2 outcome/baseline contract and disposable persistence harness."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import Any

PACKET_RELATIVE = Path("docs/hq/master/nwr_outcome_baseline_contract_v1_20260801")
GOLDEN_PACKET_RELATIVE = Path("docs/hq/master/nwr_golden_lane_v1_20260731")
SCORING_RELATIVE = Path("config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json")
OUTCOME_TARGET_RELATIVE = Path(
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/"
    "HISTORICAL_TARGET_MANIFEST.csv"
)
OUTCOME_CONTRACT_RELATIVE = Path(
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/"
    "TARGET_AND_CENSORING_CONTRACT.md"
)
SCORING_SHA256 = "59e7a65f61fd95cd83e82ba0fb631e4977faf120d7692f3aa3ebc690000af3a7"
OUTCOME_TARGET_SHA256 = "2c287a505ac79ca5719df4723fd918fb6391ac2ef6e8cab9c862039babd9205a"
OUTCOME_CONTRACT_SHA256 = "65e1e24bab905c78da0b78b588388b3ed5ea7e121af40d43221fda2bbf6f5cdc"
SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
REPLACEMENT_RANKS = {"QB": 12, "RB": 30, "WR": 40, "TE": 12}
REQUIRED_TARGETS = {
    "WIN_NOW_POINTS": ("0", "March 1 of t+1", "CONTRACT_ONLY"),
    "WIN_NOW_FINISH": ("0", "March 1 of t+1", "CONTRACT_ONLY"),
    "TWO_YEAR_VECTOR": ("0|1", "March 1 of t+2", "CONTRACT_ONLY"),
    "THREE_YEAR_VECTOR": ("0|1|2", "March 1 of t+3", "CONTRACT_ONLY"),
    "WITHIN_3Y_HIT": ("0|1|2", "March 1 of t+3", "EXISTING_GOVERNED"),
    "TWO_OF_3Y_HIT": ("0|1|2", "March 1 of t+3", "EXISTING_GOVERNED"),
    "AVAILABILITY_CONTEXT": ("0", "source-specific recorded time", "NOT_A_FOOTBALL_TARGET"),
    "EVIDENCE_CONFIDENCE": ("", "decision cutoff", "NOT_A_FOOTBALL_TARGET"),
    "MARKET_RETENTION": ("", "N/A", "NOT_ADMITTED"),
}
PROTECTED_PATH_TOKENS = {
    "localdata",
    "local_exports",
    "persistent",
    "recovery",
    "user_state",
    "nwr_shared_data",
}


def canonical_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(canonical_bytes(path))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def validate_temporal_cutoff(label_available_date: str, decision_cutoff: str) -> None:
    if date.fromisoformat(label_available_date) > date.fromisoformat(decision_cutoff):
        raise AssertionError("future label leakage")


def validate_identity(row: Mapping[str, Any]) -> None:
    player_id = str(row.get("player_id", "")).strip()
    position = str(row.get("position", "")).strip().upper()
    if not player_id or player_id.lower().startswith("name:"):
        raise AssertionError("invalid or name-only identity")
    if position not in SUPPORTED_POSITIONS:
        raise AssertionError("unsupported position")


def validate_source_use(status: str, requested_use: str) -> None:
    normalized = status.upper()
    if requested_use == "MODEL" and (
        "BLOCKED" in normalized or "NOT_ADMITTED" in normalized or "REVIEW_ONLY" in normalized
    ):
        raise AssertionError("blocked source requested for model use")


def require_support(*, rows: int, positives: int, negatives: int, seasons: int) -> None:
    if rows < 100 or positives < 20 or negatives < 20 or seasons < 5:
        raise AssertionError("insufficient support")


def validate_fold(
    *,
    train_label_available_dates: Iterable[str],
    decision_cutoff: str,
    validation_anchor: int,
    test_anchor: int,
) -> None:
    if validation_anchor >= test_anchor:
        raise AssertionError("nonchronological fold")
    for available in train_label_available_dates:
        validate_temporal_cutoff(available, decision_cutoff)


def _number(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise AssertionError("nonfinite scoring value")
    return number


def build_replacement_baselines(
    rows: Iterable[Mapping[str, Any]],
    ranks: Mapping[str, int] = REPLACEMENT_RANKS,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[tuple[str, float, int]]] = {
        position: [] for position in SUPPORTED_POSITIONS
    }
    seen: set[tuple[str, int]] = set()
    for row in rows:
        validate_identity(row)
        player_id = str(row["player_id"]).strip()
        position = str(row["position"]).strip().upper()
        season = int(row["season"])
        key = (player_id, season)
        if key in seen:
            raise AssertionError("duplicate player-season identity")
        seen.add(key)
        grouped[position].append((player_id, _number(row["nwr_points"]), season))

    output: list[dict[str, Any]] = []
    for position in sorted(SUPPORTED_POSITIONS):
        rank = int(ranks[position])
        values = sorted(grouped[position], key=lambda item: (-item[1], item[0]))
        if len(values) < rank:
            raise AssertionError(f"missing replacement reference: {position}")
        seasons = {item[2] for item in values}
        if len(seasons) != 1:
            raise AssertionError(f"mixed replacement seasons: {position}")
        boundary = values[rank - 1][1]
        semantic_rank = 1 + sum(value > boundary for _player_id, value, _season in values)
        output.append(
            {
                "boundary_tie_count": sum(
                    value == boundary for _player_id, value, _season in values
                ),
                "position": position,
                "reference_points": boundary,
                "reference_semantic_rank": semantic_rank,
                "review_replacement_rank": rank,
                "season": next(iter(seasons)),
                "status": "REVIEW_ONLY_COMPARATOR",
            }
        )
    return output


def classify_against_replacement(points: float, reference_points: float) -> str:
    if points > reference_points:
        return "ABOVE_REPLACEMENT"
    if points == reference_points:
        return "AT_REPLACEMENT"
    return "BELOW_REPLACEMENT"


def build_fixture_rows(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    if spec.get("schema_version") != "NWR_PHASE_2_SYNTHETIC_BASELINE_FIXTURE_V1":
        raise AssertionError("unsupported persistence fixture")
    if spec.get("synthetic_only") is not True:
        raise AssertionError("persistence fixture must be synthetic")
    season = int(spec["season"])
    start = _number(spec["start_points"])
    step = _number(spec["step_points"])
    rows: list[dict[str, Any]] = []
    positions = spec.get("positions")
    if not isinstance(positions, dict) or set(positions) != set(SUPPORTED_POSITIONS):
        raise AssertionError("fixture position set changed")
    for position in sorted(SUPPORTED_POSITIONS):
        count = int(positions[position])
        if count < REPLACEMENT_RANKS[position]:
            raise AssertionError("fixture replacement support is insufficient")
        for index in range(1, count + 1):
            rows.append(
                {
                    "nwr_points": start - ((index - 1) * step),
                    "player_id": f"fixture:{position}:{index:03d}",
                    "position": position,
                    "season": season,
                }
            )
    return rows


def baseline_artifact(spec: Mapping[str, Any]) -> dict[str, Any]:
    rows = build_fixture_rows(spec)
    return {
        "baselines": build_replacement_baselines(rows),
        "contract_version": "NWR_OUTCOME_BASELINE_CONTRACT_V1",
        "input_rows": len(rows),
        "schema_version": "NWR_PHASE_2_PERSISTED_BASELINE_V1",
        "synthetic_only": True,
    }


def validate_disposable_output_root(output_root: Path, repo_root: Path) -> Path:
    candidate = output_root.resolve(strict=False)
    repository = repo_root.resolve()
    if output_root.exists():
        raise AssertionError("disposable output root must not already exist")
    try:
        candidate.relative_to(repository)
    except ValueError:
        pass
    else:
        raise AssertionError("production or repository output root refused")
    lowered = {part.lower() for part in candidate.parts}
    if lowered & PROTECTED_PATH_TOKENS:
        raise AssertionError("protected production or user-state output root refused")
    if not candidate.parent.is_dir() or candidate.parent.is_symlink():
        raise AssertionError("disposable output parent is missing or unsafe")
    return candidate


def read_persisted_baseline(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError("persisted baseline is unreadable") from exc
    if not isinstance(value, dict) or value.get("schema_version") != (
        "NWR_PHASE_2_PERSISTED_BASELINE_V1"
    ):
        raise AssertionError("persisted baseline schema is invalid")
    return value


def materialize_persistence_fixture(
    spec: Mapping[str, Any], output_root: Path, repo_root: Path
) -> dict[str, Any]:
    root = validate_disposable_output_root(output_root, repo_root)
    root.mkdir()
    final_path = root / "baseline.json"
    temporary = root / "baseline.json.tmp"
    artifact = baseline_artifact(spec)
    body = canonical_json_bytes(artifact)
    try:
        with temporary.open("xb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(final_path)
        reread = read_persisted_baseline(final_path)
        if reread != artifact or final_path.read_bytes() != body:
            raise AssertionError("persisted baseline reread mismatch")
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "artifact_bytes": len(body),
        "artifact_sha256": sha256_bytes(body),
        "baseline_count": len(artifact["baselines"]),
        "input_rows": artifact["input_rows"],
        "round_trip": "PASS",
    }


def _validate_manifest(packet: Path) -> None:
    manifest_path = packet / "MANIFEST.json"
    if not manifest_path.is_file():
        raise AssertionError("missing packet manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = {
        path.name for path in packet.iterdir() if path.is_file() and path.name != "MANIFEST.json"
    }
    if set(manifest.get("files", {})) != files:
        raise AssertionError("packet manifest file set changed")
    if manifest.get("required_file_count") != len(files) + 1:
        raise AssertionError("packet manifest count changed")
    for name, receipt in manifest["files"].items():
        body = canonical_bytes(packet / name)
        if receipt.get("bytes") != len(body) or receipt.get("sha256") != sha256_bytes(body):
            raise AssertionError(f"packet manifest receipt changed: {name}")


def validate_target_rows(rows: Iterable[Mapping[str, str]]) -> None:
    targets = {str(row.get("target_id", "")): row for row in rows}
    if set(targets) != set(REQUIRED_TARGETS):
        raise AssertionError("target definition set drift")
    for target_id, (offsets, available, status) in REQUIRED_TARGETS.items():
        row = targets[target_id]
        if (
            row.get("event_offsets") != offsets
            or row.get("label_available_date") != available
            or row.get("production_status") != status
        ):
            raise AssertionError(f"target definition drift: {target_id}")
    for target_id in targets:
        scope = targets[target_id].get("position_scope")
        if target_id == "MARKET_RETENTION":
            if scope != "NONE":
                raise AssertionError("market target position scope changed")
        elif scope != "QB|RB|WR|TE":
            raise AssertionError(f"target position scope drift: {target_id}")


def _validate_contract_files(repo_root: Path, packet: Path) -> None:
    if sha256(repo_root / SCORING_RELATIVE) != SCORING_SHA256:
        raise AssertionError("scoring authority changed")
    if sha256(repo_root / OUTCOME_TARGET_RELATIVE) != OUTCOME_TARGET_SHA256:
        raise AssertionError("Outcome target manifest changed")
    if sha256(repo_root / OUTCOME_CONTRACT_RELATIVE) != OUTCOME_CONTRACT_SHA256:
        raise AssertionError("Outcome target contract changed")

    scoring = json.loads((repo_root / SCORING_RELATIVE).read_text(encoding="utf-8"))
    league = scoring.get("league_format", {})
    if (
        scoring.get("scoring_version_id") != "nwr_1qb_nonppr_fd_v1"
        or league.get("teams") != 10
        or league.get("superflex") is not False
        or league.get("ppr") is not False
        or league.get("te_premium") is not False
    ):
        raise AssertionError("NWR scoring semantics changed")

    scoring_rows = read_csv(packet / "SCORING_AND_POPULATION_CONTRACT.csv")
    if len(scoring_rows) != 12:
        raise AssertionError("scoring and population contract row count changed")
    validate_target_rows(read_csv(packet / "TARGET_CONTRACT.csv"))

    replacements = read_csv(packet / "REPLACEMENT_REFERENCE_CONTRACT.csv")
    observed_ranks = {
        row["position"]: int(row["review_replacement_rank"]) for row in replacements
    }
    if observed_ranks != REPLACEMENT_RANKS:
        raise AssertionError("replacement reference ranks changed")
    if any(row["status"] != "REVIEW_ONLY_COMPARATOR" for row in replacements):
        raise AssertionError("replacement reference promoted beyond review only")

    source_rows = read_csv(packet / "SOURCE_ELIGIBILITY_MATRIX.csv")
    blocked = [row for row in source_rows if "BLOCKED" in row["status"]]
    if len(blocked) != 6:
        raise AssertionError("six fail-closed source controls must remain visible")
    for row in blocked:
        try:
            validate_source_use(row["status"], "MODEL")
        except AssertionError:
            pass
        else:
            raise AssertionError("blocked source became model eligible")

    strata = read_csv(packet / "POSITION_AND_LIFECYCLE_STRATA.csv")
    position_ids = {row["stratum_id"] for row in strata if row["stratum_family"] == "position"}
    lifecycle_ids = {
        row["stratum_id"] for row in strata if row["stratum_family"] == "lifecycle"
    }
    if position_ids != set(SUPPORTED_POSITIONS):
        raise AssertionError("position strata changed")
    if lifecycle_ids != {
        "early_career_1_to_3",
        "prime_window_4_to_6",
        "veteran_7_to_9",
        "late_career_10_plus",
        "unknown_lifecycle",
    }:
        raise AssertionError("lifecycle strata changed")

    fold_rows = read_csv(packet / "CHRONOLOGICAL_FOLD_CONTRACT.csv")
    if {row["fold_rule_id"] for row in fold_rows} != {
        "FOLD_EXPANDING",
        "FOLD_NESTED_CALIBRATION",
        "FOLD_HORIZON_AWARE",
        "FOLD_MIN_HISTORY",
    }:
        raise AssertionError("chronological fold contract changed")
    support_text = "\n".join(
        row["required_behavior"]
        for row in read_csv(packet / "MISSINGNESS_TIE_SUPPORT_CONTRACT.csv")
    )
    for token in ("rows>=100", "positives>=20", "negatives>=20", "seasons>=5"):
        if token not in support_text:
            raise AssertionError(f"minimum support contract missing: {token}")


def expected_persistence_result(packet: Path) -> dict[str, Any]:
    spec = json.loads((packet / "PERSISTENCE_FIXTURE.json").read_text(encoding="utf-8"))
    artifact = baseline_artifact(spec)
    body = canonical_json_bytes(artifact)
    return {
        "artifact_bytes": len(body),
        "artifact_sha256": sha256_bytes(body),
        "baseline_count": len(artifact["baselines"]),
        "input_rows": artifact["input_rows"],
        "protected_state_write_count": 0,
        "round_trip": "PASS",
        "schema_version": "NWR_PHASE_2_PERSISTENCE_RESULTS_V1",
        "two_root_deterministic": True,
    }


def validate(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    packet = root / PACKET_RELATIVE
    _validate_manifest(packet)
    _validate_contract_files(root, packet)
    expected = expected_persistence_result(packet)
    result_path = packet / "PRODUCTION_PERSISTENCE_RESULTS.json"
    actual = json.loads(result_path.read_text(encoding="utf-8"))
    if actual != expected:
        raise AssertionError("production-persistence result changed")
    return {
        "contract_rows": sum(
            len(read_csv(packet / name))
            for name in (
                "SCORING_AND_POPULATION_CONTRACT.csv",
                "SOURCE_ELIGIBILITY_MATRIX.csv",
                "TARGET_CONTRACT.csv",
                "REPLACEMENT_REFERENCE_CONTRACT.csv",
                "POSITION_AND_LIFECYCLE_STRATA.csv",
                "CHRONOLOGICAL_FOLD_CONTRACT.csv",
                "MISSINGNESS_TIE_SUPPORT_CONTRACT.csv",
            )
        ),
        "persistence": expected,
        "schema_version": "NWR_OUTCOME_BASELINE_CONTRACT_VALIDATION_V1",
        "valid": True,
    }


def write_manifest(packet: Path, packet_relative: Path, schema_version: str) -> None:
    files: dict[str, dict[str, Any]] = {}
    for path in sorted(packet.iterdir(), key=lambda item: item.name):
        if not path.is_file() or path.name == "MANIFEST.json":
            continue
        body = canonical_bytes(path)
        files[path.name] = {"bytes": len(body), "sha256": sha256_bytes(body)}
    manifest = {
        "files": files,
        "hash_representation": "UTF8_LF_CANONICAL_BYTES",
        "manifest_excludes_self": True,
        "packet": packet_relative.as_posix(),
        "required_file_count": len(files) + 1,
        "schema_version": schema_version,
    }
    (packet / "MANIFEST.json").write_bytes(canonical_json_bytes(manifest))


def write_generated(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    packet = root / PACKET_RELATIVE
    result = expected_persistence_result(packet)
    result_path = packet / "PRODUCTION_PERSISTENCE_RESULTS.json"
    result_path.write_bytes(canonical_json_bytes(result))
    write_manifest(
        packet,
        PACKET_RELATIVE,
        "NWR_OUTCOME_BASELINE_CONTRACT_MANIFEST_V1",
    )
    return result


def write_golden_manifest(repo_root: Path) -> None:
    root = repo_root.resolve()
    write_manifest(
        root / GOLDEN_PACKET_RELATIVE,
        GOLDEN_PACKET_RELATIVE,
        "NWR_GOLDEN_LANE_MANIFEST_V2",
    )


def run_two_root_harness(repo_root: Path) -> dict[str, Any]:
    packet = repo_root.resolve() / PACKET_RELATIVE
    spec = json.loads((packet / "PERSISTENCE_FIXTURE.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="nwr-phase2-") as parent:
        parent_path = Path(parent)
        first = materialize_persistence_fixture(spec, parent_path / "root-a", repo_root)
        second = materialize_persistence_fixture(spec, parent_path / "root-b", repo_root)
    if first != second:
        raise AssertionError("two-root persistence output differs")
    return first


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-generated", action="store_true")
    parser.add_argument("--write-golden-manifest", action="store_true")
    parser.add_argument("--run-persistence-harness", action="store_true")
    args = parser.parse_args()
    if args.write_generated:
        print(json.dumps(write_generated(args.repo_root), sort_keys=True, separators=(",", ":")))
        return 0
    if args.write_golden_manifest:
        write_golden_manifest(args.repo_root)
        print('{"golden_manifest_written":true}')
        return 0
    if args.run_persistence_harness:
        result = run_two_root_harness(args.repo_root)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    print(json.dumps(validate(args.repo_root), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
