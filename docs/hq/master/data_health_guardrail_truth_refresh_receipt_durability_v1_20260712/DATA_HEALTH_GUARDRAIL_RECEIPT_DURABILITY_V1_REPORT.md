# Data Health Guardrail Truth and Refresh Receipt Durability V1

Verdict: `GREEN_DATA_HEALTH_GUARDRAIL_RECEIPT_DURABILITY_V1_READY_FOR_HQ_REVIEW`

## Outcome

This bounded lane makes refresh-attempt metadata durable inside the existing ignored local refresh boundary and corrects Data Health presentation mappings that could overstate a mixed, stale, skipped, gated, unavailable, missing, or invalid outcome. It does not change refresh execution, source truth, source admission, freshness thresholds, production datasets, rankings, formulas, recommendations, recovery behavior, or trust-strip behavior.

The authoritative writer remains the refresh orchestrator. `refresh_receipt_store_service.py` is a narrow serializer/validator used after an existing run completes. The Refresh Data and Settings / Data Health pages are read-only on open and display the validated durable receipt alongside unchanged canonical Refresh Recovery guidance.

## Truth corrections

- A receipt being structurally valid is shown separately from whether its results are healthy or current.
- Current success, stale retained data, partial success, failure, skip, unavailable, gated, and not-enough-information remain distinct.
- “Sources refreshed” is green only when at least one result is an explicit successful current refresh.
- Skipped, unavailable/not-configured, and gated counts are separate.
- The DynastyProcess row describes the latest refresh outcome and cannot become green from an unverified or stale result.
- NFLVerse coverage count remains coverage-only and cannot imply dataset health.
- Missing, corrupt, oversized, duplicate-key, integrity-invalid, or unsupported receipts fail closed.
- Latest refresh attempt, latest successful refresh, and last-known-good retained data have separate identifiers and labels.

## Durability contract

Supported: ordinary Streamlit rerun, in-session page navigation, browser reload connected to the same app, and a fresh local application process using the same undeleted `local_exports/refresh_data/` root.

Not supported: deleted local state, a different root, a different machine or OS account, deployment replication, cloud storage, external databases, or distributed concurrent writers.

Writes use a same-directory temporary file, flush, `fsync`, and atomic replacement. A validated prior latest becomes the single backup. Invalid latest content is never promoted to backup truth. Corrupt or oversized latest content is quarantined with bounded retention; unsupported schema remains preserved and fails closed. Archives are bounded to 20, quarantine to 5, and each receipt to 2 MiB.

## Implementation boundary

Application changes are limited to the two approved pages and one receipt display component. Service changes are limited to the orchestrator receipt-write hook, truthful Data Health display mapping, and one receipt-store helper. Focused fixtures and tests write only to test roots except the controlled rendered-evidence fixture, whose output remains ignored and untracked.

No roster-hydration work was started.

## Evidence index

- `RECEIPT_STORAGE_AND_SCHEMA_DECISION.md` records the design gate completed before service/application edits.
- `FIELD_AND_LIFECYCLE_REUSE_MAP.csv` records the mandatory preflight reuse audit.
- `GUARDRAIL_TRUTH_MATRIX.csv` records user-facing truth decisions.
- `REFRESH_RECEIPT_SCHEMA.md` and `LAST_KNOWN_GOOD_CONTRACT.md` define the mechanical lifecycle.
- `RERUN_RELOAD_DURABILITY_REVIEW.md` records supported and unsupported durability.
- `REPRESENTATIVE_RENDER_REVIEW.md` identifies controlled desktop and compact renders.
- `VALIDATION_RESULTS.md` records commands and exact totals.
- The no-change and protected-path proofs record the preserved systems.
