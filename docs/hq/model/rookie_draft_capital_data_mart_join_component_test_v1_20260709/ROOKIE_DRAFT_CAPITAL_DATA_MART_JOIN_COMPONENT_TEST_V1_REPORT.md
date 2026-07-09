# Rookie Draft Capital Data Mart Join / Component Test V1 Report

Verdict: `YELLOW_ROOKIE_DRAFT_CAPITAL_PARTIAL_WITH_CAVEATS`

Artifact path: `C:\NWR\Niners-War-Room-rookie-draft-capital-data-mart-join-component-test-v1-20260709\docs\hq\model\rookie_draft_capital_data_mart_join_component_test_v1_20260709`

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

Prior market/ADP commit verified: `ee4c1505008bfead024aa326fb07155297491d91`

## Executive Summary

Positive draft-capital evidence was found and joined as a review-only sidecar. The source/use and identity gates pass only for positive drafted-player evidence sourced through the prior nflverse draft-pick admission packets. Missing draft evidence is not treated as UDFA, fake round 8 remains blocked, CFBD/prospect production remains blocked, and the sidecar is not production/model-use.

Sidecar rows: `5518`

Positive draft-evidence joined rows: `4044` / `5518` (`73.3%`)

Source/use safe review-only source rows: `6`

Cluster-seed formulas tested: `18` fixed candidates from the seven Gauntlet clusters where available.

## Best Results

- Best component: `INGREDIENT_ONLY_EARLY_CAREER_DRAFT_SCORE`: Spearman `0.534` vs PYF `0.709`
- Best formula x ingredient: `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_DRAFT_OVERALL_PCT050`: Spearman `0.740`, formula-alone `0.738`, PYF `0.722`
- Best ingredient combination: `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_DRAFT_AGE_EARLY_PCT050_050`: Spearman `0.744`, formula-alone `0.738`, PYF `0.722`

These results are positive-draft-evidence subset results, not full-history-comparable plateau claims. No result justifies review-only ranking simulation.

## Gate Decision

- Source/identity gate passed: `yes_for_positive_drafted_review_only_rows`
- Sidecar built: `yes`
- Component tests run: `yes`
- Formula x ingredient tests run: `yes`
- Ingredient combination tests run: `yes_bounded_review_only`
- Full-history-comparable plateau break: `no`
- Snap/depth `.763` comparable break: `no`

## Preserved Blocks

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior remains unchanged.
- Push/merge was not performed.
- Source promotion was not performed.
- Canonical `local_exports` was not mutated.
- CFBD, combine/prospect production, and UDFA inference remain blocked.
