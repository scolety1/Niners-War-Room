# Roster Snapshot and Freshness Contract

## Purpose

This is a future read-only contract. It does not authorize a provider call, snapshot write, page integration, or roster calculation.

## Snapshot unit

A roster snapshot is an immutable, validated observation of one admitted source, one approved opaque league reference, one source roster/team identity, one schema version, and one source-as-of instant. It contains normalized asset rows and no arbitrary provider payload.

The source roster ID and league reference are private local identifiers. User-facing presentation should use approved labels or redacted opaque references.

## Lifecycle states

The future roster lane must reuse the existing governed meanings:

| Condition | Required state |
| --- | --- |
| Successful current hydration with current retained snapshot | CURRENT_RETAINED_DATA plus successful current receipt |
| Successful hydration but stale by owned threshold | STALE_RETAINED_DATA |
| Failed latest attempt with matching retained prior snapshot | Failed latest attempt plus explicit last_known_good_receipt_id |
| No matching retained snapshot | NO_USABLE_RETAINED_DATA |
| Freshness cannot be established | NOT_ENOUGH_INFORMATION |
| Some exact identities unresolved | identity_exception UNRESOLVED_IDENTITY and partial coverage |
| Source unavailable | SOURCE_UNAVAILABLE |
| Source behind admission/policy gate | SOURCE_GATED |
| Source intentionally not run | SOURCE_SKIPPED |
| Corrupt/unsupported receipt or snapshot | NOT_ENOUGH_INFORMATION or no usable data; never current |

## Timestamp ownership

- source_as_of_utc: owned by the admitted source or a documented source snapshot observation.
- hydration_started_at_utc and hydration_finished_at_utc: owned by the local hydration action.
- created_at_utc: owned by the receipt/snapshot store.
- stale threshold: owned by a separately approved league-state freshness policy; it is not inferred from current market or model thresholds.

Source-as-of and hydration times must never be conflated.

## Retention and last-known-good matching

A prior snapshot may be shown as last-known-good only when all are true:

- same admitted_source_id;
- same approved opaque league reference;
- same source roster/team ID;
- compatible snapshot schema major version;
- validated integrity;
- explicit CURRENT_RETAINED_DATA or STALE_RETAINED_DATA state;
- no identity or source collision that invalidates the prior snapshot.

A failed latest attempt may not overwrite, delete, relabel, or mutate the prior valid snapshot.

## Partial success

- Resolved rows may be shown only with the unresolved count and denominator visible.
- Any complete-roster or position-depth statement is prohibited when an unresolved or unsupported asset could affect it.
- Duplicate identity, corrupt schema, or integrity failure invalidates calculation for the snapshot.
- One unresolved player is not rounded away.

## Receipt integration decision

Preferred path: add one roster dataset result to the existing closed refresh receipt family, using redacted stable source_id/dataset_id and current retained-data/identity exception fields.

This is allowed only if the existing closed schema can express the roster subject without private league or roster IDs and without arbitrary details. If it cannot, a separate bounded roster receipt family must:

- copy the existing lifecycle meanings;
- use the same Decision Trust and Refresh Recovery vocabulary;
- remain under an ignored local root;
- reject secrets, absolute paths, raw payloads, and unknown fields;
- be approved independently.

No current Data Health code changes are made or authorized by this packet.

## Read-only page behavior

The page must:

- never refresh on open;
- never create a snapshot on open;
- show the latest attempt separately from retained data;
- label stale and last-known-good data;
- show source, as-of, identity coverage, unresolved assets, and completeness;
- show no healthy/complete state when evidence is missing;
- retain manual workflow as a separate PRESENTATION_ONLY lane until intentionally migrated.
