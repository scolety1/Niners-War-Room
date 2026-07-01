# Missing Row Policy

Missing player-week rows cannot be converted to zero.

## Required Language

When a player-week source row is absent from admitted `player_stats_weekly`, display and downstream review packets must use:

`Not enough information`

## Not Allowed

- Do not treat a missing player-week row as zero production.
- Do not treat a missing source row as inactive.
- Do not treat a missing source row as healthy, clean, low-risk, no-role, no-usage, or no-snap.
- Do not infer zero from roster, schedule, or identity absence unless a later explicit point-in-time gate approves that logic.
- Do not emit current-player probabilities, recommendations, model features, or label truth from this packet.

## Why

The admitted row-level source proves that observed `player_stats` rows have explicit numeric component values. It does not prove that every rostered or schedule-eligible player-week is present. Missing rows therefore remain unknown.
