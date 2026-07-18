# Receipt Storage and Schema Decision

Decision status: `DESIGN_GATE_APPROVED_FOR_BOUNDED_IMPLEMENTATION`

Reviewed against live HQ `6bcb9c3c36fc560c30151591feaeff9d3960499f` on 2026-07-13. The audit inspected the current refresh orchestrator, Data Health service and pages, Refresh Recovery adapter and component, source-governance fields, existing local receipts and source manifests, the Development Lab local-state lifecycle, and the canonical Refresh Recovery and Decision Trust Strip packets.

## Decision

Use the existing repository-approved `local_exports/refresh_data/` boundary. The authoritative owner remains `src/services/data_refresh_orchestrator_service.py`; a single narrow receipt-store helper may implement serialization, validation, atomic replacement, backup, quarantine, and bounded retention on the orchestrator's behalf. This is not a general persistence framework and does not own source state, refresh execution, freshness, admission, ranking, or recovery behavior.

The inspected boundary already holds `latest_refresh_status.json`, per-run archived status JSON, and source-specific refresh manifests. It is ignored by Git. Existing receipts contain operational run/result metadata only and survive process restarts while that local directory remains present. No existing persisted Data Health snapshot lifecycle was found, so Data Health will read the receipt lifecycle rather than create another snapshot store.

## V1 contract

| Decision item | Approved contract |
|---|---|
| Authoritative receipt owner | The refresh orchestrator after a run completes; page code is read-only except for invoking an existing explicit refresh control. |
| Schema version | Integer `1`; missing or any other version is unsupported and fails closed. |
| Receipt identifier | Opaque `rr_` plus a deterministic SHA-256 prefix over canonical run identity and result metadata. It is not a source identifier. |
| Source/dataset identifiers | Existing `source_id`, `source_family`, and `dataset_id` only. No matching, substitution, or new registry. |
| Creation timestamp | Actual UTC receipt-write time, recorded separately from existing run timestamps. |
| Refresh timestamps | Existing `started_at_utc`, `finished_at_utc`, per-result `start_time`, `end_time`, `last_attempt_at`, and `last_success_at`/`last_success_timestamp`. Missing values remain missing. |
| Source as-of | Existing `last_success_at`, `last_success_timestamp`, `timestamp`, and explicit freshness/as-of strings only. No timestamp is inferred. |
| Refresh outcome | Existing run `overall_status` plus complete per-result `action_type`, `status`, `refreshed`, `execution_status`, and `headline_status`. Canonical Refresh Recovery presentation remains the sole eight-state display adapter. |
| Partial success | Preserved through the complete per-result breakdown. The canonical run summary may label mixed success/incomplete results `PARTIAL_SUCCESS`; storage does not invent a second mapping. |
| Failure context | Existing bounded `user_explanation`, `user_message`, `last_result`, `caveat`, and exit metadata. No repair advice is invented. |
| Retained data | Per-result status is `CURRENT_RETAINED_DATA` only with explicit successful refresh plus explicit current/fresh evidence; `STALE_RETAINED_DATA` only under existing explicit stale evidence; `NO_USABLE_RETAINED_DATA` only when explicitly recorded; otherwise `NOT_ENOUGH_INFORMATION`. |
| Latest successful relationship | A prior validated receipt may be identified as the latest successful receipt for the same source/dataset. This historical relationship does not assert retained data. |
| Last-known-good relationship | Added only when the current result explicitly records retained data and a prior validated, integrity-passing, source/dataset-matching successful receipt exists. Otherwise blank. |
| Storage boundary | Existing local-only `local_exports/refresh_data/`; no cloud, external database, provider call, cross-machine claim, or tracked production artifact. |
| Test override | Existing `status_root`/`status_path` parameters point all test writes into `tmp_path`. |
| Atomic write | Serialize UTF-8 JSON to a unique same-directory temporary file, flush and `fsync`, then `Path.replace` the destination. |
| Backup | Before replacing latest, validate the existing latest receipt. Only a valid prior latest is atomically copied to `backups/latest_refresh_status.backup.json`. Invalid content never becomes backup truth. |
| Corruption | Oversized, truncated, malformed, structurally invalid, or integrity-invalid latest content fails closed and is moved to bounded `quarantine/`; a valid backup is reported separately and never relabeled as the latest attempt. |
| Unsupported schema | Report `UNSUPPORTED_SCHEMA`; do not parse as healthy and do not silently rewrite or delete it. A separately validated backup may be displayed only as prior receipt evidence. |
| Retention | At most 20 run archives, one validated latest backup, and 5 quarantined files. Latest remains one file. |
| Size bound | Maximum 2 MiB per receipt; oversize fails closed before JSON parsing. |
| Privacy | Operational metadata only. No credentials, tokens, cookies, raw provider payloads, source rows, rankings, formulas, recommendations, plugin output, or frozen comparators. Existing diagnostic path strings are text, never rendered as clickable user-facing links. |
| Supported durability | Streamlit rerun, in-session page navigation, browser reload that reconnects to the same local app, and a fresh local application process using the same undeleted receipt root. |
| Unsupported durability | Deleted local state, different receipt root, different machine, different OS account, cloud/deployment replication, and concurrent distributed writers. |
| Rollback | Revert the implementation commit. V1 keeps legacy top-level run/result keys, so older readers ignore added metadata. Local receipt files may remain ignored or be manually removed; no source, ranking, or production-data rollback is required. |

## Fail-closed load outcomes

`VALID_LATEST`, `MISSING`, `CORRUPT`, `OVERSIZED`, and `UNSUPPORTED_SCHEMA` remain mechanically distinct. `VALID_BACKUP_AVAILABLE` is supplemental evidence about a prior validated receipt; it never upgrades the current load outcome. Corrupt latest plus corrupt backup yields no usable receipt. Missing latest plus valid backup still displays the latest attempt as missing.

## Stop-condition review

The design requires no new source fact, threshold, admission decision, source fallback, retry, refresh, raw payload, external storage, or change to Refresh Recovery/Decision Trust Strip semantics. The approved existing local boundary is sufficient, so `BLOCKED_DATA_HEALTH_RECEIPT_DURABILITY_STORAGE_BOUNDARY_NOT_AVAILABLE` does not apply.
