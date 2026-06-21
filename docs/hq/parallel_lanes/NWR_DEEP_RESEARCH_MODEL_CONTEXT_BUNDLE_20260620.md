# NWR Deep Research Model Context Bundle - 2026-06-20

This bundle is sanitized for external/Deep Research review. It intentionally excludes raw private value rows, raw Sleeper roster/user data, raw Lane Exchange data, and local-only package contents.

Use this as the complete context for auditing whether Niners War Room is missing important dynasty-value signals.

## 1. League Settings

League: Las Vegas Enginerds

Format:

- 10 teams
- dynasty/keeper hybrid
- 1QB
- no superflex
- non-PPR
- no TE premium
- rushing and receiving first-down scoring
- no passing first-down scoring
- kicker included
- defense/IDP not used for current NWR player model

Lineup / roster slots from league settings:

- Starters: `QB`, `RB`, `RB`, `WR`, `WR`, `WR`, `TE`, `FLEX`, `FLEX`, `K`
- Bench: 18 bench slots
- Total roster slots: 28
- FLEX is treated as non-superflex skill-position flex context.

Scoring settings from league settings:

| Category | Setting |
| --- | --- |
| Passing yards | `0.0333333333` per yard, roughly 1 point per 30 yards |
| Passing TD | `3` |
| Passing INT | `-1` |
| Passing 2PT | `2` |
| Rushing yards | `0.1` per yard |
| Rushing TD | `4` |
| Rushing first down | `0.4` |
| Rushing 2PT | `2` |
| Receiving yards | `0.1` per yard |
| Reception | `0` |
| Receiving TD | `4` |
| Receiving first down | `0.4` |
| Receiving 2PT | `2` |
| Fumble lost | `-1` |
| Kick return yards | `0.0333333333` per yard |
| Punt return yards | `0.0333333333` per yard |
| Special teams TD | `4` |
| Fumble recovery TD | `4` |
| XP made | `1` |
| FG 0-19 | `2` |
| FG 20-29 | `2` |
| FG 30-39 | `2` |
| FG 40-49 | `3` |
| FG 50+ | `4` |

Current model implication:

- Elite RB/WR/flex assets should matter more than replaceable QBs.
- QB values need real 1QB VORP/rushing separation to carry premium value.
- TEs need real no-premium VORP/route/target separation to justify premium value.
- Empty receptions should not be overvalued.
- First-down production and chain-moving role matter for RB/WR/TE evaluation.

## 2. Current Source Stack

| Source | Current role | Status |
| --- | --- | --- |
| Sleeper | League truth: settings, rosters, users/team mappings, draft order, traded picks, transactions, ownership evidence | GREEN for league-state truth |
| nflverse / nflreadpy | Historical/player stats and usage context | GREEN for display/stat context; model use blocked |
| CollegeFootballData | Rookie/college yearly refresh candidate | Candidate only; requires API key and Rookie HQ guardrails |
| RotoWire | Optional paid display context for projections/news/injuries | YELLOW, blocked by API key/license/field verification |
| Market/ADP/rankings/projections/trade calculators | Display-only context if later approved | Must never become NWR private value |

Source firewall:

- Sleeper can define league truth, ownership, rosters, pick order, and transaction evidence.
- nflverse can provide historical factual stats and role/usage context.
- Market/ADP may support opponent behavior, likely availability, and pick timing only if approved later.
- Public rankings, ADP, trade calculators, projection systems, and market values must not drive NWR private value, hidden sort, or rankings.

## 3. Current Model / Input Status

Veteran private value:

- Exists as a stripped/manual private-value Lane Exchange package.
- Current package status: approved for controlled local live-test/simulation scope only.
- Raw rows are intentionally excluded from this bundle.
- Safe schema summary only:
  - `asset_id`
  - `player`
  - `position`
  - `nfl_team`
  - `nwr_private_rank`
  - `nwr_private_value`
  - `value_source`
  - `source_status`
  - `trust_status`
  - `pool_status`
  - `separation_note`
- Current row count: 232.
- Current safety note: private values are internal/manual and must not be blended with ADP, market rank, market value, projections, probability bands, hidden sort fields, or external model leakage.

Rookie board / rookie input:

- Exists as manually curated/frozen Rookie HQ input.
- Current approved local-live-test row count: 54.
- Safe schema summary:
  - `rookie_rank`
  - `player`
  - `position`
  - `nfl_team`
  - `age`
  - `nfl_draft_capital`
  - `depth_chart_role`
  - `tier_label`
  - `draft_action`
  - `warning_severity`
  - `manual_question`
  - `board_order_frozen`
- This input is approved only within current local-live-test/rehearsal scope, not as broad final draft-day approval.

Outcome V1:

- Exists as optional display-only long-term outcome columns.
- Outcome display snapshot is not required for Mock Draft controlled local rehearsal.
- No Outcome package is currently pinned or required.
- Outcome columns referenced in Master status docs:
  - QB T12
  - RB T12
  - RB T24
  - WR T12
  - WR T24
  - WR T36
  - TE T12

Mock Draft:

- Controlled local simulation/rehearsal used a pinned snapshot.
- The controlled simulation output is not final draft advice.
- Final draft-day use, final recommendation paths, hosted deployment, production app wiring, private-value changes, source-data mutation, and broad simulation/recommendation paths remain blocked until explicit Tim/Master approval.

## 4. Current Stats Pipeline Status

Current nflverse display candidates:

- `stats_context/player_weekly_stats_display_context`
- `stats_context/player_season_stats_display_context`
- `stats_context/player_usage_context`
- `stats_context/player_stats_crosscheck_report`

Current kept display/stat field categories:

- identity fields
- team
- position
- season
- week
- passing attempts/completions/yards/TD/INT
- rushing attempts/yards/TD
- receiving targets/receptions/yards/TD
- passing/rushing/receiving first downs when present
- offensive snaps
- defensive snaps
- special-teams snaps
- snap percentages

Current missing expansion targets:

- `rosters`
- `weekly_rosters`
- `participation`
- `opportunity`

Expansion purpose:

- Improve role context, identity metadata, availability, games/experience context, route/participation context, opportunity context, and display/backtest inventory.
- Do not approve any model/private-value use from expansion alone.

## 5. Current Field Policy V1 Summary

GREEN future-test categories:

- games played
- age / experience / roster metadata
- rosters / weekly_rosters
- participation
- opportunity
- air yards
- YAC
- sack metrics
- fumble metrics
- return stats
- first-down production/rates
- snap share trends
- target/carry trends

GREEN means suitable for local-only display candidates and future backtest inventories. It does not mean approved for private value or model use.

YELLOW backtest-only categories:

- EPA
- CPOE
- WOPR
- PACR
- RACR
- target_share
- air_yards_share
- advanced efficiency/share/expected/diff fields

YELLOW fields may be useful, but must remain display-only or backtest-only until proven out of sample and approved by Tim/Master/QA.

RED blocked categories:

- `fantasy_points`
- `fantasy_points_ppr`
- `headshot_url` for modeling
- penalties
- misc_yards
- most fumble recovery fields
- kicker detail buckets for current format
- defensive stats unless IDP is added
- 2-point conversion fields as predictive inputs

RED fields can remain in raw local snapshots for audit if needed, but are blocked from model/ranking/private-value use in current policy.

## 6. Current Hard Guardrails For Research

- Deep Research output is advisory only.
- No ADP/market in private value.
- No hidden market sort.
- No projection blending.
- No stats-to-model integration without backtest and Tim/Master/QA approval.
- No draft recommendations or final advice approval from research alone.
- No raw private values should be requested or used.
- No raw Sleeper private roster/user data should be requested.
- No final draft-day approval can be granted by this research.
- No hosted deployment, production app wiring, or simulation/recommendation approval can be granted by this research.

## 7. Current Safe Backtest Proposal

Baseline cohort:

- current kept display fields only
- identity/team/position/season/week
- basic passing/rushing/receiving counting stats
- first-down fields
- snap counts/snap percentages

Enhanced volume/role cohort:

- games played
- age / experience
- roster and weekly roster metadata
- snap share trends
- route/participation/opportunity if available
- air yards
- YAC
- target trends
- carry trends
- first downs per target/carry/reception
- yards per opportunity

Advanced cohort:

- EPA
- CPOE
- WOPR
- PACR
- RACR
- target share
- air-yards share
- other advanced efficiency/share/expected/diff fields

Targets:

- next-season NWR scoring
- next-8-week NWR scoring
- positional finish probabilities
- position-specific value translation by QB/RB/WR/TE

Metrics:

- RMSE
- MAE
- Spearman rank correlation
- top-N hit rate
- calibration if probability targets are used

Evaluation rules:

- Evaluate separately by QB/RB/WR/TE.
- Compare baseline versus enhanced volume/role versus advanced cohorts.
- Check whether advanced fields add incremental signal beyond simple usage/counting stats.
- Check stability and missingness.
- Keep all results out of private value until reviewed and approved.

## 8. Questions For Deep Research

Please answer these questions for a 10-team, 1QB, non-PPR dynasty/keeper hybrid league with 0.4 rushing and receiving first-down scoring:

1. Are we missing important dynasty-value signals?
2. Are our GREEN/YELLOW/RED field categories correct?
3. Which fields should we test first?
4. Which fields should remain display-only forever?
5. Which model target is safest and most useful: next-season scoring, next-8-week scoring, positional finish probability, or another target?
6. What architecture should we use for backtesting and eventual model candidates?
7. What source types are missing, if any?
8. What are the biggest leakage risks?
9. How should we handle 1QB suppression, no-PPR receiving roles, no-TE-premium TE evaluation, and first-down scoring?
10. What should remain blocked until manual Tim/Master/QA approval?

## 9. Requested Deep Research Output Format

Please return:

1. Executive verdict.
2. Missing signal list, ordered by likely value.
3. Field policy critique: GREEN/YELLOW/RED changes recommended.
4. Backtest plan improvements.
5. Model-target recommendation.
6. Position-by-position notes for QB/RB/WR/TE.
7. Source gaps and licensing/audit concerns.
8. Leakage and overfitting risks.
9. Recommended implementation order.
10. Items that must remain blocked.
