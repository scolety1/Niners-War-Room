# Validation results

## Canonical and data gates

| Gate | Result |
| --- | --- |
| Live remote `origin/work/hq-parallel-control` | `cdc77f32507ef7e451b872b9a7c28275af6c4725` |
| Expected tree | `d5df1e865b010b58b49be70b8b3ba91308159ef6` |
| Active data-pack validation | 0 errors, 0 warnings |
| Active pack row counts | players 240; rosters 240; official rankings 240; model outputs 240; future picks 50; pick values 50; metadata 7 |
| Approved full dynasty board | 240 rows; exact pinned hash; 0 validation errors |
| Outcome V1 | 240 rows; exact pinned hash; 0 validation errors |
| Outcome V2 | 240 rows; exact tracked hash; 0 validation errors |
| NFLVerse player context | 294 rows; 0 validation errors |
| Frozen draft board | 66 rows; green |
| Ranking-surface leakage audit | 0 findings |

## Runtime and rendered gates

| Gate | Result |
| --- | --- |
| Expected PowerShell start command | `HEALTHY`; `VERIFIED_RUNNING`; state `RUNNING` |
| Loopback health | HTTP 200, body `ok` |
| Rendered Dynasty Rankings | 240 rows; exact accepted top five |
| Rendered Data Health | commit `cdc77f...`; full dynasty 240 green; frozen board 66 green |
| Rendered ranking consumers | Draft Cockpit, Player Compare, Trading Lab, Legacy Rankings, and War Board resolved their intended sources |
| Installed Desktop shortcut cycle after lineage repair | `HEALTHY / VERIFIED_RUNNING` then `STOPPED`; port released |
| Final status | `STOPPED`; ownership `NONE`; no remaining resources |

## Automated tests

| Selection | Result |
| --- | --- |
| Ranking consumers, Data Health, pages, and navigation | 144 passed |
| Windows process ownership plus desktop launcher | 81 passed |
| Disposable shortcut exact target, idempotence, migration, and uninstall | Included in launcher selection; passed |

Final combined rerun: 225 passed in 41.69 seconds.

The first all-launcher run while the live verification server occupied port 8520 correctly failed maintenance tests that require a free port. The identical launcher file passed 40/40 after the verified runtime was stopped. No test was skipped, xfailed, or weakened to conceal a runtime defect.

## Final lifecycle evidence

The final installed Desktop-shortcut cycle produced:

```text
Start: HEALTHY / VERIFIED_RUNNING / RUNNING
Stop: STOPPED / port_released=true
Final status: STOPPED / process_ownership=NONE / remaining_resources={}
```

No new `[WinError 6] The handle is invalid` entry appeared after migration to the PowerShell wrapper.
