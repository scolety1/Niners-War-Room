# NWR Stats Model Backtest Backlog - 2026-06-20

Owner: Master/Main HQ

Status: Backlog only. No model integration is approved.

## Current Policy

nflverse stats are display/stat-context `latest_candidate` packages only. They are not approved for private value, hidden rank/sort, recommendations, simulations, final draft-day decisions, or Mock Draft direct decision logic.

## GREEN Future-Test Fields

These are acceptable to inventory and backtest later because they are interpretable role, volume, or availability signals:

- games played
- age, experience, roster metadata
- roster and weekly roster status
- participation and route/snap involvement
- air yards
- yards after catch
- sack metrics
- fumble metrics
- return stats
- first-down production and first-down rates
- snap share trends
- target trends
- carry trends

## YELLOW Backtest-Only Fields

These may be useful, but require backtesting and audit before any policy change:

- passing EPA
- rushing EPA
- receiving EPA
- passing CPOE
- target share
- air-yards share
- WOPR
- PACR
- RACR
- expected/diff fields
- advanced efficiency fields
- advanced share fields

YELLOW fields must remain display-only or backtest-only until Tim/Master/QA explicitly approves a later source policy.

## RED Blocked Fields

These are blocked for model/private-value use in current format:

- `fantasy_points`
- `fantasy_points_ppr`
- `headshot_url` for modeling
- penalties
- misc yards
- most fumble recovery fields
- kicker detail buckets
- defensive stats unless IDP is added
- two-point conversion fields as predictive model inputs

## Missing Dataset Backlog

The next data expansion should focus on datasets that improve role context without changing model logic:

- `rosters`
- `weekly_rosters`
- `participation`
- `opportunity`

All expanded outputs remain local-only raw snapshots and display-only `latest_candidate` packages unless a later approval changes scope.

## Backtest Design

Future backtests should:

- avoid Mock Draft recommendation paths
- avoid private value integration
- avoid hidden ranking or sorting
- evaluate next-season and next-8-week NWR scoring outcomes
- evaluate by QB, RB, WR, and TE
- compare baseline kept display fields against expanded volume/usage fields
- compare advanced fields only as separate YELLOW cohorts
- measure RMSE, MAE, and rank correlation
- report whether advanced fields add signal beyond simple usage and counting stats

## Required Approval Before Implementation

Before any field becomes private value or model input, Tim/Master/QA must approve:

- source licensing and caching policy
- identity mapping policy
- leakage checks
- field cohort
- backtest result threshold
- rollback plan

## Master Verdict

GREEN for backlog creation.

YELLOW-HOLD for any model/private-value use.
