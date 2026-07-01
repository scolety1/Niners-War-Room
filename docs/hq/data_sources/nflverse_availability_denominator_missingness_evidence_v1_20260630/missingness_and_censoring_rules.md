# Missingness And Censoring Rules

## Global Rule

Missing availability is not healthy, clean, safe, low-risk, played, missed, inactive, zero snaps, zero stats, off-roster, no-role, or confirmed unavailable.

Every missing or gated denominator value must display as `Not enough information`.

## Field Rules

- `games_while_rostered`: may display only when weekly roster and schedule joins support the player-season denominator. Missing roster/schedule data is not zero rostered games and is not off-roster proof.
- `games_with_snaps`: may display observed snap-game counts only. Missing snap rows are not zero snaps, no role, inactive, or missed games.
- `games_with_recorded_stats`: may display observed stat-game counts only. Missing stat rows are not zero stats, no production, inactive, or missed games.
- `games_played_context`: may display only as an explanatory context string. It is not a played/missed label, injury-risk score, durability score, or recommendation input.
- `per_game_denominator`: may display only where `games_while_rostered` is supportable. It cannot be used as a model denominator without future label parity, historical replay, and leakage gates.
- `games_missed_while_rostered`: remains `Not enough information` unless a future lane supplies explicit, point-in-time active/inactive/missed evidence and a tested censoring policy.
- `injury_report_status`: missing injury report data is not healthy, clean, low-risk, or no injury.
- `roster_status` and `weekly_roster_status`: missing roster data is not off-roster, inactive, active, clean, or source truth.
- `last_active_season`, `last_active_week`, and `snap_sample_size`: display context only; not health, role, or availability inference.

## Censoring Risks

A denominator row can be censored by identity gating, missing weekly roster data, missing schedules, bye weeks, postponed/canceled games, inactive/game-status ambiguity, postseason exclusion, missing snap/stat records, or missing injury reports. None of those censoring cases may be collapsed into zero or false.
