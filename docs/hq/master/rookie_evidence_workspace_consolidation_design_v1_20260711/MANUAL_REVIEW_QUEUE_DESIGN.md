# Manual Review Queue Design

## Purpose

The queue records questions and decisions without editing source evidence. It is append-only, evidence-linked, and incapable of silently resolving an item through a join, refresh, or display fallback.

## Common queue schema

Primary key: `review_id`.

Required fields:

- `review_id`
- `queue_type`
- `entity_type`
- `entity_key`
- `nwr_player_id` if resolved
- `source_entity_keys`
- `lifecycle_stage`
- `field_or_issue`
- `evidence_artifact_ids`
- `evidence_observation_ids`
- `source_receipt_ids`
- `conflict_ids`
- `priority`
- `owner_role`
- `status`
- `opened_at`
- `last_reviewed_at`
- `due_or_recheck_at`
- `allowed_resolution`
- `required_proof`
- `decision_id`
- `closure_receipt_id`
- `closed_at`
- `supersedes_review_id`
- `notes`.

`entity_key` is a queue key, not a player identity. Name-only records may use a source row key while `nwr_player_id` remains null.

## Priority

- `P0`: privacy, rights, credential exposure, frozen/protected mutation, or production-use risk;
- `P1`: identity/draft-status conflict that could corrupt multiple records or authorities;
- `P2`: incomplete lineage, outcome/position conflict, missing receipt, or stale authority;
- `P3`: coverage gap, unavailable period, documentation cleanup, or deferred review.

## Status

`OPEN`, `CLAIMED`, `WAITING_EVIDENCE`, `DECISION_PROPOSED`, `APPROVAL_REQUIRED`, `APPROVED`, `REJECTED`, `CLOSED_NO_CHANGE`, `SUPERSEDED`, `DUPLICATE_QUEUE_ITEM`.

Only `APPROVED`, `REJECTED`, and `CLOSED_NO_CHANGE` close the item, and each requires a closure receipt. `DUPLICATE_QUEUE_ITEM` links to the controlling review ID and does not erase history.

## Queue types

| Queue type | Entry key | Default priority/owner | Allowed resolution | Required proof | Closure receipt |
|---|---|---|---|---|---|
| `IDENTITY_CONFLICT` | source namespace + source ID/assertion IDs | P1 / identity steward | bind, keep separate, defer, reject assertion | durable IDs or human multi-source proof; uniqueness/collision audit | identity decision + alias/assertion IDs |
| `DRAFT_STATUS_CONFLICT` | player/assertion + draft year + league | P1 / draft evidence steward | select scoped positive event, keep competing, mark unknown | official/admitted event receipt and identity proof | event decision and source receipts |
| `LIKELY_VS_CONFIRMED_UDFA` | player/assertion + entry event | P1 / draft evidence steward | verified UDFA, keep likely, keep unknown, wrong universe | independent admitted confirmation; draft absence alone prohibited | entry-status decision receipt |
| `MISSING_SOURCE_RECEIPT` | artifact + source/dataset | P2 / source governance | attach permitted receipt, mark unrecoverable, keep blocked | acquisition/version/hash/schema/coverage/use evidence | receipt ID or unrecoverable decision |
| `UNCLEAR_SOURCE_RIGHTS` | source + dataset + field + purpose | P0/P1 / rights owner | allow named purpose, block, local-only, not enough information | authoritative license/terms/permission and privacy review | rights/use decision ID |
| `CONFLICTING_DRAFT_CAPITAL` | player/assertion + draft event | P1 / draft evidence steward | approve one scoped assertion, retain both unresolved | source receipts, exact identity, event chronology | conflict resolution ID |
| `POSITION_CONFLICT` | player/assertion + validity interval | P2 / identity steward | time-bound positions, correct assertion, keep unresolved | provider/event receipts and season context | position-event decision |
| `OUTCOME_LABEL_CONFLICT` | player + scoring system + season/window + metric | P1/P2 / outcome steward | retain separate systems, approve scoped interpretation, correct transform | scoring rules, receipts, applicability, parity and identity | outcome conflict decision |
| `STALE_OR_SUPERSEDED_ARTIFACT` | predecessor artifact ID | P3 / artifact steward | designate successor, keep current, archive logically | byte/schema/population/authority parity and rollback | supersession decision |
| `INCOMPLETE_SEASON_COVERAGE` | dataset + season/position/team | P2/P3 / source steward | mark unavailable, missing expected, partial accepted, collect later | coverage receipt and expectation contract | coverage decision |
| `FAILED_LINEAGE` | artifact/observation + missing lineage field | P1/P2 / lineage steward | attach proof, keep blocked, mark unrecoverable | required receipt/transformation/as-of evidence | lineage decision |
| `NOT_ENOUGH_INFORMATION` | entity + question + evidence version | P2/P3 / owning domain | remain unknown, reclassify with proof, close no change | evidence listed in the opening item | decision or no-change receipt |

## Initial queue seeds from this audit

The design does not open or resolve queue records, but the first implementation should seed metadata entries for:

- 50 duplicate current identity assertions propagated across current artifacts;
- three distinct current approvals without stable candidate IDs;
- 54 historical drafted/likely-UDFA name groups;
- five historical bridge rows missing GSIS;
- 102 positive draft rows missing player ID;
- Kevin Coleman Jr. multi-CFBD-ID conflict;
- seven current draft-round conflicts;
- current `confirmed_udfa_review_only` semantics;
- 31,614 unmatched CFBD rows at appropriate batched/partitioned queue grain;
- missing historical entry builder/input lineage;
- local GSIS bridge/rookie label receipt-chain gaps;
- Outcome V2 versus Historical Fantasy Finish conflict;
- Formula Data Mart versus Historical Model Lab target conflict;
- threshold applicability for QB/TE T24/T36;
- 22 linked historical rookie rows without usable horizon values;
- rights/retention questions for CFBD, prospect grades, RotoWire/provider exports, third-party combine, and restricted recovered matrices;
- off-HQ ranking simulation source, identity, duplicate-rank, and authority blockers.

Large populations must be partitioned by stable source keys and issue type. A single aggregate count is not a substitute for reviewable evidence links, but creating tens of thousands of queue records without an approved batching design is also prohibited.

## No-silent-resolution rule

A queue item may not close because:

- a newer file appears;
- a normalized name matches;
- one value is non-null;
- one source is more familiar;
- duplicate bytes are found;
- a human previously approved review-only use;
- a product surface displays a value;
- a source-family registry looks permissive;
- missing evidence is interpreted as a negative fact.

Closure requires an allowed resolution, required proof, an explicit decision, a closure receipt, and successful validation. Source evidence remains unchanged.

## Audit trail

Every status change appends a `review_event` with prior/new status, actor role, timestamp, reason, evidence version, and decision/receipt IDs. Edits to a closed item create a superseding review item; they do not overwrite history.

## Product boundary

The queue design does not create a new UI or replace existing manual-review flows. A future read-only workspace may link to existing queues and normalize metadata. Product routing, notifications, assignment automation, or resolution controls require a separate authorized lane.
