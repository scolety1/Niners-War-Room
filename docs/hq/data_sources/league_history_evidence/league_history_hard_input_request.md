# League History Hard Input Request

## Needed Before Evidence Can Become Actual

The current league-history evidence package remains YELLOW because direct hard inputs are still missing.

## Please Provide

1. Actual 2026 draft log export.
   - Preferred shape: use `actual_2026_draft_log_INPUT_TEMPLATE.csv`.
   - Required: round, pick, selecting team, player, position if available, original pick owner if available.

2. Sleeper trade history export.
   - Preferred shape: use `sleeper_trade_history_INPUT_TEMPLATE.csv`.
   - Required: trade date, teams/sides, raw assets sent by each side, accepted/rejected status.

3. Owner/team mapping.
   - Preferred shape: use `league_history_owner_team_mapping.csv`.
   - Required: canonical LVE team name, current owner label, Sleeper roster ID if available.

4. Brian Thomas Jr. clarification.
   - Confirm whether the phrase about dropping him from a top 5 meant actual roster drop, unprotected status, free-agent availability, draft/acquisition, or only ranking-list movement.

## Current Boundaries

- Gmail metadata is review-only until confirmed by hard input.
- Free-agent snapshots are not drop proof.
- Unprotected is not dropped unless a final cut/drop source confirms it.
- No 2026 draft rows have been invented.
- No Sleeper trade rows have been invented.
- Nothing in this package is training-allowed.
