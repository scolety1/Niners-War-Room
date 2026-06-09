# Best Public Structured Data Stack for a Local-First Fantasy Football Value Model

## Executive recommendation

The best free/public, legally downloadable stack for a local-first deterministic veteran-value model is the entity["organization","nflverse","open-source NFL data collective"] release ecosystem, accessed through entity["software","nflreadr","R package for downloading nflverse data"] or entity["software","nflreadpy","Python package for downloading nflverse data"], with three layers at the center: weekly player stats for canonical player outcomes, play-by-play for exact re-derivation and validation, and identity/availability data for joins and durability context. The best companion sources inside that same ecosystem are the ffverse/DynastyProcess ID crosswalk and entity["software","ffopportunity","expected fantasy points package"] expected-opportunity data. This gives you a fully structured backbone without relying on market rankings or brittle page scraping. citeturn44search3turn40view0turn34search3turn38search0

For your format specifically — 1QB, no PPR, 0.4 rushing/receiving first-down bonus, start-heavy WR requirements, deep keepers — the minimum viable data stack is `player_stats + pbp + players + rosters_weekly + ff_playerids + snap_counts`, with `ff_opportunity` as the best expected-opportunity layer. `participation` and `depth_charts` help, but both have important caveats; `injuries` is useful historically, but official nflverse injury data is currently unavailable for 2025 onward. citeturn42view0turn20view0turn24view0turn29view0turn43view0

Primary references: urlnflreadr docsturn44search3, urlnflverse data scheduleturn35search0, urlnflreadpy docsturn33search0, urlnflverse-data repoturn34search3, urlffopportunity docsturn38search0, and urlDynastyProcess data repoturn39search0. citeturn44search3turn42view0turn40view0turn34search3turn38search0turn39search0

## Recommended dataset stack

- **Weekly player stats — best canonical fact table.**  
  Use `load_player_stats(summary_level = "week")` in R or `nfl.load_player_stats(summary_level="week")` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.{csv|parquet|rds}`  
  Coverage: 1999+. Update cadence: nightly after game days; the Thursday refresh is the cleanest post-correction snapshot. Formats: CSV, parquet, RDS. Terms risk: low for local use; nflverse-data is CC BY 4.0. Confidence: **99**. citeturn13view3turn42view0turn34search3

- **Play-by-play — best validation and derivation layer.**  
  Use `load_pbp()` in R or `nfl.load_pbp()` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.{csv|parquet|rds}`  
  Coverage: 1999+. Update cadence: nightly after game days, with raw rebuild options available faster in the wider nflverse toolchain; Thursday is again the cleanest corrected snapshot. Formats: CSV, parquet, RDS. Terms risk: low for local use; CC BY 4.0 via nflverse-data. Confidence: **99**. citeturn14view5turn42view0turn34search3

- **Player master IDs and mostly immutable bio/draft data.**  
  Use `load_players()` in R or `nfl.load_players()` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/players/players.{csv|parquet|rds}`  
  Coverage: broad player master, not a season-week fact table; `gsis_id` is the primary key. Formats: CSV, parquet, RDS. Update cadence: the loader exposes the current release, but the prose docs do not publish a fixed refresh schedule for this file. Terms risk: low for local use; CC BY 4.0 via nflverse-data. Confidence: **88**. citeturn15view0turn23view0turn35search4turn34search3

- **Weekly rosters — best active/inactive/status layer and one of the best places to grab `sleeper_id`.**  
  Use `load_rosters_weekly()` in R or `nfl.load_rosters_weekly()` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{season}.{csv|parquet|rds}`  
  Coverage: 2002+. Update cadence: roster data updates daily at 7 AM UTC. Formats: CSV, parquet, RDS. Terms risk: low for local use; CC BY 4.0 via nflverse-data. Confidence: **97**. citeturn14view1turn24view0turn42view0turn34search3

- **Season rosters — supplemental player/status source.**  
  Use `load_rosters()` in R or `nfl.load_rosters()` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.{csv|parquet|rds}`  
  Coverage: 1920+ by season-level roster year. Best use: supplementing weekly rosters when you need extra IDs, current team, or roster status context. Terms risk: low. Confidence: **93**. citeturn14view0turn24view0turn42view0

- **Snap counts — best structured role/playing-time proxy.**  
  Use `load_snap_counts()` in R or `nfl.load_snap_counts()` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.{csv|parquet|rds}`  
  Coverage: 2012+. Update cadence: every day at 0, 6, 12, and 18 UTC during the season, depending on urlPro Football Referencehttps://www.pro-football-reference.com/ availability. Formats: CSV, parquet, RDS. Key caveat: keyed by `pfr_player_id`, so you need a bridge to `gsis_id`. Terms risk: low to moderate, but still officially redistributed through nflverse-data. Confidence: **96**. citeturn3view5turn29view0turn42view0

- **Participation — best public route/coverage/context source, but not a true routes-run table.**  
  Use `load_participation()` in R or `nfl.load_participation()` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/pbp_participation/pbp_participation_{season}.{csv|parquet|rds}`  
  Coverage: 2016+. Update cadence: pre-2023 data came from NGS; 2023+ participation is FTN-backed and only posted after the season is complete, not in-season. Formats: CSV, parquet, RDS. Terms risk: moderate because recent data is CC BY-SA 4.0 and requires attribution to urlFTN Datahttps://ftnfantasy.com/stats/sports-data via nflverse. Confidence: **82**. citeturn13view5turn28view0turn42view0turn34search2

- **Depth charts — useful for starts proxies and role ranking, but schema changed after 2024.**  
  Use `load_depth_charts()` in R or `nfl.load_depth_charts()` in Python. Direct path in current source code:  
  `https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_{season}.rds`  
  Coverage: 2001+. Update cadence: daily at 7 AM UTC year-round. Key caveat: from 2025 onward there is no week field; updates are timestamped snapshots appended over time. Another caveat: package docs expose a `file_type` argument, but the current loader source hardcodes `.rds`, so treat this as effectively RDS-only from the release path unless the package changes. Confidence: **84**. citeturn12view6turn30search0turn42view0turn3view3

- **Injuries — historically useful, currently broken for 2025+.**  
  Use `load_injuries()` in R or `nfl.load_injuries()` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.{csv|parquet|rds}`  
  Coverage: 2009–2024 in practice, because nflverse explicitly says the source died after the 2024 season and there is no 2025 data yet. Formats: CSV, parquet, RDS. Terms risk: low for historical local use. Confidence: **94** for 2009–2024, **10** for 2025+. citeturn12view7turn8view3turn42view0

- **Fantasy player IDs — best Sleeper-to-nflverse bridge.**  
  Use `load_ff_playerids()` in R or `nfl.load_ff_playerids()` in Python. Direct path in current source code:  
  `https://github.com/dynastyprocess/data/raw/master/files/db_playerids.rds`  
  Coverage: current crosswalk table rather than a weekly fact table. The docs expose `sleeper_id`, `gsis_id`, `pfr_id`, `espn_id`, `pff_id`, `merge_name`, plus draft/bio fields; the repo says it updates weekly. Format: RDS from the loader path. Terms risk: low to moderate; it is public and openly maintained, but it is outside nflverse-data and lives in a GPL-3.0 repository. Confidence: **98**. citeturn43view0turn8view1turn39search0

- **Expected opportunity — best public xFP/xFD layer, but do not use its total fantasy points field as your exact league score.**  
  Use `load_ff_opportunity(stat_type = "weekly")` in R or `nfl.load_ff_opportunity(stat_type="weekly")` in Python. Direct path template:  
  `https://github.com/ffverse/ffopportunity/releases/download/{model_version}-data/ep_{stat_type}_{season}.rds`  
  Coverage: 2006+. Formats: RDS from the loader path. Best use: expected yards, TDs, and first downs by player/game. Update cadence: automated releases exist, but the official docs do not publish a clean weekday/time SLA the way nflverse does for pbp/stats. Terms risk: low to moderate for local use; public automated releases. Confidence: **91**. citeturn43view0turn36view0turn38search0turn38search2

- **Optional enrichment: Next Gen Stats.**  
  Use `load_nextgen_stats(stat_type = "passing" | "receiving" | "rushing")` in R or `nfl.load_nextgen_stats(...)` in Python. Direct path template:  
  `https://github.com/nflverse/nflverse-data/releases/download/nextgen_stats/ngs_{stat_type}.{csv|parquet|rds}`  
  Coverage: 2016+. Update cadence: nightly during season, but only for players who clear NGS minimum attempt thresholds. This is an enrichment layer, not your core deterministic backbone. Confidence: **80**. citeturn14view3turn44search1turn42view0

## Exact field import matrix

The minimum import set below is intentionally biased toward player-level veteran valuation from real usage and production rather than market sentiment.

**Fields from weekly player stats.**  
Access for every row in this block: R `load_player_stats(summary_level="week")`; Python `nfl.load_player_stats(summary_level="week")`; path `https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.{csv|parquet|rds}`; history 1999+; nightly updates after game days; low legal risk under nflverse-data’s CC BY 4.0 release model. citeturn20view0turn13view3turn42view0turn34search3

| Exact field | Pos | Direct or derive | Why import | Confidence |
|---|---|---:|---|---:|
| `completions` | QB | Direct | Passing volume/accuracy base | 99 |
| `attempts` | QB | Direct | Passing volume | 99 |
| `passing_yards` | QB | Direct | Core fantasy production | 99 |
| `passing_tds` | QB | Direct | Core fantasy production | 99 |
| `passing_interceptions` | QB | Direct | Negative scoring / volatility | 99 |
| `passing_first_downs` | QB | Direct | Useful QB real-stat value feature even if not scored in your league | 98 |
| `passing_air_yards` | QB | Direct | Aggressiveness / downfield intent | 97 |
| `carries` | QB/RB | Direct | Rushing volume | 99 |
| `rushing_yards` | QB/RB/WR | Direct | Core fantasy production | 99 |
| `rushing_tds` | QB/RB/WR | Direct | Core fantasy production | 99 |
| `rushing_first_downs` | QB/RB/WR | Direct | **Direct match for your 0.4 rushing first-down bonus** | 99 |
| `receptions` | RB/WR/TE | Direct | Usage context even in non-PPR | 99 |
| `targets` | RB/WR/TE | Direct | Core receiving opportunity | 99 |
| `receiving_yards` | RB/WR/TE | Direct | Core fantasy production | 99 |
| `receiving_tds` | RB/WR/TE | Direct | Core fantasy production | 99 |
| `receiving_first_downs` | RB/WR/TE | Direct | **Direct match for your 0.4 receiving first-down bonus** | 99 |
| `receiving_air_yards` | RB/WR/TE | Direct | Role quality and upside | 98 |
| `target_share` | RB/WR/TE | Direct | Team-level share, already computed | 98 |
| `air_yards_share` | RB/WR/TE | Direct | Team-level vertical share, already computed | 98 |
| `wopr` | WR/TE/RB | Direct | Compact usage/role summary | 98 |

**Fields from play-by-play.**  
Access for every row in this block: R `load_pbp()`; Python `nfl.load_pbp()`; path `https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.{csv|parquet|rds}`; history 1999+; nightly updates after game days; low legal risk under CC BY 4.0. Use this block when you want exact local re-derivation, auditing, or custom scoring logic rather than trusting aggregates. citeturn26view1turn27search0turn26view0turn14view5turn42view0

| Exact field | Pos | Direct or derive | Why import | Confidence |
|---|---|---:|---|---:|
| `game_id` | All | Direct | Primary game key | 99 |
| `play_id` | All | Direct | Primary play key | 99 |
| `play_type` | All | Direct | Filter pass/run/no-play | 99 |
| `pass_attempt` | QB/WR/TE/RB | Direct | Pass-play denominator; target derivation | 99 |
| `rush_attempt` | QB/RB/WR | Direct | Exact rushing-play denominator | 99 |
| `touchdown` | All | Direct | Exact play-level TD events | 99 |
| `pass_touchdown` | QB/WR/TE/RB | Direct | Passing TD attribution logic | 99 |
| `rush_touchdown` | QB/RB/WR | Direct | Rushing TD attribution logic | 99 |
| `first_down` | All | Direct | Play-level first-down event | 98 |
| `first_down_pass` | QB/WR/TE/RB | Direct | Rebuild passing and receiving first downs | 99 |
| `first_down_rush` | QB/RB/WR | Direct | Rebuild rushing first downs | 99 |
| `passer_player_id` | QB | Direct | Passing attribution key | 99 |
| `receiver_player_id` | RB/WR/TE | Direct | Target attribution key | 99 |
| `rusher_player_id` | QB/RB/WR | Direct | Rushing attribution key | 99 |
| `air_yards` | QB/RB/WR/TE | Direct | Exact play-level air yards | 99 |
| `yards_after_catch` | RB/WR/TE | Direct | Play-level receiving outcome quality | 97 |
| `down` | All | Direct | Situational context | 99 |
| `ydstogo` | All | Direct | Situational context | 99 |
| `yardline_100` | All | Direct | Field position context | 99 |
| `game_seconds_remaining` | All | Direct | Game-state context | 99 |
| `epa` | All | Direct | Optional efficiency/context feature | 97 |
| `targets` | RB/WR/TE | **Derive** | Count pass plays where player is `receiver_player_id` | 97 |
| `passing_first_downs` | QB | **Derive** | Sum `first_down_pass` by `passer_player_id` | 96 |
| `receiving_first_downs` | RB/WR/TE | **Derive** | Sum `first_down_pass` by `receiver_player_id` | 96 |
| `rushing_first_downs` | QB/RB/WR | **Derive** | Sum `first_down_rush` by `rusher_player_id` | 97 |

**Fields from snap counts.**  
Access for every row in this block: R `load_snap_counts()`; Python `nfl.load_snap_counts()`; path `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.{csv|parquet|rds}`; history 2012+; four daily refresh windows during season; join key is `pfr_player_id`, not `gsis_id`. citeturn29view0turn3view5turn42view0

| Exact field | Pos | Direct or derive | Why import | Confidence |
|---|---|---:|---|---:|
| `game_id` | All | Direct | Join to game-week facts | 99 |
| `week` | All | Direct | Weekly key | 99 |
| `team` | All | Direct | Weekly team key | 99 |
| `pfr_player_id` | All | Direct | Required bridge key to canonical IDs | 99 |
| `offense_snaps` | QB/RB/WR/TE | Direct | Best public playing-time numerator | 99 |
| `offense_pct` | QB/RB/WR/TE | Direct | Best public snap-share field | 99 |
| `st_snaps` | RB/WR/TE | Direct | Mostly a noise filter / special teams role hint | 92 |

**Fields from participation.**  
Access for every row in this block: R `load_participation()`; Python `nfl.load_participation()`; path `https://github.com/nflverse/nflverse-data/releases/download/pbp_participation/pbp_participation_{season}.{csv|parquet|rds}`; history 2016+; recent seasons are not in-season refreshed; 2023+ data is FTN-backed and season-end only. The `route` field is **not** all routes run by all eligible receivers; it is the route for the primary receiver on a play. citeturn28view0turn13view5turn42view0turn34search2

| Exact field | Pos | Direct or derive | Why import | Confidence |
|---|---|---:|---|---:|
| `nflverse_game_id` | All | Direct | Game key for merge back to pbp | 99 |
| `play_id` | All | Direct | Play key for merge back to pbp | 99 |
| `offense_players` | QB/RB/WR/TE | Direct | On-field participation proxy | 95 |
| `offense_positions` | QB/RB/WR/TE | Direct | Positional on-field context | 94 |
| `offense_personnel` | QB/RB/WR/TE | Direct | Team-level personnel usage context | 93 |
| `offense_formation` | QB/RB/WR/TE | Direct | Formation context | 92 |
| `route` | WR/TE/RB | Direct, but limited | Useful route-type signal, **not routes run** | 70 |
| `time_to_throw` | QB/WR/TE | Direct | Passing-game context | 90 |
| `was_pressure` | QB/WR/TE | Direct | Passing-game context | 90 |
| `number_of_pass_rushers` | QB | Direct | Pass-protection context | 88 |

**Availability, depth, and injury fields.**  
This block mixes three files because the questions are closely related: weekly rosters for who was available, depth charts for start/rank proxies, and injuries for official body-part and practice statuses. Weekly rosters: R `load_rosters_weekly()`, Py `nfl.load_rosters_weekly()`, path `.../weekly_rosters/roster_weekly_{season}.{csv|parquet|rds}`, history 2002+, daily 7 AM UTC. Depth charts: R `load_depth_charts()`, Py `nfl.load_depth_charts()`, path `.../depth_charts/depth_charts_{season}.rds`, history 2001+, daily 7 AM UTC, schema changed after 2024. Injuries: R `load_injuries()`, Py `nfl.load_injuries()`, path `.../injuries/injuries_{season}.{csv|parquet|rds}`, history 2009–2024 in practice; no 2025 yet. citeturn24view0turn14view1turn30search0turn8view3turn12view7turn42view0

| Exact field | Dataset | Direct or derive | Why import | Confidence |
|---|---|---:|---|---:|
| `status` | `rosters_weekly` | Direct | Active / inactive / IR / practice squad context | 98 |
| `status_description_abbr` | `rosters_weekly` | Direct | Compact status code | 96 |
| `week` | `rosters_weekly` | Direct | Weekly availability key | 99 |
| `game_type` | `rosters_weekly` | Direct | REG / POST distinction | 99 |
| `sleeper_id` | `rosters_weekly` | Direct | Native bridge to urlSleeperhttps://sleeper.com/ IDs | 98 |
| `dt` | `depth_charts` | Direct | Timestamped depth snapshot from 2025 onward | 95 |
| `pos_abb` | `depth_charts` | Direct | Position abbreviation | 95 |
| `pos_slot` | `depth_charts` | Direct | Formation slot group | 90 |
| `pos_rank` | `depth_charts` | Direct | Best public start/rank proxy | 88 |
| `report_primary_injury` | `injuries` | Direct | Main body-part injury flag | 99 |
| `report_secondary_injury` | `injuries` | Direct | Supplemental body-part injury flag | 96 |
| `report_status` | `injuries` | Direct | Official game status | 99 |
| `practice_primary_injury` | `injuries` | Direct | Practice injury detail | 98 |
| `practice_secondary_injury` | `injuries` | Direct | Practice injury detail | 95 |
| `practice_status` | `injuries` | Direct | DNP / limited / full equivalents | 99 |
| `date_modified` | `injuries` | Direct | Injury recency timestamp | 97 |
| `games_active` | `rosters_weekly` + snaps/stats | **Derive** | Count weeks where player is not on reserve/inactive and/or logged snaps/stats | 85 |
| `games_started` | `depth_charts` + snaps | **Derive proxy** | No clean direct core field; use nearest `pos_rank == 1` snapshot plus offensive snaps | 45 |

**Fields from expected opportunity.**  
Access for every row in this block: R `load_ff_opportunity(stat_type="weekly")`; Python `nfl.load_ff_opportunity(stat_type="weekly")`; path `https://github.com/ffverse/ffopportunity/releases/download/{model_version}-data/ep_weekly_{season}.rds`; history 2006+; release-driven updates. The key reason to import this table in your format is expected first downs and expected component production, not the canned fantasy-point total. citeturn36view0turn43view0turn38search0

| Exact field | Pos | Direct or derive | Why import | Confidence |
|---|---|---:|---|---:|
| `pass_attempt` | QB | Direct | Expected passing-opportunity denominator | 96 |
| `rec_attempt` | RB/WR/TE | Direct | Expected target-opportunity denominator | 96 |
| `rush_attempt` | QB/RB | Direct | Expected rushing-opportunity denominator | 96 |
| `pass_air_yards` | QB | Direct | Expected passing opportunity quality context | 94 |
| `rec_air_yards` | RB/WR/TE | Direct | Expected receiving opportunity quality context | 94 |
| `pass_yards_gained_exp` | QB | Direct | Expected passing yards | 95 |
| `rec_yards_gained_exp` | RB/WR/TE | Direct | Expected receiving yards | 95 |
| `rush_yards_gained_exp` | QB/RB | Direct | Expected rushing yards | 95 |
| `pass_touchdown_exp` | QB | Direct | Expected passing TDs | 95 |
| `rec_touchdown_exp` | RB/WR/TE | Direct | Expected receiving TDs | 95 |
| `rush_touchdown_exp` | QB/RB | Direct | Expected rushing TDs | 95 |
| `pass_first_down_exp` | QB | Direct | Expected passing first downs | 94 |
| `rec_first_down_exp` | RB/WR/TE | Direct | Expected receiving first downs | 94 |
| `rush_first_down_exp` | QB/RB | Direct | Expected rushing first downs | 94 |
| `total_fantasy_points_exp` | All | Direct, but **scoring-mismatched** | Secondary QA field only; its underlying fantasy assumptions are not your exact league rules | 78 |

The important modeling implication is simple: for your league, use the component expected fields (`*_yards_gained_exp`, `*_touchdown_exp`, `*_first_down_exp`) and rebuild your own expected score locally. Do **not** treat `fantasy_points`, `fantasy_points_ppr`, `rec_fantasy_points`, or `total_fantasy_points_exp` as league-exact labels, because those bundled fields encode standard/PPR assumptions and do not know about your no-PPR plus 0.4 first-down bonus settings. citeturn20view0turn36view0

## Sleeper-to-nflverse ID mapping strategy

The cleanest local mapping strategy is to treat `gsis_id` as your canonical internal player key, then bridge everything else into it. The official player master explicitly calls `gsis_id` the primary key for player data, while the ffverse crosswalk exposes `sleeper_id`, `gsis_id`, `pfr_id`, `espn_id`, `pff_id`, `merge_name`, and other bridge fields. Weekly rosters are the second-best verification layer because they also include `sleeper_id` and `gsis_id` together, plus current team/position/status. citeturn23view0turn8view1turn24view0

Use this join order:

1. **Primary bridge:** `load_ff_playerids()` where `sleeper_id IS NOT NULL` and `gsis_id IS NOT NULL`.  
   This is the best public crosswalk for urlSleeperhttps://sleeper.com/ to nflverse IDs. The repository says it is updated weekly. citeturn43view0turn8view1turn39search0

2. **Current-season verification:** `load_rosters_weekly()` or `load_rosters()` on `sleeper_id`.  
   Use this to confirm current team, position, and roster status, and to catch recent players who exist in rosters before the broader player master settles. citeturn24view0turn14view1

3. **Canonical enrichment:** `load_players()` on `gsis_id`.  
   Pull `display_name`, `birth_date`, `position`, `position_group`, `pfr_id`, `espn_id`, `pff_id`, `smart_id`, and draft/experience fields here. citeturn23view0turn15view0

4. **Snap-count bridge:** join snap counts through `pfr_id -> pfr_player_id`.  
   Snap counts are the one important recommended file keyed on PFR IDs, so keep that bridge materialized locally. citeturn29view0turn23view0

5. **Conflict handling:** if a `sleeper_id` match is missing or ambiguous, fall back in this order:  
   `espn_id` / `pfr_id` / `pff_id` exact match, then normalized `merge_name + birth_date + position`, then `name + team + jersey` only as a last resort. Store `mapping_source`, `mapping_rule`, and `mapping_confidence` in your bridge table. This is an inference from the documented ID fields and is the most robust deterministic workflow I found. citeturn8view1turn24view0turn23view0

One subtle but important point: the ffverse player-ID dictionary documents `mfl_id` as the table’s primary key, not `sleeper_id`. So use `sleeper_id` as a crosswalk column, not as your warehouse primary key. Your warehouse primary key should be `gsis_id`, with a separate ID bridge table. citeturn8view1

## Local CSV schemas for import

The schemas below are the smallest sensible local-first layout that still preserves deterministic rebuilds. They are based directly on the official field dictionaries above, but normalized for local use. citeturn20view0turn23view0turn24view0turn29view0turn36view0

`dim_player_ids.csv`
```text
gsis_id,sleeper_id,pfr_id,espn_id,pff_id,smart_id,merge_name,display_name,birth_date,position,position_group,latest_team,mapping_source,mapping_rule,mapping_confidence,is_current,source_dataset,source_release,ingested_at_utc
```

`dim_players.csv`
```text
gsis_id,display_name,first_name,last_name,short_name,football_name,birth_date,college_name,jersey_number,position,position_group,ngs_position,rookie_season,last_season,years_of_experience,draft_year,draft_round,draft_pick,height,weight,headshot,source_dataset,source_release,ingested_at_utc
```

`fact_player_week_stats.csv`
```text
player_id,season,week,season_type,team,opponent_team,position,position_group,completions,attempts,passing_yards,passing_tds,passing_interceptions,passing_first_downs,passing_air_yards,carries,rushing_yards,rushing_tds,rushing_first_downs,receptions,targets,receiving_yards,receiving_tds,receiving_first_downs,receiving_air_yards,target_share,air_yards_share,wopr,source_dataset,source_release,ingested_at_utc
```

`fact_player_week_usage.csv`
```text
gsis_id,season,week,game_id,team,position,pfr_player_id,offense_snaps,offense_pct,st_snaps,nflverse_game_id,play_count_on_field,pass_plays_on_field,route_tagged_target_plays,primary_route_mix,offense_personnel_mix,offense_formation_mix,depth_snapshot_dt,pos_abb,pos_slot,pos_rank,source_dataset,source_release,ingested_at_utc
```

`fact_player_week_health.csv`
```text
gsis_id,season,week,team,position,roster_status,roster_status_abbr,is_active_week,is_ir_week,report_primary_injury,report_secondary_injury,report_status,practice_primary_injury,practice_secondary_injury,practice_status,injury_last_modified,source_dataset,source_release,ingested_at_utc
```

`fact_player_week_xfp.csv`
```text
player_id,season,week,posteam,position,pass_attempt,rec_attempt,rush_attempt,pass_air_yards,rec_air_yards,pass_yards_gained_exp,rec_yards_gained_exp,rush_yards_gained_exp,pass_touchdown_exp,rec_touchdown_exp,rush_touchdown_exp,pass_first_down_exp,rec_first_down_exp,rush_first_down_exp,total_fantasy_points_exp,source_dataset,model_version,source_release,ingested_at_utc
```

A few implementation-level schema rules are worth fixing up front:

- Keep **raw source keys** (`player_id`, `gsis_id`, `pfr_player_id`, `sleeper_id`, `game_id`, `play_id`) rather than collapsing them too early.
- Keep **`source_dataset`**, **`source_release`**, and **`ingested_at_utc`** on every CSV so your model remains replayable and deterministic.
- Store **custom-scoring outputs in your own derived tables**, not in the imported raw tables, because the shipped fantasy-point fields are not league-exact for your format.

## Known limitations and legal posture

The biggest practical limitations are not about structure; they are about coverage gaps and schema shifts. Injury data is the clearest current gap: nflverse explicitly states there is no 2025 injury data yet. Participation is also imperfect for live-season role analysis, because 2023+ participation data is FTN-backed and only posted after the postseason, and its `route` field is not a true routes-run denominator. Depth charts changed schema after 2024 and no longer ship a native `week` from 2025 onward. citeturn42view0turn28view0turn30search0

The second major limitation is format consistency. Most core nflverse-data releases expose CSV, parquet, and RDS, but some of the most useful auxiliary files are effectively RDS-only from the documented loader source today: `load_depth_charts()` currently hardcodes an `.rds` release path despite exposing a `file_type` argument; `load_ff_playerids()` points to a single `.rds`; and `load_ff_opportunity()` points to `.rds` release files. If your local-first system wants pure CSV artifacts, plan to export these to your own local CSV layer after ingestion. citeturn12view6turn3view3turn43view0

The third limitation is scoring mismatch. `player_stats` includes `fantasy_points` and `fantasy_points_ppr`, and `ff_opportunity` includes fantasy-point totals, but those shipped totals follow generic standard/PPR assumptions rather than your exact dynasty format. For your league, the safe path is to import raw and expected component stats and compute your own labels locally, especially because your 0.4 rushing/receiving first-down bonus is not a standard baked-in system field. citeturn20view0turn36view0

On legal posture, the picture is good for local deterministic modeling. The broad nflverse-data repository is CC BY 4.0; the Python docs also note that most nflverse data is broadly CC BY 4.0, with FTN-derived data under CC BY-SA 4.0; and the DynastyProcess data repo is openly published and updated weekly. For local use, this is a low-risk set of structured exports. The main caution is redistribution: preserve attribution generally, and preserve share-alike obligations for FTN-backed data or anything materially derived from it in a way that tracks raw content closely. citeturn34search3turn40view0turn5view3turn39search0

The short version is:

- **Best core backbone:** `load_player_stats`, `load_pbp`, `load_players`, `load_rosters_weekly`, `load_snap_counts`, `load_ff_playerids`. citeturn20view0turn26view1turn23view0turn24view0turn29view0turn8view1
- **Best opportunity layer:** `load_ff_opportunity`, using component expected fields, not canned total fantasy points. citeturn36view0turn43view0
- **Useful but caveated:** `load_participation`, `load_depth_charts`, `load_injuries`, `load_nextgen_stats`. citeturn28view0turn30search0turn8view3turn44search1turn42view0
- **Do not center the model on rankings or market files** if the goal is real-stat veteran value. Use them only later as optional priors, not as the backbone. citeturn44search7