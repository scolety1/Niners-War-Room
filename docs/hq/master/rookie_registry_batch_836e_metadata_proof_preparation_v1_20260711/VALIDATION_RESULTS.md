# Validation Results

## Controlling-state and packet checks

- Required remote fetch and live-HQ resolution: PASS.
- Live HQ equals expected `b6d16e64d4c182f4a9a5cce558a4b389d0d48bc1`: PASS; remote advance is zero commits.
- All eight controlling manifests parse and all 123 listed normalized hashes and byte counts match: PASS; zero mismatches.
- Mapping contract, queue contract, and canonical queue normalized hashes: PASS.
- The canonicalized source commit `bcace1428dde51b6a308b31a0be2d4c90c067610` exists as a side-branch commit; its full source packet tree is byte-equivalent to the adopted HQ tree: PASS.
- Isolated worktree and branch from verified live HQ: PASS.

## Batch and evidence checks

- Exact batch reconciliation: PASS; two rows and two unique target queue IDs.
- Queue existence and uniqueness: PASS; each target occurs exactly once in the 5,147-row canonical queue.
- Queue state: PASS; both remain `BLOCKED`, open, and closure-ineligible.
- Exact proof-element matrix: PASS; 12 unique required elements per target row.
- Exact evidence ledger: PASS; 12 unique ledger entries and all cited canonical hashes reconcile.
- Canonical source registry and artifact-source mapping registry: PASS; both have zero data rows.
- Source-use decision, player identity, alias, identity-assertion, and evidence-observation registries: PASS; zero data rows.
- Optional `PROPOSED_ENDPOINT_RECORD_REVIEW.csv`: PASS; intentionally absent because proof is incomplete.
- Reversible local-path and inference-term scan of this packet: PASS; zero matches.
- No raw, local-only, restricted, or off-HQ content copied or activated: PASS.

## Artifact validation

- CSV parsing: PASS; six CSV files parsed with 2, 12, 15, 8, 24, and 2 data rows respectively.
- Duplicate keys: PASS for queue IDs, ledger entry IDs, matrix `(queue_id, element_number)` keys, gap IDs, and closure decision queue IDs.
- Registry validator: PASS; 146 checks, 0 issues, 1,269 artifacts, 23 authorities, 0 explicit decisions, 0 real player rows, and 0 real evidence-observation rows.
- Focused tests: 68 assertions across the scaffold, linkage-gap, and metadata-queue suites reached 100% three times. The bundled Python process then hung during pytest teardown and never produced an exit code, including with plugin autoload disabled; the stuck processes started by this lane were stopped. Result: `PASS_ASSERTIONS_WITH_ENVIRONMENT_TEARDOWN_CAVEAT`.
- Manifest JSON parse, file count, 14 listed normalized byte counts and SHA-256 values, and intentional optional-file absence: PASS with zero mismatches.
- Protected-path and app/ranking/formula/source-registry/plugin-governance staged diff scan: PASS; all 15 staged files are inside the sole allowed packet prefix and zero prohibited paths changed.
- Canonical queue, mapping contract, queue contract, and rookie registry byte-change scan: PASS; zero changes.
- `git diff --check` and `git diff --cached --check`: PASS after final-scope staging.
- Clean worktree after local commit: final closeout check; it cannot be established before the commit exists.
