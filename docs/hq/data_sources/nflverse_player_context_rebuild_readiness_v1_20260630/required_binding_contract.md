# Required Binding Contract

Verdict: `YELLOW_WAITING_FOR_BINDING_ARTIFACT`

## Required Artifact

Before any player-context rebuild can run, the following packet must be merged into `origin/work/hq-parallel-control`:

`docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/`

The required primary CSV is:

`docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/approved_identity_nwr_binding_v1.csv`

The packet must include a manifest or guardrail report with:

- `binding_verdict=GREEN_APPROVED_IDENTITY_NWR_BINDING_READY`
- `rebuild_player_context_permitted=true`
- `source_overlay=docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_approved_overlay_v1.csv`
- `non_approved_rows_excluded=true`
- `name_only_or_fuzzy_binding_used=false`

## Required Primary CSV Columns

The binding CSV must include these columns:

- `player_name`
- `position`
- `team`
- `approved_nflverse_id`
- `approved_gsis_id`
- `approved_pfr_id`
- `bound_nwr_player_id`
- `bound_nwr_player_name`
- `bound_nwr_position`
- `bound_nwr_team`
- `binding_status`
- `binding_method`
- `binding_evidence`
- `human_decision`
- `approved_by_human`
- `approval_scope`
- `review_only`
- `display_only`
- `model_use_allowed`
- `training_allowed`
- `source_truth_allowed`
- `rank_logic_allowed`
- `hidden_sort_allowed`
- `trade_value_allowed`
- `pick_value_allowed`
- `source_overlay`
- `notes`

## Required Row Contract

The binding CSV must contain exactly the approved overlay rows that are being applied. For the expected full apply, it must contain all 43 rows from `identity_approved_overlay_v1.csv`.

Each applied row must satisfy all of:

- Present in `identity_approved_overlay_v1.csv`.
- Not present in `identity_overlay_non_approved_rows.csv`.
- `human_decision=APPROVE_REVIEW_ONLY`.
- `approved_by_human=true`.
- `approval_scope=review_only_display_only_identity_use`.
- `approved_nflverse_id` is populated and not `Not enough information`.
- `approved_gsis_id` is populated and not `Not enough information`.
- `bound_nwr_player_id` is populated and not `Not enough information`.
- `bound_nwr_player_id` is unique within the binding artifact.
- `binding_status=BOUND_TO_CURRENT_NWR_PLAYER_ID`.
- `binding_method` is deterministic or explicitly human-verified against the current NWR player row.
- `review_only=true`.
- `display_only=true`.
- All model/training/source-truth/rank/hidden-sort/trade/pick flags are `false`.

## Forbidden Binding Inputs

- Do not bind by name-only matching.
- Do not bind by fuzzy matching without explicit human evidence.
- Do not bind rows from `identity_overlay_non_approved_rows.csv`.
- Do not bind `RECOMMEND_HUMAN_REVIEW`, `RECOMMEND_KEEP_BLOCKED`, `PENDING`, or `KEEP_BLOCKED` rows.
- Do not use raw/shared/local/cache/vendor/Gmail/runtime/secret paths as tracked inputs.
- Do not approve rows with missing approved NFLVerse/GSIS IDs.

## Rebuild Permission Rule

The rebuild lane must stop with `YELLOW_WAITING_FOR_BINDING_ARTIFACT` unless the binding packet is present, merged into the HQ base, schema-valid, count-valid, guardrail-valid, and explicitly says `rebuild_player_context_permitted=true`.

If any binding row fails validation, the rebuild lane must stop with `RED_GUARDRAIL_FAILURE`.
