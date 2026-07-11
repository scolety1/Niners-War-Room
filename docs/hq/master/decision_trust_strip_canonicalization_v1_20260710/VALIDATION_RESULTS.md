# Validation Results

## Repository and source

- Live HQ: `3f41919c506175293465b134f1495c042f710168`; no advance.
- Source parent: exactly live HQ.
- Canonicalization: exact `--ff-only` preservation to `c0e1defc299ad5fbb9c25b7878851156d5da3776`.
- Source inventory: 24 paths, all classified and in scope.
- Source manifest: PASS, 14 hashed documentation artifacts.

## Tests

- Affected focused/regression/navigation command: PASS — 125 passed in 2.08 seconds.
- Representative Streamlit AppTest: included and PASS.
- Route/navigation smoke: included and PASS.
- Clean-HQ trust-banner baseline: 2 failed / 3 passed.
- Source trust-banner baseline: 2 failed / 3 passed.
- Baseline signatures: identical; unchanged thin wrapper; no new failure.

## Static and semantic validation

- Python compilation: PASS — five affected implementation/page files.
- Ruff on all affected implementation/page/test/fixture files: PASS.
- Passive-adapter review: PASS.
- Eight-state semantic consistency: PASS.
- Canonical field order and labels: PASS.
- Accessibility and representative visual review: PASS with minor multi-entity density caveat.

## Documentation and CSV

- Required canonicalization files: PASS — all nine, non-empty.
- Source and adoption CSV parsing: PASS.
- Duplicate-key checks: PASS.
- Internal paths: PASS.
- Bundled artifact-tool CSV import/inspection: PASS.

## Safety gates

- Frozen packet byte change: none.
- Protected/source-registry/ranking/formula/outcome diff: none.
- Sorting/filter/recommendation/eligibility changes: none.
- Trading Lab manual behavior: preserved.
- `git diff --check`: PASS.
- `git diff --cached --check`: rerun after staging adoption packet.

Final remote-advance, push, and clean-worktree checks occur after the adoption commit.
