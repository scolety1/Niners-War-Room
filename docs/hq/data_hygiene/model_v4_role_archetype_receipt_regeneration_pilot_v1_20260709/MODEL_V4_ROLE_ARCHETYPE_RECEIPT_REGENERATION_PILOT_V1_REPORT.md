# Model v4 Role Archetype Receipt Regeneration Pilot V1 Report

## Verdict

`GREEN_ROLE_ARCHETYPE_RECEIPTS_REGENERATED_REVIEW_ONLY`

## Clear Answer

Role-archetype receipts were regenerated safely as review-only, lagged usage/context receipts. They may support future review-only component signal tests, but they do not unblock exact Model v4 replay, Formula Gauntlet tournaments, rankings integration, or production/model-use.

## Scope

- Rows generated: `5518`
- Season coverage: `2013-2025`
- Position coverage: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Receipt family regenerated: `role_archetype_receipts` only
- Source: review-only partial replay input panel with lagged prior-season usage/production fields

## Archetype Summary

- Distinct archetypes: `16`
- Largest buckets: `wr_moderate_volume_target_volume=962, rb_moderate_volume_touch_volume=589, wr_high_volume_target_volume=538, te_moderate_volume_target_volume=496, wr_sparse_history_low_games=439, rb_high_volume_touch_volume=361, rb_sparse_history_low_games=344, te_sparse_history_low_games=342`

## Safety Decision

Maximum allowed use: `REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`.

These receipts are not role truth, scouting labels, future outcome labels, exact Model v4 replay receipts, or production/model-use inputs.