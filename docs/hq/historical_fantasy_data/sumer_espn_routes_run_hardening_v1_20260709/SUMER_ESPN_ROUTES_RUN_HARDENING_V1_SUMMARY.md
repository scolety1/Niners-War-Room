# Sumer/ESPN Routes Run Hardening V1 Summary

Lane: Sumer/ESPN Routes Run Permission, API, Export, Identity-Crosswalk Hardening V1
Artifact date: 2026-07-09
Worktree: `C:\NWR\Niners-War-Room-sumer-espn-routes-run-hardening-v1-20260709`
Branch: `work/lane-sumer-espn-routes-run-hardening-v1-20260709`
Verified base: `origin/work/hq-parallel-control` at `a7364d74edadbb08d011496ec08acbbbb2e8c052`

## Verdict

`YELLOW_ROUTE_DENOMINATOR_LEADS_REMAIN_BLOCKED`

No source reached `GREEN_ROUTE_DENOMINATOR_CANDIDATE`.

This hardening lane confirms that SumerSports and ESPN Receiver Scores are the strongest public route-denominator leads currently known to NWR, but neither can become an approved future-admission candidate without provider permission or a documented public license/export/API path.

## Preserved V2B Context

Canonical V2B packet:

- `docs/hq/historical_fantasy_data/routes_run_denominator_recovery_v2b_20260709/`

Preserved V2B result:

- Full route denominator GREEN candidates: 0.
- WR/TE route denominator lead rows: 5.
- RB route denominator lead rows: 4.
- Blocked/proprietary/no-feed rows: 8.
- Proxy fallback metrics: 8.
- True routes/YPRR/TPRR remain blocked for production.

## Sumer Result

SumerSports public pages were checked at:

- https://sumersports.com/players/wide-receiver/
- https://sumersports.com/players/tight-end/
- https://sumersports.com/players/running-back/
- https://sumersports.com/terms-of-service/
- https://sumersports.com/end-user-license-agreement/

WR and TE pages visibly expose `Routes Run`, `Targets/Route Run`, and `YPRR`. Schema-only page probes found route-count-like fields for WR/TE/RB in 2022-2025:

- `sumerPlayerId`
- `receivingPassRoutesRun`
- `receivingTargetsPerRouteRun`
- `receivingYardsPerRouteRun`

RB route fields remain payload-only in the public page surface. The visible RB table did not expose `Routes Run`, `Targets/Route Run`, or `YPRR`.

Sumer did not reach GREEN because:

- Terms and EULA restrict copying, automated retrieval, scraping, indexing, reuse, and exploitation unless expressly authorized.
- No documented public API or bulk export was found.
- Historical route payload rows were observed only for 2022-2025, not 2017-2021.
- `sumerPlayerId` is promising but not yet crosswalked to NWR canonical identity.
- RB payload fields need provider confirmation that they are supported, intentional, and licensable.

Sumer verdict: `YELLOW_ROUTE_DENOMINATOR_LEAD`.

## ESPN Result

ESPN Receiver Scores public surfaces were checked at:

- https://espnanalytics.com/receivers
- https://nfl-player-metrics.s3.amazonaws.com/rtm/rtm_data.json
- https://disneytermsofuse.com/english/

The ESPN Receiver Scores page displays seasons 2017-2025, WR/TE/RB position filters, and table columns for routes and yards per route. The public client JSON object exposes actual route-denominator fields:

- `rtm_routes`
- `rtm_targets`
- `yds`
- `gsis_id`
- `dot_com_id`
- `tm`
- `position`
- season-range fields

Schema-only probe metadata:

- Rows: 3,554.
- Positions: FB, RB, TE, WR.
- Position row counts: FB 19, RB 906, TE 712, WR 1,917.
- Seasons observed: 2017-2025.
- Missing `gsis_id`: 0.
- Missing `dot_com_id`: 0.
- Missing `rtm_routes`: 0.
- Individual-season-like rows: 1,869.
- Combined-season-like rows: 1,685.

ESPN did not reach GREEN because:

- The S3 object is an undocumented client object, not a documented public data feed.
- Disney terms grant only limited personal/noncommercial use and restrict copying, automated extraction, data mining, and dataset/database creation without express permission.
- Row grain needs hard filtering because individual-season and combined-season rows coexist.
- Eligibility thresholds mean the object is not necessarily a full denominator for all pass catchers.

ESPN verdict: `YELLOW_ROUTE_DENOMINATOR_LEAD`.

## Current Route/YPRR/TPRR Status

True routes/YPRR/TPRR remain blocked for production use. YPRR and TPRR remain derivable only in principle if a future source-admission lane obtains a permitted route denominator source and clears identity, coverage, missingness, and row-grain gates.

## Recommended Next Lane

Run `Provider Permission and Contractable Route Feed Request V1`.

Minimum next-lane outputs:

1. Provider permission memo for SumerSports and ESPN/Disney.
2. Written approval, contract, or documented public license for `routes_run` use.
3. Supported export/API/feed documentation.
4. Field dictionary for Sumer `receivingPassRoutesRun` and ESPN `rtm_routes`.
5. Identity crosswalk proof for Sumer IDs and ESPN GSIS/dot-com IDs.
6. Missingness and eligibility audit by season, position, and row grain.
7. Use gate that keeps all route/YPRR/TPRR outputs blocked unless admission passes.
