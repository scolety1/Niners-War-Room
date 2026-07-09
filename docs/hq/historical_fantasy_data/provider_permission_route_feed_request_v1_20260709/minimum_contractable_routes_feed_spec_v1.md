# Minimum Contractable Routes Feed Spec V1

## Purpose

This is the exact feed NWR needs to unlock true route-denominator work later. It is a request/specification, not an admitted source contract.

## Required Data Product

The provider must supply actual player-level `routes_run` counts for NFL pass catchers.

Required coverage:

- WR
- TE
- RB
- optionally FB if included in provider receiver tracking metrics

Required historical range:

- Preferred: 2017-current or better, matching ESPN Receiver Scores public coverage.
- Acceptable short-term: 2022-current if source is otherwise clean and especially strong for WR/TE/RB.
- Any shorter range requires a separate NWR value/use review.

## Required Row Grain

Minimum accepted grain:

- player-season

Preferred grain:

- player-week
- player-game

If multiple grains are provided, each must be explicitly labeled. Combined-season, career-to-date, rolling-window, leaderboard, or eligibility-threshold rows must be separable from true player-season/week/game rows.

## Required Fields

Minimum fields:

- `provider`
- `provider_feed_name`
- `season`
- `player_id`
- `player_name`
- `team`
- `position`
- `routes_run`
- `source_updated_at`

Preferred fields:

- `provider_player_id`
- `gsis_id`
- `espn_id`
- `nflverse_player_id`
- `week`
- `game_id`
- `opponent_team`
- `team_game_id`
- `targets`
- `receiving_yards`
- `route_participation`
- `targets_per_route_run`
- `yards_per_route_run`
- `eligibility_threshold`
- `coverage_flag`
- `missingness_reason`
- `source_row_hash`

## Field Dictionary Requirements

The provider must define:

- exact meaning of `routes_run`
- whether run-blocking/pass-blocking/non-route snaps are excluded
- treatment of screens, RPOs, penalties, sacks, throwaways, spikes, kneels, trick plays, and no-play penalties
- player eligibility rules by position
- whether routes include decoy/clear-out routes
- whether RB check-release and delayed routes count
- source event basis: tracking, charting, official participation, or derived model
- integer/count type and null/zero policy
- target and yards fields if included
- time zone and update timestamp convention

## Identity Requirements

At least one stable provider key is required.

Preferred identity fields:

- `gsis_id`
- `espn_id`
- provider-specific stable player ID with official crosswalk

Name/team/season alone is not accepted as an approved join path. A future admission lane must produce an identity crosswalk audit before any route feed is used.

## Retrieval Requirements

One of the following is required:

- documented API endpoint
- provider-managed export
- recurring CSV/parquet/static file delivery
- signed storage bucket or data room export

The retrieval path must include:

- repeatable authentication or access method
- download cadence
- file naming convention
- schema version
- checksum/hash or ETag support
- provider timestamp/provenance metadata
- retention and backfill policy

## Licensing Requirements

The license or contract must explicitly answer:

- whether NWR may store the data internally
- whether NWR may compute derived internal metrics such as YPRR and TPRR
- whether NWR may display derived metrics internally
- whether NWR may display raw `routes_run`
- whether NWR may redistribute any raw or derived fields
- whether NWR may use the feed for model research
- whether NWR may use the feed in production rankings
- attribution requirements
- deletion/expiration obligations
- audit/logging requirements
- account/user restrictions

## Admission Blockers

The feed remains blocked if any are missing:

- actual player-level route counts
- permission-safe use
- reproducible retrieval
- clear row grain
- stable identity
- historical coverage
- position coverage
- missingness documentation
- storage/redistribution rights
- provider provenance
