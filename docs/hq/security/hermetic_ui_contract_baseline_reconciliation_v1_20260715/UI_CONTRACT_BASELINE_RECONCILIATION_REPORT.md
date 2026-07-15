# UI Contract Baseline Reconciliation V1

## Verdict

`GREEN_HERMETIC_UI_CONTRACT_BASELINE_RECONCILIATION_READY_FOR_HQ_REVIEW`

## Controlling state

- Remote: `origin`
- Canonical branch: `origin/work/hq-parallel-control`
- Expected and verified live HQ: `6bcb9c3c36fc560c30151591feaeff9d3960499f`
- Remote advance: none after `git fetch --all --prune --tags`
- Successor branch: `work/ui-contract-baseline-reconciliation-v1-20260715`
- Worktree: `C:\NWR\Niners-War-Room-ui-contract-baseline-reconciliation-v1-20260715`
- Push: not run

The primary repository worktree's five modified DynastyProcess CSV files were not edited, staged, reset, copied, or otherwise touched.

## Clean-baseline reproduction

The exact explicit nine-node command collected nine tests and produced `6 failed, 3 passed in 0.12s`. The six failures matched the reported categories exactly: three Phase-5 display-language checks, one Player Board label check, and two trust-banner checks.

All six assertions read tracked source text. No local export, LocalData pack, untracked fixture, private evidence, or security candidate was used to establish the baseline.

## Authority result

Four expectations were stale after the accepted Draft-Day V1 route and vocabulary changes. Two trust tests were wrapper-level harness defects already identified by the canonical Decision Trust Strip adoption packet and the July 11 current-surface map.

| Area | Classification | Repair |
|---|---|---|
| Phase-5 warning-group assertion | `STALE_TEST_EXPECTATION` | Keep the governed warning-group/raw-code assertion on the legacy Decision Board that still owns it; stop requiring it from the later Draft Prep surface. |
| Phase-5 filter-language assertion | `STALE_TEST_EXPECTATION` | Assert the accepted current Dynasty Rankings presets and advanced-filter vocabulary. |
| Phase-5 score-disclosure assertion | `STALE_TEST_EXPECTATION` | Assert the current rankings trust/receipt disclosure and canonical six-field trust vocabulary. |
| Player Board UI labels | `STALE_TEST_EXPECTATION` | Point the test to the canonical `/rankings` implementation and assert the accepted Dynasty Rankings labels. |
| One primary trust banner | `FIXTURE_OR_HARNESS_DEFECT` | Resolve the route wrapper to the canonical rankings implementation while retaining old-banner checks on legacy consumers and the Draft Prep gated banner. |
| Required review-only banner | `FIXTURE_OR_HARNESS_DEFECT` | Validate the accepted Decision Trust Strip on rankings and the still-applicable review-only/scouting banners on other pages. |

## Repair scope

Only three tracked tests and this packet changed. No application page, component, service, model, data file, fixture data, navigation definition, route definition, accessibility markup, responsive CSS, security automation, or frozen artifact changed.

The focused result is `9 passed in 0.09s`. The owning and adjacent regression set is `100 passed, 14 skipped`; all skips are the existing clean-worktree local-pack sentinels and none of the nine focused nodes is skipped or xfailed.

## Security-lane separation

Commit `1dd0e28754d25f1ce5d2effcc53ca0d31bb41a6b` was not cherry-picked. No security patch was adopted or reimplemented. The medium-severity guardrail lane, Hermetic bootstrap, LocalData tier, automation behavior, profile, commit behavior, and push behavior remain outside this branch.

The two trust failures do not exercise negated status parsing and are not the low-severity negated-status finding from scan `85b6913f-ffcf-437e-bd3a-3597d75eb8c5`. No Decision Trust Strip service behavior was changed.

## Disposition

The repaired baseline is ready for independent HQ merge review. The medium-severity security transplant may resume only after HQ independently accepts this local commit as the canonical baseline repair.
