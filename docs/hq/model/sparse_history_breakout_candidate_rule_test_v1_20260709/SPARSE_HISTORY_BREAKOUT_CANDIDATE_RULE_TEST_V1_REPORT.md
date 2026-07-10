# Sparse-History Breakout Candidate Rule Test V1

## Verdict

`GREEN_SPARSE_HISTORY_RULE_TEST_FOUND_PROMISING_MISS_REDUCTION`

## Scope

This is a bounded review-only sparse-history rule overlay test. It did not change production rankings, app/runtime/model behavior, source promotion, push/merge state, canonical `local_exports`, ranking simulation, or production/model-use approval.

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`.

Prior sparse-history design commit verified: `f493dbf751e42b1f258df14e41a20fde9274d136`.

## Registry

Rules registered: `12`.

Windows tested: `full_history 2013-2025`, `broad_window 2014-2025`, and `partial_window 2022-2025`.

## Best Results

Best net miss-reduction rule: `RULE_005_EARLY_CAREER_LIFECYCLE_025` on `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100` / `full_history`, net miss reduction `12`, misses resolved `31`, new misses `19`.

Best false-positive trap rule: `RULE_010_FALSE_POSITIVE_TRAP_STRICT_10` with FP reduction `0`.

Best false-negative breakout rule: `RULE_005_EARLY_CAREER_LIFECYCLE_025` with FN reduction `6`.

Trap-rule decision: No false-positive trap rule achieved positive FP reduction; trap downgrades should stay context/harm review only.

Rules with material Spearman lift (`>= .003`): `1`.

Rules with material net miss reduction (`>= 8`): `6`.

Rules with unacceptable collateral/harm flags: `17`.

## Classifications

- `PROMISING_REVIEW_ONLY_RULE`: `RULE_002_DEPTH_STARTER_BREAKOUT_05, RULE_005_EARLY_CAREER_LIFECYCLE_025, RULE_006_DRAFT_CAPITAL_WITH_ROLE_05, RULE_011_SPARSE_HISTORY_COMPOSITE_BALANCED`
- `MIXED_REVIEW_ONLY_RULE`: `RULE_001_ROLE_PROMOTION_BREAKOUT_05, RULE_003_SNAP_GROWTH_BREAKOUT_05, RULE_008_POSITION_SPECIFIC_BREAKOUT_05`
- `CONTEXT_ONLY_RULE`: `RULE_004_AVAILABILITY_REBOUND_05, RULE_010_FALSE_POSITIVE_TRAP_STRICT_10`
- `HARMFUL_RULE`: `RULE_009_FALSE_POSITIVE_TRAP_DOWNGRADE_05`
- `PARTIAL_WINDOW_ONLY_RULE`: `RULE_007_EXPECTED_OPPORTUNITY_PARTIAL_05, RULE_012_COMPOSITE_PARTIAL_EXPECTED_OPP`
- `BLOCKED_OR_INVALID`: `none`

## Decision

Review-only ranking simulation remains not justified. The next lane is `Sparse-History Rule Refinement Contract V1`.
