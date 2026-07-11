# Canonical Information Architecture

## Design goal

The future Rookie Evidence Workspace is an additive, read-only evidence registry. It organizes existing evidence without moving it, reinterpreting it, changing authority, or combining lifecycle stages into a generic player record.

The word `canonical` means canonical metadata, keys, authority decisions, and lineage. It does not mean that every registered value is admitted, correct, production-ready, or safe to redistribute.

## Proposed directory structure

```text
docs/hq/rookie_evidence_workspace_v1/
  README.md
  WORKSPACE_OVERVIEW.md
  WORKSPACE_MANIFEST.json
  IMPLEMENTATION_STATUS.csv
  registries/
    PLAYER_IDENTITY_REGISTRY.csv
    PLAYER_ALIAS_REGISTRY.csv
    IDENTITY_ASSERTION_LEDGER.csv
    SOURCE_REGISTRY.csv
    DATASET_REGISTRY.csv
    SOURCE_USE_DECISION_LEDGER.csv
    SOURCE_RECEIPT_REGISTRY.csv
    EVIDENCE_ARTIFACT_REGISTRY.csv
    ARTIFACT_LIFECYCLE_LINK.csv
    DATASET_LIFECYCLE_LINK.csv
    FIELD_DEFINITION_REGISTRY.csv
    FIELD_LINEAGE_LEDGER.csv
    LIFECYCLE_EVENT_REGISTRY.csv
  evidence/
    pre_draft/
      PRE_DRAFT_EVIDENCE_INDEX.csv
      PRE_DRAFT_FIELD_MANIFEST.csv
    draft_event/
      DRAFT_EVENT_EVIDENCE_INDEX.csv
      DRAFT_EVENT_FIELD_MANIFEST.csv
    post_draft_preseason/
      POST_DRAFT_PRESEASON_EVIDENCE_INDEX.csv
      POST_DRAFT_PRESEASON_FIELD_MANIFEST.csv
    rookie_season/
      ROOKIE_SEASON_EVIDENCE_INDEX.csv
      ROOKIE_SEASON_FIELD_MANIFEST.csv
    multi_year_outcomes/
      MULTI_YEAR_OUTCOME_EVIDENCE_INDEX.csv
      OUTCOME_WINDOW_REGISTRY.csv
      OUTCOME_THRESHOLD_APPLICABILITY.csv
  conflicts/
    EVIDENCE_CONFLICT_LEDGER.csv
    DUPLICATE_RELATIONSHIP_LEDGER.csv
  queues/
    MISSING_EVIDENCE_QUEUE.csv
    MANUAL_REVIEW_QUEUE.csv
    SOURCE_ADMISSION_QUEUE.csv
  supersession/
    SUPERSESSION_LEDGER.csv
  archive/
    ARCHIVE_MANIFEST.csv
    RESTRICTED_LOCATOR_REGISTRY.csv
  governance/
    NO_RECREATE_INDEX.csv
    VALIDATION_RULES.md
    VALIDATION_RESULTS.md
    RIGHTS_AND_PRIVACY_BOUNDARY.md
```

No directory or file above is created by this design lane. The tree is a contract for a later implementation lane.

## Information layers

### 1. Identity layer

The identity layer mints one opaque, provider-independent `nwr_player_id` and stores provider IDs as aliases. It records assertions and conflicts rather than overwriting aliases. Normalized names are review aids only.

### 2. Source and rights layer

The source layer separates:

- source family;
- dataset or endpoint;
- acquisition receipt;
- field family;
- allowed purpose;
- rights/privacy boundary;
- use decision version.

A permissive source-family default cannot override a narrower blocked dataset, field, identity, rights, or use decision. The narrowest applicable decision wins; ties fail closed.

### 3. Artifact layer

Every existing file, local output, restricted locator, or branch-only artifact receives an immutable `artifact_id`. The registry stores path or permitted locator, hash, schema, row count, grain, authority state, artifact scope, source/use state, and relationships. Artifact scope may be governance, product consumer, protected/frozen, review simulation, or cross-lifecycle. Separate link rows connect an artifact or dataset to zero or more of the five lifecycle stages; composite/non-player classifications never enter the exact lifecycle enum. The registry does not copy raw values in the first lane.

### 4. Lifecycle evidence layer

Each player evidence observation is indexed into exactly one primary lifecycle stage. Cross-stage artifacts may link to several stages, and cross-stage derivations retain references to all parents, but no observation copies a draft-event field into pre-draft evidence or a later outcome into rookie-season input.

### 5. Lineage layer

Every consolidated field observation must retain source, timestamp, as-of date, receipt, transformation, confidence, and supersession. A displayed value is never separated from its lineage record.

### 6. Conflict and queue layer

Conflicts, duplicates, missing evidence, source-admission questions, and manual reviews are first-class append-only records. They cannot be silently resolved by a loader, join, or display component.

### 7. Governance and archive layer

No-recreate, supersession, archive, restricted locators, implementation status, hashes, and validation results make preservation and rollback explicit.

## Lifecycle boundaries

| Stage | Included evidence | Excluded evidence |
|---|---|---|
| `PRE_DRAFT` | college production, testing, declared position, school stints, measurements, admitted grades, timestamped pre-draft market context | draft result, NFL roster, rookie NFL usage, later outcomes |
| `DRAFT_EVENT` | drafted/undrafted/supplemental/transaction event, round, pick, team, evidence-backed entry status | pre-draft prospect value; later roster or outcomes |
| `POST_DRAFT_PRESEASON` | roster assignment, contract, camp/depth role, injuries, early opportunity with timestamps | draft-event values recast as pre-draft; regular-season outcomes |
| `ROOKIE_SEASON` | games, snaps, routes where admitted, touches, targets, points, availability, rookie-year finish | year-two or later values |
| `MULTI_YEAR_OUTCOME` | year-two, three-year, five-year, threshold hits, survival, availability-adjusted outcomes | incomplete windows interpreted as misses |

`CROSS_LIFECYCLE_IDENTITY`, `GOVERNANCE`, `PRODUCT_CONSUMER`, and `REVIEW_SIMULATION` are registry classifications, not player-evidence stages.

## Canonical views

Views may join metadata without changing underlying authority:

- `v_player_identity_status`: stable aliases, unresolved assertions, and manual-review status;
- `v_artifact_authority`: one row per artifact with current and historical authority decisions;
- `v_player_lifecycle_evidence`: references to stage-specific observations, not flattened values;
- `v_missing_expected_evidence`: expected evidence with no admitted observation;
- `v_open_manual_review`: unresolved queue items and linked evidence;
- `v_source_use_matrix`: source/dataset/field/purpose decisions;
- `v_supersession_chain`: predecessor/successor relationships with no deletion;
- `v_no_recreate`: existing systems, builders, fixtures, and parked work.

No view may:

- infer a value from absence;
- choose between conflicting values without an approved decision;
- collapse review-only and production-admitted states;
- coerce unavailable, not applicable, missing, blocked, and unknown into one null;
- join on normalized name as a controlling key;
- expose restricted raw paths or provider content when only a sanitized locator is allowed.

## Primary and foreign keys

The high-level graph is:

```text
player_registry (nwr_player_id)
  -> player_alias_registry (alias_id, nwr_player_id)
  -> identity_assertion_ledger (identity_assertion_id, candidate nwr_player_id)
  -> lifecycle_event_registry (lifecycle_event_id, nwr_player_id)
  -> stage evidence indexes (evidence_observation_id, nwr_player_id)

source_registry (source_id)
  -> dataset_registry (dataset_id, source_id)
  -> source_use_decision_ledger (use_decision_id, dataset_id)
  -> source_receipt_registry (receipt_id, dataset_id)

evidence_artifact_registry (artifact_id, receipt_id?)
  -> field_lineage_ledger (lineage_id, artifact_id, observation_id?)
  -> duplicate/conflict/supersession ledgers
  -> review and missing queues
```

Provider IDs, player names, seasons, and sentinel values are not workspace primary keys.

## Immutable, append-only, and mutable fields

### Immutable

- generated opaque IDs;
- original artifact path or sanitized locator ID;
- original artifact hash and byte count;
- source receipt identity and acquisition timestamp;
- original observed value and original state;
- original lifecycle stage and row grain;
- closed human decision receipt;
- protected/frozen designation.

### Append-only

- identity assertions and conflicts;
- source/use decisions;
- evidence observations and corrections;
- supersession relationships;
- review events and closure receipts;
- archive events;
- manifest versions and validation results.

### Mutable only as workflow metadata

- queue assignee/owner role;
- current queue status;
- implementation progress;
- non-authoritative display label, provided prior labels remain in event history.

## Versioning

- Schema version: semantic version, beginning `1.0.0`.
- Registry snapshot: `YYYYMMDD.N` plus Git commit.
- Every record carries `record_version`, `valid_from`, and optional `valid_to`.
- Corrections append a new record and a supersession link; they do not edit historical evidence.
- Breaking schema changes create a new major version and retain prior readers/manifests.
- Evidence-state or source-use changes require a decision ID and effective timestamp.

## Manifests and hashes

Each workspace snapshot requires:

- SHA-256 for every permitted tracked/local file;
- a sanitized locator and `hash_status=WITHHELD_OR_NOT_PERMITTED` when canonical retention of a restricted digest/path is not authorized;
- row and column counts for structured artifacts;
- complete schema fingerprints;
- source/normalized hashes when permitted;
- deterministic manifest ordering;
- a declaration that the manifest excludes its own hash to avoid a circular digest.

Hash equality establishes byte equivalence, not authority equivalence or permission to delete.

## Validation requirements

- UTF-8 and CSV parse checks;
- schema-version and required-column checks;
- unique primary keys and valid foreign keys;
- allowed enum values;
- no sentinel used as an ID;
- no name-only controlling join;
- lifecycle-field allowlist checks;
- source/use/rights precedence checks;
- missing/unknown/unavailable/not-applicable distinction;
- duplicate and conflict relationship coverage;
- window completion/censoring checks;
- threshold-applicability checks;
- hash and manifest verification;
- protected/frozen/no-recreate diff checks;
- exact inventory and source-artifact parity;
- rollback rehearsal.

## Archive policy summary

Archive means logical retirement, not deletion. Original artifacts remain at their source path until an independently authorized retention decision proves byte/hash parity, authority parity, rights compliance, and rollback. Restricted artifacts remain outside HQ; only permitted locators and aggregate metadata enter the registry.
