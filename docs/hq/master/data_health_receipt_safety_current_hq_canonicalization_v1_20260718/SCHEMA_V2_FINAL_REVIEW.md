# Schema V2 Final Review

Receipt schema version 2 is a closed, integrity-bound JSON document. Its exact 14 top-level fields are schema_version, receipt_id, created_at_utc, refresh_action_id, run_id, started_at_utc, finished_at_utc, loader_mode, overall_status, status_path, outcome_summary, lifecycle, results, and integrity.

The outcome_summary, lifecycle, integrity, and each result object also require exact key sets. Unknown keys are rejected. Input result rows reject unauthorized nested dict, list, tuple, or set values. Disk JSON parsing uses a recursive duplicate-key hook and rejects non-standard numeric constants. Exact type checks prevent Python bool values from satisfying integer fields and prevent string values such as false from satisfying JSON-boolean fields.

The receipt is serialized canonically with sorted keys and a trailing newline. The integrity object uses SHA-256 over the canonical document excluding integrity. The serialized byte length must be at most 2,097,152 bytes. Results are bounded to 1 through 256 rows; archive retention is exactly 20 and quarantine retention exactly 5.

The final review exercised valid documents, unknown fields at every closed object level, invalid types and enums, recursive duplicate keys, integrity mismatch, privacy strings, relative traversal and absolute paths, exact-limit and over-limit serialized candidates, and the real 2,102,591-byte rejected candidate. All required cases passed.
