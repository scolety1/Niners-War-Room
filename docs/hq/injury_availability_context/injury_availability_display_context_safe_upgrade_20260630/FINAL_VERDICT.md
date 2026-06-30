# Final Verdict

Verdict: `YELLOW_WAITING_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`

## Reason

The lane can safely add docs, schema, a service contract, and tests for
display-only/review-only injury and availability context.

It cannot activate refreshed NFLVerse roster, schedule, snap, stat, or dynamic
season-anchor calculations because the current completion gate still lists
`nflverse pull/status` as `YELLOW`.

## Safe Now

- Preserve existing injury-report source gate.
- Preserve existing V0 Rankings and Player Compare display.
- Add display-only/review-only schema for future availability denominators.
- Keep missing injury or availability context as `Not enough information`.
- Explain season-total report-week counts versus per-game denominator caveats.

## Waiting

- `games_while_rostered`
- `games_with_snaps`
- `games_with_recorded_stats`
- `games_played_context`
- `games_missed_while_rostered`
- `per_game_denominator`
- dynamic season anchors

## Blocked

- injury-risk score
- medical projection
- ACL/comeback projection
- LVE durability score reuse
- scraped/vendor/Gmail/rumor data
- missing-data-as-healthy logic
- model/rank/source-truth promotion

## Final Status

Safe prep is complete. Active dataset-backed availability computation waits for
`WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`.
