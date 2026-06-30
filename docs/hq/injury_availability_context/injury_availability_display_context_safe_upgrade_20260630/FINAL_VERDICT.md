# Final Verdict

Verdict: `YELLOW_PARTIAL_AVAILABILITY_CONTEXT_GATED`

## Reason

The merged HQ player context artifact supports safe factual availability display
for 240 safe identity rows. The lane now activates direct tracked-artifact fields
in Player Compare and preserves existing Rankings Data Review visibility.

It remains partial because 54 rows require identity review, schedule
next-game/opponent/bye has 0 current/future safe rows, and per-game denominator
fields are not present in the tracked artifact.

## Safe Now

- roster status
- weekly roster status
- injury report status
- practice status
- injury report date/week
- last active season/week
- snap recency and sample size
- age and age source
- identity join status and caveat
- availability context present/unavailable labels

## Waiting

- `games_while_rostered`
- `games_with_snaps`
- `games_with_recorded_stats`
- `games_played_context`
- `games_missed_while_rostered`
- `per_game_denominator`
- dynamic season anchors
- current/future next-game, opponent, and bye context

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
tracked artifact extension and identity/schedule review where applicable.
