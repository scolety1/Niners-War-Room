# Model v4 Red Zone Exact Receipt Regeneration Pilot V1 Report

## Verdict

`YELLOW_RED_ZONE_RECEIPTS_PARTIAL_WITH_CAVEATS`

## Clear Answer

Red-zone source/as-of safety is proven only for a narrow review-only partial pilot using typed 2024-2025 Sleeper weekly red-zone sidecar fields. Exact 2013-2025 red-zone receipts are still not available.

## What Was Generated

- Receipt rows generated: `1306`
- Season coverage: `2024=648, 2025=658`
- Position coverage: `QB=228, RB=346, TE=198, UNKNOWN=159, WR=375`
- Metric coverage: `red_zone_carries=434, red_zone_pass_attempts=147, red_zone_targets=725`
- Duplicate keys: `0`
- Identity flags: `IDENTITY_LIMITED_GSIS_PRESENT_BUT_NO_REVIEW_MART_POSITION_NAME=159, PARTIAL_GSIS_TO_REVIEW_MART_LATEST_IDENTITY=605, PASS_GSIS_TO_REVIEW_MART_IDENTITY=542`

## Source / As-Of Decision

- Source availability: proven for the tracked 2024-2025 compact review-only sidecar.
- Source/use-gate status: review-only source-admission candidate; not model-use, training, production, source-truth, ranking, or app use.
- As-of safety: safe only for completed source-season review or lagged N+1 component testing. It is blocked for same-season prediction use.
- Missingness: sparse missing source keys remain unknown/not enough information, not zero.
- Ambiguous `rz_att`: excluded.

## Source Artifacts Found

- `docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/nwr_player_week_redzone_sidecar_v1.parquet`
- `docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/nwr_redzone_sidecar_decision_v1.md`
- `docs/hq/data_sources/sleeper_nflverse_usage_redzone_source_admission_v1_20260701/usage_redzone_field_mapping.csv`
- `docs/hq/data_sources/sleeper_nflverse_usage_redzone_source_admission_v1_20260701/sleeper_weekly_stats_receipt.csv`
- `docs/hq/data_sources/sleeper_nflverse_usage_redzone_source_admission_v1_20260701/season_week_coverage_matrix.csv`
- `docs/hq/data_sources/sleeper_nflverse_usage_redzone_source_admission_v1_20260701/missingness_and_zero_policy.md`

## Maximum Allowed Use

`PARTIAL_REVIEW_ONLY_WITH_CAVEATS`

These receipts may support future review-only component signal tests after Master HQ approval. They do not approve Formula Gauntlet tournaments, exact replay, production/model-use, formula weights, rankings integration, hidden sort, recommendation logic, or source promotion.

## Gates Preserved

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- Production/model-use remains blocked.
- Rankings integration remains blocked.
- No source was promoted.
