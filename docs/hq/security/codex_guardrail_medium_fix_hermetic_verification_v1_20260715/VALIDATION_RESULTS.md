# Validation Results

| Gate | Result | Exit |
|---|---:|---:|
| PowerShell AST parse | all 8 owned/revised scripts parse | 0 |
| Focused security | 20 passed | 0 |
| Bootstrap/tier contracts | 14 passed | 0 |
| Hermetic Python | 2241 passed; 0 skip/xfail/xpass | 0 |
| LocalData absent | `BLOCKED_MISSING_LOCAL_TEST_PACK`; no collection | 4 |
| Developer aggregate | Hermetic 0 independently visible; LocalData 4 independently visible | 4 |
| Canonical UI contract | 9 passed | 0 |
| Corrected Future Tools file | 7 passed | 0 |
| Changed Python Ruff | zero findings | 0 |
| Scoped Ruff differential | HQ 81; candidate 81 | zero new |
| Repository-wide Ruff differential | HQ 4443; candidate 4443 | zero new |
| Current-HQ Hermetic-like baseline | 2229 passed; 1 false-positive failure | 1 |
| Candidate differential | 2241 passed | 0 |
| `git diff --check` | pass | 0 |
| `git diff --cached --check` | pass | 0 |

No application source, data, formula, ranking, source-admission, profile, dependency, or frozen-artifact change exists. No push was performed.
