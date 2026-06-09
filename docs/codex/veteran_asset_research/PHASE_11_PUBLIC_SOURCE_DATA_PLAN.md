# Public Source Data Plan for LVE War Room Veteran Scoring

## Executive recommendation

For a first decision-ready, local-first veteran model, the strongest free/public backbone is: official **entity["company","Sleeper","fantasy platform"]** league and player data for canonical roster state and ID matching; **entity["organization","Fantasy Football Analytics","projection site"]** for projected stat-line and win-now baseline via CSV/API exports; **entity["organization","DynastyProcess","fantasy data project"]** `values.csv` as the best exportable free dynasty market prior; and the **entity["organization","nflverse","nfl data project"]** family for age, injuries, depth charts, snap counts, player stats, expected points, and Next Gen Stats. That stack is clean enough for deterministic local imports, covers QB/RB/WR/TE, and avoids brittle dependence on forbidden or undocumented scraping. Its main weakness is that free public sources do **not** offer a truly clean, exportable, legally unambiguous dynasty **liquidity** feed, so liquidity should be treated as low-confidence unless you add an optional licensed API. citeturn2view0turn3view0turn5view0turn5view1turn15view0turn16view1turn23search1turn26view2turn27view2turn39view0

The recommended source stack is therefore: **primary projection** = Fantasy Football Analytics; **primary dynasty market prior** = DynastyProcess values; **age/biographical + cross-platform identity** = nflverse `load_ff_playerids`; **injury/status** = nflverse `load_injuries` with Sleeper player-status fields as a refresh-time fallback; **depth/role** = nflverse `load_depth_charts` plus `load_snap_counts`; **advanced stats** = nflverse player stats, Next Gen Stats, and expected-points releases, with participation data used historically rather than as an in-season live input because the docs say 2023+ participation is released after the postseason is complete. citeturn26view2turn27view2turn27view1turn27view0turn28view0turn29search1turn29search4turn31search0

Risk level, maintenance burden, confidence impact, and feature-engineering recommendations below are **model-design judgments**. Capabilities, exports, supported fields, update cadence notes, and access/terms limitations are **evidence-backed from cited source material**.

## Recommended source stack

### Foundational league-state source

**entity["company","Sleeper","fantasy platform"]**  
URL: `https://docs.sleeper.com/`

Evidence-backed capabilities: the official read-only API exposes league metadata, scoring settings, rosters, users, matchups, transactions, traded picks, and a `/players/nfl` endpoint that includes fields such as `fantasy_positions`, `team`, `age`, `years_exp`, `injury_status`, `practice_participation`, `depth_chart_position`, and `depth_chart_order`. Sleeper says no token is required, the API is free to use, and the `/players` call is intended only once per day at most. citeturn2view0turn3view0turn3view1turn3view2turn3view3

Assessment: export/API availability is **yes** via official JSON endpoints; scraping is **not required**; legal/terms risk is **low** when used as documented; expected maintenance burden is **low**; QB/RB/WR/TE coverage is **full**; update frequency is effectively the platform’s live state for league objects and roughly daily for the all-players refresh. Recommended use in the model: canonical player keys, team/league context, rostered-player universe, current status fallback, and league scoring settings. Confidence impact: **high for matching and eligibility**, **low for player value by itself**. citeturn2view0turn3view0

### Primary projection source

**entity["organization","Fantasy Football Analytics","projection site"]**  
URL: `https://fantasyfootballanalytics.net/`

Evidence-backed capabilities: FFA says users can download projections customized to league settings, download either custom rankings or raw projections by statistical category as CSV, and also access projections through an API. The FAQ states users can modify the app’s “Scoring Settings,” current and historical projections are downloadable, historical projections require an Insider subscription or API access, and the site does **not currently** provide dynasty/keeper projections. FFA also states season projections are usually released after the NFL Draft, weekly projections are released on Wednesdays and updated regularly until Sunday. citeturn5view0turn5view1turn6search3turn6search5turn42search10

Assessment: export/API availability is **yes** for CSV and API; scraping is **not required** if you use first-party exports; legal/terms risk is **low to medium** for first-party CSV/API use and **higher** if you try to rebuild upstream scraping pipelines yourself; maintenance burden is **low** for periodic export imports; QB/RB/WR/TE coverage is **full**. Recommended use in the model: primary `lve_projection_value` baseline using raw stat projections rescored locally to LVE settings; not a dynasty market source. Confidence impact: **high for win-now baseline**, **medium for niche scoring modifiers** because the cited materials document custom scoring support broadly but do not specifically document projected rushing/receiving first-down fields. citeturn7view0turn5view0turn5view1

### Primary dynasty market prior

**entity["organization","DynastyProcess","fantasy data project"]**  
URL: `https://github.com/dynastyprocess/data` and `https://dynastyprocess.com/values/`

Evidence-backed capabilities: the public repository says it is an open-data fantasy football repository updated via GitHub Actions on a **weekly** basis and that its main files include `values.csv`, `values-players.csv`, `values-picks.csv`, and FantasyPros-derived ranking files. The linked `ffscrapr` docs show `dp_values()` can fetch those files and that the data include columns such as `player`, `pos`, `team`, `age`, `draft_year`, `ecr_1qb`, `ecr_2qb`, `ecr_pos`, `value_1qb`, `value_2qb`, `scrape_date`, and `fp_id`. The DynastyProcess methodology page says the values are created by scraping **entity["company","FantasyPros","fantasy sports company"]** Dynasty ECR and converting ranks along an exponential decay curve, and it explicitly says the printed chart assumes what FantasyPros assumes: a typical **12-team PPR** dynasty format rostering roughly 300 players. citeturn15view0turn16view0turn16view1

Assessment: export/API availability is **yes** via direct data files and package access; scraping is **not required for consumption**, though the upstream methodology depends on scraped FantasyPros dynasty ranks; legal/terms risk is **medium** because the repo is open and published, but the chain of provenance comes from scraped third-party rankings and the repo itself is GPL-licensed; maintenance burden is **low**; QB/RB/WR/TE coverage is **full**. Recommended use in the model: primary **market value prior** for `market_liquidity`, specifically `value_1qb` and `ecr_1qb`, with a confidence haircut because this is a generic 12-team PPR dynasty market proxy, not direct LVE value and not a true liquidity feed. Confidence impact: **medium for market value**, **low for pure liquidity**. citeturn15view0turn16view0turn16view1

### Age, biography, and cross-platform identity source

**entity["organization","nflverse","nfl data project"]** `load_ff_playerids`  
URL: `https://nflreadr.nflverse.com/reference/load_ff_playerids.html`

Evidence-backed capabilities: nflreadr documents `load_ff_playerids()` as access to DynastyProcess’s fantasy player ID database to connect nflverse with other platforms. The official example shows fields including `fantasypros_id`, `gsis_id`, `sleeper_id`, `nfl_id`, `espn_id`, `name`, `merge_name`, `position`, `team`, `birthdate`, `age`, `draft_year`, `draft_round`, `draft_pick`, `draft_ovr`, `height`, and more. nflverse documents that its public data repository is downloadable manually or via packages and is licensed under CC BY 4.0. citeturn26view2turn32search1turn32search2turn33search1

Assessment: export/API availability is **yes** via csv/parquet/rds and package access; scraping is **not required**; legal risk is **low** with attribution; maintenance burden is **low**; QB/RB/WR/TE coverage is **full**. Recommended use in the model: canonical identity bridge for name matching, bio, age, experience, and draft capital. Confidence impact: **high**, because it lets you standardize on one player key while keeping platform IDs for Sleeper, FantasyPros, and other feeds. citeturn26view2turn32search1

### Injury and status source

nflverse `load_injuries`  
URL: `https://nflreadr.nflverse.com/reference/load_injuries.html`

Evidence-backed capabilities: the official docs state `load_injuries()` returns weekly injury report data, available since 2009, in `rds`, `csv`, or `parquet`, with example fields including `report_primary_injury`, `report_secondary_injury`, `report_status`, `practice_primary_injury`, `practice_secondary_injury`, `practice_status`, and `date_modified`. citeturn27view2

Assessment: export/API availability is **yes**; scraping is **not required**; legal risk is **low** within nflverse’s published release model; maintenance burden is **low**; QB/RB/WR/TE coverage is **full**. Recommended use in the model: primary `injury_durability` feed and refresh-time injury-status input. Confidence impact: **high for documented injury/practice status**, **medium for long-horizon durability** unless you aggregate over multiple seasons. A practical fallback at import time is Sleeper’s player-status fields for current roster-state cross-checking. citeturn27view2turn3view2

### Depth chart and role source

nflverse `load_depth_charts` plus `load_snap_counts`  
URLs: `https://nflreadr.nflverse.com/articles/dictionary_depth_charts.html` and `https://nflreadr.nflverse.com/reference/load_snap_counts.html`

Evidence-backed capabilities: the depth-chart dictionary shows fields including `dt`, `team`, `player_name`, `gsis_id`, `pos_grp`, `pos_name`, `pos_abb`, `pos_slot`, and `pos_rank`, with a note that the source changed after the 2024 season and the documented variables apply from 2025 onward. The snap-count docs say they load game-level snap counts beginning in 2012 and include `offense_snaps`, `offense_pct`, `defense_snaps`, `defense_pct`, `st_snaps`, and `st_pct`. citeturn27view1turn27view0

Assessment: export/API availability is **yes**; scraping is **not required**; legal risk is **low** through nflverse release access; maintenance burden is **low**; QB/RB/WR/TE coverage is **full** for your positions of interest. Recommended use in the model: primary `role_security` source, especially for starter flag, depth rank, and role persistence. Confidence impact: **high** when depth rank and offensive snap share agree, and **lower** when the chart says “starter” but snap share is unstable. citeturn27view1turn27view0

### Advanced stat source

nflverse player stats, expected points, and Next Gen Stats  
URLs: `https://nflreadr.nflverse.com/reference/index.html`, `https://nflreadr.nflverse.com/reference/load_ff_opportunity.html`, and `https://nflreadr.nflverse.com/reference/load_nextgen_stats.html`

Evidence-backed capabilities: nflreadr’s index documents `load_player_stats()`, `load_nextgen_stats()`, `load_ff_opportunity()`, `load_participation()`, and related dictionaries. Official docs/examples show that the player-stats release includes `rushing_first_downs`, `receiving_first_downs`, `target_share`, `air_yards_share`, and `wopr`; expected-points data include play- and weekly-level expected fantasy points and first-down indicators; and Next Gen Stats provide position-specific measurements such as QB aggressiveness and intended air yards, WR/TE average separation and share of intended air yards, and RB expected rushing yards, with current-season NGS updating every night. citeturn23search1turn28view0turn29search0turn29search4turn31search0

Assessment: export/API availability is **yes** via package or release files; scraping is **not required**; legal risk is **low** for standard nflverse releases, but note that participation data has an attribution/license requirement, and the docs say 2023+ participation is released only after the postseason is complete. Maintenance burden is **low to medium** depending on how many derived features you build. QB/RB/WR/TE coverage is **full**, though some NGS measures have attempt thresholds. Recommended use in the model: `first_down_td_fit`, `target_earning_stability`, `route_share_stability`, and position-specific role features. Confidence impact: **high** for historical role/efficiency features, **medium** for route-specific features if you rely on participation data that lags during the season. citeturn29search1turn29search4turn31search0turn28view0

### Optional licensed upgrade

**entity["company","Fantasy Nerds","fantasy sports company"]** API  
URL: `https://api.fantasynerds.com/docs/nfl`

Evidence-backed capabilities: the official API docs expose endpoints for current players, depth charts, injury reports, weekly projections, rest-of-season projections, draft projections, draft rankings, dynasty rankings, and player adds/drops. The NFL data dictionary includes fields like `depth` and `dob`, and the pricing page lists the football API at $399.95 per year. The FAQ says client-side JavaScript exposure of the API key is against their terms, so local-first apps should import on a controlled refresh step, not expose the key at runtime. citeturn36view0turn37view0turn37view1turn37view2turn37view3turn35search4turn38search5turn38search9

Assessment: export/API availability is **yes**; scraping is **not required**; legal risk is **low** once licensed; maintenance burden is **low**; QB/RB/WR/TE coverage is **full**. Recommended use in the model: best optional non-enterprise replacement for a lot of the free-source patchwork, especially if you want one licensed periodic import for projections + dynasty rankings + injuries + depth. Confidence impact: **high** for operational simplicity, **medium** for market/liquidity because dynasty rankings are still rankings rather than actual trade-frequency data. citeturn36view0turn38search9

### Optional enterprise-grade upgrade

**entity["company","SportsDataIO","sports data company"]**  
URL: `https://sportsdata.io/nfl-api`

Evidence-backed capabilities: SportsDataIO markets an NFL API with scores, stats, injuries, rosters/depth charts, weekly fantasy projections, historical data, and fantasy projections “for any timeframe,” including projected individual stats and fantasy points by category and total points. The workflow guide documents a depth-charts endpoint, and the 2025 confirmed coverage page says it added estimated injury return timelines and weekly effective depth charts for 2025-26. citeturn36view1turn36view2turn36view3turn35search0

Assessment: export/API availability is **yes**; scraping is **not required**; legal risk is **low** once licensed; maintenance burden is **very low**; QB/RB/WR/TE coverage is **full**. Recommended use in the model: ideal if you want the cleanest single-vendor import path and can accept likely enterprise pricing. Confidence impact: **high**, but this is optional and probably more expensive than warranted for a 10-team local-first dynasty tool. citeturn36view1turn36view3

## Sources to avoid

The clearest avoid is **entity["organization","KeepTradeCut","fantasy rankings site"]** as a machine-ingested dependency. KTC’s own FAQ says it has **no API or CSV** for rankings and values, its terms forbid scraping and other automated data collection, and its dynasty values are built around a crowdsourced **12-team, .5 PPR** format with 1QB and superflex modes; the FAQ also says its TE-premium values are algorithmic transformations of that base. That makes it useful as a human reference, but not as a legally clean, deterministic import backbone for LVE. citeturn40view0turn41view0

Avoid any plan that depends on automated extraction from raw **FantasyPros** public pages. Their rankings pages can expose CSV downloads in some contexts and support standard/half/PPR views, but the Terms of Use say that except for a single personal-use copy, users may not copy, reproduce, republish, transmit, or distribute site documents or information without permission. Use first-party exports only where explicitly allowed, or consume downstream materialized datasets with care; do not make raw page scraping a required production input. citeturn10view0turn11view0turn13search3turn13search5turn12search0turn13search4

Avoid making **entity["organization","FantasyCalc","fantasy football rankings site"]** a required automated import dependency in v1. The official site says its rankings and trade values are generated from millions of real trades and that its trade database contains millions of deals, which is attractive conceptually, but the public materials found here do not document a stable public export or API for automated local imports. Its terms page is also thin in the snippets returned, emphasizing IP compliance without providing the kind of explicit exportability you want. That makes FantasyCalc reasonable as a manual research cross-check, but too ambiguous for the core deterministic data plan. citeturn17search0turn17search2turn20search3turn43search0

Avoid contaminating player value with the league-rank PDF. Per your own rule, it belongs only in a forced-release exposure workflow. It should never enter market, projection, role, or age features.

## Minimum viable data plan and ideal data plan

The **minimum viable plan** that is enough for a first decision-ready model is:

- Sleeper for league state, scoring settings, roster membership, and canonical player universe.
- Fantasy Football Analytics for import-time projected stat lines and baseline projected value.
- DynastyProcess `values.csv` for a free exportable dynasty market prior.
- nflverse `load_ff_playerids`, `load_injuries`, `load_depth_charts`, `load_snap_counts`, `load_ff_opportunity`, `load_nextgen_stats`, and player-stats releases for age, role, injuries, first-down fit, target earning, and position-specific context. citeturn2view0turn3view0turn5view0turn5view1turn15view0turn16view1turn26view2turn27view2turn27view1turn27view0turn28view0turn29search4turn31search0

With that minimum stack, the features that should be **neutralized with confidence penalties** are true market liquidity, current-year route participation for very recent season state, and any direct first-down projections that are not explicitly supplied by the projection feed. In practice, that means `market_liquidity` should use DynastyProcess as a market prior and then shrink toward the positional mean unless you have a better licensed source; `route_share_stability` should rely more on prior-year snap and target-share data than on fresh route-participation feeds; and `lve_projection_value` should be built from locally rescored projection stat lines with `first_down_td_fit` handled separately from historical first-down and TD data rather than assumed to be embedded in source fantasy-point totals. These are model-design choices, not claims about source capability.  

The minimum stack still requires some **manual review** at import time: ambiguous player matches, players with recent team changes but stale depth-chart rows, players returning from major injury where market and role sources diverge sharply, and any player with conflicting position labels across the import set. Manual review is not ranking by hand; it is exception handling for malformed or conflicting source records.

The **ideal plan**—if time and moderate cost are acceptable—is to keep the open backbone above and add Fantasy Nerds as a licensed refresh/import feed for dynasty rankings, weekly and ROS projections, depth charts, and injuries. That reduces fragility, lowers legal ambiguity around machine access, and gives you a second non-user-authored source to compare against FFA and DynastyProcess. If you want a single-vendor, enterprise-grade stack with broader coverage and stronger service promises, SportsDataIO is the premium path, but it is probably more than this project needs. citeturn36view0turn37view0turn37view1turn37view2turn37view3turn38search9turn36view1turn36view2turn36view3

Over time, confidence should improve by storing every import as a dated local snapshot, comparing source drift rather than replacing values blindly, measuring how often each source disagrees with realized usage, and gradually reweighting sources by out-of-sample usefulness for **LVE’s** rules rather than by generic public opinion. That weighting framework is a heuristic design choice.

## Feature mapping and implementation-ready CSV schemas

### Feature map

The mappings below are **model-design choices** built on the source capabilities documented above.

- **`lve_projection_value`**: FFA raw stat projections rescored locally to LVE scoring. Do not trust source fantasy totals when first-down bonuses are absent or unclear. Use projection stat lines as the base, then add a separate first-down adjustment derived from historical first-down rates by player and position.
- **`role_security`**: nflverse depth-chart `pos_rank` + offensive snap share + recent opportunity concentration. For QB, weight starting designation and passing/rushing workload stability. For RB, weight snap share, carries, and receiving involvement. For WR/TE, weight target share and route/snap persistence.
- **`age_curve`**: nflverse bio fields (`age`, `birthdate`, `draft_year`, `years_exp` if merged from Sleeper or derived) transformed by position-specific priors.
- **`market_liquidity`**: DynastyProcess `value_1qb`, `ecr_1qb`, `ecr_pos`, and scrape date as a market prior. Because that file does not encode true transaction frequency, shrink this feature toward neutral unless you later add a licensed trade/liquidity feed.
- **`position_replaceability`**: local computation from LVE lineup settings plus projection tiers and rostered-player distribution. For TE, calculate replaceability directly from projected starter gap, not from TE-premium public markets.
- **`first_down_td_fit`**: nflverse `rushing_first_downs`, `receiving_first_downs`, rushing/receiving TDs, carries, targets, receptions, expected points, and player archetype. RBs should get more weight on first-down and TD creation; WRs/TEs should rely more on receiving first downs and target value.
- **`target_earning_stability`**: nflverse `targets`, `target_share`, `air_yards_share`, `wopr`, and year-over-year or rolling-window variance. This is mainly a WR/TE feature, but receiving RBs can benefit from the same structure.
- **`route_share_stability`**: historical participation/route information when available; otherwise snap share plus target/share proxies with a confidence haircut.
- **`injury_durability`**: nflverse injury-report counts, severity/status categories, recurrence by body area, games missed proxies, and days since last modification.

### CSV schemas

The schemas below are **implementation-ready design recommendations** for a deterministic local import layer.

#### `public_source_catalog.csv`

```csv
source_id,source_name,source_url,source_role,access_method,access_artifact,export_format,requires_scrape,license_or_terms_summary,legal_risk_level,maintenance_burden,update_frequency_text,coverage_qb,coverage_rb,coverage_wr,coverage_te,base_confidence,last_refresh_utc,notes
sleeper,Sleeper,https://docs.sleeper.com/,league_state,official_api,league/rosters/players,json,false,official read-only api,low,low,live league objects + daily player map,true,true,true,true,0.95,,canonical ids and league context
ffa,Fantasy Football Analytics,https://fantasyfootballanalytics.net/,projection,csv_or_api,raw_projections,csv,false,first-party export/api; historical optional paid,low_medium,low,season after draft; weekly wednesday-sunday,true,true,true,true,0.85,,primary projection baseline
dynastyprocess,DynastyProcess,https://github.com/dynastyprocess/data,market_prior,direct_file,values.csv,csv,false,open repo; upstream derived from scraped fp dynasty ecr,medium,low,weekly,true,true,true,true,0.65,,market prior not true liquidity
ff_playerids,nflverse_ff_playerids,https://nflreadr.nflverse.com/reference/load_ff_playerids.html,bio_id_bridge,release_or_package,ff_playerids,parquet,false,cc by 4.0 with attribution,low,low,periodic release,true,true,true,true,0.95,,cross-platform ids and bio
injuries,nflverse_injuries,https://nflreadr.nflverse.com/reference/load_injuries.html,injury,release_or_package,injuries,parquet,false,cc by 4.0 with attribution,low,low,weekly injury reports,true,true,true,true,0.9,,primary injury feed
depth,nflverse_depth_charts,https://nflreadr.nflverse.com/articles/dictionary_depth_charts.html,role,release_or_package,depth_charts,parquet,false,cc by 4.0 with attribution,low,low,source-updated,true,true,true,true,0.8,,starter/depth rank
snaps,nflverse_snap_counts,https://nflreadr.nflverse.com/reference/load_snap_counts.html,role,release_or_package,snap_counts,parquet,false,cc by 4.0 with attribution,low,low,game-level weekly,true,true,true,true,0.85,,role stability
player_stats,nflverse_player_stats,https://nflreadr.nflverse.com/reference/index.html,advanced_stats,release_or_package,player_stats,parquet,false,cc by 4.0 with attribution,low,medium,season/game-level,true,true,true,true,0.9,,first downs target share wopr
ff_opportunity,nflverse_ff_opportunity,https://nflreadr.nflverse.com/reference/load_ff_opportunity.html,advanced_stats,release_or_package,ff_opportunity,parquet,false,cc by 4.0 with attribution,low,medium,release-based,true,true,true,true,0.85,,expected points
ngs,nflverse_nextgen_stats,https://nflreadr.nflverse.com/reference/load_nextgen_stats.html,advanced_stats,release_or_package,nextgen_stats,parquet,false,cc by 4.0 with attribution,low,medium,current season nightly,true,true,true,true,0.8,,ngs thresholds apply
fn_api,Fantasy Nerds,https://api.fantasynerds.com/docs/nfl,licensed_upgrade,official_api,multiple_endpoints,json,false,licensed api key required,low,low,in-season endpoints,true,true,true,true,0.85,,optional paid upgrade
sportsdataio,SportsDataIO,https://sportsdata.io/nfl-api,licensed_premium,official_api,multiple_endpoints,json,false,licensed commercial api,low,very_low,real-time/vendor-managed,true,true,true,true,0.9,,optional premium upgrade
```

#### `player_projection_inputs.csv`

```csv
player_key,player_name,position,team,season,asof_date,projection_source_id,source_player_id,scoring_profile_id,proj_pass_attempts,proj_completions,proj_pass_yards,proj_pass_tds,proj_pass_ints,proj_rush_attempts,proj_rush_yards,proj_rush_tds,proj_targets,proj_receptions,proj_rec_yards,proj_rec_tds,proj_fumbles_lost,proj_rush_first_downs,proj_rec_first_downs,proj_fantasy_points_source,proj_fantasy_points_lve_rescored,projection_confidence,staleness_days,missing_projection_flags,notes
```

#### `player_market_inputs.csv`

```csv
player_key,player_name,position,team,season,asof_date,market_source_id,source_player_id,value_1qb,ecr_1qb,ecr_pos,value_2qb,ecr_2qb,market_rank,market_delta,market_scrape_date,liquidity_score,liquidity_proxy_type,market_confidence,staleness_days,format_assumption_flags,notes
```

#### `player_role_inputs.csv`

```csv
player_key,player_name,position,team,season,asof_date,role_source_id,source_player_id,depth_timestamp_utc,depth_pos_group,depth_pos_slot,depth_pos_rank,starter_flag,offense_snaps,offense_snap_pct,games_sampled,targets,target_share,air_yards_share,wopr,carries,rush_attempt_share,route_participation_pct,role_confidence,staleness_days,role_conflict_flags,notes
```

#### `player_injury_inputs.csv`

```csv
player_key,player_name,position,team,season,asof_date,injury_source_id,source_player_id,latest_report_week,report_primary_injury,report_secondary_injury,report_status,practice_primary_injury,practice_secondary_injury,practice_status,date_modified_utc,injury_events_rolling_1y,injury_events_rolling_2y,games_missed_proxy,days_since_last_report,injury_confidence,staleness_days,injury_conflict_flags,notes
```

#### `player_bio_inputs.csv`

```csv
player_key,player_name,position,team,season,asof_date,bio_source_id,source_player_id,sleeper_id,gsis_id,nfl_id,espn_id,fantasypros_id,birthdate,age,years_exp,draft_year,draft_round,draft_pick,draft_ovr,height_in,weight_lb,college,bio_confidence,staleness_days,bio_conflict_flags,notes
```

#### `normalized_veteran_feature_backfill.csv`

```csv
player_key,player_name,position,team,season,asof_date,lve_projection_value,role_security,age_curve,market_liquidity,position_replaceability,first_down_td_fit,target_earning_stability,route_share_stability,injury_durability,projection_confidence,market_confidence,role_confidence,injury_confidence,bio_confidence,overall_feature_confidence,missing_feature_flags,source_snapshot_id,manual_review_required,notes
```

## Validation and contamination controls

### Validation rules

The canonical join key should be `player_key`, resolved in this order: `sleeper_id` if present, else `gsis_id`, else a deterministic `merge_name + birthdate + position` fallback. If multiple candidate matches exist, fail the import for that row rather than guessing. nflverse’s ID bridge is strong enough to make this practical because it includes Sleeper, NFL, ESPN, and FantasyPros identifiers in one table. citeturn26view2

Use source-specific stale thresholds. A practical starting policy is: projections stale after 14 days in the offseason once post-draft projections exist; injuries/depth stale after 7 days in-season and 30 days in the offseason; market prior stale after 14 days; bio stale after 365 days unless draft-year rollover occurs. Those thresholds are heuristic design choices. Every imported row should also carry both `asof_date` and the source’s own published/modified/scrape timestamp where available.  

Missing data should not silently become zero. Instead, map each missing component to one of three states: `not_applicable`, `temporarily_missing`, or `structurally_unavailable`. Then apply confidence penalties accordingly. For example, direct projected first-down fields are structurally unavailable in many projection feeds, so the model should estimate them from player history and role instead of writing zeros.

For source conflicts, use a precedence ladder: official league state from Sleeper for roster membership and platform IDs; nflverse bio bridge for cross-platform identity; nflverse injuries for injury records; nflverse depth plus snap counts for role; FFA for primary projections; DynastyProcess for market prior. If two high-confidence sources disagree materially, store both, choose the higher-precedence source, and cut the downstream feature confidence.  

Confidence penalties should be additive and transparent. A workable policy is to subtract confidence for stale source data, structurally mismatched format assumptions, one-source-only features, and identity ambiguity. The model should be allowed to score a player with partial data, but should surface that the score is weakly supported.

### No-hindsight and no-live-runtime rules

All external data should be available only during an explicit refresh/import step. The runtime scorer should read from frozen local CSV snapshots only. No live API calls, no page fetches, and no recomputation from remote endpoints during ordinary scoring. That is a design rule aligned with your local-first requirement.

Each refresh should produce a versioned local snapshot, and all scoring outputs should record the snapshot ID used. If you later backtest or evaluate a prior decision, use only the snapshot that existed at or before that as-of date. Never backfill realized future stats into historical feature rows.

### Contamination controls

Do **not** use the league-rank PDF as player value. Restrict it to a separate forced-release exposure flag such as `forced_release_exposure = 1/0` and keep it out of every player-value feature and any learned weights.

Treat generic dynasty market as a **prior**, not as LVE truth. DynastyProcess itself says its values depend on FantasyPros dynasty ranks and the assumptions of a typical 12-team PPR dynasty environment. LVE is 1QB, no PPR, no TE premium, includes first-down bonuses, and has deep benches plus a forced-release mechanic. Therefore, market prior should be shrunk, not copied. citeturn16view0

Avoid PPR contamination by rescoring projection stat lines locally and by preferring stat-line features over source fantasy totals whenever possible. Avoid Superflex contamination by using explicit 1QB fields such as DynastyProcess `value_1qb` and by refusing to mix in superflex columns or rankings. Avoid TE-premium contamination by ignoring TE-premium public toggles and by computing TE value from LVE replacement levels and role quality instead of importing TE-boosted public rankings. KTC’s own FAQ is a useful warning here because it states its values are based on a vanilla 12-team, .5PPR base and that TE premium is an algorithmic overlay. citeturn16view1turn40view0

## Open questions and limitations

There is no free public source in this research set that is simultaneously: clearly licensed for machine ingestion, exportable, low-maintenance, and a strong direct measure of dynasty **trade liquidity**. The free stack above gives you a good market prior, but not a clean transaction-frequency feed.

The documentation gathered here supports FFA as the best free projection export source, but it does **not** specifically document projected rushing/receiving first-down fields. For LVE, the safe plan is to derive first-down fit from historical stats and role, not to assume a source’s fantasy totals already capture that bonus.

DynastyProcess is the best exportable free dynasty market file I found, but it inherits both generic format assumptions and an upstream provenance chain based on scraped FantasyPros dynasty ranks. That is why I recommend it as a confidence-damped prior rather than as the sole arbiter of veteran value.