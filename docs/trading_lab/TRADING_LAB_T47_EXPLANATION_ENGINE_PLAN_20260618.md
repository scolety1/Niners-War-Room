# Trading Lab T47 Explanation Engine Plan - 2026-06-18

## Goal

Create review-grade explanations for each fixture-backed trade package.

## Helpers

- `explain_nwr_edge`
- `explain_market_fairness`
- `explain_opponent_fit`
- `explain_roster_impact`
- `explain_keeper_drop_impact`
- `explain_risk_flags`
- `build_trade_explanation`

## Guardrails

- Explanations are review notes only.
- Fixture values only.
- No real integrations.
- No automated decisioning or trade submission.

## Validation

Tests cover each explanation section and blocked action language.
