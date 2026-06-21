# Sleeper ADP Display Context V0

## Purpose

Sleeper ADP Display Context V0 creates a local-only Lane Exchange `latest_candidate`
package for market timing context:

`market_behavior/sleeper_adp_display_context`

This helps Mock Draft and Master review where Sleeper market timing appears to sit,
but it is not an NWR value source and is not final draft advice.

## Source Risk

Official Sleeper API docs do not document an ADP or projections endpoint. The
public endpoint discovered during the Master spike returned HTTP 200 and exposed
ADP-like fields, but because it is undocumented, every output from this source is:

`YELLOW_UNDOCUMENTED_ENDPOINT`

That means it may be useful for display and timing review, but it must not drive
private value, rankings, hidden sorting, model training, recommendations,
simulations, or final draft decisions.

## Endpoint

The script queries the discovered public read-only endpoint:

`https://api.sleeper.com/projections/nfl/<season>?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF`

Default season: `2026`

Default positions: `QB`, `RB`, `WR`, `TE`, `K`, `DEF`

The script does not scrape Sleeper web pages, use browser automation, bypass
authentication, or save the raw API payload.

## Script

Repo script:

`scripts/sleeper_adp_display_context_v0.py`

Default behavior is report-only. It writes a local-only report under:

`C:\NWR_SHARED_DATA\scheduled_ingest\reports\market_behavior\`

Candidate package writing requires the explicit flag:

```powershell
python scripts/sleeper_adp_display_context_v0.py --season 2026 --write-candidate
```

Candidate packages are written under:

`C:\NWR_SHARED_DATA\lane_exchange\market_behavior\sleeper_adp_display_context\`

The script never creates or updates `latest_approved.json`.

## Candidate Fields

The V0 candidate CSV includes only safe display/market-context fields:

- `source_name`
- `source_type`
- `source_risk`
- `season`
- `collected_at`
- `updated_at`
- `last_modified`
- `sleeper_player_id`
- `player_name`
- `normalized_player_name`
- `team`
- `position`
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
- `preferred_adp_for_nwr`
- `preferred_adp_reason`
- `stale_flag`
- `source_notes`

Projection point fields such as `pts_std`, `pts_half_ppr`, and `pts_ppr` are
omitted in V0.

## Preferred ADP Rule

NWR is dynasty/keeper and non-PPR, so the preferred display field is chosen in
this order:

1. `adp_dynasty_std`
2. `adp_dynasty`
3. `adp_std`
4. `adp_ppr` only as a last-resort display-only fallback

`adp_rookie` remains a separate rookie market-context field and does not replace
the main preferred ADP value.

The script does not choose `adp_2qb` or `adp_dynasty_2qb` as preferred because
NWR is 1QB.

## Allowed Use

The manifest allows only:

- `display_only`
- `market_awareness`
- `draft_timing_context`
- `mock_draft_display_overlay`

This can help an operator see broad market timing and likely availability, but it
does not change NWR private value or draft ranking.

## Blocked Use

The manifest blocks:

- `private_value`
- `hidden_sort`
- `rankings`
- `model_training`
- `recommendations`
- `final_draft_decisions`
- `decision_driving_simulations`
- `deployment_without_approval`

ADP must remain separate from NWR private value, veteran private values, rookie
ranking, generated recommendations, simulation decision drivers, and any final
draft-day approval.

## Manual CSV Fallback

If the undocumented endpoint becomes unavailable, stale, schema-shifted, or too
risky, NWR should fall back to a local-only manual CSV or a separately approved
source research path. Manual ADP import would still be display-only unless a later
Tim/Master/QA policy explicitly changes that.
