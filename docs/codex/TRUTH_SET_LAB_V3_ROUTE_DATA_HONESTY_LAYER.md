# Truth Set Lab v3 Phase 5: Route Data Honesty Layer

## Status

The route-data honesty layer is implemented as a review-only guardrail. It does
not change active rankings, active data packs, model formulas, or readiness
gates. It prevents current route defaults and proxies from being described as
real route evidence.

## What Is Now Explicitly Unavailable

The current free/public structured source stack does not provide safe true:

- routes run
- route participation
- targets per route run
- yards per route run

Those fields are now labeled with one of:

- `unavailable_free_public`
- `missing_paid_or_charted_data`
- `proxy_only_snap_target`

## Generated v3 Reports

| output | path |
|---|---|
| route honesty rows | `local_exports/truth_set_lab/v3/reports/truth_set_v3_route_data_honesty.csv` |
| summary CSV | `local_exports/truth_set_lab/v3/reports/truth_set_v3_route_data_honesty_summary.csv` |
| summary JSON | `local_exports/truth_set_lab/v3/reports/truth_set_v3_route_data_honesty_summary.json` |

## Model Truth Contract Changes

`route_role` is no longer treated as derived real route data. It is classified as:

- `unavailable_free_public` when the row is a missing/default route value,
- `missing_paid_or_charted_data` when the role bucket has no useful route input,
- `proxy_only_snap_target` when a non-default route-like value exists without a
  true legal route denominator.

This means neutral/default route values can show in receipts as imputed or proxy
context, but not as imported football evidence.

## Source Coverage And Receipts

Source coverage now treats route-dependent WR/TE role rows as review/proxy when
route evidence is unavailable or defaulted. Player receipts show route-related
rows with the route honesty source status instead of implying that route data was
imported.

## Still Allowed

The model can continue to use these as public/free role context:

- snap share
- target share
- targets per game
- air-yards share

But they must remain labeled as proxy/context, not routes run, route
participation, TPRR, or YPRR.

## Safety

- Active rankings overwritten: false
- Model scores changed: false
- Readiness labels changed: false
- Review-only status retained: true
