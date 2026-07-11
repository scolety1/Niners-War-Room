# Migration and Supersession Plan

## Migration rule

Migration is additive registration, not relocation. Original evidence remains available until field, row, authority, rights, and hash parity all pass. No destructive migration is authorized.

## Phase 1 — Inventory freeze

- Inputs: this packet, live-HQ artifact paths, permitted local locators, Git commits, hashes, manifests.
- Outputs: versioned immutable artifact inventory and baseline manifest.
- Allowed paths: new future workspace packet only.
- Blockers: unverified live HQ, missing artifact, restricted path exposure, hash mismatch.
- Rollback: remove the new inventory snapshot.
- Validation: artifact count, path existence/locator status, CSV parse, hashes, protected/frozen diff.
- Stop conditions: any source file write, move, rename, deletion, or out-of-scope path.

## Phase 2 — Authority classification

- Inputs: frozen inventory, source/use decisions, no-recreate controls, human decision receipts.
- Outputs: artifact- and family-level authority ledger with decision precedence.
- Allowed paths: registry metadata only.
- Blockers: conflicting source/use authority without explicit fail-closed state.
- Rollback: discard the new authority snapshot; source artifacts unchanged.
- Validation: every artifact has one current primary state and all orthogonal gates; no review-to-production promotion.
- Stop conditions: registry/source admission change, implicit precedence, or authority assigned from filename recency alone.

## Phase 3 — Identity reconciliation

- Inputs: provider aliases, GSIS bridge, Sleeper/CFBD review assertions, collision audits.
- Outputs: opaque NWR IDs, alias assertions, conflicts, and manual-review queue references.
- Allowed paths: append-only identity registry; unresolved evidence may retain null NWR ID.
- Blockers: duplicate provider ID, mixed namespace, name-only join, missing proof, conflicting provider records.
- Rollback: remove the new identity snapshot; original assertions remain.
- Validation: unique active aliases, no sentinel IDs, join-method allowlist, collision/unmatched counts.
- Stop conditions: automatic name-based binding, silent deduplication, or source values rewritten.

## Phase 4 — Canonical schema creation

- Inputs: approved schema/key/state/lifecycle contracts.
- Outputs: empty versioned schemas, dictionaries, validators, manifests.
- Allowed paths: new workspace scaffold only.
- Blockers: ambiguous grain, missing FK, missing lifecycle or rights field, incompatible enum semantics.
- Rollback: delete the unpopulated scaffold.
- Validation: schema fixtures, enum checks, PK/FK tests, state transitions, restricted-locator handling.
- Stop conditions: schema flattens lifecycle stages or permits name-only keys/missing-as-zero.

## Phase 5 — Read-only workspace build

- Inputs: inventory/authority metadata and a bounded approved pilot set.
- Outputs: artifact, source/use, receipt, no-recreate, conflict, and implementation-status registries.
- Allowed paths: new workspace; metadata and sanitized locators only in the immediate lane.
- Blockers: raw player data needed, rights unknown, hash absent where required, scope expansion.
- Rollback: delete the read-only workspace.
- Validation: source artifact parity, hashes, no writes to evidence, no product imports, deterministic rebuild.
- Stop conditions: player values copied without authorization, source promotion, formula/app dependency, or production wiring.

## Phase 6 — Duplicate and supersession review

- Inputs: duplicate register, file/row hashes, schema/population parity, human decisions.
- Outputs: duplicate relationships and explicit predecessor/successor chains.
- Allowed paths: append-only relationship ledgers.
- Blockers: conflicting evidence, non-unique keys, incomplete parity, missing rights.
- Rollback: remove relationship snapshot; no source deletion.
- Validation: each relationship has class, proof, scope, authority, and rollback.
- Stop conditions: automatic merge/delete, newest-file-wins, or conflicting values collapsed.

## Phase 7 — Manual-review queue creation

- Inputs: unresolved identities, status conflicts, rights gaps, lineage failures, missing coverage.
- Outputs: typed queue items with evidence links and proof requirements.
- Allowed paths: append-only queue registry; no resolutions in the creation lane.
- Blockers: unstable entry keys, private evidence exposure, unbounded fan-out without batching contract.
- Rollback: delete queue snapshot if no decisions have been recorded.
- Validation: unique review IDs, valid evidence links, allowed statuses, closure requirements.
- Stop conditions: item auto-closed, name-only identity set, or missing proof omitted.

## Phase 8 — Validation and parity checks

- Inputs: read-only workspace and all registered originals.
- Outputs: field/row/artifact/authority/rights/lineage parity report and rollback rehearsal.
- Allowed paths: validation artifacts only.
- Blockers: any count/hash/value/state/lineage loss or restricted-content leak.
- Rollback: revert/remove the workspace snapshot.
- Validation: exact and semantic parity, duplicate preservation, conflict preservation, stage boundaries, use gates, source rights, frozen paths.
- Stop conditions: unexplained mismatch or evidence unavailable to rollback.

## Phase 9 — Optional product-surface design

- Inputs: validated read-only workspace and separate product authorization.
- Outputs: design only for evidence/status visibility.
- Allowed paths: separately approved docs/UI design lane.
- Blockers: unresolved identity/source/rights/latency/accessibility issues.
- Rollback: remove optional design/feature; workspace remains independent.
- Validation: no scoring, sorting, recommendations, draft behavior, or hidden influence.
- Stop conditions: UI is proposed before read-only parity or changes authority semantics.

## Phase 10 — Separate production-admission decisions

- Inputs: validated evidence, explicit source/rights/use proposals, production risk assessment.
- Outputs: independent decision packets; possibly no admission.
- Allowed paths: separately authorized source/model/product lane.
- Blockers: any unresolved source, rights, identity, leakage, missingness, outcome, or frozen-comparator issue.
- Rollback: purpose-specific feature flag/data contract and prior production baseline.
- Validation: full production test plan, monitoring, governance, and approval.
- Stop conditions: design/scaffold treated as admission or formula/product behavior altered without authorization.

## Supersession contract

A successor may supersede a predecessor only when:

- scopes match explicitly;
- source and identity authority are equal or stronger for the same purpose;
- schema and population differences are documented;
- conflicting values are resolved or remain separately blocked;
- row/field/authority parity passes;
- hashes and manifests are preserved;
- rollback can restore the predecessor view;
- a human decision receipt authorizes logical supersession.

Supersession never deletes or rewrites the predecessor. Partial supersession is field- and purpose-specific.

## Known supersession candidates, not decisions

- Gate F V5 may be the current review-display successor to V1-V4, but duplicate and key caveats remain.
- Draft-capital repair V2 is later review evidence than V1 for seven conflicting rounds, but stable identity/source proof is still required.
- Historical label builder V1 supersedes the earlier Gate C blocker only for the 2012-2024 drafted-player review-label scope.
- Later current depth-chart receipts supersede a prior zero-current-coverage statement, not the historical-model coverage conclusion.
- Outcome V2 2012-2024 supersedes older 2019-2024 sources for its tracked review scope; the 2000 probe is not automatically admitted.

## Rollback readiness

Every phase is a new directory/snapshot with no source mutation. Rollback removes or deactivates the newest registry snapshot and restores the prior manifest/view. If rollback requires recreating evidence, the phase was not safe and must not proceed.
