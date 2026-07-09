# Routes Run Identity Join Risk V2B

## Summary

Identity risk is the main reason visible route-count leads cannot be admitted even if a future lane clears licensing. NWR must not use name-only joins for route denominators because route fields would materially affect derived YPRR/TPRR and downstream historical fantasy features.

## Source-Level Risk

| Source | Observed identity fields | Risk level | Notes |
| --- | --- | --- | --- |
| SumerSports | `sumerPlayerId` observed in page payload | medium/high | Stronger than name-only, but no admitted NWR crosswalk or provider ID documentation exists. |
| ESPN Receiver Scores client JSON | `gsis_id`, `dot_com_id` | low/medium if licensed | GSIS is NWR-friendly, but the source itself is not permission-safe yet. |
| ESPN public page | display name/team | high | Page display alone is insufficient for approved joins. |
| PlayerProfiler public pages | player slug/display identity; possible hidden IDs not documented | high | Public page aggregation would likely require name/page joins unless provider documents IDs. |
| nflverse participation | GSIS/player IDs in public package data | low | Identity-safe, but the field is not full `routes_run`. |
| nflverse NGS/FTN public subsets | nflverse IDs/play IDs | low | Identity-safe, but no route denominator. |
| Public GitHub/Kaggle files | varies | high | Usually sample-specific, name-only, or unclear provenance. |
| Local NWR caches | no route-count source file found | not applicable | No candidate file to join. |

## Required Join Gates

Any future admission lane must provide:

1. Provider field dictionary naming the player identifier.
2. Crosswalk to NWR canonical player identity, preferably via GSIS, ESPN ID, or another admitted stable provider ID.
3. Collision audit for same-name players and team changes.
4. Season/team validation against admitted roster data.
5. Missingness report for unmatched IDs.
6. Ban on name-only joins as approved data path.

## Current Conclusion

ESPN has the best identity shape because `gsis_id` is present in the client object, but it remains blocked by licensing and feed-documentation gates. Sumer has a plausible provider ID but needs a crosswalk. PlayerProfiler public pages remain identity-unsafe until a supported export/API documents stable IDs.
