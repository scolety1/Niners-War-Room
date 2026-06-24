# NWR Model Backtest And Sensitivity Design - 2026-06-23

Generated at UTC: 2026-06-24T02:36:33.759820+00:00

Scope: design/spec only. This document does not train, retune, deploy, mutate rankings, mutate production model outputs, update latest pointers, update pinned snapshots, or modify Frozen Final Draft Board V1.

## Executive Verdict

**YELLOW design status.** The framework can safely evaluate the NWR dynasty/keeper model if it keeps four tracks separate: strict truth backtest, caution backtest, proxy sensitivity test, and market sanity comparison. It is not ready for automated retuning until historical rows are joined to future outcome labels with as-of-safe features and the row eligibility gates below are implemented as hard checks.

## Source Data Context

Primary drop-list source:

- `docs/hq/data_sources/historical_drop_lists/NWR_HISTORICAL_DROP_LIST_RECONSTRUCTION_2010_2026.csv`
- `docs/hq/data_sources/historical_drop_lists/NWR_RECENT_ACTUAL_OR_INFERRED_DROP_LISTS_2021_2026.csv`
- `docs/hq/data_sources/historical_drop_lists/NWR_PROXY_DROP_LISTS_2010_2021.csv`
- `docs/hq/data_sources/historical_drop_lists/NWR_HISTORICAL_DROP_LIST_RECONSTRUCTION_METHOD_20260623.md`

Known label status:

- 2010-2021: proxy-only dropped-player pools.
- 2022-2024: inferred/unprotected PDF rows unless upgraded by transaction or commissioner evidence.
- 2025: explicit PDF `CUT` evidence.
- 2026: actual/current availability or unprotected context; not proof of bad cuts.
- `PROXY_DROP`, `PROXY_ONLY`, and `LOW` confidence rows: sensitivity-only.

## Four Test Buckets

### 1. Truth Backtest

Purpose: measure whether NWR model outputs would have ranked/valued players sensibly against high-confidence actual league evidence and future outcomes.

Eligible rows:

- `source_class = ACTUAL_DROP`
- `confidence = HIGH`
- explicit transaction, commissioner, approved package, or explicit cut-list evidence
- future outcome label available from an approved as-of-safe outcome dataset

Current eligible seasons:

- 2025 actual PDF `CUT` rows can enter only after future outcome labels are available and source timing is documented.
- 2026 current Drop Decision rows are not yet a completed historical backtest season; use as validation/display context until future outcomes mature.

Training use: no for drop labels themselves. Actual drop status can define availability/cohort membership, but future outcome labels such as `next_nwr_points`, `next_nwr_ppg`, and top-N finish flags are the supervised targets.

### 2. Caution Backtest

Purpose: widen the review set to understand robustness when near-actual inferred league evidence is included.

Eligible rows:

- all truth-backtest rows
- `source_class = INFERRED_DROP` with `confidence = HIGH` or `MEDIUM`
- timestamped `CURRENT_FA_SNAPSHOT` with `HIGH` confidence may be included only as an explicitly labeled availability-context comparison

Current eligible seasons:

- 2022-2024 inferred/unprotected PDF rows, as caution rows only.
- 2025 actual rows.
- 2026 current context rows only as current availability validation, not completed historical truth.

Reporting requirement: every caution metric must be shown beside strict truth metrics and must not be merged into one headline number.

### 3. Sensitivity Test

Purpose: test whether conclusions are brittle when synthetic/proxy rows are included or excluded.

Eligible rows:

- `source_class = PROXY_DROP`
- `confidence = PROXY_ONLY`
- any row with `confidence = LOW`
- low-confidence inferred/current snapshot rows

Current eligible seasons:

- 2010-2021 proxy rows.
- Any future low-confidence or unclassified rows after explicit sensitivity labeling.

Hard rule: sensitivity rows may never become direct training truth, rank penalties, bad-cut proof, actual-drop evidence, source-truth labels, private value, hidden sort, or draft advice.

### 4. Market Sanity Comparison

Purpose: compare NWR outputs against external market/timing context without letting market become NWR value.

Eligible data:

- DynastyProcess values, ADP, ECR, market ranks, market values, FantasyPros or other rank/projection-like fields, when allowed by source policy as display/comparison.

Allowed use:

- market sanity comparison
- timing context
- disagreement bucket labels such as `model_higher_than_market`
- diagnostic stratification only

Forbidden use:

- training label
- private value
- rank penalty
- hidden sort
- target variable
- model improvement proof by itself

## Row Weighting

| Bucket | Row Type | Suggested Weight | Notes |
| --- | --- | ---: | --- |
| Truth | ACTUAL_DROP/HIGH | 1.00 | Availability/cohort evidence only; future outcome target still comes from actual performance labels. |
| Caution | INFERRED_DROP/HIGH | 0.70 | Separate caution metrics; do not merge into truth headline. |
| Caution | INFERRED_DROP/MEDIUM | 0.45 | Current 2022-2024 PDF rows; use down-weighted. |
| Caution | CURRENT_FA_SNAPSHOT/HIGH | 0.35 | Availability context only; must be timestamped. |
| Sensitivity | PROXY_DROP/PROXY_ONLY | 0.10 | Robustness/gap-analysis only. |
| Sensitivity | LOW confidence any source_class | 0.05 | Fail closed; sensitivity only. |
| Market sanity | DISPLAY_ONLY market/ADP | 0.00 | Not part of model scoring; only comparison strata. |

Weights are reporting weights, not permission to train. A row with `allowed_for_training = no` remains forbidden for training even if it has a nonzero sensitivity/reporting weight.

## Forbidden Rows

Exclude from truth/caution headline metrics:

- `PROXY_DROP`, `PROXY_ONLY`, `LOW` confidence rows.
- rows with missing `source_class` or `confidence`.
- rows without an as-of date/source timing note.
- rows lacking a future outcome label when the metric requires future outcome.
- display-only market/ADP/Outcome rows as target labels.
- current 2026 availability rows for completed historical performance claims until the outcome window matures.

## Leakage Controls

1. Every feature row must carry `feature_as_of`, `source_snapshot_path`, `source_created_at` where available, `source_timing_class`, and `live_use_allowed`.
2. Future outcome labels can join only after the simulated decision date.
3. Final season aggregates can be features only for prior completed seasons; same-season final totals are target labels or leakage.
4. Current 2026 drop/availability context cannot be backdated into older seasons.
5. ADP/market/projection/rank-like fields must fail closed if they appear in feature columns for private value or rank prediction.
6. Outcome display columns must fail closed if used as model features or rank overrides.
7. Proxy row identifiers must carry `source_class=PROXY_DROP` and `confidence=PROXY_ONLY`; a test should assert zero proxy rows in truth/caution headline sets.
8. Missing values must be explicit missingness indicators or confidence caps, never silent zeros or hidden neutral value.

## Time-Split Rules

Recommended first implementation:

- Build one row per player-season-decision-window.
- Use rolling-origin splits by season.
- Minimum two prior seasons for toy/local smoke tests; minimum four prior seasons for any promoted research claim.
- Never train on the same season being evaluated.
- Keep 2026 as holdout/current validation until future outcomes mature.
- For rookie outcomes, evaluate only mature windows separately from `rookie_year_only` or `partial_two_year_window` labels.

Suggested season handling:

- 2010-2021: sensitivity-only; may appear only in proxy inclusion/exclusion deltas.
- 2022-2024: caution set only unless upgraded.
- 2025: truth candidate once future outcome labels exist.
- 2026: current validation/display holdout, not completed historical backtest.

## Metrics

Primary metrics when future outcomes exist:

- Spearman rank correlation between NWR score/rank and future outcome.
- Top-N hit rate by position.
- Mean absolute error / RMSE for point or PPG targets where numeric predictions exist.
- Keeper/drop classification sanity: did players flagged as keep-worthy outperform replacement/drop cohorts?
- Regret buckets: high model score/low future outcome, low model score/high future outcome, and unavailable/dropped useful veteran misses.
- False positive premium picks: model would have elevated a player into early draft capital but future outcome missed threshold.
- False negative useful veterans: model would have buried or ignored a veteran who later cleared useful/starter thresholds.
- Calibration by position: QB/RB/WR/TE separately.
- Calibration by age bucket: RB age cliffs, WR older windows, TE late-career, QB 1QB suppression.
- Sensitivity delta: movement in metrics and rank decisions when proxy rows are included/excluded.

Market sanity metrics:

- NWR-vs-market disagreement buckets.
- Whether market-higher or NWR-higher groups later outperform.
- Count of cases where market context would have changed timing but not value.

Market metrics must never be used as proof that market should become NWR private value.

## Failure Cases

RED failures:

- Any proxy/low-confidence row appears in training labels or truth headline metrics.
- Any ADP/market/rank/projection field appears as a private-value feature or target.
- Outcome display probability overrides rank, sort, score, or value.
- Missing outcome is encoded as zero probability or low value.
- 2026 current availability is treated as historical bad-cut proof.
- Feature timestamp is after the simulated decision date.

YELLOW failures:

- Inferred rows dominate caution metrics.
- Too few ACTUAL/HIGH rows to make a truth claim.
- Position or age bucket has sparse coverage.
- Identity joins rely on name-only fallback without manual review.
- Metrics improve only after proxy rows are included.

## Reporting Format

Each run should produce:

- `RUN_MANIFEST.json`: source files, hashes, run time, git SHA, feature cutoff rules, row eligibility counts.
- `ROW_ELIGIBILITY_AUDIT.csv`: row-level bucket assignment and exclusion reason.
- `TRUTH_BACKTEST_METRICS.csv`: strict ACTUAL/HIGH only.
- `CAUTION_BACKTEST_METRICS.csv`: ACTUAL/HIGH plus eligible inferred rows, reported separately.
- `SENSITIVITY_DELTA_METRICS.csv`: proxy included/excluded deltas.
- `MARKET_SANITY_COMPARISON.csv`: display-only market disagreement diagnostics.
- `FAILURE_CASES.csv`: false positive premium picks, false negative useful veterans, identity/source issues.
- `BACKTEST_REPORT.md`: human-readable summary with GREEN/YELLOW/RED verdict.

## Model Improvement Criteria

A later model candidate may count as an improvement only if:

- it improves truth-backtest metrics on ACTUAL/HIGH rows without worsening key position/age buckets,
- it does not rely on proxy/low-confidence rows for the improvement claim,
- it preserves or improves caution metrics without hiding inferred-row uncertainty,
- it reduces false positive premium picks and false negative useful veterans,
- it maintains market/ADP as display-only, and
- it passes leakage, blocked-field, missingness, and identity audits.

## False Confidence Criteria

Treat a candidate as false confidence if:

- improvement appears only after proxy rows are included,
- actual/high evidence is too sparse for a claim,
- market agreement is presented as model accuracy,
- missing data rows receive confident ranks without confidence caps,
- 2022-2024 inferred rows are blended into truth metrics,
- 2026 current rows are presented as completed historical validation, or
- one position/age bucket drives all improvement while another bucket regresses.

## Recommended Implementation Plan

1. Implement a read-only row eligibility builder that loads the reconstructed drop-list CSVs and emits `ROW_ELIGIBILITY_AUDIT.csv` with bucket and exclusion reasons.
2. Add tests that assert zero `PROXY_DROP`, `PROXY_ONLY`, or `LOW` rows in truth/caution headline sets.
3. Join only approved future outcome labels with explicit as-of feature snapshots.
4. Produce a dry-run report with counts only before any metric computation.
5. After review, compute metrics for truth, caution, sensitivity, and market sanity tracks separately.

## Non-Goals

- No model retraining.
- No production model output changes.
- No ranking changes.
- No latest pointer or frozen board mutation.
- No market/private-value blending.
- No promotion of proxy rows into truth.
