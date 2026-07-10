# Full Review-Only Formula Gauntlet Candidate Arena V1 Report

## Verdict

`GREEN_REVIEW_ONLY_GAUNTLET_FOUND_STRONG_CANDIDATE_NEIGHBORHOODS`

## Clear Answer

The full review-only Formula Gauntlet Candidate Arena registered exactly `120` fixed candidates before scoring. `114` candidates were scored with review-safe Formula Data Mart fields and `6` were blocked/invalid because PFR broken-tackle values or fair full-window red-zone values were not present in the mart. The best neighborhoods remained fixed multi-year production, especially three-year weighted variants. This is a review-only reference benchmark, not production accuracy or rankings integration.

## Benchmark Scope

- Rows tested: `5518`
- Seasons: `2013-2025`
- Positions: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Candidate registry rows: `120`
- Scored candidates: `114`
- Blocked/invalid candidates: `6`
- Candidate families represented: `15`
- Review-only rows: `5518`
- Model-use allowed rows: `0`
- Production-approved rows: `0`

## PYF Baseline

- PYF overall Spearman: `0.741`
- PYF startable precision: `52.1%`

## Best Overall Review-Only Candidate

`GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE` from `H_PRIOR_PRODUCTION_DECLINE_GUARD` produced Spearman `0.755` versus comparable PYF `0.741`.

## Best Candidate By Position

- QB: `GAUNTLET_020_THREE_YEAR_55_30_15` with Spearman `0.736` versus PYF `0.712`.
- RB: `GAUNTLET_109_ROBUST_WINSOR_THREE_60_10` with Spearman `0.652` versus PYF `0.633`.
- WR: `GAUNTLET_016_THREE_YEAR_75_20_5` with Spearman `0.703` versus PYF `0.691`.
- TE: `GAUNTLET_016_THREE_YEAR_75_20_5` with Spearman `0.719` versus PYF `0.701`.

## PYF Comparison

- Score-changing candidates beating PYF overall: `90`
- Candidate-position rows beating PYF: `279`

## Guardrail Findings

- Sparse-history rows: `1453` with startable rate `3.3%`.
- Low-games rows: `1453` with startable rate `3.3%`.
- High-volume role rows contained `469` PYF false positives.
- Low/sparse role rows contained `54` PYF false negatives.
- Older/late lifecycle rows contained `76` PYF false positives.
- Young/early lifecycle rows contained `190` PYF false negatives.

## PFR / Red-Zone Findings

- PFR RB broken tackle candidates were registered but blocked because the Formula Data Mart has only status metadata, not actual `pfr_rush_brk_tkl__raw` or per-game values.
- Red-zone candidates were registered but blocked because available red-zone receipts are partial 2024-2025 lagged review-only context, not a fair 2013-2025 formula input.

## Stability

The stability review uses season-level and leave-one-season-out directional checks. Strong candidates were not driven by a single outlier season when the leave-one-season-out direction remained positive for most omitted seasons. See `GAUNTLET_STABILITY_BY_SEASON.csv` and `GAUNTLET_OUTLIER_INFLUENCE_REVIEW.csv`.

## Recommendation

Recommended next lane: `Champion Refinement Contract V1 around top 3-8 review-only candidates`.

This recommendation is for a contract/design lane only. Production/model-use, rankings integration, app/runtime changes, source promotion, exact replay claims, and final champion selection remain blocked.
