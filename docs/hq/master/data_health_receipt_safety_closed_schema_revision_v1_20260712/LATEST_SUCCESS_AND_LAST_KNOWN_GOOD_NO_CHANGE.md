# Latest Success and Last-Known-Good No Change

The four identities remain mechanically distinct:

- top-level `receipt_id` is the latest attempted refresh receipt;
- each successful row points `latest_successful_receipt_id` to the current receipt;
- a failed/non-success row may retain the validated matching prior receipt as its latest
  success;
- `last_known_good_receipt_id` is populated only when that matching prior row was an explicit
  success and the new row explicitly establishes current/stale retained data.

A prior receipt is eligible only when it independently passes the full v2 schema, privacy,
size, duplicate-key, and integrity checks. Source/dataset pairs must match exactly. Blank
means not established; backup presence alone is never promoted to current truth.

The inherited latest-success/LKG, current/stale, partial, failure, skip, unavailable, gated,
identity-exception, and source-exception tests pass unchanged in meaning. The dashboard still
reports latest attempt separately from validated prior evidence.
