# NWR Backtest As-Of And Leakage Rules V1

Owner: Master/Main HQ

Status: Required guardrail before any model/source backtest. This document does
not approve private value, ranking, hidden sort, recommendation, simulation,
final draft-day decision, deployment, or `latest_approved`.

## Core Rule

Every feature used in a backtest must have an explicit as-of date or cutoff.
If the feature cannot prove when it would have been known, it is not eligible
for the simulated decision window.

## Required As-Of Fields

Every generated backtest row or feature group must carry:

- `feature_as_of`
- `source_snapshot_path` or source identifier
- `source_created_at` where available
- source dataset name
- `source_timing_class`
- `live_use_allowed`
- leakage review status
- notes for any stale, inferred, or manually assigned timing

## Leakage Blocks

The following are prohibited:

- Target-season future data in prediction windows.
- Season-end summaries when simulating preseason decisions, unless the season
  is strictly prior to the prediction season.
- Post-game stats used before that game happened.
- 2025+ depth-chart snapshots used before their timestamp.
- 2023+ participation fields treated as live in-season data.
- Future injury/practice updates used before their report timestamp.
- ADP/market/ranking/projection data used as private value or model input.
- Fantasy points or fantasy points PPR used as model features.
- External projections or rankings used as model features.
- Any hidden sort, recommendation, or draft-decision output from exploratory
  features.

## Window Rules

### Preseason Or Draft-Day Backtest

Allowed:

- Prior-season finalized stats.
- Prior-season roster/profile metadata.
- Prior-season participation if treated as historical.
- Current pre-draft league truth only if it was known at the simulated date.
- Display-only ADP/market context only in separate non-model analysis.

Blocked:

- Same-season future weekly stats.
- Same-season final season totals.
- Future depth charts, injuries, rosters, or transactions.
- Any final fantasy scoring outcome from the target window.

### In-Season Rolling Backtest

Allowed:

- Stats through the prior completed week.
- Snap counts through the prior completed week.
- Current roster/depth/injury state only as of the simulated date.

Blocked:

- Current week final stats before game completion.
- Later-season aggregates.
- Participation data that was not available in-season.

### Next-Season Backtest

Allowed:

- All prior seasons that were complete before the prediction date.
- Offseason context with documented source dates.

Blocked:

- Target-season outcomes, final totals, fantasy points, and future roster moves.

## Source-Specific Rules

### nflverse Player Stats

- Weekly stats can be live/in-season display candidates when refreshed and
  as-of labeled.
- Season stats require explicit distinction between season-to-date and final
  season aggregate.
- Final season aggregates are offseason/finalized context.

### nflverse Participation

- 2023+ participation is historical/offseason/backtest-only because it arrives
  after all postseason games are completed.
- It cannot be used as live in-season or draft-day data.
- `route` is the primary receiver route, not every receiver route.

### Depth Charts

- 2025+ depth charts require timestamp assignment.
- Backtests must select the latest depth chart at or before the simulated date.
- Staleness must be visible in reports.

### Injuries

- Historical injury/practice fields are useful when as-of dates are available.
- A live 2026 nflverse injury/practice feed is not confirmed in the local probe.
- Any live injury fallback source requires separate source-policy approval.

### ADP And Market

- ADP/market is display-only context.
- It is never private value.
- It is never hidden sort.
- It is never a recommendation or simulation decision driver.

## Backtest Reporting Requirements

Every backtest report must include:

- Train/test seasons and windows.
- Prediction date/cutoff.
- Feature groups used.
- Source timing classes used.
- Explicit excluded fields.
- Leakage audit result.
- Missingness by position.
- Metrics by position: RMSE, MAE, Spearman rank correlation, top-N hit rate,
  and calibration if probabilities are produced.

## Approval Gates

Backtest output is advisory only until Tim/Master/QA approves a later source
policy. A successful backtest still does not automatically approve:

- `veteran_private_values` changes.
- Rookie board changes.
- Mock Draft recommendations.
- Hidden ranking/sort.
- Simulations.
- Final draft-day advice.
- Deployment.

## Master Verdict

GREEN as a leakage-control rule set.

YELLOW for any feature with unresolved timing.

RED for any model or live workflow that cannot prove as-of safety.
