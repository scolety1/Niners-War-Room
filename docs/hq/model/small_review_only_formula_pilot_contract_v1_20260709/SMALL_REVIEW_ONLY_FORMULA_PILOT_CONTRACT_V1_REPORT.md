# Small Review-Only Formula Pilot Contract V1 Report

## Verdict

`GREEN_SMALL_FORMULA_PILOT_CONTRACT_READY`

## Clear Answer

The small review-only formula pilot contract is ready because the available Formula Data Mart can support a limited, auditable player-season pilot using PYF as the mandatory anchor plus review-only age/lifecycle and role-archetype context. It does not clear Formula Gauntlet, 100-candidate runs, champion refinement, rankings integration, production/model-use, or exact Model v4 historical replay.

## Scope

- Seasons: `2013-2025`
- Positions: QB/RB/WR/TE
- Expected row grain: `player_id + season + position`
- Expected row count: around `5,518`
- Outputs: review-only benchmark artifacts and diagnostics only
- Required baseline: PYF / prior-year points
- Allowed context: role archetype, age/lifecycle, sparse-history and low-games flags, confidence cap as caution/coverage context only

## Allowed Pilot Shape

This contract permits up to `15` candidate definitions. The candidates are intentionally simple and interpretable. They are not a Formula Gauntlet tournament and are not allowed to select production winners.

The pilot may test:

- PYF baseline behavior.
- two-year and three-year weighted production variants with predeclared weights.
- position-scoped PYF reporting variants.
- sparse-history, low-games, prior-decline, age/lifecycle, and role-archetype guarded diagnostics.
- a review-only guardrail stack that explains PYF miss patterns without production implications.

## Blocked Pilot Shape

The pilot may not run 100 candidates, optimize weights, train ML models, select winners, use hidden sort logic, touch rankings, promote sources, use blocked inputs, or claim production/model accuracy.

## Advancement Boundary

A variant may be called `promising review-only` only if it compares against PYF, reports position-level metrics, does not materially worsen sparse-history or low-games slices, improves or clearly contextualizes PYF false positives or false negatives, uses only allowed inputs, and passes leakage/as-of and source/use-gate checks.

No candidate may be production-approved by this pilot.

## Current Gates Preserved

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- Production/model-use remains blocked.
- Confidence cap remains caution/coverage context only.
- Role archetype remains review-only guardrail and miss-taxonomy context only.
- Age/lifecycle remains review-only formula-family context, diagnostic slice, and guarded candidate context only.

## Recommendation

Recommended next lane: `Small Review-Only Formula Pilot V1`.

That next lane should execute only the candidates and metrics in this contract. It should stop immediately if the data mart, PYF baseline, leakage/as-of checks, or use-gate checks cannot be reproduced.
