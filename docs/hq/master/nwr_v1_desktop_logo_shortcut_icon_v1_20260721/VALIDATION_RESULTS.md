# Validation results

| Gate | Result |
|---|---|
| Starting HQ/tree | PASS: `6d465ed0639d8e216a5fd89372a1ed90c0189055` / `d421fc81380e15482c9f9976d985f0344f57c8f4` |
| Source PNG decode/copy | PASS: 1254 x 1254; source-exact SHA-256 |
| ICO frames | PASS: 16, 24, 32, 48, 64, 128, 256; every frame decoded |
| 16/32 visual review | PASS: recognizable composition; 32 preserves shield/NWR structure |
| Disposable shortcut lifecycle | PASS: fresh/update/stale/wrong/unrelated/missing/redirected/space/non-ASCII/uninstall/reinstall |
| Command icon preservation | PASS |
| Launcher entry Stop | PASS: `STOPPED`, port released, ownership NONE |
| Hermetic | PASS: 13 bootstrap, 20 security controls, 2,734 Python tests, exit 0 |
| LocalData | `BLOCKED_MISSING_LOCAL_TEST_PACK`, exit 4; not passed or skipped |
| Five-finding regressions | PASS inside accepted controls; no new scan |
| Data Health/CSV/trust/ranking/route/UI contracts | PASS inside Hermetic |
| Changed-file Ruff | PASS |
| Full-tree Ruff differential | PASS: 4,443 vs 4,443; delta zero |
| Python compilation | PASS |
| PowerShell parsing | PASS |
| Protected/frozen/security automation | PASS: no change |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS before staging; repeat required after staging |
| Primary five CSV hashes | PASS: 5/5 exact |
| Persistent settled baseline | PASS at documentation checkpoint |
| Backups/recovery validation | PASS: 5/5 retained backups; recovery valid |

The first Hermetic attempt correctly failed only 10 maintenance tests because the pre-existing real runtime still owned port 8520; 2,724 other tests passed. After exact canonical Stop, the authoritative rerun passed all 2,734 tests with exit 0.
