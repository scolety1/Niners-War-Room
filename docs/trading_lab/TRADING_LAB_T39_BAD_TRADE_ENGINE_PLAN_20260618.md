# Trading Lab T39 Bad Trade Engine Plan - 2026-06-18

## Goal

Generate warning flags from scored fixture packages and fixture context.

## Helpers

- `detect_negative_nwr_edge`
- `detect_unrealistic_market_gap`
- `detect_keeper_damage`
- `detect_drop_pressure_damage`
- `detect_low_opponent_fit`
- `detect_public_market_missing`
- `detect_untouchable_asset_included`
- `build_trade_warnings`

## Guardrails

- Fixture-only warnings.
- No old finance framing.
- No automated actions.
- No real integration claims.

## Validation

Tests cover the major warning categories using fake packages only.
