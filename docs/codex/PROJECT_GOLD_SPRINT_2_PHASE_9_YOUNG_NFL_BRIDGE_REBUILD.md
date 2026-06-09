# Project Gold Sprint 2 / Phase 9: Young NFL Bridge Rebuild

Date: 2026-05-14

## Scope

This phase rebuilt the young-player lifecycle layer so first-, second-, and third-year NFL players are no longer displayed as one generic bridge bucket.

Rankings remain review-only.

## Changes

Lifecycle labels now separate:

- `incoming_rookie`
- `year_one_nfl_bridge`
- `year_two_nfl_bridge`
- `year_three_nfl_bridge`
- `established_veteran`

The legacy `young_nfl_bridge` value is still treated as part of the young-player bridge family for older fixtures, tests, and audit imports, but newly derived preview rows use the year-specific labels.

## Receipt Fix

The `young_nfl_bridge_nfl_evidence_weight` receipt row now displays the actual NFL evidence strength from the bridge service, not the leftover NFL blend share after the prior weight is applied.

This makes the bridge receipt clearer:

- draft/prospect prior score
- bridge decay weight
- NFL evidence strength
- final bridge contribution

## Regenerated Preview

Generated preview:

`local_exports/nflverse_model_previews/sprint2_phase9_young_bridge_20260514`

Mirrored active receipt source:

`local_exports/active_veteran_model_public_sources`

Preview counts:

- Total rows: 1,039
- Established veterans: 634
- Year-one NFL bridge: 145
- Year-two NFL bridge: 128
- Year-three NFL bridge: 132
- Bridge evidence receipt rows: 405

## Guardrails

No player was blindly boosted.

No formulas were tuned to match opinions.

Draft/prospect prior remains an uncertainty bridge:

- strongest before/early in NFL evidence
- reduced as real production, role, usage, confidence, and source coverage improve
- removed for established veterans

## Remaining Trust Notes

The bridge layer is now more inspectable, but the model is still review-only. The next trust work should keep focusing on:

- role/usage truth
- source coverage quality
- named player sanity fixtures
- RB/WR cross-position balance
- whether any young-player bridge contribution is too dominant for players with weak NFL evidence

