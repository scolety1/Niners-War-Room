# API-SPORTS Injury Display Context V0

Owner: Master/Main HQ

Status: YELLOW source-risk, display-only live injury fallback. This document
does not approve private value, rankings, hidden sort, recommendations,
simulations, model training, final draft decisions, deployment, or
`latest_approved`.

## Purpose

API-SPORTS is a fallback source for live/current injury and practice-status
context because the local nflverse probe did not provide a reliable live 2026
injury feed.

This source is useful for human-readable health sanity checks and source
cross-checking. It must not alter Mock Draft logic, rankings, private values, or
recommendations.

## Credential Handling

The script reads the API key only from the process environment variable:

`NWR_API_SPORTS_KEY`

The key must not be committed, written to repo files, written to reports, or
printed in logs. Diagnostics redact authorization details and record only
SET/MISSING status outside the script.

If Codex cannot see the process env var but Windows User scope is set, invoke the
script from a shell that loads the User-scope value into the current process
without printing it.

## Script

`scripts/api_sports_injury_display_context_v0.py`

Behavior:

- Discovers NFL team IDs through API-SPORTS when team IDs are not provided.
- Fetches injury rows team-by-team.
- Enforces a default request budget guard of 80 calls.
- Writes local-only schema diagnostics under:
  `C:\NWR_SHARED_DATA\vendor_spikes\api_sports_injuries\`
- Writes a local-only report under:
  `C:\NWR_SHARED_DATA\scheduled_ingest\reports\availability_context\`
- Optionally writes a Lane Exchange `latest_candidate` package only.
- Never writes `latest_approved`.

## Candidate Package

`availability_context/api_sports_injury_display_context`

Candidate schema:

- `source_name`
- `source_risk`
- `collected_at`
- `season`
- `team`
- `api_sports_team_id`
- `api_sports_player_id`
- `player_name`
- `normalized_player_name`
- `position`
- `injury_status`
- `practice_status`
- `injury_type`
- `injury_notes`
- `game_week`
- `game_date`
- `last_update`
- `stale_flag`
- `match_status`
- `matched_sleeper_id`
- `matched_gsis_id`
- `matched_player_id`
- `source_notes`

## Manifest Policy

Required manifest flags:

- `approval_status`: `candidate`
- `source_name`: `API-SPORTS`
- `source_risk`: `YELLOW_LICENSE_AND_CURRENT_ONLY`
- `contains_private_value`: false
- `contains_market_data`: false
- `contains_adp`: false
- `contains_health_status`: true
- `historical_coverage`: `current_only_from_api`

Allowed use:

- display-only
- live injury context
- practice status context
- draft-day health sanity
- source cross-check

Blocked use:

- private value
- hidden sort
- rankings
- model training
- recommendations
- simulations
- final draft decisions
- deployment without approval

## Identity Matching

V0 attempts source-backed identity matching from existing local display context
crosswalk candidates when present:

- `stats_context/player_roster_display_context`
- `stats_context/player_weekly_roster_display_context`

Matching is by normalized name, team, and position. Ambiguous rows are reported
as ambiguous and not silently merged.

## Request Budget

Free-tier planning assumes a conservative ceiling of 80 requests per run. The
script fails closed if projected team discovery plus team-by-team injury calls
would exceed that threshold.

## Live Probe Result

Initial 2026 team-discovery probing returned a sanitized API-SPORTS plan
restriction:

`Free plans do not have access to this season, try from 2022 to 2024.`

Result:

- No 2026 live injury candidate package was created.
- The script refused to write `latest_candidate` because there were zero
  normalizable current injury rows.
- API-SPORTS remains YELLOW until Tim confirms the key/plan covers current 2026
  NFL injury data or approves a supported-season schema-only probe.

## How It Differs From nflverse Injury History

nflverse injury history is useful for backtests where historical report dates
are available. API-SPORTS V0 is a current/live display fallback and should be
treated as current-only unless a later source review proves historical coverage
and licensing.

API-SPORTS does not block Backtest V0 because Backtest V0 intentionally avoided
live injury features.

## Future Scheduling

This source may later be added to Scheduled Data Refresh after Tim/Master
approval. No scheduled task is created by V0.

## Master Verdict

YELLOW. Useful as display-only live injury/practice context if the API endpoint
and key work, but blocked from model/private-value/draft-decision use.
