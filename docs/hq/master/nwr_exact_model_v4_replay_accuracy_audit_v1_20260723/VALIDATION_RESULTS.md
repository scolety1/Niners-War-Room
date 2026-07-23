# Validation results

Status: `PASS_WITH_EXPECTED_LOCALDATA_BLOCK`.

## Research tooling

- Focused replay, receipt-schema, deterministic-regeneration, temporal-leakage,
  identity, exactness-mask, metric-reproduction, walk-forward, candidate-gate,
  current-board no-change, and manifest tests: 8 passed.
- Deterministic clean rerun: packet aggregate hash identical before/after.
- Python compilation of `scripts`, `src`, and `tests`: pass.
- Changed-file Ruff: pass.
- No-new-Ruff differential: exact starting checkout and candidate each report
  the same 4,443 pre-existing findings under identical rules.
- Changed PowerShell parsing: not applicable; zero PowerShell files changed.

## Repository gates

- Hermetic bootstrap controls: 13 passed, 0 failed.
- Security automation controls: 20 passed, 0 failed.
- Hermetic Python collection: 2,774 passed with strict no-skip enforcement.
- Hermetic owned Ruff: pass.
- Final Hermetic verdict: `HERMETIC_TIER_PASS`, exit 0.
- LocalData: exact `BLOCKED_MISSING_LOCAL_TEST_PACK`, native exit 4. The pack was
  not synthesized, copied, imported, or bypassed.
- Existing five-finding, CSV-formula security, trust-classification, Data Health
  passive-read/page-open, launcher ownership, route, ranking, compare, trading,
  draft, and persistence regressions passed inside Hermetic.
- No security scan was run.
- Dedicated launcher execution was not necessary because launcher code and
  runtime integration were unchanged; its existing tests passed in Hermetic.
- No skip, xfail, or xpass was added.

## Windows path note

An initial non-authoritative run from the long workspace path reported one
`FileNotFoundError` for a tracked rookie-outcomes fixture after 2,773 passes.
The exact blob was present in Git and the stable checkout at SHA-256
`99b8727871b5d902df8eee59f55eee76eddb942734800170129050ae0c3acad2`.
Windows path-length access, not repository content, caused the failure. The same
unchanged isolated worktree was temporarily moved to a short path and the full
authoritative gate passed 2,774 tests. No fixture or test was restored, copied,
or changed.

## Integrity and preservation

- Canonical tracked and stable-runtime board: 240 rows, SHA-256
  `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`;
  ordered top five unchanged.
- Frozen 2026 comparator SHA-256:
  `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179`.
- Production ranking change: `NONE`; frozen 2026 change: `NONE`.
- Five opaque primary CSV hashes: exact at lane start, after receipt recovery,
  after historical evaluation, before and after the tooling commit, and before
  the audit commit.
- Persistent product state: exact 14 files / 542,801 bytes; Digest V1
  `88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`.
- Recovery quarantine: exact 7 files / 172,878 bytes; Digest V1
  `1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.
- Production, formula, identity, UI/route, Data Health, security, and frozen
  paths: unchanged.
- `git diff --check`: pass.
- `git diff --cached --check`: pass before each commit.
- Push: not performed.
