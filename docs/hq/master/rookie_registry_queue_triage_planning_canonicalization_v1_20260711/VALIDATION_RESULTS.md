# Validation Results

Result: `PASS_GREEN_CANONICALIZATION_GATE`.

- Remote fetch and direct live-head readback: PASS at `774ebe881ffbaa7774119243b22292cd477ca62d`; advance 0.
- Source ancestry: PASS; live HQ is the direct parent and merge base of `bcace1428dde51b6a308b31a0be2d4c90c067610`.
- Source inventory: 19 added files, all inside the declared source packet; no prohibited path.
- Source manifest: 18 listed files plus self-excluded manifest; normalized size/hash issues 0.
- Source CSVs: 6/6 parse through RFC 4180-compatible and bundled spreadsheet parsing; duplicate primary keys 0.
- Mapping contract / queue contract / queue file hashes: 3/3 exact PASS.
- Canonical queue: 5,147 rows, 5,147 unique queue IDs, 5,147 unique history references, 0 closure receipts.
- Canonical categories: 1,156 / 1,269 / 1,269 / 1,269 / 162 / 3 / 19; PASS.
- Canonical priorities: P1 2,428; P2 2,538; P3 181; PASS.
- Canonical statuses: BLOCKED 2,428; NOT_ENOUGH_INFORMATION 2,700; DEFERRED 19; PASS.
- Proof patterns / batches / assigned rows: 69 / 69 / 5,147; grouping issues 0.
- Current exact-proof closable rows: 0; canonical mutation flags true 0; closure-eligible flags true 0.
- Proof partition: exact 0; partial 3; conflicting explicit 0; not found 4,224; restricted/local-only 825; off-HQ 95.
- First batch: `batch_836e8658fea7760a7278dd66`, exactly 2 rows, documentation-only proof preparation; PASS.
- Active artifact-authority links 113; other active relationship types 0; deferred candidates 28 inactive; source/use decisions 0.
- Source registry, source-link registry, player, alias, identity-assertion, evidence-observation, and closure-event rows: 0.
- Registry validator: `146 checks / 0 issues`; PASS.
- Queue validate-only builder: 5,147 rows / 0 issues; PASS.
- Focused tests: `68 passed`. A first run from the long review-worktree path produced two Windows path-length access failures and 66 passes; the identical unmodified suite reran through a short local junction and passed 68/68. No test was weakened or edited.
- Privacy/locator, protected-path, frozen-artifact, runtime/app/ranking/formula/source-registry/plugin-governance, and byte-change scans: PASS with 0 prohibited changes.
- `git diff --check`, `git diff --cached --check`, canonical manifest validation, final remote readback, push, and clean-worktree checks: required final gates and recorded by the canonicalization commit workflow.
