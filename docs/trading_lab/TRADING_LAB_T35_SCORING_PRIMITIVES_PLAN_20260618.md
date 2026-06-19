# Trading Lab T35 Scoring Primitives Plan - 2026-06-18

## Goal

Add pure scoring primitives for fixture-backed fantasy trade packages.

## Rules

- NWR private value stays separate from public fantasy market value.
- Public fantasy market value never overwrites NWR value.
- Scores are manual review labels, not automatic actions.
- No real data imports.
- No broad app integration.

## Helpers

- `calculate_nwr_delta`
- `calculate_public_market_delta`
- `score_market_fairness`
- `score_opponent_fit`
- `score_roster_impact`
- `score_keeper_drop_impact`
- `score_risk`
- `build_package_score`
- `build_review_verdict`

## Validation

Tests cover fake value math, value separation, market-fair/negative-NWR cases, unrealistic cases, and no submission language.
