# Mock Draft Manual Column Mapping Packet

## Purpose

Use this packet when real CSV headers do not exactly match the Mock Draft input
schemas. Mapping is review-only and must not run simulations, create draft
outputs, or commit real files.

## Common Safe Aliases

- `player`, `player_name`, `name` -> `player`
- `asset_id`, `player_id` -> `asset_id`
- `pos` -> `position`
- `team` -> `nfl_team`
- `adp`, `market_adp`, `overall_adp` -> `market_adp_pick` for market context only
- `nwr_score`, `nwr_value`, `private_score` -> `nwr_private_value` for NWR private value only

## Must Stay Separate

- ADP, market rank, market value, availability curve, and pick-timing fields are
  opponent behavior only.
- NWR private value, NWR quality score, private score, and WAR-style value fields
  are NWR private value only.
- Ambiguous names such as `value`, `score`, `rank`, or `rating` require manual
  mapping notes before validation.

## Invalid Mappings

- Mapping `adp` or `market_adp` into `nwr_private_value`.
- Mapping `nwr_score` or `private_score` into market behavior context.
- Combining market behavior and NWR private value in one committed fixture unless
  the fixture is explicitly adversarial and expected to fail.

## Future Mapping Prompt

```text
Validate these Mock Draft CSV headers read-only. Do not run simulations, do not
copy real data, and do not commit real files. Use the Mock Draft header alias
contract to propose canonical mappings. Keep ADP/market behavior separate from
NWR private value. Report unresolved mappings and GREEN/YELLOW/RED readiness.
```

No simulation may run until mappings and input contracts validate.
