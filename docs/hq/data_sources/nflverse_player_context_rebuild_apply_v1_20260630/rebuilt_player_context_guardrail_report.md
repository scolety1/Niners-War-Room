# Rebuilt Player Context Guardrail Report

Verdict: `YELLOW_PARTIAL_REBUILD_WITH_GATED_ROWS`

## What Changed

- Updated the tracked display artifact with 41 review/display-only approved identity bindings.
- Updated the identity join-health count from 240 safe / 54 gated to 281 safe / 13 gated.
- Updated schema metadata to cite `approved_identity_nwr_binding_v1` for identity fields.
- Created this apply packet under `docs/hq/data_sources/nflverse_player_context_rebuild_apply_v1_20260630/`.

## What Did Not Change

- App pages changed: no
- Rankings behavior changed: no
- Player Compare behavior changed: no
- Trading Lab behavior changed: no
- Development Lab behavior changed: no
- Draft Room behavior changed: no
- Outcome probabilities changed: no
- Model logic changed: no
- Rank logic changed: no
- Source-truth logic changed: no
- Hidden sort changed: no
- Trade/pick valuation changed: no
- `latest_candidate` or `latest_approved` changed: no
- Frozen board/pinned snapshots changed: no
- Runtime JSON changed: no
- Raw/shared/cache/local_exports/secrets tracked: no
- `ff_rankings` used: no

## Conservative Flags

Every display artifact row keeps:

- `display_only=true`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `rank_logic_allowed=false`
- `hidden_sort_allowed=false`
- `trade_value_allowed=false`
- `pick_value_allowed=false`

## Remaining Gated Rows

Rows in `remaining_gated_rows.csv` must continue to display `Not enough information` / needs identity review until a later explicit review resolves them.
