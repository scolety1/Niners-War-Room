# Formula Gauntlet Data Readiness Checklist

No real Formula Gauntlet should run until these prerequisites are satisfied or explicitly waived for review-only research.

## Required Before Candidate Tournament

- [ ] Admitted historical fantasy finishes are available and source-traced.
- [ ] Historical finish caveats, including any 2025 reconciliation caveats, are documented.
- [ ] Stable player identity joins exist for every season and position in scope.
- [ ] Name-only joins are excluded or manually reviewed.
- [ ] Source-safe stats inventory exists.
- [ ] Every candidate stat has source-gate status.
- [ ] Current active formula receipt chain status is documented.
- [ ] Missing upstream formula receipts are mapped.
- [ ] Baseline definitions are frozen before candidate evaluation.
- [ ] League scoring format is confirmed: 10-team dynasty/keeper hybrid, 1QB, non-PPR, first-down scoring, K de-emphasized.
- [ ] Starters are confirmed: 1 QB, 2 RB, 3 WR, 1 TE, 2 FLEX, 1 K.
- [ ] FLEX eligibility is confirmed as RB/WR/TE only.
- [ ] Position-specific outcome labels are available for QB, RB, WR, and TE.
- [ ] Train, validation, and holdout split policy is written before running candidates.
- [ ] Review-only artifact destination is declared.
- [ ] Leakage guardrails are encoded and audited.
- [ ] Missing-data handling is explicit.
- [ ] Prior-year finish baseline is available.
- [ ] Current-formula-family proxy baseline is available if exact formula replay remains blocked.
- [ ] Exact current formula replay status is declared.

## Required Source-Gate Checks

- [ ] NGS status is confirmed before any NGS-derived metric use.
- [ ] PFR advanced stats status is confirmed before any PFR-derived metric use.
- [ ] NFLVerse field-level availability is confirmed before field use.
- [ ] CFBD rookie profile fields are confirmed before model use.
- [ ] Injury and availability context has point-in-time receipts before use.
- [ ] Route/YPRR/TPRR remain blocked unless a separate admission lane approves them.
- [ ] PFF, SIS, Sportradar, commercial FTN, and proprietary charting sources remain blocked unless a separate license/source-admission lane approves them.

## Required Baseline Ladder

- [ ] Prior-year finish baseline.
- [ ] Opportunity-only baseline.
- [ ] Position-only naive baseline.
- [ ] Age-adjusted dynasty baseline if source-safe.
- [ ] Current-formula-family proxy baseline.
- [ ] Exact current formula replay baseline only after receipt chain is complete.

## Required Metrics

- [ ] MAE by overall and position.
- [ ] Spearman by overall and position.
- [ ] Top-12, Top-24, and Top-36 hit rate where position-appropriate.
- [ ] Startable precision.
- [ ] Cutline harm count.
- [ ] False-positive and false-negative buckets.
- [ ] Season-level stability.
- [ ] Archetype-level stability.
- [ ] Missingness sensitivity.

## Stop Conditions

- [ ] Any source-truth promotion would be required.
- [ ] Any candidate needs unadmitted stats.
- [ ] Exact current formula replay is claimed without receipts.
- [ ] Candidate outputs would touch production rankings or app behavior.
- [ ] Market/projection/display fields leak into private-value features.
- [ ] Future-season data leaks into feature rows.

## Current Setup-Lane Status

`WAITING_FOR_MORE_STATS_AND_DATA`

This setup lane does not satisfy the checklist. It only defines it.
