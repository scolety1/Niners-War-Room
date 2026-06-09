# Model v4 Phase 5F Projection And First-Down Projection Strategy

Generated: 2026-05-16

## Purpose

This phase separates raw-stat projections, recomputed LVE projection points, missing projections, local baseline projections, and estimated first-down projections. First-down estimates are generated from historical nflverse first-down rates and remain review-only with explicit labels.

Detailed CSV: `docs/model_v4/PHASE_5_PROJECTION_FIRST_DOWN_STRATEGY.csv`

## Summary

- Truth-set players reviewed: 80
- Projection source rows evaluated by estimator: 40
- Historical production rows used for first-down rates: 179
- Player-level historical rate rows available: 70
- Position-level historical rate rows available: 4
- Estimated-from-history first-down projection rows: 37
- Direct first-down projection rows: 0
- Missing first-down projection rows among projection-source rows: 3
- Missing projection players in v4 truth set: 42

## Projection Buckets

| bucket | players |
| --- | ---: |
| independent_raw_stat_projection_recompute | 38 |
| missing_projection | 42 |

## First-Down Projection Status

| status | players |
| --- | ---: |
| estimated_from_history | 37 |
| missing_first_down_projection | 3 |
| missing_projection | 40 |

## Warning Counts

| warning | players |
| --- | ---: |
| `estimated_from_history` | 37 |
| `first_down_projection_preview_only` | 38 |
| `missing_first_down_projection` | 1 |
| `missing_projection_data` | 42 |
| `projection_first_downs_estimated_from_history` | 37 |
| `supplied_projection_points_ignored` | 37 |

## Policy Decisions

- Supplied projection fantasy point totals remain ignored; v4 recomputes LVE projection points from raw stat columns.
- Estimated first downs are labeled `estimated_from_history`, never `direct_first_down_projection`.
- Estimated first downs remain `preview_only_not_active_scoring` and retain review/confidence warnings.
- Missing projections emit `missing_projection_data` so they cannot silently preserve fake confidence.
- Local baseline projections are still treated as non-independent forecasts when present; no local baseline rows were promoted in this v4 preview.

## Review-Only Guard

Model v4 remains review-only. This phase updates projection receipts, source coverage, warnings, and preview-only first-down estimates only; it does not promote active rankings or unlock readiness gates.
