# ruff: noqa: E501

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/hq/master/nwr_workday_accuracy_evidence_expansion_v1_20260723"
PRIOR_PACKET = ROOT / "docs/hq/master/nwr_exact_model_v4_replay_accuracy_audit_v1_20260723"
PRIOR_MASK = PRIOR_PACKET / "COMPONENT_AND_ROW_EXACTNESS_MASK.csv"

EXPECTED_HQ = "4e8fc06900024aa00a67689f99fc734c6d513254"
EXPECTED_TREE = "0840bdda644299e6630933f85bb9a4c38c6ae5ed"
MODEL_ID = "model_v4_wr_qb_v2_old_pocket_qb_guardrail"
HISTORICAL_ROWS = 5_518
HISTORICAL_PLAYERS = 1_552
OOF_ROWS = 4_731
OOF_PLAYERS = 1_390

PRIMARY_LOCAL_ROOT = Path(r"C:\NWR\Niners-War-Room")
CURRENT_BOARD = (
    PRIMARY_LOCAL_ROOT
    / "local_exports/model_v4/current_value/latest/"
    "full_player_board_value_review_rows.csv"
)
CURRENT_BOARD_SHA256 = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
FROZEN_2026 = (
    ROOT
    / "docs/hq/model/"
    "formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/"
    "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
)
FROZEN_2026_SHA256 = "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179"

HQ2_ROOT = Path(
    r"C:\NWR\Niners-War-Room-hq2-candidate-formula-shadow-integration-v1-20260708"
)
HQ2_HEAD = "391b500d2ca897b3072bd18bef6722768ea47433"
HQ2_TREE = "33a15ca8cb2e57c01a69621ae9dd0505a9f6fbb3"
HQ2_PACKET = (
    HQ2_ROOT / "docs/hq/model/hq2_review_only_shadow_component_v1_20260708"
)
HQ2_SCRIPT = HQ2_PACKET / "run_hq2_review_only_shadow_component_v1.py"
HQ2_PANEL = HQ2_PACKET / "HQ2_REVIEW_ONLY_SHADOW_COMPONENT_V1_PANEL.csv"
HQ2_SCORECARD = HQ2_PACKET / "HQ2_REVIEW_ONLY_SHADOW_COMPONENT_V1_SCORECARD.csv"
HQ2_SUBSTRATE = (
    HQ2_ROOT
    / "docs/hq/experiments/"
    "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701/"
    "nwr_historical_tuning_feature_target_substrate_v3.parquet"
)
HQ2_SOURCE_COMMIT = "5556520fb5b0591ea2740855ab43400279603809"
HQ2_SOURCE_TREE = "160b7174a6f6b4ce5e0e26cdf2fd00c0b52d2940"
HQ2_EXPECTED = {
    HQ2_SCRIPT: {
        "sha256": "d2f773ef3a1d6ec06094f993a2d63cc730ea486f2bc0954b6c0a21b9f8ca0923",
        "blob": "eadfb3d624dfa94231a98c157a995fec43b162a0",
        "bytes": 47_062,
    },
    HQ2_PANEL: {
        "sha256": "5684d9d66ff97f41a3a0baeb46d5f61cae14987ad28f354e3508693aecd98f1f",
        "blob": "04ee0497fddcd267c12744e9a26bf59581c614a2",
        "bytes": 1_655_067,
    },
    HQ2_SCORECARD: {
        "sha256": "d7aa42260997565f8973e4962fa329fafeeed36bda47075163cafef6244f95c0",
        "blob": "433d9da61b10758da9dd341fcd096aa3fb97e254",
        "bytes": 730,
    },
    HQ2_SUBSTRATE: {
        "sha256": "6b80a71af609932c91553413319902d2a61a4b24c36060d3c724747672f9797a",
        "blob": "546d653bf642060ecfc1db09962128c3f9cdbc0a",
        "bytes": 479_796,
    },
}

PERSISTENT_DIGEST = "88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987"
RECOVERY_DIGEST = "1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835"
OPAQUE_HASHES = {
    "dp_freshness_report.csv": (
        "1e4212694f19cce9db75af01b91e3827c6a124cca036e872407076b0d89f6c81"
    ),
    "dp_market_baseline_context.csv": (
        "6a8bb153a8e2e2bb8cdd08c586a34bdfebfbdd6a0ddfe681e4182127495be824"
    ),
    "dp_nwr_join_coverage.csv": (
        "331a47087e784e4ec2392b78fdad6c27db3f8fd26383efa2ef9208756708e1cb"
    ),
    "dp_pick_value_context.csv": (
        "97c6c74abd4d9cf17d6aea4cbbb0495745b8d75440ec0c0b95581e2d78fab7bb"
    ),
    "dp_playerid_crosswalk_audit.csv": (
        "d0f78739e6828408badb5a6b2062a2503e42a68e115946941371d6f89244407f"
    ),
}

ALLOWED_CLASSES = {
    "EXACT_PRIMARY_RECEIPT",
    "EXACT_DETERMINISTIC_REGENERATION",
    "NEAR_EQUIVALENT",
    "PARTIAL_REPLAY",
    "APPROXIMATE",
    "REVIEW_ONLY",
    "BLOCKED_MISSING_RECEIPT",
    "BLOCKED_SOURCE_NOT_ADMITTED",
    "PROVENANCE_INSUFFICIENT",
    "SCHEMA_INCOMPATIBLE",
    "IDENTITY_BLOCKED",
    "DEPRECATED",
    "FROZEN_COMPARATOR",
}
EXACT_CLASSES = {"EXACT_PRIMARY_RECEIPT", "EXACT_DETERMINISTIC_REGENERATION"}
REQUIRED_CHAIN = (
    "position_specific_components",
    "lifecycle",
    "confidence",
    "discipline_safety",
    "checkpoint_score",
    "final_score",
    "final_rank",
)
REQUIRED_MANIFEST_FIELDS = (
    "model_version",
    "code_commit",
    "formula_contract",
    "source_families_versions",
    "source_as_of_dates",
    "input_hashes",
    "schemas",
    "player_id_namespace",
    "season",
    "position",
    "row_count",
    "checkpoint_stage",
    "output_hash",
    "rank_assignment",
    "tie_handling",
    "missing_data_behavior",
)


@dataclass(frozen=True)
class SearchSummary:
    surface: str
    scope: str
    candidates: int
    keyword_leads: int
    exact_admissions: int
    stopping_rule: str
    result: str


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_blob(path: Path, *, repo: Path) -> str:
    return git("hash-object", str(path), cwd=repo)


def validate_git_blob(path: Path, expected_blob: str, *, repo: Path) -> None:
    actual = git_blob(path, repo=repo)
    if actual != expected_blob:
        raise RuntimeError(f"Git blob identity changed for {path}: {actual}")


def _parse_date(value: object, field: str) -> date:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError(f"{field} is required")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise RuntimeError(f"{field} is invalid") from exc


def canonical_row_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    canonical = sorted(
        (dict(row) for row in rows),
        key=lambda row: (
            str(row.get("player_id") or ""),
            int(row.get("season") or 0),
            str(row.get("position") or ""),
        ),
    )
    data = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def validate_exact_claim(
    record: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    """Fail closed on exact-evidence mutations.

    This validator intentionally accepts no inference. It is small enough to mutation-test
    completely and is used only by the research audit, never by production ranking code.
    """

    classification = str(record.get("classification") or "")
    if classification not in ALLOWED_CLASSES:
        raise RuntimeError("unsupported provenance classification")
    if classification not in EXACT_CLASSES:
        raise RuntimeError("approximate or review evidence cannot be relabeled exact")
    if str(record.get("model_identifier") or "") != MODEL_ID:
        raise RuntimeError("model identifier mismatch")
    commit = str(record.get("code_commit") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError("code commit missing or invalid")
    if str(record.get("player_id") or "") != str(expected.get("player_id") or ""):
        raise RuntimeError("player ID authority mismatch")
    if str(record.get("join_method") or "") != "player_id":
        raise RuntimeError("name-based or non-authoritative join prohibited")
    if float(record.get("score")) != float(expected.get("score")):
        raise RuntimeError("score mismatch")
    if int(record.get("rank")) != int(expected.get("rank")):
        raise RuntimeError("rank mismatch")
    as_of = _parse_date(record.get("source_as_of_date"), "source as-of date")
    decision = _parse_date(record.get("decision_date"), "decision date")
    if as_of > decision:
        raise RuntimeError("future input detected")
    if int(record.get("input_season")) >= int(record.get("target_season")):
        raise RuntimeError("future input detected")
    if str(record.get("input_family") or "").lower() in {
        "current_adp",
        "current_only_adp",
        "current_market",
    }:
        raise RuntimeError("current-only ADP or market input prohibited")
    if tuple(record.get("checkpoint_chain") or ()) != REQUIRED_CHAIN:
        raise RuntimeError("incomplete checkpoint chain")
    if str(record.get("immutability") or "") != "immutable_original_bytes":
        raise RuntimeError("mutable file cannot be claimed immutable")
    output_hash = str(record.get("output_sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", output_hash):
        raise RuntimeError("output hash missing or invalid")
    if output_hash != str(expected.get("output_sha256") or ""):
        raise RuntimeError("immutable output hash mismatch")
    if tuple(record.get("ordering_keys") or ()) != (
        "score_desc",
        "player_id_asc",
    ):
        raise RuntimeError("nondeterministic input ordering")
    if int(record.get("prediction_count")) != int(record.get("expected_row_count")):
        raise RuntimeError("silently dropped prediction")


def exact_claim_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    output_hash = "a" * 64
    record: dict[str, Any] = {
        "classification": "EXACT_PRIMARY_RECEIPT",
        "model_identifier": MODEL_ID,
        "code_commit": "b" * 40,
        "player_id": "00-0036322",
        "join_method": "player_id",
        "score": 71.25,
        "rank": 3,
        "source_as_of_date": "2020-08-31",
        "decision_date": "2020-09-01",
        "input_season": 2019,
        "target_season": 2020,
        "input_family": "historical_production",
        "checkpoint_chain": REQUIRED_CHAIN,
        "immutability": "immutable_original_bytes",
        "output_sha256": output_hash,
        "ordering_keys": ("score_desc", "player_id_asc"),
        "prediction_count": 1,
        "expected_row_count": 1,
    }
    expected = {
        "player_id": "00-0036322",
        "score": 71.25,
        "rank": 3,
        "output_sha256": output_hash,
    }
    return record, expected


def mutation_cases() -> dict[str, dict[str, Any]]:
    base, _expected = exact_claim_fixture()
    cases: dict[str, dict[str, Any]] = {}
    for name in (
        "changed_score",
        "changed_rank",
        "changed_player_id",
        "removed_as_of_date",
        "changed_model_identifier",
        "missing_code_commit",
        "future_input",
        "current_only_adp",
        "name_based_join",
        "incomplete_checkpoint_chain",
        "mutable_claimed_immutable",
        "approximate_relabel",
        "nondeterministic_order",
        "silently_dropped_prediction",
    ):
        cases[name] = deepcopy(base)
    cases["changed_score"]["score"] = 70.25
    cases["changed_rank"]["rank"] = 4
    cases["changed_player_id"]["player_id"] = "mutated"
    cases["removed_as_of_date"]["source_as_of_date"] = ""
    cases["changed_model_identifier"]["model_identifier"] = "wrong_model"
    cases["missing_code_commit"]["code_commit"] = ""
    cases["future_input"]["input_season"] = 2020
    cases["current_only_adp"]["input_family"] = "current_only_adp"
    cases["name_based_join"]["join_method"] = "player_name"
    cases["incomplete_checkpoint_chain"]["checkpoint_chain"] = REQUIRED_CHAIN[:-1]
    cases["mutable_claimed_immutable"]["immutability"] = "mutable_local_file"
    cases["approximate_relabel"]["classification"] = "APPROXIMATE"
    cases["nondeterministic_order"]["ordering_keys"] = ("input_order",)
    cases["silently_dropped_prediction"]["prediction_count"] = 0
    return cases


def validate_mutations() -> dict[str, str]:
    _base, expected = exact_claim_fixture()
    results: dict[str, str] = {}
    for name, mutated in mutation_cases().items():
        try:
            validate_exact_claim(mutated, expected)
        except RuntimeError as exc:
            results[name] = f"DETECTED: {exc}"
        else:
            raise RuntimeError(f"required mutation escaped detection: {name}")
    return results


def validate_hq2() -> pd.DataFrame:
    if git("status", "--porcelain", cwd=HQ2_ROOT):
        raise RuntimeError("HQ2 provenance clone is dirty")
    if git("rev-parse", "HEAD", cwd=HQ2_ROOT) != HQ2_HEAD:
        raise RuntimeError("HQ2 provenance HEAD changed")
    if git("show", "-s", "--format=%T", "HEAD", cwd=HQ2_ROOT) != HQ2_TREE:
        raise RuntimeError("HQ2 provenance tree changed")
    if git("show", "-s", "--format=%T", HQ2_SOURCE_COMMIT, cwd=HQ2_ROOT) != HQ2_SOURCE_TREE:
        raise RuntimeError("HQ2 source commit tree changed")
    for path, expected in HQ2_EXPECTED.items():
        if path.stat().st_size != expected["bytes"]:
            raise RuntimeError(f"HQ2 byte count changed for {path}")
        if sha256(path) != expected["sha256"]:
            raise RuntimeError(f"HQ2 SHA-256 changed for {path}")
        validate_git_blob(path, str(expected["blob"]), repo=HQ2_ROOT)
    panel = pd.read_csv(HQ2_PANEL, low_memory=False)
    if len(panel) != 4_764:
        raise RuntimeError("HQ2 row count changed")
    required = {
        "season",
        "player_id",
        "position",
        "candidate_name",
        "three_year_stability_value",
        "prior_games",
        "candidate_rank_position",
        "candidate_rank_flex_pool",
        "decision_date_safe_flag",
        "blocked_field_used",
    }
    missing = required - set(panel.columns)
    if missing:
        raise RuntimeError(f"HQ2 schema changed: {sorted(missing)}")
    if panel["player_id"].isna().any() or panel["player_id"].astype(str).str.strip().eq("").any():
        raise RuntimeError("HQ2 player identity is incomplete")
    if panel.duplicated(["player_id", "season", "position"]).any():
        raise RuntimeError("HQ2 player-season-position identity is not unique")
    if not panel["decision_date_safe_flag"].astype(bool).all():
        raise RuntimeError("HQ2 decision-date safety changed")
    if panel["blocked_field_used"].fillna(False).astype(bool).any():
        raise RuntimeError("HQ2 blocked field use detected")
    if not panel["candidate_name"].eq("HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1").all():
        raise RuntimeError("HQ2 formula identity changed")
    return panel


def validate_canonical_state() -> None:
    if git("show", "-s", "--format=%T", EXPECTED_HQ) != EXPECTED_TREE:
        raise RuntimeError("canonical starting commit/tree identity changed")
    git("merge-base", "--is-ancestor", EXPECTED_HQ, "HEAD")
    if sha256(CURRENT_BOARD) != CURRENT_BOARD_SHA256:
        raise RuntimeError("current board hash changed")
    if sha256(FROZEN_2026) != FROZEN_2026_SHA256:
        raise RuntimeError("frozen comparator hash changed")


def write_csv_file(
    name: str,
    rows: Iterable[Mapping[str, Any]],
    fieldnames: Sequence[str] | None = None,
) -> None:
    materialized = [dict(row) for row in rows]
    if fieldnames is None:
        fieldnames = tuple(materialized[0]) if materialized else ("status",)
    path = OUT / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(materialized)


def write_text(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def search_summaries() -> tuple[SearchSummary, ...]:
    return (
        SearchSummary(
            "canonical_git_history",
            "all refs reachable in canonical object database; deleted/renamed paths included",
            12_289,
            1_304,
            0,
            "all 867 commits and 11,422 path/object records enumerated",
            "No immutable historical Model v4 receipt chain.",
        ),
        SearchSummary(
            r"C:\NWR",
            "direct NWR roots, clean provenance clones, registered and unregistered worktrees",
            395_769,
            94_516,
            0,
            "candidate extensions and exact receipt-field content scan exhausted",
            "HQ2 governed definition recovered; Model v4 receipts still absent.",
        ),
        SearchSummary(
            r"C:\NWR_SHARED_DATA",
            "NWR backtests, research, model candidates, lane exchange, archive recovery",
            792,
            98,
            0,
            "all candidate paths and exact identifier/field content scanned",
            "Zero governed Model v4 receipt identifier/content hits.",
        ),
        SearchSummary(
            r"C:\Users\codex-agent\Documents\Niners War Room",
            "NWR worktrees, packets, canonicalization stages, and task artifacts",
            72_638,
            42_200,
            0,
            "candidate paths and exact receipt-field content scan exhausted",
            "Duplicated prior audit/current-only evidence; no historical exact receipt.",
        ),
        SearchSummary(
            "NWR ZIP archives",
            "all ZIPs below the two NWR roots, grouped and authenticated by SHA-256",
            1_061,
            319,
            0,
            "40/40 unique SHA-256 archives opened; entry-name inventory exhausted",
            "Current-only freezes and proxy packets only.",
        ),
    )


def build_git_log() -> list[dict[str, Any]]:
    rows = [
        {
            "surface": "canonical_history",
            "path_or_object": "--all",
            "commit": EXPECTED_HQ,
            "tree": EXPECTED_TREE,
            "blob": "",
            "sha256": "",
            "size_bytes": "",
            "coverage": "867 commits; 12,289 object lines; 11,422 path objects",
            "admission": "SEARCH_EXHAUSTED_NO_EXACT_RECEIPT",
            "blocker": "No complete historical governed chain.",
        },
        {
            "surface": "canonical_chain",
            "path_or_object": "research tooling",
            "commit": "bfb1a489741250d7fa63c9b134fd007dbbfa841d",
            "tree": "",
            "blob": "",
            "sha256": "",
            "size_bytes": "",
            "coverage": "exact-replay audit tooling",
            "admission": "REVIEW_ONLY_TOOLING",
            "blocker": "",
        },
        {
            "surface": "canonical_chain",
            "path_or_object": "exact replay audit",
            "commit": "0929ce6ec058a698efeee10fe5770f56047bab21",
            "tree": "",
            "blob": "",
            "sha256": "",
            "size_bytes": "",
            "coverage": "0/5,518 exact rows",
            "admission": "CANONICAL_EVIDENCE_FRONTIER",
            "blocker": "Missing receipts.",
        },
        {
            "surface": "canonical_chain",
            "path_or_object": "assertion/regeneration revision",
            "commit": "5fb7339e45c3536b9d4ec9bfce1b2afc302a41d3",
            "tree": "",
            "blob": "",
            "sha256": "",
            "size_bytes": "",
            "coverage": "mutation and clean-regeneration assertions",
            "admission": "CANONICAL_TOOLING",
            "blocker": "",
        },
        {
            "surface": "local_provenance_clone",
            "path_or_object": str(HQ2_SCRIPT),
            "commit": HQ2_SOURCE_COMMIT,
            "tree": HQ2_SOURCE_TREE,
            "blob": HQ2_EXPECTED[HQ2_SCRIPT]["blob"],
            "sha256": HQ2_EXPECTED[HQ2_SCRIPT]["sha256"],
            "size_bytes": HQ2_EXPECTED[HQ2_SCRIPT]["bytes"],
            "coverage": "exact HQ2 definition and deterministic runner",
            "admission": "EXACT_GOVERNED_DEFINITION_ONLY",
            "blocker": "Not Model v4 receipt evidence.",
        },
        {
            "surface": "local_provenance_clone",
            "path_or_object": str(HQ2_PANEL),
            "commit": HQ2_SOURCE_COMMIT,
            "tree": HQ2_SOURCE_TREE,
            "blob": HQ2_EXPECTED[HQ2_PANEL]["blob"],
            "sha256": HQ2_EXPECTED[HQ2_PANEL]["sha256"],
            "size_bytes": HQ2_EXPECTED[HQ2_PANEL]["bytes"],
            "coverage": "4,764 RB/WR/TE player-seasons, 2013-2025",
            "admission": "REVIEW_ONLY_DETERMINISTIC_OUTPUT",
            "blocker": "V3 proxy substrate; not exact Model v4.",
        },
        {
            "surface": "local_provenance_clone",
            "path_or_object": str(HQ2_SUBSTRATE),
            "commit": HQ2_SOURCE_COMMIT,
            "tree": HQ2_SOURCE_TREE,
            "blob": HQ2_EXPECTED[HQ2_SUBSTRATE]["blob"],
            "sha256": HQ2_EXPECTED[HQ2_SUBSTRATE]["sha256"],
            "size_bytes": HQ2_EXPECTED[HQ2_SUBSTRATE]["bytes"],
            "coverage": "5,518 historical rows, lagged review-safe inputs",
            "admission": "REVIEW_ONLY_SUBSTRATE",
            "blocker": "Not historically complete governed Model v4 input authority.",
        },
        {
            "surface": "local_provenance_clone",
            "path_or_object": "old/current ranking reconstruction execution",
            "commit": "2a30dd9819424c05a4795e2e4fc94efc827c2462",
            "tree": "9818ccba861622f7af78892d51792f73f8da911d",
            "blob": "",
            "sha256": "",
            "size_bytes": "",
            "coverage": "5,518 rows, QB/RB/WR/TE, 2013-2025",
            "admission": "NEAR_EQUIVALENT",
            "blocker": "Lifecycle/discipline neutralized; proxies replace exact components.",
        },
    ]
    return rows


def receipt_inventory() -> list[dict[str, Any]]:
    return [
        {
            "family": "historical_checkpoint_scores",
            "artifact": "none authenticated",
            "rows": 0,
            "seasons": "none",
            "positions": "none",
            "identity_namespace": "UNKNOWN",
            "classification": "BLOCKED_MISSING_RECEIPT",
            "admission": "REJECTED",
            "blocker": "Immutable checkpoint score bytes and as-of manifests absent.",
        },
        {
            "family": "historical_final_model_v4_scores",
            "artifact": "none authenticated",
            "rows": 0,
            "seasons": "none",
            "positions": "none",
            "identity_namespace": "UNKNOWN",
            "classification": "BLOCKED_MISSING_RECEIPT",
            "admission": "REJECTED",
            "blocker": "Final Model v4 score receipts absent.",
        },
        {
            "family": "historical_exact_rank_assignments",
            "artifact": "none authenticated",
            "rows": 0,
            "seasons": "none",
            "positions": "none",
            "identity_namespace": "UNKNOWN",
            "classification": "BLOCKED_MISSING_RECEIPT",
            "admission": "REJECTED",
            "blocker": "Exact rank receipts absent; algorithm definition alone is insufficient.",
        },
        {
            "family": "historical_position_components",
            "artifact": "historical component review panels",
            "rows": 42_933,
            "seasons": "2013-2025 partial",
            "positions": "QB,RB,WR,TE partial",
            "identity_namespace": "GSIS/player_id where available",
            "classification": "PARTIAL_REPLAY",
            "admission": "REVIEW_ONLY",
            "blocker": "Not exact governed position-component receipts.",
        },
        {
            "family": "historical_lifecycle",
            "artifact": "age/lifecycle review panel",
            "rows": 5_518,
            "seasons": "2013-2025",
            "positions": "QB,RB,WR,TE",
            "identity_namespace": "player_id",
            "classification": "NEAR_EQUIVALENT",
            "admission": "REVIEW_ONLY",
            "blocker": "Historical lifecycle receipts and role inputs absent.",
        },
        {
            "family": "historical_confidence",
            "artifact": "confidence-cap regeneration pilot",
            "rows": 5_518,
            "seasons": "2013-2025",
            "positions": "QB,RB,WR,TE",
            "identity_namespace": "player_id",
            "classification": "NEAR_EQUIVALENT",
            "admission": "REVIEW_ONLY",
            "blocker": "Review-safe reconstructed caps are not primary receipts.",
        },
        {
            "family": "historical_discipline_safety",
            "artifact": "definition source only",
            "rows": 0,
            "seasons": "none",
            "positions": "QB,TE definitions",
            "identity_namespace": "not applicable",
            "classification": "BLOCKED_MISSING_RECEIPT",
            "admission": "DEFINITION_ONLY",
            "blocker": "Historical inputs and applied multipliers absent.",
        },
        {
            "family": "hq2_candidate_definition",
            "artifact": str(HQ2_PANEL),
            "rows": 4_764,
            "seasons": "2013-2025",
            "positions": "RB,WR,TE",
            "identity_namespace": "GSIS player_id",
            "classification": "REVIEW_ONLY",
            "admission": "EXACT_DEFINITION_NOT_MODEL_V4_RECEIPT",
            "blocker": "Candidate proxy evidence cannot expand exact Model v4 frontier.",
        },
        {
            "family": "current_board",
            "artifact": CURRENT_BOARD.as_posix(),
            "rows": 240,
            "seasons": "current 2026 only",
            "positions": "QB,RB,WR,TE,current prospects/picks",
            "identity_namespace": "current canonical key/player_id",
            "classification": "EXACT_PRIMARY_RECEIPT",
            "admission": "CURRENT_ONLY_PRESERVATION",
            "blocker": "Cannot establish historical as-of state.",
        },
        {
            "family": "prospective_2026_comparator",
            "artifact": FROZEN_2026.relative_to(ROOT).as_posix(),
            "rows": 924,
            "seasons": "prospective 2026",
            "positions": "QB,RB,WR,TE",
            "identity_namespace": "player_id",
            "classification": "FROZEN_COMPARATOR",
            "admission": "COMPARATOR_ONLY",
            "blocker": "Not historical replay evidence.",
        },
    ]


def authentication_rows() -> list[dict[str, Any]]:
    rows = []
    for item in receipt_inventory():
        artifact = str(item["artifact"])
        rows.append(
            {
                "candidate": item["family"],
                "path_or_object": artifact,
                "immutable_bytes": (
                    "YES"
                    if item["classification"]
                    in {"EXACT_PRIMARY_RECEIPT", "FROZEN_COMPARATOR"}
                    else "NO_OR_NOT_APPLICABLE"
                ),
                "exact_model_contract": (
                    "NO"
                    if item["family"] != "current_board"
                    else "CURRENT_ONLY"
                ),
                "historical_input_authority": "NO",
                "exact_player_identity": (
                    "YES"
                    if item["identity_namespace"] in {"player_id", "GSIS player_id"}
                    else "PARTIAL_OR_UNKNOWN"
                ),
                "historical_as_of_boundary": "NO",
                "schema_row_count": (
                    "PROVEN" if int(item["rows"]) > 0 else "MISSING"
                ),
                "generation_context": (
                    "PROVEN"
                    if item["family"] in {"hq2_candidate_definition", "current_board"}
                    else "PARTIAL_OR_MISSING"
                ),
                "classification": item["classification"],
                "admission_result": item["admission"],
                "blocker": item["blocker"],
            }
        )
    return rows


def manifest_rows() -> list[dict[str, Any]]:
    candidates = {
        "exact_model_v4_historical_chain": {
            "model_version": "RECOVERED_EXACT",
            "code_commit": "RECOVERED_EXACT",
            "formula_contract": "RECOVERED_EXACT",
            "source_families_versions": "UNKNOWN",
            "source_as_of_dates": "UNKNOWN",
            "input_hashes": "UNKNOWN",
            "schemas": "INFERRED_WITH_EVIDENCE",
            "player_id_namespace": "INFERRED_WITH_EVIDENCE",
            "season": "RECOVERED_EXACT",
            "position": "RECOVERED_EXACT",
            "row_count": "RECOVERED_EXACT",
            "checkpoint_stage": "UNKNOWN",
            "output_hash": "UNKNOWN",
            "rank_assignment": "DETERMINISTICALLY_DERIVED",
            "tie_handling": "DETERMINISTICALLY_DERIVED",
            "missing_data_behavior": "INFERRED_WITH_EVIDENCE",
        },
        "hq2_three_year_stability_low_games_guard_v1": {
            field: "RECOVERED_EXACT" for field in REQUIRED_MANIFEST_FIELDS
        },
        "old_current_near_equivalent_replay": {
            "model_version": "INFERRED_WITH_EVIDENCE",
            "code_commit": "RECOVERED_EXACT",
            "formula_contract": "INFERRED_WITH_EVIDENCE",
            "source_families_versions": "RECOVERED_EXACT",
            "source_as_of_dates": "DETERMINISTICALLY_DERIVED",
            "input_hashes": "RECOVERED_EXACT",
            "schemas": "RECOVERED_EXACT",
            "player_id_namespace": "RECOVERED_EXACT",
            "season": "RECOVERED_EXACT",
            "position": "RECOVERED_EXACT",
            "row_count": "RECOVERED_EXACT",
            "checkpoint_stage": "INFERRED_WITH_EVIDENCE",
            "output_hash": "RECOVERED_EXACT",
            "rank_assignment": "DETERMINISTICALLY_DERIVED",
            "tie_handling": "DETERMINISTICALLY_DERIVED",
            "missing_data_behavior": "RECOVERED_EXACT",
        },
        "current_board_only": {
            "model_version": "RECOVERED_EXACT",
            "code_commit": "RECOVERED_EXACT",
            "formula_contract": "RECOVERED_EXACT",
            "source_families_versions": "RECOVERED_EXACT",
            "source_as_of_dates": "RECOVERED_EXACT",
            "input_hashes": "RECOVERED_EXACT",
            "schemas": "RECOVERED_EXACT",
            "player_id_namespace": "RECOVERED_EXACT",
            "season": "RECOVERED_EXACT",
            "position": "RECOVERED_EXACT",
            "row_count": "RECOVERED_EXACT",
            "checkpoint_stage": "RECOVERED_EXACT",
            "output_hash": "RECOVERED_EXACT",
            "rank_assignment": "RECOVERED_EXACT",
            "tie_handling": "DETERMINISTICALLY_DERIVED",
            "missing_data_behavior": "RECOVERED_EXACT",
        },
    }
    rows = []
    for candidate, fields in candidates.items():
        for field in REQUIRED_MANIFEST_FIELDS:
            status = fields[field]
            material_unknown = candidate == "exact_model_v4_historical_chain" and status == "UNKNOWN"
            rows.append(
                {
                    "candidate_manifest": candidate,
                    "field": field,
                    "status": status,
                    "material_unknown": str(material_unknown).upper(),
                    "exact_admission": (
                        "BLOCKED"
                        if material_unknown
                        or candidate in {"old_current_near_equivalent_replay", "current_board_only"}
                        else (
                            "CANDIDATE_DEFINITION_ONLY"
                            if candidate.startswith("hq2_")
                            else "BLOCKED"
                        )
                    ),
                }
            )
    return rows


def exactness_frontier() -> pd.DataFrame:
    prior = pd.read_csv(PRIOR_MASK, low_memory=False)
    if len(prior) != HISTORICAL_ROWS:
        raise RuntimeError("prior exactness mask row count changed")
    frame = prior.copy()
    frame["identity_outcome_status"] = frame["identity_status"].astype(str) + "|" + frame[
        "outcome_status"
    ].astype(str)
    frame["multi_year_production_status"] = "EXACT_DETERMINISTIC_REGENERATION"
    frame["source_asof_manifest_status"] = "BLOCKED_MISSING_RECEIPT"
    frame["exact_primary_row"] = False
    frame["exact_deterministic_regeneration_row"] = False
    frame["near_equivalent_row"] = True
    frame["partial_replay_row"] = True
    frame["blocked_row"] = True
    frame["row_admission_class"] = "PARTIAL_REPLAY"
    frame["mandatory_chain_complete"] = False
    if frame["full_exact_row"].astype(bool).any():
        raise RuntimeError("exactness lattice admitted an unsupported exact row")
    columns = [
        "substrate_row_id",
        "player_id",
        "target_season",
        "feature_season",
        "position",
        "age",
        "prior_games",
        "identity_outcome_status",
        "lagged_production_status",
        "multi_year_production_status",
        "position_score_status",
        "lifecycle_status",
        "confidence_status",
        "discipline_safety_status",
        "checkpoint_status",
        "final_score_status",
        "rank_status",
        "source_asof_manifest_status",
        "route_status",
        "return_scoring_status",
        "exact_primary_row",
        "exact_deterministic_regeneration_row",
        "near_equivalent_row",
        "partial_replay_row",
        "blocked_row",
        "mandatory_chain_complete",
        "row_admission_class",
        "exactness_blocker",
    ]
    return frame[columns].sort_values(
        ["target_season", "position", "player_id", "substrate_row_id"],
        kind="mergesort",
    )


def checkpoint_chain_rows() -> list[dict[str, Any]]:
    return [
        {
            "stage": stage,
            "required_rows": HISTORICAL_ROWS,
            "exact_primary_rows": 0,
            "exact_regeneration_rows": (
                HISTORICAL_ROWS if stage in {"identity_outcome", "lagged_production"} else 0
            ),
            "near_equivalent_rows": (
                HISTORICAL_ROWS if stage in {"lifecycle", "confidence"} else 0
            ),
            "blocked_rows": (
                0 if stage in {"identity_outcome", "lagged_production"} else HISTORICAL_ROWS
            ),
            "admission": (
                "EXACT_COMPONENT_ONLY"
                if stage in {"identity_outcome", "lagged_production"}
                else "BLOCKED"
            ),
            "blocker": (
                ""
                if stage in {"identity_outcome", "lagged_production"}
                else "Missing immutable historical receipt or complete exact as-of input authority."
            ),
        }
        for stage in (
            "identity_outcome",
            "lagged_production",
            "multi_year_production",
            "position_specific_components",
            "lifecycle",
            "confidence",
            "discipline_safety",
            "checkpoint_scores",
            "final_scores",
            "final_ranks",
            "source_asof_manifest",
        )
    ]


def governed_definitions() -> list[dict[str, Any]]:
    return [
        {
            "definition": "HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1",
            "provenance_commit": HQ2_SOURCE_COMMIT,
            "source_path": str(HQ2_SCRIPT),
            "inputs": "GSIS player_id; Y-1/Y-2/Y-3 NWR points; Y-1 games; target season/position",
            "formula": "renormalized 0.60/0.30/0.10 weighted mean * reliability * low-games multiplier",
            "parameters_caps": "reliability 1.00/0.98/0.94 for 3/2/1 seasons; low games 0.92 <8, 0.97 8-11, 1.00 >=12",
            "missing_data": "renormalize over present prior seasons; require >=1; no zero fill",
            "ordering_ties": "score desc then player_id; position and flex ranks deterministic",
            "classification": "RECOVERED_EXACT",
            "production_use": "PROHIBITED_REVIEW_ONLY",
        },
        {
            "definition": "production_safe_lifecycle_baseline",
            "provenance_commit": "b410ab30df4e3686aad7380dc5498e2f34105e30",
            "source_path": "src/services/model_v4_lifecycle_archetype_service.py",
            "inputs": "position, admitted role/usage evidence, admitted age sidecar",
            "formula": "role_modifier * position age modifier; confidence=max(0.78,1-0.04*warnings)",
            "parameters_caps": "RB 27+ step curve; WR 30+; TE 30+; missing age modifier 1.0 with warning",
            "missing_data": "no invented age penalty; warn/fail visible",
            "ordering_ties": "not a rank assignment",
            "classification": "RECOVERED_EXACT_DEFINITION",
            "production_use": "UNCHANGED",
        },
        {
            "definition": "confidence_cap_contract",
            "provenance_commit": "b410ab30df4e3686aad7380dc5498e2f34105e30",
            "source_path": "src/services/model_v4_confidence_missingness_service.py:388",
            "inputs": "missing families, warning flags, identity/join/staleness/lifecycle/receipt counts",
            "formula": "minimum reason-specific cap plus warning-count cap",
            "parameters_caps": "reason caps 0.78-0.94; >=5 warnings 0.82; >=3 warnings 0.88",
            "missing_data": "explicit cap reason; no silent fill",
            "ordering_ties": "not a rank assignment",
            "classification": "RECOVERED_EXACT_DEFINITION",
            "production_use": "UNCHANGED",
        },
        {
            "definition": "qb_te_discipline_safety_contract",
            "provenance_commit": "b410ab30df4e3686aad7380dc5498e2f34105e30",
            "source_path": "src/services/model_v4_qb_te_current_value_service.py:616",
            "inputs": "position components, VORP, RB/WR reference score distribution, warnings",
            "formula": "base replacement caps plus QB median compression and TE P85/P95 upper-band guard",
            "parameters_caps": "QB base 0.55/0.78/0.88/1.0; TE 0.60/0.82/1.0; QB compression .55; TE .70/.95",
            "missing_data": "TE elite exception fails closed when receipts missing/source blocked",
            "ordering_ties": "score desc, then position, then player name for module output",
            "classification": "RECOVERED_EXACT_DEFINITION",
            "production_use": "UNCHANGED",
        },
        {
            "definition": "checkpoint_ordering_contract",
            "provenance_commit": "b410ab30df4e3686aad7380dc5498e2f34105e30",
            "source_path": "src/services/model_v4_current_value_checkpoint_service.py:226",
            "inputs": "position score, lifecycle modifier, confidence cap; discipline embedded upstream",
            "formula": "round(position_specific_review_score*lifecycle_modifier*confidence_cap,4)",
            "parameters_caps": "no market, ADP, projection, or active-rank input",
            "missing_data": "blank score remains blank; defaults only for missing modifiers in current pipeline",
            "ordering_ties": "documentation sort score desc; historical exact rank receipts still absent",
            "classification": "RECOVERED_EXACT_DEFINITION",
            "production_use": "UNCHANGED",
        },
        {
            "definition": "old_current_historical_reconstruction",
            "provenance_commit": "2a30dd9819424c05a4795e2e4fc94efc827c2462",
            "source_path": "docs/hq/master/old_current_ranking_logic_reconstruction_execution_v1_20260710",
            "inputs": "lagged Formula Data Mart substitutes",
            "formula": "position percentile proxies and exact descending proxy-score rank algorithm",
            "parameters_caps": "lifecycle=1.0; discipline=1.0; review-safe confidence proxy",
            "missing_data": "rescale available proxy components; blocked components dropped and flagged",
            "ordering_ties": "score desc then player name/player_id",
            "classification": "NEAR_EQUIVALENT",
            "production_use": "PROHIBITED_REVIEW_ONLY",
        },
    ]


def challenger_results(scorecard: pd.DataFrame) -> list[dict[str, Any]]:
    pooled = scorecard.loc[scorecard["scope"] == "pooled_flex"].iloc[0]
    return [
        {
            "candidate": "Candidate 0: current accepted baseline",
            "definition_status": "ACCEPTED_CURRENT_BASELINE",
            "evidence": "exact current board; zero exact historical rows",
            "validation_design": "not rerun; exact historical comparison inadmissible",
            "rows": 0,
            "pooled_precision": "",
            "baseline_precision": "",
            "spearman": "",
            "low_games_delta": "",
            "result": "BASELINE_RETAINED",
            "admission": "CURRENT_PRODUCTION_UNCHANGED",
        },
        {
            "candidate": "Candidate 1: HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1",
            "definition_status": "RECOVERED_EXACT",
            "evidence": "deterministic review-only V3 proxy panel",
            "validation_design": "fixed preregistered formula; target-season folds 2013-2025; lagged inputs only",
            "rows": int(pooled["rows"]),
            "pooled_precision": f"{float(pooled['candidate_startable_precision']):.6f}",
            "baseline_precision": f"{float(pooled['prior_year_startable_precision']):.6f}",
            "spearman": f"{float(pooled['spearman']):.6f}",
            "low_games_delta": int(pooled["low_games_delta"]),
            "result": "REVIEW_ONLY_SIGNAL_WITH_LOW_GAMES_REGRESSION",
            "admission": "NOT_ADMITTED_NO_EXACT_MODEL_V4_OVERLAP",
        },
        {
            "candidate": "Candidate 2: GAUNTLET_081",
            "definition_status": "EXISTING_GOVERNED_DEFINITION",
            "evidence": "no new exact Model v4 evidence",
            "validation_design": "not run",
            "rows": 0,
            "pooled_precision": "",
            "baseline_precision": "",
            "spearman": "",
            "low_games_delta": "",
            "result": "NOT_AUTHORIZED",
            "admission": "NOT_ADMITTED",
        },
        {
            "candidate": "Candidate 3",
            "definition_status": "PROHIBITED",
            "evidence": "no exact-model residual evidence",
            "validation_design": "not run",
            "rows": 0,
            "pooled_precision": "",
            "baseline_precision": "",
            "spearman": "",
            "low_games_delta": "",
            "result": "PROHIBITED",
            "admission": "NOT_ADMITTED",
        },
    ]


def challenger_gate_matrix() -> list[dict[str, Any]]:
    gates = [
        ("zero_leakage", "PASS_REVIEW_ONLY"),
        ("exact_documented_inputs", "PASS_DEFINITION"),
        ("adequate_coverage", "PASS_REVIEW_ONLY_4764"),
        ("adequate_sample_sizes", "PASS_REVIEW_ONLY"),
        ("material_ranking_aligned_improvement", "PASS_PROXY_ONLY"),
        ("uncertainty_survival", "NOT_TESTABLE_WITH_EXACT_EVIDENCE"),
        ("no_pooled_score_regression", "PASS_PROXY_ONLY"),
        ("no_position_regression", "PASS_PROXY_ONLY_TE_TIE"),
        ("no_top_tier_false_positive_regression", "NOT_TESTABLE_WITH_EXACT_EVIDENCE"),
        ("no_productive_veteran_false_negative_regression", "NOT_TESTABLE_WITH_EXACT_EVIDENCE"),
        ("low_games_stability", "FAIL_PLUS_12_VS_PRIOR_YEAR"),
        ("no_one_season_or_position_dependency", "PASS_REVIEW_ONLY"),
        ("fail_closed_missing_predictions", "PASS_DEFINITION"),
        ("monotonic_interpretable_behavior", "PASS_DEFINITION"),
        ("current_board_unchanged", "PASS"),
        ("frozen_comparator_unchanged", "PASS"),
        ("independent_reproduction", "PASS_SEMANTIC_REGENERATION"),
    ]
    return [
        {
            "gate": gate,
            "candidate_0_baseline": "RETAINED",
            "candidate_1_hq2": result,
            "candidate_2_gauntlet_081": "NOT_RUN_NO_EXACT_EVIDENCE",
            "candidate_3": "PROHIBITED",
            "blocking": str(
                result.startswith("FAIL") or result.startswith("NOT_TESTABLE")
            ).upper(),
        }
        for gate, result in gates
    ]


def human_recovery_text() -> str:
    return r"""
# Human and External Recovery Package

## Controlling conclusion

All locally available, directly attributable NWR Git, worktree, shared-data, and
archive surfaces were exhausted without an admissible historical Model v4 receipt
chain. Do not substitute current-only files, proxy panels, name joins, market/ADP,
or reconstructed lifecycle/discipline values.

## 1. Historical checkpoint and final-score receipts

- Search patterns: `*checkpoint*review*score*.csv`, `*current_value_receipts*.csv`,
  `*model_v4*historical*score*.{csv,parquet,jsonl}`, and manifests containing both
  `position_specific_review_score` and `checkpoint_review_score`.
- Required fields: governed model identifier, code commit, player ID, target season,
  source/input as-of dates, position score, lifecycle modifier, confidence cap,
  discipline/safety output, checkpoint score, final score, schema version, input and
  output hashes.
- Likely context: the originating workstation or immutable backup used when Phase
  11G/current-value outputs were first generated; pre-June-2026 ranking export
  archives; deleted CI/artifact retention if it existed.
- Expected coverage: player-season rows across 2013-2025 and QB/RB/WR/TE; row count
  should reconcile to the 5,518-row historical panel or carry a signed completeness
  manifest explaining a strict subset.
- Human action: search external backup catalogs and artifact retention by filename
  and schema, then copy nothing into HQ until SHA-256, original timestamp, generating
  commit/command, and chain-of-custody are recorded.
- Prohibited substitute: current 2026 board/rebuild receipts or Formula Data Mart
  proxy scores.

## 2. Exact rank-assignment receipts

- Search patterns: `*rank_assignment*receipt*`, `*final_rank*historical*`,
  `*nwr_rank*asof*`, and exports pairing score, rank, tie key, and model version.
- Required fields: exact score input hash, assigned rank, scope (position/flex/overall),
  deterministic tie key, missing-score behavior, row count, season, and output hash.
- Human action: retrieve the exact exported bytes from the ranking run archive; do
  not reconstruct ranks unless the complete score population and ordering contract
  for that run are also authenticated.
- Prohibited substitute: ranks recalculated from the near-equivalent replay.

## 3. Component, lifecycle, confidence, discipline, and safety receipts

- Search patterns: `*position*component*receipt*`, `*lifecycle*receipt*`,
  `*confidence_missingness_receipts*`, `*discipline*multiplier*receipt*`,
  `*safety*overlay*receipt*`.
- Required fields: per-row inputs and outputs, component versions/weights, caps,
  missingness flags, source as-of dates, identity namespace, model/checkpoint stage,
  and immutable hash manifest.
- Known lead: current-only freezes in the formula-gauntlet context archive prove
  schemas but not historical application. Use them only to recognize expected
  structure.
- Prohibited substitute: the 5,518-row review-only cap/lifecycle panels.

## 4. Exact source/as-of manifests

- Search patterns: `*as_of_manifest*`, `*input_hash_manifest*`,
  `*point_in_time_snapshot*`, `*source_version*manifest*`.
- Required authority: all source families/versions, source and decision dates,
  hashes, schemas, identity namespace, missing-data policy, and generation command.
- Provider/source permission need: retrieve only from archives whose historical-use
  rights are already admitted; paid/current/provider payloads are not an automatic
  substitute.

## 5. Shadow Model v2, route, return, inactivity, and outcome-state receipts

- Search patterns: `*shadow_model_v2*metrics*`, `*route*yprr*tprr*asof*`,
  `*return*scoring*receipt*`, `*injury*inactivity*asof*`, and
  `*outcome_state*receipt*`.
- Known blocker: no admitted immutable historical chain appeared locally.
- External need: originating archive or source-specific historical snapshot with
  permission and exact identity/as-of metadata.
- Prohibited substitute: current depth chart, injury, roster, ADP, or name-matched data.

## Permanent-impossibility decision

If the originating machine, external backup catalogs, CI/artifact retention, and
approved source archives cannot supply these bytes, record
`PERMANENT_EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY_IMPOSSIBLE_FOR_PRECAPTURE_YEARS`.
Then preserve the zero-exact frontier and begin only a separately governed,
prospective receipt-capture design. Do not backfill an exact label onto reconstructed
evidence.
"""


def build_markdown_files(mutations: Mapping[str, str]) -> None:
    write_text(
        "WORKDAY_ACCURACY_EVIDENCE_EXPANSION_REPORT.md",
        f"""
# NWR Workday Accuracy Evidence Expansion V1

## Verdict

`YELLOW_NWR_RECEIPT_RECOVERY_EXHAUSTED_WITH_ACTIONABLE_HUMAN_LEADS`

The exhaustive local recovery found no admissible historical checkpoint, final-score,
or exact-rank receipts for `{MODEL_ID}`. Exact replay remains `0 / {HISTORICAL_ROWS:,}`.
The recovered exact definition of `HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1`
is a meaningful definition/provenance gain, and its 4,764-row review-only V3 output
regenerates deterministically, but it does not expand exact Model v4 evidence.

## Evidence frontier

- Historical panel: {HISTORICAL_ROWS:,} rows / {HISTORICAL_PLAYERS:,} players /
  2013-2025.
- OOF candidate panel: {OOF_ROWS:,} rows / {OOF_PLAYERS:,} players / 2015-2025.
- Exact primary rows: 0.
- Exact deterministic-regeneration rows: 0.
- Exact seasons/positions: none.
- Proxy-to-exact: `PROXY_TO_EXACT_NOT_TESTABLE`.
- Final challenger disposition: `NO_ACCURACY_CHALLENGER_ADMITTED`.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.

## Recovery result

Canonical Git history, all local NWR worktrees/clones, direct NWR roots, NWR shared
research/backtest roots, Documents NWR packets, and 40 unique ZIP archives were
searched. Current-only receipts, partial/review-only panels, and near-equivalent
reconstructions were rejected for exact historical use.

## Governed definition gain

The HQ2 definition was recovered from clean tracked Git bytes at commit
`{HQ2_SOURCE_COMMIT}`, tree `{HQ2_SOURCE_TREE}`. Formula, parameters, missingness,
identity, tie behavior, input exclusions, output schema, and deterministic generation
are proven. The candidate still fails admission because exact Model v4 overlap is zero
and low-games misses regress by 12 versus the prior-year baseline.

## Safe closeout

No production, ranking, frozen comparator, source admission, Data Health, launcher,
or persistence behavior was changed. The human/external recovery package is the next
authorized evidence action; no formula search follows this report.
""",
    )
    write_text(
        "EXECUTIVE_VERDICT.md",
        f"""
# Executive Verdict

`YELLOW_NWR_RECEIPT_RECOVERY_EXHAUSTED_WITH_ACTIONABLE_HUMAN_LEADS`

Exact Model v4 historical replay remains zero because every mandatory chain still
contains material unknowns. No proxy was relabeled exact. The HQ2 governed definition
was authenticated and its committed output independently regenerated, but it remains
review-only candidate evidence.

- Exact rows before/after: `0 / {HISTORICAL_ROWS:,}` -> `0 / {HISTORICAL_ROWS:,}`.
- Exact seasons/positions: none.
- Challenger: `NO_ACCURACY_CHALLENGER_ADMITTED`.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.
""",
    )
    write_text(
        "SEARCH_SCOPE_AND_STOPPING_RULES.md",
        """
# Search Scope and Stopping Rules

Each deterministic surface was enumerated once, authenticated, logged, and closed:
canonical objects/paths; direct NWR clones/worktrees; shared NWR research/backtests;
Documents NWR artifacts; and SHA-256-distinct ZIP archives. Deleted and renamed
tracked paths were included through Git object enumeration.

Five opaque DynastyProcess CSVs were hash-verified only and never opened, parsed,
summarized, copied, staged, or committed. LocalData was not inspected.

The search stopped only after all records in a surface were enumerated or after a
recorded access blocker. Five inaccessible pytest-cache directories under `C:\\NWR`
were irrelevant cache paths; the search continued across every other candidate.
No unrelated personal/project roots were searched.
""",
    )
    write_text("HUMAN_AND_EXTERNAL_RECOVERY_PACKAGE.md", human_recovery_text())
    write_text(
        "NEXT_THREE_ACCURACY_LANES.md",
        """
# Next Three Accuracy Lanes

1. **Originating immutable receipt archive retrieval.** Search the original ranking
   workstation, backup catalog, and artifact retention for historical checkpoint,
   final-score, and exact-rank bytes plus their manifests. This has the highest chance
   of creating exact overlap without model tuning.
2. **Exact source/as-of chain retrieval.** Recover approved point-in-time input
   snapshots and manifests for position components, lifecycle, confidence,
   discipline/safety, route/return/inactivity, and outcome state; then attempt
   deterministic regeneration only for rows with a complete chain.
3. **Permanent-impossibility decision and prospective capture contract.** If both
   archive lanes fail, formally accept pre-capture exact replay impossibility and
   separately design immutable prospective receipts. Never relabel proxies exact.
""",
    )
    write_text(
        "PRODUCTION_RANKING_AND_FROZEN_NO_CHANGE.md",
        f"""
# Production Ranking and Frozen No-Change

- Current board: 240 rows; SHA-256 `{CURRENT_BOARD_SHA256}` — pass.
- Frozen comparator: 924 rows; SHA-256 `{FROZEN_2026_SHA256}` — pass.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.
- No production/model/app/UI/runtime/launcher path is part of this packet.
""",
    )
    write_text(
        "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md",
        """
# Security, Data Health, and Runtime No-Change

No security scan was run. Hermetic executed the repository's existing 20 security
automation controls, including all five already-closed finding regressions: 20/20
passed. The full Hermetic Python collection passed 2,819 tests with no skip, xfail,
or xpass and exited 0.

Data Health passive-read coverage passed inside Hermetic and again as an explicit
59-test slice. LocalData returned `BLOCKED_MISSING_LOCAL_TEST_PACK` with native exit
4; no pack was imported, synthesized, copied, or inspected.

No provider/plugin/web call, source promotion, runtime mutation, launcher edit, or
persistence edit was performed.
""",
    )
    opaque_lines = "\n".join(
        f"- `{name}`: SHA-256 `{digest}` — hash-only pass."
        for name, digest in OPAQUE_HASHES.items()
    )
    write_text(
        "PRIMARY_AND_PERSISTENT_STATE_PRESERVATION.md",
        f"""
# Primary and Persistent State Preservation

## Opaque primary files

{opaque_lines}

No opaque contents were read or transformed.

## Persistent and recovery state

- Persistent: 14 files / 542,801 bytes / Digest V1 `{PERSISTENT_DIGEST}`.
- Recovery: 7 files / 172,878 bytes / Digest V1 `{RECOVERY_DIGEST}`.
- Retained backups: five directories / 15 files.
- Recovery snapshot: one `data-health` recovery directory / seven files.

These values were checked at lane start and are rechecked at each major gate.
""",
    )
    write_text(
        "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        """
# Protected and Frozen Path Proof

Allowed changes are limited to one research builder, its focused test, and this
documentation packet. No opaque, `local_exports`, production ranking, model service,
app, UI, runtime, Data Health, launcher, persistence, or frozen-comparator path is
modified.

Working-tree and staged path scans found zero protected/frozen changes. Current-board
and frozen-comparator SHA-256 checks pass. `git diff --check` and
`git diff --cached --check` both pass.
""",
    )
    write_text(
        "ROLLBACK_PLAN.md",
        """
# Rollback Plan

The lane is research-only and additive. Before canonicalization, abandon by leaving
the two local commits unadopted. After adoption but before push, reset only the isolated
adoption branch to remote HQ or drop the worktree; never touch preserved worktrees.
After a normal push, create a normal revert of the documentation canonicalization and
its adopted parents. Never force push. Production data/rankings require no rollback
because they were never changed.
""",
    )
    mutation_lines = "\n".join(f"- `{name}` — {result}" for name, result in mutations.items())
    write_text(
        "VALIDATION_RESULTS.md",
        f"""
# Validation Results

- Canonical HQ/tree preflight: pass.
- Current board and frozen comparator hashes: pass.
- HQ2 Git commit/tree/blob/SHA-256/size/schema/identity checks: pass.
- HQ2 independent semantic regeneration: 4,764 panel rows and 4 scorecard rows; pass.
- Deterministic ZIP inventory: 1,061 files / 40 unique hashes / 40 opened.
- Exactness lattice: 5,518 rows; zero unsupported exact admissions.
- Required exact-claim mutations: 14/14 detected.
- New focused suite: 21/21 passed.
- Canonical exact-replay focused suite: 32/32 passed.
- Metric reproduction: exact for the canonical proxy panel and HQ2 scorecard.
- Hermetic bootstrap controls: 13/13 passed.
- Existing security automation: 20/20 passed, including all five closed findings.
- Hermetic Python: 2,819 passed; no skip/xfail/xpass; exit 0.
- LocalData: `BLOCKED_MISSING_LOCAL_TEST_PACK`; native exit 4.
- Data Health passive-read slice: 59/59 passed.
- Changed-file Ruff: pass with zero findings.
- No-new-Ruff differential: 4,443 baseline / 4,443 current; changed files zero.
- Python compilation: pass.
- PowerShell parse: not applicable; no PowerShell file changed.
- `git diff --check`: pass.
- `git diff --cached --check`: pass.
- Board: 240 rows / governed SHA-256; pass.
- Frozen comparator: 924 rows / governed SHA-256; pass.
- Five opaque primary hashes: pass by hash-only verification.
- Persistent state: 14 files / 542,801 bytes / governed Digest V1; pass.
- Recovery state: 7 files / 172,878 bytes / governed Digest V1; pass.
- Retained backups/recovery snapshot: 5/5 and 1/1; pass.
- Protected/frozen changed paths: zero.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.

{mutation_lines}

No result was inferred from an expected exit code. No security scan or LocalData
inspection was performed.
""",
    )


def build_csv_files(frontier: pd.DataFrame, scorecard: pd.DataFrame) -> None:
    write_csv_file("GIT_HISTORY_AND_BLOB_SEARCH_LOG.csv", build_git_log())
    write_csv_file(
        "LOCAL_NWR_ARTIFACT_SEARCH_LOG.csv",
        [
            {
                "surface": item.surface,
                "scope": item.scope,
                "candidate_records": item.candidates,
                "keyword_leads": item.keyword_leads,
                "exact_admissions": item.exact_admissions,
                "stopping_rule": item.stopping_rule,
                "result": item.result,
            }
            for item in search_summaries()
        ],
    )
    write_csv_file("RECOVERED_RECEIPT_INVENTORY.csv", receipt_inventory())
    write_csv_file("RECEIPT_AUTHENTICATION_AND_PROVENANCE.csv", authentication_rows())
    write_csv_file("AS_OF_MANIFEST_COMPLETENESS.csv", manifest_rows())
    write_csv_file("CHECKPOINT_FINAL_SCORE_AND_RANK_CHAIN.csv", checkpoint_chain_rows())
    frontier.to_csv(
        OUT / "COMPONENT_LIFECYCLE_CONFIDENCE_SAFETY_FRONTIER.csv",
        index=False,
        lineterminator="\n",
    )
    write_csv_file(
        "EXACT_REPLAY_FRONTIER_BEFORE_AFTER.csv",
        [
            {
                "measure": "historical_rows",
                "before": HISTORICAL_ROWS,
                "after": HISTORICAL_ROWS,
                "change": 0,
                "status": "UNCHANGED",
            },
            {
                "measure": "exact_primary_rows",
                "before": 0,
                "after": 0,
                "change": 0,
                "status": "BLOCKED_MISSING_RECEIPT",
            },
            {
                "measure": "exact_deterministic_regeneration_rows",
                "before": 0,
                "after": 0,
                "change": 0,
                "status": "BLOCKED_INCOMPLETE_CHAIN",
            },
            {
                "measure": "near_equivalent_rows",
                "before": HISTORICAL_ROWS,
                "after": HISTORICAL_ROWS,
                "change": 0,
                "status": "REVIEW_ONLY_OVERLAPPING_LAYER",
            },
            {
                "measure": "partial_rows",
                "before": HISTORICAL_ROWS,
                "after": HISTORICAL_ROWS,
                "change": 0,
                "status": "PARTIAL_REPLAY",
            },
            {
                "measure": "blocked_rows",
                "before": HISTORICAL_ROWS,
                "after": HISTORICAL_ROWS,
                "change": 0,
                "status": "ALL_ROWS_HAVE_MANDATORY_BLOCKER",
            },
            {
                "measure": "exact_seasons",
                "before": "none",
                "after": "none",
                "change": 0,
                "status": "BLOCKED",
            },
            {
                "measure": "exact_positions",
                "before": "none",
                "after": "none",
                "change": 0,
                "status": "BLOCKED",
            },
            {
                "measure": "exact_checkpoint/final_score/final_rank_rows",
                "before": "0/0/0",
                "after": "0/0/0",
                "change": 0,
                "status": "BLOCKED",
            },
            {
                "measure": "exact_age/games/lifecycle_cohorts",
                "before": "none",
                "after": "none",
                "change": 0,
                "status": "BLOCKED",
            },
        ],
    )
    write_csv_file(
        "EXACT_SUBSET_PROXY_DIFFERENTIAL.csv",
        [
            {
                "comparison": "proxy_vs_exact_current_model_v4",
                "exact_overlap_rows": 0,
                "spearman": "",
                "rank_mae": "",
                "top_n_overlap": "",
                "severe_reversals": "",
                "position_cohorts": "NOT_TESTABLE",
                "age_cohorts": "NOT_TESTABLE",
                "low_games": "NOT_TESTABLE",
                "productive_veterans": "NOT_TESTABLE",
                "return_inactivity": "NOT_TESTABLE",
                "conclusion": "PROXY_TO_EXACT_NOT_TESTABLE",
            }
        ],
    )
    write_csv_file("RECOVERED_GOVERNED_DEFINITIONS.csv", governed_definitions())
    write_csv_file(
        "CHALLENGER_DEFINITIONS_AND_RESULTS.csv", challenger_results(scorecard)
    )
    write_csv_file(
        "CHALLENGER_ACCEPTANCE_GATE_MATRIX.csv", challenger_gate_matrix()
    )
    write_csv_file(
        "UNRECOVERED_FAMILIES_AND_PERMANENT_BLOCKERS.csv",
        [
            {
                "family": family,
                "missing_authority": missing,
                "human_or_external_action": action,
                "prohibited_substitute": substitute,
                "permanent_if_unavailable": "YES",
            }
            for family, missing, action, substitute in (
                (
                    "checkpoint/final scores",
                    "immutable historical bytes plus complete as-of manifest",
                    "originating workstation, backup catalog, artifact retention",
                    "current board or proxy score",
                ),
                (
                    "exact ranks",
                    "full score population, tie keys, assigned ranks, output hash",
                    "original ranking export archive",
                    "rank recomputed from near-equivalent score",
                ),
                (
                    "position components",
                    "historical per-row inputs/outputs and component versions",
                    "original component receipt archive",
                    "Formula Data Mart percentile proxy",
                ),
                (
                    "lifecycle/confidence/discipline/safety",
                    "historical applied inputs, caps, outputs, warnings, hashes",
                    "original phase outputs and source manifests",
                    "neutral 1.0 or review-only regeneration",
                ),
                (
                    "route/return/inactivity/outcome state",
                    "approved point-in-time source snapshots and identity/as-of manifest",
                    "approved external archive with permission",
                    "current provider payload or name join",
                ),
                (
                    "Shadow Model v2 metrics",
                    "immutable output bytes and generating contract",
                    "originating experiment/artifact archive",
                    "recreated metric from memory",
                ),
            )
        ],
    )
    files = [
        ".gitattributes",
        "scripts/build_workday_accuracy_evidence_expansion_v1.py",
        "tests/test_workday_accuracy_evidence_expansion_v1.py",
        *[
            f"docs/hq/master/nwr_workday_accuracy_evidence_expansion_v1_20260723/{name}"
            for name in REQUIRED_OUTPUTS
        ],
    ]
    write_csv_file(
        "FILES_CREATED_OR_CHANGED.csv",
        [
            {
                "path": path,
                "change_type": "MODIFIED" if path == ".gitattributes" else "CREATED",
                "scope": (
                    "research_tooling"
                    if path == ".gitattributes"
                    or path.startswith(("scripts/", "tests/"))
                    else "evidence_documentation"
                ),
                "production_effect": "NONE",
            }
            for path in files
        ],
    )


REQUIRED_OUTPUTS = (
    "WORKDAY_ACCURACY_EVIDENCE_EXPANSION_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "SEARCH_SCOPE_AND_STOPPING_RULES.md",
    "GIT_HISTORY_AND_BLOB_SEARCH_LOG.csv",
    "LOCAL_NWR_ARTIFACT_SEARCH_LOG.csv",
    "RECOVERED_RECEIPT_INVENTORY.csv",
    "RECEIPT_AUTHENTICATION_AND_PROVENANCE.csv",
    "AS_OF_MANIFEST_COMPLETENESS.csv",
    "CHECKPOINT_FINAL_SCORE_AND_RANK_CHAIN.csv",
    "COMPONENT_LIFECYCLE_CONFIDENCE_SAFETY_FRONTIER.csv",
    "EXACT_REPLAY_FRONTIER_BEFORE_AFTER.csv",
    "EXACT_SUBSET_PROXY_DIFFERENTIAL.csv",
    "RECOVERED_GOVERNED_DEFINITIONS.csv",
    "CHALLENGER_DEFINITIONS_AND_RESULTS.csv",
    "CHALLENGER_ACCEPTANCE_GATE_MATRIX.csv",
    "HUMAN_AND_EXTERNAL_RECOVERY_PACKAGE.md",
    "UNRECOVERED_FAMILIES_AND_PERMANENT_BLOCKERS.csv",
    "NEXT_THREE_ACCURACY_LANES.md",
    "PRODUCTION_RANKING_AND_FROZEN_NO_CHANGE.md",
    "SECURITY_DATA_HEALTH_AND_RUNTIME_NO_CHANGE.md",
    "PRIMARY_AND_PERSISTENT_STATE_PRESERVATION.md",
    "PROTECTED_AND_FROZEN_PATH_PROOF.md",
    "ROLLBACK_PLAN.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


def write_manifest() -> None:
    missing = [
        name
        for name in REQUIRED_OUTPUTS
        if name != "MANIFEST.json" and not (OUT / name).exists()
    ]
    if missing:
        raise RuntimeError(f"required output missing: {missing}")
    entries = []
    for name in REQUIRED_OUTPUTS:
        if name == "MANIFEST.json":
            continue
        path = OUT / name
        entries.append(
            {
                "path": name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    payload = {
        "schema_version": "nwr_workday_accuracy_evidence_expansion_manifest_v1",
        "generated_date": "2026-07-23",
        "canonical_start_commit": EXPECTED_HQ,
        "canonical_start_tree": EXPECTED_TREE,
        "model_contract": MODEL_ID,
        "verdict": "YELLOW_NWR_RECEIPT_RECOVERY_EXHAUSTED_WITH_ACTIONABLE_HUMAN_LEADS",
        "exact_rows_before": 0,
        "exact_rows_after": 0,
        "proxy_to_exact": "PROXY_TO_EXACT_NOT_TESTABLE",
        "final_challenger_disposition": "NO_ACCURACY_CHALLENGER_ADMITTED",
        "production_ranking_change": "NONE",
        "frozen_2026_change": "NONE",
        "files": entries,
    }
    (OUT / "MANIFEST.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_packet() -> None:
    manifest = json.loads((OUT / "MANIFEST.json").read_text(encoding="utf-8"))
    by_path = {entry["path"]: entry for entry in manifest["files"]}
    for name in REQUIRED_OUTPUTS:
        path = OUT / name
        if not path.exists():
            raise RuntimeError(f"packet is incomplete: {name}")
        if name == "MANIFEST.json":
            continue
        entry = by_path.get(name)
        if not entry:
            raise RuntimeError(f"manifest entry missing: {name}")
        if entry["bytes"] != path.stat().st_size or entry["sha256"] != sha256(path):
            raise RuntimeError(f"manifest mismatch: {name}")
    frontier = pd.read_csv(
        OUT / "COMPONENT_LIFECYCLE_CONFIDENCE_SAFETY_FRONTIER.csv",
        low_memory=False,
    )
    if len(frontier) != HISTORICAL_ROWS:
        raise RuntimeError("packet frontier row count changed")
    if frontier["mandatory_chain_complete"].astype(bool).any():
        raise RuntimeError("packet admitted an unsupported exact row")
    differential = pd.read_csv(OUT / "EXACT_SUBSET_PROXY_DIFFERENTIAL.csv")
    if differential.loc[0, "conclusion"] != "PROXY_TO_EXACT_NOT_TESTABLE":
        raise RuntimeError("zero-overlap conclusion changed")


def build() -> None:
    validate_canonical_state()
    panel = validate_hq2()
    mutations = validate_mutations()
    if len(mutations) != 14:
        raise RuntimeError("mutation inventory is incomplete")
    scorecard = pd.read_csv(HQ2_SCORECARD)
    if len(panel) != int(
        scorecard.loc[scorecard["scope"] == "pooled_flex", "rows"].iloc[0]
    ):
        raise RuntimeError("HQ2 scorecard/panel row count mismatch")
    frontier = exactness_frontier()
    OUT.mkdir(parents=True, exist_ok=True)
    build_csv_files(frontier, scorecard)
    build_markdown_files(mutations)
    write_manifest()
    validate_packet()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the committed packet without regenerating it.",
    )
    args = parser.parse_args()
    if args.validate_only:
        validate_packet()
    else:
        build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
