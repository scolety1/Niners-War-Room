# HQ1 Route/YPRR/TPRR Source Admission Search V1

## Lane Scope

This HQ1 lane investigated whether NWR can identify a safe, public, reproducible, historically usable source for routes run, route participation, targets per route run, yards per route run, first downs per route, or route-alignment/depth denominators.

This is source-admission search only. It does not admit or promote any source. It does not calculate YPRR, TPRR, route share, first downs per route, or any route metric as an approved model input. It does not score features, compare candidates to prior-year finish, modify production behavior, or touch HQ2 work.

## Packets Read

- `docs/hq/deep_research_upgrades/orchestration_v1_20260708/`
- `docs/hq/deep_research_upgrades/hq1_feature_discovery_registry_v1_20260708/`
- `docs/hq/deep_research_upgrades/hq1_public_source_status_reconciliation_v2_20260708/`
- `docs/hq/deep_research_upgrades/hq1_candidate_metric_formula_cards_v21_20260708/`

## Public Sources Inspected

The lane reviewed existing NWR HQ1 packets, local source-status registries, and public documentation or public surfaces for:

- nflverse participation data
- nflverse FTN charting subset
- nflverse Next Gen Stats aggregates
- nflverse/PFR snap counts
- SumerSports public WR and TE route leaderboards
- ESPN Receiver Scores public leaderboard
- NFL Next Gen Stats route recognition documentation
- NFL Big Data Bowl sample tracking datasets
- commercial FTN Data surfaces
- prior HQ1 blocked-source registries for PFF, SIS, Sportradar, commercial FTN, scraped proprietary route data, and public route snippets

## Result

No source satisfied NWR's current admission criteria for a true full routes-run denominator.

The lane found public or partially public route-adjacent surfaces, but each failed at least one mandatory source-admission requirement:

- nflverse participation is reproducible and ID-friendly, but its `route` field describes the primary receiver route on a play. It is not a full routes-run denominator for every eligible receiver.
- SumerSports public WR and TE pages display Routes Run, Targets/Route Run, and YPRR, but the pages do not provide an admitted documented feed, stable downloadable historical files, safe player IDs, licensing/provenance receipts, or all-position route-denominator coverage.
- ESPN Receiver Scores publicly displays route-derived receiver columns and says it evaluates every route a pass catcher runs using NFL Next Gen Stats data, but it is a display product without a documented reproducible data feed, durable NWR join keys, license/usage proof, checksums, or source contract.
- NFL Next Gen Stats route recognition documentation confirms that route classification can cover all route runners in the underlying tracking data, but the documentation does not expose a public, reproducible player route-denominator feed for NWR.
- PFR snap counts and team pass attempts can support exposure proxies only. Snaps and team pass attempts are not routes.
- NFL Big Data Bowl tracking releases are samples or competition datasets, not broad, continuous, multi-season source feeds for NWR route metrics.
- PFF, SIS, Sportradar, commercial FTN, and scraped proprietary route data remain blocked.

## Candidate Source Findings

Two public display surfaces deserve preservation as future source-admission leads only:

- ESPN Receiver Scores: public historical season selector currently covers 2017 through 2025 and includes `ROUTES` and `YDS/RT` display columns. It still lacks the source contract, stable data export, durable IDs, historical file receipts, licensing clarity, and checksum/provenance path required for NWR admission.
- SumerSports WR and TE pages: public tables display Routes Run, Targets/Route Run, and YPRR for WR and TE. They still lack a documented reproducible feed, durable IDs, full position coverage, licensing clarity, and historical reproducibility proof.

Neither lead is admitted. Neither can be used for model inputs, rankings, scoring, source truth, or UI integration from this lane.

## Why Partial Sources Are Insufficient

True YPRR requires:

`receiving_yards / full_routes_run`

True TPRR requires:

`targets / full_routes_run`

The denominator must count routes run by the player across eligible pass plays. A targeted-route label, primary-receiver route, snap count, pass attempt, target, reception, team dropback, or public leaderboard snippet is not a substitute for full routes run.

## Route Proxy Status

Route-like proxies remain available for future research planning when their own input sources are admitted or review-gated. They must stay labeled as proxies.

Examples preserved in this packet include:

- targets per team pass attempt
- receiving yards per team pass attempt
- first downs per target
- first downs per team pass attempt
- air yards per team pass attempt
- targets per offensive snap
- receiving yards per offensive snap
- receiving first downs per offensive snap
- target share
- air-yards share
- WOPR
- Chain-Mover Score

These are not YPRR, TPRR, route share, route participation, or routes-run metrics.

## Future Source-Admission Recommendations

Recommended future HQ1 lanes:

1. ESPN Receiver Scores source-admission probe: determine whether a documented, license-safe, reproducible export/API with durable player IDs and historical receipts exists.
2. SumerSports route surface admission probe: determine whether Sumer can provide a stable, public, license-safe, reproducible data feed with durable IDs and full coverage proof.
3. nflverse participation source-continuity audit: preserve primary-receiver route context with an explicit no-route-denominator gate.
4. PFR/nflverse snap counts source admission review: evaluate snap-based exposure proxies separately from route metrics.
5. Public NGS route feed monitor: periodically recheck whether NFL or nflverse publishes a full routes-run denominator feed.

## Final Verdict

`YELLOW_HQ1_ROUTE_SOURCE_PARTIAL_ONLY_PROXIES_AVAILABLE`

No safe public reproducible full routes-run source was found. Partial sources and route-like proxies are documented for future planning, and true YPRR/TPRR remain blocked.

## Evidence References

- nflreadr participation loader: https://nflreadr.nflverse.com/reference/load_participation.html
- nflreadr participation dictionary: https://nflreadr.nflverse.com/articles/dictionary_participation.html
- nflreadr FTN charting loader: https://nflreadr.nflverse.com/reference/load_ftn_charting.html
- nflreadr Next Gen Stats loader: https://nflreadr.nflverse.com/reference/load_nextgen_stats.html
- nflreadr Next Gen Stats dictionary: https://nflreadr.nflverse.com/articles/dictionary_nextgen_stats.html
- nflreadr snap counts loader: https://nflreadr.nflverse.com/reference/load_snap_counts.html
- SumerSports WR public surface: https://sumersports.com/players/wide-receiver/
- SumerSports TE public surface: https://sumersports.com/players/tight-end/
- ESPN Receiver Scores public surface: https://espnanalytics.com/receivers
- NFL Next Gen Stats route recognition article: https://www.nfl.com/news/next-gen-stats-intro-to-new-route-recognition-model
- FTN commercial data page: https://ftnfantasy.com/stats/sports-data
