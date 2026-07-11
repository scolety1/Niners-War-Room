from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT / "docs/hq/rookie_evidence_workspace_v1"
REGISTRY_ROOT = WORKSPACE_ROOT / "registries"
PACKET_ROOT = REPO_ROOT / "docs/hq/master/rookie_evidence_registry_read_only_scaffold_v1_20260711"
EXPECTED_LOCALITIES = {
    "LIVE_HQ": 1085,
    "LOCAL_ONLY": 162,
    "LOCAL_ONLY_RESTRICTED": 3,
    "OFF_HQ_BRANCH_ONLY": 19,
}
NON_ADMITTING_EFFECTS = {
    "NO_SOURCE_ADMISSION",
    "ROUTING_CEILING_ONLY",
    "SEPARATE_EXPLICIT_DECISION_REQUIRED",
    "BLOCKS_ADMISSION",
}
ABSOLUTE_PATH = re.compile(r"(?i)(?:^|[|;\s])(?:[a-z]:[\\/]|/Users/|/home/)")
RESTRICTED_SCHEME = re.compile(r"(?i)LOCAL_ONLY_RESTRICTED://")
GIT_LOCATOR = re.compile(r"(?i)git:[0-9a-f]{40}:")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    detail: str


@dataclass(frozen=True)
class ValidationReport:
    status: str
    check_count: int
    issue_count: int
    artifact_count: int
    authority_count: int
    explicit_decision_count: int
    real_player_row_count: int
    real_evidence_observation_row_count: int
    locality_counts: dict[str, int]
    evidence_state_counts: dict[str, int]
    duplicate_conflict_count: int
    no_recreate_count: int
    issues: tuple[ValidationIssue, ...]


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), [dict(row) for row in reader]


def _canonical_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".py"}:
        data = data.replace(b"\r\n", b"\n")
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest()


def _issue(issues: list[ValidationIssue], code: str, path: Path, detail: str) -> None:
    issues.append(ValidationIssue(code, path.relative_to(REPO_ROOT).as_posix(), detail))


def _validate_manifest(path: Path, issues: list[ValidationIssue]) -> int:
    checks = 1
    data = json.loads(path.read_text(encoding="utf-8"))
    for entry in data["files"]:
        checks += 1
        target = REPO_ROOT / entry["path"]
        if not target.is_file():
            _issue(issues, "manifest_missing_file", path, entry["path"])
            continue
        if len(_canonical_bytes(target)) != entry["bytes"]:
            _issue(issues, "manifest_byte_mismatch", target, str(entry["bytes"]))
        if _sha256(target) != entry["sha256"]:
            _issue(issues, "manifest_hash_mismatch", target, entry["sha256"])
    return checks


def _validate_schema_file(
    name: str,
    definition: dict[str, Any],
    issues: list[ValidationIssue],
) -> tuple[list[dict[str, str]], int]:
    path = WORKSPACE_ROOT / definition["path"]
    checks = 3
    if not path.is_file():
        _issue(issues, "schema_file_missing", path, name)
        return [], checks
    header, rows = _read_csv(path)
    expected = tuple(definition["headers"])
    if header != expected:
        _issue(issues, "header_mismatch", path, f"expected={expected}; actual={header}")
    primary_key = tuple(definition["primary_key"])
    keys = [tuple(row[field] for field in primary_key) for row in rows]
    if any(not all(key) for key in keys):
        _issue(issues, "blank_primary_key", path, "Primary-key component is blank")
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        _issue(issues, "duplicate_primary_key", path, str(duplicates[:3]))
    order_fields = tuple(definition["deterministic_order"])

    def order_key(row: dict[str, str]) -> tuple[int | str, ...]:
        return tuple(
            int(row[field]) if row[field].isdigit() else row[field] for field in order_fields
        )

    if rows != sorted(rows, key=order_key):
        _issue(issues, "nondeterministic_order", path, "Rows are not deterministically sorted")
    return rows, checks


def validate_registry(root: Path = WORKSPACE_ROOT) -> ValidationReport:
    if root != WORKSPACE_ROOT:
        raise ValueError("V1 validator accepts only the fixed read-only workspace root")
    issues: list[ValidationIssue] = []
    checks = 0
    schema_path = root / "governance/SCHEMAS.json"
    schemas = json.loads(schema_path.read_text(encoding="utf-8"))
    rows_by_file: dict[str, list[dict[str, str]]] = {}
    for name, definition in schemas.items():
        if name == "closed_enums":
            continue
        rows, count = _validate_schema_file(name, definition, issues)
        rows_by_file[name] = rows
        checks += count

    artifacts = rows_by_file["EVIDENCE_ARTIFACT_REGISTRY.csv"]
    authorities = rows_by_file["AUTHORITY_REGISTRY.csv"]
    sources = rows_by_file["SOURCE_REGISTRY.csv"]
    datasets = rows_by_file["DATASET_REGISTRY.csv"]
    receipts = rows_by_file["SOURCE_RECEIPT_REGISTRY.csv"]
    decisions = rows_by_file["SOURCE_USE_DECISION_LEDGER.csv"]
    locators = rows_by_file["SANITIZED_LOCATOR_REGISTRY.csv"]
    lifecycle_links = rows_by_file["ARTIFACT_LIFECYCLE_LINK.csv"]
    dataset_lifecycle_links = rows_by_file["DATASET_LIFECYCLE_LINK.csv"]

    checks += 12
    if len(artifacts) != 1269:
        _issue(
            issues,
            "artifact_count",
            REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
            str(len(artifacts)),
        )
    locality_counts = Counter(row["locality_class"] for row in artifacts)
    if dict(locality_counts) != EXPECTED_LOCALITIES:
        _issue(
            issues,
            "locality_reconciliation",
            REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
            str(dict(locality_counts)),
        )
    evidence_states = set(schemas["closed_enums"]["evidence_state"])
    unknown_states = sorted({row["evidence_state"] for row in artifacts} - evidence_states)
    if unknown_states:
        _issue(
            issues,
            "unknown_evidence_state",
            REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
            str(unknown_states),
        )
    if {row["locality_class"] for row in artifacts} - set(
        schemas["closed_enums"]["locality_class"]
    ):
        _issue(
            issues,
            "unknown_locality",
            REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
            "Unknown locality",
        )

    if len(authorities) != 23:
        _issue(
            issues,
            "authority_count",
            REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
            str(len(authorities)),
        )
    authority_ids = {row["authority_id"] for row in authorities}
    if len(authority_ids) != len(authorities):
        _issue(
            issues,
            "authority_duplicate",
            REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
            "Duplicate authority ID",
        )
    for row in authorities:
        if row["production_authority"] != "false":
            _issue(
                issues,
                "production_authority_true",
                REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
                row["authority_id"],
            )
        if row["player_value_authority"] != "false":
            _issue(
                issues,
                "player_value_authority_true",
                REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
                row["authority_id"],
            )
        if row["source_admission_effect"] not in NON_ADMITTING_EFFECTS:
            _issue(
                issues,
                "source_promotion",
                REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
                row["authority_id"],
            )
        if row["legacy_field_interpretation"] != "NON_MACHINE_INTERPRETABLE_LEGACY_SCOPE_FIELD":
            _issue(
                issues,
                "legacy_field_interpretation",
                REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
                row["authority_id"],
            )
        for field in (
            "metadata_registration_status",
            "authority_scope_class",
            "source_admission_effect",
            "permitted_use_class",
        ):
            if row[field] not in set(schemas["closed_enums"][field]):
                _issue(
                    issues,
                    "authority_enum",
                    REGISTRY_ROOT / "AUTHORITY_REGISTRY.csv",
                    f"{row['authority_id']}:{field}",
                )

    artifact_ids = {row["artifact_id"] for row in artifacts}
    locator_ids = {row["locator_id"] for row in locators}
    if len(locators) != 1269:
        _issue(
            issues,
            "locator_count",
            REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
            str(len(locators)),
        )
    if {row["artifact_id"] for row in locators} != artifact_ids:
        _issue(
            issues,
            "locator_artifact_fk",
            REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
            "Locator/artifact set mismatch",
        )
    if {row["locator_id"] for row in artifacts} != locator_ids:
        _issue(
            issues,
            "artifact_locator_fk",
            REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
            "Artifact/locator set mismatch",
        )
    lifecycle_values = set(schemas["closed_enums"]["lifecycle_stage"])
    for row in lifecycle_links:
        if row["artifact_id"] not in artifact_ids:
            _issue(
                issues,
                "artifact_lifecycle_fk",
                REGISTRY_ROOT / "ARTIFACT_LIFECYCLE_LINK.csv",
                row["artifact_id"],
            )
        if row["lifecycle_stage"] not in lifecycle_values:
            _issue(
                issues,
                "artifact_lifecycle_enum",
                REGISTRY_ROOT / "ARTIFACT_LIFECYCLE_LINK.csv",
                row["lifecycle_stage"],
            )
    if dataset_lifecycle_links:
        _issue(
            issues,
            "unexpected_dataset_lifecycle_rows",
            REGISTRY_ROOT / "DATASET_LIFECYCLE_LINK.csv",
            str(len(dataset_lifecycle_links)),
        )

    expected_dictionary_values = {
        "LIFECYCLE_DICTIONARY.csv": ("lifecycle_stage", "lifecycle_stage"),
        "EVIDENCE_STATE_DICTIONARY.csv": ("evidence_state", "evidence_state"),
        "SOURCE_USE_PURPOSE_DICTIONARY.csv": ("purpose", "purpose"),
        "SOURCE_USE_DECISION_VALUE_DICTIONARY.csv": (
            "decision_value",
            "decision_value",
        ),
        "ARTIFACT_SCOPE_DICTIONARY.csv": (
            "artifact_scope_class",
            "artifact_scope_class",
        ),
    }
    for filename, (column, enum_name) in expected_dictionary_values.items():
        actual = {row[column] for row in rows_by_file[filename]}
        expected = set(schemas["closed_enums"][enum_name])
        if actual != expected:
            _issue(
                issues,
                "dictionary_enum_mismatch",
                WORKSPACE_ROOT / schemas[filename]["path"],
                filename,
            )

    for row in artifacts:
        for key in ("artifact_id", "authority_id", "source_id", "dataset_id", "receipt_id"):
            value = row[key]
            if value and (
                ABSOLUTE_PATH.search(value)
                or RESTRICTED_SCHEME.search(value)
                or GIT_LOCATOR.search(value)
            ):
                _issue(
                    issues,
                    "path_in_key",
                    REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
                    f"{row['artifact_id']}:{key}",
                )
        if row["authority_id"] and row["authority_id"] not in authority_ids:
            _issue(
                issues,
                "artifact_authority_fk",
                REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
                row["artifact_id"],
            )
        if row["source_id"] and row["source_id"] not in {item["source_id"] for item in sources}:
            _issue(
                issues,
                "artifact_source_fk",
                REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
                row["artifact_id"],
            )
        if row["dataset_id"] and row["dataset_id"] not in {item["dataset_id"] for item in datasets}:
            _issue(
                issues,
                "artifact_dataset_fk",
                REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
                row["artifact_id"],
            )
        if row["receipt_id"] and row["receipt_id"] not in {item["receipt_id"] for item in receipts}:
            _issue(
                issues,
                "artifact_receipt_fk",
                REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
                row["artifact_id"],
            )

    for row in locators:
        searchable = "|".join(row.values())
        if (
            ABSOLUTE_PATH.search(searchable)
            or RESTRICTED_SCHEME.search(searchable)
            or GIT_LOCATOR.search(searchable)
        ):
            _issue(
                issues,
                "raw_or_composite_locator",
                REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
                row["artifact_id"],
            )
        locality = row["locality_class"]
        if locality == "LIVE_HQ":
            if not row["repository_relative_location"] or row["sanitized_locator_id"]:
                _issue(
                    issues,
                    "live_locator_shape",
                    REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
                    row["artifact_id"],
                )
        else:
            if row["repository_relative_location"]:
                _issue(
                    issues,
                    "non_live_repository_path",
                    REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
                    row["artifact_id"],
                )
            if not row["sanitized_locator_id"]:
                _issue(
                    issues,
                    "missing_sanitized_locator",
                    REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
                    row["artifact_id"],
                )
        if locality == "LOCAL_ONLY_RESTRICTED":
            if row["rights_state"] != "BLOCKED" or row["active_use_state"] != "USE_BLOCKED":
                _issue(
                    issues,
                    "restricted_not_blocked",
                    REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
                    row["artifact_id"],
                )
        if locality == "OFF_HQ_BRANCH_ONLY":
            if not re.fullmatch(r"[0-9a-f]{40}", row["audit_git_commit"]):
                _issue(
                    issues,
                    "off_hq_commit",
                    REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
                    row["artifact_id"],
                )
            if not row["audit_git_object_path"] or row["active_use_state"] != "USE_BLOCKED":
                _issue(
                    issues,
                    "off_hq_active_use",
                    REGISTRY_ROOT / "SANITIZED_LOCATOR_REGISTRY.csv",
                    row["artifact_id"],
                )

    purposes = set(schemas["closed_enums"]["purpose"])
    values = set(schemas["closed_enums"]["decision_value"])
    decision_grains: set[tuple[str, str, str, str]] = set()
    dataset_ids = {row["dataset_id"] for row in datasets}
    receipt_ids = {row["receipt_id"] for row in receipts}
    for row in decisions:
        grain = (row["dataset_id"], row["field_family"], row["purpose"], row["decision_version"])
        if grain in decision_grains:
            _issue(
                issues,
                "duplicate_decision_grain",
                REGISTRY_ROOT / "SOURCE_USE_DECISION_LEDGER.csv",
                str(grain),
            )
        decision_grains.add(grain)
        if row["purpose"] not in purposes or row["decision_value"] not in values:
            _issue(
                issues,
                "decision_enum",
                REGISTRY_ROOT / "SOURCE_USE_DECISION_LEDGER.csv",
                row["use_decision_id"],
            )
        if row["dataset_id"] not in dataset_ids or row["approval_receipt_id"] not in receipt_ids:
            _issue(
                issues,
                "decision_fk",
                REGISTRY_ROOT / "SOURCE_USE_DECISION_LEDGER.csv",
                row["use_decision_id"],
            )

    if "ARTIFACT_AUTHORITY_LINK.csv" in rows_by_file:
        mapping_statuses = set(schemas["closed_enums"]["mapping_status"])
        authority_links = rows_by_file["ARTIFACT_AUTHORITY_LINK.csv"]
        if len(authority_links) != 113:
            _issue(
                issues,
                "artifact_authority_link_count",
                REGISTRY_ROOT / "ARTIFACT_AUTHORITY_LINK.csv",
                str(len(authority_links)),
            )
        for row in authority_links:
            if (
                row["left_endpoint_type"] != "ARTIFACT"
                or row["left_endpoint_id"] not in artifact_ids
            ):
                _issue(
                    issues,
                    "artifact_authority_left_fk",
                    REGISTRY_ROOT / "ARTIFACT_AUTHORITY_LINK.csv",
                    row["mapping_id"],
                )
            if (
                row["right_endpoint_type"] != "AUTHORITY"
                or row["right_endpoint_id"] not in authority_ids
            ):
                _issue(
                    issues,
                    "artifact_authority_right_fk",
                    REGISTRY_ROOT / "ARTIFACT_AUTHORITY_LINK.csv",
                    row["mapping_id"],
                )
            if row["mapping_status"] not in mapping_statuses:
                _issue(
                    issues,
                    "mapping_status_enum",
                    REGISTRY_ROOT / "ARTIFACT_AUTHORITY_LINK.csv",
                    row["mapping_id"],
                )
            if row["locality_class"] != "LIVE_HQ":
                _issue(
                    issues,
                    "non_live_active_metadata_link",
                    REGISTRY_ROOT / "ARTIFACT_AUTHORITY_LINK.csv",
                    row["mapping_id"],
                )
            if row["authority_effect"] != "NO_AUTHORITY_CHANGE_METADATA_REFERENCE_ONLY":
                _issue(
                    issues,
                    "mapping_authority_effect",
                    REGISTRY_ROOT / "ARTIFACT_AUTHORITY_LINK.csv",
                    row["mapping_id"],
                )
        for name in (
            "ARTIFACT_SOURCE_LINK.csv",
            "ARTIFACT_DATASET_LINK.csv",
            "ARTIFACT_RECEIPT_LINK.csv",
            "DATASET_SOURCE_LINK.csv",
            "DATASET_RECEIPT_LINK.csv",
            "RECEIPT_SOURCE_LINK.csv",
        ):
            if rows_by_file[name]:
                _issue(
                    issues,
                    "unexpected_active_link_rows",
                    REGISTRY_ROOT / name,
                    str(len(rows_by_file[name])),
                )
        if any(
            row[field]
            for row in artifacts
            for field in ("authority_id", "source_id", "dataset_id", "receipt_id")
        ):
            _issue(
                issues,
                "active_artifact_optional_fk_populated",
                REGISTRY_ROOT / "EVIDENCE_ARTIFACT_REGISTRY.csv",
                "Phase B must keep active optional artifact FKs blank",
            )

    empty_names = (
        "PLAYER_IDENTITY_REGISTRY.csv",
        "PLAYER_ALIAS_REGISTRY.csv",
        "IDENTITY_ASSERTION_LEDGER.csv",
        "EVIDENCE_OBSERVATION_REGISTRY.csv",
    )
    for name in empty_names:
        if rows_by_file[name]:
            _issue(
                issues,
                "real_or_fixture_rows_in_registry",
                REGISTRY_ROOT / name,
                str(len(rows_by_file[name])),
            )

    duplicate_path = root / "conflicts/DUPLICATE_CONFLICT_RELATIONSHIP_LEDGER.csv"
    _, duplicate_rows = _read_csv(duplicate_path)
    no_recreate_path = root / "governance/NO_RECREATE_RELATIONSHIP_LEDGER.csv"
    _, no_recreate_rows = _read_csv(no_recreate_path)
    if len(duplicate_rows) != 30:
        _issue(issues, "duplicate_relationship_count", duplicate_path, str(len(duplicate_rows)))
    if any(row["resolution_status"] != "UNRESOLVED_REVIEW_OBJECT" for row in duplicate_rows):
        _issue(issues, "conflict_auto_resolution", duplicate_path, "Resolved relationship present")
    if len(no_recreate_rows) != 40:
        _issue(issues, "no_recreate_count", no_recreate_path, str(len(no_recreate_rows)))
    for row in no_recreate_rows:
        searchable = "|".join(row.values())
        if (
            ABSOLUTE_PATH.search(searchable)
            or GIT_LOCATOR.search(searchable)
            or RESTRICTED_SCHEME.search(searchable)
        ):
            _issue(issues, "unsafe_no_recreate_locator", no_recreate_path, row["no_recreate_id"])

    checks += _validate_manifest(root / "WORKSPACE_MANIFEST.json", issues)
    checks += _validate_manifest(PACKET_ROOT / "MANIFEST.json", issues)

    return ValidationReport(
        status="PASS" if not issues else "FAIL",
        check_count=checks,
        issue_count=len(issues),
        artifact_count=len(artifacts),
        authority_count=len(authorities),
        explicit_decision_count=len(decisions),
        real_player_row_count=len(rows_by_file["PLAYER_IDENTITY_REGISTRY.csv"]),
        real_evidence_observation_row_count=len(rows_by_file["EVIDENCE_OBSERVATION_REGISTRY.csv"]),
        locality_counts=dict(sorted(locality_counts.items())),
        evidence_state_counts=dict(
            sorted(Counter(row["evidence_state"] for row in artifacts).items())
        ),
        duplicate_conflict_count=len(duplicate_rows),
        no_recreate_count=len(no_recreate_rows),
        issues=tuple(issues),
    )


def main() -> None:
    report = validate_registry()
    print(
        json.dumps(
            {**asdict(report), "issues": [asdict(issue) for issue in report.issues]},
            indent=2,
            sort_keys=True,
        )
    )
    if report.status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
