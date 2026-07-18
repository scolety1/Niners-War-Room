# Read-Only Inspection Boundary

`inspect_refresh_receipt(status_path=...)` is the authoritative passive read interface.
`load_refresh_receipt` remains only as a compatibility name and delegates directly to that
non-mutating function; it has no quarantine flag and no mutating default.

Inspection performs this bounded sequence: existence check, byte-size check, UTF-8 decode,
duplicate-key-aware JSON parse, schema/version/type/enum/privacy validation, integrity
verification, and separate backup validation. It returns `RefreshReceiptLoadResult` with
`automatic_mutation_performed=False`. Invalid non-missing states set
`maintenance_required=True` and explicitly state that no automatic quarantine occurred.

Inspection never calls staging, replace, rollback, quarantine, archive, prune, mkdir, unlink,
touch, or timestamp-update helpers. Both affected pages and the Data Health dashboard call
`inspect_refresh_receipt` directly.

Explicit quarantine is separate:

- `quarantine_invalid_refresh_receipt(..., confirmed=False)` raises `PermissionError`.
- `confirmed=True` is required.
- Only existing corrupt or oversized latest bytes are eligible.
- The action is not called by either page and no new maintenance UI was added.

The approved refresh-orchestrator write transaction may preserve an invalid prior latest as
quarantine evidence only after the complete replacement candidate has passed every preflight
gate. This is lifecycle mutation, not inspection.
