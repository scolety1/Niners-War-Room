# Validation Results

## State, ancestry, and adoption

- Fetch all remotes and prune: PASS.
- Live HQ resolution: PASS; actual and expected are `b6d16e64d4c182f4a9a5cce558a4b389d0d48bc1`.
- Remote advance: PASS; zero commits and no intervening diff.
- Source ancestry: PASS; `497e5f0b5dd1020b47f53cf862aa63571cd735eb` is the direct child of live HQ.
- Isolated worktrees: PASS; original source worktree remained untouched.
- Source scope inventory: PASS; 15 added files and all are under the sole source-packet prefix.
- Canonicalization method: PASS; fast-forward adoption preserves the source commit and packet unchanged, followed by a separate docs-only closeout commit.

## Contracts, manifests, rows, and effects

- Source manifest JSON parse and 14 listed file entries: PASS; zero normalized byte/hash mismatches.
- Source CSV parsing: PASS; row counts `2`, `12`, `15`, `8`, `24`, and `2` across the six CSVs.
- Mapping contract SHA-256 `19bb737de35f476ad39bff50d41f25e5ec6ef3b88dacd48d23b47917960fa264`: PASS.
- Queue contract SHA-256 `e6c5d46f114afb4edc59b007e3422c0e543e1a3403be6708e93b610d67c30075`: PASS.
- Queue SHA-256 `9ef64f1a3a06dc96a968da37bc53e825de656b0545e177c6d9c899485db6971f`: PASS.
- Evidence SHA-256 `d8baefe7b41fcd8a601f33d6dc9d6c0f2753d4f3e3b5189d25b72cb065a594df`: PASS.
- Exact target reconciliation: PASS; both IDs occur once, remain `BLOCKED`, have blank closure receipts, and receive `PROOF_PARTIAL_MISSING_EXACT_ELEMENT`.
- Canonical queue byte/no-change proof: PASS; baseline and source Git blobs are identical.
- No mapping, endpoint, source/use decision, closure event, deferred activation, identity resolution, source promotion, or rights expansion: PASS; all zero.
- Player/evidence rows: PASS; zero real player rows and zero real evidence-observation rows.
- Missing-proof classification: PASS; exact packet evidence and every missing canonical endpoint element are classified without inference.
- Pause and reentry gate: PASS; explicit, fail-closed, and non-mutating.
- No-recreate index: PASS; four prohibited repeat patterns require a new canonical metadata trigger.

## Executable validation

- Registry validator on clean HQ: PASS; `146 checks / 0 issues`, 1,269 artifacts, 23 authorities, 0 explicit decisions, 0 real player rows, and 0 real evidence-observation rows.
- Registry validator on source: PASS; identical result.
- Queue validator on clean HQ and source: PASS; 5,147 rows, 0 issues, 0 automatic closures, and 0 player-level rows on both.
- Focused pytest baseline: PASS; 68 passed in 1.82s, teardown completed, exit 0.
- Focused pytest source: PASS; 68 passed in 1.70s, teardown completed, exit 0.
- Pytest differential: PASS; identical normal behavior, 120-second timeout not reached, no source-specific regression.
- No test modified, skipped, weakened, or marked xfail: PASS; source diff is docs-only.
- Privacy/rights/locator scan: PASS; fail-closed with no sensitive locator or rights expansion.
- Protected/frozen/app/ranking/formula/source-registry/plugin-governance diff scans: PASS; zero prohibited paths.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS after staging.
- Final source-manifest and closeout-manifest validation: PASS; zero mismatches.
- Clean worktree after commit and push: required final Git check; reported with the final handoff because a commit cannot contain its own hash.
