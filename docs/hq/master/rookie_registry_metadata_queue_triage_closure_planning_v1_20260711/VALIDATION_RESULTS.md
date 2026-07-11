# Validation Results

Result: `PASS_YELLOW_PROOF_PREPARATION_REQUIRED`.

## Repository and controlling-state gates

- Remote fetch: PASS.
- Live `origin/work/hq-parallel-control`: `774ebe881ffbaa7774119243b22292cd477ca62d` — PASS.
- Remote advance from expected head: 0 commits — PASS.
- New isolated worktree and branch from exact live HQ: PASS.
- Mapping contract, queue contract, and queue canonical Git-blob SHA-256 values: 3/3 PASS.

## Queue gates

- CSV parse and exact data rows: 5,147 — PASS.
- Unique queue IDs and history references: 5,147 each — PASS.
- Categories: 1,156 / 1,269 / 1,269 / 1,269 / 162 / 3 / 19 — PASS.
- Priorities: P1 2,428; P2 2,538; P3 181 — PASS.
- Statuses: BLOCKED 2,428; NOT_ENOUGH_INFORMATION 2,700; DEFERRED 19 — PASS.
- Closed, automatically closed, and nonblank closure receipts: 0 / 0 / 0 — PASS.
- Fail-closed source/use implication: 5,147/5,147 — PASS.
- Canonical queue mutation: 0 paths and 0 bytes — PASS.

## Triage and proof gates

- Coarse proof families: 19 — PASS.
- Execution-safe proof patterns and proposed batches: 69 / 69 — PASS.
- Batch row-count reconciliation: 5,147 — PASS.
- Duplicate batch IDs, proof-pattern IDs, or queue-to-batch assignments: 0 — PASS.
- Complete existing exact proof for queued closure: 0 rows — PASS.
- Proof-state partition: exact 0; partial 3; proof not found 4,224; restricted/local-only 825; off-HQ 95; conflicting explicit proof 0 — PASS.
- Derived primary-status reconciliation: 23 + 795 + 12 + 3 + 95 + 970 + 2,166 + 1,083 = 5,147 — PASS.
- First lane: `batch_836e8658fea7760a7278dd66`, 2 rows, proof preparation only — PASS.
- Closure-proof matrix: all seven present queue categories covered — PASS.

## Boundary gates

- Active artifact-to-authority links: 113 unchanged — PASS.
- Other active relationship types: 0 — PASS.
- Deferred candidates: 28 unchanged and inactive — PASS.
- Explicit source/use decisions: 0 — PASS.
- Source promotions, rights expansions, identity resolutions, off-HQ activations: 0 — PASS.
- Player, alias, identity-assertion, evidence-observation, and player-value rows added: 0 — PASS.
- Raw restricted locators, reversible local/private paths, player names, and player facts in derived outputs: 0 — PASS.
- App/runtime/UI/ranking/formula/recommendation/production/plugin/draft/frozen-artifact changes: 0 — PASS.

## Artifact gates

- Required deliverables: 19/19 nonempty — PASS.
- CSV files parse through an RFC 4180 parser and the bundled spreadsheet artifact parser — PASS.
- JSON manifest parse and listed-file hash/size verification: PASS.
- Protected-path and frozen-artifact scans: PASS.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS.
- Local commit only; push not performed: PASS.
- Clean worktree after local commit: required final gate.
