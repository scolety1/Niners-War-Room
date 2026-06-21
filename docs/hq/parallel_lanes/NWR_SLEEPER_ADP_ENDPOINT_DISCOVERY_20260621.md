# NWR Sleeper ADP Endpoint Discovery - 2026-06-21

Owner: Master/Main HQ

Status: YELLOW source-risk discovery. Public endpoint appears usable, but it is not documented in the official Sleeper API docs reviewed for NWR.

## Purpose

Before building a manual CSV import or using FantasyPros/third-party ADP, this spike checked whether Sleeper exposes usable ADP fields through an official or public endpoint.

This is discovery only. No puller, importer, Lane Exchange package, `latest_candidate`, `latest_approved`, pinned snapshot, Mock Draft logic, private value, simulation, deployment, or scheduled task was created or changed.

## Official Docs Finding

Official Sleeper docs reviewed:

```text
https://docs.sleeper.com/
```

Finding:

- The official docs describe a read-only API that does not require an API token.
- The documented sections cover users, avatars, leagues, drafts, players, and trending players.
- The official docs reviewed do not document a projections endpoint or ADP endpoint.
- Therefore, the tested projections endpoint must be treated as undocumented and source-risk YELLOW even though it returned usable data.

## Local-Only Schema Report

Local-only reports were written under:

```text
C:\NWR_SHARED_DATA\vendor_spikes\sleeper_adp\
```

Files:

- `SLEEPER_ADP_ENDPOINT_DISCOVERY_SCHEMA_REPORT_20260621.md`
- `sleeper_adp_endpoint_discovery_results_20260621.csv`

Raw API responses were not saved.

## Endpoints Tested

Documented control endpoints:

| Endpoint | Result |
| --- | --- |
| `https://api.sleeper.app/v1/league/1344772855908290560` | HTTP 200 via `curl.exe` |
| `https://api.sleeper.app/v1/players/nfl/trending/add?lookback_hours=24&limit=1` | HTTP 200 via `curl.exe` |

Undocumented projection/ADP endpoint:

```text
https://api.sleeper.com/projections/nfl/2026?season_type=regular&position[]=DEF&position[]=K&position[]=QB&position[]=RB&position[]=TE&position[]=WR
```

Also tested:

```text
https://api.sleeper.app/projections/nfl/2026?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE&order_by=adp_std
```

Both `api.sleeper.com` and `api.sleeper.app` returned HTTP 200 for the projection endpoint via `curl.exe`.

Runtime note:

- `Invoke-WebRequest` failed in this shell for both documented Sleeper control endpoints and the projections endpoint with a local client error.
- `curl.exe` succeeded, so the discovery result is based on `curl.exe`.

## HTTP / Shape Summary

| Season | Query | HTTP | Rows | Approx bytes | Shape |
| --- | --- | ---: | ---: | ---: | --- |
| 2026 | no `order_by` | 200 | 3292 | 3087421 | array |
| 2026 | `order_by=adp_std` | 200 | 3292 | 3087421 | array |
| 2026 | `order_by=adp_ppr` | 200 | 3292 | 3087421 | array |
| 2026 | `order_by=adp_half_ppr` | 200 | 3292 | 3087421 | array |
| 2026 | `order_by=adp_2qb` | 200 | 3292 | 3087421 | array |
| 2026 | `order_by=pts_ppr` | 200 | 3292 | 3087421 | array |
| 2026 | `order_by=pts_half_ppr` | 200 | 3292 | 3087421 | array |
| 2026 | `order_by=pts_std` | 200 | 3292 | 3087421 | array |
| 2025 | no `order_by` | 200 | 3294 | 2982228 | array |
| 2025 | `order_by=adp_std` | 200 | 3294 | 2982228 | array |

The tested `order_by` values changed output ordering but did not appear to hide fields. For 2026, response byte counts remained the same across tested ordering values.

## Response Shape Summary

Top-level row keys observed:

- `category`
- `company`
- `date`
- `game_id`
- `last_modified`
- `opponent`
- `player`
- `player_id`
- `season`
- `season_type`
- `sport`
- `stats`
- `status`
- `team`
- `updated_at`
- `week`
- `week_shard`

Identity-like fields observed:

- `player_id`
- `player.first_name`
- `player.last_name`
- `player.position`
- `player.fantasy_positions`
- `player.team`
- `player.team_abbr`
- `team`
- `season`
- `season_type`

Timestamp / staleness-like fields observed:

- `date`
- `updated_at`
- `last_modified`
- `player.news_updated`
- `player.team_changed_at`

Projection/points fields observed:

- `stats.pts_std`
- `stats.pts_half_ppr`
- `stats.pts_ppr`

ADP-like fields observed:

- `stats.adp_std`
- `stats.adp_half_ppr`
- `stats.adp_ppr`
- `stats.adp_2qb`
- `stats.adp_dynasty`
- `stats.adp_dynasty_std`
- `stats.adp_dynasty_half_ppr`
- `stats.adp_dynasty_ppr`
- `stats.adp_dynasty_2qb`
- `stats.adp_rookie`
- `stats.adp_idp`
- `stats.adp_idp_1qb`

No explicit `superflex` field name was observed. `adp_2qb` and `adp_dynasty_2qb` may be the closest visible proxy, but this must be labeled exactly as Sleeper provides it.

## Candidate Schema If Used Later

If Tim/Master approves a follow-up YELLOW source-risk prototype, a display-only package could use:

- `source`
- `source_endpoint`
- `source_risk`
- `pulled_at`
- `season`
- `season_type`
- `player_id`
- `first_name`
- `last_name`
- `player_name`
- `position`
- `fantasy_positions`
- `team`
- `adp_std`
- `adp_half_ppr`
- `adp_ppr`
- `adp_2qb`
- `adp_dynasty`
- `adp_dynasty_std`
- `adp_dynasty_half_ppr`
- `adp_dynasty_ppr`
- `adp_dynasty_2qb`
- `adp_rookie`
- `pts_std`
- `pts_half_ppr`
- `pts_ppr`
- `updated_at`
- `last_modified`
- `notes`

Allowed package name if approved later:

```text
market_behavior/adp_display_context
```

or:

```text
market_behavior/sleeper_adp_display_context
```

## Fit For NWR

Potentially sufficient for:

- display-only market/ADP context
- Mock Draft display overlay, if explicitly approved later
- opponent behavior / likely availability / pick timing context
- cross-checking draft timing assumptions

Not sufficient or not approved for:

- NWR private value
- `model_value/veteran_private_values`
- hidden sort
- model training
- recommendations
- final draft decisions
- simulations
- production deployment

## Source Risk Classification

YELLOW.

Reason:

- Endpoint is public and returned stable-looking JSON with ADP fields.
- It exposes useful ADP and projection fields, including standard, half-PPR, PPR, 2QB, dynasty, dynasty-scoring variants, rookie, and IDP ADP fields.
- However, the endpoint is not documented in the official Sleeper docs reviewed for NWR.
- It must remain source-risk YELLOW until Sleeper documents it or Tim/Master accepts an undocumented-endpoint policy.

GREEN would require official Sleeper documentation or explicit Sleeper source confirmation.

RED would apply if later testing shows instability, auth requirements, endpoint removal, terms/source conflict, missing identity fields, or unacceptable staleness.

## Recommended Next Step

Recommended path:

1. Do not build a production puller yet.
2. Create a separate `Sleeper ADP YELLOW source-risk prototype` prompt only if Tim/Master approves.
3. Prototype local-only raw pull + redacted schema report + display-only `latest_candidate` support, with no `latest_approved`.
4. Keep a manual CSV import V0 as backup.
5. Continue source research for FantasyPros / BeatADP / other ADP sources only as display-only alternatives, with licensing and audit checks.

Recommended current verdict:

```text
Undocumented Sleeper ADP YELLOW spike only.
```

## Hard Policy Statement

ADP remains display-only market context. ADP must never become NWR private value, hidden sort, model training, recommendations, simulations, or final draft-day decisions without a separate Tim/Master/QA-approved source policy. Current policy does not approve that use.
