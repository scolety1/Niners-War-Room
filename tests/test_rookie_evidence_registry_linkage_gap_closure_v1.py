from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from scripts.validate_rookie_evidence_registry_scaffold_v1 import validate_registry

ROOT = Path("docs/hq/rookie_evidence_workspace_v1")
REGISTRIES = ROOT / "registries"
PACKET = Path(
    "docs/hq/master/rookie_evidence_registry_deterministic_linkage_gap_closure_v1_20260711"
)
CONTRACT_HASH = "19bb737de35f476ad39bff50d41f25e5ec6ef3b88dacd48d23b47917960fa264"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def canonical_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_mapping_contract_was_frozen() -> None:
    assert canonical_hash(PACKET / "DETERMINISTIC_MAPPING_EVIDENCE_CONTRACT.md") == CONTRACT_HASH


def test_extended_registry_validator_passes() -> None:
    report = validate_registry()
    assert report.status == "PASS", report.issues
    assert report.check_count >= 118


def test_active_artifact_authority_links_are_exact_and_unique() -> None:
    links = rows(REGISTRIES / "ARTIFACT_AUTHORITY_LINK.csv")
    assert len(links) == 113
    assert len({row["mapping_id"] for row in links}) == 113
    assert len({row["left_endpoint_id"] for row in links}) == 113
    assert {row["mapping_status"] for row in links} == {"VERIFIED_EXACT_MANIFEST_REFERENCE"}
    assert {row["locality_class"] for row in links} == {"LIVE_HQ"}
    assert {row["authority_effect"] for row in links} == {
        "NO_AUTHORITY_CHANGE_METADATA_REFERENCE_ONLY"
    }
    assert {row["source_use_effect"] for row in links} == {"NO_SOURCE_OR_USE_PERMISSION"}


def test_active_link_endpoints_exist() -> None:
    links = rows(REGISTRIES / "ARTIFACT_AUTHORITY_LINK.csv")
    artifact_ids = {
        row["artifact_id"] for row in rows(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    }
    authority_ids = {row["authority_id"] for row in rows(REGISTRIES / "AUTHORITY_REGISTRY.csv")}
    assert {row["left_endpoint_id"] for row in links} <= artifact_ids
    assert {row["right_endpoint_id"] for row in links} <= authority_ids


def test_no_other_active_link_registry_is_populated() -> None:
    for name in (
        "ARTIFACT_SOURCE_LINK.csv",
        "ARTIFACT_DATASET_LINK.csv",
        "ARTIFACT_RECEIPT_LINK.csv",
        "DATASET_SOURCE_LINK.csv",
        "DATASET_RECEIPT_LINK.csv",
        "RECEIPT_SOURCE_LINK.csv",
    ):
        assert rows(REGISTRIES / name) == []


def test_verified_ledger_preserves_active_and_deferred_evidence() -> None:
    verified = rows(PACKET / "VERIFIED_METADATA_LINKS.csv")
    assert len(verified) == 141
    review_counts = Counter(row["review_status"] for row in verified)
    assert review_counts == {
        "READY_FOR_HQ_REVIEW": 113,
        "DEFERRED_ENDPOINTS_NOT_REGISTERED": 25,
        "DEFERRED_ENDPOINT_NOT_REGISTERED_AND_PROTECTED_SCOPE": 3,
    }
    assert sum(row["proof_type"] == "VERIFIED_EXPLICIT_ID_REFERENCE" for row in verified) == 25
    assert sum(row["proof_type"] == "VERIFIED_EXACT_HASH_RECEIPT" for row in verified) == 3


def test_deferred_candidates_do_not_populate_endpoint_registries() -> None:
    assert rows(REGISTRIES / "SOURCE_REGISTRY.csv") == []
    assert rows(REGISTRIES / "DATASET_REGISTRY.csv") == []
    assert rows(REGISTRIES / "SOURCE_RECEIPT_REGISTRY.csv") == []
    artifacts = rows(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    assert all(
        not row[field]
        for row in artifacts
        for field in ("authority_id", "source_id", "dataset_id", "receipt_id")
    )


def test_all_artifacts_reconcile_once() -> None:
    reconciliation = rows(PACKET / "ARTIFACT_MAPPING_RECONCILIATION.csv")
    assert len(reconciliation) == 1269
    assert len({row["artifact_id"] for row in reconciliation}) == 1269
    assert Counter(row["overall_mapping_status"] for row in reconciliation) == {
        "VERIFIED_EXACT_MANIFEST_REFERENCE": 113,
        "VERIFIED_EXACT_HASH_RECEIPT": 3,
        "UNRESOLVED_NO_EXPLICIT_LINK": 969,
        "LOCAL_ONLY_METADATA_ONLY": 162,
        "RESTRICTED_SANITIZED_ONLY": 3,
        "OFF_HQ_AUDIT_ONLY": 19,
    }
    assert {row["active_optional_foreign_keys_populated"] for row in reconciliation} == {"false"}


def test_unresolved_relationship_counts_are_exact() -> None:
    unresolved = rows(PACKET / "UNRESOLVED_METADATA_LINKS.csv")
    assert len(unresolved) == 4963
    assert len({row["mapping_id"] for row in unresolved}) == 4963
    assert Counter(row["relationship_type"] for row in unresolved) == {
        "ARTIFACT_AUTHORITY": 1156,
        "ARTIFACT_SOURCE": 1269,
        "ARTIFACT_DATASET": 1269,
        "ARTIFACT_RECEIPT": 1269,
    }
    assert all(not row["right_endpoint_id"] for row in unresolved)


def test_no_canonical_conflicting_link_is_created() -> None:
    assert rows(PACKET / "CONFLICTING_EXPLICIT_LINKS.csv") == []


def test_exact_source_use_decisions_remain_zero_and_fail_closed() -> None:
    assert rows(REGISTRIES / "SOURCE_USE_DECISION_LEDGER.csv") == []
    review = rows(PACKET / "SOURCE_USE_EXPLICIT_DECISION_REVIEW.csv")
    assert len(review) == 9
    assert all(row["verified_decisions"] == "0" for row in review)
    assert all(row["decision_result"] == "NOT_ENOUGH_INFORMATION" for row in review)


def test_no_real_player_or_evidence_rows() -> None:
    for name in (
        "PLAYER_IDENTITY_REGISTRY.csv",
        "PLAYER_ALIAS_REGISTRY.csv",
        "IDENTITY_ASSERTION_LEDGER.csv",
        "EVIDENCE_OBSERVATION_REGISTRY.csv",
    ):
        assert rows(REGISTRIES / name) == []


def test_outputs_contain_no_raw_absolute_or_restricted_locator() -> None:
    searchable = "\n".join(
        path.read_text(encoding="utf-8-sig") for path in PACKET.iterdir() if path.is_file()
    )
    assert not re.search(r"(?i)([a-z]:[/\\]|/Users/|/home/)", searchable)
    assert "LOCAL_ONLY_RESTRICTED://" not in searchable


def test_legacy_canonical_now_is_not_mapping_evidence() -> None:
    links = rows(REGISTRIES / "ARTIFACT_AUTHORITY_LINK.csv")
    assert all("canonical_now" not in row["evidence_field"] for row in links)


def test_phase_b_manifest_is_complete_and_valid() -> None:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["required_file_count"] == 17
    assert len(manifest["files"]) == 16
    for entry in manifest["files"]:
        path = Path(entry["path"])
        data = path.read_bytes().replace(b"\r\n", b"\n")
        assert len(data) == entry["bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
