# NWR Model Signal Source Coverage Matrix - 2026 Readiness

Date: 2026-06-21

Owner: Master/Main HQ

Status: Discovery/inventory only. No model feature, private value, ranking,
hidden sort, recommendation, simulation, final draft decision, deployment, or
`latest_approved` approval is granted by this document.

## Executive Summary

NWR has strong coverage for league truth, player identity, roster metadata, draft
capital, weekly/season production, snap counts, ADP market timing, play-by-play
derivations, depth charts, and many advanced historical/backtest sources through
Sleeper and nflverse/nflreadpy.

The biggest remaining gaps for 2026 readiness are:

- Direct live 2026 injury/practice status from nflverse is not available in the
  local runtime probe; `load_injuries(2026)` failed with season range 2009-2025.
- Participation-derived route/personnel/pressure fields are historical/offseason
  only for 2023+ because nflverse participation arrives after all post-season
  games and does not update during the season.
- Exact routes run by every player, targets per route run, and true route
  participation percentage are not directly covered by the current candidate
  packages.
- Direct offensive line grades are not available from the current free/open NWR
  source stack; only proxies are available.
- Sleeper ADP is useful and current-looking, but source risk remains
  `YELLOW_UNDOCUMENTED_ENDPOINT`.

## Sources Inspected

### Current Local Lane Exchange Candidates

| Package | Rows | Current embedded timing metadata | Notes |
| --- | ---: | --- | --- |
| `stats_context/player_weekly_stats_display_context` | 38,402 | Not embedded in current package | Generated before source-timing metadata V1. |
| `stats_context/player_season_stats_display_context` | 4,017 | Not embedded in current package | Generated before source-timing metadata V1. |
| `stats_context/player_roster_display_context` | 6,353 | Not embedded in current package | Generated before source-timing metadata V1. |
| `stats_context/player_weekly_roster_display_context` | 93,428 | Not embedded in current package | Generated before source-timing metadata V1. |
| `stats_context/player_usage_context` | 156,389 | Not embedded in current package | Contains snap counts, participation, and opportunity rows. |
| `stats_context/player_stats_crosscheck_report` | 12 | Not embedded in current package | Source-audit candidate. |
| `market_behavior/sleeper_adp_display_context` | 3,292 | Source risk embedded | Primary ADP market/timing source; candidate only. |

Timing metadata has been added to the normalizer for future `stats_context`
candidates, but the currently generated candidate CSVs/manifests predate that
change. Regenerating display-only `latest_candidate` packages would be the next
safe step if embedded timing fields are required in the package files.

### Exact Current Candidate Fields

`player_weekly_stats_display_context`:

`source_dataset`, `source_file`, `source_row_count`, `source_row_number`,
`context_type`, `approval_status`, `allowed_use`, `blocked_use`, `player_id`,
`player_name`, `player_display_name`, `position`, `position_group`, `team`,
`opponent_team`, `season`, `week`, `season_type`, `completions`, `attempts`,
`passing_yards`, `passing_tds`, `passing_interceptions`,
`passing_first_downs`, `carries`, `rushing_yards`, `rushing_tds`,
`rushing_first_downs`, `targets`, `receptions`, `receiving_yards`,
`receiving_tds`, `receiving_first_downs`, `passing_air_yards`,
`receiving_air_yards`, `passing_yards_after_catch`,
`receiving_yards_after_catch`, `sack_fumbles`, `rushing_fumbles`,
`receiving_fumbles`, `rushing_fumbles_lost`, `receiving_fumbles_lost`.

`player_season_stats_display_context`:

`source_dataset`, `source_file`, `source_row_count`, `source_row_number`,
`context_type`, `approval_status`, `allowed_use`, `blocked_use`, `player_id`,
`player_name`, `player_display_name`, `position`, `position_group`,
`recent_team`, `season`, `season_type`, `completions`, `attempts`,
`passing_yards`, `passing_tds`, `passing_interceptions`,
`passing_first_downs`, `carries`, `rushing_yards`, `rushing_tds`,
`rushing_first_downs`, `targets`, `receptions`, `receiving_yards`,
`receiving_tds`, `receiving_first_downs`, `passing_air_yards`,
`receiving_air_yards`, `passing_yards_after_catch`,
`receiving_yards_after_catch`, `sack_fumbles`, `rushing_fumbles`,
`receiving_fumbles`, `rushing_fumbles_lost`, `receiving_fumbles_lost`.

`player_roster_display_context` and `player_weekly_roster_display_context`:

`source_dataset`, `source_file`, `source_row_count`, `source_row_number`,
`context_type`, `approval_status`, `allowed_use`, `blocked_use`, `gsis_id`,
`pfr_id`, `espn_id`, `sportradar_id`, `yahoo_id`, `rotowire_id`,
`fantasy_data_id`, `sleeper_id`, `smart_id`, `full_name`, `football_name`,
`first_name`, `last_name`, `position`, `ngs_position`, `team`, `season`,
`week`, `game_type`, `depth_chart_position`, `jersey_number`, `status`,
`status_description_abbr`, `birth_date`, `height`, `weight`, `college`,
`years_exp`, `entry_year`, `rookie_year`, `draft_club`, `draft_number`.

`player_usage_context`:

`source_dataset`, `source_file`, `source_row_count`, `source_row_number`,
`context_type`, `approval_status`, `allowed_use`, `blocked_use`,
`pfr_player_id`, `player`, `position`, `team`, `opponent`, `season`, `week`,
`game_type`, `game_id`, `offense_snaps`, `offense_pct`, `defense_snaps`,
`defense_pct`, `st_snaps`, `st_pct`, `possession_team`, `nflverse_game_id`,
`old_game_id`, `play_id`, `route`, `offense_formation`, `offense_personnel`,
`players_on_play`, `offense_players`, `defense_players`, `n_offense`,
`n_defense`, `ngs_air_yards`, `was_pressure`, `offense_names`,
`defense_names`, `offense_positions`, `defense_positions`, `offense_numbers`,
`defense_numbers`, `player_id`, `full_name`, `posteam`, `receptions`,
`pass_air_yards`, `rec_air_yards`, `pass_attempt`, `rec_attempt`,
`rush_attempt`, `pass_completions`, `pass_yards_gained`, `rec_yards_gained`,
`rush_yards_gained`, `pass_touchdown`, `rec_touchdown`, `rush_touchdown`,
`pass_first_down`, `rec_first_down`, `rush_first_down`, `pass_interception`,
`rec_interception`, `rec_fumble_lost`, `rush_fumble_lost`,
`total_yards_gained`, `total_touchdown`, `total_first_down`.

`sleeper_adp_display_context`:

`source_name`, `source_type`, `source_risk`, `season`, `collected_at`,
`updated_at`, `last_modified`, `sleeper_player_id`, `player_name`,
`normalized_player_name`, `team`, `position`, `adp_std`, `adp_half_ppr`,
`adp_ppr`, `adp_2qb`, `adp_dynasty`, `adp_dynasty_std`,
`adp_dynasty_half_ppr`, `adp_dynasty_ppr`, `adp_dynasty_2qb`, `adp_rookie`,
`preferred_adp_for_nwr`, `preferred_adp_reason`, `stale_flag`,
`source_notes`.

### Local nflreadpy Runtime Probe

Local runtime: `nflreadpy 0.1.5`

Available functions include `load_players`, `load_draft_picks`, `load_combine`,
`load_ff_playerids`, `load_injuries`, `load_depth_charts`, `load_schedules`,
`load_pbp`, `load_team_stats`, `load_nextgen_stats`, `load_ftn_charting`,
`load_pfr_advstats`, `load_contracts`, `load_rosters`,
`load_rosters_weekly`, `load_participation`, `load_ff_opportunity`, and
`load_snap_counts`.

Selected runtime probes:

| Source | Probe result |
| --- | --- |
| `load_injuries(2024)` | 6,215 rows, fields include injury type/status/practice/date. |
| `load_injuries(2025)` | 6,068 rows in local runtime, but official schedule caveat should be reviewed. |
| `load_injuries(2026)` | Failed: season must be between 2009 and 2025. |
| `load_depth_charts(2026)` | 258,248 rows, fields include `dt`, team, player, GSIS, position slot/rank. |
| `load_schedules(2026)` | 272 rows, fields include game timing, teams, lines, QB/coach/stadium context. |
| `load_pbp(2025)` | 48,771 rows, 372 fields including `yardline_100`, play type, rush/pass/target/TD/first-down fields, pace/context fields. |
| `load_team_stats(2025)` | 570 rows, 103 fields including team pass/run/sack/scoring environment. |
| `load_ff_opportunity(2025, weekly)` | 6,054 rows, 159 fields including attempts, air yards, expected/diff/fantasy fields. |
| `load_ff_opportunity(2025, pbp_pass)` | 18,463 rows, fields include receiver, air yards, yardline, first down, touchdown, pass context. |
| `load_ff_opportunity(2025, pbp_rush)` | 15,345 rows, fields include rusher, yardline, goal-to-go, first down, TD, QB scramble. |
| `load_nextgen_stats(2025, passing/receiving/rushing)` | Available, includes time to throw, separation, intended air yards, efficiency, expected fields. |
| `load_ftn_charting(2025)` | 47,316 rows, fields include box count, motion, play action, RPO, pass rushers, blitzers, QB fault sack. |
| `load_pfr_advstats(2025, pass/rec/rush)` | Available, includes drops, broken tackles, pressure/hurry/hit fields, yards before/after contact. |
| `load_ff_playerids()` | 12,462 rows, 35 ID/crosswalk fields. |
| `load_draft_picks([2025, 2026])` | 514 rows, fields include season, round, pick, team, college, age, IDs. |
| `load_combine([2025, 2026])` | 648 rows, fields include draft year/team/round/overall and combine measurements. |
| `load_contracts()` | Available but value/contract fields are not approved for model use. |

## Signal Coverage Matrix

| Signal/category | Exact field(s) | Source/package | Direct or derived | 2026 availability | Timing class | Live use allowed | Model use status | Source risk | Notes/caveats |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Age, birthdate, years experience | `birth_date`, `years_exp`, `age`, `date_of_birth`, `draft_year` | Current roster packages; `load_ff_playerids`; `load_players`; `load_contracts` | Direct | available_2026_now for roster/ID sources | live_draft_day_candidate for roster metadata, offseason_refresh for age curves | True for display if fresh | backtest_candidate only | GREEN_OPEN_RELEASE | Good coverage. Age curves need backtest and no private-value approval yet. |
| Draft capital | `round`, `pick`, `team`, `season`; `draft_year`, `draft_team`, `draft_round`, `draft_ovr`; `draft_club`, `draft_number` | `load_draft_picks`, `load_combine`, roster packages, `ff_playerids` | Direct | available_2026_now | offseason_refresh_only | False for live decisions, true for display | backtest_candidate only | GREEN_OPEN_RELEASE | Fully covered. Use for rookie/history research only until model policy approved. |
| Weekly active/inactive status | `status`, `status_description_abbr`, `week`, `team` | `weekly_rosters`; Sleeper rosters | Direct | available_2026_now if refreshed | live_draft_day_candidate | True for display | display_only/backtest_candidate | GREEN_OPEN_RELEASE/Sleeper league truth | Good coverage; stale flag needed on candidate regeneration. |
| Injury/practice status | `report_primary_injury`, `report_secondary_injury`, `report_status`, `practice_primary_injury`, `practice_secondary_injury`, `practice_status`, `date_modified` | `load_injuries` | Direct | 2024/2025 available in runtime; 2026 unavailable in runtime probe | weekly_refresh_candidate for available seasons, yellow_unknown_timing for 2026 | False for 2026 until source exists | display_only/backtest_candidate | YELLOW_TIMING_CAVEAT | Official schedule says injury source changed/died after 2024; local runtime has 2025 rows but no 2026. Needs source confirmation. |
| Depth chart status | 2024: `depth_team`, `depth_position`; 2025+: `dt`, `pos_grp`, `pos_name`, `pos_slot`, `pos_rank` | `load_depth_charts` | Direct | available_2026_now | live_draft_day_candidate if refreshed | True for display | display_only/backtest_candidate | GREEN_OPEN_RELEASE | 2025+ uses timestamp `dt` rather than weekly assignment. Good live display candidate. |
| Route participation/routes run | `players_on_play`, `offense_players`, `defense_players`, `route`, `offense_names`, `offense_positions` | `participation` in `player_usage_context`; `load_participation` | Partial/inferred | historical_only/offseason_only for 2023+ | historical_backtest_only | False | yellow_backtest_only | YELLOW_TIMING_CAVEAT | `route` is primary receiver route, not every receiver route. Exact player routes run still missing. |
| Targets per route run | Need targets plus true routes run denominator | `weekly_stats` targets; `opportunity` targets; participation on-field lists | Derived if route denominator can be built | current_season_unknown | yellow_unknown_timing | False | yellow_backtest_only | YELLOW_TIMING_CAVEAT | Not directly available. Requires exact routes run or careful inference. |
| Air yards | `passing_air_yards`, `receiving_air_yards`, `pass_air_yards`, `rec_air_yards`, `ngs_air_yards`, `air_yards`, `avg_intended_air_yards` | weekly/season stats, opportunity, PBP, NGS, participation | Direct | available_2026_now for current pulled stats if refreshed; historical for participation | weekly_refresh_candidate/historical_backtest_only | True for display if source fresh | backtest_candidate only | GREEN_OPEN_RELEASE/YELLOW for participation | Strong coverage. Prefer weekly/opportunity/PBP/NGS over participation for live-ish use. |
| First-down rates | `passing_first_downs`, `rushing_first_downs`, `receiving_first_downs`, `pass_first_down`, `rec_first_down`, `rush_first_down`, `first_down_pass`, `first_down_rush` | weekly/season stats, opportunity, PBP | Derived rates | available_2026_now if refreshed | weekly_refresh_candidate | True for display | backtest_candidate only | GREEN_OPEN_RELEASE | First downs per target/carry/reception covered. First downs per route needs route denominator. |
| Red-zone/goal-line touches | `yardline_100`, `play_type`, `rush_attempt`, `pass_attempt`, `receiver_player_id`, `rusher_player_id`, `touchdown`, `goal_to_go`, `yardline_100 <= 20/10/5` | `load_pbp`, `load_ff_opportunity` pbp pass/rush | Derived | historical/current-season if PBP refreshed; not in current candidate package | weekly_refresh_candidate | True for display after implementation | backtest_candidate only | GREEN_OPEN_RELEASE | Derivable but not yet normalized into a candidate package. |
| QB rushing role | `carries`, `rushing_yards`, `rushing_tds`, `rush_attempt`, `qb_scramble`, `rusher_player_id`, `goal_to_go`, `yardline_100` | weekly stats, PBP, opportunity pbp_rush | Direct plus derived designed/scramble split | available_2026_now if refreshed | weekly_refresh_candidate | True for display | backtest_candidate only | GREEN_OPEN_RELEASE | Basic role covered. Designed vs scramble can be derived from PBP fields with care. |
| QB sack/sack-fumble context | `sacks_suffered`, `sack_yards_lost`, `sack_fumbles`, `sack_fumbles_lost`, `times_sacked`, `times_blitzed`, `times_hurried`, `times_hit`, `times_pressured`, `was_pressure`, `n_pass_rushers` | team stats, PFR advanced passing, participation, FTN charting | Direct/proxy | available_2026_now if refreshed for team/PFR/FTN; participation historical/offseason | weekly_refresh_candidate/historical_backtest_only | True for display where source fresh | backtest_candidate/yellow_backtest_only | GREEN_OPEN_RELEASE/YELLOW_TIMING_CAVEAT | Good proxy coverage, not direct OL grade. FTN/PFR fields need policy review. |
| Team environment | `attempts`, `carries`, `play_type`, `posteam`, `game_seconds_remaining`, `score_differential`, `xpass`, `no_huddle`, `seconds`, team stats totals | PBP, team stats, schedules | Derived | available_2026_now if refreshed | weekly_refresh_candidate | True for display | backtest_candidate only | GREEN_OPEN_RELEASE | PROE, neutral pass rate, pace, plays, run/pass rate derivable from PBP/team stats. Not yet packaged. |
| Offensive line context | No direct OL grades; proxies: sacks/pressure/hurries/hits, rushing yards before/after contact, box count, QB fault sack, pass rushers | PFR advanced, team stats, FTN charting, NGS/PBP proxies | Proxy/external needed | partially covered | weekly_refresh_candidate/yellow_backtest_only | False for direct grades; true for proxy display | yellow_backtest_only | YELLOW_LICENSE_REVIEW for direct grades | Direct OL grades likely require paid/external source such as PFF/SportsDataIO/FTN licensing. |
| Player ID crosswalks | `sleeper_id`, `gsis_id`, `espn_id`, `yahoo_id`, `pfr_id`, `fantasypros_id`, `pff_id`, `rotowire_id`, `fantasy_data_id`, `cfbref_id`, `cfb_player_id` | `load_ff_playerids`, roster packages, draft picks, combine, Sleeper players | Direct | available_2026_now | live_draft_day_candidate/offseason_refresh | True for display/joining | display_only/backtest_candidate | GREEN_OPEN_RELEASE | Strong coverage. CFBD/college mapping still needs rookie source policy. |
| True ADP for market timing | Sleeper `adp_dynasty_std`, `adp_dynasty`, `adp_std`, `adp_rookie`; preferred rule in ADP package | `market_behavior/sleeper_adp_display_context` | Direct | available_2026_now | display_only | True for display only | display_only | YELLOW_UNDOCUMENTED_ENDPOINT | Primary ADP source for now. Never private value/ranking/sort/recommendation/simulation driver. |

## Coverage Classification

### Fully Covered For Display/Backtest Inventory

- Age, birthdate, experience.
- Draft capital.
- Weekly roster/active status.
- Depth chart status.
- Basic weekly/season production.
- Air yards.
- First downs per target/carry/reception.
- QB rushing basics.
- Player ID crosswalks.
- Sleeper ADP display/timing context.

### Partially Covered

- Injury/practice status: 2024/2025 available locally; 2026 not available in
  runtime probe.
- Route participation: on-field lists and primary receiver route are available
  historically/offseason, but not true routes run for every player and not live
  in-season for 2023+.
- Targets per route run: targets are covered, routes-run denominator is not.
- Red-zone/goal-line touches: derivable from PBP/opportunity but not yet
  normalized into NWR candidates.
- Team environment: derivable from PBP/team stats but not yet normalized.
- QB sack/pressure context: good proxies from team/PFR/FTN, but not direct OL
  quality.
- Offensive line context: proxy-only from free/open sources.

### Missing Or External Needed

- Direct 2026 nflverse injury/practice feed in local runtime.
- Exact routes run by player.
- Targets per route run as a direct field.
- True route participation percentage.
- Direct offensive line grades.
- PFF/FantasyPros/SportsDataIO IDs beyond crosswalk fields need source-specific
  validation if those vendors are used.

## 2026 Live Usability Summary

Live/draft-day display candidates if refreshed:

- Sleeper league truth: rosters, draft order, traded picks, transactions,
  ownership.
- Sleeper ADP display context: YELLOW source-risk, display-only.
- nflverse rosters/weekly_rosters.
- nflverse depth charts.
- weekly player stats, snap counts, team stats, PBP-derived current-week
  context after games.
- schedules and matchup context.

Historical/offseason only:

- 2023+ participation fields.
- season stats.
- draft/combine/career profile fields.
- participation-derived route/personnel/pressure features.

Blocked from model/private value until later policy:

- Any stats-to-model integration.
- ADP/market blending.
- fantasy points and fantasy points PPR.
- advanced expected/diff/EPA/CPOE/WOPR/PACR/RACR/share fields.
- direct recommendations or simulation decision drivers.

## Recommended Next Implementation Path

1. Regenerate display-only `stats_context` latest_candidate packages with the
   source-timing metadata normalizer, without creating `latest_approved`.
2. Add a source-policy/design prompt for injury and depth-chart display
   candidates, with 2026 injury feed availability called out as a blocker.
3. Add PBP/opportunity derivation planning for red-zone, goal-line, QB rushing
   splits, first-down rates, and team environment packages.
4. Add an ID crosswalk candidate package from `ff_playerids` for safer joins
   across Sleeper, GSIS, PFR, FantasyPros, PFF, Rotowire, FantasyData, and CFBD.
5. Ask Deep Research to review missing signals, paid/free source options for OL
   and true route participation, and the safest first backtest candidates.

## Questions For Deep Research

1. Are any important dynasty-value signals missing from this matrix?
2. Are any fields misclassified as live, historical, YELLOW, or RED?
3. What is the best free or paid source for exact routes run and targets per
   route run?
4. What is the safest source for offensive line quality if direct grades are
   needed?
5. Which fields should be first backtest candidates for QB/RB/WR/TE?
6. Which signals are likely redundant or too noisy for NWR dynasty value?
7. Which fields should remain permanently blocked from private value?

## Final Master Verdict

GREEN for discovery and documentation.

YELLOW for model readiness because several strong signals are only historical,
offseason, derived, or source-risked.

RED for any direct use of stats/ADP as private value, hidden sorting, rankings,
recommendations, simulations, or final draft-day decisions before Tim/Master/QA
approval.
