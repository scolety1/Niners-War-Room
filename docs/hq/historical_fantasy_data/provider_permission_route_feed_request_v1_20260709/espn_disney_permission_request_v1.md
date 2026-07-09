# ESPN / Disney Permission Request V1

## Goal

Ask ESPN, Disney, or ESPN Analytics whether NWR can license or obtain permission-safe access to receiver tracking denominator data, including `rtm_routes`.

## Why ESPN

Canonical hardening found ESPN Receiver Scores to be the strongest identity-shaped lead:

- public Receiver Scores page displays routes and yards per route
- public client object exposes `rtm_routes`, `rtm_targets`, `yds`, `gsis_id`, `dot_com_id`, `tm`, `position`, and season-range fields
- observed seasons: 2017-2025
- observed positions: FB, RB, TE, WR
- missing `gsis_id`: 0 in schema-only probe
- missing `dot_com_id`: 0 in schema-only probe

This does not authorize use. The client object is undocumented and Disney terms block dataset extraction without permission.

## Request To ESPN / Disney

NWR requests a supported, permission-safe receiver tracking metrics feed with:

- `rtm_routes` or equivalent actual routes-run denominator
- WR/TE/RB coverage
- season grain at minimum
- week/game grain if available
- `gsis_id`
- `dot_com_id`
- player name, team, season, position
- field dictionary
- historical coverage range
- row-grain definitions
- eligibility threshold documentation
- missingness documentation
- reproducible API/export/static file path
- license terms for internal storage, research, derived metrics, and any display

## Questions For ESPN / Disney

1. Can ESPN/Disney license or permit NWR use of Receiver Scores route denominator data?
2. Is `rtm_routes` an actual routes-run count?
3. What rows are official player-season rows versus combined-season or leaderboard rows?
4. Are WR, TE, and RB all supported?
5. Is FB included or separable?
6. What historical seasons are available?
7. Is week/game grain available?
8. What player IDs are official: GSIS, ESPN dot-com ID, or another key?
9. What field dictionary is available for `rtm_routes`, `rtm_targets`, `yds`, score fields, and season fields?
10. What eligibility thresholds apply by year and position?
11. What low-volume players are excluded?
12. Is there a documented API, export, or paid feed rather than an undocumented client object?
13. Are checksums, schema versions, update timestamps, or provenance metadata available?
14. What usage is allowed: internal storage, model research, derived YPRR/TPRR, internal display, production rankings?
15. What raw or derived redistribution restrictions apply?

## Minimum Acceptable ESPN Response

ESPN/Disney must provide:

- written permission or contract terms
- supported feed/export/API documentation
- route field dictionary
- row-grain separation rules
- season/position/eligibility coverage table
- GSIS/dot-com identity documentation
- missingness notes
- storage and derived-metric rights

## Current Status

`YELLOW_ROUTE_DENOMINATOR_LEAD`

ESPN remains blocked until permission, feed documentation, row-grain, eligibility/missingness, and allowed-use gates are cleared.
