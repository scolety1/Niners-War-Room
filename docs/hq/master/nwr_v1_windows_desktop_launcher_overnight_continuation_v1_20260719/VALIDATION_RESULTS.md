# Validation results

| Gate | Result |
| --- | --- |
| Accepted/remote HQ | exact `dc399a8c…` / `e6f98339…` |
| Prior launcher commit | `f227e0bd…` |
| Bounded correction commit | `4c6fd443…` |
| Independent correction re-review | no correction-commit blocker |
| Focused launcher tests | 28 passed |
| Real no-browser lifecycle | health 200; `VERIFIED_RUNNING`; duplicate 0; stop 0; port free |
| Backup family/schema/path/rollback attacks | rejected or exact rollback |
| Browser ownership cleanup | focused pass; GUI not run |
| PowerShell parsing | pass |
| Python compilation | pass |
| Changed-file Ruff | pass |
| Hermetic bootstrap controls | 13/13 |
| Security controls | 20/20 |
| Hermetic Python | 2,676 passed; exit 0 |
| LocalData | `BLOCKED_MISSING_LOCAL_TEST_PACK`; exit 4 |
| Legacy Data Health | `CORRUPT`; migration/start blocked |
| Explorer identity | unresolved/access denied |
| Stable checkout | absent; not created |
| Desktop/Start Menu | absent; not installed |
| Push | not performed |
| Primary hashes | all five exact |
| Protected/frozen paths | unchanged |

The final verdict is blocked machine adoption, not a failed launcher correction.
