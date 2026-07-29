# Validation results

## Deterministic builder gates

- source hashes and canonical ancestry: PASS
- 43-row current authority inventory: PASS
- 79-row V3 schema / 72 governed fields / 7 aliases: PASS
- exact-ID target and censor contract: PASS
- nested chronological OOF contract: PASS
- C0 baseline constants and reproduction: PASS
- per-field acceptance completeness: PASS (72/72)
- probability bounds: PASS
- governed logical violations: PASS (zero after projection)
- blocked fields nonnumeric: PASS
- wrong-position `N/A`: PASS
- current insufficient `Not enough information`: PASS
- Finished V1 row/order/hash/top-five: PASS
- integration rows: PASS (17280)

## Release classifications

| classification | fields |
| --- | --- |
| OUTCOME_V3_KEEP_CURRENT_BASELINE | 36 |
| OUTCOME_V3_BLOCKED_WEAK_CALIBRATION | 16 |
| OUTCOME_V3_BLOCKED_LOW_SAMPLE | 8 |
| OUTCOME_V3_UPGRADE_ADMISSIBLE | 7 |
| OUTCOME_V3_DIRECTIONALLY_BETTER_NOT_ADOPTED | 5 |

## Completed release receipts

- Outcome, UI, navigation, accessibility, and page-open checks: PASS (67/67)
- expanded implementation and independent focused suites: PASS (85/85 each)
- Decision Trust and Refresh Recovery regressions: PASS (58/58)
- passive Data Health suite: PASS (59/59)
- CSV/formula-security regression suite: PASS (272/272)
- browser viewport checks: PASS (6/6 across 375x812, 768x1024, 1440x1000)
- privacy-safe screenshot captures: PASS (4/4)
- changed-path Python compilation: PASS
- changed-path Ruff: PASS (zero findings)
- repository Ruff differential: PASS (HQ 4,443; candidate 4,443; new 0)
- whitespace (`git diff --check`): PASS
- LocalData missing-pack contract: PASS
  (`BLOCKED_MISSING_LOCAL_TEST_PACK`, child exit 4)
- Finished V1 board/frozen/opaque/persistent/recovery preservation: PASS
- protected and frozen path scan: PASS
- provider calls: NONE
- security scan: NOT RUN, as required
- scheduled refresh task: DISABLED; matching refresh processes: 0
- clean implementation Hermetic gate: PASS
  (13/13 bootstrap controls, 20/20 repository controls,
  2,895/2,895 tests, exit 0)
- independent clean-root rebuild: PASS
  (34/34 regenerated text artifacts matched committed raw blobs;
  4/4 screenshots retained; `--verify-existing` PASS)
- independent diff/path and rejected-chain review: PASS
  (48 changed paths; zero protected matches; no prior evidence commit entered)
- independent adoption Hermetic gate: PASS
  (13/13 bootstrap controls, 20/20 repository controls,
  2,895/2,895 tests, exit 0)
- independent adoption LocalData and preservation: PASS
  (required child exit 4; all pinned receipts exact)

## Post-push closeout

Remote readback, stable-checkout update, and launcher lifecycle are performed
only after this reviewed candidate is committed and the conditional normal
non-force push succeeds. They are never inferred from the builder itself.
