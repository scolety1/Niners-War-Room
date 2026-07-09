# Model v4 Partial Historical Replay Benchmark V1 Report

## Verdict

`YELLOW_MODEL_V4_PARTIAL_REPLAY_MIXED_SIGNAL_WITH_CAVEATS`

## Clear Answer

The partial historical replay shows useful lagged factual signal, especially from prior-year points and simple passing/rushing/receiving yardage or opportunity fields. However, the best non-PYF component-source signals did not beat the simple prior-year-points baseline in any position. It should be interpreted as a review-only component signal audit, not as exact Model v4 accuracy. No predeclared partial Model v4 score exists, so this lane did not create one.

## Benchmark Scope

- Seasons: `2013-2025`
- Positions: `QB`, `RB`, `WR`, `TE`
- Rows tested: `5518`
- Position rows: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Labels: `next_nwr_points`, `next_nwr_ppg`, `next_position_finish`, `startable_hit`, `startable_bucket`
- Inputs: review-only partial component receipts and lagged V3 factual overlap columns only
- Excluded inputs: exact current-board fields, current ADP, market, current injury/depth/roster context, target-season outcomes as inputs, source-gated blocked fields, and all exact checkpoint/lifecycle/confidence/candidate-overlay rows

## Metrics Summary

| Position | Seasons | Rows | Metric Type | Spearman | Top-12 | Top-24 | Top-36 | Startable Precision | Caveat |
| -------- | ------: | ---: | ----------- | -------: | -----: | -----: | -----: | ------------------: | ------ |
| QB | 13 | 754 | best_non_pyf_component_source | 0.683 | 48.1% |  |  | 50.8% | passing_production::prior_passing_yards; single_component_proxy_not_formula_score |
| RB | 13 | 1429 | best_non_pyf_component_source | 0.628 | 41.7% | 55.1% |  | 46.9% | first_down_high_value::prior_rushing_yards; single_component_proxy_not_formula_score |
| WR | 13 | 2124 | best_non_pyf_component_source | 0.683 | 39.1% | 55.1% | 63.0% | 55.4% | first_down_yardage::prior_receiving_yards; single_component_proxy_not_formula_score |
| TE | 13 | 1211 | best_non_pyf_component_source | 0.691 | 50.6% |  |  | 48.1% | first_down_yardage::prior_receiving_yards; single_component_proxy_not_formula_score |

## Baseline Comparison

| Model / Signal / Baseline | Scope | Metric | Result | Beat Baseline? | Caveat |
| ------------------------- | ----- | ------ | -----: | -------------- | ------ |
| prior_year_points_baseline | QB | Spearman rank vs next-season finish | 0.712 |  | safe baseline from completed feature-season NWR points |
| best_non_pyf_component_source | QB | Spearman rank vs next-season finish | 0.683 | No | best allowed component source excluding prior_nwr_points/prior_nwr_ppg |
| Production Rankings Backtest V1 current-formula-family proxy | QB | Spearman | 0.699 | not_comparable_in_this_lane | prior accepted packet says proxy did not beat simple prior-year finish overall |
| prior_year_points_baseline | RB | Spearman rank vs next-season finish | 0.633 |  | safe baseline from completed feature-season NWR points |
| best_non_pyf_component_source | RB | Spearman rank vs next-season finish | 0.628 | No | best allowed component source excluding prior_nwr_points/prior_nwr_ppg |
| Production Rankings Backtest V1 current-formula-family proxy | RB | Spearman | 0.636 | not_comparable_in_this_lane | prior accepted packet says proxy did not beat simple prior-year finish overall |
| prior_year_points_baseline | WR | Spearman rank vs next-season finish | 0.691 |  | safe baseline from completed feature-season NWR points |
| best_non_pyf_component_source | WR | Spearman rank vs next-season finish | 0.683 | No | best allowed component source excluding prior_nwr_points/prior_nwr_ppg |
| Production Rankings Backtest V1 current-formula-family proxy | WR | Spearman | 0.686 | not_comparable_in_this_lane | prior accepted packet says proxy did not beat simple prior-year finish overall |
| prior_year_points_baseline | TE | Spearman rank vs next-season finish | 0.701 |  | safe baseline from completed feature-season NWR points |
| best_non_pyf_component_source | TE | Spearman rank vs next-season finish | 0.691 | No | best allowed component source excluding prior_nwr_points/prior_nwr_ppg |
| Production Rankings Backtest V1 current-formula-family proxy | TE | Spearman | 0.685 | not_comparable_in_this_lane | prior accepted packet says proxy did not beat simple prior-year finish overall |

## Coverage / Missingness

See `MODEL_V4_PARTIAL_REPLAY_COVERAGE_MISSINGNESS.csv`. All benchmarked input receipts remain `partial_replay_proxy_only`, `review_only`, not model-use, not production, and not source-truth.

## What This Proves

- The lagged factual receipt panel is reproducible and decision-date separated for review-only benchmark use.
- Several partial component source fields have directional signal against next-season outcomes.
- The strongest signals often overlap with simple prior-year production, which remains a serious baseline.

## What This Does Not Prove

- Exact Model v4 accuracy.
- Production-active approval.
- Source promotion.
- Historical replay completeness.
- Future 2026 accuracy.

## Recommendation

`Partial signal is promising; send to Formula Gauntlet as review-only evidence.`

The useful portion is not a formula. It is a signal inventory and baseline sanity check. Exact historical replay remains blocked until the missing checkpoint/lifecycle/confidence/candidate-overlay receipt chain is recovered.
