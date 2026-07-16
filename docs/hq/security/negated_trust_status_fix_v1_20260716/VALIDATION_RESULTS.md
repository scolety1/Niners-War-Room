# Validation Results

| Gate | Result |
|---|---|
| Current-HQ safe PoC | four negated values became `VALID_CURRENT`; text hidden |
| Postpatch paired PoC | zero `VALID_CURRENT`; all five source values retained |
| New malicious/legitimate security matrix | 26 passed |
| Decision Trust Strip owning set | 78 passed |
| Exact canonical UI contract | 9 passed |
| Strict Hermetic clean committed tree | 2267 passed; zero skip/xfail/xpass; exit 0 |
| Focused security controls inside Hermetic | 20 passed |
| Bootstrap controls inside Hermetic | 13 passed |
| LocalData availability | `BLOCKED_MISSING_LOCAL_TEST_PACK`; 0 collected; exit 4 |
| Changed-file Ruff | pass; zero findings |
| Scoped Ruff differential | baseline 81; candidate 81; zero new |
| Repository Ruff differential | baseline 4443; candidate 4443; zero new |
| `git diff --check` and cached check | pass |

The first strict Hermetic attempt ran before the local commit. It collected the
full 2267-test set: 2257 passed and 10 legacy cleanliness assertions rejected
the expected dirty `src/services/` path. The authoritative result above is the
identical gate rerun from the clean committed tree.

LocalData was not run, skipped, xfailed, or represented as Hermetic. The
owner-authorized pack was absent, so the tier blocked before collection.
