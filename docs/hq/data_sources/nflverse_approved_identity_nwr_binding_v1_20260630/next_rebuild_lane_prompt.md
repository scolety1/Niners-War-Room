# Next Rebuild Lane Prompt

Use this only after `work/nflverse-approved-identity-nwr-binding-v1-20260630` is reviewed and merged.

Task: Rebuild the NFLVerse player context display artifact using only approved and bound review-only identity rows.

Inputs:

- `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/approved_identity_nwr_binding_matrix.csv`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

Rules:

1. Use only rows where `binding_status=BOUND_REVIEW_ONLY`.
2. Keep rows from `unbound_or_ambiguous_identity_rows.csv` gated as `Not enough information` / `Needs identity review`.
3. Do not use rows from `identity_overlay_non_approved_rows.csv`.
4. Preserve all flags:
   - `display_only=true`
   - `review_only=true` where added
   - `model_use_allowed=false`
   - `training_allowed=false`
   - `source_truth_allowed=false`
   - `rank_logic_allowed=false`
   - `hidden_sort_allowed=false`
   - `trade_value_allowed=false`
   - `pick_value_allowed=false`
5. Do not change app behavior, Rankings, model logic, source truth, latest pointers, or protected artifacts.
6. Do not use `ff_rankings`, market/ADP, DynastyProcess IDs, vendor/private/Gmail data, raw shared cache, or secrets.
7. Missing values remain `Not enough information`.

Expected starting counts from this packet:

- Bound review-only rows: 41
- Still unbound/gated rows: 2
