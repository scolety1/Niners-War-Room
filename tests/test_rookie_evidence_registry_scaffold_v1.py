from __future__ import annotations

import csv
import inspect
import json
import re
from pathlib import Path

import pytest

from scripts.validate_rookie_evidence_registry_scaffold_v1 import validate_registry
from src.services.rookie_evidence_registry_service import (
    DECISION_VALUES,
    PURPOSES,
    RookieEvidenceRegistry,
    narrower_blocker_wins,
)

ROOT = Path("docs/hq/rookie_evidence_workspace_v1")
REGISTRIES = ROOT / "registries"
CANONICAL_AUTHORITY = Path(
    "docs/hq/master/rookie_evidence_workspace_design_canonicalization_v1_20260711/"
    "AUTHORITY_CANONICALITY_NORMALIZED.csv"
)
LEGACY_AUTHORITY = Path(
    "docs/hq/master/rookie_evidence_workspace_consolidation_design_v1_20260711/"
    "EVIDENCE_AUTHORITY_CLASSIFICATION.csv"
)
FIXTURE = Path("tests/fixtures/rookie_evidence_registry_v1/SYNTHETIC_EVIDENCE_OBSERVATIONS.csv")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def registry() -> RookieEvidenceRegistry:
    return RookieEvidenceRegistry(ROOT)


def test_full_validator_passes() -> None:
    report = validate_registry()
    assert report.status == "PASS", report.issues
    assert report.issue_count == 0


def test_authority_registry_is_exact_normalized_copy() -> None:
    assert _rows(REGISTRIES / "AUTHORITY_REGISTRY.csv") == _rows(CANONICAL_AUTHORITY)


def test_authority_registry_has_exactly_23_unique_rows() -> None:
    rows = _rows(REGISTRIES / "AUTHORITY_REGISTRY.csv")
    assert len(rows) == 23
    assert len({row["authority_id"] for row in rows}) == 23


def test_authority_rows_are_never_production_or_player_value_authority() -> None:
    rows = _rows(REGISTRIES / "AUTHORITY_REGISTRY.csv")
    assert {row["production_authority"] for row in rows} == {"false"}
    assert {row["player_value_authority"] for row in rows} == {"false"}


def test_authority_rows_create_no_source_promotion() -> None:
    rows = _rows(REGISTRIES / "AUTHORITY_REGISTRY.csv")
    non_admitting = {
        "NO_SOURCE_ADMISSION",
        "ROUTING_CEILING_ONLY",
        "SEPARATE_EXPLICIT_DECISION_REQUIRED",
        "BLOCKS_ADMISSION",
    }
    assert {row["source_admission_effect"] for row in rows} <= non_admitting


def test_legacy_canonical_now_is_not_a_machine_input() -> None:
    legacy_header = tuple(_rows(LEGACY_AUTHORITY)[0])
    assert "canonical_now" in legacy_header
    validator_source = Path("scripts/validate_rookie_evidence_registry_scaffold_v1.py").read_text(
        encoding="utf-8"
    )
    service_source = Path("src/services/rookie_evidence_registry_service.py").read_text(
        encoding="utf-8"
    )
    assert "EVIDENCE_AUTHORITY_CLASSIFICATION.csv" not in validator_source
    assert "EVIDENCE_AUTHORITY_CLASSIFICATION.csv" not in service_source
    assert {
        row["legacy_field_interpretation"] for row in _rows(REGISTRIES / "AUTHORITY_REGISTRY.csv")
    } == {"NON_MACHINE_INTERPRETABLE_LEGACY_SCOPE_FIELD"}


def test_closed_enums_are_exact() -> None:
    schemas = json.loads((ROOT / "governance/SCHEMAS.json").read_text(encoding="utf-8"))
    assert tuple(schemas["closed_enums"]["purpose"]) == PURPOSES
    assert tuple(schemas["closed_enums"]["decision_value"]) == DECISION_VALUES
    assert tuple(schemas["closed_enums"]["lifecycle_stage"]) == (
        "PRE_DRAFT",
        "DRAFT_EVENT",
        "POST_DRAFT_PRESEASON",
        "ROOKIE_SEASON",
        "MULTI_YEAR_OUTCOME",
    )
    assert tuple(schemas["closed_enums"]["evidence_state"]) == (
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


def test_inventory_and_locality_reconcile_exactly(registry: RookieEvidenceRegistry) -> None:
    summary = registry.summary()
    assert summary.artifact_count == 1269
    assert dict(summary.locality_counts) == {
        "LIVE_HQ": 1085,
        "LOCAL_ONLY": 162,
        "LOCAL_ONLY_RESTRICTED": 3,
        "OFF_HQ_BRANCH_ONLY": 19,
    }


def test_artifact_and_locator_primary_keys_are_unique() -> None:
    artifacts = _rows(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    locators = _rows(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")
    assert len({row["artifact_id"] for row in artifacts}) == len(artifacts)
    assert len({row["locator_id"] for row in locators}) == len(locators)


def test_artifact_locator_foreign_keys_are_lossless() -> None:
    artifacts = _rows(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    locators = _rows(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")
    assert {row["locator_id"] for row in artifacts} == {row["locator_id"] for row in locators}
    assert {row["artifact_id"] for row in artifacts} == {row["artifact_id"] for row in locators}


def test_registry_rows_are_deterministically_sorted() -> None:
    for name, key in (
        ("EVIDENCE_ARTIFACT_REGISTRY.csv", "artifact_id"),
        ("AUTHORITY_REGISTRY.csv", "authority_id"),
        ("SANITIZED_LOCATOR_REGISTRY.csv", "locator_id"),
    ):
        values = [row[key] for row in _rows(REGISTRIES / name)]
        assert values == sorted(values)


def test_local_paths_are_sanitized_and_never_keys() -> None:
    locators = _rows(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")
    local = [row for row in locators if row["locality_class"] == "LOCAL_ONLY"]
    assert len(local) == 162
    assert all(not row["repository_relative_location"] for row in local)
    assert all(row["sanitized_locator_id"].startswith("loc_local_") for row in local)
    assert not re.search(r"(?i)[a-z]:[\\/]", "\n".join("|".join(row.values()) for row in local))


def test_restricted_locators_are_non_reversible_and_withheld() -> None:
    locators = _rows(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")
    restricted = [row for row in locators if row["locality_class"] == "LOCAL_ONLY_RESTRICTED"]
    artifacts = {
        row["artifact_id"]: row for row in _rows(REGISTRIES / "EVIDENCE_ARTIFACT_REGISTRY.csv")
    }
    assert len(restricted) == 3
    assert all(row["sanitized_locator_id"].startswith("loc_restricted_") for row in restricted)
    assert all(row["rights_state"] == "BLOCKED" for row in restricted)
    assert all(artifacts[row["artifact_id"]]["sha256"] == "" for row in restricted)
    blob = "\n".join("|".join(row.values()) for row in restricted)
    assert "LOCAL_ONLY_RESTRICTED://" not in blob
    assert not re.search(r"(?i)[a-z]:[\\/]", blob)


def test_off_hq_locators_are_audit_only_and_use_blocked() -> None:
    locators = _rows(REGISTRIES / "SANITIZED_LOCATOR_REGISTRY.csv")
    off_hq = [row for row in locators if row["locality_class"] == "OFF_HQ_BRANCH_ONLY"]
    assert len(off_hq) == 19
    assert all(row["active_use_state"] == "USE_BLOCKED" for row in off_hq)
    assert all(re.fullmatch(r"[0-9a-f]{40}", row["audit_git_commit"]) for row in off_hq)
    assert all(row["audit_git_object_path"] for row in off_hq)


def test_no_explicit_source_use_decision_is_invented(registry: RookieEvidenceRegistry) -> None:
    assert registry.summary().explicit_decision_count == 0
    assert _rows(REGISTRIES / "SOURCE_USE_DECISION_LEDGER.csv") == []


@pytest.mark.parametrize("purpose", PURPOSES)
def test_missing_decisions_fail_closed_for_every_purpose(
    registry: RookieEvidenceRegistry, purpose: str
) -> None:
    result = registry.decision(
        dataset_id="synthetic_missing_dataset",
        field_family="synthetic_missing_field_family",
        purpose=purpose,
    )
    assert result.decision_value == "NOT_ENOUGH_INFORMATION"
    assert result.evidence_state == "SOURCE_UNADMITTED"
    assert result.use_decision_id is None


def test_unknown_purpose_is_rejected(registry: RookieEvidenceRegistry) -> None:
    with pytest.raises(ValueError, match="Unknown purpose"):
        registry.decision(
            dataset_id="synthetic_missing_dataset",
            field_family="synthetic_missing_field_family",
            purpose="RANKING",
        )


def test_narrower_blockers_override_broad_defaults() -> None:
    assert narrower_blocker_wins(family_default="ALLOWED", dataset_decision="BLOCKED") == "BLOCKED"
    assert (
        narrower_blocker_wins(family_default="ALLOWED", purpose_decision="NOT_ENOUGH_INFORMATION")
        == "NOT_ENOUGH_INFORMATION"
    )
    assert (
        narrower_blocker_wins(
            family_default="ALLOWED",
            purpose_decision="ALLOWED",
            legal_or_privacy_blocked=True,
        )
        == "BLOCKED"
    )


def test_broad_allowed_default_does_not_expand_missing_purpose() -> None:
    assert narrower_blocker_wins(family_default="ALLOWED") == "NOT_ENOUGH_INFORMATION"


def test_duplicate_conflict_relationships_remain_unresolved() -> None:
    rows = _rows(ROOT / "conflicts/DUPLICATE_CONFLICT_RELATIONSHIP_LEDGER.csv")
    assert len(rows) == 30
    assert all(row["resolution_status"] == "UNRESOLVED_REVIEW_OBJECT" for row in rows)
    assert all(row["artifact_id_a"] == row["artifact_id_b"] == "" for row in rows)
    assert sum(row["duplicate_class"] == "CONFLICTING_EVIDENCE" for row in rows) == 9


def test_no_recreate_relationship_integrity() -> None:
    rows = _rows(ROOT / "governance/NO_RECREATE_RELATIONSHIP_LEDGER.csv")
    assert len(rows) == 40
    assert len({row["no_recreate_id"] for row in rows}) == 40
    assert all(row["active_use_state"] == "NO_ACTIVE_USE_AUTHORIZED" for row in rows)
    assert not re.search(r"(?i)[a-z]:[\\/]", "\n".join("|".join(row.values()) for row in rows))


@pytest.mark.parametrize(
    "name",
    (
        "PLAYER_IDENTITY_REGISTRY.csv",
        "PLAYER_ALIAS_REGISTRY.csv",
        "IDENTITY_ASSERTION_LEDGER.csv",
        "EVIDENCE_OBSERVATION_REGISTRY.csv",
    ),
)
def test_real_player_and_evidence_registries_are_header_only(name: str) -> None:
    assert _rows(REGISTRIES / name) == []


def test_synthetic_fixture_is_unmistakable_and_excluded(registry: RookieEvidenceRegistry) -> None:
    fixture_rows = _rows(FIXTURE)
    assert len(fixture_rows) == 1
    assert fixture_rows[0]["fixture_class"] == "SYNTHETIC_VALIDATION_FIXTURE"
    assert all(
        "synthetic" in fixture_rows[0][key]
        for key in ("nwr_player_id", "artifact_id", "source_id", "dataset_id")
    )
    assert registry.summary().artifact_count == 1269
    assert _rows(REGISTRIES / "EVIDENCE_OBSERVATION_REGISTRY.csv") == []


def test_read_only_service_defines_no_write_or_network_behavior() -> None:
    source = inspect.getsource(RookieEvidenceRegistry)
    forbidden = (
        ".write_text(",
        ".write_bytes(",
        'open("w',
        "open('w",
        "requests.",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
    )
    assert all(token not in source for token in forbidden)


def test_no_application_runtime_import_or_wiring() -> None:
    matches = []
    for path in Path("app").rglob("*.py"):
        if "rookie_evidence_registry" in path.read_text(encoding="utf-8"):
            matches.append(path.as_posix())
    assert matches == []


def test_no_source_promotion_identity_resolution_or_scoring_api() -> None:
    public_names = {
        name
        for name, value in inspect.getmembers(RookieEvidenceRegistry)
        if callable(value) and not name.startswith("_")
    }
    assert public_names == {"artifact", "artifacts_by_metadata", "decision", "summary"}
    assert not public_names & {
        "promote_source",
        "resolve_identity",
        "rank_players",
        "calculate_value",
        "train_model",
        "score_production",
        "migrate_evidence",
    }


def test_workspace_manifest_declares_all_runtime_authority_closed() -> None:
    manifest = json.loads((ROOT / "WORKSPACE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["read_only"] is True
    assert manifest["runtime_wiring"] is False
    assert manifest["player_value_authority"] is False
    assert manifest["production_authority"] is False
    assert manifest["source_promotion"] is False
