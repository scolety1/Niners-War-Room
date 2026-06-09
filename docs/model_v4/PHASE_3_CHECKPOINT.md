# Model v4 Phase 3 Checkpoint

Created: 2026-05-16

Phase 3 produced a review-only Model v4 preview stack. It did not overwrite
active rankings, unlock readiness gates, or promote any output into the normal
app decision surfaces.

## What Phase 3 Built

### Formula Lane Architecture

`FORMULA_LANE_ARCHITECTURE.md` defines six separate lanes:

- Dynasty Asset Value
- Roster Decision Value
- Required Top-Five Release Pain
- Trade / Market Context
- Draft Value
- Confidence

The global separation rules are intact:

- league rank cannot affect Dynasty Asset Value
- market cannot affect private football value
- required top-five release logic is roster-rule context only
- draftable-player logic is separate from rostered-player value
- unavailable route metrics cannot be scored as real evidence
- snap share can be used only as a role proxy

### Formula Config

`MODEL_V4_FORMULA_CONFIG.json` is a review-only config with version
`model_v4_review_only_0.1.0`.

The config defines position component weights, lifecycle rules, confidence
rules, forbidden-input rules, market policy, league-rank policy, and route
metric policy. Guardrails remain active:

- active rankings must not load this config
- no decision-ready unlock
- no roster-ready unlock
- no draft-ready unlock
- no final-money-ready unlock

### Component Calculators

`model_v4_component_calculator_service.py` implements review-only component
calculators for:

- production
- first-down scoring fit
- usage/opportunity
- snap/proxy role
- projection
- age/dropoff
- young-player prior
- confidence

Each component emits raw fields, raw values, normalized score, source status,
contribution, weight, warning, unavailable reason, and `review_only=True`.
Neutral or missing sections are visible instead of hidden as real evidence.

### V4 Preview Outputs

`build_model_v4_preview.py` generated review-only artifacts under
`local_exports/model_v4/review_only_latest`.

Current preview summary:

- truth-set players: 80
- preview output rows: 80
- component rows: 640
- receipt rows: 640
- source coverage rows: 640
- warning rows: 839
- review status: review_only
- active rankings overwritten: false
- app promotion: false
- decision-ready unlocked: false
- draft-ready unlocked: false
- final-money-ready unlocked: false

Source coverage currently shows 358 covered component rows and 282 missing
component rows across the 80-player truth set.

The largest warning groups are:

- young-player prior not applicable: 50
- missing production data: 45
- missing snap share data: 45
- missing usage opportunity data: 45
- missing first-down data: 45
- missing projection data: 42
- missing participation proxy: 40
- local baseline projection not independent: 38
- missing first-down projection: 38

Some of those warnings are expected review labels, not data bugs. For example,
young-player prior is not applicable for established veterans.

## Audit Results

### Sanity Fixture Dry Run

`PHASE_3_SANITY_FIXTURE_DRY_RUN.md` compares the review-only v4 preview against
the sanity fixture contract.

Current result:

- fixtures: 29
- ready: 26
- review: 3
- blocked: 0
- decision-ready unlocked: false
- auto-fixes applied: false

Review findings:

- `wr_elite_tier_001`: JSN, Puka, and CeeDee are below the core-tier review threshold.
- `wr_jsn_top_tier_002`: JSN is just below the top-tier review threshold.
- `wr_puka_core_004`: Puka is below the core-tier review threshold.

These remain data/source review findings, not proven formula bugs.

### Named-Player Audit

`PHASE_3_NAMED_PLAYER_REVIEW.md` audits 19 important players:

- all requested named players matched
- player review rows: 3
- inspection rows: 6
- inspection review rows: 2
- decision-ready unlocked: false
- score changes applied: false

Ready inspections:

- QB suppression: Lamar does not top the named elite RB/WR group.
- TE suppression: Brock Bowers remains below the top named RB/WR benchmark.
- aging veteran dropoff: Keenan Allen does not outrank young cornerstone RBs.
- market and league-rank separation: clean in v4 private receipts.

Review inspections:

- RB vs WR balance: some elite-WR sanity players remain below the v4 core threshold.
- Young-player bridge behavior: Luther Burden and Kaleb Johnson remain weak-confidence rows due missing NFL production / usage / snap evidence.

### Formula / Receipt Patch Pass

`PHASE_3_FORMULA_REVIEW_PATCH_PASS.md` classified all Phase 3F/3G findings.

Patch applied:

- Fixed named-player report language so positive caution rows are no longer
  presented as `top_negative_receipt_drivers`.

No formula weight changes were made. No formula config changes were made.

## Remaining Data Gaps

These are the main unresolved evidence gaps before trusting the preview as a
real decision engine:

- true route participation, routes run, TPRR, and YPRR remain unavailable from a safe free/public source
- snap share is only a role proxy, not route evidence
- first-down projections are missing
- many incoming/year-one players have no NFL production, first-down, usage, or snap evidence
- some projections are missing or local-baseline only
- source coverage still includes missing component rows across the broader truth set

## Remaining Formula Concerns

No formula bug was proven in Phase 3. The main formula-review concern is WR
tier calibration, but the current evidence points first to source/coverage gaps:

- JSN, Puka, and CeeDee are near or below review thresholds.
- Elite RB checks pass.
- QB/TE suppression checks pass.
- young-player prior is not overpowering NFL evidence in the fixture set.
- market and league rank are not contaminating private value.

The next formula work should not change weights until a WR evidence audit
proves whether the issue is:

- missing data
- source coverage
- normalization
- lifecycle handling
- a true component weight imbalance

## Readiness Confirmation

- Active rankings overwritten: no
- Active app rankings promoted: no
- Roster readiness unlocked: no
- Draft readiness unlocked: no
- Final decision readiness unlocked: no
- Review-only policy remains active: yes

## Next-Step Decision

### Ready for Phase 4 app integration?

Yes, but only as an audit/workbench integration. The app can safely expose the
Model v4 preview, receipts, warnings, and fixture reports behind review-only
labels. It is not ready for normal My Team / War Board decision replacement.

### Ready for another formula patch pass?

Not yet. Phase 3H found no proven formula bug. The right next pass is a WR
evidence audit before any formula tuning.

### Ready for external/pro audit?

Yes, as a review-only checkpoint packet. An external audit should focus on:

- whether WR values are low because of missing evidence or formula imbalance
- whether the component weights are defensible for 10-team 1QB no-PPR LVE
- whether the route/proxy and first-down-projection gaps are handled honestly
- whether receipt explanations are sufficient to trust future formula changes

## Recommended Phase 4 Start

Start Phase 4 with a WR evidence audit:

- Jaxon Smith-Njigba
- Puka Nacua
- CeeDee Lamb
- Tee Higgins
- Brian Thomas Jr.
- Malik Nabers
- Ja'Marr Chase
- Justin Jefferson
- Amon-Ra St. Brown

Compare production, first-down fit, usage, projection, snap proxy, missing
route data, and confidence warnings before touching weights.
