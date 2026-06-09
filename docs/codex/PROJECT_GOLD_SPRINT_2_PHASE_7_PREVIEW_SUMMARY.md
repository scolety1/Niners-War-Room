# Project Gold Sprint 2 Phase 7 Preview Summary

Generated: 2026-05-14

This phase regenerated the public-data preview and stats-first preview after the Sprint 1 projection schema change. No formulas were tuned, no paid data was added, and no decision-ready gate was unlocked.

## Generated Artifacts

| artifact | path |
|---|---|
| Public data preview | `local_exports/nflverse/preview/sprint2_phase7_public_20260514` |
| Raw source folder | `local_exports/nflverse/preview/sprint2_phase7_public_20260514/raw` |
| Stats-first model preview | `local_exports/nflverse_model_previews/sprint2_phase7_stats_first_20260514` |
| Preview outputs | `local_exports/nflverse_model_previews/sprint2_phase7_stats_first_20260514/stats_first_veteran_model_preview_outputs.csv` |
| Preview contributions | `local_exports/nflverse_model_previews/sprint2_phase7_stats_first_20260514/stats_first_feature_contributions.csv` |
| Source coverage | `local_exports/nflverse_model_previews/sprint2_phase7_stats_first_20260514/stats_first_source_coverage.csv` |
| Active receipt mirror | `local_exports/active_veteran_model_public_sources` |

## Row Counts

| file/report | rows |
|---|---:|
| Sleeper roster snapshot players | 240 |
| Sleeper player universe | 12,175 |
| DynastyProcess ID rows | 12,440 |
| nflverse player rows | 24,966 |
| identity bridge rows | 232 |
| weekly player stat rows | 10,521 |
| snap count rows | 20,524 |
| depth chart rows | 166,111 |
| injury rows | 5,152 |
| participation rows | 0 |
| baseline projection rows | 689 |
| normalized feature rows | 1,039 |
| receipt rows | 11,429 |
| preview model output rows | 1,039 |
| preview outlier rows | 2,994 |

## Projection Status Verification

All required generated files now physically include `projection_source_status`:

| file | has projection_source_status | rows |
|---|---|---:|
| `projection_raw_import.csv` | yes | 689 |
| `stats_first_normalized_features.csv` | yes | 1,039 |
| `lve_normalized_feature_receipts.csv` | yes | 11,429 |
| `stats_first_source_coverage.csv` | yes | 1,039 |

Projection classification:

| status | rows/players |
|---|---:|
| `independent_projection` | 0 |
| `local_baseline_projection` in projection raw rows | 689 |
| `local_baseline_projection` in normalized rows | 689 |
| `missing_projection` in normalized rows | 350 |
| `disabled_projection` | 0 |

Receipt projection rows:

| projection_source_status | receipt rows |
|---|---:|
| `local_baseline_projection` | 1,378 |
| `missing_projection` | 700 |

## Projection Guardrail Verification

Local baseline projections do not act as real independent forecast evidence:

| check | result |
|---|---:|
| local-baseline players with `expected_lve_points_score != 50` | 0 |
| missing-projection players with `expected_lve_points_score != 50` | 0 |
| average confidence with local baseline projection | 72.33 |
| average confidence with missing projection | 41.13 |

The generated preview manifest still says:

| field | value |
|---|---|
| `decision_ready` | `false` |
| `review_status` | `review` |
| `model_promotion` | `not_allowed` |

## Source Coverage Counts

| bucket | status counts |
|---|---|
| production | `review`: 807; `review_missing`: 135; `ready`: 97 |
| role/usage | `ready`: 1,033; `review_missing`: 6 |
| projection | `review`: 689; `review_missing`: 350 |
| injury | `ready`: 800; `review_missing`: 239 |
| age/bio | `ready`: 1,039 |
| market/liquidity | `review_missing`: 1,039 |
| decision effect | `review_only`: 903; `blocks_decision_ready`: 136 |

Critical missing buckets:

| missing critical bucket pattern | players |
|---|---:|
| none | 903 |
| production | 130 |
| production + role/usage | 5 |
| role/usage | 1 |

## Identity Counts

| identity field | counts |
|---|---|
| review status | `ready`: 232 |
| match method | `sleeper_id`: 232 |

## Review-Only Confirmation

The recalibration policy remains active:

| field | value |
|---|---|
| policy active | `true` |
| policy status | `model_recalibration` |
| policy title | `Model Under Recalibration` |
| rankings review-only | `true` |

## Phase 7 Conclusion

Phase 7 completed its intended regeneration. The schema is current, the projection status is visible in raw/normalized/receipt/coverage files, and local baseline projections are quarantined correctly.

The biggest Sprint 2 evidence problem is no longer hidden projection defaults. The next real issue is source quality:

1. production freshness / missing production for 136 decision-blocking rows,
2. no true independent projection source,
3. no participation rows,
4. role/usage still needs an evidence audit despite mostly `ready` status,
5. market/liquidity remains intentionally missing and should stay separate from private value.

Recommended next phase: **Project Gold Sprint 2 / Phase 8: Role/Usage Evidence Audit**.