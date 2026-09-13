from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.services.governance_release_summary_service import (
    FORBIDDEN_SUMMARY_FIELDS,
    OWNER_MARKERS,
    RELEASE_SUMMARY_KIND,
    RELEASE_SUMMARY_SCHEMA_VERSION,
    ReleaseSummaryError,
    derive_release_admission_summary,
    load_and_validate_release_admission_summary,
    summary_json_bytes,
    validate_release_admission_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_RECEIPT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "model"
    / "nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912"
    / "NWR_DATA_GOVERNANCE.json"
)
COMMITTED_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "model"
    / "nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912"
    / "NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json"
)


def _canonical_receipt() -> tuple[dict[str, object], bytes]:
    receipt_bytes = CANONICAL_RECEIPT_PATH.read_bytes()
    return json.loads(receipt_bytes.decode("utf-8-sig")), receipt_bytes


def _base_receipt(**overrides: object) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": 1,
        "authority": "NWR_DATA_GOVERNANCE",
        "approval_status": "APPROVED_FOR_REDRAFT_V1",
        "season": 2026,
        "source_sha256": "a" * 64,
        "source_id": "test-source-id",
        "approved_by": "Test Owner (not a real identity)",
        "approved_at_utc": "2026-08-08T12:00:00+00:00",
        "valid_until": "2026-10-08",
        "admission_scope": "NWR_REDRAFT_2026_LIVE",
        "component_sources_as_of": {"veterans": "2026-08-08"},
    }
    receipt.update(overrides)
    return receipt


def _valid_summary(**overrides: object) -> dict[str, object]:
    receipt = _base_receipt()
    summary = derive_release_admission_summary(receipt, json.dumps(receipt).encode("utf-8"))
    summary.update(overrides)
    return summary


# ---------------------------------------------------------------------------
# 1. Real canonical-receipt fixture: the committed release summary must be
#    byte-for-byte reproducible from the committed canonical receipt (the
#    regeneration/drift-detection test named in the directive).
# ---------------------------------------------------------------------------


def test_committed_release_summary_has_zero_drift_from_canonical_receipt() -> None:
    assert CANONICAL_RECEIPT_PATH.is_file(), "canonical receipt fixture must exist"
    assert COMMITTED_SUMMARY_PATH.is_file(), "committed release summary must exist"
    receipt, receipt_bytes = _canonical_receipt()
    regenerated = derive_release_admission_summary(receipt, receipt_bytes)
    regenerated_bytes = summary_json_bytes(regenerated)
    committed_bytes = COMMITTED_SUMMARY_PATH.read_bytes()
    assert regenerated_bytes == committed_bytes, (
        "committed NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json has drifted from a fresh "
        "derivation of the canonical receipt -- regenerate it via "
        "scripts/derive_governance_release_summary.py"
    )


def test_committed_summary_binds_to_the_exact_canonical_receipt_bytes() -> None:
    receipt, receipt_bytes = _canonical_receipt()
    committed = json.loads(COMMITTED_SUMMARY_PATH.read_bytes().decode("utf-8-sig"))
    import hashlib

    assert committed["derived_from_canonical_receipt_sha256"] == hashlib.sha256(receipt_bytes).hexdigest()
    assert committed["source_sha256"] == receipt["source_sha256"]
    assert committed["valid_until"] == receipt["valid_until"]


def test_canonical_receipt_itself_is_never_modified_by_this_module() -> None:
    """Defense-in-depth: nothing in this test file, or the service module it
    exercises, ever writes to the canonical receipt path. Asserted by
    checking it still parses as the exact real approved receipt shape."""

    receipt, _ = _canonical_receipt()
    assert receipt["authority"] == "NWR_DATA_GOVERNANCE"
    assert receipt["approval_status"] == "APPROVED_FOR_REDRAFT_V1"
    assert "approved_by" in receipt
    assert "Spencer Colety" in receipt["approved_by"]


# ---------------------------------------------------------------------------
# 2. The summary never carries PII by construction.
# ---------------------------------------------------------------------------


def test_derived_summary_never_contains_forbidden_fields_or_owner_markers() -> None:
    receipt, receipt_bytes = _canonical_receipt()
    summary = derive_release_admission_summary(receipt, receipt_bytes)
    for field in FORBIDDEN_SUMMARY_FIELDS:
        assert field not in summary
    serialized = json.dumps(summary)
    for marker in OWNER_MARKERS:
        assert marker not in serialized


def test_committed_summary_file_contains_no_owner_markers_real_content_scan() -> None:
    body = COMMITTED_SUMMARY_PATH.read_text(encoding="utf-8")
    for marker in OWNER_MARKERS:
        assert marker not in body


def test_derive_raises_on_missing_required_canonical_field() -> None:
    receipt = _base_receipt()
    del receipt["approval_status"]
    with pytest.raises(ReleaseSummaryError, match="missing required field"):
        derive_release_admission_summary(receipt, json.dumps(receipt).encode("utf-8"))


# ---------------------------------------------------------------------------
# 3. validate_release_admission_summary: accepts good, rejects tampered --
#    proves the release-summary runtime check is not a no-op.
# ---------------------------------------------------------------------------


def test_validate_accepts_a_well_formed_matching_summary() -> None:
    summary = _valid_summary()
    result = validate_release_admission_summary(
        summary,
        season=2026,
        source_sha256="a" * 64,
        expected_authority="NWR_DATA_GOVERNANCE",
        expected_approval_status="APPROVED_FOR_REDRAFT_V1",
    )
    assert result == summary


def test_validate_rejects_source_sha256_mismatch() -> None:
    summary = _valid_summary()
    with pytest.raises(ReleaseSummaryError, match="does not bind"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="b" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_season_mismatch() -> None:
    summary = _valid_summary()
    with pytest.raises(ReleaseSummaryError, match="does not bind"):
        validate_release_admission_summary(
            summary,
            season=2027,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_expired_summary() -> None:
    summary = _valid_summary(valid_until="2020-01-01")
    with pytest.raises(ReleaseSummaryError, match="expired"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_wrong_approval_status() -> None:
    summary = _valid_summary(approval_status="SOMETHING_ELSE")
    with pytest.raises(ReleaseSummaryError, match="not independently admitted"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_wrong_kind() -> None:
    summary = _valid_summary(kind="NOT_A_REAL_KIND")
    with pytest.raises(ReleaseSummaryError, match="kind is unrecognized"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_wrong_schema_version() -> None:
    summary = _valid_summary(summary_schema_version=RELEASE_SUMMARY_SCHEMA_VERSION + 1)
    with pytest.raises(ReleaseSummaryError, match="schema is unsupported"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_missing_required_field() -> None:
    summary = _valid_summary()
    del summary["valid_until"]
    with pytest.raises(ReleaseSummaryError, match="missing"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_reintroduced_forbidden_field() -> None:
    """A hand-tampered summary that tries to smuggle approved_by back in is
    refused even though every other field is otherwise valid -- proves this
    is not merely a shape check but an active privacy guard."""

    summary = _valid_summary()
    summary["approved_by"] = "Someone"
    with pytest.raises(ReleaseSummaryError, match="forbidden field"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_owner_marker_smuggled_into_an_allowed_field() -> None:
    summary = _valid_summary(source_id="Spencer Colety's private note")
    with pytest.raises(ReleaseSummaryError, match="owner-identity marker"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


def test_validate_rejects_malformed_canonical_binding_hash() -> None:
    summary = _valid_summary(derived_from_canonical_receipt_sha256="not-a-hash")
    with pytest.raises(ReleaseSummaryError, match="binding hash is malformed"):
        validate_release_admission_summary(
            summary,
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )


# ---------------------------------------------------------------------------
# 4. File-based loader used by the real install path.
# ---------------------------------------------------------------------------


def test_load_and_validate_from_file_hashes_actual_bytes_on_disk(tmp_path: Path) -> None:
    summary = _valid_summary()
    path = tmp_path / "summary.json"
    path.write_bytes(summary_json_bytes(summary))
    import hashlib

    loaded, digest = load_and_validate_release_admission_summary(
        path,
        season=2026,
        source_sha256="a" * 64,
        expected_authority="NWR_DATA_GOVERNANCE",
        expected_approval_status="APPROVED_FOR_REDRAFT_V1",
    )
    assert loaded == summary
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()


def test_load_and_validate_from_file_missing_file() -> None:
    with pytest.raises(ReleaseSummaryError, match="missing"):
        load_and_validate_release_admission_summary(
            Path("does-not-exist.json"),
            season=2026,
            source_sha256="a" * 64,
            expected_authority="NWR_DATA_GOVERNANCE",
            expected_approval_status="APPROVED_FOR_REDRAFT_V1",
        )
