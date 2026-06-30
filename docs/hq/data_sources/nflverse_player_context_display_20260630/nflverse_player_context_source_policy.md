# NFLVerse Player Context Source Policy

Verdict: `YELLOW_PARTIAL_PLAYER_CONTEXT_ARTIFACT`

- `display_only=true` for every row.
- `model_use_allowed=false`, `training_allowed=false`, `source_truth_allowed=false`, `rank_logic_allowed=false`, `hidden_sort_allowed=false`, `trade_value_allowed=false`, and `pick_value_allowed=false`.
- Missing data remains `Not enough information` or `NEED_DATASET_REFRESH`.
- Missing injury is not healthy.
- Missing depth chart data is not no-role.
- Missing snap data is not zero snaps.
- Missing draft capital is not confirmed UDFA.
- Ambiguous identity and fallback name matches remain `Review needed`.
- `ff_rankings` remains blocked and is not used.
- Contract context is non-financial display metadata only; it excludes dollar values, guarantees, APY, cap values, and valuation signals.
- Schedule context is only populated when a current/future game context is approved. The current artifact leaves it unavailable rather than inferring a bye or next opponent from stale/historical schedules.