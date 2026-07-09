# Gauntlet Candidate Diversity / Clustering Audit V1 Report

## Verdict

`GREEN_GAUNTLET_HAS_DIVERSE_PROMISING_NEIGHBORHOODS`

## Clear Answer

The Gauntlet results are promising but meaningfully clustered. The headline `90` formulas beating PYF does not represent 90 independent signals. The scored candidates collapse into `7` output-correlation neighborhoods, with `6` genuinely distinct promising clusters and an effective independent candidate count of `6`. The top candidates are highly clustered around multi-year production, with small age/lifecycle, role, and decline-context modifiers.

## Candidate Inventory

- Raw candidates registered: `120`
- Scored candidates: `114`
- Score-changing candidates beating PYF overall: `90`
- Output-correlation clusters: `7`
- Promising clusters: `6`
- Genuinely distinct promising clusters: `6`
- Effective independent candidate count: `6`
- Near-duplicate output pairs at correlation >= `0.995`: `1649`
- Same-neighborhood pairs at correlation >= `0.98`: `2749`
- Near-top candidates within 0.001 Spearman of best: `21`

## Interpretation

The result is not "90 independent formulas beat PYF." It is better read as a smaller number of stable formula neighborhoods beating PYF, led by three-year weighted production and nearby production-plus-context variants. Position-specific candidates are useful as distinct refinement seeds because their scope differs, even when their underlying scoring behavior remains production-centered.

## Refinement Decision

`READY_FOR_DIVERSE_CHAMPION_REFINEMENT`

Champion refinement is justified only as review-only contract work around diverse seeds, not as production selection. The next lane should refine top neighborhoods deliberately, not simply clone the top 0.755 Spearman variants.

## Recommended Refinement Seeds

- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE` (`H_PRIOR_PRODUCTION_DECLINE_GUARD`): best_overall_cluster_representative
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE` (`K_HYBRID_PRODUCTION_AGE_ROLE`): top_distinct_cluster_backfill
- `GAUNTLET_039_QB_THREE_55_30_15` (`E_POSITION_SPECIFIC_PRODUCTION`): top_distinct_cluster_backfill
- `GAUNTLET_057_TE_THREE_75_20_5` (`E_POSITION_SPECIFIC_PRODUCTION`): top_distinct_cluster_backfill
- `GAUNTLET_051_WR_THREE_65_25_10` (`E_POSITION_SPECIFIC_PRODUCTION`): top_distinct_cluster_backfill
- `GAUNTLET_093_ROLE_RB_TOUCH_ROLE_REPORT` (`J_ROLE_ARCHETYPE_CONTEXT`): top_distinct_cluster_backfill

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Source promotion remains blocked.
- No app/runtime/model behavior changed.
- No champion refinement was run in this lane.
