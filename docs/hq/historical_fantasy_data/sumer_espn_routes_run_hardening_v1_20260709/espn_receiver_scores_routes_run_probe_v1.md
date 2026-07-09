# ESPN Receiver Scores Routes Run Probe V1

## Public Surfaces Checked

- Receiver Scores page: https://espnanalytics.com/receivers
- Public client object: https://nfl-player-metrics.s3.amazonaws.com/rtm/rtm_data.json
- Disney Terms of Use: https://disneytermsofuse.com/english/

This probe used public, non-authenticated surfaces only and recorded schema/count metadata. No raw player rows were copied into the repository.

## Public Page Findings

The ESPN Receiver Scores page describes receiver ratings as route-based and exposes:

- season selector covering 2017-2025
- position filters for WR/TE, WR, TE, and RB
- table columns for receiving yards, routes, targets, and yards per route
- eligibility cutoffs for WR/TE and RB

This page confirms that ESPN's public analytics surface displays an actual routes denominator. It does not by itself provide a documented, licensed bulk feed.

## Client Object Schema Findings

The public client object was reachable without authentication and returned HTTP 200.

Schema metadata observed:

- Last-Modified: Mon, 09 Feb 2026 16:27:08 GMT.
- Content-Length: 1,366,614 bytes.
- ETag: `"b5ad6c6bacad432fc28073422a51a2b2"`.
- Root type: JSON array.
- Rows: 3,554.
- Fields: `gsis_id`, `position`, `tm`, `overall`, `open_score`, `catch_score`, `yac_score`, `rtm_routes`, `rtm_targets`, `min_season`, `max_season`, `min_player_season`, `max_player_season`, `min_rtm_targets`, `dot_com_id`, `first_nm`, `last_nm`, `full_nm`, `yds`.
- Seasons observed: 2017-2025.
- Positions observed: FB, RB, TE, WR.
- Position row counts: FB 19, RB 906, TE 712, WR 1,917.
- Missing `gsis_id`: 0.
- Missing `dot_com_id`: 0.
- Missing `rtm_routes`: 0.
- Missing `rtm_targets`: 0.
- Missing `yds`: 0.
- Individual-season-like rows: 1,869.
- Combined-season-like rows: 1,685.

## Identity Findings

ESPN is the strongest identity lead because the client object contains both:

- `gsis_id`
- `dot_com_id`

If ESPN/Disney permission were obtained, `gsis_id` could likely support a safe NWR identity join. Permission is the key unresolved gate.

## Row-Grain Findings

The client object mixes individual-season-like rows and combined-season-like rows. A future admission lane would need a hard row-grain filter and reconciliation rules before any use:

- select only intended player-season rows for historical fantasy data
- exclude combined-season rows unless separately justified
- preserve eligibility threshold metadata
- measure missing low-volume players by season and position

## Permission and Terms Findings

Disney terms grant limited personal/noncommercial use and restrict copying, automated extraction, data mining, and building datasets/databases without express permission. The public object is an undocumented client artifact, not a documented open data feed.

## Classification

`YELLOW_ROUTE_DENOMINATOR_LEAD`

ESPN has actual route denominator fields, strong identity fields, and 2017-2025 coverage. It does not satisfy the GREEN gate because licensing, documented feed status, row-grain hardening, and eligibility/missingness audit remain unresolved.

## What Would Unblock ESPN

1. ESPN/Disney written permission, documented license, or official data feed terms.
2. Confirmation that `rtm_data.json` or successor feed is stable and intended for external data use.
3. Field dictionary for `rtm_routes`, `rtm_targets`, season fields, and row-grain flags.
4. Eligibility threshold documentation by season/position.
5. Missingness audit against admitted player/receiving universes.
6. NWR GSIS/dot-com identity crosswalk verification.
