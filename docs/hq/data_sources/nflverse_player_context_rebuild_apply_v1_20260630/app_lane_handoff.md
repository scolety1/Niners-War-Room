# App Lane Handoff

The tracked player context artifact now has 281 rows passing:

- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- `display_only=true`
- all model/training/source-truth/rank/hidden-sort/trade/pick flags `false`

## Required Consumption Rules

1. Read only the tracked artifact:
   `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
2. Join by `nwr_player_id` only.
3. Require `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.
4. Confirm fields in `nflverse_player_context_schema_manifest.csv` remain `SAFE_NOW_DISPLAY_ONLY` and display-only before showing them.
5. Treat `Not enough information`, `NEED_IDENTITY_REVIEW`, `NEED_DATASET_REFRESH`, `NEED_SCHEMA_REVIEW`, `BLOCKED_SOURCE_POLICY`, and `BLOCKED_VENDOR_OR_PRIVATE` as unavailable display values.
6. Never read raw `C:/NWR_SHARED_DATA` from app pages.
7. Never use these fields for model input, training, source truth, ranking, hidden sort, trade value, pick value, recommendations, injury risk, or medical projection.

## Newly Available Identity Rows

The 41 rows listed in `player_context_rebuild_delta.csv` are now review/display-only identity-safe. Their non-identity context values may still be `Not enough information`.

## Still Gated

The 13 rows listed in `remaining_gated_rows.csv` remain gated. Kentrel Bullock and Jamal Haynes are still not bound by this apply.
