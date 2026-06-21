# NWR ADP Primary Source Decision - 2026-06-21

## Decision Summary

Sleeper ADP is the primary ADP market/timing source for NWR for now.

This decision is based on the Sleeper ADP Display Context V0 validation result:

- 3,292 rows pulled from the Sleeper projections endpoint.
- 0 missing preferred ADP values.
- Candidate package: `market_behavior/sleeper_adp_display_context`.
- Approval status remains `candidate`.
- Source risk remains `YELLOW_UNDOCUMENTED_ENDPOINT`.

Manual CSV import remains the fallback if the Sleeper endpoint becomes unavailable,
schema-shifted, stale, or too risky.

FantasyPros/ECR/rankings may remain market ranking context, but they are not treated
as true ADP unless a true ADP export/source is found and approved later.

## Source Status

Sleeper official API docs do not document the projections/ADP endpoint.

The discovered public endpoint works and returns ADP fields, including:

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

Because the endpoint is undocumented, this source is useful but not fully trusted.
Its source status is:

`YELLOW_UNDOCUMENTED_ENDPOINT`

## Preferred ADP Rule For NWR

NWR is dynasty/keeper and 1QB non-PPR, so the preferred ADP rule is:

1. Primary: `adp_dynasty_std`
2. Fallback 1: `adp_dynasty`
3. Fallback 2: `adp_std`
4. Rookie context: `adp_rookie` as separate timing context

Do not use 2QB/Superflex ADP as the primary ADP because NWR is 1QB.

Do not use PPR ADP as primary unless standard/dynasty standard values are missing.

## Allowed Uses

Sleeper ADP may be used for:

- Display-only context
- Market awareness
- Draft timing context
- Mock Draft display overlay
- Stale/availability warnings

## Blocked Uses

Sleeper ADP must not be used for:

- Private value
- Hidden sort
- Rankings
- Model training
- Recommendations
- Final draft decisions
- Decision-driving simulations

ADP must stay separate from NWR private value, rookie ranking, veteran private
values, generated recommendations, simulation decision drivers, and any final
draft-day approval.

## Recommended Next Step

Build Mock Draft ADP Display Overlay V0 using:

`market_behavior/sleeper_adp_display_context`

The overlay must not change pick logic, board sorting, private value, ranking,
recommendations, simulations, or final draft-day decision behavior.
