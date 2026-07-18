# Revised Receipt Schema and Mutation Order

Decision date: 2026-07-13 America/Denver

## Ownership and version

The authoritative receipt owner remains `src/services/data_refresh_orchestrator_service.py`.
The orchestrator is the only automatic writer, and only after an approved refresh run has
already produced its outcome. The receipt store owns projection, validation, serialization,
integrity, and the local atomic lifecycle. Pages and dashboards are read-only consumers.

The revised contract is schema version `2`. Version 1 accepted open-ended result mappings;
version 2 materially narrows that shape, freezes exact types and enums, and therefore cannot
truthfully retain the version-1 identifier. Version 1 and every other version fail closed as
`UNSUPPORTED_SCHEMA`. Passive reads never migrate, repair, archive, or quarantine them.

## Closed recursive schema

No object may contain a key not listed below. No result field may contain an object or list.
The only lists are the top-level `results` list, bounded to 256 rows. JSON booleans and
integers are checked with exact Python/JSON types so booleans cannot satisfy integer fields
and integers or strings cannot satisfy booleans.

### Top level

| Field | Exact type and rule |
|---|---|
| `schema_version` | integer, exactly `2` |
| `receipt_id` | string, `rr_` plus 24 lowercase hexadecimal characters |
| `created_at_utc` | RFC 3339 UTC string: `YYYY-MM-DDTHH:MM:SS[.ffffff]Z` or the same with `+00:00` |
| `refresh_action_id` | opaque ID string, 1-64 characters |
| `run_id` | opaque ID string, 1-64 characters, equal to `refresh_action_id` |
| `started_at_utc` | RFC 3339 UTC string in the format above |
| `finished_at_utc` | string, same format, not earlier than start |
| `loader_mode` | string enum: `QUICK_REFRESH`, `FULL_SAFE_REFRESH`, `CHECK_PROTECTED_ARTIFACTS`, `MANUAL_SOURCES_CHECKLIST` |
| `overall_status` | string enum: `GREEN`, `YELLOW`, `RED` |
| `status_path` | fixed string `local_exports/refresh_data/latest_refresh_status.json` |
| `outcome_summary` | closed object described below |
| `lifecycle` | closed object described below |
| `results` | list of 1-256 closed result objects |
| `integrity` | closed object described below |

### `outcome_summary`

Exactly two keys are allowed. `successful_refresh_results` and
`incomplete_or_non_refresh_results` are integers from 0 through 256. Their sum must equal
the result count, and the successful count must equal the mechanically derived number of
rows whose `refreshed`, `action_type`, and `status` values form an explicit success.

### `lifecycle`

| Field | Exact type and rule |
|---|---|
| `storage_boundary` | fixed string `local_exports/refresh_data` |
| `latest_attempt_receipt_id` | opaque receipt ID equal to top-level `receipt_id` |
| `last_known_good_relationship` | fixed string `per_source_explicit_retention_only` |
| `archive_retention` | integer, exactly `20` |
| `quarantine_retention` | integer, exactly `5` |

### Each `results` row

Every row is flat and contains exactly these fields:

| Field | Exact type and rule |
|---|---|
| `source_id` | identifier string, 1-128 characters |
| `source_name` | display string, 1-160 characters |
| `dataset_id` | identifier string, 0-128 characters; empty means source-level result |
| `source_family` | identifier string, 0-64 characters |
| `action_type` | enum: `REFRESHED`, `CHECK_ONLY`, `SKIPPED_BY_POLICY`, `NOT_CONFIGURED`, `BLOCKED_MANUAL`, `FAILED` |
| `status` | enum: `GREEN`, `YELLOW`, `RED`, `SKIPPED`, `NOT_CONFIGURED`, `BLOCKED` |
| `refreshed` | JSON boolean only |
| `execution_status` | enum: empty, `succeeded`, `failed`, `blocked_policy`, `blocked_config`, `skipped`, `success`, `partial`, `partial_success` |
| `headline_status` | enum: empty, `succeeded`, `failed`, `blocked_policy`, `blocked_config`, `stale`, `review_only`, `review`, `skipped`, `unknown`, `partial`, `partial_success`, `current`, `fresh`, plus the existing uppercase `PARTIAL`, `PARTIAL_SUCCESS`, `CURRENT`, `FRESH`, `STALE` variants |
| `freshness_status` | enum: empty, `current`, `fresh`, `stale`, `pass`, `review`, `fail`, `unknown`, `not_applicable`, or the exact existing uppercase forms of those values |
| `retained_data_status` | enum: `CURRENT_RETAINED_DATA`, `STALE_RETAINED_DATA`, `NO_USABLE_RETAINED_DATA`, `NOT_ENOUGH_INFORMATION` |
| `latest_successful_receipt_id` | empty string or valid opaque receipt ID |
| `last_known_good_receipt_id` | empty string or valid opaque receipt ID |
| `identity_exception` | enum: empty or `UNRESOLVED_IDENTITY` |
| `source_exception` | enum: empty or `SOURCE_CONTRACT_EXCEPTION` |
| `error_category` | enum: `NONE`, `PARTIAL_SUCCESS`, `STALE_DATA`, `SOURCE_SKIPPED`, `SOURCE_UNAVAILABLE`, `SOURCE_GATED`, `REFRESH_FAILED`, `NOT_ENOUGH_INFORMATION` |
| `error_summary` | approved category-derived string, 1-192 characters; never copied from provider output or arbitrary metadata |
| `source_as_of_utc` | null or an already-available RFC 3339 UTC timestamp in the exact format above; never inferred |

The source/dataset pair must be unique. Identifier strings use only ASCII letters, digits,
period, underscore, colon, and hyphen. Opaque IDs use the same alphabet and reveal no path
or credential. All strings are bounded as shown, or at 64 characters for enums/opaque run
IDs. No value is coerced.

### `integrity`

Exactly `algorithm` and `digest` are allowed. `algorithm` is fixed to `sha256`; `digest` is
64 lowercase hexadecimal characters. The digest is SHA-256 over the UTF-8 deterministic
serialization of the complete document with the `integrity` member omitted.

## Input projection and privacy

The orchestrator's rich result object is an input contract, not a persisted schema. Known
orchestrator fields that are not named above are intentionally never copied. This includes
runner and cache paths, commands, environment-variable names, artifact paths, provider
details, counts, formulas, ranking facts, and arbitrary source payloads. Unknown top-level
or result-input keys are rejected. Nested input values are rejected. The safe receipt is
constructed field by field; it is never formed by copying then sanitizing a result mapping.

Persisted strings and candidate keys are recursively checked for authorization, bearer,
token, credential, cookie/session, API-key, raw-header/provider-payload, stack-trace, and
absolute Windows/POSIX path signals. The error summary is selected from fixed approved
category text instead of passing through arbitrary source or provider detail.

## JSON and size rules

JSON input is decoded with an `object_pairs_hook` that rejects duplicate keys before normal
mapping construction. UTF-8 is required. Serialization uses sorted keys, compact separators,
no ASCII escaping, and one terminal newline. `RECEIPT_MAX_BYTES` is 2 MiB and applies to the
exact final bytes, including integrity metadata and the terminal newline. The same bound is
checked before parsing a stored receipt.

## Complete validation order

1. Require an exact mapping input and reject unknown/missing top-level input keys.
2. Validate exact top-level input types, opaque IDs, loader/status enums, and timestamps.
3. Require 1-256 result inputs; reject unknown keys and every nested result value.
4. Project only named safe fields, deriving lifecycle relationships and bounded error text.
5. Validate the complete closed document without integrity: keys, exact types, bounds,
   enums, nullability, unique subjects, cross-field relationships, and privacy rules.
6. Deterministically serialize the integrity-free body.
7. Compute SHA-256 integrity, add the closed integrity object, and validate again.
8. Serialize the exact final bytes and reject a size above 2 MiB.
9. Read and validate latest and backup without mutation; use only validated version-2 prior
   evidence for latest-success/LKG relationships, then repeat steps 4-8 for the finalized
   candidate.
10. Only after all checks pass may the storage root or a temporary file be created.

Any failure through step 9 leaves directory entries, bytes, hashes, and measurable mtimes
unchanged.

## Durable mutation and rollback order

1. Capture exact pre-transaction bytes and metadata for every target that may change.
2. Create same-root temporary files for the finalized latest, archive, conditional prior
   backup, and conditional invalid-latest quarantine evidence; flush and `fsync` each.
3. Replace the backup target only when the prior latest was valid.
4. Replace the archive target with the finalized candidate.
5. Replace conditional quarantine evidence for an invalid prior latest.
6. Replace latest last. Until this succeeds, the candidate is never accepted as latest.
7. On any failure before latest replacement completes, restore all changed targets exactly
   from captured bytes, remove newly created targets, and remove all transaction temporaries.
8. After successful latest replacement, prune archives to 20 and quarantine items to 5.
   Pruning is part of the approved orchestrator lifecycle, never a read action.
9. Return a structured write result naming latest/archive, whether backup changed, whether
   quarantine evidence was created, receipt ID, byte length, and committed status.

The previous valid latest remains recoverable as the bounded backup. A valid existing backup
is left untouched when latest is missing or invalid. Rollback never mutates source data,
production datasets, or paths outside `local_exports/refresh_data`.

## Read-only inspection and explicit maintenance

`inspect_refresh_receipt` opens bytes, checks size, rejects duplicate keys, validates the
closed schema and exact types, validates privacy and integrity, separately inspects backup,
and returns a bounded status object. It never creates a directory, writes a temporary,
moves, deletes, quarantines, archives, repairs, restores, touches, or updates a timestamp.
Missing, corrupt, oversized, invalid-type, and unsupported-schema states remain in place and
report that no automatic quarantine occurred and explicit maintenance is required.

Quarantine is a separate mutating interface requiring an explicit `confirmed=True` gate, or
may occur inside the already-approved refresh-orchestrator write transaction after the new
candidate has completely passed validation. No page render, disclosure expansion,
navigation, reload, or status inspection calls that interface. No maintenance UI is added by
this revision.
