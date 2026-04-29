# Data Contract

## Snapshots
Use frozen local snapshot folders such as `sample_data/2026_pre_declaration` and future `data_packs/YYYY_label` folders. Old data packs must not be overwritten.

## Canonical IDs
Player identity is anchored by `player_id`, with `merge_name` used for matching. Team identity is anchored by `team_id`; owner identity is anchored by owner/team fields from roster and pick files.

## Input Schemas
- `dim_players.csv`: player identity, position, NFL team, external IDs, active flag.
- `fact_rosters.csv`: snapshot date, season, league/team/owner, player, position, roster status, official rank, source.
- `fact_official_rankings.csv`: source/rank metadata and official rank, including rank placeholder flag.
- `fact_future_picks.csv`: pick year, round, slot, label, original/current team, certainty.
- `fact_pick_values.csv`: overall pick, base value, future discount, certainty, declaration adjustment, final value.
- `model_outputs.csv`: private, market, war, keeper, drop, outcome, confidence, risk, recommendation.
- `metadata_sources.csv`: source and review metadata.

## Validation Rules
Reject imports for duplicate rostered players, duplicated picks with multiple owners, missing team IDs, missing player identity, invalid pick labels, roster hard-limit violations without override, and inability to calculate official top five.

Warn for missing official rank, rank 400 placeholder, player not in `dim_players`, unknown owner/team, unknown position, missing market value, missing model output, and kicker inclusion.

## Missing Data
Missing features lower confidence and shrink outcome probabilities toward position/draft-cap priors. Missing official ranks remain visible warnings because official ranks control league rules.
