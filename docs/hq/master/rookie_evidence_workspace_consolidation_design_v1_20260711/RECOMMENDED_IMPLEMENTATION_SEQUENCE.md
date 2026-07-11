# Recommended Implementation Sequence

## Immediate lane

### Rookie Evidence Registry Read-Only Scaffold V1

Build only the metadata and validation shell described in `IMMEDIATE_NEXT_LANE_CONTRACT.md`.

Why it is first:

- documentation/data-architecture focused;
- reversible by removing one new directory;
- non-destructive and independent of formulas;
- uses existing admitted governance and review-authorized metadata;
- bounded to schemas, registries, locators, hashes, and validators;
- exposes gaps without resolving them;
- gives future identity and parity work stable keys.

Maximum scope:

- artifact registry;
- source/dataset/use decision registry;
- receipt metadata registry;
- state/lifecycle dictionaries;
- duplicate/conflict/no-recreate imports from this design packet;
- implementation status and validators;
- no player-value rows.

## Later lane 1

### Rookie Identity Assertion Registry and Human Review Queue V1

Register provider aliases and identity assertions without forcing resolution. Seed bounded review items for current duplicate/no-ID records, historical drafted/likely overlaps, missing GSIS, and multi-provider conflicts. Do not alter source artifacts or product joins.

Entry gate: immediate scaffold validated and hash-stable.

Exit gate: unique active provider aliases, unresolved rows preserved, no name-based controlling joins, and review queues with closure contracts.

## Later lane 2

### Lifecycle-Specific Read-Only Evidence Index V1

Register a bounded, purpose-limited set of admitted/review-authorized observations in separate pre-draft, draft-event, post-draft/preseason, rookie-season, and multi-year indexes. Begin with positive drafted-event metadata and local bridge/label metadata; raw/value inclusion requires a separate permitted-retention decision.

Entry gate: identity assertions and source/use/rights decisions available.

Exit gate: lifecycle, receipt, lineage, missingness, applicability, and censoring parity.

## Later lane 3

### Duplicate, Conflict, and Supersession Parity Review V1

Review the 157/107 current chain, tracked/local exact copies, draft-round conflicts, scoring-system conflicts, target-system conflicts, threshold applicability, and candidate supersession chains. Produce decisions only; delete nothing.

Entry gate: read-only indices and stable observation IDs.

Exit gate: every relationship classified, human decisions receipted, and rollback proven.

## Work that remains parked

- production rookie scoring and ranking integration;
- CFBD production/model/training use;
- inferred or automatic UDFA truth;
- unadmitted prospect grades, provider data, raw caches, or third-party integration;
- hidden recommendation, sorting, trade-value, or draft logic;
- formula tuning, sparse-history activation, overlays, and ranking simulations;
- review-only comparator use in production;
- current market/ADP used as historical evidence;
- app UI implementation before workspace parity;
- merging competing historical scoring or target systems;
- recreating absent legacy outputs/builders.

## Separate decisions required after the sequence

Even a successful third later lane does not authorize:

- source promotion;
- model training;
- production scoring;
- ranking changes;
- product wiring;
- redistribution/export;
- frozen-comparator use.

Each requires a separate purpose-specific authorization and validation packet.
