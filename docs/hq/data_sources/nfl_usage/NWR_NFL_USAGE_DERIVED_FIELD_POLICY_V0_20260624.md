# NFL Usage Derived Field Policy V0

## Status

Research-only. Derived fields are not model inputs and are not app-wired in V0.

## Formulas

- `touches = carries + receptions`
- `opportunities = carries + targets`
- `red_zone_carries = carries where yardline_100 <= 20`
- `red_zone_targets = targets where yardline_100 <= 20`
- `red_zone_touches = red_zone_carries + red-zone receptions when available; otherwise proxy from red_zone_targets capped by receptions`
- `inside_10_carries = carries where yardline_100 <= 10`
- `inside_10_targets = targets where yardline_100 <= 10`
- `inside_10_touches = inside_10_carries + inside-10 receptions when available; otherwise proxy from inside_10_targets capped by receptions`
- `inside_5_carries = carries where yardline_100 <= 5`
- `inside_5_targets = targets where yardline_100 <= 5`
- `inside_5_touches = inside_5_carries + inside-5 receptions when available; otherwise proxy from inside_5_targets capped by receptions`
- `rushing_first_downs = count of player rushes with rush first-down flag`
- `receiving_first_downs = count of player targets/receptions with pass first-down flag`
- `first_downs_per_touch = (rushing_first_downs + receiving_first_downs) / touches`
- `red_zone_share = player red-zone carries plus targets / team-week red-zone carries plus targets`
- `inside_10_share = player inside-10 carries plus targets / team-week inside-10 carries plus targets`
- `inside_5_share = player inside-5 carries plus targets / team-week inside-5 carries plus targets`

## Labels

Counts from public play facts are `TRUE_DERIVED_FACT` when required fields are present. Share/rate fields are `DERIVED_PROXY` until backtested and promoted. Any field using a proxy denominator must say proxy in its name or notes.
