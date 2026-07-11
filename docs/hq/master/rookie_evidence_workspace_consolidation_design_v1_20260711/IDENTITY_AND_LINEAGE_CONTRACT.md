# Identity and Lineage Contract

## Controlling identity rule

Name-only matching is prohibited as controlling evidence. Normalized name, name+position, name+team, name+school, fuzzy name, and phonetic name may generate review candidates only. They cannot create or overwrite a canonical identity, join player values, resolve draft status, or support scoring/model/training/production use.

## Required identity fields

Every player identity record or assertion supports:

- canonical opaque `nwr_player_id`;
- GSIS ID where available;
- Sleeper ID where available;
- provider IDs with explicit namespaces;
- college identity and school stints;
- draft identity and event ID;
- normalized name for review only;
- position with validity period;
- birth date only when admitted;
- team and season context;
- identity confidence;
- join method;
- join evidence;
- conflict reason;
- manual-review status;
- source, receipt, as-of, and decision lineage.

The same field name may not silently mix GSIS, Sleeper, CFBD, or packet-local IDs. Existing mixed `player_id` and `nwr_player_id` fields are registered with their actual namespace or `NAMESPACE_UNRESOLVED`.

## Current identity reality

- The principal current chain has `157` row occurrences but `107` distinct exact records.
- `104` distinct current records have non-placeholder candidate IDs; three approved records—Sieh Bangura, Devin Voisin, and Braylon James—lack NWR/Sleeper IDs.
- Current IDs include numeric Sleeper-like values, GSIS strings, and missing values under the same field names.
- The historical GSIS bridge has `1,025` unique drafted rows, `1,020` with GSIS and five missing GSIS.
- The 919 historical rookie labels use GSIS/player-stats identity; their NWR and CFBD IDs are absent.
- The positive drafted manifest has `102` rows without a player ID.
- CFBD has `31,614` unmatched rows, ambiguous/multiple candidates, and duplicate assertions.
- Historical entry status contains 54 name+position+class groups spanning drafted and likely-UDFA records; some are likely duplicates, while Chris Davis and Chris Givens are true same-name conflicts.

None of those conditions may be hidden by a deduplication or fallback join.

## Identity assertion workflow

1. Preserve the source row and its provider ID, even if unresolved.
2. Create an immutable `identity_assertion_id`.
3. Record candidate NWR identity, join method, evidence, season/team/position context, and confidence.
4. Run uniqueness and collision checks across active aliases.
5. Route unsafe or competing assertions to the identity queue.
6. A human decision may approve a review-only binding without granting source truth, model, training, ranking, or production use.
7. A controlling binding requires a separate allowed-use decision and durable provider evidence.
8. Corrections append a new assertion and supersession link; the old assertion remains.

## Join-method classes

| Class | Methods | Controlling use |
|---|---|---|
| `STABLE_ID_EXACT` | exact GSIS, Sleeper, CFBD, or provider ID through an admitted unique crosswalk | allowed only for purposes covered by source/use decision |
| `OFFICIAL_EVENT_ID` | official draft/transaction ID plus admitted player crosswalk | allowed within event scope |
| `HUMAN_MULTI_SOURCE_DURABLE_ID` | human-approved agreement across two or more durable IDs with collision checks | purpose-limited; decision receipt required |
| `NAME_POSITION_REVIEW` | exact/normalized name + position, optionally team/school/season | review candidate only |
| `FUZZY_NAME_REVIEW` | fuzzy/phonetic/token similarity | review candidate only |
| `NAME_ONLY_PROHIBITED` | name without durable corroboration | never controlling; route to unresolved queue |

## Special-case handling

### Name changes

Store each legal/display name as a time-bounded alias. Do not rewrite historical source names. A human-reviewed alias relationship links the names to one NWR ID.

### Suffixes and punctuation

Preserve original text. Store normalized forms only for review candidate generation. Suffix removal, punctuation folding, apostrophe handling, and diacritic folding never establish identity.

### Duplicate names

Require durable provider IDs or human-approved multi-source evidence. Team, school, position, and birth date are conflict evidence, not substitutes for an ID. Same-name records may remain separate indefinitely.

### Position changes

Use a time-bounded `player_position_event`. Do not overwrite the source position or interpret a mismatch as the same person without identity proof. Outcome threshold applicability uses the position defined for that window.

### School transfers

Use a `college_stint_id` with school, season, start/end dates, and source. The player keeps one canonical ID; school identity is contextual. Multiple schools in one cycle are not duplicate players.

### Player re-entry

One person retains one `nwr_player_id`; each league entry/re-entry receives a separate `entry_event_id`. A new draft, supplemental, international allocation, or transaction event is not a new player identity.

### Supplemental drafts

Use `draft_event_type=SUPPLEMENTAL_DRAFT`, with event date, round/forfeited pick context, team, league, and official source. Do not coerce to the standard draft table without event lineage.

### International players

College identity may be `NOT_APPLICABLE`. Store international club/league identities and entry mechanism. Absence of a college row is not missing expected evidence unless the population contract requires one.

### Missing provider IDs

Preserve the observation under its source row key with null `nwr_player_id`; create an identity assertion and queue. Do not fabricate a stable ID from a name hash.

### Conflicting provider records

Retain every assertion, create `DUPLICATE_CONFLICTING`, list fields and source receipts, block controlling joins, and require a closure receipt. Never pick the newest or most complete row automatically.

## Lineage fields required for every consolidated value

- `source_id`
- `dataset_id`
- `receipt_id`
- source timestamp
- acquisition timestamp
- decision-date as-of
- original source path or permitted restricted locator
- source row key and source field
- original value and typed value
- source/use status for the intended purpose
- transformation ID, version, parameters, and code commit
- identity assertion and join method
- confidence and confidence basis
- lifecycle stage and event/window ID
- missingness/availability/censoring/applicability states
- predecessor/superseded source or observation
- validation and human decision receipts.

## Lineage gaps found

- The historical entry-status CSV has no tracked reproducible builder or complete input receipt chain.
- Local GSIS bridge and 919-row labels have hashes now recoverable, but their tracked manifests do not persist complete input hashes/raw receipt metadata.
- Current Gate F V5 has no complete row-level source timestamp, receipt ID, transformation version, or superseded-source pointer.
- The draft-capital sidecar stores source path/hash and join/as-of status but lacks a complete independent source timestamp/receipt/transformation chain.
- Legacy and off-HQ ranking pipelines use manual recovery or normalized-name joins and cannot be admitted.
- Local outcome systems have strong hashes/manifests but materially different scoring/rank bases; lineage must preserve them as independent systems.

## Lineage validation

A row fails controlling lineage if any of these is true:

- source or field purpose is not admitted;
- identity is name-only or ambiguous;
- source/acquisition/as-of timing cannot be established for the intended use;
- transformation cannot be reproduced;
- original value is not preserved;
- competing source is hidden;
- missing/censored/not-applicable state is coerced;
- receipt/rights/privacy boundary is absent;
- a superseded or review-only value is presented as production-admitted.

Failure keeps the record in the workspace as blocked/supporting evidence and creates a queue item. It does not remove the record.
