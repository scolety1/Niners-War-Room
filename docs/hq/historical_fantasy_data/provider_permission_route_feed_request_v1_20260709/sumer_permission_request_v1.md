# SumerSports Permission Request V1

## Goal

Ask SumerSports whether NWR can license or otherwise obtain a permission-safe route denominator feed for NFL WR/TE/RB pass catchers.

## Why Sumer

Canonical hardening found:

- WR public pages visibly expose `Routes Run`, `Targets/Route Run`, and `YPRR`.
- TE public pages visibly expose `Routes Run`, `Targets/Route Run`, and `YPRR`.
- WR/TE/RB public page payloads appear to include `receivingPassRoutesRun`, `receivingTargetsPerRouteRun`, and `receivingYardsPerRouteRun` for 2022-2025.
- RB route fields are payload-only and need provider confirmation.
- `sumerPlayerId` appears in payloads but is not yet crosswalked to NWR identity.

This does not authorize use. It only motivates a permission request.

## Request To Sumer

NWR requests a supported, permission-safe route feed with:

- `receivingPassRoutesRun`
- `receivingTargetsPerRouteRun`
- `receivingYardsPerRouteRun`
- WR/TE/RB coverage
- season grain at minimum
- week/game grain if available
- `sumerPlayerId` and any stable crosswalk fields
- player name, team, season, position
- field dictionary
- historical coverage range
- update cadence
- export/API/static file path
- missingness documentation
- license terms for internal storage, research, and derived metrics

## Questions For Sumer

1. Can SumerSports license or permit use of NFL route denominator data for internal NWR historical fantasy research?
2. Is `receivingPassRoutesRun` the actual player routes-run denominator?
3. Is the field available for WR, TE, and RB?
4. Are RB route fields supported, intentional, and available for export?
5. What historical seasons are available?
6. What row grains are available: season, week, game, play, or other?
7. What player identity fields are included?
8. Is there an official crosswalk from `sumerPlayerId` to GSIS, ESPN ID, or another public/stable ID?
9. What team, season, week, and game fields are included?
10. Is there a documented API, export, or static data delivery path?
11. Are checksums, schema versions, or provenance metadata available?
12. What usage is allowed: internal storage, model research, derived YPRR/TPRR, internal display, production rankings?
13. What raw or derived redistribution restrictions apply?
14. What attribution, deletion, user-seat, or audit obligations apply?

## Minimum Acceptable Sumer Response

Sumer must provide:

- written permission or contract terms
- feed/export/API documentation
- route field dictionary
- WR/TE/RB coverage confirmation
- season/position coverage table
- player identity documentation
- missingness/eligibility notes
- storage and derived-metric rights

## Current Status

`YELLOW_ROUTE_DENOMINATOR_LEAD`

Sumer remains blocked until permission, supported feed path, identity, and coverage gates are cleared.
