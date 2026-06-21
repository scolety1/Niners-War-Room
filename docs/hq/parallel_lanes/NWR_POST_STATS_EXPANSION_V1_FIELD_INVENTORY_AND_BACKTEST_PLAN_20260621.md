# Post Stats Expansion V1 Field Inventory And Backtest Plan - 2026-06-21

## Purpose

This checkpoint updates the post-Stats-Expansion-V1 field inventory with an
explicit timing policy. The goal is to prevent NWR from treating historical or
season-end-only nflverse fields as live draft-day inputs.

No field in this document is approved for private value, hidden ranking/sort,
model training, recommendations, simulations, or final draft decisions.

## Source Timing Note

nflreadr/nflverse documentation states that participation data prior to 2023 came
from NFL NGS. Participation data from 2023 onward is courtesy of FTN and is
provided after all post-season games are completed; it does not update during the
season.

References reviewed:

- `https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html`
- `https://nflreadr.nflverse.com/reference/load_participation.html`
- `https://nflreadr.nflverse.com/articles/dictionary_participation.html`

Practical NWR consequence:

- Participation-derived fields are excellent for historical backtests and
  offseason refreshes.
- Participation-derived fields are not reliable live-refresh draft-day signals
  for current-season use.
- Participation-derived fields must remain display-only or backtest-only until a
  later Tim/Master/QA policy approves a specific model use.

## Current V1 Candidate Packages

| Package | Rows | SHA256 | Status |
| --- | ---: | --- | --- |
| `stats_context/player_roster_display_context` | 6,353 | `a458d0287a2c3bb020caf60fa256e666d31bf448f884116afb05547581b1f89e` | `latest_candidate`, display-only |
| `stats_context/player_weekly_roster_display_context` | 93,428 | `4fd9df34056b68582cf31454691ce86a964bb65523d22b1632ad11a8eb25b734` | `latest_candidate`, display-only |
| `stats_context/player_usage_context` | 156,389 | `dcceceeaf8fc5e2ded49b57d335a260efe3242f1cf48a45af0529b396db46a41` | `latest_candidate`, display-only |
| `stats_context/player_stats_crosscheck_report` | 12 | `0ad44ddb740893b37217cd017e703bae77bea36da57de0da5657aaa436d64f69` | `latest_candidate`, source audit |

No `stats_context` package is approved. No `latest_approved` was created.

## Exact V1 Field Inventory

### `player_roster_display_context`

Fields:

`source_dataset`, `source_file`, `source_row_count`, `source_row_number`,
`context_type`, `approval_status`, `allowed_use`, `blocked_use`, `gsis_id`,
`pfr_id`, `espn_id`, `sportradar_id`, `yahoo_id`, `rotowire_id`,
`fantasy_data_id`, `sleeper_id`, `smart_id`, `full_name`, `football_name`,
`first_name`, `last_name`, `position`, `ngs_position`, `team`, `season`,
`week`, `game_type`, `depth_chart_position`, `jersey_number`, `status`,
`status_description_abbr`, `birth_date`, `height`, `weight`, `college`,
`years_exp`, `entry_year`, `rookie_year`, `draft_club`, `draft_number`.

Timing classification:

| Field/category | Live/draft-day usable | Historical backtest usable | Offseason-refresh usable | Display-only | Notes |
| --- | --- | --- | --- | --- | --- |
| Source/audit fields | No | Yes | Yes | Yes | Audit only, never model input. |
| Player IDs and names | Yes, if snapshot is fresh | Yes | Yes | Yes | Identity linking only. |
| Position/team/status/depth chart/jersey | Yes, if snapshot is fresh | Yes | Yes | Yes | Useful for roster/status review, not private value. |
| Birth date/height/weight/college/experience/draft metadata | Limited | Yes | Yes | Yes | Better for offseason and backtest lifecycle context. |

### `player_weekly_roster_display_context`

Fields:

`source_dataset`, `source_file`, `source_row_count`, `source_row_number`,
`context_type`, `approval_status`, `allowed_use`, `blocked_use`, `gsis_id`,
`pfr_id`, `espn_id`, `sportradar_id`, `yahoo_id`, `rotowire_id`,
`fantasy_data_id`, `sleeper_id`, `smart_id`, `full_name`, `football_name`,
`first_name`, `last_name`, `position`, `ngs_position`, `team`, `season`,
`week`, `game_type`, `depth_chart_position`, `jersey_number`, `status`,
`status_description_abbr`, `birth_date`, `height`, `weight`, `college`,
`years_exp`, `entry_year`, `rookie_year`, `draft_club`, `draft_number`.

Timing classification:

| Field/category | Live/draft-day usable | Historical backtest usable | Offseason-refresh usable | Display-only | Notes |
| --- | --- | --- | --- | --- | --- |
| Weekly team/status fields | Yes, if latest pull is fresh | Yes | Yes | Yes | Good for current roster/status cross-checks. |
| Weekly identity/history | Limited | Yes | Yes | Yes | Useful for historical availability and team movement. |
| Age/experience/draft metadata | Limited | Yes | Yes | Yes | Same policy as roster package. |

### `player_usage_context`

Fields:

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

Timing classification:

| Field/category | Live/draft-day usable | Historical backtest usable | Offseason-refresh usable | Display-only | Notes |
| --- | --- | --- | --- | --- | --- |
| Source/audit/context fields | No | Yes | Yes | Yes | Audit and provenance only. |
| Identity/team/opponent/game fields | Yes, if source dataset is fresh | Yes | Yes | Yes | Used for joining and context, not value. |
| Snap counts: `offense_snaps`, `offense_pct`, `defense_snaps`, `defense_pct`, `st_snaps`, `st_pct` | Yes, if latest snap-count pull is fresh | Yes | Yes | Yes | Most live-friendly usage signal in V1. |
| Participation membership: `players_on_play`, `offense_players`, `defense_players`, names/positions/numbers | No for current-season live use | Yes | Yes, after season-end refresh | Yes | 2023+ participation is season-end-only. |
| Personnel/formation: `offense_formation`, `offense_personnel`, `n_offense`, `n_defense` | No for current-season live use | Yes | Yes, after season-end refresh | Yes | Historical role-context only for 2023+ seasons. |
| Pressure/route context: `was_pressure`, `route`, `ngs_air_yards` | No for current-season live use | Yes | Yes, after season-end refresh | Yes | YELLOW backtest-only for model research. |
| Opportunity/counting fields: attempts, receptions, air yards, yards, TD, first downs, INT, fumbles | YELLOW until source freshness is confirmed | Yes | Yes | Yes | Can support historical backtests; live use requires source timing review. |

### `player_stats_crosscheck_report`

Fields:

`source_dataset`, `source_file`, `source_row_count`, `source_column_count`,
`safe_display_field_count`, `quarantined_field_count`, `quarantined_fields`,
`approval_status`, `allowed_use`, `blocked_use`, `notes`.

Timing classification:

| Field/category | Live/draft-day usable | Historical backtest usable | Offseason-refresh usable | Display-only | Notes |
| --- | --- | --- | --- | --- | --- |
| Crosscheck/audit fields | No | Yes | Yes | Yes | Source-health and field-policy audit only. |
| Quarantine summary | No | Yes | Yes | Yes | Used to prevent unsafe fields from entering candidates. |

## Explicit Participation Field Classification

| Field/category | Current V1 status | Timing policy | Research/model policy |
| --- | --- | --- | --- |
| `players_on_play` | Kept in `player_usage_context` | Historical/offseason-refresh only for 2023+ | YELLOW backtest-only role-context candidate. |
| `offense_players` / `defense_players` | Kept | Historical/offseason-refresh only for 2023+ | Can build on-field participation evidence, not live. |
| `offense_personnel` | Kept | Historical/offseason-refresh only for 2023+ | Can build personnel group role context. |
| `defense_personnel` | Not in current V1 candidate | Historical/offseason-refresh only if added later | Future backtest-only field if source provides it. |
| `defenders_in_box` | Not in current V1 candidate | Historical/offseason-refresh only if added later | Future defensive box context candidate. |
| `number_of_pass_rushers` | Not in current V1 candidate | Historical/offseason-refresh only if added later | Future pressure context candidate. |
| `time_to_throw` | Not in current V1 candidate | Historical/offseason-refresh only if added later | Future QB/context candidate; avoid overfitting. |
| `was_pressure` | Kept | Historical/offseason-refresh only for 2023+ | YELLOW backtest-only pressure context. |
| `route` | Kept | Historical/offseason-refresh only for 2023+ | YELLOW backtest-only; this is the primary receiver route, not every receiver route. |
| Coverage fields such as man/zone or coverage type | Not in current V1 candidate | Historical/offseason-refresh only if added later | YELLOW backtest-only; not live-refresh. |

Important route caveat:

`route` is the route taken by the primary receiver on the play. It is not a full
route-run record for every receiver on the field.

## Field Category Status

| Category | Status | Timing |
| --- | --- | --- |
| Roster identity/status | GREEN display, not model-approved | Live/draft-day usable if fresh, historical/offseason usable. |
| Weekly roster identity/status | GREEN display, not model-approved | Live/draft-day usable if fresh, historical/offseason usable. |
| Snap counts/snap percentage | GREEN display, YELLOW model-backtest | More live-friendly than participation; still display-only in V1. |
| Opportunity counting fields | GREEN display, YELLOW source-timing review | Historical/backtest usable; live use requires schedule confirmation. |
| Participation membership/personnel/route/pressure | GREEN display, YELLOW backtest-only | Historical/offseason only for 2023+; not live draft-day. |
| Advanced/share/expected/EPA/CPOE/WOPR/PACR/RACR fields | YELLOW backtest-only if inventoried later | Not in current display candidates; must remain excluded unless policy changes. |
| Fantasy points, market, ADP, ranks, scores, private-value-like fields | RED blocked | Not allowed for private value or model/ranking use. |

## Model Signal Coverage Map

| Desired signal | Can build now? | Current evidence | Timing caveat | Status |
| --- | --- | --- | --- | --- |
| On-field participation | Yes, historically | `players_on_play`, `offense_players`, `defense_players`, names/positions/numbers | 2023+ season-end-only | YELLOW backtest-only |
| Personnel group role | Yes, historically | `offense_personnel`, `offense_formation`, `n_offense`, `n_defense` | 2023+ season-end-only | YELLOW backtest-only |
| Pressure context | Partially | `was_pressure`; future fields may add pass-rusher count/time-to-throw | 2023+ season-end-only for participation-derived context | YELLOW backtest-only |
| Defensive box context | Not yet | `defenders_in_box` not in current candidate | Needs additional source/field pass | Missing |
| Primary route context | Yes, historically | `route` | Primary receiver only; 2023+ season-end-only | YELLOW backtest-only |
| Exact routes run by player | No | V1 does not provide receiver-by-receiver route-run totals | Needs another source or careful inference | Missing |
| Targets per route run | No | Targets/opportunity and primary route exist, but true player routes are missing | Needs route-run denominator | Missing |
| True route participation percentage | No | On-field membership helps, but no full route-run counts | Needs another source or robust derivation | Missing |
| Offensive line grades | No | No grading source in V1 | Needs another licensed/source-approved provider | Missing |

## Backtest Plan Update

Backtests must split live-refresh features from historical/offseason-only
features. Do not mix timing categories without a leakage check.

Recommended backtest tiers:

1. Live-refresh candidate tier:
   roster/weekly roster identity/status, snap counts, snap percentages, basic
   weekly/season counting stats, and only fields whose source freshness is
   documented.
2. Historical/offseason participation tier:
   on-field participation, personnel, pressure, primary route, and play-level
   membership fields. These may be excellent dynasty role features, but they are
   not live in-season refresh fields for 2023+.
3. Advanced backtest-only tier:
   EPA, CPOE, WOPR, PACR, RACR, shares, expected/diff, and other advanced
   efficiency fields if a later inventory adds them. These remain YELLOW and must
   prove incremental signal beyond volume/snap/roster context.
4. RED blocked tier:
   fantasy points, market/ADP, rankings, scores, private-value-like fields,
   hidden sort fields, and any field that would leak target outcomes.

Evaluation targets remain:

- next-season NWR scoring
- next-8-week NWR scoring
- positional finish probabilities
- QB/RB/WR/TE-specific results

Metrics remain:

- RMSE
- MAE
- Spearman rank correlation
- top-N hit rate
- calibration if probabilistic targets are added

Any future model proposal must report performance separately for live-refresh
features and historical/offseason-only features.

## Recommended Next Build Step

Add source-timing metadata to nflverse stats candidates and normalizer reports:

- `source_timing_class`: `live_refresh`, `historical_backtest`,
  `offseason_refresh`, or `unknown_yellow`
- `live_use_allowed`: true/false
- `historical_backtest_allowed`: true/false
- `offseason_refresh_allowed`: true/false
- `timing_notes`

This should be a display/reporting metadata upgrade only. It must not create
`latest_approved`, private value, hidden sorting, recommendations, simulations,
or final draft-day decisions.

## Master Verdict

GREEN for documentation and field timing separation.

YELLOW for participation-derived model research because participation is
historical/offseason-only for 2023+ and must be backtested without live-data
assumptions.

RED for using any V1 stats field directly as private value, rankings, hidden
sort, recommendation logic, simulation decision logic, or final draft-day
decision input.
