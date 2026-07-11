# Next Lane Ready-to-Paste Prompt

## NWR Master ChatGPT Work Request

### Rookie Evidence Registry Read-Only Scaffold V1

This is a documentation/data-architecture implementation lane. Build only a reversible, metadata-only Rookie Evidence Registry scaffold from the canonicalized Rookie Evidence Workspace Consolidation Design V1.

Do not implement product behavior. Do not change rankings, formulas, production data, source admission, app behavior, draft behavior, recommendations, hidden logic, or frozen 2026 artifacts. Do not move, delete, rename, rewrite, deduplicate, consolidate, or copy existing rookie evidence. Commit locally only. Do not push.

Before work:

1. Fetch all remotes.
2. Resolve live `origin/work/hq-parallel-control`.
3. Inspect every intervening commit if it advanced.
4. Stop on any conflict with rookie evidence, identity/source governance, product behavior, formula pause, plugin manual-only policy, or frozen artifacts.
5. Create a new isolated worktree and branch from verified live HQ.
6. Do not disturb existing worktrees.

Controlling design inputs:

- `docs/hq/master/rookie_evidence_workspace_consolidation_design_v1_20260711/ROOKIE_EVIDENCE_WORKSPACE_CONSOLIDATION_DESIGN_V1_REPORT.md`
- `CANONICAL_INFORMATION_ARCHITECTURE.md`
- `CANONICAL_SCHEMA_AND_KEY_CONTRACT.md`
- `EVIDENCE_STATE_AND_LIFECYCLE_CONTRACT.md`
- `IDENTITY_AND_LINEAGE_CONTRACT.md`
- `SOURCE_ADMISSION_RIGHTS_AND_PRIVACY_BOUNDARY.md`
- `MANUAL_REVIEW_QUEUE_DESIGN.md`
- `MIGRATION_AND_SUPERSESSION_PLAN.md`
- `IMMEDIATE_NEXT_LANE_CONTRACT.md`
- the inventory, authority, duplicate/conflict, and no-recreate CSVs in the same packet.

Objective:

Create one new, separately versioned workspace-scaffold packet containing only schemas, metadata registries, validation, status, and manifests. Populate only a bounded artifact/source/use/receipt/relationship/no-recreate pilot. Keep all player/alias/evidence observation tables empty except schema headers; no player values may enter the scaffold.

The bounded pilot includes metadata for:

- source registry and HQ1 receipt standard;
- the controlling design packet;
- positive drafted admission manifest;
- historical GSIS bridge tracked packet and permitted sanitized local hash/locator metadata;
- historical rookie label tracked packet and permitted sanitized local hash/locator metadata;
- historical entry-status metadata and failed-lineage state;
- current CFBD human decision metadata with the 157/107 duplicate caveat;
- current V5 metadata with the 157/107 duplicate caveat;
- draft-capital sidecar metadata;
- Outcome V2 compact source metadata;
- protected/no-recreate/frozen dependencies;
- sanitized restricted/off-HQ locator metadata.

Required architecture:

- versioned player, alias, identity assertion, source, dataset, use decision, receipt, artifact, field, lineage, lifecycle, conflict, duplicate, missing, manual-review, source-admission, supersession, archive, restricted-locator, no-recreate, implementation-status, and manifest schemas;
- opaque NWR IDs; provider IDs are aliases;
- no sentinel or name-based primary key;
- separate pre-draft, draft-event, post-draft/preseason, rookie-season, and multi-year outcome schemas;
- non-player artifact scope stored separately from exact five-value player-evidence lifecycle links;
- closed enums for the 14 evidence states and every orthogonal, queue, assertion, duplicate-class, duplicate-disposition, locality, availability, and censoring state;
- normalized source-use rows for all nine purposes at dataset + field + purpose grain; prose may not create a decision;
- lossless full field lineage and duplicate relationships carrying proof, scope, authority, disposition, decision/closure receipts, validation, and rollback;
- append-only decisions and supersession;
- sanitized restricted locators;
- fail-closed source/use/rights precedence.

Explicit exclusions:

- no player-value rows;
- no identity resolution or queue resolution;
- no deduplication or conflict authority decision;
- no raw/local/provider/private data copy;
- no CFBD or prospect production use;
- no verified-UDFA inference;
- no formula/model/training/ranking work;
- no product UI, services, tests, or app imports;
- no plugin calls or research;
- no source-registry changes;
- no frozen-comparator use.

Validate:

- live HQ and isolated worktree;
- all writes confined to the new scaffold packet;
- parse, schema, unique-key, FK, enum, state-precedence, and sentinel checks;
- cross-file enum/schema parity and rejection of undeclared states or free-text source decisions;
- no name-only controlling joins;
- locator sanitization and privacy/rights checks;
- source artifact hash/schema/row-count parity;
- zero player-value rows copied;
- duplicate/conflict/no-recreate parity;
- protected, frozen, ranking, formula, app, production-data, source-registry, and plugin-governance no-change scans;
- deterministic manifest;
- rollback rehearsal;
- `git diff --check`, `git diff --cached --check`, local commit, and clean worktree.

Stop if any existing artifact must change or if the work requires identity resolution, source promotion, player-data ingestion, product behavior, formula work, or a rights assumption.

Return a local commit to Master HQ for review. Do not push or execute any later lane.
