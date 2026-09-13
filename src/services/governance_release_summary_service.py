"""Privacy-safe governance receipt projection (NWR Post-UI Product V1).

This module builds and validates a small, distributable **projection** of an
already-approved NWR data-governance receipt (e.g.
``NWR_DATA_GOVERNANCE.json``), suitable for bundling inside a packaged Tauri
installer -- where the full canonical receipt cannot ship because its own
audit trail legitimately contains the real owner's name (``approved_by``).

This is NOT a new approval mechanism. It never authorizes anything; it only
restates a subset of facts about an admission that already happened,
hash-bound to the exact canonical receipt it was derived from so it cannot be
silently repointed at a different admission. See
``docs/codex/post_ui_v1/NWR_PRIVACY_SAFE_PACKAGING_DESIGN_V1.md`` for the
full design rationale.

Nothing in this module touches scoring, ranking, roster legality, or draft
recommendation logic -- it only reasons about the shape of a governance
receipt/summary JSON document.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

RELEASE_SUMMARY_SCHEMA_VERSION = 1
RELEASE_SUMMARY_KIND = "NWR_GOVERNANCE_RELEASE_ADMISSION_SUMMARY"

# The exact fields copied from the canonical receipt into the release-safe
# summary. Anything not named here (most importantly `approved_by` and
# `approved_at_utc`) is never read from the canonical receipt at all by
# `derive_release_admission_summary` -- there is no subtraction/redaction
# step to get wrong, because the output is built field-by-field from this
# explicit allowlist rather than copied-then-stripped from the input.
_COPIED_CANONICAL_FIELDS: tuple[str, ...] = (
    "authority",
    "approval_status",
    "season",
    "source_id",
    "source_sha256",
    "valid_until",
)
_OPTIONAL_COPIED_CANONICAL_FIELDS: tuple[str, ...] = (
    "admission_scope",
    "component_sources_as_of",
)

# Kept in sync with desktop/scripts/check-resource-allowlists.mjs's own
# `ownerMarkers` constant by tests/test_privacy_safe_packaging_bundle.py,
# which parses that file's source text and asserts the two lists are
# identical -- this list must never drift from the real packaging guard's
# own list. Used here purely as an additional, defense-in-depth check on the
# derived/validated summary content; the actual packaging-time enforcement
# remains check-resource-allowlists.mjs, unmodified.
OWNER_MARKERS: tuple[str, ...] = (
    "Michael Colety",
    "Spencer Colety",
    "las-vegas-enginerds",
)

# Fields that must NEVER appear in a release-safe summary. Defense in depth
# only -- `derive_release_admission_summary` never writes these by
# construction; this constant exists so a test can assert that guarantee
# explicitly and so `validate_release_admission_summary` can refuse a
# hand-tampered file that reintroduces one.
FORBIDDEN_SUMMARY_FIELDS: tuple[str, ...] = (
    "approved_by",
    "approved_at_utc",
    "requested_by",
    "reason",
    "limitations",
    "local_path",
    "notes",
)

_REQUIRED_SUMMARY_FIELDS: tuple[str, ...] = (
    "summary_schema_version",
    "kind",
    "derived_from_canonical_receipt_sha256",
    "authority",
    "approval_status",
    "season",
    "source_id",
    "source_sha256",
    "valid_until",
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReleaseSummaryError(ValueError):
    """Raised when a canonical receipt cannot be summarized, or a release
    summary fails validation. Never raised for content reasons related to
    scoring/ranking -- this module only reasons about governance JSON
    shape."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive_release_admission_summary(
    canonical_receipt: dict[str, Any],
    canonical_receipt_bytes: bytes,
) -> dict[str, Any]:
    """Pure function: build the release-safe summary for a canonical
    governance receipt already known to be well-formed.

    Deterministic -- calling this twice with the same inputs always produces
    an identical dict (used by the regeneration/drift test). Builds the
    output field-by-field from `_COPIED_CANONICAL_FIELDS` -- it does not
    start from a copy of `canonical_receipt` and delete keys, so a future
    field added to the canonical receipt schema is excluded by default,
    never included by accident.
    """

    if not isinstance(canonical_receipt, dict):
        raise ReleaseSummaryError("Canonical governance receipt must be a JSON object.")
    missing = [field for field in _COPIED_CANONICAL_FIELDS if field not in canonical_receipt]
    if missing:
        raise ReleaseSummaryError(
            "Canonical governance receipt is missing required field(s) for "
            "release-summary derivation: " + ", ".join(missing)
        )
    summary: dict[str, Any] = {
        "summary_schema_version": RELEASE_SUMMARY_SCHEMA_VERSION,
        "kind": RELEASE_SUMMARY_KIND,
        "derived_from_canonical_receipt_sha256": _sha256_bytes(canonical_receipt_bytes),
    }
    for field in _COPIED_CANONICAL_FIELDS:
        summary[field] = canonical_receipt[field]
    for field in _OPTIONAL_COPIED_CANONICAL_FIELDS:
        if field in canonical_receipt:
            summary[field] = canonical_receipt[field]
    return summary


def summary_json_bytes(summary: dict[str, Any]) -> bytes:
    """The exact, stable byte encoding used both to write the committed
    summary file and to hash it -- sorted keys, 2-space indent, trailing
    newline, so regeneration is byte-for-byte reproducible."""

    return (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _contains_owner_marker(value: Any) -> str | None:
    """Recursively scan a JSON-decoded value for any known owner-identity
    marker string. Returns the marker found, or None."""

    if isinstance(value, str):
        for marker in OWNER_MARKERS:
            if marker in value:
                return marker
        return None
    if isinstance(value, dict):
        for item in value.values():
            found = _contains_owner_marker(item)
            if found:
                return found
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _contains_owner_marker(item)
            if found:
                return found
        return None
    return None


def validate_release_admission_summary(
    summary: dict[str, Any],
    *,
    season: int,
    source_sha256: str,
    expected_authority: str,
    expected_approval_status: str,
) -> dict[str, Any]:
    """Validate a release-safe summary against the projection artifact it is
    meant to admit. Mirrors the runtime-relevant checks
    `redraft_engine_v1_service._validate_approval_receipt` performs against a
    full canonical receipt (artifact-hash binding, admission-state matching,
    expiry), on the reduced field set a release summary actually carries.
    Returns the summary dict unchanged on success.

    Raises ReleaseSummaryError on any failure -- never silently accepts a
    malformed, mismatched, expired, or tampered summary. This is the runtime
    verification path a packaged build uses instead of the full-receipt
    validator; it must reject exactly the same classes of tampering.
    """

    if not isinstance(summary, dict):
        raise ReleaseSummaryError("Release admission summary must be a JSON object.")
    missing = [field for field in _REQUIRED_SUMMARY_FIELDS if field not in summary]
    if missing:
        raise ReleaseSummaryError(
            "Release admission summary is missing: " + ", ".join(missing)
        )
    present_forbidden = [field for field in FORBIDDEN_SUMMARY_FIELDS if field in summary]
    if present_forbidden:
        raise ReleaseSummaryError(
            "Release admission summary carries forbidden field(s): "
            + ", ".join(present_forbidden)
        )
    marker = _contains_owner_marker(summary)
    if marker:
        raise ReleaseSummaryError(
            f"Release admission summary contains an owner-identity marker ({marker!r}); refusing."
        )
    if summary["summary_schema_version"] != RELEASE_SUMMARY_SCHEMA_VERSION:
        raise ReleaseSummaryError("Release admission summary schema is unsupported.")
    if summary["kind"] != RELEASE_SUMMARY_KIND:
        raise ReleaseSummaryError("Release admission summary kind is unrecognized.")
    if summary["authority"] != expected_authority or summary["approval_status"] != expected_approval_status:
        raise ReleaseSummaryError("Release admission summary is not independently admitted.")
    try:
        summary_season = int(summary["season"])
    except (TypeError, ValueError) as exc:
        raise ReleaseSummaryError("Release admission summary season is invalid.") from exc
    if summary_season != season or summary["source_sha256"] != source_sha256:
        raise ReleaseSummaryError("Release admission summary does not bind this snapshot.")
    if not str(summary["source_id"]).strip():
        raise ReleaseSummaryError("Release admission summary source id is required.")
    digest = str(summary["derived_from_canonical_receipt_sha256"])
    if not _HEX64.match(digest):
        raise ReleaseSummaryError(
            "Release admission summary's canonical-receipt binding hash is malformed."
        )
    try:
        valid_until = date.fromisoformat(str(summary["valid_until"]))
    except ValueError as exc:
        raise ReleaseSummaryError("Release admission summary valid_until date is invalid.") from exc
    today = datetime.now(UTC).date()
    if valid_until < today:
        raise ReleaseSummaryError("Release admission summary has expired.")
    return summary


def load_and_validate_release_admission_summary(
    summary_path: Path,
    *,
    season: int,
    source_sha256: str,
    expected_authority: str,
    expected_approval_status: str,
) -> tuple[dict[str, Any], str]:
    """File-based counterpart of `validate_release_admission_summary`, used
    by the real install path. Hashes the ACTUAL bytes on disk (not a
    re-serialization) so the returned digest matches exactly what a caller
    would get from independently hashing the installed file -- the same
    guarantee `_validate_approval_receipt` provides for the full-receipt
    path."""

    if not summary_path.is_file():
        raise ReleaseSummaryError("Release admission summary is missing.")
    try:
        data = summary_path.read_bytes()
    except OSError as exc:
        raise ReleaseSummaryError("Release admission summary is unreadable.") from exc
    try:
        summary = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseSummaryError("Release admission summary is unreadable.") from exc
    validate_release_admission_summary(
        summary,
        season=season,
        source_sha256=source_sha256,
        expected_authority=expected_authority,
        expected_approval_status=expected_approval_status,
    )
    return summary, _sha256_bytes(data)
