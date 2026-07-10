# Formula Results Master Review / Data Upgrade Pivot V1 Report

## Verdict

`GREEN_FORMULA_RESULTS_PLATEAU_CONFIRMED_DATA_UPGRADE_NEXT`

## Clear Answer

The current review-only formula family improved beyond PYF but has plateaued with the available ingredients. The best refined candidate, `REFINE_007_OVERALL_THREE_65_25_10_LATE_20`, reached Spearman `0.755` versus PYF `0.741`, but did not beat the prior full-Gauntlet best reference `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE` at Spearman `0.755`. More same-ingredient weight tweaking should pause until new or better data enters the Formula Data Mart.

## Current Best References

- PYF baseline: `0.741`
- Best small pilot: `PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10` Spearman `0.754`
- Best medium pilot: `MEDIUM_011_THREE_YEAR_60_30_10` Spearman `0.754`
- Best full Gauntlet: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE` Spearman `0.755`
- Best refinement: `REFINE_007_OVERALL_THREE_65_25_10_LATE_20` Spearman `0.755`

## Plateau Decision

- Refinement beat PYF: yes.
- Refinement beat prior Gauntlet best: no.
- Seed neighborhoods materially improved: no.
- Top candidates are small variants of multi-year production plus age/role/decline context.
- Further same-ingredient refinement is blocked for now.

## Top Data Upgrade

Recommended next execution lane:

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

Rationale: the narrow PFR RB broken-tackle hypothesis was preserved as review-only, but the values were absent from the Formula Data Mart, so Gauntlet could not score that branch. This is the most direct next test of a missing feature that might add non-duplicate RB context. It remains RB-only, review-only, non-production, and must keep PFF/proxy/broad-PFR uses blocked.

## Gates

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior remains unchanged.
- No current formula is a production winner.
- No source is promoted by this packet.
