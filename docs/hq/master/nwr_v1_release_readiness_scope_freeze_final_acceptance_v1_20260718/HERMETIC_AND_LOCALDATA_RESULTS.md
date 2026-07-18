# Hermetic and LocalData results

## Hermetic

Canonical command:

`powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\scripts\verify-repository.ps1 -Tier Hermetic -RepoRoot .`

Verified HQ baseline result:

- deterministic bootstrap: pass;
- bootstrap controls: 13 passed, 0 failed;
- focused security controls: 20 passed, 0 failed;
- Hermetic Python: 2,613 passed in 135.92 s;
- owned Ruff: pass;
- total command duration: 190.931 s;
- exit: 0;
- skips/xfails/xpasses: 0/0/0.

The bounded correction adds one Hermetic test. A dirty pre-commit probe collected all 2,614 tests and failed only ten lane tests that intentionally reject uncommitted `app/` changes plus one stale Data Health expectation; the stale expectation was corrected and its 123-test affected suite passed. The authoritative clean committed candidate must therefore finish at 2,614 passed, no prohibited non-execution results, exit 0.

## LocalData

Canonical command:

`powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\scripts\verify-repository.ps1 -Tier LocalData -RepoRoot .`

Result: `BLOCKED_MISSING_LOCAL_TEST_PACK`; duration 0.484 s; exit 4.

LocalData was not passed, skipped, xfailed, Hermetically counted, copied, synthesized, or waived. Its absence is an accepted V1 caveat because supported workflows start and fail closed without it.
