# Routes Run Denominator Recovery V2B Summary

Lane: NWR Historical Fantasy Data Lane - Routes Run Denominator Recovery V2B
Artifact date: 2026-07-09
Worktree: `C:\NWR\Niners-War-Room-routes-run-denominator-recovery-v2b-20260709`
Branch: `work/lane-routes-run-denominator-recovery-v2b-20260709`
Verified base: `origin/work/hq-parallel-control` at `4aced300c917d952ae08afcaf927268402423834`

## Verdict

`YELLOW_ROUTES_RUN_DENOMINATOR_LEADS_ONLY`

No source reached `GREEN_ROUTE_DENOMINATOR_CANDIDATE`. The lane did find stronger route-denominator leads than the original route/YPRR/TPRR packet, especially:

- SumerSports WR and TE public stats pages visibly expose `Routes Run`, `Targets/Route Run`, and `YPRR`.
- SumerSports RB public pages do not visibly expose those route columns, but page payload probes found route-count-like receiving fields for 2022-2025.
- ESPN Receiver Scores exposes a public client object with `rtm_routes`, `rtm_targets`, `yds`, ESPN dot-com IDs, GSIS IDs, seasons 2017-2025, and WR/TE/RB/FB positions.
- PlayerProfiler public player pages display route metrics, including RB examples, but no permission-safe aggregate retrieval path was found.

These are leads, not admitted feeds. The hard blockers remain licensing/terms, undocumented client payloads, lack of explicit bulk export permission, identity crosswalk hardening, and missingness/coverage measurement. True routes/YPRR/TPRR remain blocked for production use until a separate source-admission lane obtains a permitted and reproducible source path.

## Search Scope

The lane inspected:

- Canonical HQ route/source context in `docs/hq/deep_research_upgrades/`.
- Prior V1 route/YPRR/TPRR artifacts from the read-only prior worktree `C:\NWR\Niners-War-Room-historical-fantasy-route-yprr-tprr-source-recovery-v1-20260708`.
- Public SumerSports WR, TE, and RB pages plus SumerSports terms.
- Public ESPN Receiver Scores page, public ESPN client JSON object, and Disney terms.
- NFL Next Gen Stats route-recognition methodology pages.
- nflverse, nflreadr, nflfastR, nflreadpy, nflverse-data dictionaries and loaders.
- Public GitHub/Kaggle-like route/tracking leads at a provenance/licensing level.
- Local NWR caches and review roots: this fresh worktree, `C:\NWR_REVIEW`, `C:\NWR_SANDBOX`, and the prior route V1 worktree.
- User-provided formula gauntlet revival handoff zip, extracted only to `C:\NWR_TMP\fgzip` for inspection.

## Source Findings

### SumerSports

References:

- https://sumersports.com/players/wide-receiver/
- https://sumersports.com/players/tight-end/
- https://sumersports.com/players/running-back/
- https://sumersports.com/terms-of-service/

WR and TE pages visibly show `Routes Run`, `Targets/Route Run`, and `YPRR`. Schema-only public page probes found `sumerPlayerId`, `receivingPassRoutesRun`, `receivingTargetsPerRouteRun`, and `receivingYardsPerRouteRun` for 2022-2025. Public page probes for 2017-2021 returned page shells but no route payload rows.

RB pages do not visibly show route columns, but the public page payload contains the same route-count-like receiving fields for 2022-2025. This makes Sumer a stronger RB lead than the visible UI suggests, but still not a green candidate because Sumer terms restrict automated retrieval/copying, no documented public bulk export/API was found, and the Sumer player ID crosswalk into NWR identity has not been admitted.

Classification: `YELLOW_ROUTE_DENOMINATOR_LEAD`.

### ESPN Receiver Scores

References:

- https://espnanalytics.com/receivers
- https://nfl-player-metrics.s3.amazonaws.com/rtm/rtm_data.json
- https://disneytermsofuse.com/english/

The public ESPN Receiver Scores page lists routes and yards per route in the display surface and covers 2017-2025. The public client object contains row-level fields including `gsis_id`, `dot_com_id`, `position`, `tm`, `rtm_routes`, `rtm_targets`, `yds`, and season-range fields. Schema probes found WR, TE, RB, and FB coverage with no missing GSIS or ESPN dot-com IDs in the object.

This is the strongest identity-safe technical lead because GSIS IDs are present. It still cannot be admitted here: the S3 object is an undocumented client artifact, not a documented public data feed, and Disney terms restrict automated extraction and dataset/database creation without permission.

Classification: `YELLOW_ROUTE_DENOMINATOR_LEAD`.

### PlayerProfiler

References:

- https://www.playerprofiler.com/nfl/javonte-williams/
- https://www.playerprofiler.com/nfl/travis-etienne/
- https://www.playerprofiler.com/nfl/george-kittle/
- https://www.playerprofiler.com/fantasy-football-stats/
- https://www.playerprofiler.com/terms-of-use/

Public individual pages display `Routes Run`, `Route Participation`, and `Yards Per Route Run`, including RB examples. Some pages also expose weekly route tables in the rendered public surface. This is valuable as an RB coverage lead because Sumer's RB route data is hidden rather than visible.

No legal, reproducible, non-paywalled aggregate export was found. PlayerProfiler's Data Analysis export is a paid/subscription product, and the terms prohibit copying, scraping, aggregation, republishing, or reuse of content without authorization. Public pages are therefore leads only, not an approved bulk data source.

Classification: public pages `YELLOW_ROUTE_DENOMINATOR_LEAD`; paid/export surfaces `RED_ROUTE_DENOMINATOR_BLOCKED`.

### NFL Next Gen Stats

Reference:

- https://www.nfl.com/news/next-gen-stats-intro-to-new-route-recognition-model

NGS route-recognition methodology confirms that route classification exists internally for eligible route runners and includes WR, TE, and RB route runners. The public material is methodology and examples, not a public player-season or player-week route-count release.

Classification: `RED_ROUTE_DENOMINATOR_BLOCKED`.

### nflverse / nflreadr / nflfastR / nflreadpy

References:

- https://nflreadr.nflverse.com/reference/load_participation.html
- https://nflreadr.nflverse.com/articles/dictionary_participation.html
- https://nflreadr.nflverse.com/reference/load_ftn_charting.html
- https://nflreadr.nflverse.com/reference/load_nextgen_stats.html
- https://nflreadr.nflverse.com/articles/dictionary_nextgen_stats.html

nflverse participation is public, reproducible, and ID-safe, but the `route` field is the primary receiver route label on a play, not a full eligible player routes-run denominator. nflverse Next Gen Stats receiving aggregates do not expose route counts. The public FTN subset through nflverse does not expose route denominators.

Classification: participation `PROXY_ONLY_NOT_TRUE_ROUTES`; NGS and FTN aggregates `RED_ROUTE_DENOMINATOR_BLOCKED`.

## Local Cache Findings

Local search found route-related documentation, templates, guardrails, and prior packet artifacts, but no usable route-count data cache with admissible provenance and rights. `C:\NWR_REVIEW` contained only two `routes_run` text hits in historical asset inventory files and no `receivingPassRoutesRun`, `rtm_routes`, or visible `Routes Run` files. `C:\NWR_SANDBOX` contained many route-honesty and model-lab references, but no source-safe denominator cache. The prior V1 worktree contained only V1 audit artifacts and lead notes. The formula gauntlet revival handoff zip contained the already-canonical HQ route/source-readiness packets and model-context references, not a new route-count feed.

No local file was promoted. No external or dirty worktree was modified.

## Current Counts

- Full route denominator candidates reaching GREEN: 0.
- Route denominator lead rows: 7.
- WR/TE route denominator lead rows: 5.
- RB route denominator lead rows: 4.
- Blocked/proprietary/no-feed rows: 8.
- Proxy-only source rows in source inventory: 1.
- Proxy fallback metrics preserved: 8.

## Final Status

True routes/YPRR/TPRR remain blocked for production. YPRR and TPRR are derivable in principle if a future lane admits a real `routes_run` denominator source with permitted access and safe identity joins. Until then, route-like fields remain research leads and all route-adjacent replacements remain proxies.

Recommended next lane: `Sumer/ESPN routes_run permission, API, export, identity-crosswalk hardening lane`, with Provider permission/API documentation, stable retrieval proof, season/position coverage tables, crosswalk audit, missingness report, and use-gate review as required outputs.
