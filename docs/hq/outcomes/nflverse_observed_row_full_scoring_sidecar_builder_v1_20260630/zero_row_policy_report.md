# Zero Row Policy Report

## Policy

Explicit zero rows may be emitted only when an observed source row exists and the source value is explicitly numeric zero. Missing player-week rows are never zero.

## V1 implementation

Compact V1 emits explicit zero rows for composite blocker components only:

- `fumbles_lost`
- `return_yards`
- `return_or_special_touchdowns`

Explicit zero rows created: `35,106`

Direct component zero expansion remains blocked for compact V1. This means omitted direct zero component rows must be treated as `Not enough information` by future parity code unless a later zero-expanded artifact is approved.
