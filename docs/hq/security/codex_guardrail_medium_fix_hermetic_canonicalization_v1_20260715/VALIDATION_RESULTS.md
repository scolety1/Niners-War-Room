# Validation Results

| Gate | Independent result |
|---|---:|
| Original Git-state PoC | applicable; exit 0; staged/untracked omitted |
| Original mutable-profile PoC | applicable; exit 0; reload and expression sink present |
| Postpatch focused security | 20 passed |
| Alternate bypass review | 10/10 pass |
| PowerShell AST | 8/8 parse |
| Bootstrap controls | 13 passed |
| Complete Hermetic | 2241 passed; no skip/xfail/xpass; exit 0 |
| LocalData absent | exact marker; 0 collected; exit 4 |
| Current-HQ differential | 2229 passed, 1 false-positive baseline failure |
| Candidate differential | 2241 passed, 0 failed |
| Exact UI contract | 9 passed |
| Scoped Ruff | HQ 81; candidate 81 |
| Repository Ruff | HQ 4443; candidate 4443 |
| Changed Python Ruff | zero findings |
| Application source diff | empty |
| Implementation packet | 22/22 present; JSON/CSV valid |
| Canonicalization packet | 17/17 present; JSON/CSV valid before commit |
| `git diff --check` / cached check | pass / pass |

Both findings were valid before the patch and are fully fixed afterward. LocalData absence is the only caveat. No push is claimed by this pre-push receipt; final remote readback is recorded in the mission master receipt.
