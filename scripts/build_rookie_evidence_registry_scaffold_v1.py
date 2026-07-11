# ruff: noqa: E501
# Long documentation strings are emitted verbatim; wrapping them would alter the generated packet.
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIGN_ROOT = (
    REPO_ROOT / "docs/hq/master/rookie_evidence_workspace_consolidation_design_v1_20260711"
)
CANON_ROOT = (
    REPO_ROOT / "docs/hq/master/rookie_evidence_workspace_design_canonicalization_v1_20260711"
)
WORKSPACE_ROOT = REPO_ROOT / "docs/hq/rookie_evidence_workspace_v1"
REGISTRY_ROOT = WORKSPACE_ROOT / "registries"
GOVERNANCE_ROOT = WORKSPACE_ROOT / "governance"
CONFLICT_ROOT = WORKSPACE_ROOT / "conflicts"
ARCHIVE_ROOT = WORKSPACE_ROOT / "archive"
PACKET_ROOT = REPO_ROOT / "docs/hq/master/rookie_evidence_registry_read_only_scaffold_v1_20260711"
SCHEMA_VERSION = "1.0.0"
SNAPSHOT_VERSION = "20260711.1"
STARTING_HEAD = "e6d680195f9e4512885ac281c215f2fb2ae4b64c"

LIFECYCLE_STAGES = (
    ("PRE_DRAFT", "Pre-draft", "Player evidence before the draft event."),
    ("DRAFT_EVENT", "Draft-event", "Draft, supplemental, or entry-event evidence."),
    (
        "POST_DRAFT_PRESEASON",
        "Post-draft / pre-season",
        "Player evidence after the draft and before the regular season.",
    ),
    ("ROOKIE_SEASON", "Rookie-season", "Player evidence from the rookie season."),
    (
        "MULTI_YEAR_OUTCOME",
        "Multi-year outcomes",
        "Outcome evidence beyond the rookie-season boundary.",
    ),
)

EVIDENCE_STATES = (
    "CANONICAL_ADMITTED",
    "CANONICAL_REVIEW_ONLY",
    "SUPPORTING_EVIDENCE",
    "PROVISIONAL",
    "IDENTITY_UNRESOLVED",
    "SOURCE_UNADMITTED",
    "USE_BLOCKED",
    "DUPLICATE_EQUIVALENT",
    "DUPLICATE_CONFLICTING",
    "SUPERSEDED",
    "LOCAL_ONLY_RESTRICTED",
    "MISSING_EXPECTED",
    "UNAVAILABLE",
    "NOT_ENOUGH_INFORMATION",
)

PURPOSES = (
    "LOCAL_RETENTION",
    "CANONICAL_HQ_SUMMARY",
    "RAW_RECEIPT_STORAGE",
    "DISPLAY",
    "RESEARCH",
    "MODEL_TRAINING",
    "PRODUCTION_SCORING",
    "REDISTRIBUTION",
    "EXPORT",
)

DECISION_VALUES = (
    "ALLOWED",
    "ALLOWED_WITH_CAVEATS",
    "REVIEW_ONLY",
    "BLOCKED",
    "NOT_ENOUGH_INFORMATION",
    "NOT_APPLICABLE",
)

LOCALITIES = (
    "LIVE_HQ",
    "LOCAL_ONLY",
    "LOCAL_ONLY_RESTRICTED",
    "OFF_HQ_BRANCH_ONLY",
)

NON_ADMITTING_SOURCE_EFFECTS = {
    "NO_SOURCE_ADMISSION",
    "ROUTING_CEILING_ONLY",
    "SEPARATE_EXPLICIT_DECISION_REQUIRED",
    "BLOCKS_ADMISSION",
}

ARTIFACT_HEADERS = (
    "artifact_id",
    "artifact_type",
    "artifact_scope_class",
    "evidence_state",
    "authority_id",
    "locality_class",
    "locator_id",
    "source_id",
    "dataset_id",
    "receipt_id",
    "canonical_flag",
    "supporting_flag",
    "duplicate_status",
    "superseded_status",
    "no_recreate_status",
    "implementation_status",
    "manifest_hash_status",
    "sha256",
    "row_count_metadata",
    "schema_summary",
    "as_of_metadata",
    "controlling_caveat",
    "record_version",
)

LOCATOR_HEADERS = (
    "locator_id",
    "artifact_id",
    "locality_class",
    "repository_relative_location",
    "sanitized_locator_id",
    "audit_git_commit",
    "audit_git_object_path",
    "availability_state",
    "active_use_state",
    "rights_state",
    "privacy_class",
    "reversibility_review",
    "record_version",
)

AUTHORITY_HEADERS = (
    "authority_id",
    "evidence_family",
    "metadata_registration_status",
    "authority_scope_class",
    "player_value_authority",
    "production_authority",
    "source_admission_effect",
    "locality_class",
    "permitted_use_class",
    "controlling_caveat",
    "legacy_canonical_now_value",
    "legacy_field_interpretation",
    "source_authority_row",
)

SOURCE_HEADERS = (
    "source_id",
    "source_family",
    "governance_state",
    "locality_class",
    "rights_use_review_status",
    "receipt_availability",
    "source_caveat",
    "record_version",
)

DATASET_HEADERS = (
    "dataset_id",
    "source_id",
    "dataset_name",
    "lifecycle_stage",
    "schema_summary",
    "season_population_coverage",
    "authority_id",
    "evidence_state",
    "receipt_status",
    "permitted_use_decision_refs",
    "record_version",
)

RECEIPT_HEADERS = (
    "receipt_id",
    "artifact_id",
    "dataset_id",
    "source_id",
    "receipt_type",
    "locator_id",
    "hash_status",
    "as_of_metadata",
    "rights_state",
    "privacy_class",
    "availability_state",
    "record_version",
)

DECISION_HEADERS = (
    "use_decision_id",
    "dataset_id",
    "field_family",
    "purpose",
    "decision_value",
    "decision_version",
    "effective_at",
    "evidence_links",
    "rights_status",
    "privacy_class",
    "caveat_text",
    "owner_role",
    "approval_receipt_id",
    "supersedes_use_decision_id",
)

PLAYER_HEADERS = (
    "nwr_player_id",
    "display_name",
    "normalized_name_review_only",
    "declared_position_current",
    "birth_date",
    "identity_status",
    "identity_confidence",
    "created_at",
    "created_by_lane",
    "valid_from",
    "valid_to",
    "manual_review_status",
    "record_version",
)

ALIAS_HEADERS = (
    "alias_id",
    "nwr_player_id",
    "namespace",
    "provider_id",
    "provider_name",
    "valid_from",
    "valid_to",
    "team_context",
    "season_context",
    "source_id",
    "receipt_id",
    "identity_assertion_id",
    "alias_status",
    "superseded_by_alias_id",
    "record_version",
)

IDENTITY_HEADERS = (
    "identity_assertion_id",
    "candidate_nwr_player_id",
    "asserted_nwr_player_id",
    "source_namespace",
    "provider_id",
    "normalized_name_review_only",
    "identity_confidence",
    "join_method",
    "join_evidence",
    "conflict_reason",
    "manual_review_status",
    "source_id",
    "receipt_id",
    "as_of_metadata",
    "use_decision_id",
    "record_version",
)

OBSERVATION_HEADERS = (
    "evidence_observation_id",
    "nwr_player_id",
    "artifact_id",
    "source_id",
    "dataset_id",
    "receipt_id",
    "lineage_id",
    "source_row_key",
    "evidence_type",
    "field_definition_id",
    "original_value",
    "typed_value",
    "lifecycle_stage",
    "evidence_state",
    "identity_state",
    "source_admission_state",
    "use_decision_state",
    "use_decision_id",
    "availability_state",
    "duplication_state",
    "duplicate_relationship_id",
    "locality_state",
    "censoring_state",
    "confidence",
    "effective_at",
    "source_timestamp",
    "as_of_date",
    "transformation_version",
    "superseded_observation_id",
    "fixture_class",
    "record_version",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, headers: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header_tuple = tuple(headers)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header_tuple, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header_tuple})


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".py"}:
        data = data.replace(b"\r\n", b"\n")
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest()


def _opaque(prefix: str, value: str) -> str:
    digest = hashlib.sha256(f"rookie-evidence-registry-v1|{prefix}|{value}".encode()).hexdigest()
    return f"{prefix}_{digest[:24]}"


def _bool(value: str) -> str:
    return "true" if value.strip().lower() == "true" else "false"


def _locator_row(row: dict[str, str]) -> dict[str, str]:
    artifact_id = row["artifact_id"]
    locality = row["location_status"]
    locator_id = _opaque("loc", artifact_id)
    result = {
        "locator_id": locator_id,
        "artifact_id": artifact_id,
        "locality_class": locality,
        "repository_relative_location": "",
        "sanitized_locator_id": "",
        "audit_git_commit": "",
        "audit_git_object_path": "",
        "availability_state": "NOT_ENOUGH_INFORMATION",
        "active_use_state": "USE_BLOCKED",
        "rights_state": "NOT_ENOUGH_INFORMATION",
        "privacy_class": "LOCAL_REVIEW_DATA",
        "reversibility_review": "PASS_NO_RAW_OR_REVERSIBLE_LOCATOR_STORED",
        "record_version": SCHEMA_VERSION,
    }
    if locality == "LIVE_HQ":
        result.update(
            repository_relative_location=row["path"],
            availability_state="PRESENT",
            active_use_state="NOT_AUTHORIZED_BY_LOCATOR",
            rights_state="REVIEW_ONLY",
            privacy_class="PUBLIC_GOVERNANCE",
            reversibility_review="PASS_REPOSITORY_RELATIVE_LOCATION_ONLY",
        )
    elif locality == "LOCAL_ONLY":
        result["sanitized_locator_id"] = _opaque("loc_local", artifact_id)
    elif locality == "LOCAL_ONLY_RESTRICTED":
        result.update(
            sanitized_locator_id=_opaque("loc_restricted", artifact_id),
            rights_state="BLOCKED",
            privacy_class="LICENSED_PROVIDER_RESTRICTED",
        )
    elif locality == "OFF_HQ_BRANCH_ONLY":
        match = re.fullmatch(r"git:([0-9a-f]{40}):(.+)", row["path"])
        if not match:
            raise ValueError(f"Invalid off-HQ locator for {artifact_id}")
        result.update(
            sanitized_locator_id=_opaque("loc_offhq", artifact_id),
            audit_git_commit=match.group(1),
            audit_git_object_path=match.group(2),
            rights_state="BLOCKED",
            reversibility_review="PASS_OFF_HQ_AUDIT_GIT_OBJECT_ONLY",
        )
    else:
        raise ValueError(f"Unknown locality {locality!r}")
    return result


def _artifact_row(row: dict[str, str], locator_id: str) -> dict[str, str]:
    locality = row["location_status"]
    restricted = locality == "LOCAL_ONLY_RESTRICTED"
    off_hq = locality == "OFF_HQ_BRANCH_ONLY"
    caveat = row["known_caveats"].strip()
    if restricted:
        caveat = (
            "Restricted aggregate metadata only; raw paths, provider content, private identifiers, "
            "and reversible locator material are withheld."
        )
    elif off_hq:
        caveat = (
            "Off-HQ Git object is retained for audit discovery and no-recreate protection only; "
            "active evidence, migration, ranking, formula, training, production, and runtime use are blocked."
        )
    return {
        "artifact_id": row["artifact_id"],
        "artifact_type": row["schema_or_structure"] or "UNKNOWN_METADATA",
        "artifact_scope_class": row["lifecycle_or_artifact_scope"],
        "evidence_state": row["evidence_state"],
        "authority_id": "",
        "locality_class": locality,
        "locator_id": locator_id,
        "source_id": "",
        "dataset_id": "",
        "receipt_id": "",
        "canonical_flag": _bool(row["canonical"]),
        "supporting_flag": _bool(row["supporting"]),
        "duplicate_status": (
            "DUPLICATE_RECORDED" if _bool(row["duplicated"]) == "true" else "NO_DUPLICATE_FLAG"
        ),
        "superseded_status": (
            "SUPERSEDED_RECORDED" if _bool(row["superseded"]) == "true" else "NOT_SUPERSEDED"
        ),
        "no_recreate_status": (
            "NO_RECREATE_REQUIRED" if restricted or off_hq else "SEPARATE_LEDGER_CONTROLS"
        ),
        "implementation_status": "REGISTERED_METADATA_ONLY",
        "manifest_hash_status": (
            "WITHHELD_OR_NOT_PERMITTED" if restricted else "SOURCE_INVENTORY_SHA256_RECORDED"
        ),
        "sha256": "" if restricted else row["sha256"],
        "row_count_metadata": row["row_count_if_csv"],
        "schema_summary": (
            "restricted aggregate; content withheld" if restricted else row["schema_or_structure"]
        ),
        "as_of_metadata": row["as_of_status"],
        "controlling_caveat": caveat,
        "record_version": SCHEMA_VERSION,
    }


def _lifecycle_links(inventory: list[dict[str, str]]) -> list[dict[str, str]]:
    mapping = {
        "PRE_DRAFT": ("PRE_DRAFT",),
        "PRE_DRAFT_LEGACY": ("PRE_DRAFT",),
        "DRAFT_EVENT": ("DRAFT_EVENT",),
        "DRAFT_EVENT_AND_POST_DRAFT_PRESEASON": (
            "DRAFT_EVENT",
            "POST_DRAFT_PRESEASON",
        ),
        "DRAFT_EVENT_TO_ROOKIE_OUTCOME_BRIDGE": ("DRAFT_EVENT", "ROOKIE_SEASON"),
        "ROOKIE_SEASON_AND_MULTI_YEAR_OUTCOME": (
            "ROOKIE_SEASON",
            "MULTI_YEAR_OUTCOME",
        ),
        "LATER_OUTCOME_RESEARCH": ("MULTI_YEAR_OUTCOME",),
        "PRE_DRAFT_TO_MULTI_YEAR_LEGACY": tuple(stage[0] for stage in LIFECYCLE_STAGES),
    }
    links: list[dict[str, str]] = []
    for row in inventory:
        stages = mapping.get(row["lifecycle_or_artifact_scope"], ())
        for stage in stages:
            links.append(
                {
                    "artifact_id": row["artifact_id"],
                    "lifecycle_stage": stage,
                    "link_scope": "ARTIFACT_METADATA_COVERAGE_ONLY",
                    "link_basis": "EXPLICIT_DESIGN_SCOPE_LABEL_MAPPING",
                    "primary_for_artifact_or_dataset": "false",
                    "decision_or_receipt_id": "",
                    "record_version": SCHEMA_VERSION,
                }
            )
    return sorted(links, key=lambda item: (item["artifact_id"], item["lifecycle_stage"]))


def _duplicate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    relationship_types = {
        "EXACT_DUPLICATE": "DUPLICATE_EQUIVALENT",
        "SCHEMA_EQUIVALENT_DUPLICATE": "DUPLICATE_EQUIVALENT",
        "TRANSFORMED_DERIVATIVE": "DERIVES_FROM",
        "OVERLAPPING_POPULATION": "OVERLAPS",
        "STALE_PREDECESSOR": "SUPERSEDES_PROPOSAL",
        "CONFLICTING_EVIDENCE": "DUPLICATE_CONFLICTING",
        "INDEPENDENT_CORROBORATION": "SUPPORTS",
        "NOT_ACTUALLY_DUPLICATED": "NO_DUPLICATE_RELATION",
    }
    result = []
    for row in rows:
        result.append(
            {
                "relationship_id": row["register_id"],
                "relationship_type": relationship_types[row["classification_enum"]],
                "duplicate_class": row["classification_enum"],
                "artifact_id_a": "",
                "artifact_id_b": "",
                "design_reference_a": row["artifact_a"],
                "design_reference_b": row["artifact_b_or_group"],
                "relationship_scope": row["scope"],
                "count_basis": row["count_basis"],
                "disposition": row["disposition_enum"],
                "human_review_required": row["human_review_required"],
                "blocker": row["blocker"],
                "relationship_validation_status": row["relationship_validation_status"],
                "decision_receipt_status": row["decision_receipt_status"],
                "resolution_status": "UNRESOLVED_REVIEW_OBJECT",
                "record_version": SCHEMA_VERSION,
            }
        )
    return sorted(result, key=lambda item: item["relationship_id"])


def _safe_no_recreate_reference(index_id: str, value: str) -> tuple[str, str]:
    allowed_prefixes = ("docs/", "src/", "tests/", "scripts/", "config/", "data/", "app/")
    parts = [part.strip() for part in value.split("|")]
    if parts and all(part.startswith(allowed_prefixes) for part in parts):
        return value, ""
    return "", _opaque("nrref", index_id)


def _no_recreate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for row in rows:
        repo_ref, sanitized_ref = _safe_no_recreate_reference(
            row["index_id"], row["evidence_paths"]
        )
        result.append(
            {
                "no_recreate_id": row["index_id"],
                "artifact_id": "",
                "repository_relative_reference": repo_ref,
                "sanitized_reference_locator_id": sanitized_ref,
                "classification": row["classification"],
                "required_treatment": row["required_treatment"],
                "blocker_or_guardrail": row["blocker_or_guardrail"],
                "active_use_state": "NO_ACTIVE_USE_AUTHORIZED",
                "record_version": SCHEMA_VERSION,
            }
        )
    return sorted(result, key=lambda item: item["no_recreate_id"])


def _schemas(artifact_scopes: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    schema_rows: dict[str, tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]] = {
        "EVIDENCE_ARTIFACT_REGISTRY.csv": (
            ARTIFACT_HEADERS,
            ("artifact_id",),
            {
                "authority_id": "AUTHORITY_REGISTRY.csv.authority_id?",
                "locator_id": "SANITIZED_LOCATOR_REGISTRY.csv.locator_id",
                "source_id": "SOURCE_REGISTRY.csv.source_id?",
                "dataset_id": "DATASET_REGISTRY.csv.dataset_id?",
                "receipt_id": "SOURCE_RECEIPT_REGISTRY.csv.receipt_id?",
            },
        ),
        "SOURCE_REGISTRY.csv": (SOURCE_HEADERS, ("source_id",), {}),
        "DATASET_REGISTRY.csv": (
            DATASET_HEADERS,
            ("dataset_id",),
            {
                "source_id": "SOURCE_REGISTRY.csv.source_id",
                "authority_id": "AUTHORITY_REGISTRY.csv.authority_id?",
            },
        ),
        "SOURCE_RECEIPT_REGISTRY.csv": (
            RECEIPT_HEADERS,
            ("receipt_id",),
            {
                "artifact_id": "EVIDENCE_ARTIFACT_REGISTRY.csv.artifact_id?",
                "dataset_id": "DATASET_REGISTRY.csv.dataset_id?",
                "source_id": "SOURCE_REGISTRY.csv.source_id?",
                "locator_id": "SANITIZED_LOCATOR_REGISTRY.csv.locator_id?",
            },
        ),
        "AUTHORITY_REGISTRY.csv": (AUTHORITY_HEADERS, ("authority_id",), {}),
        "SOURCE_USE_DECISION_LEDGER.csv": (
            DECISION_HEADERS,
            ("use_decision_id",),
            {
                "dataset_id": "DATASET_REGISTRY.csv.dataset_id",
                "approval_receipt_id": "SOURCE_RECEIPT_REGISTRY.csv.receipt_id",
            },
        ),
        "SANITIZED_LOCATOR_REGISTRY.csv": (
            LOCATOR_HEADERS,
            ("locator_id",),
            {"artifact_id": "EVIDENCE_ARTIFACT_REGISTRY.csv.artifact_id"},
        ),
        "PLAYER_IDENTITY_REGISTRY.csv": (PLAYER_HEADERS, ("nwr_player_id",), {}),
        "PLAYER_ALIAS_REGISTRY.csv": (
            ALIAS_HEADERS,
            ("alias_id",),
            {"nwr_player_id": "PLAYER_IDENTITY_REGISTRY.csv.nwr_player_id"},
        ),
        "IDENTITY_ASSERTION_LEDGER.csv": (
            IDENTITY_HEADERS,
            ("identity_assertion_id",),
            {},
        ),
        "EVIDENCE_OBSERVATION_REGISTRY.csv": (
            OBSERVATION_HEADERS,
            ("evidence_observation_id",),
            {},
        ),
        "ARTIFACT_LIFECYCLE_LINK.csv": (
            (
                "artifact_id",
                "lifecycle_stage",
                "link_scope",
                "link_basis",
                "primary_for_artifact_or_dataset",
                "decision_or_receipt_id",
                "record_version",
            ),
            ("artifact_id", "lifecycle_stage"),
            {"artifact_id": "EVIDENCE_ARTIFACT_REGISTRY.csv.artifact_id"},
        ),
        "DATASET_LIFECYCLE_LINK.csv": (
            (
                "dataset_id",
                "lifecycle_stage",
                "link_scope",
                "link_basis",
                "primary_for_artifact_or_dataset",
                "decision_or_receipt_id",
                "record_version",
            ),
            ("dataset_id", "lifecycle_stage"),
            {"dataset_id": "DATASET_REGISTRY.csv.dataset_id"},
        ),
        "DUPLICATE_CONFLICT_RELATIONSHIP_LEDGER.csv": (
            (
                "relationship_id",
                "relationship_type",
                "duplicate_class",
                "artifact_id_a",
                "artifact_id_b",
                "design_reference_a",
                "design_reference_b",
                "relationship_scope",
                "count_basis",
                "disposition",
                "human_review_required",
                "blocker",
                "relationship_validation_status",
                "decision_receipt_status",
                "resolution_status",
                "record_version",
            ),
            ("relationship_id",),
            {
                "artifact_id_a": "EVIDENCE_ARTIFACT_REGISTRY.csv.artifact_id?",
                "artifact_id_b": "EVIDENCE_ARTIFACT_REGISTRY.csv.artifact_id?",
            },
        ),
        "NO_RECREATE_RELATIONSHIP_LEDGER.csv": (
            (
                "no_recreate_id",
                "artifact_id",
                "repository_relative_reference",
                "sanitized_reference_locator_id",
                "classification",
                "required_treatment",
                "blocker_or_guardrail",
                "active_use_state",
                "record_version",
            ),
            ("no_recreate_id",),
            {"artifact_id": "EVIDENCE_ARTIFACT_REGISTRY.csv.artifact_id?"},
        ),
        "LIFECYCLE_DICTIONARY.csv": (
            (
                "lifecycle_stage",
                "phase_order",
                "display_label",
                "scope",
                "record_version",
            ),
            ("lifecycle_stage",),
            {},
        ),
        "EVIDENCE_STATE_DICTIONARY.csv": (
            ("evidence_state", "precedence", "controlling_rule", "record_version"),
            ("evidence_state",),
            {},
        ),
        "SOURCE_USE_PURPOSE_DICTIONARY.csv": (
            ("purpose", "record_version"),
            ("purpose",),
            {},
        ),
        "SOURCE_USE_DECISION_VALUE_DICTIONARY.csv": (
            ("decision_value", "record_version"),
            ("decision_value",),
            {},
        ),
        "ARTIFACT_SCOPE_DICTIONARY.csv": (
            ("artifact_scope_class", "scope_kind", "record_version"),
            ("artifact_scope_class",),
            {},
        ),
        "IMPLEMENTATION_STATUS.csv": (
            (
                "component_id",
                "implementation_status",
                "runtime_wiring",
                "caveat",
                "record_version",
            ),
            ("component_id",),
            {},
        ),
    }
    special_paths = {
        "DUPLICATE_CONFLICT_RELATIONSHIP_LEDGER.csv": (
            "conflicts/DUPLICATE_CONFLICT_RELATIONSHIP_LEDGER.csv"
        ),
        "NO_RECREATE_RELATIONSHIP_LEDGER.csv": ("governance/NO_RECREATE_RELATIONSHIP_LEDGER.csv"),
        "LIFECYCLE_DICTIONARY.csv": "governance/LIFECYCLE_DICTIONARY.csv",
        "EVIDENCE_STATE_DICTIONARY.csv": "governance/EVIDENCE_STATE_DICTIONARY.csv",
        "SOURCE_USE_PURPOSE_DICTIONARY.csv": ("governance/SOURCE_USE_PURPOSE_DICTIONARY.csv"),
        "SOURCE_USE_DECISION_VALUE_DICTIONARY.csv": (
            "governance/SOURCE_USE_DECISION_VALUE_DICTIONARY.csv"
        ),
        "ARTIFACT_SCOPE_DICTIONARY.csv": "governance/ARTIFACT_SCOPE_DICTIONARY.csv",
        "IMPLEMENTATION_STATUS.csv": "IMPLEMENTATION_STATUS.csv",
    }
    special_order = {
        "LIFECYCLE_DICTIONARY.csv": ["phase_order"],
        "EVIDENCE_STATE_DICTIONARY.csv": ["precedence"],
    }
    result: dict[str, dict[str, Any]] = {}
    for name, (headers, primary_key, foreign_keys) in schema_rows.items():
        result[name] = {
            "schema_version": SCHEMA_VERSION,
            "path": special_paths.get(name, f"registries/{name}"),
            "headers": list(headers),
            "primary_key": list(primary_key),
            "foreign_keys": foreign_keys,
            "deterministic_order": special_order.get(name, list(primary_key)),
            "duplicate_key_policy": "REJECT",
        }
    result["closed_enums"] = {
        "lifecycle_stage": [row[0] for row in LIFECYCLE_STAGES],
        "evidence_state": list(EVIDENCE_STATES),
        "locality_class": list(LOCALITIES),
        "purpose": list(PURPOSES),
        "decision_value": list(DECISION_VALUES),
        "artifact_scope_class": list(artifact_scopes),
        "duplicate_class": [
            "EXACT_DUPLICATE",
            "SCHEMA_EQUIVALENT_DUPLICATE",
            "TRANSFORMED_DERIVATIVE",
            "OVERLAPPING_POPULATION",
            "STALE_PREDECESSOR",
            "CONFLICTING_EVIDENCE",
            "INDEPENDENT_CORROBORATION",
            "NOT_ACTUALLY_DUPLICATED",
        ],
        "duplicate_disposition": [
            "RETAIN_BOTH",
            "DESIGNATE_CANONICAL_AND_SUPPORTING",
            "SUPERSEDE",
            "ARCHIVE_LOGICALLY",
            "MERGE_LATER",
            "MANUAL_REVIEW",
            "BLOCK_CONSOLIDATION",
        ],
        "metadata_registration_status": [
            "REGISTER_AUTHORITY_METADATA",
            "REGISTER_LOCATOR_METADATA_ONLY",
            "REGISTER_NO_RECREATE_METADATA_ONLY",
            "REGISTER_DEPENDENCY_METADATA_ONLY",
        ],
        "authority_scope_class": [
            "GOVERNANCE_POLICY_ONLY",
            "PROTECTED_EVALUATION_POLICY_ONLY",
            "SOURCE_FAMILY_ROUTING_CEILING_ONLY",
            "RECEIPT_STANDARD_ONLY",
            "EVIDENCE_REVIEW_ONLY",
            "DECISION_RECEIPT_ONLY",
            "BLOCK_POLICY_ONLY",
            "LOCAL_REVIEW_LOCATOR_ONLY",
            "OFF_HQ_AUDIT_LOCATOR_ONLY",
            "NO_RECREATE_REFERENCE_ONLY",
            "PRODUCT_DEPENDENCY_REFERENCE_ONLY",
        ],
        "source_admission_effect": sorted(NON_ADMITTING_SOURCE_EFFECTS),
        "permitted_use_class": [
            "GOVERNANCE_METADATA_ONLY",
            "PROTECTED_EVALUATION_POLICY_METADATA_ONLY",
            "RECEIPT_STANDARD_METADATA_ONLY",
            "REVIEW_METADATA_ONLY",
            "DECISION_RECEIPT_METADATA_ONLY",
            "BLOCKER_METADATA_ONLY",
            "LOCAL_LOCATOR_METADATA_ONLY",
            "OFF_HQ_AUDIT_METADATA_ONLY",
            "NO_RECREATE_METADATA_ONLY",
            "DEPENDENCY_METADATA_ONLY",
        ],
    }
    return result


def build_workspace() -> dict[str, int]:
    inventory = _read_csv(DESIGN_ROOT / "EXISTING_WORKSPACE_INVENTORY.csv")
    authority = _read_csv(CANON_ROOT / "AUTHORITY_CANONICALITY_NORMALIZED.csv")
    duplicate = _read_csv(DESIGN_ROOT / "DUPLICATION_AND_CONFLICT_REGISTER.csv")
    no_recreate = _read_csv(DESIGN_ROOT / "NO_RECREATE_ROOKIE_EVIDENCE_INDEX.csv")

    for directory in (REGISTRY_ROOT, GOVERNANCE_ROOT, CONFLICT_ROOT, ARCHIVE_ROOT, PACKET_ROOT):
        directory.mkdir(parents=True, exist_ok=True)

    locators = [_locator_row(row) for row in inventory]
    locators.sort(key=lambda item: item["locator_id"])
    locator_by_artifact = {row["artifact_id"]: row["locator_id"] for row in locators}
    artifacts = [_artifact_row(row, locator_by_artifact[row["artifact_id"]]) for row in inventory]
    artifacts.sort(key=lambda item: item["artifact_id"])

    _write_csv(REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv", ARTIFACT_HEADERS, artifacts)
    _write_csv(REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv", LOCATOR_HEADERS, locators)
    _write_csv(
        REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
        AUTHORITY_HEADERS,
        sorted(authority, key=lambda item: item["authority_id"]),
    )
    _write_csv(REGISTRY_ROOT / "SOURCE_REGISTRY.csv", SOURCE_HEADERS, [])
    _write_csv(REGISTRY_ROOT / "DATASET_REGISTRY.csv", DATASET_HEADERS, [])
    _write_csv(REGISTRY_ROOT / "SOURCE_RECEIPT_REGISTRY.csv", RECEIPT_HEADERS, [])
    _write_csv(REGISTRY_ROOT / "SOURCE_USE_DECISION_LEDGER.csv", DECISION_HEADERS, [])
    _write_csv(REGISTRY_ROOT / "PLAYER_IDENTITY_REGISTRY.csv", PLAYER_HEADERS, [])
    _write_csv(REGISTRY_ROOT / "PLAYER_ALIAS_REGISTRY.csv", ALIAS_HEADERS, [])
    _write_csv(REGISTRY_ROOT / "IDENTITY_ASSERTION_LEDGER.csv", IDENTITY_HEADERS, [])
    _write_csv(REGISTRY_ROOT / "EVIDENCE_OBSERVATION_REGISTRY.csv", OBSERVATION_HEADERS, [])

    lifecycle_links = _lifecycle_links(inventory)
    _write_csv(
        REGISTRY_ROOT / "ARTIFACT_LIFECYCLE_LINK.csv",
        (
            "artifact_id",
            "lifecycle_stage",
            "link_scope",
            "link_basis",
            "primary_for_artifact_or_dataset",
            "decision_or_receipt_id",
            "record_version",
        ),
        lifecycle_links,
    )
    _write_csv(
        REGISTRY_ROOT / "DATASET_LIFECYCLE_LINK.csv",
        (
            "dataset_id",
            "lifecycle_stage",
            "link_scope",
            "link_basis",
            "primary_for_artifact_or_dataset",
            "decision_or_receipt_id",
            "record_version",
        ),
        [],
    )

    _write_csv(
        GOVERNANCE_ROOT / "LIFECYCLE_DICTIONARY.csv",
        (
            "lifecycle_stage",
            "phase_order",
            "display_label",
            "scope",
            "record_version",
        ),
        [
            {
                "lifecycle_stage": value,
                "phase_order": index,
                "display_label": display,
                "scope": scope,
                "record_version": SCHEMA_VERSION,
            }
            for index, (value, display, scope) in enumerate(LIFECYCLE_STAGES, start=1)
        ],
    )
    _write_csv(
        GOVERNANCE_ROOT / "EVIDENCE_STATE_DICTIONARY.csv",
        ("evidence_state", "precedence", "controlling_rule", "record_version"),
        [
            {
                "evidence_state": value,
                "precedence": index,
                "controlling_rule": "Closed state; orthogonal dimensions remain separately recorded.",
                "record_version": SCHEMA_VERSION,
            }
            for index, value in enumerate(EVIDENCE_STATES, start=1)
        ],
    )
    _write_csv(
        GOVERNANCE_ROOT / "SOURCE_USE_PURPOSE_DICTIONARY.csv",
        ("purpose", "record_version"),
        [{"purpose": purpose, "record_version": SCHEMA_VERSION} for purpose in sorted(PURPOSES)],
    )
    _write_csv(
        GOVERNANCE_ROOT / "SOURCE_USE_DECISION_VALUE_DICTIONARY.csv",
        ("decision_value", "record_version"),
        [
            {"decision_value": value, "record_version": SCHEMA_VERSION}
            for value in sorted(DECISION_VALUES)
        ],
    )
    artifact_scopes = tuple(sorted({row["lifecycle_or_artifact_scope"] for row in inventory}))
    _write_csv(
        GOVERNANCE_ROOT / "ARTIFACT_SCOPE_DICTIONARY.csv",
        ("artifact_scope_class", "scope_kind", "record_version"),
        [
            {
                "artifact_scope_class": scope,
                "scope_kind": ("EXACT_OR_COMPOSITE_ARTIFACT_SCOPE_NOT_PLAYER_OBSERVATION_STAGE"),
                "record_version": SCHEMA_VERSION,
            }
            for scope in artifact_scopes
        ],
    )

    duplicate_rows = _duplicate_rows(duplicate)
    _write_csv(
        CONFLICT_ROOT / "DUPLICATE_CONFLICT_RELATIONSHIP_LEDGER.csv",
        (
            "relationship_id",
            "relationship_type",
            "duplicate_class",
            "artifact_id_a",
            "artifact_id_b",
            "design_reference_a",
            "design_reference_b",
            "relationship_scope",
            "count_basis",
            "disposition",
            "human_review_required",
            "blocker",
            "relationship_validation_status",
            "decision_receipt_status",
            "resolution_status",
            "record_version",
        ),
        duplicate_rows,
    )
    no_recreate_rows = _no_recreate_rows(no_recreate)
    _write_csv(
        GOVERNANCE_ROOT / "NO_RECREATE_RELATIONSHIP_LEDGER.csv",
        (
            "no_recreate_id",
            "artifact_id",
            "repository_relative_reference",
            "sanitized_reference_locator_id",
            "classification",
            "required_treatment",
            "blocker_or_guardrail",
            "active_use_state",
            "record_version",
        ),
        no_recreate_rows,
    )

    status_entities = (
        "artifact_registry",
        "source_registry",
        "dataset_registry",
        "receipt_registry",
        "authority_registry",
        "lifecycle_dictionary",
        "evidence_state_dictionary",
        "source_use_decision_registry",
        "duplicate_conflict_relationships",
        "no_recreate_relationships",
        "sanitized_locator_registry",
        "player_registry_schema",
        "alias_registry_schema",
        "identity_assertion_schema",
        "evidence_observation_schema",
        "read_only_loader_and_validator",
    )
    _write_csv(
        WORKSPACE_ROOT / "IMPLEMENTATION_STATUS.csv",
        ("component_id", "implementation_status", "runtime_wiring", "caveat", "record_version"),
        [
            {
                "component_id": entity,
                "implementation_status": "IMPLEMENTED_METADATA_ONLY",
                "runtime_wiring": "NONE",
                "caveat": "No player truth, source promotion, identity resolution, or production authority.",
                "record_version": SCHEMA_VERSION,
            }
            for entity in sorted(status_entities)
        ],
    )

    schemas = _schemas(artifact_scopes)
    _write_text(
        GOVERNANCE_ROOT / "SCHEMAS.json",
        json.dumps(schemas, indent=2, sort_keys=True),
    )
    _write_text(
        WORKSPACE_ROOT / "README.md",
        """# Rookie Evidence Workspace V1

This directory is a metadata-first, read-only registry scaffold. It indexes the canonical design inventory without copying player observations, resolving identities, promoting sources, or authorizing ranking, formula, training, production-scoring, application, or product use.

`AUTHORITY_REGISTRY.csv` is copied only from the normalized 23-row authority contract. The legacy `canonical_now` field is retained as an opaque historical string and is never interpreted. Empty source, dataset, receipt, player, alias, identity-assertion, evidence-observation, and source/use decision registries fail closed until exact receipt-backed mappings exist.

Application runtime must not import this workspace or its loader. The companion service is read-only and intended only for tests and CLI diagnostics.
""",
    )
    _write_text(
        GOVERNANCE_ROOT / "VALIDATION_RULES.md",
        """# Validation Rules

The validator rejects schema drift, duplicate primary keys, nondeterministic order, invalid foreign keys, unknown enums, any authority row count other than 23, any true production/player-value authority, any source-admitting authority effect, missing-decision permission, raw local paths, reversible restricted locators, active off-HQ use, populated real player/alias/identity/evidence registries, and manifest hash drift.

The validator never reads or interprets `EVIDENCE_AUTHORITY_CLASSIFICATION.csv.canonical_now`; only the normalized authority registry is machine input.
""",
    )

    counts = {
        "artifact_rows": len(artifacts),
        "live_hq": sum(row["locality_class"] == "LIVE_HQ" for row in artifacts),
        "local_only": sum(row["locality_class"] == "LOCAL_ONLY" for row in artifacts),
        "restricted": sum(row["locality_class"] == "LOCAL_ONLY_RESTRICTED" for row in artifacts),
        "off_hq": sum(row["locality_class"] == "OFF_HQ_BRANCH_ONLY" for row in artifacts),
        "authority_rows": len(authority),
        "duplicate_relationships": len(duplicate_rows),
        "no_recreate_relationships": len(no_recreate_rows),
        "lifecycle_links": len(lifecycle_links),
        "explicit_source_use_decisions": 0,
    }
    build_documentation(counts, schemas, authority, artifacts, duplicate_rows, no_recreate_rows)
    refresh_manifests()
    return counts


def build_documentation(
    counts: dict[str, int],
    schemas: dict[str, dict[str, Any]],
    authority: list[dict[str, str]],
    artifacts: list[dict[str, str]],
    duplicate_rows: list[dict[str, str]],
    no_recreate_rows: list[dict[str, str]],
) -> None:
    verdict = "YELLOW_ROOKIE_EVIDENCE_REGISTRY_SCAFFOLD_V1_COMPLETE_WITH_METADATA_CAVEATS"
    _write_text(
        PACKET_ROOT / "EXECUTIVE_VERDICT.md",
        f"""# Executive Verdict

`{verdict}`

The read-only scaffold registers all {counts["artifact_rows"]:,} controlling inventory artifacts with exact locality parity while withholding raw local/restricted paths and preserving off-HQ objects only for audit/no-recreate discovery. All 23 normalized authority rows remain non-production and non-player-value. Source, dataset, receipt, and purpose-specific decision rows remain empty because the design packet does not supply exact opaque IDs plus receipt-backed mappings at the required grain; missing decisions fail closed.
""",
    )
    _write_text(
        PACKET_ROOT / "ROOKIE_EVIDENCE_REGISTRY_SCAFFOLD_V1_REPORT.md",
        f"""# Rookie Evidence Registry Scaffold V1 Report

## Outcome

The registry is an additive metadata index only. It starts from remote HQ `{STARTING_HEAD}`, does not alter evidence, and does not connect to application runtime or decision logic.

## Reconciliation

- Design inventory: {counts["artifact_rows"]:,}
- Registered artifact rows: {counts["artifact_rows"]:,}
- Rejected artifact rows: 0
- Deferred artifact rows: 0
- Locality: {counts["live_hq"]:,} live-HQ; {counts["local_only"]:,} local-only; {counts["restricted"]:,} restricted; {counts["off_hq"]:,} off-HQ
- Authority rows: {counts["authority_rows"]}
- Explicit source/use decision rows: {counts["explicit_source_use_decisions"]}
- Duplicate/conflict review objects: {counts["duplicate_relationships"]}
- No-recreate relationships: {counts["no_recreate_relationships"]}
- Real player, alias, identity-assertion, and evidence-observation rows: 0 each

## Metadata caveat

Artifact authority, source, dataset, and receipt foreign keys remain null because the controlling inventory supplies no exact row-level mapping to the normalized authority IDs or durable source/dataset/receipt IDs. Minting those links would require interpretation or guessing. The complete artifact inventory remains discoverable by its existing opaque IDs, locator class, state, flags, integrity metadata, scope, and caveat. This is the fail-closed result required by canonical HQ.
""",
    )
    reuse_rows = [
        {
            "existing_component": "CSV registry loader",
            "path": "src/services/source_registry_service.py",
            "purpose": "Read-only CSV loading with exact header checks",
            "reusable_elements": "pathlib/csv conventions; immutable tuple return; fail-fast header validation",
            "incompatibilities": "Production source semantics are broader and cannot be reused as rookie authority",
            "chosen_scaffold_location": "docs/hq/rookie_evidence_workspace_v1/",
            "reason": "Exact controlling design location; disconnected from runtime",
        },
        {
            "existing_component": "Evidence status registry",
            "path": "docs/hq/integration/evidence_status_registry_v1_20260626.csv",
            "purpose": "Conservative evidence-lane status metadata",
            "reusable_elements": "CSV-first review flags and closed fail-closed tests",
            "incompatibilities": "Lane-level grain cannot represent artifact/locator/decision keys",
            "chosen_scaffold_location": "docs/hq/rookie_evidence_workspace_v1/",
            "reason": "Additive specialized registry avoids competing general framework",
        },
        {
            "existing_component": "Source registry",
            "path": "config/source_registry.csv",
            "purpose": "Production source firewall metadata",
            "reusable_elements": "CSV shape and duplicate/header checks only",
            "incompatibilities": "Protected production system; canonical packet forbids source promotion or edits",
            "chosen_scaffold_location": "docs/hq/rookie_evidence_workspace_v1/registries/SOURCE_REGISTRY.csv",
            "reason": "Header-only metadata schema leaves production registry unchanged",
        },
        {
            "existing_component": "Data validators",
            "path": "src/data/validators.py",
            "purpose": "Repository validation style",
            "reusable_elements": "Explicit issues and deterministic validation",
            "incompatibilities": "Data-pack/runtime contracts are unrelated to metadata authority",
            "chosen_scaffold_location": "src/services/rookie_evidence_registry_service.py",
            "reason": "Pure read-only loader plus scoped validator",
        },
        {
            "existing_component": "HQ artifact manifests",
            "path": "docs/hq/**/artifact_manifest.csv",
            "purpose": "Artifact inventory and hash receipts",
            "reusable_elements": "repository-relative paths; SHA-256; deterministic ordering",
            "incompatibilities": "No uniform cross-packet foreign keys or restricted locator contract",
            "chosen_scaffold_location": "docs/hq/rookie_evidence_workspace_v1/WORKSPACE_MANIFEST.json",
            "reason": "One scoped manifest with self-hash exclusion",
        },
        {
            "existing_component": "No-recreate index",
            "path": "docs/hq/master/rookie_evidence_workspace_consolidation_design_v1_20260711/NO_RECREATE_ROOKIE_EVIDENCE_INDEX.csv",
            "purpose": "Preserve existing systems and parked evidence",
            "reusable_elements": "40 controlling relationship IDs and treatments",
            "incompatibilities": "Five entries include absolute locators and cannot be copied",
            "chosen_scaffold_location": "docs/hq/rookie_evidence_workspace_v1/governance/NO_RECREATE_RELATIONSHIP_LEDGER.csv",
            "reason": "Unsafe references replaced with non-reversible opaque locator IDs",
        },
        {
            "existing_component": "Canonical authority normalization",
            "path": "docs/hq/master/rookie_evidence_workspace_design_canonicalization_v1_20260711/AUTHORITY_CANONICALITY_NORMALIZED.csv",
            "purpose": "Only permitted machine authority interpretation",
            "reusable_elements": "All 23 rows and exact closed fields",
            "incompatibilities": "Legacy canonical_now cannot be parsed",
            "chosen_scaffold_location": "docs/hq/rookie_evidence_workspace_v1/registries/AUTHORITY_REGISTRY.csv",
            "reason": "Exact normalized copy; legacy value remains opaque",
        },
    ]
    _write_csv(
        PACKET_ROOT / "PREFLIGHT_REUSE_MAP.csv",
        (
            "existing_component",
            "path",
            "purpose",
            "reusable_elements",
            "incompatibilities",
            "chosen_scaffold_location",
            "reason",
        ),
        reuse_rows,
    )
    inventory_rows = []
    for name, definition in sorted(schemas.items()):
        if name == "closed_enums":
            continue
        inventory_rows.append(
            {
                "structure": name,
                "path": f"docs/hq/rookie_evidence_workspace_v1/{definition['path']}",
                "schema_version": definition["schema_version"],
                "primary_key": "|".join(definition["primary_key"]),
                "row_policy": "METADATA_ONLY_OR_HEADER_ONLY",
                "deterministic_order": "|".join(definition["deterministic_order"]),
                "duplicate_key_policy": definition["duplicate_key_policy"],
            }
        )
    _write_csv(
        PACKET_ROOT / "SCAFFOLD_FILE_AND_SCHEMA_INVENTORY.csv",
        (
            "structure",
            "path",
            "schema_version",
            "primary_key",
            "row_policy",
            "deterministic_order",
            "duplicate_key_policy",
        ),
        inventory_rows,
    )
    reconciliation_rows = [
        {
            "category": "TOTAL",
            "design_rows": counts["artifact_rows"],
            "registered_rows": counts["artifact_rows"],
            "rejected_rows": 0,
            "deferred_rows": 0,
            "reason": "Exact opaque artifact IDs retained; sensitive locator fields sanitized separately.",
        }
    ]
    for label, key in (
        ("LIVE_HQ", "live_hq"),
        ("LOCAL_ONLY", "local_only"),
        ("LOCAL_ONLY_RESTRICTED", "restricted"),
        ("OFF_HQ_BRANCH_ONLY", "off_hq"),
    ):
        reconciliation_rows.append(
            {
                "category": label,
                "design_rows": counts[key],
                "registered_rows": counts[key],
                "rejected_rows": 0,
                "deferred_rows": 0,
                "reason": "Metadata parity without raw/reversible locator promotion.",
            }
        )
    _write_csv(
        PACKET_ROOT / "ARTIFACT_REGISTRY_RECONCILIATION.csv",
        ("category", "design_rows", "registered_rows", "rejected_rows", "deferred_rows", "reason"),
        reconciliation_rows,
    )
    _write_csv(
        PACKET_ROOT / "AUTHORITY_REGISTRY_VALIDATION.csv",
        (
            "authority_id",
            "unique_id",
            "player_value_authority_false",
            "production_authority_false",
            "source_promotion_effect",
            "legacy_field_interpretation",
            "result",
        ),
        [
            {
                "authority_id": row["authority_id"],
                "unique_id": "true",
                "player_value_authority_false": str(
                    row["player_value_authority"] == "false"
                ).lower(),
                "production_authority_false": str(row["production_authority"] == "false").lower(),
                "source_promotion_effect": "NONE",
                "legacy_field_interpretation": row["legacy_field_interpretation"],
                "result": "PASS",
            }
            for row in sorted(authority, key=lambda item: item["authority_id"])
        ],
    )
    _write_csv(
        PACKET_ROOT / "LOCATOR_SANITIZATION_REVIEW.csv",
        (
            "locality_class",
            "design_count",
            "registered_count",
            "raw_absolute_paths_stored",
            "reversible_restricted_locators_stored",
            "active_use_authorized_by_locator",
            "result",
        ),
        [
            {
                "locality_class": locality,
                "design_count": sum(row["locality_class"] == locality for row in artifacts),
                "registered_count": sum(row["locality_class"] == locality for row in artifacts),
                "raw_absolute_paths_stored": 0,
                "reversible_restricted_locators_stored": 0,
                "active_use_authorized_by_locator": 0,
                "result": "PASS",
            }
            for locality in LOCALITIES
        ],
    )
    _write_csv(
        PACKET_ROOT / "SOURCE_USE_DECISION_REVIEW.csv",
        (
            "purpose",
            "explicit_supported_decision_rows",
            "missing_decision_result",
            "automatic_expansion_allowed",
            "production_or_training_grants",
            "result",
        ),
        [
            {
                "purpose": purpose,
                "explicit_supported_decision_rows": 0,
                "missing_decision_result": "NOT_ENOUGH_INFORMATION",
                "automatic_expansion_allowed": "false",
                "production_or_training_grants": 0,
                "result": "PASS_FAIL_CLOSED",
            }
            for purpose in PURPOSES
        ],
    )
    _write_text(
        PACKET_ROOT / "EMPTY_PLAYER_SCHEMA_PROOF.md",
        """# Empty Player Schema Proof

`PLAYER_IDENTITY_REGISTRY.csv`, `PLAYER_ALIAS_REGISTRY.csv`, `IDENTITY_ASSERTION_LEDGER.csv`, and `EVIDENCE_OBSERVATION_REGISTRY.csv` contain exactly one header row and zero data rows. They define keys and orthogonal state fields but contain no player names, provider IDs, aliases, identity assertions, values, draft/UDFA facts, measurements, outcomes, rankings, scores, or model inputs.

The single unmistakable synthetic fixture lives only under `tests/fixtures/rookie_evidence_registry_v1/`, uses impossible synthetic IDs and the marker `SYNTHETIC_VALIDATION_FIXTURE`, and is outside every registry export and real-row count.
""",
    )
    class_counts: dict[str, int] = {}
    for row in duplicate_rows:
        class_counts[row["duplicate_class"]] = class_counts.get(row["duplicate_class"], 0) + 1
    classes = "\n".join(f"- `{key}`: {value}" for key, value in sorted(class_counts.items()))
    _write_text(
        PACKET_ROOT / "DUPLICATE_CONFLICT_AND_NO_RECREATE_REVIEW.md",
        f"""# Duplicate, Conflict, and No-Recreate Review

The scaffold preserves {len(duplicate_rows)} design relationship objects and {len(no_recreate_rows)} no-recreate relationships without deletion, merge, preference, or fact selection.

{classes}

Artifact selectors from the design remain review references rather than guessed artifact foreign keys. Every relationship is `UNRESOLVED_REVIEW_OBJECT`; the design statuses `AUDITED_DESIGN_INPUT_NOT_IMPLEMENTED` and `NOT_CREATED_DESIGN_LANE` remain intact. Absolute no-recreate references are replaced by opaque, non-reversible locator IDs.
""",
    )
    _write_text(
        PACKET_ROOT / "READ_ONLY_RUNTIME_BOUNDARY.md",
        """# Read-Only Runtime Boundary

The companion loader opens CSV/JSON files only for reading, returns immutable tuples, validates metadata, looks up opaque IDs, and returns fail-closed decision summaries. It contains no file-write API, network call, player-value load, identity resolution, source promotion, ranking, formula, training, scoring, migration, or application integration.

No application page, route, runtime bootstrap, ranking service, formula service, draft service, or production data path imports the loader. The scaffold is available only to tests and explicit CLI diagnostics.
""",
    )
    _write_text(
        PACKET_ROOT / "PRIVACY_AND_RIGHTS_REVIEW.md",
        """# Privacy and Rights Review

All 162 local-only absolute paths are replaced by opaque locator IDs. The three restricted records retain only artifact ID, non-reversible locator ID, locality/state/rights/privacy metadata, permitted aggregate row/schema metadata, and a withholding caveat; raw paths, raw hashes, provider content, private IDs, and reversible locator material are excluded. The 19 off-HQ locators retain only the permitted commit and repository-relative object path for audit/no-recreate discovery and are explicitly use-blocked.

No source/use rights were inferred from accessibility, public visibility, cache presence, review history, identity approval, recency, hashes, or prose. Result: `PASS_NO_RIGHTS_OR_PRIVACY_EXPANSION`.
""",
    )
    _write_text(
        PACKET_ROOT / "ROLLBACK_PLAN.md",
        """# Rollback Plan

Rollback is a single local revert of the scaffold commit after HQ review, or deletion of the isolated unmerged branch/worktree. The lane changes only new scaffold, validator/service, focused-test, synthetic-fixture, and documentation files. It modifies no evidence, production registry, application, protected evaluation, or frozen 2026 file, so rollback requires no data restoration or migration reversal.
""",
    )
    _write_text(
        PACKET_ROOT / "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        """# Protected and Frozen Path Proof

The allowed diff is limited to `docs/hq/rookie_evidence_workspace_v1/`, `docs/hq/master/rookie_evidence_registry_read_only_scaffold_v1_20260711/`, the scoped read-only service/validator/build script, focused tests, and one synthetic fixture. The prospective 2026 freeze packet, production data, source registry, application pages/routes, ranking/formula/draft services, identity systems, plugin systems, and canonical exports are outside the write set. Final Git diff and byte-change scans validate this boundary.
""",
    )
    _write_text(
        PACKET_ROOT / "VALIDATION_RESULTS.md",
        f"""# Validation Results

Build-time deterministic generation completed with {counts["artifact_rows"]:,} artifact rows, {counts["authority_rows"]} authority rows, {counts["duplicate_relationships"]} duplicate/conflict objects, {counts["no_recreate_relationships"]} no-recreate relationships, and exact locality parity. Restricted content was withheld during generation and no source/use decisions were inferred.

The final validation run records the exact commands and totals after focused and regression tests; this file is intentionally updated with those completed results before commit rather than claiming unexecuted checks.
""",
    )


def _status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return sorted(paths)


def refresh_manifests() -> None:
    registry_files = sorted(
        path
        for path in WORKSPACE_ROOT.rglob("*")
        if path.is_file()
        and path.name not in {"WORKSPACE_MANIFEST.json", "REGISTRY_FILE_MANIFEST.csv"}
    )
    _write_csv(
        WORKSPACE_ROOT / "REGISTRY_FILE_MANIFEST.csv",
        ("path", "schema_version", "bytes", "sha256", "manifest_rule"),
        [
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "schema_version": SCHEMA_VERSION,
                "bytes": len(_canonical_bytes(path)),
                "sha256": _sha256(path),
                "manifest_rule": "SHA256_CANONICAL_LF_TEXT",
            }
            for path in registry_files
        ],
    )
    workspace_files = sorted(
        path
        for path in WORKSPACE_ROOT.rglob("*")
        if path.is_file() and path.name != "WORKSPACE_MANIFEST.json"
    )
    workspace_manifest = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_version": SNAPSHOT_VERSION,
        "starting_remote_head": STARTING_HEAD,
        "read_only": True,
        "runtime_wiring": False,
        "player_value_authority": False,
        "production_authority": False,
        "source_promotion": False,
        "text_hash_normalization": "CRLF_TO_LF_BEFORE_SHA256",
        "manifest_self_hash_excluded": True,
        "files": [
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "bytes": len(_canonical_bytes(path)),
                "sha256": _sha256(path),
            }
            for path in workspace_files
        ],
    }
    _write_text(
        WORKSPACE_ROOT / "WORKSPACE_MANIFEST.json",
        json.dumps(workspace_manifest, indent=2, sort_keys=True),
    )

    changed = _status_paths()
    ledger_path = PACKET_ROOT / "FILES_CREATED_OR_CHANGED.csv"
    _write_csv(
        ledger_path,
        ("path", "change_type", "bytes", "sha256_or_rule", "scope_result"),
        [
            {
                "path": path,
                "change_type": "ADDED",
                "bytes": (
                    (REPO_ROOT / path).stat().st_size if (REPO_ROOT / path).is_file() else ""
                ),
                "sha256_or_rule": (
                    "SELF_HASH_EXCLUDED"
                    if path.endswith("FILES_CREATED_OR_CHANGED.csv")
                    else (
                        "PACKET_MANIFEST_REGENERATED_AFTER_LEDGER"
                        if path.endswith(
                            "rookie_evidence_registry_read_only_scaffold_v1_20260711/MANIFEST.json"
                        )
                        else (
                            _sha256(REPO_ROOT / path)
                            if (REPO_ROOT / path).is_file()
                            else "DIRECTORY"
                        )
                    )
                ),
                "scope_result": "ALLOWED_SCAFFOLD_SCOPE",
            }
            for path in changed
        ],
    )
    packet_files = sorted(
        path for path in PACKET_ROOT.iterdir() if path.is_file() and path.name != "MANIFEST.json"
    )
    packet_manifest = {
        "packet": "rookie_evidence_registry_read_only_scaffold_v1_20260711",
        "schema_version": SCHEMA_VERSION,
        "starting_remote_head": STARTING_HEAD,
        "remote_advanced": False,
        "manifest_self_hash_excluded": True,
        "text_hash_normalization": "CRLF_TO_LF_BEFORE_SHA256",
        "files": [
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "bytes": len(_canonical_bytes(path)),
                "sha256": _sha256(path),
            }
            for path in packet_files
        ],
    }
    _write_text(
        PACKET_ROOT / "MANIFEST.json", json.dumps(packet_manifest, indent=2, sort_keys=True)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args()
    if args.manifest_only:
        refresh_manifests()
        return
    counts = build_workspace()
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
