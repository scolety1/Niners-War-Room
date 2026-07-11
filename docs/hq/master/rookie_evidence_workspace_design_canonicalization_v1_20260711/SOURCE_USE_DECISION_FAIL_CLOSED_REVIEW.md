# Source and Use Decision Fail-Closed Review

## Exact decision grain

The future scaffold requires one versioned decision per:

`dataset_id × field_family × purpose × decision_version`

The purpose set remains exactly:

1. `LOCAL_RETENTION`
2. `CANONICAL_HQ_SUMMARY`
3. `RAW_RECEIPT_STORAGE`
4. `DISPLAY`
5. `RESEARCH`
6. `MODEL_TRAINING`
7. `PRODUCTION_SCORING`
8. `REDISTRIBUTION`
9. `EXPORT`

The decision-value set remains exactly:

- `ALLOWED`
- `ALLOWED_WITH_CAVEATS`
- `REVIEW_ONLY`
- `BLOCKED`
- `NOT_ENOUGH_INFORMATION`
- `NOT_APPLICABLE`

Every populated decision must link an existing explicit decision or approval receipt that supports that exact dataset, field family, purpose, version, rights status, privacy class, and caveat. Descriptive prose is not parsed into a decision.

## Prohibited derivation

Admission or use must not be derived from a broad source-family default, accessibility, local cache, public visibility, prior review use, human identity approval, newer artifact, favorable values, source manifest, hash availability, decision-receipt existence alone, or descriptive prose.

The family-level matrix in the source design is a routing ceiling only. A narrower legal, privacy, dataset, field, identity, receipt, or purpose blocker wins.

## Missing-decision behavior

When an explicit supported decision does not exist:

- use `NOT_ENOUGH_INFORMATION` for the `SOURCE_USE_DECISION_LEDGER.decision_value` unless an explicit `BLOCKED` or `NOT_APPLICABLE` receipt controls;
- use evidence state `SOURCE_UNADMITTED` when source admission is absent or denied;
- use evidence state `USE_BLOCKED` when the requested downstream use is blocked;
- use evidence state/locality `LOCAL_ONLY_RESTRICTED` for local, restricted, or off-HQ evidence that cannot be admitted into HQ.

These are separate dimensions. Do not place evidence-state values in the six-value decision column or coerce `NOT_ENOUGH_INFORMATION` into permission.

## Review result

- Automatic source promotion decisions created: `0`
- Formula, ranking, model-training, production-scoring, or product-use grants created: `0`
- CFBD production/model/training grants created: `0`
- Provider/prospect rights expanded: `0`
- Conflicting systems automatically preferred: `0`
- Decisions inferred from prose: `0`

Result: `PASS_FAIL_CLOSED_NO_PERMISSION_INVENTED`.
