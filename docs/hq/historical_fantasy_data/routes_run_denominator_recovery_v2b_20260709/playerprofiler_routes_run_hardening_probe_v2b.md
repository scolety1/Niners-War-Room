# PlayerProfiler Routes Run Hardening Probe V2B

## Scope

Public examples inspected:

- https://www.playerprofiler.com/nfl/javonte-williams/
- https://www.playerprofiler.com/nfl/travis-etienne/
- https://www.playerprofiler.com/nfl/george-kittle/
- https://www.playerprofiler.com/fantasy-football-stats/
- https://www.playerprofiler.com/terms-of-use/

This probe focused on whether PlayerProfiler can recover RB routes_run if Sumer remains WR/TE-visible and RB-hidden.

## Public Page Findings

Public individual player pages display route-adjacent and route-denominator fields, including:

- `Routes Run`
- `Route Participation`
- `Route %`
- `Yards Per Route Run`
- `First Downs Per Route Run` on some WR/TE pages
- weekly `Routes` tables on some pages

RB examples make PlayerProfiler a useful route-denominator lead for running backs. The public pages demonstrate that PlayerProfiler has route data at the player level.

## Export and Reproducibility Findings

No permission-safe public aggregate export was found. The Data Analysis surface advertises export workflows, but that surface is a paid/subscription analytics product. The lane hard blockers explicitly exclude paid PlayerProfiler exports unless a separate licensed source-admission lane approves them.

Public pages are manually reachable, but a reproducible NWR source cannot be based on scraping individual pages. There is no admitted public endpoint, no documented bulk file, no clear player ID contract for NWR joins, and no measured coverage/missingness.

## Terms and Licensing Risk

PlayerProfiler terms prohibit copying, capturing, scraping, aggregation, republishing, transfer, sharing, distribution, and exploitation of content without authorization. This blocks use of public page content as a dataset source in this lane.

## Classification

Public individual pages: `YELLOW_ROUTE_DENOMINATOR_LEAD`
Paid Data Analysis/export surfaces: `RED_ROUTE_DENOMINATOR_BLOCKED`

## Required Hardening Before Admission

1. Provider permission or license for bulk route-count use.
2. Non-paywalled or expressly licensed export/API path.
3. Field dictionary for routes, route participation, YPRR, and weekly route fields.
4. Stable player ID field and crosswalk to NWR canonical IDs.
5. Season, week, team, and game key documentation where applicable.
6. Missingness/coverage audit by position, season, and player.
7. Confirmation that no scraping or page aggregation is required.
