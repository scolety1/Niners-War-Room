# Validation Rules

The validator rejects schema drift, duplicate primary keys, nondeterministic order, invalid foreign keys, unknown enums, any authority row count other than 23, any true production/player-value authority, any source-admitting authority effect, missing-decision permission, raw local paths, reversible restricted locators, active off-HQ use, populated real player/alias/identity/evidence registries, and manifest hash drift.

The validator never reads or interprets `EVIDENCE_AUTHORITY_CLASSIFICATION.csv.canonical_now`; only the normalized authority registry is machine input.
