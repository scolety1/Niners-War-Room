# Independent Adoption and Canonicalization

## Decision

`YELLOW_NWR_RECEIPT_RECOVERY_EXHAUSTED_WITH_ACTIONABLE_HUMAN_LEADS`

The workday accuracy evidence-expansion lane is admissible for documentation-only
canonicalization. No historical Model v4 checkpoint, final-score, or exact-rank
receipt was promoted. Exact replay remains zero rows, proxy-to-exact comparison
remains `PROXY_TO_EXACT_NOT_TESTABLE`, and the final challenger disposition
remains `NO_ACCURACY_CHALLENGER_ADMITTED`.

Production ranking change: `NONE`.

Frozen 2026 change: `NONE`.

## Adopted lineage

- Starting HQ: `4e8fc06900024aa00a67689f99fc734c6d513254`
- Starting tree: `0840bdda644299e6630933f85bb9a4c38c6ae5ed`
- Adopted tooling commit: `290654eec0b4edf71de833ae63aa87b1404b0efe`
- Tooling tree: `ef5a098799a5a580d05e1a42786b392f6c570f1e`
- Adopted evidence commit: `cdf18bbf4d4d6e29525e587405de1ff2ac077fec`
- Evidence tree: `3b0b18bb7f582f12d7718373ed89ad9c27bd5bb3`

Both source changes were independently adopted in
`C:\NWR\Niners-War-Room-workday-accuracy-evidence-expansion-adoption-v1-20260723`.
The final evidence tree was then checked out independently and detached at
`C:\NWR\Niners-War-Room-workday-accuracy-evidence-expansion-clean-review-v3-20260723`.

## Bounded correction

Independent adoption found one bounded deterministic-serialization defect:
Windows checkout normalization made packet manifest hashes depend on worktree
line endings, and one tracked comparator path embedded the originating worktree
root. The correction:

1. extends the repository's existing LF policy only to this packet, builder,
   and focused test;
2. emits the tracked frozen comparator as a repository-relative path;
3. serializes every generated CSV with explicit LF line endings; and
4. adds focused cross-worktree path and LF serialization regression assertions.

No formula, ranking, outcome, identity, source-admission, lifecycle, confidence,
discipline, safety, checkpoint, comparator, or application behavior changed.

## Independent regeneration

The final detached checkout passed packet validation before regeneration.
Regeneration completed, validation passed again, and Git reported a zero diff
and clean status. `MANIFEST.json` SHA-256 was identical before and after:

`4953a98b9bc51722c17b908c646ac560edf7da54bdfb0f36d36f26074e19c730`

## Independent gates

- Focused recovery/authentication/exactness/mutation suite: 23 passed.
- All 14 required mutations were detected.
- Changed-file Ruff: passed.
- Existing security regression automation: 20/20 passed; no security scan ran.
- Passive-read Data Health slice: 59/59 passed.
- LocalData: `BLOCKED_MISSING_LOCAL_TEST_PACK`; native exit 4.
- Hermetic: `HERMETIC_TIER_PASS`; 2,821 passed in 606.57 seconds; native exit 0.
- Clean-checkout regeneration: passed with byte-identical manifest and zero diff.
- Current board and frozen comparator: unchanged.
- Opaque primary files, persistent state, and recovery state: unchanged.

## Evidence review

The repository and NWR-provenance search exhausted its deterministic surfaces
without authenticating a complete historical current-Model-v4 chain. The
recovered `HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1` definition and its
review-only deterministic panel remain correctly separated from exact Model v4
receipt evidence. The candidate is not admitted because exact Model v4 overlap
is zero and its low-games stability gate fails.

The human/external retrieval package remains the controlling route for original
checkpoint, final-score, exact-rank, component, lifecycle, confidence, and
discipline/safety receipt families. Proxy values are prohibited substitutes.

## Push and rollback

A normal non-force push to `work/hq-parallel-control` is admissible only after
preservation is rechecked and a final fetch proves the remote has not advanced
incompatibly. Rollback is a normal
revert of the documentation-only canonicalization commit and, if required, the
two adopted commits. Rollback must not touch production data, LocalData,
persistent or recovery state, the five opaque CSVs, retained backups, or the
recovery snapshot.
