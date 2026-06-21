# nflverse Source Timing Metadata V1

## Purpose

Stats Expansion V1 added broader nflverse display candidates. Source Timing
Metadata V1 embeds timing classification into normalizer rows, manifests, and
reports so future consumers cannot accidentally treat historical/offseason-only
fields as live draft-day inputs.

This is metadata only. It does not approve private value, rankings, hidden sort,
model training, recommendations, simulations, final draft decisions, deployment,
or `latest_approved`.

## Fields Added

Normalized candidate rows now include:

- `source_timing_class`
- `live_use_allowed`
- `timing_notes`

Candidate manifests and `latest_candidate.json` pointers now include:

- `source_timing_summary`
- `source_timing_classes`
- `live_use_allowed`
- `timing_notes` in manifests

## Timing Classes

| Timing class | Meaning |
| --- | --- |
| `live_draft_day_candidate` | May be used as display-only live/draft-day context if the source snapshot is fresh and no later gate blocks it. |
| `historical_backtest_only` | Historical/backtest use only; not live draft-day context. |
| `offseason_refresh_only` | Season-level/offseason refresh context; not live draft-day context. |
| `display_only` | Audit/display row only. |
| `unknown_timing_yellow` | Timing is not sufficiently classified; live use blocked until review. |

## Initial Dataset Timing Policy

| Dataset | Timing class | Live use allowed | Notes |
| --- | --- | --- | --- |
| `weekly_stats` | `live_draft_day_candidate` | true | Display-only weekly stats if refreshed; subject to corrections/staleness. |
| `season_stats` | `unknown_timing_yellow` | false | Season-to-date summaries may be live/in-season display candidates when built from a current player-stats source, but final season aggregates remain offseason/finalized context. Require explicit as-of/source freshness before live use. |
| `rosters` | `live_draft_day_candidate` | true | Current roster metadata if refreshed; stale data must be visible. |
| `weekly_rosters` | `live_draft_day_candidate` | true | Weekly roster/status context if current source supports it. |
| `snap_counts` | `live_draft_day_candidate` | true | After-game snap context; not projections. |
| `participation` | `historical_backtest_only` | false | 2023+ FTN participation arrives after all post-season games and does not update during season. |
| `opportunity` | `unknown_timing_yellow` | false | Needs source-specific timing review before live use. |
| `normalizer_warning` | `display_only` | false | Audit/warning rows only. |

## Participation Caveat

nflreadr/nflverse documentation says participation data prior to 2023 came from
NFL NGS. Participation data from 2023 onward is courtesy of FTN and is provided
after all post-season games are completed; it does not update during the season.

Therefore participation-derived fields such as `players_on_play`,
`offense_players`, `defense_players`, `offense_personnel`, `route`, and
`was_pressure` are historical/offseason/backtest-only for 2023+ unless a later
source policy approves a separate live source.

`route` remains the primary receiver route on a play, not every receiver route.

## Guardrails

- `latest_candidate` may include timing metadata.
- `latest_approved` must not be created or updated by this metadata work.
- Stats remain display/stat context only.
- Stats are not private value.
- Stats are not rankings.
- Stats are not hidden sort keys.
- Stats are not model training inputs.
- Stats are not recommendations.
- Stats are not simulations.
- Stats are not final draft decisions.
- Stats must not alter Mock Draft logic.

## Season Stats Correction

The original V1 policy classified `season_stats` as broadly
`offseason_refresh_only`. That was too coarse.

Corrected rule:

- Season-to-date summaries can be live/in-season display candidates when built
  from a current player-stats source and labeled with an explicit as-of cutoff.
- Final full-season aggregates remain offseason/finalized historical context.
- Until the normalizer or consumer can prove which mode applies, `season_stats`
  rows are classified as `unknown_timing_yellow` and `live_use_allowed=false`.

## Recommended Next Step

Run the normalizer in dry-run mode against the latest nflverse snapshot and review
the timing section of the report. Only after review should Master decide whether
to regenerate display-only `latest_candidate` packages with the new timing
metadata. Even then, `latest_approved` remains blocked.
