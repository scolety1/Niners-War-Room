# Project Gold Sprint 2 / Phase 12: Position Formula Rebuild Proposal

Generated: 2026-05-14

## Scope

This is a narrow formula pass. The audit record from Phases 7-11 does **not** support a broad reweight yet because the active free-data preview still has:

- stale production coverage relative to newer role/depth/injury files
- no true independent projection feed
- missing participation/route data
- missing market/liquidity data

Rankings must remain review-only.

## Audit Inputs Reviewed

- `PROJECT_GOLD_SPRINT_2_PHASE_7_ROLE_USAGE_TRUTH_CHECK.md`
- `PROJECT_GOLD_SPRINT_2_PHASE_8_AGE_DROPOFF_SANITY_AUDIT.md`
- `PROJECT_GOLD_SPRINT_2_PHASE_9_YOUNG_BRIDGE_SANITY_AUDIT.md`
- `PROJECT_GOLD_SPRINT_2_PHASE_10_RANKING_SURFACE_VERIFICATION_AUDIT.md`
- `PROJECT_GOLD_SPRINT_2_PHASE_11_MARKET_CONTAMINATION_AUDIT.md`
- `CRITICAL_PLAYER_SOURCE_TRUTH_AUDIT.md`
- `JSN_TEE_SOURCE_INVESTIGATION.md`
- `RB_WR_CROSS_POSITION_REALITY_CHECK.md`
- `NINERS_ROSTER_DECISION_TRIAL_RUN.md`

## Supported Formula Problems

### QB

Problem: the 1QB elite exception was too dependent on expected/projection fields. Sprint 1 and 2 explicitly quarantined local baseline projections as non-independent evidence. That is correct, but it means a secure rushing QB with elite actual LVE production can be over-suppressed if expected/projection scores are neutralized.

Supported change: allow the QB elite/rushing exception to use a real recent-production signal as an alternative to independent expected/projection evidence. Keep the start-security gate and rushing gate intact.

### TE

Problem: the no-premium elite TE exception also leaned on expected/projection evidence. In no-TE-premium, elite TE treatment should require route role and target earning first, but a TE with strong route/target profile plus proven production or efficiency should not need an independent projection feed to avoid generic TE suppression.

Supported change: allow the TE elite exception to use route role + target earning + actual production/efficiency as the gate. Keep non-elite/no-route TEs suppressed.

## Unsupported / Deferred Formula Changes

### RB

No broad RB reweight is supported in this phase. Existing fixtures already prevent a role-only or fragile workload spike from becoming RB1, and the cross-position audit showed RB/WR balance improved after local baseline projection neutralization.

Deferred until better data:

- true independent opportunity/projection data
- stronger goal-line/red-zone role data
- cleaner injury/workload fragility source

### WR

No broad WR reweight is supported in this phase. JSN vs Tee is currently a source-window problem, not a proven formula bug. Target earning, route role, age, and production stability are already visible in receipts.

Deferred until better data:

- current-season production import
- route participation / TPRR
- independent projections

## Fixtures To Add Before Applying

- Elite secure rushing QB with neutral expected/projection still clears 1QB elite exception when actual LVE production and rushing are elite.
- Good pocket QB with neutral expected/projection remains suppressed.
- Elite route/target TE with neutral expected/projection but proven production/efficiency can clear no-premium elite exception.
- Low-route TE remains suppressed even with decent production.

## Expected Impact

This should only affect edge cases where projection status is review-only but actual football evidence is strong. It should not:

- let market affect private value
- boost all QBs
- boost generic TEs
- change RB/WR balance
- clear review-only status
