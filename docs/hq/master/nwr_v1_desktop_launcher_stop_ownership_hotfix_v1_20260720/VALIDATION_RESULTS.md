# Validation results

| Gate | Result |
|---|---|
| Focused launcher/process review | PASS: 84 |
| Mutation controls | PASS: 5/5 detected |
| Three live browser lifecycle cycles | PASS: 3/3 |
| Delayed recovery | PASS: first exit 7; subsequent exact Stop exit 0 |
| Hermetic bootstrap | PASS: 13/13 |
| Security regressions | PASS: 20/20; no new scan |
| Hermetic Python/Ruff | PASS: 2,724; exit 0 |
| LocalData | `BLOCKED_MISSING_LOCAL_TEST_PACK`; exit 4 |
| Python compilation | PASS |
| PowerShell parse | PASS: 4 files |
| Changed Ruff / no-new-Ruff | PASS |
| Skip/xfail/xpass differential | PASS: no additions |
| Git diff checks | PASS |
| Primary CSV hashes | PASS: 5/5 exact |
| Persistent inventory | PASS: 13/13 exact |
| Port/process final state | PASS: free/absent |
| Independent exact-commit review | PASS: 16/16 safe answers |
