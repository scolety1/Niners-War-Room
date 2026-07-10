# Medium Review-Only Formula Pilot V1 Report

## Verdict

`GREEN_MEDIUM_FORMULA_PILOT_FOUND_STRONG_REVIEW_ONLY_CANDIDATES`

## Clear Answer

The medium review-only formula pilot ran exactly `40` approved candidates against `5518` review-only player-season rows. `25` rank-changing candidate(s) beat PYF overall by Spearman, and `88` candidate-position result(s) beat PYF by position. The strongest family remained fixed multi-year weighted production. Role archetype and age/lifecycle remained useful for slice reporting and guardrail context, not as production ranking inputs.

## Benchmark Scope

- Rows tested: `5518`
- Seasons: `2013-2025`
- Positions: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Candidates tested: `40`
- Review-only rows: `5518`
- Model-use allowed rows: `0`
- Production-approved rows: `0`
- Sparse-history rows: `1453`
- Low-games rows: `1453`
- Missing age/lifecycle rows: `8`

## Best Overall Review-Only Candidate

`MEDIUM_009_THREE_YEAR_70_20_10` produced Spearman `0.754` versus comparable PYF `0.741`.

## Best Candidate By Position

- QB: `MEDIUM_012_THREE_YEAR_55_30_15` with Spearman `0.736` versus PYF `0.712`.
- RB: `MEDIUM_011_THREE_YEAR_60_30_10` with Spearman `0.651` versus PYF `0.633`.
- WR: `MEDIUM_010_THREE_YEAR_65_25_10` with Spearman `0.703` versus PYF `0.691`.
- TE: `MEDIUM_009_THREE_YEAR_70_20_10` with Spearman `0.719` versus PYF `0.701`.

## PYF Comparison

- PYF overall Spearman: `0.741`
- PYF startable precision: `52.1%`
- Rank-changing candidates beating PYF overall: `25`
- Candidate-position results beating PYF: `88`
- Context-only diagnostic candidates: `12`

## Guardrail Findings

- Sparse-history rows: `1453` with startable rate `3.3%`.
- Low-games rows: `1453` with startable rate `3.3%`.
- High-volume role rows contained `469` PYF false positives.
- Low/sparse role rows contained `54` PYF false negatives.
- Older/late lifecycle rows contained `76` PYF false positives.
- Young/early lifecycle rows contained `190` PYF false negatives.

## Interpretation

This pilot does not approve a formula winner, production model, ranking input, hidden sort, or app behavior change. It shows that simple fixed multi-year production variants remain the best near-term review-only direction. Age/lifecycle and role archetype are useful because they explain where PYF and multi-year production miss, especially older prior-production decline and young/early breakout-window rows.

## Recommendation

Recommended next lane: `Focused 60-80 Candidate Review-Only Gauntlet Contract V1`.

Master HQ should only consider a focused review-only expansion if it remains fixed, predeclared, source-gated, and explicitly non-production. The 100-candidate Gauntlet, champion refinement, rankings integration, and production/model-use remain blocked.
