# Censoring Policy

Verdict: `YELLOW_CENSORING_POLICY_DEFINED_NO_ABSENCE_APPROVAL`

## Global Policy

Missing availability evidence is censored to `Not enough information`.

It is not:

- healthy
- clean
- safe
- low risk
- active
- inactive
- played
- missed
- off-roster
- no role
- zero snaps
- zero stats
- no injury

## Field-Level Policy

- `games_while_rostered`: may display only when weekly roster and schedule joins
  support the denominator. Missing support is not zero rostered games.
- `games_with_snaps`: may display positive snap-game evidence. Missing snap
  rows are not zero snaps, no role, inactive, or missed games.
- `games_with_recorded_stats`: may display positive stat-game evidence. Missing
  stat rows are not zero production, inactive, or missed games.
- `games_played_context`: may display as an explanation of rostered, snap, and
  stat counts. It is not a played label or a health label.
- `per_game_denominator`: may display only when the tracked denominator row is
  safe. It is not a model denominator.
- `games_missed_while_rostered`: fully censored. It remains
  `Not enough information`.
- `injury_report_status`: missing report rows are not healthy or clean.
- `practice_status`: missing practice rows are not full participation or health.
- `roster_status`: missing roster status is not active, inactive, off-roster, or
  clean.
- `weekly_roster_status`: missing weekly roster status is not active, inactive,
  missed, or clean.
- `snap_sample_size`: missing sample is not zero usage.
- `last_active_season` and `last_active_week`: missing activity is not current
  unavailability and not current health.

## Censoring Causes

Rows may be censored by:

- unresolved identity
- missing weekly roster support
- missing schedule support
- missing snap source rows
- missing stat source rows
- missing injury report rows
- current/future as-of uncertainty
- schedule byes or exceptions
- inactive/game-status ambiguity
- postseason exclusion
- source coverage limits

None of these censoring causes can be treated as a false value or zero value.

## Future Gate Requirement

Any future absence or missed-game field must carry an explicit censoring reason
per row. Rows without strict proof must remain `Not enough information`.
