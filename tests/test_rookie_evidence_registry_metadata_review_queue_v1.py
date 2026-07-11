from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from scripts.build_rookie_evidence_registry_metadata_review_queue_v1 import (
    CATEGORIES,
    CREATED_AT_RECEIPT,
    PACKET,
    PRIORITIES,
    PRIORITY_BY_CATEGORY,
    QUEUE_CONTRACT_HASH,
    STATUS_BY_CATEGORY,
    STATUSES,
    build_queue,
    opaque,
    validate_queue,
)

REGISTRIES = Path("docs/hq/rookie_evidence_workspace_v1/registries")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def canonical_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_queue_contract_was_frozen_before_population() -> None:
    assert canonical_hash(PACKET / "QUEUE_SCHEMA_AND_PRIORITY_CONTRACT.md") == QUEUE_CONTRACT_HASH


def test_queue_validator_passes_with_exact_total() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    report = validate_queue(queue)
    assert report["status"] == "PASS", report["issues"]
    assert report["queue_count"] == 5147


def test_queue_ids_are_unique_recomputable_and_sorted() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    ids = [row["queue_id"] for row in queue]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids)) == 5147
    assert all(
        row["queue_id"]
        == opaque(
            "queue",
            row["queue_category"],
            row["subject_endpoint_id"],
            row["related_endpoint_type"],
            row["related_endpoint_id"],
        )
        for row in queue
    )


def test_category_counts_are_exact_and_closed() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    assert set(CATEGORIES) == {
        "ARTIFACT_AUTHORITY_LINK_MISSING",
        "ARTIFACT_SOURCE_LINK_MISSING",
        "ARTIFACT_DATASET_LINK_MISSING",
        "ARTIFACT_RECEIPT_LINK_MISSING",
        "DATASET_SOURCE_LINK_MISSING",
        "DATASET_RECEIPT_LINK_MISSING",
        "RECEIPT_SOURCE_LINK_MISSING",
        "EXPLICIT_SOURCE_USE_DECISION_MISSING",
        "CONFLICTING_EXPLICIT_METADATA_LINK",
        "LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW",
        "RESTRICTED_RIGHTS_REVIEW",
        "OFF_HQ_AUDIT_LOCATOR_REVIEW",
        "NOT_ENOUGH_INFORMATION",
    }
    assert Counter(row["queue_category"] for row in queue) == {
        "ARTIFACT_AUTHORITY_LINK_MISSING": 1156,
        "ARTIFACT_SOURCE_LINK_MISSING": 1269,
        "ARTIFACT_DATASET_LINK_MISSING": 1269,
        "ARTIFACT_RECEIPT_LINK_MISSING": 1269,
        "LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW": 162,
        "RESTRICTED_RIGHTS_REVIEW": 3,
        "OFF_HQ_AUDIT_LOCATOR_REVIEW": 19,
    }


def test_priority_counts_and_frozen_rules_are_exact() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    assert set(PRIORITIES) == {
        "P0_INTEGRITY_BLOCKER",
        "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
        "P2_LINEAGE_GAP",
        "P3_AUDIT_OR_NO_RECREATE_GAP",
        "P4_INFORMATIONAL",
    }
    assert all(row["priority"] == PRIORITY_BY_CATEGORY[row["queue_category"]] for row in queue)
    assert Counter(row["priority"] for row in queue) == {
        "P1_AUTHORITY_OR_RIGHTS_BLOCKER": 2428,
        "P2_LINEAGE_GAP": 2538,
        "P3_AUDIT_OR_NO_RECREATE_GAP": 181,
    }


def test_initial_status_counts_are_exact_and_none_closed() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    assert set(STATUSES) == {
        "OPEN",
        "BLOCKED",
        "NOT_ENOUGH_INFORMATION",
        "DEFERRED",
        "CLOSED_WITH_RECEIPT",
    }
    assert all(row["status"] == STATUS_BY_CATEGORY[row["queue_category"]] for row in queue)
    assert Counter(row["status"] for row in queue) == {
        "BLOCKED": 2428,
        "NOT_ENOUGH_INFORMATION": 2700,
        "DEFERRED": 19,
    }
    assert all(not row["closure_receipt"] for row in queue)


def test_subject_state_and_locality_are_exact_registry_metadata() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    artifacts = {
        row["artifact_id"]: row for row in rows(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    }
    assert all(row["subject_endpoint_type"] == "ARTIFACT" for row in queue)
    assert all(row["subject_endpoint_id"] in artifacts for row in queue)
    assert all(
        row["evidence_state_classification"]
        == artifacts[row["subject_endpoint_id"]]["evidence_state"]
        and row["locality_class"] == artifacts[row["subject_endpoint_id"]]["locality_class"]
        for row in queue
    )


def test_populated_related_ids_are_existing_sanitized_locators_only() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    locator_ids = {row["locator_id"] for row in rows(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")}
    populated = [row for row in queue if row["related_endpoint_id"]]
    assert len(populated) == 184
    assert all(row["related_endpoint_type"] == "LOCATOR" for row in populated)
    assert {row["related_endpoint_id"] for row in populated} <= locator_ids


def test_queue_contains_no_player_rows_or_restricted_locator_content() -> None:
    queue_text = (PACKET / "METADATA_REVIEW_QUEUE.csv").read_text(encoding="utf-8-sig")
    assert not re.search(r"(?i)(nwrp_|player_id|player_name|verified_udfa)", queue_text)
    assert not re.search(r"(?i)([a-z]:[/\\]|/Users/|/home/|\\\\|file://|\.\./)", queue_text)
    assert "LOCAL_ONLY_RESTRICTED://" not in queue_text


def test_queue_has_no_authority_permission_or_decision_expansion() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    assert {row["source_use_implication"] for row in queue} == {
        "NO_AUTHORITY_SOURCE_OR_USE_CHANGE;FAIL_CLOSED"
    }
    assert all(row["queue_category"] != "EXPLICIT_SOURCE_USE_DECISION_MISSING" for row in queue)
    assert rows(REGISTRIES / "SOURCE_USE_DECISION_LEDGER.csv") == []


def test_queue_generation_is_deterministic() -> None:
    assert build_queue() == rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    assert {row["created_at_receipt"] for row in build_queue()} == {CREATED_AT_RECEIPT}


def test_no_real_player_or_evidence_registry_rows() -> None:
    for name in (
        "PLAYER_IDENTITY_REGISTRY.csv",
        "PLAYER_ALIAS_REGISTRY.csv",
        "IDENTITY_ASSERTION_LEDGER.csv",
        "EVIDENCE_OBSERVATION_REGISTRY.csv",
    ):
        assert rows(REGISTRIES / name) == []


def test_queue_is_not_imported_by_application_runtime() -> None:
    symbols = ("METADATA_REVIEW_QUEUE", "metadata_review_queue")
    for root in (Path("app"), Path("src")):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert not any(symbol in text for symbol in symbols), path


def test_summary_tables_match_queue() -> None:
    queue = rows(PACKET / "METADATA_REVIEW_QUEUE.csv")
    category_summary = rows(PACKET / "QUEUE_CATEGORY_SUMMARY.csv")
    priority_summary = rows(PACKET / "QUEUE_PRIORITY_SUMMARY.csv")
    category_counts = Counter(row["queue_category"] for row in queue)
    priority_counts = Counter(row["priority"] for row in queue)
    assert all(
        int(row["queue_count"]) == category_counts[row["queue_category"]]
        for row in category_summary
    )
    assert all(
        int(row["queue_count"]) == priority_counts[row["priority"]] for row in priority_summary
    )


def test_phase_c_manifest_is_complete_and_valid() -> None:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["required_file_count"] == 15
    assert manifest["queue_row_count"] == 5147
    assert manifest["player_level_row_count"] == 0
    assert manifest["automatically_closed_count"] == 0
    assert len(manifest["files"]) == 14
    for entry in manifest["files"]:
        path = Path(entry["path"])
        data = path.read_bytes().replace(b"\r\n", b"\n")
        assert len(data) == entry["bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
