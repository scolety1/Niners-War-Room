# NWR Source Timing Taxonomy Correction Plan - 2026-06-21

Owner: Master/Main HQ

Status: Corrective source-policy plan. This document does not approve private
value, rankings, hidden sort, recommendations, simulations, final draft-day
decisions, deployment, or `latest_approved`.

## Purpose

Deep Research found that the current source coverage is sufficient for first
backtest work, but the source timing taxonomy needs sharper boundaries before
any feature generator or model backtest begins.

## Correction 1: Season Stats

Previous broad classification:

- `season_stats` = `offseason_refresh_only`

Corrected classification:

- Season-to-date summaries can be live/in-season display candidates when they
  are built from a current player-stats source and labeled with an explicit
  as-of cutoff.
- Final full-season aggregates remain offseason/finalized historical context.
- If the normalizer cannot prove which mode applies, classify season stats as
  `unknown_timing_yellow` and set `live_use_allowed=false`.

Implementation note:

- The normalizer now treats `season_stats` as `unknown_timing_yellow` until
  source freshness and as-of semantics are explicit.

## Correction 2: Injuries

Current reality:

- Historical injury and practice-status fields are useful where available.
- The local nflverse runtime probe did not provide a live 2026
  injury/practice feed.
- 2026 live injury status requires a fallback source if NWR wants draft-day or
  in-season live injury context.

Policy:

- Historical injury data may be used for backtest research with correct as-of
  cutoffs.
- Live 2026 injury/practice status is not covered by the current nflverse
  source path.
- Any injury fallback source must be evaluated for license, freshness,
  identity mapping, and display-only policy before package creation.

## Correction 3: 2025+ Depth Charts

Current reality:

- 2025+ depth charts use timestamped snapshots rather than simple week-keyed
  rows.

Policy:

- Depth-chart rows require timestamp/as-of assignment.
- Consumers must show or enforce stale-data warnings.
- Backtests must choose the latest depth-chart snapshot available at or before
  the simulated decision date.
- No future depth-chart snapshot may be used in a prior prediction window.

## Timing Classes For Backtest Planning

| Class | Use |
| --- | --- |
| `live_draft_day_candidate` | Display-only live context if source freshness is verified. |
| `historical_backtest_only` | Backtest and historical research only; not live draft-day context. |
| `offseason_refresh_only` | Offseason/finalized context; not live decision context unless prior-season only. |
| `unknown_timing_yellow` | Block live use until as-of/source timing is resolved. |
| `display_only` | Audit/report context only. |

## Required Consumer Behavior

- Read `source_timing_class`, `live_use_allowed`, and `timing_notes`.
- Respect row-level timing when a package mixes datasets.
- Treat package-level `live_use_allowed=false` as a hard stop for live use
  unless a filtered row-level view is created and approved.
- Keep participation-derived fields historical/offseason/backtest-only for
  2023+ unless a separate live source is approved.

## Master Verdict

GREEN for corrected taxonomy.

YELLOW for any source with unclear timing, missing 2026 live feed, or mixed
dataset timing.

RED for any backtest or live workflow that ignores as-of cutoffs or uses future
data.
