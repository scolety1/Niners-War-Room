# Rookie/Prospect Data Handoff - 2026-05-17

Source working directory:
`C:/Users/codex-agent/Documents/New project`

This handoff summarizes the separate rookie/prospect data package that should be
integrated into Model v4 after first-down and return data canonicalization.

## Project Fit

The package is aimed at Model v4's rookie/prospect blocker for a 10-team, 1QB,
non-PPR dynasty league with 0.4 rushing/receiving first-down scoring.

The intended use is stats-first and source-aware:

- factual college and draft evidence can become prospect prior evidence;
- market/rank/ADP/scouting opinion stays context unless explicitly promoted
  with labels and confidence caps;
- no silent name joins;
- no broad app promotion until receipts and audits pass.

## Major Processed Sources

### CollegeFootballData

Scripts:

- `scripts/college_football_data/export_cfbd.py`
- `scripts/college_football_data/build_prospect_tables.py`
- `scripts/college_football_data/run_cfbd_pipeline.ps1`
- `scripts/college_football_data/README.md`

Processed outputs:

- `data/college_football_data/processed/college_player_seasons_wide.csv`
- `data/college_football_data/processed/college_team_seasons_wide.csv`
- `data/college_football_data/processed/college_market_share.csv`
- `data/college_football_data/processed/college_player_category_summary.csv`
- `data/college_football_data/processed/roster.csv`
- `data/college_football_data/processed/recruiting_players.csv`
- `data/college_football_data/processed/draft_picks.csv`

Approximate counts:

- player seasons: 44,840
- market-share rows: 44,840
- rosters: 124,479
- recruiting players: 15,323
- draft picks: 1,551

### RotoWire College And Rookie Data

Processed outputs:

- `data/rotowire/processed/rotowire_cfb_stats_all.csv`
- `data/rotowire/processed/rotowire_cfb_targets_all.csv`
- `data/rotowire/processed/rotowire_cfb_advanced_team_stats_all.csv`
- `data/rotowire/processed/rotowire_workout_stats.csv`
- `data/rotowire/processed/rotowire_upcoming_depth_charts.csv`
- `data/rotowire/processed/rotowire_rookie_rankings_2026.csv`
- `data/rotowire/processed/rotowire_cfb_injury_report_2026.csv`
- `data/rotowire/processed/rotowire_nfl_injury_report.csv`

Approximate counts:

- CFB stats: 50,198
- CFB targets: 12,979
- CFB advanced team stats: 825
- workout/combine rows: 2,097
- upcoming NFL depth chart rows: 727
- RotoWire rookie ranking/projection rows: 87
- CFB injury report rows: 326
- NFL injury report rows: 503

### Market Context

Processed outputs:

- `data/fantasypros/processed/fantasypros_overall_adp_2026.csv`
- `data/market/processed/rookie_adp_2026_04_23_to_2026_05_17.csv`
- `data/market/processed/rookie_watchlist_2027_mock_first_round.csv`
- `data/market/processed/rookie_watchlist_2027_fantasy_names.csv`

Use:

- market/context only;
- not private football value;
- useful for trade liquidity, pick trade review, and sanity checks.

### Third-Party NFL Draft Combine/Pro-Day Package

Source:
`array-carpenter/nfl-draft-data`

Script:

- `scripts/third_party/import_nfl_draft_data.py`

Processed outputs:

- `data/third_party/nfl_draft_data/processed/combine_pro_day.csv`
- `data/third_party/nfl_draft_data/processed/combine_official.csv`
- `data/third_party/nfl_draft_data/processed/combine_skill_positions_all.csv`
- `data/third_party/nfl_draft_data/processed/combine_dataset_manifest.csv`
- `data/third_party/nfl_draft_data/processed/combine_rookie_coverage.csv`
- `data/third_party/nfl_draft_data/processed/combine_rookie_missing_detail.csv`

Approximate counts:

- combine/pro-day coalesced rows: 8,647
- official combine rows: 6,568
- skill-position rows: 5,094

Coverage notes:

- rookie ADP 2026: 51/51 matched;
- RotoWire rookie rankings 2026: 83/87 matched;
- RotoWire workout stats: 1,761/2,089 matched any pro day;
- 2027 watchlist expectedly sparse.

License note:

- no license was found in downloaded repository files;
- keep this as local research/source-limited evidence unless a license is
  confirmed;
- do not redistribute raw/derived rows from this package without review.

## Modeling Guidance

The data stack is now broad enough to stop general collection and begin
engineering the prospect layer.

Recommended prospect feature table shape:

- identity: player, normalized name, position, college, NFL team, source IDs;
- draft capital: draft year, round, pick, pick value;
- age/lifecycle: DOB, draft age, breakout age if available;
- college production: career, final season, best season;
- usage: target share, rushing share, receiving role, TD share;
- efficiency: yards per target, yards per carry, adjusted production;
- team context: pass rate, run rate, plays/game, conference/team environment;
- athleticism: height, weight, BMI, 40, speed/burst/agility/size-adjusted
  testing;
- recruiting: stars/rating/rank where useful;
- injury: current flags/context only until severity model exists;
- landing spot: NFL depth chart / role competition;
- market: rookie ADP, FantasyPros ADP, RotoWire rookie rank as context;
- confidence/source quality: source fields, missingness, ambiguity flags.

## Integration Risks

- entity resolution across CFBD, RotoWire, FantasyPros, Sleeper, nflverse, and
  Kaggle remains the main risk;
- names such as `Omar Cooper Jr.` vs `Omar Cooper` require alias handling;
- market/ranking data must not leak into private value;
- scouting blurbs and copyrighted text should not be ingested as model evidence;
- missing DOB, early-declare status, route participation, and exact games missed
  remain known gaps;
- third-party combine/pro-day package has unresolved license status.

## Next Engineering Steps

1. Build a prospect source manifest in the main Model v4 repo.
2. Build a prospect identity crosswalk:
   normalized name, draft year, college, position, player URL, Sleeper ID,
   CFBD ID, nflverse/GSIS/NFL IDs where available.
3. Create one canonical prospect feature table.
4. Add no-leakage tests:
   market/ADP/rank cannot directly drive private football value.
5. Add ambiguity tests:
   no silent fuzzy joins, aliases require explicit evidence.
6. Build position-specific prospect prior components.
7. Backtest historical classes before using rookie priors in Golden Build.
8. Re-run named-player and sanity audits after integration.

## Current Recommendation

Do not collect more broad rookie data unless an audit identifies a specific
field gap. The stack is strong enough to build the rookie feature table and
start backtesting.
