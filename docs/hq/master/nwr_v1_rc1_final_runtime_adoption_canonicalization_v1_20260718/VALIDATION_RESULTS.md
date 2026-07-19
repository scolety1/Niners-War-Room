# Validation results

## Independent final questions

| # | Question | Answer | Evidence |
| --- | --- | --- | --- |
| 1 | Is the source ancestry exact? | Yes | `7a3d01a5` -> `c380956d` -> `51f2e96b`; both direct-parent checks passed. |
| 2 | Does the combined source tree equal the reported tree? | Yes | Successor tree is exactly `336fb52f3dedfe18da04b54ef54885be6aa06dec`. |
| 3 | Is `/draft-cockpit-root` correct? | Yes | Production-registered `SUPPORTED_HIDDEN_ROUTE`; direct and internal navigation agree; H1 is `Draft Cockpit`. |
| 4 | Does the complete endpoint matrix pass? | Yes | 180/180. |
| 5 | Do three independent runtime cycles pass? | Yes | 3/3 with six successful starts and six graceful shutdowns. |
| 6 | Is the Windows fatal absent? | Yes | Zero `_PySemaphore_Wakeup`, `ReleaseSemaphore failed`, or other fatal markers. |
| 7 | Are all listeners, ports, and processes cleaned? | Yes | Zero retained listeners/processes and port 8520 released after every stop. |
| 8 | Does the runtime-state classifier use path ownership? | Yes | Normalized governed-root ownership controls classification. |
| 9 | Are documentation manifests excluded safely? | Yes | Exact `docs/hq/` authority and required tracked manifest are not runtime state. |
| 10 | Are actual runtime manifests and receipts still detected? | Yes | Local, nested, and service-owned runtime authorities pass. |
| 11 | Is Hermetic validation green? | Yes | 13/13 bootstrap; 20/20 security; 2,648 passed; exit 0. |
| 12 | Is LocalData accurately blocked? | Yes | `BLOCKED_MISSING_LOCAL_TEST_PACK`, exit 4, separately counted. |
| 13 | Do all supported workflows pass? | Yes | Focused suite and live acceptance passed. |
| 14 | Are all five security findings closed? | Yes | Existing focused regressions and 20/20 security controls passed. |
| 15 | Is Data Health passive and truthful? | Yes | No provider refresh or receipt/runtime mutation on page read. |
| 16 | Are CSV exports safe? | Yes | Development Lab and Draft Freeze spreadsheet-safe regressions passed. |
| 17 | Are trust, source, identity, and freshness states truthful? | Yes | Fail-closed trust tests and protected checks passed. |
| 18 | Is V1 scope frozen? | Yes | No parked or post-V1 capability was enabled. |
| 19 | Are known limitations accurate? | Yes | LocalData, local-only durability, parked work, screen-reader recommendation, warnings, and unproven CPython owner are truthful. |
| 20 | Is automation still disabled? | Yes | `READY_FOR_HUMAN_REENABLE_REVIEW`; automatic commit/push remain false and unauthorized. |
| 21 | Are protected and frozen paths unchanged? | Yes | 139-path set has zero candidate diffs; nine protected blobs match HQ. |
| 22 | Are all five preservation hashes unchanged? | Yes | All pre-review, post-Hermetic, post-cycle, and pre-push checks match; post-push readback is mandatory. |
| 23 | Is rollback complete? | Yes | Linear normal-revert plan is complete; no reset or force push. |
| 24 | Is there any unresolved release blocker? | No | Every release-critical gate passed. |

## Additional exact results

- Starting HQ/tree: `7a3d01a5fdd95f4a71d49ced7ff00b334434aa73` / `b4ab40e584c7c1d39d00f93ee8e5725dc22aafdf`.
- Remote advance: none after fetch/prune.
- Source branch: `work/nwr-v1-rc1-runtime-targeted-revision-v1-20260718`; clean.
- Combined diff: 77 paths; 17 non-packet plus 24 original release packet plus preserved 17-file RED packet plus 19-file successor packet.
- Route inventory: 60 endpoints including root; 59 registered; 18 visible; 41 hidden.
- Browser failures: zero in every recorded category.
- Runtime: 3/3; six starts; six exit-0 graceful shutdowns; zero forced cleanup, retained listener/process, fatal marker, or reset.
- Focused route/classifier/lifecycle: 64 passed.
- Focused CSV/trust: 300 passed.
- Focused core workflows: 277 passed.
- Hermetic: 2,648 passed; zero skip/xfail/xpass; exit 0.
- Ruff: changed paths green; full-tree delta zero from identical 4,443-finding baselines.
- LocalData: exact missing-pack block; exit 4.
- Push decision at commit creation: authorized subject only to final remote/preservation rechecks and normal non-force push.
