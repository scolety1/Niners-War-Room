# Validation results

| Gate | Result |
| --- | --- |
| Accepted HQ commit/tree | exact `dc399a8…` / `e6f983…` |
| Initial combined focused launcher/lifecycle/persistence | 75 passed |
| Post-review launcher ownership/restore regressions | 20 passed |
| Real first/warm start | health 200 |
| Duplicate launch | exit 0; one server |
| Clean stop/restart | exit 0; no force; port free |
| Changed-state post-shutdown backup | one valid snapshot |
| Crash/stale-lock recovery | state hash retained; restart healthy |
| Restore dry-run/restore | pass through owning draft service |
| Corrupt backup | rejected |
| Worktree replacement | same state available |
| Disposable shortcut install/uninstall | pass |
| PowerShell parsing | pass |
| Changed-file Ruff | pass |
| Python compilation | pass |
| Hermetic bootstrap controls | 13/13 |
| Security controls | 20/20 |
| Hermetic Python | 2,668 passed; zero skip/xfail/xpass; exit 0 |
| LocalData | `BLOCKED_MISSING_LOCAL_TEST_PACK`; exit 4 |
| Existing Data Health receipt | `CORRUPT`; backup `MISSING` |
| Existing tracked service/app diff | none |
| Primary CSV hashes | all five exact |
| GUI browser window/background process | not run; installation blocked |
| Final real ownership cycle | `VERIFIED_RUNNING`; health 200; duplicate exit 0; clean stop |
| Independent final re-review | no implementation commit blocker |

Independent review initially returned red for six concrete ownership, restore, logging, and shortcut-collision gaps. The implementation was not committed in that state. The findings were corrected and covered by the post-review regression set; the final independent re-review is the controlling review result.

The prior Hermetic attempt with experimental service path overrides produced ten intentional frozen-path failures. Those changes were fully removed. The controlling final run is the 2,668-pass result.
