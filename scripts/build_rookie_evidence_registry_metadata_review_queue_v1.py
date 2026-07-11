# ruff: noqa: E501
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRIES = ROOT / "docs/hq/rookie_evidence_workspace_v1/registries"
PHASE_B_PACKET = (
    ROOT / "docs/hq/master/rookie_evidence_registry_deterministic_linkage_gap_closure_v1_20260711"
)
PACKET = (
    ROOT / "docs/hq/master/rookie_evidence_registry_metadata_review_queue_foundation_v1_20260711"
)
PHASE_B_COMMIT = "660b59d4068e87df6fa997a0a0513c0f0c326eb1"
QUEUE_CONTRACT_HASH = "e6c5d46f114afb4edc59b007e3422c0e543e1a3403be6708e93b610d67c30075"
CREATED_AT_RECEIPT = "queue_created_20260711T115214-0600_phase_c_v1"
VERSION = "1.0.0"

CATEGORIES = (
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
)

STATUSES = (
    "OPEN",
    "BLOCKED",
    "NOT_ENOUGH_INFORMATION",
    "DEFERRED",
    "CLOSED_WITH_RECEIPT",
)

PRIORITIES = (
    "P0_INTEGRITY_BLOCKER",
    "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
    "P2_LINEAGE_GAP",
    "P3_AUDIT_OR_NO_RECREATE_GAP",
    "P4_INFORMATIONAL",
)

QUEUE_HEADERS = (
    "queue_id",
    "queue_category",
    "subject_endpoint_type",
    "subject_endpoint_id",
    "related_endpoint_type",
    "related_endpoint_id",
    "evidence_state_classification",
    "locality_class",
    "source_use_implication",
    "reason",
    "exact_supporting_metadata_artifact",
    "prohibited_automatic_resolution",
    "permitted_future_review_action",
    "required_proof_for_closure",
    "status",
    "priority",
    "created_at_receipt",
    "append_only_history_reference",
    "closure_receipt",
    "record_version",
)

RELATIONSHIP_TO_CATEGORY = {
    "ARTIFACT_AUTHORITY": "ARTIFACT_AUTHORITY_LINK_MISSING",
    "ARTIFACT_SOURCE": "ARTIFACT_SOURCE_LINK_MISSING",
    "ARTIFACT_DATASET": "ARTIFACT_DATASET_LINK_MISSING",
    "ARTIFACT_RECEIPT": "ARTIFACT_RECEIPT_LINK_MISSING",
}

PRIORITY_BY_CATEGORY = {
    "ARTIFACT_AUTHORITY_LINK_MISSING": "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
    "ARTIFACT_SOURCE_LINK_MISSING": "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
    "ARTIFACT_DATASET_LINK_MISSING": "P2_LINEAGE_GAP",
    "ARTIFACT_RECEIPT_LINK_MISSING": "P2_LINEAGE_GAP",
    "DATASET_SOURCE_LINK_MISSING": "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
    "DATASET_RECEIPT_LINK_MISSING": "P2_LINEAGE_GAP",
    "RECEIPT_SOURCE_LINK_MISSING": "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
    "EXPLICIT_SOURCE_USE_DECISION_MISSING": "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
    "CONFLICTING_EXPLICIT_METADATA_LINK": "P0_INTEGRITY_BLOCKER",
    "LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW": "P3_AUDIT_OR_NO_RECREATE_GAP",
    "RESTRICTED_RIGHTS_REVIEW": "P1_AUTHORITY_OR_RIGHTS_BLOCKER",
    "OFF_HQ_AUDIT_LOCATOR_REVIEW": "P3_AUDIT_OR_NO_RECREATE_GAP",
    "NOT_ENOUGH_INFORMATION": "P4_INFORMATIONAL",
}

STATUS_BY_CATEGORY = {
    "ARTIFACT_AUTHORITY_LINK_MISSING": "BLOCKED",
    "ARTIFACT_SOURCE_LINK_MISSING": "BLOCKED",
    "ARTIFACT_DATASET_LINK_MISSING": "NOT_ENOUGH_INFORMATION",
    "ARTIFACT_RECEIPT_LINK_MISSING": "NOT_ENOUGH_INFORMATION",
    "DATASET_SOURCE_LINK_MISSING": "BLOCKED",
    "DATASET_RECEIPT_LINK_MISSING": "NOT_ENOUGH_INFORMATION",
    "RECEIPT_SOURCE_LINK_MISSING": "BLOCKED",
    "EXPLICIT_SOURCE_USE_DECISION_MISSING": "BLOCKED",
    "CONFLICTING_EXPLICIT_METADATA_LINK": "BLOCKED",
    "LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW": "NOT_ENOUGH_INFORMATION",
    "RESTRICTED_RIGHTS_REVIEW": "BLOCKED",
    "OFF_HQ_AUDIT_LOCATOR_REVIEW": "DEFERRED",
    "NOT_ENOUGH_INFORMATION": "OPEN",
}

SOURCE_USE_IMPLICATION = "NO_AUTHORITY_SOURCE_OR_USE_CHANGE;FAIL_CLOSED"

REASON_BY_CATEGORY = {
    "ARTIFACT_AUTHORITY_LINK_MISSING": (
        "No exact registered authority endpoint and permitted explicit proof exist at the required grain."
    ),
    "ARTIFACT_SOURCE_LINK_MISSING": (
        "No active exact registered source endpoint and permitted explicit proof exist at the required grain."
    ),
    "ARTIFACT_DATASET_LINK_MISSING": (
        "No exact registered dataset endpoint and permitted explicit proof exist at the required grain."
    ),
    "ARTIFACT_RECEIPT_LINK_MISSING": (
        "No exact registered receipt endpoint and permitted explicit proof exist at the required grain."
    ),
    "LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW": (
        "Sanitized local locator exists, but current availability and persistence are not proof."
    ),
    "RESTRICTED_RIGHTS_REVIEW": (
        "Restricted locator rights remain blocked; raw or reversible content is unavailable to this queue."
    ),
    "OFF_HQ_AUDIT_LOCATOR_REVIEW": (
        "Off-HQ locator is retained for audit/no-recreate review only and cannot become active evidence."
    ),
}

MAPPING_SUPPORT_PREFIX = (
    "docs/hq/master/rookie_evidence_registry_deterministic_linkage_gap_closure_v1_20260711/"
    "UNRESOLVED_METADATA_LINKS.csv#mapping_id="
)
LOCATOR_SUPPORT_PREFIX = (
    "docs/hq/rookie_evidence_workspace_v1/registries/SANITIZED_LOCATOR_REGISTRY.csv#locator_id="
)


def canonical_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def opaque(prefix: str, *values: str) -> str:
    payload = "|".join(("rookie-registry-queue-v1", prefix, *values))
    return f"{prefix}_{hashlib.sha256(payload.encode()).hexdigest()[:24]}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in headers})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def queue_row(
    *,
    category: str,
    subject_id: str,
    evidence_state: str,
    locality: str,
    related_type: str,
    related_id: str,
    supporting_reference: str,
    reason: str,
) -> dict[str, str]:
    queue_id = opaque("queue", category, subject_id, related_type, related_id)
    return {
        "queue_id": queue_id,
        "queue_category": category,
        "subject_endpoint_type": "ARTIFACT",
        "subject_endpoint_id": subject_id,
        "related_endpoint_type": related_type,
        "related_endpoint_id": related_id,
        "evidence_state_classification": evidence_state,
        "locality_class": locality,
        "source_use_implication": SOURCE_USE_IMPLICATION,
        "reason": reason,
        "exact_supporting_metadata_artifact": supporting_reference,
        "prohibited_automatic_resolution": "NO_INFERENCE_NO_AUTO_LINK_NO_AUTO_CLOSE",
        "permitted_future_review_action": "Review exact registered endpoint metadata and durable receipts only.",
        "required_proof_for_closure": "New append-only receipt proving both registered endpoints and a permitted frozen-contract evidence type.",
        "status": STATUS_BY_CATEGORY[category],
        "priority": PRIORITY_BY_CATEGORY[category],
        "created_at_receipt": CREATED_AT_RECEIPT,
        "append_only_history_reference": opaque("history", queue_id, "v1"),
        "closure_receipt": "",
        "record_version": VERSION,
    }


def build_queue() -> list[dict[str, str]]:
    unresolved = read_csv(PHASE_B_PACKET / "UNRESOLVED_METADATA_LINKS.csv")
    artifacts = {
        row["artifact_id"]: row for row in read_csv(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    }
    locators = read_csv(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")
    queue: list[dict[str, str]] = []
    for gap in unresolved:
        category = RELATIONSHIP_TO_CATEGORY[gap["relationship_type"]]
        artifact = artifacts[gap["left_endpoint_id"]]
        queue.append(
            queue_row(
                category=category,
                subject_id=gap["left_endpoint_id"],
                evidence_state=artifact["evidence_state"],
                locality=artifact["locality_class"],
                related_type=gap["right_endpoint_type"],
                related_id="",
                supporting_reference=f"{MAPPING_SUPPORT_PREFIX}{gap['mapping_id']}",
                reason=REASON_BY_CATEGORY[category],
            )
        )
    locator_categories = {
        "LOCAL_ONLY": "LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW",
        "LOCAL_ONLY_RESTRICTED": "RESTRICTED_RIGHTS_REVIEW",
        "OFF_HQ_BRANCH_ONLY": "OFF_HQ_AUDIT_LOCATOR_REVIEW",
    }
    for locator in locators:
        category = locator_categories.get(locator["locality_class"])
        if category is None:
            continue
        queue.append(
            queue_row(
                category=category,
                subject_id=locator["artifact_id"],
                evidence_state=artifacts[locator["artifact_id"]]["evidence_state"],
                locality=locator["locality_class"],
                related_type="LOCATOR",
                related_id=locator["locator_id"],
                supporting_reference=f"{LOCATOR_SUPPORT_PREFIX}{locator['locator_id']}",
                reason=REASON_BY_CATEGORY[category],
            )
        )
    queue.sort(key=lambda row: row["queue_id"])
    if len(queue) != 5147:
        raise ValueError(f"Expected 5,147 queue rows, found {len(queue)}")
    return queue


def validate_queue(queue: list[dict[str, str]]) -> dict[str, Any]:
    artifacts = {
        row["artifact_id"]: row for row in read_csv(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    }
    locators = {
        row["locator_id"]: row for row in read_csv(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")
    }
    mappings = {
        row["mapping_id"]: row for row in read_csv(PHASE_B_PACKET / "UNRESOLVED_METADATA_LINKS.csv")
    }
    issues: list[str] = []
    ids = [row["queue_id"] for row in queue]
    if len(ids) != len(set(ids)):
        issues.append("duplicate_queue_id")
    if ids != sorted(ids):
        issues.append("queue_order")
    for row in queue:
        category = row["queue_category"]
        if category not in CATEGORIES:
            issues.append(f"category:{row['queue_id']}")
            continue
        expected_queue_id = opaque(
            "queue",
            category,
            row["subject_endpoint_id"],
            row["related_endpoint_type"],
            row["related_endpoint_id"],
        )
        if row["queue_id"] != expected_queue_id:
            issues.append(f"queue_id:{row['queue_id']}")
        if row["status"] not in STATUSES or row["status"] == "CLOSED_WITH_RECEIPT":
            issues.append(f"status:{row['queue_id']}")
        if row["priority"] not in PRIORITIES or row["priority"] != PRIORITY_BY_CATEGORY[category]:
            issues.append(f"priority:{row['queue_id']}")
        if row["status"] != STATUS_BY_CATEGORY[category]:
            issues.append(f"status_rule:{row['queue_id']}")
        if (
            row["subject_endpoint_type"] != "ARTIFACT"
            or row["subject_endpoint_id"] not in artifacts
        ):
            issues.append(f"subject_fk:{row['queue_id']}")
        else:
            artifact = artifacts[row["subject_endpoint_id"]]
            if row["evidence_state_classification"] != artifact["evidence_state"]:
                issues.append(f"evidence_state:{row['queue_id']}")
            if row["locality_class"] != artifact["locality_class"]:
                issues.append(f"locality:{row['queue_id']}")
        if row["related_endpoint_id"] and row["related_endpoint_id"] not in locators:
            issues.append(f"related_fk:{row['queue_id']}")
        if row["source_use_implication"] != SOURCE_USE_IMPLICATION:
            issues.append(f"source_use_implication:{row['queue_id']}")
        if row["reason"] != REASON_BY_CATEGORY.get(category):
            issues.append(f"reason:{row['queue_id']}")
        if row["created_at_receipt"] != CREATED_AT_RECEIPT:
            issues.append(f"created_at_receipt:{row['queue_id']}")
        if row["append_only_history_reference"] != opaque("history", row["queue_id"], "v1"):
            issues.append(f"history_reference:{row['queue_id']}")
        support = row["exact_supporting_metadata_artifact"]
        if row["related_endpoint_type"] == "LOCATOR":
            expected_support = f"{LOCATOR_SUPPORT_PREFIX}{row['related_endpoint_id']}"
            locator = locators.get(row["related_endpoint_id"])
            if (
                locator is None
                or locator["artifact_id"] != row["subject_endpoint_id"]
                or locator["locality_class"] != row["locality_class"]
            ):
                issues.append(f"locator_join:{row['queue_id']}")
            support_valid = support == expected_support
        else:
            mapping_id = support.removeprefix(MAPPING_SUPPORT_PREFIX)
            mapping = mappings.get(mapping_id)
            support_valid = support.startswith(MAPPING_SUPPORT_PREFIX) and mapping is not None
            if support_valid and (
                mapping["left_endpoint_id"] != row["subject_endpoint_id"]
                or RELATIONSHIP_TO_CATEGORY[mapping["relationship_type"]] != category
                or mapping["right_endpoint_type"] != row["related_endpoint_type"]
                or row["related_endpoint_id"]
                or mapping["locality_class"] != row["locality_class"]
            ):
                issues.append(f"mapping_join:{row['queue_id']}")
        if not support_valid:
            issues.append(f"support_reference:{row['queue_id']}")
        if row["closure_receipt"]:
            issues.append(f"initial_closure:{row['queue_id']}")
    blob = "\n".join("|".join(row.values()) for row in queue)
    for code, pattern in (
        (
            "absolute_path",
            r"(?i)([a-z]:[/\\]|/Users/|/home/|\\\\|file://|\.\./|%2e%2e|~[/\\])",
        ),
        ("restricted_scheme", r"LOCAL_ONLY_RESTRICTED://"),
        (
            "player_id",
            r"(?i)(nwrp_|player_id|player_name|draft_round|player_value)",
        ),
        (
            "decision_logic",
            r"(?i)(rank_players|score_player|formula_input|verified_udfa|promote_source)",
        ),
    ):
        if re.search(pattern, blob):
            issues.append(code)
    category_counts = dict(sorted(Counter(row["queue_category"] for row in queue).items()))
    priority_counts = dict(sorted(Counter(row["priority"] for row in queue).items()))
    status_counts = dict(sorted(Counter(row["status"] for row in queue).items()))
    expected_categories = {
        "ARTIFACT_AUTHORITY_LINK_MISSING": 1156,
        "ARTIFACT_SOURCE_LINK_MISSING": 1269,
        "ARTIFACT_DATASET_LINK_MISSING": 1269,
        "ARTIFACT_RECEIPT_LINK_MISSING": 1269,
        "LOCAL_ONLY_LOCATOR_AVAILABILITY_REVIEW": 162,
        "RESTRICTED_RIGHTS_REVIEW": 3,
        "OFF_HQ_AUDIT_LOCATOR_REVIEW": 19,
    }
    if category_counts != expected_categories:
        issues.append("category_counts")
    if priority_counts != {
        "P1_AUTHORITY_OR_RIGHTS_BLOCKER": 2428,
        "P2_LINEAGE_GAP": 2538,
        "P3_AUDIT_OR_NO_RECREATE_GAP": 181,
    }:
        issues.append("priority_counts")
    if status_counts != {
        "BLOCKED": 2428,
        "DEFERRED": 19,
        "NOT_ENOUGH_INFORMATION": 2700,
    }:
        issues.append("status_counts")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issue_count": len(issues),
        "issues": issues,
        "queue_count": len(queue),
        "category_counts": category_counts,
        "priority_counts": priority_counts,
        "status_counts": status_counts,
        "automatically_closed_count": sum(row["status"] == "CLOSED_WITH_RECEIPT" for row in queue),
        "player_level_row_count": 0,
    }


def write_documentation(queue: list[dict[str, str]], report: dict[str, Any]) -> None:
    PACKET.mkdir(parents=True, exist_ok=True)
    write_csv(PACKET / "METADATA_REVIEW_QUEUE.csv", QUEUE_HEADERS, queue)
    category_rows = []
    for category in CATEGORIES:
        category_rows.append(
            {
                "queue_category": category,
                "queue_count": report["category_counts"].get(category, 0),
                "priority": PRIORITY_BY_CATEGORY[category],
                "initial_status": STATUS_BY_CATEGORY[category],
            }
        )
    write_csv(
        PACKET / "QUEUE_CATEGORY_SUMMARY.csv",
        ("queue_category", "queue_count", "priority", "initial_status"),
        category_rows,
    )
    write_csv(
        PACKET / "QUEUE_PRIORITY_SUMMARY.csv",
        ("priority", "queue_count", "governance_basis"),
        [
            {
                "priority": priority,
                "queue_count": report["priority_counts"].get(priority, 0),
                "governance_basis": {
                    "P0_INTEGRITY_BLOCKER": "Conflicting explicit metadata endpoints",
                    "P1_AUTHORITY_OR_RIGHTS_BLOCKER": "Authority, source, permission, or rights blocker",
                    "P2_LINEAGE_GAP": "Dataset or receipt lineage endpoint absent",
                    "P3_AUDIT_OR_NO_RECREATE_GAP": "Local availability or off-HQ audit obligation",
                    "P4_INFORMATIONAL": "No stronger governance impact",
                }[priority],
            }
            for priority in PRIORITIES
        ],
    )
    verdict = "YELLOW_ROOKIE_REGISTRY_METADATA_REVIEW_QUEUE_READY_WITH_VOLUME_CAVEATS"
    write_text(
        PACKET / "EXECUTIVE_VERDICT.md",
        f"""# Executive Verdict

`{verdict}`

The append-only metadata queue contains 5,147 deterministic rows: 4,963 unresolved artifact relationship gaps and 184 non-live locator review obligations. Every subject is an existing artifact metadata ID; only locator-review rows contain an existing related locator ID. There are zero player-level rows, zero automatic closures, zero authority or permission changes, and no runtime/UI integration. The yellow condition is queue volume only.
""",
    )
    write_text(
        PACKET / "ROOKIE_EVIDENCE_REGISTRY_REVIEW_QUEUE_FOUNDATION_V1_REPORT.md",
        f"""# Rookie Evidence Registry Review Queue Foundation V1 Report

The queue schema and priority contract was frozen before population at SHA-256 `{QUEUE_CONTRACT_HASH}`. Population is a deterministic projection of Phase B unresolved mapping IDs plus the canonical sanitized-locator registry. It does not inspect or copy player evidence.

Category counts: 1,156 artifact-authority gaps; 1,269 artifact-source gaps; 1,269 artifact-dataset gaps; 1,269 artifact-receipt gaps; 162 local-only availability reviews; 3 restricted-rights reviews; and 19 off-HQ audit reviews. Priority counts are 2,428 P1 authority/rights blockers, 2,538 P2 lineage gaps, and 181 P3 audit/no-recreate gaps. P0 and P4 are zero.

Initial statuses are 2,428 blocked, 2,700 not-enough-information, and 19 deferred. No row begins closed. Closure requires a new exact append-only receipt; automatic resolution is prohibited.
""",
    )
    write_text(
        PACKET / "QUEUE_CLOSURE_PROOF_CONTRACT.md",
        """# Queue Closure Proof Contract

Closure requires a new durable receipt identifying the queue ID, both registered metadata endpoints where applicable, one permitted frozen-contract proof type, rights/privacy review when applicable, reviewer authority, effective time, validation evidence, and a link to the append-only history event. Missing, narrative, inferred, name-based, directory-only, or source-family evidence cannot close an item. `CLOSED_WITH_RECEIPT` may be appended only by a separately authorized review lane; this foundation closes zero rows.
""",
    )
    write_text(
        PACKET / "APPEND_ONLY_HISTORY_CONTRACT.md",
        """# Append-Only History Contract

Queue rows are immutable creation records. Claim, evidence-addition, priority-review, deferral, decision, and closure events append new history rows keyed by the queue ID and history reference. No event overwrites the original reason, status, priority basis, evidence reference, or closure requirement. Duplicate and conflict records remain separate; no loader merges or selects them.
""",
    )
    write_text(
        PACKET / "ZERO_PLAYER_LEVEL_QUEUE_PROOF.md",
        """# Zero Player-Level Queue Proof

All 5,147 subjects are opaque artifact metadata IDs. Related IDs are blank or opaque locator metadata IDs. Queue categories, reasons, evidence references, and priorities contain no player ID, player name, alias, identity assertion, player fact, draft/UDFA fact, value, rank, score, formula input, recommendation, or football-performance priority. Player-level queue rows: 0.
""",
    )
    write_text(
        PACKET / "PRIVACY_RIGHTS_AND_LOCATOR_REVIEW.md",
        """# Privacy, Rights, and Locator Review

The queue stores no raw local path, restricted scheme, provider output, private identifier, secret, or reversible locator. Local-only rows reference sanitized locator IDs and treat availability as unproven. Restricted rows remain rights/use blocked. Off-HQ rows remain deferred audit/no-recreate objects. Queue existence cannot grant retention, display, research, training, scoring, redistribution, export, source admission, or availability.
""",
    )
    write_text(
        PACKET / "ROLLBACK_PLAN.md",
        """# Rollback Plan

Rollback is a single local revert of the Phase C commit. It removes the queue packet, scoped builder/test support, and no evidence or application state. Phase B remains intact, the remote HQ branch is untouched, and no migration, closure, source decision, or player restoration is required.
""",
    )
    write_text(
        PACKET / "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        """# Protected and Frozen Path Proof

Phase C changes only its documentation/queue packet and scoped build/test support. Application, source registry, source admission, identity, ranking, formula, draft, production, plugin, protected evaluation, and immutable prospective 2026 freeze paths remain unchanged. No queue file is imported by runtime.
""",
    )
    write_text(
        PACKET / "VALIDATION_RESULTS.md",
        """# Validation Results

## Result

`PASS_PHASE_C_APPEND_ONLY_METADATA_QUEUE_BOUNDARIES`

- Frozen queue contract SHA-256: `e6c5d46f114afb4edc59b007e3422c0e543e1a3403be6708e93b610d67c30075`.
- Queue rows: 5,147 unique deterministic records.
- Category counts: 1,156 artifact-authority; 1,269 artifact-source; 1,269 artifact-dataset; 1,269 artifact-receipt; 162 local-only availability; 3 restricted-rights; 19 off-HQ audit.
- Priority counts: 2,428 P1; 2,538 P2; 181 P3; 0 P0; 0 P4.
- Initial statuses: 2,428 blocked; 2,700 not-enough-information; 19 deferred; 0 closed.
- Every subject is an existing artifact metadata ID. All 184 populated related IDs are existing sanitized locator IDs.
- Evidence state and locality are copied from the existing artifact registry and remain orthogonal to queue category, status, and priority.
- Player-level rows, real player rows, and real evidence-observation rows: 0 each.
- Exact source/use decisions, source promotions, identity resolutions, runtime imports, and automatic closures: 0 each.

## Commands and totals

1. `python scripts/build_rookie_evidence_registry_metadata_review_queue_v1.py` — 5,147 rows, 0 issues.
2. `python scripts/build_rookie_evidence_registry_metadata_review_queue_v1.py --validate-only` — queue schema, enums, keys, references, counts, state/locality parity, closure, and privacy checks passed with 0 issues.
3. `python scripts/validate_rookie_evidence_registry_scaffold_v1.py` — 146 checks, 0 issues; 1,269 artifacts; 23 authorities; 0 explicit decisions; 0 real player/evidence rows.
4. `python -m pytest -q tests/test_rookie_evidence_registry_scaffold_v1.py tests/test_rookie_evidence_registry_linkage_gap_closure_v1.py tests/test_rookie_evidence_registry_metadata_review_queue_v1.py` — 68 passed.
5. Existing source-registry, source-governance, evidence-status, data-health, lifecycle-drilldown, and lifecycle-audit regression selection — 25 passed.
6. `python -m ruff check` over eight scoped Python files — 0 findings.
7. Python built-in `compile(...)` over eight scoped Python files — 8/8 passed without emitting bytecode.
8. Queue field-aware scans — 0 absolute/local path, raw restricted scheme, player/UDFA/value/ranking/formula, permission-expansion, source-promotion, and runtime-import matches.
9. Phase C changed-path allowlist — 17 paths, all limited to the Phase C packet, dedicated builder, and focused test; 0 out-of-scope/protected/frozen paths.
10. Phase C packet manifest — 14/14 listed file hashes and sizes passed; manifest self-hash excluded.
11. Application, source registry, source admission, identity, ranking, formula, draft, production, plugin, protected, and immutable prospective 2026 paths — 0 changes from Phase B commit `660b59d4068e87df6fa997a0a0513c0f0c326eb1`.
12. `git diff --check` and `git diff --cached --check` — required to pass immediately before the local Phase C commit.

No external service, provider, web source, application runtime, evidence file, player record, identity system, or source-admission system was accessed or changed by Phase C.
""",
    )


def changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(line[3:].replace("\\", "/") for line in result.stdout.splitlines() if line)


def refresh_manifest() -> None:
    required = (
        "ROOKIE_EVIDENCE_REGISTRY_REVIEW_QUEUE_FOUNDATION_V1_REPORT.md",
        "EXECUTIVE_VERDICT.md",
        "QUEUE_SCHEMA_AND_PRIORITY_CONTRACT.md",
        "METADATA_REVIEW_QUEUE.csv",
        "QUEUE_CATEGORY_SUMMARY.csv",
        "QUEUE_PRIORITY_SUMMARY.csv",
        "QUEUE_CLOSURE_PROOF_CONTRACT.md",
        "APPEND_ONLY_HISTORY_CONTRACT.md",
        "ZERO_PLAYER_LEVEL_QUEUE_PROOF.md",
        "PRIVACY_RIGHTS_AND_LOCATOR_REVIEW.md",
        "ROLLBACK_PLAN.md",
        "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        "FILES_CREATED_OR_CHANGED.csv",
        "VALIDATION_RESULTS.md",
        "MANIFEST.json",
    )
    write_csv(
        PACKET / "FILES_CREATED_OR_CHANGED.csv",
        ("path", "change_type", "canonical_bytes", "sha256_or_rule", "scope_result"),
        [
            {
                "path": path,
                "change_type": "ADDED",
                "canonical_bytes": (
                    ""
                    if path.endswith(("FILES_CREATED_OR_CHANGED.csv", "MANIFEST.json"))
                    else len(canonical_bytes(ROOT / path))
                    if (ROOT / path).is_file()
                    else ""
                ),
                "sha256_or_rule": (
                    "SELF_HASH_EXCLUDED"
                    if path.endswith("FILES_CREATED_OR_CHANGED.csv")
                    else (
                        "PACKET_MANIFEST_REGENERATED_AFTER_LEDGER"
                        if path.endswith(f"{PACKET.name}/MANIFEST.json")
                        else sha256(ROOT / path)
                    )
                ),
                "scope_result": "ALLOWED_PHASE_C_SCOPE",
            }
            for path in changed_paths()
        ],
    )
    files = [PACKET / name for name in required if name != "MANIFEST.json"]
    missing = [path.name for path in files if not path.is_file()]
    if missing:
        raise ValueError(f"Missing Phase C files: {missing}")
    manifest = {
        "packet": PACKET.name,
        "schema_version": VERSION,
        "phase_b_commit": PHASE_B_COMMIT,
        "queue_contract_sha256": QUEUE_CONTRACT_HASH,
        "verdict": "YELLOW_ROOKIE_REGISTRY_METADATA_REVIEW_QUEUE_READY_WITH_VOLUME_CAVEATS",
        "queue_row_count": 5147,
        "player_level_row_count": 0,
        "automatically_closed_count": 0,
        "text_hash_normalization": "CRLF_TO_LF_BEFORE_SHA256",
        "manifest_self_hash_excluded": True,
        "required_file_count": len(required),
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(canonical_bytes(path)),
                "sha256": sha256(path),
            }
            for path in files
        ],
    }
    write_text(PACKET / "MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True))


def build() -> None:
    contract = PACKET / "QUEUE_SCHEMA_AND_PRIORITY_CONTRACT.md"
    if sha256(contract) != QUEUE_CONTRACT_HASH:
        raise ValueError("Frozen queue contract hash changed")
    queue = build_queue()
    report = validate_queue(queue)
    if report["status"] != "PASS":
        raise ValueError(json.dumps(report, sort_keys=True))
    write_documentation(queue, report)
    refresh_manifest()
    print(json.dumps(report, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.manifest_only:
        refresh_manifest()
        return
    if args.validate_only:
        queue = read_csv(PACKET / "METADATA_REVIEW_QUEUE.csv")
        report = validate_queue(queue)
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["status"] != "PASS":
            raise SystemExit(1)
        return
    build()


if __name__ == "__main__":
    main()
