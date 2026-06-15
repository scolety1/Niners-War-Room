# Rookie Repaired CFBD Enriched Baseline Audit - 2026-06-15

## Executive verdict

Verdict: GREEN/YELLOW.

The repaired CFBD enriched baseline is safe enough to compare against the old expanded baseline and safe enough to open the conditional Phase B candidate audit. It is not a production ranking and not a v2 board.

Phase A gate results:

| Gate | Result |
| --- | --- |
| Leakage / anti-cheat | GREEN |
| Metric semantics | GREEN |
| Deterministic CFBD join policy | GREEN |
| Unresolved row policy | GREEN |
| Duplicate sensitivity | PASS |
| Feature coverage | GREEN |
| Baseline comparability | GREEN |
| Phase B allowed | yes |

No tuning happened in Phase A. No app wiring, production ranking, private score, probability, band, hidden sort key, Outcome file, veteran file, or promoted artifact was created.

## CFBD feature policy

Primary enriched baseline policy:

- deterministic repaired CFBD rows may use CFBD production/share features;
- unresolved rows receive `cfbd_feature_status=unresolved_no_enriched_features`;
- unresolved rows are not zero-filled as college production;
- duplicate-selected rows remain warning-visible and are tested both included and excluded;
- labels are evaluation-only;
- ADP, market, rankings, projections, names, IDs, schools, teams, years, and outcomes are not scoring features.

## Feature coverage

Rows evaluated: 1,099 complete-window 2010-2023 rows.

| Status | Rows |
| --- | ---: |
| deterministic joined | 972 |
| unresolved no enriched features | 127 |
| duplicate-selected | 8 |
| deterministic join rate | 0.884 |

The row count is 1,099 because the audit uses complete-window, backtest-ready rows only.

## Old baseline vs CFBD-enriched baseline

Validation split: 2022-2023.

| Model | Bucket | Stars | Star capture | Bust rate |
| --- | --- | ---: | ---: | ---: |
| old baseline | top 12 | 6/16 | 0.375 | 0.250 |
| CFBD enriched | top 12 | 6/16 | 0.375 | 0.292 |
| deterministic-only CFBD | top 12 | 6/16 | 0.375 | 0.292 |
| old baseline | top 24 | 10/16 | 0.625 | 0.417 |
| CFBD enriched | top 24 | 11/16 | 0.688 | 0.396 |
| deterministic-only CFBD | top 24 | 11/16 | 0.688 | 0.404 |

Full 2010-2023 split:

| Model | Bucket | Stars | Star capture | Bust rate |
| --- | --- | ---: | ---: | ---: |
| old baseline | top 12 | 59/125 | 0.472 | 0.095 |
| CFBD enriched | top 12 | 60/125 | 0.480 | 0.089 |
| old baseline | top 24 | 90/125 | 0.720 | 0.155 |
| CFBD enriched | top 24 | 90/125 | 0.720 | 0.154 |

Interpretation: CFBD enrichment improved validation Top 24 star capture and slightly improved full-pool Top 12 with no broad bust-rate regression, but it did not improve validation Top 12 star capture by itself.

## WR star capture

Validation WR diagnostics:

| Model | Bucket | Stars | Star capture | Bust rate |
| --- | --- | ---: | ---: | ---: |
| old baseline | top 12 | 1/4 | 0.250 | 0.000 |
| CFBD enriched | top 12 | 0/4 | 0.000 | 1.000 |
| old baseline | top 24 | 1/4 | 0.250 | 0.000 |
| CFBD enriched | top 24 | 2/4 | 0.500 | 0.400 |
| old baseline | top 36 | 2/4 | 0.500 | 0.250 |
| CFBD enriched | top 36 | 2/4 | 0.500 | 0.286 |

WR result: YELLOW. CFBD enrichment helps Top 24 WR star capture but worsens Top 12 WR bust concentration in validation. WR improvement still needs warning calibration and richer role/route/injury context before any v2 board.

## Duplicate sensitivity

Duplicate sensitivity verdict: PASS.

Across train, validation, and full splits, including versus excluding duplicate-selected rows did not materially change the candidate decision:

- validation Top 12 star capture delta: 0.000;
- validation Top 12 bust-rate delta: 0.000;
- validation Top 24 star capture delta: 0.000;
- validation Top 24 bust-rate delta: 0.000;
- full Top 12 star capture delta: 0.004;
- full Top 24 star capture delta: 0.002.

The eight duplicate-selected rows still remain manual-review rows before any production use.

## Phase A decision

Phase A cleared the gates for Phase B because:

- metric semantics were explicit and year-class based;
- deterministic CFBD join policy was visible;
- unresolved rows were not zero-filled;
- duplicate sensitivity was non-blocking;
- feature coverage was sufficient for a candidate comparison;
- anti-cheat/leakage checks passed.

Phase A does not approve production use or v2 board creation.

## Exports created

Local-only exports:

- `local_exports/rookie_framework/repaired_cfbd_enriched_baseline_audit_20260615/old_vs_cfbd_enriched_baseline_metrics_20260615.csv`
- `year_class_cfbd_enriched_metrics_20260615.csv`
- `position_cfbd_enriched_metrics_20260615.csv`
- `wr_star_capture_cfbd_enriched_diagnostics_20260615.csv`
- `duplicate_sensitivity_20260615.csv`
- `unresolved_cfbd_row_policy_20260615.csv`
- `cfbd_enriched_feature_coverage_20260615.csv`
- `README_ROOKIE_REPAIRED_CFBD_ENRICHED_BASELINE_AUDIT_20260615.md`

These exports are local-only and were not committed.

## Anti-cheat / leakage audit

| Check | Result |
| --- | --- |
| Names only used for diagnostics/reporting | PASS |
| IDs only used for identity/join/grouping | PASS |
| Outcome labels only used for evaluation | PASS |
| ADP/market excluded from scoring | PASS |
| Unresolved rows not zero-filled | PASS |
| No player/team/school/year special cases | PASS |
| No probabilities/bands/hidden sort keys | PASS |
| No production/app/veteran/Outcome files touched | PASS |

## Recommended next step

Phase B was cleared to run as a conditional audit. A v2 board should remain blocked unless Phase B candidate quality and manual-review risk are also acceptable.
