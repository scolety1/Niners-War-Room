# Medium Review-Only Formula Pilot Contract V1 Report

## Verdict

`GREEN_MEDIUM_FORMULA_PILOT_CONTRACT_READY`

## Clear Answer

The medium review-only formula pilot contract is ready because the small pilot found predeclared two-year and three-year weighted production variants that beat PYF overall and by position, while role archetype and age/lifecycle remained useful as guardrail and miss-taxonomy context. This contract expands around that evidence with `40` fixed candidates and does not approve Formula Gauntlet, champion refinement, rankings integration, production/model-use, source promotion, or exact Model v4 replay.

## Pilot Scope

- Seasons: `2013-2025`
- Positions: QB/RB/WR/TE
- Expected row count: around `5,518`
- Row grain: `player_id + season + position`
- Output status: review-only artifacts only
- Runtime/app/ranking/model behavior: unchanged
- Required baseline: PYF / prior-year points
- Candidate cap: `40` fixed candidates, below the maximum `45`

## Basis For Expansion

The accepted small pilot found:

- PYF overall Spearman: `0.741`
- two-year weighted production Spearman: `0.753`
- three-year weighted production Spearman: `0.754`
- best overall: `PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10`
- best WR candidate: `PILOT_002_TWO_YEAR_WEIGHTED_PRODUCTION_70_30`
- sparse-history rows: `1,453`, startable rate `3.3%`
- low-games rows: `1,453`, startable rate `3.3%`

## Candidate Families Included

- PYF anchor and simple one-year baselines.
- two-year weighted production variants around `70/30`.
- three-year weighted production variants around `60/30/10`.
- position-specific fixed variants for QB/RB/WR/TE.
- sparse-history and low-games guarded variants.
- prior-production decline guard diagnostics.
- age/lifecycle context diagnostics.
- role-archetype slice diagnostics.

Narrow RB broken-tackle context is not included as an executable candidate because it is not joined to the current Formula Data Mart and remains conditional review-only context only.

## Blocked Families

The contract blocks 100-candidate Gauntlet, champion refinement, optimized weights, ML training, hidden sort, recommendation logic, route/YPRR/TPRR, return scoring, red zone beyond partial caveated context, broad PFR, PFR QB passing production use, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, production Model v4 replay, exact historical replay claims, and current/future context.

## Recommended Next Lane

Recommended next lane: `Medium Review-Only Formula Pilot V1`.

That lane may execute only the fixed candidates, metrics, input gates, advancement rules, and stop conditions in this packet. It must not run 100 candidates, optimize dynamically, tune after seeing results, select winners, alter rankings, or approve production/model-use.

## Current Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Gauntlet remains blocked.
- Champion refinement remains blocked.
- Exact Model v4 replay remains blocked.
- No source promotion is approved.
