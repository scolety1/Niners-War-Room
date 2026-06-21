# Stats Context Timing Metadata Regeneration Checkpoint - 2026-06-21

## Purpose

This checkpoint records the local-only regeneration of display-only
`stats_context` Lane Exchange `latest_candidate` packages with Source Timing
Metadata V1.

The regenerated package files live under `C:\NWR_SHARED_DATA` and are not
committed to Git. This document records row counts, SHA256 hashes, timing
classification, and guardrail validation for Master coordination.

## Scope

Source snapshot:

`C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260621_000000_nflverse_expansion_v1`

Local-only regeneration report:

`C:\NWR_SHARED_DATA\scheduled_ingest\reports\stats_source_v1\STATS_CONTEXT_TIMING_METADATA_REGEN_20260621.md`

Approval scope:

- `latest_candidate` display/stat context only
- no `latest_approved`
- no private value
- no rankings
- no hidden sort
- no recommendations
- no simulations
- no model training
- no final draft decisions

## Regenerated Packages

| Package | Rows | SHA256 | Timing classification | Manifest live use |
| --- | ---: | --- | --- | --- |
| `stats_context/player_weekly_stats_display_context` | 38,402 | `5fa062b53aa9ea18cad7b90bf0b64cd2e07c81e2daf6b0cd965623c18574865b` | `live_draft_day_candidate` | true |
| `stats_context/player_season_stats_display_context` | 4,017 | `fac5c17ecb5a736d8be3ba230aee03365bc27e08a55f9baf9e557b10ca0537e3` | `offseason_refresh_only` | false |
| `stats_context/player_roster_display_context` | 6,353 | `06a0cb690d419bce4ae47a442b2fe0b101b699dfb7d895282353ed25188c7157` | `live_draft_day_candidate` | true |
| `stats_context/player_weekly_roster_display_context` | 93,428 | `e2bc056e6b72ce78066e07e32470d4d87aa9bc8ca194855ce8acd948e0ad5878` | `live_draft_day_candidate` | true |
| `stats_context/player_usage_context` | 156,389 | `50bbfd0f79ed7bfe3ca0c8ac2453da27da777ca29369081154e57a1b93747410` | mixed: `historical_backtest_only`, `live_draft_day_candidate`, `unknown_timing_yellow` | false |
| `stats_context/player_stats_crosscheck_report` | 12 | `74a139b671a86a28e2153ab3fcddbc10f11c144ce7fbdb2184ef914835754c3f` | mixed source audit | false |

## Timing Metadata Validation

All regenerated candidate rows include:

- `source_timing_class`
- `live_use_allowed`
- `timing_notes`

All regenerated manifests include timing summaries:

- `source_timing_summary`
- `source_timing_classes`
- `live_use_allowed`
- `timing_notes`

Participation validation:

- `player_usage_context` participation rows: 91,103
- participation `live_use_allowed`: all `False`
- participation remains historical/offseason/backtest-only for the 2023+
  nflverse/FTN timing caveat

## Guardrail Validation

- `stats_context/latest_approved.json` count remained `0`.
- The pinned snapshot remained present and untouched.
- No repo files were changed by the local regeneration itself.
- No shared-data files were committed.
- No raw nflverse/API data was committed.
- No private value, ranking, hidden sort, recommendation, simulation, model
  training, final draft decision, deployment, or Mock Draft logic was changed.

## Notes

`player_usage_context` is intentionally not live-use allowed at the manifest
level because it mixes:

- `snap_counts`: live/draft-day display candidate if refreshed
- `participation`: historical/offseason/backtest-only for 2023+
- `opportunity`: `unknown_timing_yellow` until source-specific timing is reviewed

Any consumer must inspect row-level timing fields or use a filtered view before
treating usage context as live display material.

## Recommended Next Steps

1. Deep Research source coverage audit.
2. Injury/depth/Sportradar source decision.
3. PBP-derived red-zone/team-environment candidate planning.
4. Backtest-only feature dataset plan.

## Master Verdict

GREEN for local-only stats timing metadata regeneration.

YELLOW for any model/private-value use. These packages remain display/stat
context `latest_candidate` only.
