# Formula Next Lane Decision

## Recommended Next Single Lane

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

## Scope

- Join only narrow RB PFR broken-tackle values that are already preserved as review-only hypotheses.
- Test only `pfr_rush_brk_tkl__raw` and `pfr_rush_brk_tkl__per_game` as review-only component context.
- Keep `pfr_rush_brk_tkl__per_attempt` diagnostic only.
- Compare against PYF, multi-year production, rushing volume, sparse-history, and low-games slices.

## Stop Conditions

Stop if source hashes, season coverage, RB identity joins, as-of safety, missingness classification, or Formula Data Mart join integrity cannot be proven.

## Explicitly Not Approved

No broad PFR promotion, no PFR QB passing production use, no PFF Elusive Rating, no `nwr_elusive_proxy_review_only`, no rankings integration, no production/model-use, and no app/runtime changes.
