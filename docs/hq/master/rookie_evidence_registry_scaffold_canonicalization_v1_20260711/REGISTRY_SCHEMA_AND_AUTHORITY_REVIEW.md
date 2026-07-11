# Registry Schema and Authority Review

The scaffold contains 1,269 unique artifact IDs and exact locality parity: 1,085 `LIVE_HQ`, 162 `LOCAL_ONLY`, 3 `LOCAL_ONLY_RESTRICTED`, and 19 `OFF_HQ_BRANCH_ONLY`. It defines 21 versioned CSV schemas with primary-key, foreign-key, deterministic-order, duplicate-key rejection, enum, and manifest controls.

The authority registry is an exact newline-normalized copy of `AUTHORITY_CANONICALITY_NORMALIZED.csv`: 23 unique authority IDs, 0 production-authority true values, 0 player-value-authority true values, and 0 source-admitting effects. The legacy `canonical_now` source field is not a machine input; its normalized legacy value remains opaque under `NON_MACHINE_INTERPRETABLE_LEGACY_SCOPE_FIELD`.

Source, dataset, receipt, and exact source/use decision registries contain zero data rows because no exact durable mapping or receipt-backed decision was provided at the required grain. Missing decisions return `NOT_ENOUGH_INFORMATION` and `SOURCE_UNADMITTED`. No optional foreign key is populated by inference.

The duplicate/conflict ledger contains 30 unresolved review objects, including 9 `CONFLICTING_EVIDENCE` relationships. The artifact primary-state count of 5 `DUPLICATE_CONFLICTING` is a different grain and is not a reconciliation error. The no-recreate ledger contains 40 relationships.
