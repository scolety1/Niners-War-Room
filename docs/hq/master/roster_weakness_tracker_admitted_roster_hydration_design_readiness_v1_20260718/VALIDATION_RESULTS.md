# Validation Results

Status: PASS for the documentation packet and pre-commit repository checks. The local commit and clean post-commit status are verified at handoff because they necessarily occur after this committed artifact is frozen.

## Repository and control-plane checks

- Live HQ `adc058512b389657830e86ad1abd4b85bebd7eea` and tree `00f6e7035fd81ad9341dd5605eb251ae375b785a` matched the expected values after fetch and prune.
- There were zero intervening commits and zero remote-advance paths to review.
- The isolated worktree and branch were created from live HQ; the primary worktree was not used for writes.
- Staged scope contained exactly 23 files and zero paths outside this packet.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS after documentation formatting normalization.

## Source, identity, roster, and route checks

- Source registry: 36 rows; zero duplicate source/table keys; source firewall issues: zero.
- Sleeper players, rosters, and drafts/traded picks are registered as `ADMITTED_FACT`.
- Synthetic roster: 24 rows; 24 unique player IDs; zero duplicates; zero missing sample dim-player joins.
- Synthetic dim players: 24 rows; zero duplicate player IDs; zero nonblank Sleeper IDs. This is the decisive failure of clean-checkout exact source-to-NWR identity proof.
- Synthetic future picks: 3 rows; zero duplicate source-coordinate tuples.
- The route file exists and navigation registers `roster-weakness-tracker`.
- Current route/service inspection confirmed a manual, framework-only descriptive surface; no hydration was executed.

## Test and LocalData checks

- Focused tests: 63 passed in 2.74 seconds.
- The first two available Python runtimes lacked pytest and ran zero tests; the primary repository virtual environment supplied pytest 9.1.1 for the successful focused run.
- Official LocalData verifier: `BLOCKED_MISSING_LOCAL_TEST_PACK`, exit 4.
- The default approved LocalData pack is absent from the clean worktree. No arbitrary disk fallback, provider call, credential read, or private payload read occurred.

## Packet and integrity checks

- All packet CSV files parsed successfully.
- Duplicate-key checks passed for the source, surface, field, weakness, failure, readiness, and file-inventory matrices.
- `MANIFEST.json` parsed and declared exactly the 23 on-disk packet files.
- Manifest/file hashes were validated for every non-manifest file; the manifest intentionally does not self-hash.
- CSV formula-prefix scan: zero findings.
- Private-style long numeric identifier scan: zero findings.
- Secret-assignment scan: zero findings.

## Preservation checks

- Nine explicit protected Git blobs matched, with zero mismatches.
- Base-HQ frozen/prospective baseline: 137 paths; zero diffs; aggregate SHA-256 `6d42096a0ddf0f270cf5ed4141647ac085fce5ca14c9187af97736eee0455611`.
- The primary worktree still had exactly the five user-owned DynastyProcess CSV modifications. All five preservation hashes matched with zero mismatches.

No provider call, roster hydration, production-data generation, application-source change, schema change, formula change, ranking change, source promotion, push, or merge was performed.
