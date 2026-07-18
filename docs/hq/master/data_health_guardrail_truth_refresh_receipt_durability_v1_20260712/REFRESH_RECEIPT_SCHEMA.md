# Refresh Receipt Schema V1

## Envelope

`schema_version` is integer `1`. `receipt_id` is an opaque deterministic `rr_` identifier derived from canonical run identity and result metadata. `created_at_utc` is actual UTC write time. `refresh_action_id` and legacy `run_id` retain the existing run identifier. Existing `started_at_utc`, `finished_at_utc`, `loader_mode`, and `overall_status` are copied without inventing timestamps or outcomes.

`status_path` is the bounded logical path `local_exports/refresh_data/latest_refresh_status.json`, not a clickable private path. `outcome_summary` contains counts only. `lifecycle` records the local storage boundary, latest-attempt receipt identifier, explicit last-known-good rule, and retention bounds. `results` preserves the complete existing per-result metadata plus the three lifecycle decorations below. `integrity` is SHA-256 over canonical JSON excluding the integrity object.

## Per-result lifecycle decorations

- `retained_data_status`: exactly one of `CURRENT_RETAINED_DATA`, `STALE_RETAINED_DATA`, `NO_USABLE_RETAINED_DATA`, or `NOT_ENOUGH_INFORMATION`.
- `latest_successful_receipt_id`: the current receipt for an explicit success, otherwise a validated matching prior success if one exists.
- `last_known_good_receipt_id`: a validated matching prior success only when the latest result is not successful and existing evidence explicitly says current or stale retained data remains.

These fields do not calculate freshness. They preserve explicit existing fields and fail closed when evidence is absent.

## Validation

A valid receipt must be at most 2 MiB, UTF-8 JSON, contain no duplicate object keys, use schema 1, have required non-empty identifiers and parseable timestamps, contain a list of uniquely keyed source/dataset results, use an allowed retained-data state, and pass its SHA-256 integrity digest. Duplicate source/dataset keys are rejected because last-known-good matching would otherwise be ambiguous.

Forbidden result keys include credential, token, cookie, password, secret, credentials, and raw/provider-payload variants. The receipt contains operational metadata only and never source rows, rankings, formulas, recommendations, plugin output, or frozen comparators.

## Files and retention

- Latest: `latest_refresh_status.json`.
- Validated prior backup: `backups/latest_refresh_status.backup.json`.
- Archives: deterministic run receipt names, newest 20 retained.
- Quarantine: corrupt/oversized latest artifacts, newest 5 retained.
- Unsupported schema: reported and preserved; never silently treated as V1.

Every write uses a unique same-directory temporary file, UTF-8 serialization, flush, `fsync`, and atomic `Path.replace`.
