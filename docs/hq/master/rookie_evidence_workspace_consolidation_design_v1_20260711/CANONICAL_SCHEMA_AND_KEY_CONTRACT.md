# Canonical Schema and Key Contract

## Key principles

1. Workspace IDs are opaque and provider-independent.
2. Provider IDs are aliases, never overloaded as the canonical NWR ID.
3. The literal `Not enough information`, blank strings, normalized names, and row numbers are never keys.
4. Every evidence row has its own immutable observation ID even when player identity is unresolved.
5. Lifecycle stage, season/window, source, receipt, and transformation are part of evidence grain.
6. Duplicate rows remain separate source assertions until an explicit relationship says they are equivalent.
7. Corrections and supersession are append-only.

## Required schemas

### `PLAYER_IDENTITY_REGISTRY.csv`

Primary key: `nwr_player_id`

| Field | Requirement |
|---|---|
| `nwr_player_id` | immutable opaque ID such as `nwrp_<uuidv7>`; never a provider ID |
| `display_name` | current admitted display name; not a key |
| `normalized_name_review_only` | normalization aid; never controls a join |
| `declared_position_current` | current admitted position or unknown |
| `birth_date` | nullable only with admitted source and lineage |
| `identity_status` | `CONFIRMED`, `PROVISIONAL`, `CONFLICTING`, or `UNRESOLVED` |
| `identity_confidence` | enumerated confidence with method/evidence; not a probability unless calibrated |
| `created_at`, `created_by_lane` | immutable creation receipt |
| `valid_from`, `valid_to` | registry validity interval |
| `manual_review_status` | current queue state, linked to review history |

### `PLAYER_ALIAS_REGISTRY.csv`

Primary key: `alias_id`. Foreign key: `nwr_player_id`.

Required fields: `alias_id`, `nwr_player_id`, `namespace`, `provider_id`, `provider_name`, `valid_from`, `valid_to`, `team_context`, `season_context`, `source_id`, `receipt_id`, `identity_assertion_id`, `alias_status`, `superseded_by_alias_id`.

Unique active constraint: `(namespace, provider_id)` may map to at most one active `nwr_player_id`. A collision creates conflict records and no active controlling alias.

Namespaces include `GSIS`, `SLEEPER`, `CFBD`, `PFR`, `DYNASTYPROCESS`, provider-specific IDs, and legacy packet-local namespaces. `NWR` is reserved for `nwr_player_id` and cannot be inferred from another namespace.

### `IDENTITY_ASSERTION_LEDGER.csv`

Primary key: `identity_assertion_id`.

Required fields include:

- candidate and asserted NWR player IDs;
- source namespace/provider ID;
- college identity and school stint when relevant;
- draft identity and event ID when relevant;
- normalized name for review only;
- position, birth date, team, and season context where admitted;
- `identity_confidence`;
- `join_method`;
- `join_evidence`;
- `conflict_reason`;
- `manual_review_status`;
- source, receipt, as-of, and decision IDs.

Allowed controlling join methods:

- exact stable provider ID already bound by an admitted crosswalk;
- exact official event/provider ID plus a unique admitted crosswalk;
- explicit human-approved multi-source binding with durable IDs and collision checks.

Review-only methods:

- exact name+position;
- normalized name+team;
- name+school+season;
- fuzzy/phonetic name.

Name-only is always prohibited as a controlling method.

### `SOURCE_REGISTRY.csv`

Primary key: `source_id`.

Fields: `source_id`, `source_name`, `provider`, `source_family`, `owner_role`, `default_admission`, `rights_status`, `privacy_class`, `redistribution_status`, `retention_status`, `registry_version`, `decision_id`, `effective_at`, `notes`.

The default is only a routing hint. Dataset/field/purpose decisions are authoritative.

### `DATASET_REGISTRY.csv`

Primary key: `dataset_id`. Foreign key: `source_id`.

Fields: endpoint/table/release, row grain, seasons, positions, teams, mutable/static status, provider version, expected schema, identity keys, lifecycle coverage, source receipt requirements, and dataset-specific rights status. Dataset lifecycle coverage uses `DATASET_LIFECYCLE_LINK.csv`; it never stores a composite value in the five-value lifecycle enum.

### `SOURCE_USE_DECISION_LEDGER.csv`

Primary key: `use_decision_id`.

Unique decision grain: `(dataset_id, field_family, purpose, decision_version)`.

Purposes are exactly:

- `LOCAL_RETENTION`
- `CANONICAL_HQ_SUMMARY`
- `RAW_RECEIPT_STORAGE`
- `DISPLAY`
- `RESEARCH`
- `MODEL_TRAINING`
- `PRODUCTION_SCORING`
- `REDISTRIBUTION`
- `EXPORT`

Decision values: `ALLOWED`, `ALLOWED_WITH_CAVEATS`, `REVIEW_ONLY`, `BLOCKED`, `NOT_ENOUGH_INFORMATION`, `NOT_APPLICABLE`.

Required fields: `use_decision_id`, `dataset_id`, `field_family`, `purpose`, `decision_value`, `decision_version`, `effective_at`, `evidence_links`, `rights_status`, `privacy_class`, `caveat_text`, `owner_role`, `approval_receipt_id`, and `supersedes_use_decision_id`. Every bounded-pilot dataset/field family receives nine purpose rows; prose in a source report is never parsed as a decision.

### `SOURCE_RECEIPT_REGISTRY.csv`

Primary key: `receipt_id`. Foreign keys: `dataset_id`, optional `artifact_id`.

Required fields follow the HQ1 receipt standard: source/provider/owner, acquisition method/time, release/version, permitted raw locator, raw and normalized hashes where permitted, row/column counts, schema/dictionary, coverage, row grain, player keys, join method, identity/source/admission/licensing/leakage/missingness/coverage states, blocked fields, rebuild path, validation, use gate, and decision-date as-of.

Restricted paths/hashes use a permitted `restricted_locator_id` and an explicit withholding reason; they are not copied into HQ.

### `EVIDENCE_ARTIFACT_REGISTRY.csv`

Primary key: `artifact_id`.

Required fields:

`artifact_id,path_or_locator,location_status,git_commit,sha256_or_hash_status,byte_count,file_type,row_count,column_count,schema_fingerprint,row_grain,artifact_scope_class,evidence_state,authority_level,canonical_flag,supporting_flag,duplicate_flag,superseded_flag,local_only_flag,blocked_flag,incomplete_flag,source_id,dataset_id,receipt_id,as_of_status,rights_status,privacy_class,proposed_disposition`.

`artifact_scope_class` is an artifact classification such as governance, product consumer, review simulation, protected/frozen, legacy fixture, or cross-lifecycle collection. It is not a lifecycle enum.

### Lifecycle coverage links

`ARTIFACT_LIFECYCLE_LINK.csv` and `DATASET_LIFECYCLE_LINK.csv` use keys `(artifact_id, lifecycle_stage)` and `(dataset_id, lifecycle_stage)`. Required fields are the parent ID, one exact five-value `lifecycle_stage`, `link_scope`, `link_basis`, `primary_for_artifact_or_dataset`, and decision/receipt ID. An artifact or dataset may have zero links when it contains no player evidence, or multiple links when it covers multiple stages. A player evidence observation always has exactly one primary lifecycle stage.

### Stage-specific evidence indexes

Every stage table uses primary key `evidence_observation_id` and foreign keys `artifact_id`, optional `nwr_player_id`, `source_id`, `dataset_id`, `receipt_id`, and `lineage_id`.

Common required fields:

- original source row key;
- stage-specific event/window key;
- evidence type and field definition ID;
- original value and typed value;
- exactly one five-value `lifecycle_stage`;
- one exact 14-value `evidence_state`;
- explicit `identity_state`;
- explicit `source_admission_state`;
- explicit `use_decision_state` plus `use_decision_id`;
- explicit `availability_state`;
- explicit `duplication_state` plus duplicate relationship ID where applicable;
- explicit `locality_state`;
- explicit `censoring_state`;
- confidence;
- effective time, source timestamp, and as-of date;
- transformation version;
- superseded observation ID.

All seven orthogonal state dimensions are required even when their value is `NOT_APPLICABLE`. They are not derivable from the primary evidence state, artifact location, or nullness.

Stage-specific keys:

| Table | Required grain beyond observation ID |
|---|---|
| `PRE_DRAFT_EVIDENCE_INDEX` | prospect cycle, evidence date, school stint, pre-draft field |
| `DRAFT_EVENT_EVIDENCE_INDEX` | `draft_event_id`, event type, draft year, league, pick/supplemental/transaction sequence |
| `POST_DRAFT_PRESEASON_EVIDENCE_INDEX` | team, season, effective date/time, evidence type |
| `ROOKIE_SEASON_EVIDENCE_INDEX` | rookie season, week/game or season grain, statistic/availability field |
| `MULTI_YEAR_OUTCOME_EVIDENCE_INDEX` | anchor season, window definition ID, threshold/metric ID, completion/censoring status |

### `OUTCOME_WINDOW_REGISTRY.csv`

Primary key: `outcome_window_id`.

Fields: anchor event, start/end rules, calendar versus active-season rule, required complete seasons, decision-date safety, threshold registry, position applicability, censoring rule, availability adjustment, and scoring basis.

### `OUTCOME_THRESHOLD_APPLICABILITY.csv`

Primary key: `(threshold_id, position, window_family)`.

Fields: `applicable`, reason, source decision, effective version. This prevents QB/TE T24/T36 generic season values from being silently treated as applicable rookie outcomes.

### `FIELD_LINEAGE_LEDGER.csv`

Primary key: `lineage_id`.

Every consolidated field retains:

- `source_id`, `dataset_id`, and `receipt_id`;
- source timestamp, acquisition timestamp, effective timestamp, and decision-date as-of;
- original source path or permitted restricted locator;
- source row key, source field, original value, and typed value;
- `use_decision_id`, purpose, and use status;
- input artifact/row/field;
- transformation ID, version, parameters, and code commit;
- identity assertion ID, join method, and join evidence;
- confidence and confidence basis;
- exact lifecycle stage plus lifecycle event ID and outcome-window ID where applicable;
- availability, missingness, censoring, and applicability states;
- previous/superseded source, lineage, and observation IDs;
- validation receipt and human decision IDs.

If any required item is stored in a linked registry rather than repeated in the ledger row, its foreign key is non-null and validation must prove the join is one-to-one and lossless for that lineage version.

### Conflict, duplicate, queue, and supersession schemas

- `EVIDENCE_CONFLICT_LEDGER`: `conflict_id`, linked assertions/observations, conflict type, field/window, evidence links, authority state, status, required proof, resolution ID.
- `DUPLICATE_RELATIONSHIP_LEDGER`: `duplicate_relation_id`, artifact/row A and B, duplicate class, relationship scope, count basis, equivalence/conflict proof, authority decision, proposed disposition, status, human-review requirement, blocker, validation receipt, rollback link, decision ID, closure receipt ID, and superseded relation ID.
- `MISSING_EVIDENCE_QUEUE`: `missing_id`, expected evidence definition, player/event/window, reason expected, availability state, evidence links, owner/status/closure receipt.
- `MANUAL_REVIEW_QUEUE`: `review_id`, queue type, entity key, evidence links, priority, owner/status, allowed resolution, required proof, closure receipt.
- `SOURCE_ADMISSION_QUEUE`: `source_queue_id`, source/dataset/field/purpose, rights/privacy/receipt/identity gaps, owner/status/decision receipt.
- `SUPERSESSION_LEDGER`: `supersession_id`, predecessor, successor, scope, reason, authority, effective date, parity receipt, rollback link.

The design packet's duplication register carries both narrative fields and closed `classification_enum` / `disposition_enum` mappings. Its `AUDITED_DESIGN_INPUT_NOT_IMPLEMENTED` validation status and `NOT_CREATED_DESIGN_LANE` decision-receipt status must remain unchanged until Phase 6 creates actual relationship, validation, decision, and closure receipts. Import rejects any narrative value without an allowlisted enum mapping.

## Deterministic key rules

1. An unresolved player still receives an `evidence_observation_id`; `nwr_player_id` stays null and an identity assertion/queue is required.
2. The same provider ID cannot actively bind to two NWR IDs.
3. The same NWR ID may have multiple time-bounded provider aliases.
4. A draft event is keyed independently of player identity so a positive draft event with missing player ID remains preserved.
5. Duplicate source rows get separate observation IDs and a duplicate relationship; loaders never discard one.
6. A source row with `Not enough information` in an ID field fails key validation and uses a surrogate observation/event key.
7. Stage evidence cannot be upserted by `(name, position, season)`.
8. Outcome keys include scoring basis, position applicability, and window definition; otherwise competing systems would collide.

## Required enums

- lifecycle: `PRE_DRAFT`, `DRAFT_EVENT`, `POST_DRAFT_PRESEASON`, `ROOKIE_SEASON`, `MULTI_YEAR_OUTCOME`;
- evidence state: `CANONICAL_ADMITTED`, `CANONICAL_REVIEW_ONLY`, `SUPPORTING_EVIDENCE`, `PROVISIONAL`, `IDENTITY_UNRESOLVED`, `SOURCE_UNADMITTED`, `USE_BLOCKED`, `DUPLICATE_EQUIVALENT`, `DUPLICATE_CONFLICTING`, `SUPERSEDED`, `LOCAL_ONLY_RESTRICTED`, `MISSING_EXPECTED`, `UNAVAILABLE`, `NOT_ENOUGH_INFORMATION`;
- availability: `PRESENT`, `MISSING_EXPECTED`, `UNAVAILABLE`, `NOT_APPLICABLE`, `NOT_ENOUGH_INFORMATION`;
- identity: `CONFIRMED`, `PROVISIONAL`, `CONFLICTING`, `UNRESOLVED`;
- source admission: `ADMITTED`, `REVIEW_ONLY`, `UNADMITTED`, `NOT_ENOUGH_INFORMATION`, `NOT_APPLICABLE`;
- use decision: `ALLOWED`, `ALLOWED_WITH_CAVEATS`, `REVIEW_ONLY`, `BLOCKED`, `NOT_ENOUGH_INFORMATION`, `NOT_APPLICABLE`;
- duplication state: `NO_DUPLICATE_RELATION`, `DUPLICATE_REVIEW_PENDING`, `DUPLICATE_EQUIVALENT`, `DUPLICATE_CONFLICTING`;
- duplicate class: `EXACT_DUPLICATE`, `SCHEMA_EQUIVALENT_DUPLICATE`, `TRANSFORMED_DERIVATIVE`, `OVERLAPPING_POPULATION`, `STALE_PREDECESSOR`, `CONFLICTING_EVIDENCE`, `INDEPENDENT_CORROBORATION`, `NOT_ACTUALLY_DUPLICATED`;
- duplicate disposition: `RETAIN_BOTH`, `DESIGNATE_CANONICAL_AND_SUPPORTING`, `SUPERSEDE`, `ARCHIVE_LOGICALLY`, `MERGE_LATER`, `MANUAL_REVIEW`, `BLOCK_CONSOLIDATION`;
- locality: `LIVE_HQ`, `LOCAL_ONLY`, `LOCAL_ONLY_RESTRICTED`, `OFF_HQ_BRANCH_ONLY`;
- censoring: `COMPLETE`, `RIGHT_CENSORED`, `LEFT_CENSORED`, `PARTIAL`, `NOT_APPLICABLE`;
- review status: `OPEN`, `CLAIMED`, `WAITING_EVIDENCE`, `DECISION_PROPOSED`, `APPROVAL_REQUIRED`, `APPROVED`, `REJECTED`, `CLOSED_NO_CHANGE`, `SUPERSEDED`, `DUPLICATE_QUEUE_ITEM`;
- identity assertion status: `PROPOSED`, `ACTIVE`, `CONFLICTING`, `REJECTED`, `SUPERSEDED`.

The evidence-state enum is closed: no other status may be stored in `evidence_state`. Queue, identity-assertion, source/use, duplication, locality, availability, and censoring statuses use their own columns and enums.

## Constraint examples

- `drafted_status=true` requires a positive draft-event observation; it cannot be inferred from a non-null round copied from an unadmitted artifact.
- `verified_udfa=true` requires an admitted confirmation observation; draft-pick absence alone fails.
- `label_value=miss` requires an applicable, complete, observed window; missing, censored, or not applicable fail.
- `model_training=ALLOWED` requires source, identity, rights, leakage, field, and purpose decisions all allowed. No current rookie artifact satisfies this.
- `production_scoring=ALLOWED` requires a separate production-admission decision. No design or scaffold record can create one.

## Migration key acceptance

A source family may be indexed at artifact level immediately. Player-level observations may be registered only when:

- the source row grain is explicit;
- a stable source row key exists or a deterministic immutable observation ID is minted;
- provider identity is exact or deliberately unresolved;
- duplicate rows are retained and related;
- receipt and use decisions are present;
- lifecycle stage and as-of rules pass;
- restricted content is permitted for the target storage.

Failure preserves the artifact at metadata level and creates a queue entry; it never justifies a guessed key.
