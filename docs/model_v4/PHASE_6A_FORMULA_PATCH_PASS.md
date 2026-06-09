# Model v4 Phase 6A Formula Patch Pass

Generated: 2026-05-16

## Status

Model v4 remains review-only.

Active app rankings, My Team, War Board, readiness gates, draft readiness, and final-money readiness were not promoted or unlocked.

Patch table: `docs/model_v4/PHASE_6A_FORMULA_PATCH_PASS.csv`

Pre-patch sanity report: `docs/model_v4/PHASE_6A_PRE_PATCH_SANITY_FIXTURES.csv`

Post-patch sanity report: `docs/model_v4/PHASE_6A_SANITY_FIXTURE_RESULTS.csv`

## Evidence Reviewed

- `docs/model_v4/PHASE_5_CHECKPOINT.md`
- `docs/model_v4/PHASE_5_WR_NORMALIZATION_AUDIT.md`
- `docs/model_v4/PHASE_5_MOVEMENT_AUDIT.md`
- `docs/model_v4/PHASE_5_VETERAN_MISSING_DATA_PENALTY.md`
- `docs/model_v4/SANITY_FIXTURE_CONTRACT.csv`
- `docs/model_v4/POSITION_FORMULA_PROPOSAL.md`
- `local_exports/model_v4/review_only_latest`

## Pre-Patch Findings

The pre-patch fixture run had 29 fixtures:

- ready: 23
- review: 6
- blocked: 0

The review findings were:

- `rb_bijan_rb1_002`: Bijan was RB2 because Saquon edged him with missing projection evidence reweighted out.
- `wr_elite_tier_001`: Puka was below the core-tier threshold.
- `wr_puka_core_004`: Puka was below the core-tier threshold.
- `qb_1qb_suppression_001`: replaceable QBs equaled or exceeded the elite RB/WR benchmark.
- `qb_replaceable_control_002`: replaceable QB controls equaled or exceeded the elite RB/WR benchmark.
- `te_no_premium_001`: ordinary/no-premium TEs equaled or exceeded the elite RB/WR benchmark.

## Patches Applied

### 1. QB Position Scarcity Suppression

The formula config already reserved 18% QB weight for `position_scarcity_suppression`, but the v4 calculator did not emit that component. That made the 1QB suppression rule a paper contract rather than an actual score receipt.

Patch:

- Added `position_scarcity_suppression` receipt rows for QBs.
- Added explicit review warnings:
  - `one_qb_suppression_review_only`
  - `elite_rushing_qb_exception_review_only`
  - `replaceable_qb_suppressed`
- Capped non-elite/non-rushing QB profiles so they cannot behave like superflex assets.

Expected effect:

- Elite/rushing QBs can remain useful exceptions.
- Replaceable or merely solid QBs fall behind elite RB/WR assets in a 10-team 1QB league.

### 2. TE No-Premium Suppression

The formula config already reserved 10% TE weight for `no_premium_suppression`, but the v4 calculator did not emit that component. That left the no-TE-premium rule under-enforced.

Patch:

- Added `no_premium_suppression` receipt rows for TEs.
- Added explicit review warnings:
  - `no_premium_te_suppression_review_only`
  - `elite_te_exception_review_only`
  - `replaceable_no_premium_te_review`
- Preserved a limited elite-volume exception while suppressing ordinary TEs.

Expected effect:

- True elite-volume TEs remain visible as possible exceptions.
- Ordinary no-premium TEs no longer crowd out elite RB/WR benchmarks.

### 3. WR Projection Balance

Phase 5G found no production or usage normalization math bug, but it did find formula/data-recency concerns: strong current raw-stat projection evidence was being overwhelmed by stale 2022-2024 production and usage rows, while route participation and route efficiency remain unavailable.

Patch:

- WR production weight changed from 26 to 22.
- WR usage/opportunity weight changed from 24 to 20.
- WR snap/proxy role weight changed from 6 to 5.
- WR projection weight changed from 10 to 19.

Expected effect:

- Current recomputed projection evidence matters more for WRs.
- Production and usage remain important, but stale historical evidence has less ability to bury current elite WR projections.
- Route metrics remain unavailable and are not faked.

### 4. Missing Evidence Uncertainty Haircut

Phase 5H correctly stopped missing veteran evidence from acting as proof of zero value. However, the pre-patch RB1 fixture showed the opposite edge case: missing projection evidence could be reweighted out and let an incomplete review-confidence row edge a complete high-confidence anchor.

Patch:

- Added `missing_evidence_policy` to `MODEL_V4_FORMULA_CONFIG.json`.
- Evidence-adjusted established-veteran rows keep missing components out of the zero-production denominator, but receive a small uncertainty haircut:
  - `missing_component_uncertainty_penalty_rate`: 0.2
  - `max_missing_component_uncertainty_penalty`: 8.0

Expected effect:

- Missing evidence is still not fake zero production.
- Missing evidence also cannot become a hidden ranking advantage.

## Changes Not Made

No RB component-weight patch was made. The RB fixture failure was resolved through the missing-evidence uncertainty policy, not by changing RB production, usage, projection, age, or young-prior weights.

No young-player bridge weight patch was made. Phase 6A fixtures showed young-prior overreach was contained after the Phase 5 repairs.

No market or league-rank scoring change was made. Market and league-rank context remain excluded from Dynasty Asset Value.

No route metric change was made. Route participation, routes run, TPRR, and YPRR remain unavailable unless a licensed structured source is added later.

## Post-Patch Result

The post-patch fixture run had 29 fixtures:

- ready: 29
- review: 0
- blocked: 0
- decision-ready unlocked: false
- auto-fixes applied by fixture runner: false

This does not mean v4 is ready for promotion. It means the known Phase 6A fixture-backed formula issues were patched enough for the next movement/audit phase.

## Current Preview Guardrails

Current regenerated v4 preview summary:

- formula version: `model_v4_review_only_0.2.0`
- preview rows: 80
- component rows: 660
- receipt rows: 660
- source coverage rows: 660
- active rankings overwritten: false
- app promotion: false
- decision ready unlocked: false
- draft ready unlocked: false
- final money ready unlocked: false

## Next Step

Proceed to Phase 6B: Post-Formula Preview And Movement Audit.

Phase 6B should compare this formula-patched preview against the Phase 5 checkpoint preview and explain every meaningful movement before any app promotion discussion.
