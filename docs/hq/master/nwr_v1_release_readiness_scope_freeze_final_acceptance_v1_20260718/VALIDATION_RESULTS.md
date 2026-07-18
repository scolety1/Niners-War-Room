# Validation results

## Ordered gate ledger

| Order | Gate | Result |
|---:|---|---|
| 1 | Fetch/prune, HQ and ancestry | Exact expected HQ/tree; no advance or intervening commit |
| 2 | Product/route inventory | 59 registered routes, 18 visible, 41 hidden, 46 unique registered modules; root alias added to smoke |
| 3 | V1 scope authority | Frozen scope and parked items reconciled |
| 4 | Clean bootstrap/start | Pass; no credentials/private data/LocalData/copy/absolute sibling dependency |
| 5 | Hermetic baseline | 13/13 bootstrap, 20/20 security, 2,613 Python, owned Ruff, exit 0 |
| 6 | LocalData | `BLOCKED_MISSING_LOCAL_TEST_PACK`, exit 4 |
| 7 | Focused security | 20/20 PowerShell; 300 CSV/trust security tests |
| 8 | Data Health/passive reads | 116 passed; final affected suite 123 passed |
| 9 | Rankings/Player Compare | 128 authoritative passed; final affected suite 137 passed |
| 10 | Trading Lab | 34 passed |
| 11 | Live/Mock Draft | 194 passed |
| 12 | Roster truth state | 66 passed |
| 13 | CSV exports | 334 passed |
| 14 | Trust classification | 58 passed |
| 15 | Navigation/all-route smoke | 180/180 pass |
| 16 | Responsive | 60/60 at each required width; zero root overflow |
| 17 | Accessibility | Semantic primary heading on 180/180; visible-route labels/disclosures pass |
| 18 | Startup/reliability | Cold/warm pass; no remaining listener/process |
| 19 | Documentation | README corrected; 24-file packet present |
| 20 | Bounded correction | One cycle only; focused reruns green |
| 21 | Affected reruns | 123 and 137 focused tests; changed-file Ruff/compile green |
| 22 | Python compilation | Changed-file compilation passed; full compile required before commit |
| 23 | Changed-file Ruff | Pass |
| 24 | No-new-Ruff differential | HQ 4,443; candidate 4,443; differential 0 |
| 25 | Security automation proof | Zero changed automation/protected security files |
| 26 | Protected/frozen scan | 533 entries; aggregate hash recorded; zero changes |
| 27 | Primary preservation | Five required hashes exact |
| 28 | `git diff --check` | Pass |
| 29 | `git diff --cached --check` | Required after exact staging |
| 30 | Independent acceptance | 22/22 answers acceptable subject to clean committed gate |
| 31 | Local commit | Exactly one local RC commit required |
| 32 | Clean successor | Required after commit; no push/tag |

## Correction-cycle test detail

- First exploratory rankings probe mixed Hermetic and LocalData-owned files: 5 failures and 6 skips due the intentionally unavailable private full-board pack. Those files are explicitly listed in `tests/hermetic_localdata_manifest.json`; this result is not counted as Hermetic, skipped, or waived.
- Authoritative rankings/compare runs excluded LocalData-owned files and prohibited skips.
- The dirty pre-commit full Hermetic probe collected 2,614 tests and failed 10 tests whose explicit purpose is to reject any dirty `app/` path plus one stale Data Health expectation. The expectation was corrected; its affected suite passed. The canonical post-commit clean run must be 2,614 passed, no skips/xfails/xpasses, exit 0.

## Independent 22-question acceptance

1. Every visible route has a disposition: yes.
2. Supported core workflows function: yes.
3. Clean isolated startup: yes.
4. Hermetic green: yes at canonical base; clean candidate rerun mandatory.
5. LocalData separate/exit 4: yes.
6. Five original security findings closed: yes.
7. Data Health passive/truthful: yes.
8. Trust/freshness/stale/gated/unavailable truthful: yes.
9. CSV spreadsheet-safe: yes.
10. Roster hydration parked: yes.
11. Trading Lab saved scenarios absent: yes.
12. Recommendations within authority: yes.
13. Compact/desktop usable: yes.
14. Release-critical controls accessible: yes; no full screen-reader certification claimed.
15. Startup/navigation reliable: yes in bounded smoke.
16. Limitations complete/honest: yes.
17. V1 scope frozen: yes.
18. Protected/frozen paths unchanged: yes.
19. Five primary hashes unchanged: yes.
20. Rollback actionable: yes.
21. Automatic commit/push disabled: yes.
22. Unresolved release blocker: no, subject to final clean committed verification.

## Final acceptance condition

Adoption is authorized only after exact staging, cached diff check, one local commit, final fetch/ancestry confirmation, clean candidate Hermetic 2,614/exit 0, LocalData exit 4, primary hash recheck, and clean successor status.
