# Routes Run Legal and Reproducibility Blockers V1

## Summary

Both SumerSports and ESPN expose route-denominator signals. Neither currently provides a permission-safe, documented public data feed that NWR can admit.

## Sumer Blockers

Primary references:

- https://sumersports.com/terms-of-service/
- https://sumersports.com/end-user-license-agreement/

Observed blockers:

- Sumer owns the Sumer Platform content and retains rights except where expressly authorized.
- Terms restrict copying, publishing, reproducing, distributing, creating derivative works, displaying, or otherwise exploiting Sumer content without authorization.
- Terms restrict robots, spiders, automated retrieval, scraping, copying, indexing, mining, and reverse engineering unless expressly permitted.
- No route data API, bulk export, static data product, or route feed license was found.
- RB route fields appear in payload only, which raises support/intent risk.

Sumer hardening status: `YELLOW_ROUTE_DENOMINATOR_LEAD`.

## ESPN Blockers

Primary references:

- https://espnanalytics.com/receivers
- https://nfl-player-metrics.s3.amazonaws.com/rtm/rtm_data.json
- https://disneytermsofuse.com/english/

Observed blockers:

- Disney terms grant limited personal/noncommercial use.
- Disney terms restrict copying, automated extraction, data mining, scraping, and compiling/building datasets or databases without express permission.
- The S3 object is a public client artifact but not a documented public data product/API.
- The object mixes individual-season-like rows and combined-season-like rows.
- Eligibility thresholds exclude some low-volume players.

ESPN hardening status: `YELLOW_ROUTE_DENOMINATOR_LEAD`.

## Non-Admissibility Statement

This lane does not admit Sumer or ESPN as source truth. It does not approve production routes, YPRR, TPRR, model inputs, ranking changes, UI display, hidden sorting, recommendations, verdicts, or boosts.

## What Would Convert a Lead Into a Candidate

A future source-admission lane would need:

1. Written provider permission or public license.
2. Documented export/API/feed path.
3. Field dictionary and row-grain definition.
4. Stable identity fields with NWR crosswalk.
5. Season/position/team coverage table.
6. Missingness and eligibility audit.
7. Confirmation that data can be retained and reproduced by NWR.
8. Explicit use gate before any production route/YPRR/TPRR use.
