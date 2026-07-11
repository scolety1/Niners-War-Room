# Rookie Evidence Workspace Consolidation Design V1 Report

## Verdict

`YELLOW_ROOKIE_EVIDENCE_WORKSPACE_DESIGN_READY_WITH_AUTHORITY_CAVEATS`

The design is ready for implementation review. A destructive consolidation is not safe, and none is authorized. The safe path is a read-only metadata registry that references existing artifacts, preserves every source and version, and keeps all player values behind their existing identity, source, use, rights, and lifecycle gates.

## Controlling repository state

- Remote: `origin`
- Controlling branch: `work/hq-parallel-control`
- Expected HEAD: `9368a083ae59bdb9dfc7744b90fae0c449097e1d`
- Verified live remote HEAD after `git fetch --all --prune`: `9368a083ae59bdb9dfc7744b90fae0c449097e1d`
- Remote advanced: `no`
- Intervening commits: `0`
- Isolated worktree: `C:\NWR\Niners-War-Room-rookie-evidence-workspace-consolidation-design-v1-20260711`
- Branch: `work/rookie-evidence-workspace-consolidation-design-v1-20260711`
- Only permitted write prefix: `docs/hq/master/rookie_evidence_workspace_consolidation_design_v1_20260711/`

## Scope and non-actions

This packet is documentation, data architecture, inventory, and migration contract only. It did not:

- change rankings, formulas, production data, source admission, app behavior, draft behavior, recommendations, or hidden logic;
- move, delete, rename, rewrite, deduplicate, consolidate, or migrate existing evidence;
- infer UDFA truth from missing draft evidence;
- call Flaim, FantasyBot, or any plugin;
- reopen plugin or formula research;
- copy raw CFBD caches, restricted provider content, private receipts, or substantial provider output into HQ;
- modify the immutable prospective 2026 freeze.

## Audit method

The audit read live-HQ files, schemas, manifests, CSV rows, lineage documents, existing builders, source registries, identity ledgers, no-recreate indexes, roadmap controls, local shared-data outputs explicitly referenced by tracked packets, and the known off-HQ review-only ranking simulation. It did not rely only on packet summaries.

The broad inventory contains:

- `1,269` artifact records;
- `1,085` live-HQ file records;
- `162` local-only file records;
- `3` sanitized local-restricted aggregate locators;
- `19` off-HQ branch-only ranking-simulation files;
- `463` CSV artifacts whose headers, row counts, hashes, and exact duplicate-row counts were inspected;
- `23` scoped authority-family decisions;
- `30` duplication/conflict register entries;
- `40` no-recreate entries.

The core tracked rookie packet set comprises `31` packet directories, `265` files, `83` CSVs, and `31,940` CSV row occurrences. Those row occurrences include derivatives and duplication and must not be read as distinct players or facts.

## Executive findings

1. There is no production-authoritative canonical Rookie Evidence Workspace today. The strongest artifacts are scoped review-only evidence and policy.
2. The historical drafted-only GSIS bridge and 919-row historical rookie label output are the most dependable player-level linkage chain. They remain local-only/review-only, contain no canonical NWR IDs, and lack a complete tracked raw-receipt/hash chain.
3. The current 157-row rookie chain is duplicate-inflated. In its principal artifacts, `157` row occurrences represent `107` distinct exact records. Fifty exact duplicate records propagate through draft, combine, universe, and Gate F V1-V5 artifacts. Only `104` distinct current records have a non-placeholder candidate player ID; three approved current records have no stable candidate ID.
4. The historical entry-status artifact contains `4,653` rows: `1,999` drafted, `2,514` likely-UDFA-needs-review, `138` wrong-universe, `2` name-collision, and `0` confirmed UDFA. It is review-only and has missing builder/input lineage.
5. Positive draft evidence is materially stronger than negative evidence. The 1,999-row drafted admission manifest contains positive completed-draft facts, but `102` rows lack a player ID. The 5,518-row review-only sidecar safely joins `4,044` player-season rows to positive draft evidence and leaves `1,474` as not enough information.
6. The current UDFA application records `28` accepted row occurrences and `10` unknown row occurrences, but only `15` accepted and `5` unknown distinct contexts. Its `confirmed_udfa_review_only` label is a review decision, not verified UDFA source truth.
7. Outcome systems cannot be merged by similarity. Outcome V2 and the Historical Fantasy Finish Foundation disagree on `6,700` shared position ranks and `3,212` shared fantasy-point values. Formula Data Mart and Historical Model Lab targets disagree on `1,302` points, `4,922` ranks, and `2,606` PPG values across shared keys.
8. Outcome threshold applicability is position-dependent. All `930` rookie-versus-season threshold mismatches were QB/TE T24/T36 fields that are not applicable under the rookie/anchor policy; all `8,214` applicable checks matched.
9. Name and name+position matching appear in several review pipelines and product display fallbacks. They are supporting review evidence only and cannot control identity in the designed workspace.
10. The off-HQ ranking simulation at `82384338db5a6f6ca73942e67ae82e469be4ddb5` is not an ancestor of live HQ, uses a manual-recovery ID source and name+position identity, carries duplicate player ranks, and conflicts with live-HQ ranking-simulation blocks. It is indexed as local-only/use-blocked and must not be consolidated.

## Answers to the ten design questions

### 1. What rookie evidence exists?

Evidence exists across five lifecycle stages plus governance and consumers:

- pre-draft: CFBD production/roster review data, combine measurements, prospect-source policies, and legacy/restricted prospect matrices;
- draft-event: positive draft picks, current repair artifacts, draft-class GSIS bridge, entry-status candidates, and UDFA review packets;
- post-draft/preseason: current universe, roster/depth-context review, and Gate F display snapshots;
- rookie-season: rookie-year finish and threshold labels, usage/availability evidence through broader Outcome/NFLVerse systems;
- multi-year: year-two, first-three-year, first-five-year, Outcome V2, historical finish, and model-lab target systems;
- supporting governance: identity audits, source registries, source-admission decisions, receipt standards, no-recreate indexes, roadmaps, Gate F/G decisions, and frozen-artifact policies;
- existing consumers: Player Compare, Trading Lab, Development Lab, Data Health, Live/Mock Draft, and historical replay.

Every discovered artifact is recorded in `EXISTING_WORKSPACE_INVENTORY.csv`; the scoped authority decision is in `EVIDENCE_AUTHORITY_CLASSIFICATION.csv`.

### 2. Which artifacts are authoritative, supporting, duplicated, superseded, blocked, missing, local-only, or review-only?

No player-level rookie artifact is production-authoritative. Authority is purpose-limited:

- `CANONICAL_ADMITTED`: governance only, including the roadmap, source-family registry, receipt standard, sanitized plugin boundary, and no-recreate controls;
- `CANONICAL_REVIEW_ONLY`: scoped policies or packet outputs such as positive drafted-event admission, historical entry-status policy, current human decision receipts, Outcome compact source, draft-capital sidecar, and immutable formula freeze;
- `SUPPORTING_EVIDENCE`: local bridge/labels, audits, coverage matrices, consumers, and independent outcome systems;
- `DUPLICATE_EQUIVALENT`: duplicate-inflated current chains and exact tracked/local copies;
- `DUPLICATE_CONFLICTING`: competing draft rounds, scoring systems, target systems, threshold semantics, or source authority;
- `SUPERSEDED`: Gate F V1-V4, early Gate C blockers, draft-capital V1 for current review display, and legacy training/source claims;
- `LOCAL_ONLY_RESTRICTED`: restricted provider matrices, off-HQ ranking simulations, legacy provider-derived pipelines, and sanitized raw-cache locators;
- `SOURCE_UNADMITTED`, `IDENTITY_UNRESOLVED`, and `USE_BLOCKED`: CFBD production, prospect grades, inferred UDFA truth, name-keyed historical data, off-HQ ranking output, and formula/ranking activation.

### 3. Which identities and joins are dependable?

Dependable within review scope:

- exact GSIS/player ID plus season/position joins in the historical draft bridge, rookie labels, Formula Data Mart, and positive draft sidecar;
- exact provider-ID assertions supported by an audited crosswalk and explicit human approval, with collision and uniqueness checks.

Not dependable as controlling identity:

- normalized name alone;
- name+position, name+team, or fuzzy name matches;
- the literal `Not enough information` as an ID;
- packet-local `canonical_universe_id` values without a namespace binding;
- mixed `player_id` columns that may be Sleeper numeric IDs, GSIS strings, or missing;
- the three approved current identities with no NWR/Sleeper ID;
- the five historical bridge rows missing GSIS;
- the 54 historical name+position+class groups spanning drafted and likely-UDFA rows.

### 4. How is lifecycle separated?

The architecture uses stage-specific observation tables and forbids implicit field movement between them. Draft capital is a draft-event fact, not a pre-draft feature. Current roster/depth/injury context is post-draft and cannot be backfilled into historical pre-draft rows. Rookie-year outcomes and multi-year windows remain separate, and every window carries completion/censoring state.

### 5. Which sources are admitted for display, research, modeling, or production?

The source-family registry is not a blanket use decision. The narrowest field/dataset/use decision controls, and conflicts fail closed.

- nflverse positive completed draft picks and combine measurements: factual source families, but the inspected rookie artifacts remain review/display-only and are not production/model/training/source truth;
- Outcome V2 compact labels: admitted for tracked review/parity only, not label truth, training, model input, or rookie production;
- CFBD: local review and identity analysis only; production/model/training/source truth remain blocked;
- current market/ADP: current display context only; no historical use;
- prospect grades, licensed provider exports, unclear-license third-party data, and raw plugin/provider output: blocked or local-only pending rights and use decisions;
- plugins: manual consultation only, `0%` numerical influence.

### 6. How are missing, provisional, disputed, and unavailable represented?

They are distinct states:

- expected evidence absent: `MISSING_EXPECTED`;
- source cannot supply the item for the period/query: `UNAVAILABLE`;
- evidence exists but awaits confirmation: `PROVISIONAL`;
- identities conflict or lack durable keys: `IDENTITY_UNRESOLVED`;
- sources or uses lack permission: `SOURCE_UNADMITTED` or `USE_BLOCKED`;
- evidence is insufficient to classify: `NOT_ENOUGH_INFORMATION`;
- conflicting values: `DUPLICATE_CONFLICTING`.

Missing never means undrafted, zero, miss, healthy, no-role, or safe. Unavailable never means blocked. Right-censored never means miss. Not applicable never means false.

### 7. What remains immutable?

- the prospective 2026 freeze and its hashes;
- all existing evidence files during every migration phase;
- human decision receipts and source receipts;
- source identifiers, acquisition timestamps, hashes, original paths/locator IDs, row grain, lifecycle stage, and original observed values;
- closed review decisions and supersession history;
- legacy/no-recreate artifacts, even when superseded or duplicated.

### 8. What may be consolidated later?

Only metadata and authority views may be consolidated first. Player values may be registered later only after:

- stable canonical IDs and audited aliases exist;
- primary/foreign keys are unique;
- source/use/rights decisions are explicit at dataset and field level;
- raw/normalized hashes and transformations are recorded;
- duplicate and conflict groups have human dispositions;
- parity proves the workspace preserves every source row and state;
- rollback restores the prior read-only view without touching original artifacts.

### 9. What requires human review?

- current duplicate-inflated identity chains and three no-ID approvals;
- 54 historical drafted/likely-UDFA name groups, including true same-name conflicts;
- likely versus confirmed-review-only UDFA semantics;
- seven current draft-round conflicts;
- source receipts and rights for CFBD, provider exports, prospect grades, third-party combine, and restricted matrices;
- Outcome V2 versus Historical Fantasy Finish scoring differences;
- Formula Data Mart versus Historical Model Lab target differences;
- position-threshold applicability and label-link versus value-availability semantics;
- stale/superseded artifacts and missing entry-status lineage;
- any requested source promotion, model/training use, production scoring, UI integration, or redistribution.

### 10. What implementation sequence is safe?

The safe order is:

1. freeze the inventory;
2. classify authority;
3. reconcile identity assertions without rewriting evidence;
4. create schemas and validators;
5. build a metadata-only read-only workspace;
6. review duplicates and supersession;
7. instantiate typed queues;
8. run parity, lineage, rights, and rollback validation;
9. optionally design product surfaces in a separate lane;
10. make separate source/production-admission decisions.

## Proposed canonical architecture

The future workspace is a registry and evidence-index layer, not a new scoring table. Its core objects are:

- immutable `player_registry` plus append-only aliases and identity assertions;
- source, dataset, receipt, artifact, and field-use registries;
- five lifecycle-specific observation families;
- a strict separation between non-player artifact scope and the exact five-value lifecycle on each player evidence observation;
- field-level lineage records;
- closed evidence/orthogonal/queue/assertion/duplicate enums and normalized nine-purpose source-use decisions;
- conflicts, missing evidence, manual review, source-admission, and supersession ledgers;
- archive manifests, no-recreate index, implementation status, and validation manifests.

Original artifacts remain in place. The workspace initially stores paths or permitted restricted locator IDs, hashes, schemas, row counts, authority states, and relationships. It does not copy raw player evidence.

## Key identity blockers

- no repository-wide canonical NWR player ID spans current Sleeper/CFBD and historical GSIS populations;
- mixed ID namespaces occur under the same field names;
- `157` current rows collapse to `107` distinct records;
- three distinct current approvals have no candidate ID;
- five historical bridge rows lack GSIS;
- `102` positive draft rows lack player IDs;
- `31,614` CFBD rows remain unmatched;
- name/name+position joins appear in review pipelines and the off-HQ simulation;
- the historical entry artifact has unresolved drafted/likely overlaps and missing builder lineage.

## Source, use, privacy, and rights blockers

- CFBD production/model/training/source-truth use remains blocked;
- no admitted historical UDFA confirmation source exists;
- prospect grades and unclear-license datasets remain blocked;
- RotoWire and other licensed/user exports remain local-only and non-redistributable absent a permitted-use decision;
- raw CFBD and shared local artifacts lack portions of the required canonical receipt chain;
- substantial provider content and private/local receipt paths must not enter HQ;
- current market/ADP cannot be used historically;
- plugin outputs remain manual-only with unknown persistent-use rights;
- two historical outcome systems and two target-label systems conflict materially.

## Duplication and conflict result

The register contains `30` groups, including `6` explicit exact-duplicate groups and `9` conflicting-evidence groups. Important counts are:

- `20` tracked rookie CSVs with `903` exact duplicate row groups/excess occurrences;
- `19` current-chain tracked/local artifacts with the recurring 157/107 pattern;
- `9` exact cross-file SHA groups affecting `18` files;
- `7` distinct draft-round conflicts;
- `54` historical drafted/likely-UDFA name groups;
- `2` large scoring/target-system conflict families;
- `930` position-inapplicable threshold mismatches that must not be interpreted as outcome disagreement.

No duplicate is approved for deletion.

## Immediate implementation lane

The immediate lane is `Rookie Evidence Registry Read-Only Scaffold V1`.

It should create only schemas, validators, a metadata artifact registry, a source/use decision registry, and sanitized locator records for a bounded set of already admitted or review-authorized local artifacts. It must not ingest player-value rows, resolve identities, deduplicate data, migrate evidence, activate formulas, or wire a product surface.

The bounded pilot set is:

- source/receipt standards;
- positive drafted admission manifest metadata;
- historical GSIS bridge metadata and hash;
- historical rookie label metadata and hash;
- current human decision receipt metadata;
- current V5 metadata with duplicate caveat;
- conflict and no-recreate registers from this design packet.

## Later lanes

Up to three later lanes are recommended:

1. `Rookie Identity Assertion Registry and Human Review Queue V1`;
2. `Lifecycle-Specific Read-Only Evidence Index V1`;
3. `Duplicate, Conflict, and Supersession Parity Review V1`.

Separate production/source admission decisions follow only after those lanes and are not implied.

## Parked work

- production rookie scoring;
- CFBD production/model/training use;
- inferred or automatically confirmed UDFA truth;
- unadmitted source integration and raw provider copying;
- formula tuning, sparse-history activation, overlays, and ranking simulations;
- frozen-comparator use in ranking, sorting, recommendations, trade, or draft logic;
- hidden recommendation logic or automated Trading Lab valuation;
- current-only market/ADP as historical evidence;
- product UI implementation before read-only parity and authority review.

## Rollback readiness

This design is fully reversible because it creates only a new documentation packet. The future scaffold is also required to be additive and read-only: deleting that new scaffold must restore the prior state without moving or altering any source artifact. Every migration phase stops on an out-of-scope path, hash mismatch, duplicate-key ambiguity, rights uncertainty, source/use escalation, identity conflict, lifecycle leakage, frozen-path change, or parity loss.

## Final assurance

No production behavior or evidence migration occurred. Existing rookie evidence remains byte-for-byte in its original locations, subject to its existing local, rights, and review boundaries.
