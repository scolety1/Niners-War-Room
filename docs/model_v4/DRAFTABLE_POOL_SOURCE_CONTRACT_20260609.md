# Draftable Pool Source Contract - 2026-06-09

## Legal draftable source types
1. `rookie`: incoming rookies from admitted rookie/prospect sources.
2. `free_agent`: unrostered/legal free agents from a current source.
3. `dropped_veteran`: officially released/dropped veterans after Roster Declaration Day.
4. `manual`: manually added draftable players with explicit source notes.
5. `protected_not_draftable`: protected roster players, blocked from confirmed draftable status.

## Draftable statuses
- `confirmed_draftable`
- `rookie_draftable`
- `free_agent_draftable`
- `dropped_veteran_draftable`
- `manual_draftable`
- `scouting_only`
- `protected_not_draftable`
- `needs_source`
- `no_baseline`
- `hidden_kicker`

## Source precedence
1. Official dropped/released veteran list after Roster Declaration Day.
2. Current rookie draftable/prospect source.
3. Current free-agent/unrostered source.
4. Manual draftable additions.
5. Protected roster source as a blocklist, not as draftable evidence.

## Blocked from private value
Market rank, league rank, ADP, startup, projections, consensus, public ranks, trade calculators, RotoWire projections/rankings, prior draft history, spreadsheet highlights, and legacy active-pack scores cannot create or modify NWR Draft Value or NWR Dynasty Score.
