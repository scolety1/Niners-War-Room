# NWR Model Signal Source Coverage Deep Research Audit Result - 2026-06-21

Owner: Master/Main HQ

Status: GREEN for first serious backtest readiness with a short pre-backtest
feature-readiness sprint. YELLOW for any model/private-value use until backtest
evidence and Tim/Master/QA approval exist.

## Verdict

Deep Research reviewed the 2026 NWR model signal source coverage matrix and
returned a GREEN verdict for starting the first serious dynasty/keeper
backtest.

The current source stack is sufficient to begin because NWR now has:

- Sleeper league truth and ADP market/timing context.
- nflverse/nflreadpy historical player stats, rosters, weekly rosters, usage,
  snap counts, participation, opportunity, PBP, and team-stat source options.
- Display-only `stats_context` latest-candidate packages with timing metadata.
- A policy boundary that keeps stats, ADP, projections, and market fields out
  of private value, recommendations, hidden sort, simulations, and final draft
  decisions.

This verdict does not approve model use, private value changes, ranking changes,
Mock Draft logic changes, simulation drivers, or final draft-day advice.

## Must-Do Pre-Backtest Sprint Items

1. Add scoring-aligned factual player stat columns already present in nflverse
   player stats.
2. Plan PBP-derived red-zone, goal-line, QB rushing, QB pressure, and team
   environment feature packages.
3. Correct source timing taxonomy for season stats, injuries, and 2025+ depth
   charts.
4. Lock backtest as-of and leakage rules before any model training or feature
   scoring work.

## Scoring-Aligned Stat Candidate Expansion

The normalizer can safely carry the following factual columns as display and
backtest candidate context when the source snapshot provides them:

- `passing_2pt_conversions`
- `rushing_2pt_conversions`
- `receiving_2pt_conversions`
- `punt_returns`
- `punt_return_yards`
- `kickoff_returns`
- `kickoff_return_yards`
- `special_teams_tds`

Fumbles-lost fields already present remain in scope:

- `rushing_fumbles_lost`
- `receiving_fumbles_lost`
- play-level `rec_fumble_lost`
- play-level `rush_fumble_lost`

Kicker fields are visible in nflverse player stats, but K is not formally
opened for NWR model scope in this sprint. Kicker fields remain optional
display/backtest candidates only and are not enabled as kept candidate columns
by this checkpoint.

## Local Candidate Regeneration Result

Source snapshot:

`C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260621_000000_nflverse_expansion_v1`

Candidate label:

`20260621_pre_backtest_scoring_aligned_v1`

| Package | Rows | SHA256 | Timing result |
| --- | ---: | --- | --- |
| `stats_context/player_weekly_stats_display_context` | 38,402 | `b6dff4f81644b873f495ab8962abbccca3c5faa649ce330b913680af393159f4` | `live_draft_day_candidate` |
| `stats_context/player_season_stats_display_context` | 4,017 | `781f5499b7b8844cc790efc2045e48ce36e52e8cfd820d57f6ed4b62a557854e` | `unknown_timing_yellow`, live use blocked until as-of/source freshness is explicit |
| `stats_context/player_roster_display_context` | 6,353 | `06a0cb690d419bce4ae47a442b2fe0b101b699dfb7d895282353ed25188c7157` | `live_draft_day_candidate` |
| `stats_context/player_weekly_roster_display_context` | 93,428 | `e2bc056e6b72ce78066e07e32470d4d87aa9bc8ca194855ce8acd948e0ad5878` | `live_draft_day_candidate` |
| `stats_context/player_usage_context` | 156,389 | `50bbfd0f79ed7bfe3ca0c8ac2453da27da777ca29369081154e57a1b93747410` | mixed; package live use false |
| `stats_context/player_stats_crosscheck_report` | 12 | `327a276fd0c18801a1e239a29bc210cc1e3ca58467121452ed5c9991e053deda` | source audit only |

Validation notes:

- All regenerated candidate rows include `source_timing_class`,
  `live_use_allowed`, and `timing_notes`.
- Participation rows remain `live_use_allowed=false`.
- `stats_context` `latest_approved` count remained `0`.
- The pinned live-test snapshot was not modified.
- No raw shared-data files are committed by this document.

## PBP-Derived Feature Package Plan

The next backtest-only planning layer should use nflverse PBP/team-stat source
material to design, not yet approve, these display/backtest candidate packages:

| Proposed package | Feature categories | Status |
| --- | --- | --- |
| `stats_context/player_red_zone_goal_line_context` | Carries/targets inside 20/10/5, goal-to-go rushes/targets, red-zone touchdowns, red-zone first downs | Plan only |
| `stats_context/team_environment_context` | Team plays, pass rate, run rate, neutral-script pass rate, pace, score differential context, PROE if derivable, team scoring environment | Plan only |
| `stats_context/qb_rushing_context` | QB rush attempts, designed-rush versus scramble split if safely derivable, goal-line QB rushing | Plan only |
| `stats_context/qb_pressure_context` | Sacks, pressures, pass rushers, blitz context, sack-fumble context, QB pressure proxies | Plan only |

These packages must remain backtest-only/latest-candidate until a later source
policy approves any broader use.

## Non-Blocking Gaps

The following gaps do not block the first serious backtest:

- Direct live 2026 injury/practice feed.
- Exact routes run by each player.
- True targets per route run.
- True route participation percentage.
- Direct offensive line grades.
- Paid/vendor coverage for injury, depth, OL, and true route metrics.

These gaps should stay on the source roadmap and Deep Research follow-up list,
but they are improvements rather than first-backtest blockers.

## Fields And Uses That Remain Blocked

The following remain blocked from private value, model inputs, hidden sort,
recommendations, simulation drivers, and final draft-day decisions:

- ADP and market fields.
- Fantasy points and fantasy points PPR.
- External projections.
- External rankings.
- EPA/CPOE/WOPR/PACR/RACR/share/expected/diff fields until backtested and
  explicitly upgraded.
- Any field without an as-of cutoff.
- Any season-end summary used as though it were available before the simulated
  decision date.

## Implementation Roadmap

1. Regenerate display-only stats candidates after scoring-aligned field and
   timing metadata updates.
2. Create PBP-derived feature design docs before writing derived package code.
3. Build an as-of-safe backtest dataset generator.
4. Run baseline backtests with simple factual usage/counting fields.
5. Add enhanced role/volume features and compare incremental signal.
6. Test advanced fields separately under YELLOW backtest-only controls.
7. Require Tim/Master/QA review before any model/private-value proposal.

## Master Verdict

GREEN for first serious backtest readiness after the sprint items are recorded
and candidate metadata is regenerated.

YELLOW for all model-use decisions.

RED for direct stats/ADP/market/projection use as private value, hidden ranking,
recommendations, simulations, or final draft decisions before approval.
