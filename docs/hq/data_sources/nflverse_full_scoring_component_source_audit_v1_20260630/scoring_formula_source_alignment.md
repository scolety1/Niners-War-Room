# Scoring Formula Source Alignment

NWR scoring version: `nwr_1qb_nonppr_fd_v1`

## Direct Alignments

- `pass_yd_pt` -> `passing_yards`
- `pass_td_pt` -> `passing_tds`
- `pass_int_pt` -> `passing_interceptions`
- `pass_1d_pt` -> `passing_first_downs`
- `pass_2pt_pt` -> `passing_2pt_conversions`
- `sack_suffered_pt` -> `sacks_suffered`
- `carry_pt` -> `carries`
- `rush_yd_pt` -> `rushing_yards`
- `rush_td_pt` -> `rushing_tds`
- `rush_1d_pt` -> `rushing_first_downs`
- `rush_2pt_pt` -> `rushing_2pt_conversions`
- `rec_pt` -> `receptions`
- `rec_yd_pt` -> `receiving_yards`
- `rec_td_pt` -> `receiving_tds`
- `rec_1d_pt` -> `receiving_first_downs`
- `rec_2pt_pt` -> `receiving_2pt_conversions`
- `fumble_recovery_td_pt` -> `fumble_recovery_tds`
- `misc_yd_pt` -> `misc_yards`

## Composite Alignments Requiring Builder Rules

- `fumble_lost_pt` -> `rushing_fumbles_lost + receiving_fumbles_lost + sack_fumbles_lost`
- `return_yd_pt` -> `kickoff_return_yards + punt_return_yards`

These are safe for a future review-only builder only for observed source rows and only if summed exactly once per player-week.

## Ambiguous Alignment

`special_teams_tds` is present in the NFLVerse source, but the current NWR scoring formula has separate `return_td_pt` and `special_td_pt` components. This packet does not approve a split or double use of `special_teams_tds`.

Future builder rule options:

1. Map `special_teams_tds` to one reviewed component and keep the other `Not enough information`.
2. Add a source that separates return touchdowns from other special touchdowns.
3. Waive one component with explicit user/source-policy approval.

Until one of those rules is approved, full scoring parity remains yellow.
