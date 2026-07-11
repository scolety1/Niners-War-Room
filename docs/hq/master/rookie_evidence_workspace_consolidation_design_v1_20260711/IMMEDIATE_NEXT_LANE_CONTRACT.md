# Immediate Next Lane Contract

## Lane name

`Rookie Evidence Registry Read-Only Scaffold V1`

## Objective

Create a small, additive metadata registry and validation scaffold for existing rookie evidence. The lane must make authority, source/use, lifecycle, duplication, conflicts, restricted locators, and no-recreate status queryable without copying player values or changing any existing system.

## Required starting state

- Start from verified live `work/hq-parallel-control` after fetching all remotes.
- Inspect any remote advance and stop on a semantic conflict.
- Use a new isolated worktree and branch.
- Treat this design packet as the controlling design input after Master HQ canonicalization.

## Allowed writes

One new, separately versioned workspace-scaffold packet under a Master-HQ-approved path. No existing file may be edited.

## Required outputs

- workspace overview;
- schema version and field dictionaries;
- empty player/alias/identity assertion schemas;
- populated artifact metadata registry for a bounded pilot set;
- source, dataset, receipt metadata, and source/use decision registries;
- closed evidence-state and orthogonal-state enum registries, plus exact five-stage lifecycle links distinct from artifact scope;
- duplicate/conflict/no-recreate relationship imports;
- restricted locator registry containing sanitized locator IDs only;
- validation rules/results;
- implementation status;
- manifest and changed-file list;
- rollback procedure.

## Bounded pilot set

Metadata only for:

1. `config/source_registry.csv` and HQ1 receipt standard;
2. this design packet;
3. positive drafted admission manifest;
4. historical GSIS bridge tracked packet plus permitted local hash/locator metadata;
5. historical rookie label tracked packet plus permitted local hash/locator metadata;
6. historical entry-status artifact metadata and failed-lineage status;
7. current CFBD human decision receipt metadata with 157/107 duplicate caveat;
8. current V5 metadata with 157/107 duplicate caveat;
9. draft-capital sidecar metadata;
10. Outcome V2 compact source metadata;
11. protected/no-recreate/frozen dependencies;
12. sanitized restricted and off-HQ locator metadata from this packet.

## Explicit exclusions

- no player-value ingestion;
- no canonical NWR player IDs minted in bulk;
- no identity resolution or manual decisions;
- no deduplication or conflict resolution;
- no raw/local/restricted data copy;
- no source admission or registry changes;
- no formula/model/training/ranking work;
- no app/service/test/product changes;
- no draft behavior, recommendation, sorting, or hidden logic;
- no UDFA inference;
- no frozen artifact changes;
- no plugin calls or research.

## Required schemas

Implement the schemas from `CANONICAL_SCHEMA_AND_KEY_CONTRACT.md` at scaffold level. Populated rows are allowed only in artifact/source/use/receipt/relationship/no-recreate/implementation registries. Player aliases and evidence observation tables remain empty with fixtures only in tests or validation examples.

## Required validations

- live-HQ verification;
- all writes within the new scaffold path;
- CSV/JSON parsing;
- unique metadata keys and valid foreign keys;
- enum and state precedence;
- exact cross-contract parity for evidence, orthogonal, queue, assertion, duplicate-class, duplicate-disposition, lifecycle, source-purpose, and source-decision enums;
- nine normalized purpose decisions per populated dataset/field family; no prose-derived admission;
- no literal sentinel in key fields;
- no name-only controlling join;
- local/restricted locator sanitization;
- hash/schema/row-count parity for pilot artifacts;
- no raw player rows in the scaffold;
- no source/use promotion;
- no production/formula/app/ranking/source-registry diff;
- frozen/protected/no-recreate scans;
- manifest validation;
- rollback rehearsal;
- `git diff --check` and clean worktree after local commit.

## Stop conditions

- a pilot artifact requires raw player values to satisfy the lane;
- a rights/private path or substantial provider content would be copied;
- artifact hash/schema/population does not match;
- duplicate/conflict records cannot be represented losslessly;
- a source/use decision is ambiguous and the loader does not fail closed;
- an existing file must be changed;
- identity resolution, formula, production, or product work becomes necessary;
- a frozen/protected path changes.

## Acceptance criteria

- one deterministic rebuild creates the same metadata files and hashes;
- every pilot artifact remains at its original location;
- every authority/use/locality/duplicate/conflict caveat is preserved;
- every duplicate relation carries class, proof, scope, authority, disposition, decision/closure receipt fields, validation, and rollback;
- every lineage schema can retain the complete source, timing, original/typed value, transform, identity, lifecycle/window, state, confidence, supersession, and receipt contract without a lossy join;
- zero player-value rows are copied;
- deleting the scaffold restores the pre-lane repository behavior and data view;
- Master HQ can review the packet without executing product code.

## Commit policy

Commit locally only. Do not push, merge, or execute a later lane.
