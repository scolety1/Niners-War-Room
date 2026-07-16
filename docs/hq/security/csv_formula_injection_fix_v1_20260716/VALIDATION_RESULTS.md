# Validation Results

| Gate | Result |
|---|---|
| Prepatch Development Lab PoC | confirmed raw `  =1+1` |
| Prepatch Draft Freeze PoC | confirmed raw tab + `@SUM(1,1)` |
| Postpatch paired PoC | both encoded; numeric controls preserved |
| New malicious/legitimate matrix | 30 passed |
| Owning and adjacent focused set | 92 passed |
| Strict Hermetic clean committed tree | 2271 passed; zero skip/xfail/xpass; exit 0 |
| Focused security controls inside Hermetic gate | 20 passed |
| Bootstrap controls inside Hermetic gate | 13 passed |
| LocalData availability | `BLOCKED_MISSING_LOCAL_TEST_PACK`; 0 collected; exit 4 |
| Changed-file Ruff | pass; zero findings |
| Repository-wide Ruff differential | baseline 4443; candidate 4443; zero new |
| `git diff --check` and cached check | pass |

The first strict Hermetic attempt was intentionally made before the local
commit. It reached the full 2271-test collection: 2261 passed and 10 legacy
cleanliness checks rejected the dirty `app/` path. The authoritative result
above is the identical gate rerun from the clean committed tree.

LocalData was not run, skipped, xfailed, or represented as Hermetic. The
approved owner-authorized pack was absent, so the tier blocked before test
collection as designed.
