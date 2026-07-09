# ESPN, NGS, and nflverse Route Blockers V2B

## ESPN Receiver Scores

References:

- https://espnanalytics.com/receivers
- https://nfl-player-metrics.s3.amazonaws.com/rtm/rtm_data.json
- https://disneytermsofuse.com/english/

The public ESPN Receiver Scores page evaluates receiver route performance and displays routes and yards per route. The public client object behind the surface contains `rtm_routes`, `rtm_targets`, `yds`, `gsis_id`, `dot_com_id`, `position`, team, and season-range fields. Schema probes found seasons 2017-2025 and positions FB/RB/TE/WR.

Why it is not green:

- The object is not documented as a public data feed or API.
- Disney terms restrict automated extraction and dataset/database creation without permission.
- Row grain includes individual-season and combined-season style rows that require filtering.
- Eligibility thresholds mean it is not necessarily complete for all low-volume pass catchers.

Classification: `YELLOW_ROUTE_DENOMINATOR_LEAD`.

## NFL Next Gen Stats Route Recognition

Reference:

- https://www.nfl.com/news/next-gen-stats-intro-to-new-route-recognition-model

NFL NGS route recognition confirms that internal route-classification data exists for eligible route runners, including WR, TE, and RB route runners. Public material is methodology and sample article tables. No public player-level route-count table, downloadable file, durable API, or licensing path was found.

Classification: `RED_ROUTE_DENOMINATOR_BLOCKED`.

## nflverse Participation

References:

- https://nflreadr.nflverse.com/reference/load_participation.html
- https://nflreadr.nflverse.com/articles/dictionary_participation.html

nflverse participation is public, reproducible, package-backed, and ID-safe. It is still not a route denominator source. The dictionary defines `route` as the primary receiver route on a play. It does not count every eligible route runner's route on each pass play and cannot produce player-level full `routes_run`.

Classification: `PROXY_ONLY_NOT_TRUE_ROUTES`.

## nflverse Next Gen Stats Receiving Aggregates

References:

- https://nflreadr.nflverse.com/reference/load_nextgen_stats.html
- https://nflreadr.nflverse.com/articles/dictionary_nextgen_stats.html

nflverse NGS receiving aggregates provide useful player receiving context such as targets, receptions, yards, separation/cushion-style fields, and air-yard-style fields depending on the dictionary. No `routes_run` denominator was found in the documented receiving dictionary.

Classification: `RED_ROUTE_DENOMINATOR_BLOCKED`.

## nflverse FTN Public Subset

Reference:

- https://nflreadr.nflverse.com/reference/load_ftn_charting.html

The public FTN subset through nflverse is reproducible and useful for public charting fields, but it does not expose route denominators. Commercial FTN may contain richer charting, but commercial FTN is blocked by this lane's hard rules unless separately licensed and admitted.

Classification: `RED_ROUTE_DENOMINATOR_BLOCKED`.

## Package-Family Conclusion

nflverse remains the best public identity-safe ecosystem for many NFL data products, but it does not currently solve true `routes_run`. Participation, snaps, team pass attempts, targets, and primary-receiver route labels must remain proxies or context, not route denominators.
