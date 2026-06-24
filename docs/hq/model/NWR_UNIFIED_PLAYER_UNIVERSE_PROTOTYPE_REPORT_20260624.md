# NWR Unified Player Universe Prototype Report

Date: 2026-06-24
Branch: `work/hq-parallel-control`
Status: REVIEW-ONLY PROTOTYPE

## Verdict

YELLOW-GREEN for review artifact creation.

RED for direct app wiring today.

The prototype successfully creates a unified review CSV and validation reports, but it intentionally keeps `app_wiring_allowed=no` and `model_input_allowed=no` for every row.

## Artifacts Created

Output folder:

`docs/hq/model/unified_player_universe_v0/`

Files:

- `unified_player_universe_v1_review.csv`
- `unified_player_universe_v1_validation_report.csv`
- `unified_player_universe_v1_duplicate_review.csv`
- `unified_player_universe_v1_identity_gap_review.csv`
- `unified_player_universe_v1_source_summary.csv`

Contract:

- `docs/hq/model/NWR_UNIFIED_PLAYER_UNIVERSE_CONTRACT_V1_20260624.md`

Build/validation harness:

- `src/services/unified_player_universe_validation_service.py`
- `scripts/build_unified_player_universe_v1_review.py`

## Row Counts

- Total review rows: 383.
- Veteran rows: 252.
- Veteran Full Dynasty source rows: 240.
- Frozen Baseline dropped-veteran checkpoint rows: 12.
- Rookie/prospect rows: 54.
- PDF free-agent rows: 77.

## Source Layer Counts

| Source layer | Rows | Notes |
| --- | ---: | --- |
| Veteran Full Dynasty Layer | 240 | Approved full dynasty source; 0 rookie/prospect rows. |
| Rookie/Prospect Layer | 54 | Rookie HQ/frozen rookie context; no fabricated Dynasty Rank. |
| Frozen Baseline Layer | 12 | Dropped-veteran checkpoint rows from frozen baseline. |
| PDF Free-Agent Availability Layer | 77 | PDF page-3 free-agent availability context only. |

Input source counts preserved in source summary:

- Full Dynasty source input: 240.
- Frozen board source input: 66.
- Rookie overlay source input: 54.
- PDF free-agent source input: 77.
- Market baseline source input: 330.
- Outcome context source input: 66.
- Identity audit source input: 1139.

## Validation Summary

All generated validation checks passed:

- Required columns exist.
- Enums valid.
- No market-as-rank source.
- Rookie/prospect rows have blank `dynasty_rank`.
- `app_wiring_allowed=no` on all rows.
- `model_input_allowed=no` on all rows.
- Duplicate groups identified.
- Missing player IDs reported.
- Age source reported.
- Missing/unsupported outcomes display `Not enough information`.
- Full dynasty veteran row count preserved at 240.
- Rookie/prospect count reported at 54.
- Frozen board source remains 66 rows.

## Duplicate Review

Duplicate review rows: 15.

Detected examples include players appearing in multiple layers, such as:

- Rashee Rice in Veteran Full Dynasty Layer and Frozen Baseline Layer.
- Brian Thomas in Veteran Full Dynasty Layer and Frozen Baseline Layer.
- Zay Flowers in Veteran Full Dynasty Layer and Frozen Baseline Layer.
- Keenan Allen in Veteran Full Dynasty Layer and Frozen Baseline Layer.
- Several PDF free-agent rows that also match veteran full dynasty rows.

Policy: do not auto-merge low-confidence duplicates. Keep `REVIEW_NEEDED`.

## Identity Gap Review

Identity gap rows: 330.

Gap types:

- `manual_review_flag`: 263.
- `missing_age`: 42.
- `low_or_missing_join_confidence`: 20.
- `missing_player_id`: 5.

Missing IDs remain visible and reviewable. They are not silently dropped.

## Rank Policy Applied

- Veteran Full Dynasty rows carry `dynasty_rank` from the approved full dynasty source.
- Rookie/prospect rows carry `rookie_rank` and `frozen_baseline_rank` only where already present.
- Frozen Baseline checkpoint rows carry `frozen_baseline_rank`.
- PDF free-agent rows are unranked review rows unless they already carry review-safe candidate rank context.
- `unified_display_rank` is generated only for review ordering and is labeled through `unified_display_rank_source`.
- Market values do not create rank.

## Market Policy Applied

Market fields are display-only:

- `dp_1qb_value`
- `dp_market_rank`
- `nwr_vs_market_gap`
- `market_match_status`

Market matched rows: 343.
Unmatched rows: 40.

No row uses market as `rank_source`.

## Outcome Policy Applied

Outcome status counts:

- `SUPPORTED`: 24.
- `MISSING`: 282.
- `NOT_APPLICABLE`: 77.

Missing and unsupported outcomes use `Not enough information`, not low probabilities.

## App/Model Gates

- App wiring allowed: no for all 383 rows.
- Model input allowed: no for all 383 rows.

This artifact must not be consumed by app pages until a later explicit integration lane approves:

- service contract.
- Data Health checks.
- duplicate review handling.
- identity gap handling.
- browser smoke.
- guardrail tests.

## Known Caveats

- The approved 240-row Full Dynasty source still has 0 rookie/prospect rows.
- The artifact commits a review CSV derived partly from ignored local source content; it does not track the ignored `local_exports` source file itself.
- Veteran rows may still carry warning/caveat language from the source board, which keeps many rows in review status.
- Age is partial; missing age remains `Not enough information`.
- Outcome context is sparse and display-only.
- Market coverage is useful for sanity display only.

## Recommendation

Next best step: Data Health and contract review, not app wiring.

After human review, the safest implementation path is:

1. Review duplicate and identity gap CSVs.
2. Decide whether the prototype artifact should remain committed review data or move to generated/ignored output for later cycles.
3. Add Data Health checks for unified universe coverage.
4. Create a read-only service contract.
5. Only then consider an opt-in Dynasty Rankings unified review view.
