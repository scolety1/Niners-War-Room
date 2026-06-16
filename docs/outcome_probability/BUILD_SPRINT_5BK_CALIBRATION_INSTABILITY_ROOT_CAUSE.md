# Sprint 5BK Calibration Instability Root-Cause

## 1. Executive verdict

Verdict: `CALIBRATION_INSTABILITY_ROOT_CAUSE_INTERNAL_ONLY_CONTINUE_RESEARCH`

Sprint 5BK investigated why all 10 RB/WR threshold heads remained calibration-unstable after Sprint 5BI. The root cause is not monotonicity. The constrained/PAVA candidate and clamped benchmark both fix the top-N-or-better threshold ordering, but neither fixes calibration-bin reliability.

Primary root causes:

- Sparse positive labels, especially in T6/T12 and in low-probability bins.
- Thin holdout sample sizes by position/head/split after dividing 2023 and 2024 into bins.
- Large observed-vs-predicted gaps in upper WR T24/T36/T48 bins and RB T48 bins.
- Current 2020-2024 historical universe is too small for player-facing exact probabilities across all RB/WR threshold heads.

Release stance remains unchanged:

- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.

## 2. Evidence reviewed

Documents reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BJ_5BI_HOLDOUT_CALIBRATION_AUDIT.md`

Local-only exports reviewed, not modified and not committed:

- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/calibration_bins.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/calibration_bin_stability.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/holdout_predictions_internal_only.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/monotonicity_audit.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/raw_clamped_constrained_metric_comparison.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/sparse_head_audit.csv`

No new local-only exports were created for 5BK.

## 3. Root-cause summary

5BI used a 5-bin calibration audit for each method, split, position, and threshold. Every RB/WR head had at least one unstable bin on validation and test for every method.

For constrained/PAVA:

| Split | Stable bins | Low-row bins | Sparse-event bins | Large-gap bins |
|---|---:|---:|---:|---:|
| Validation | 15 | 0 | 30 | 5 |
| Test | 16 | 10 | 20 | 4 |

Interpretation:

- Validation instability is dominated by sparse event bins.
- Test instability is a mix of sparse event bins and low row-count bins, with fewer but still important large-gap bins.
- Large calibration gaps cluster mostly in the wider WR thresholds and RB T48.
- Changing raw predictions with clamping or PAVA has only tiny Brier/log-loss impact and does not supply enough additional events to stabilize bins.

## 4. Sparse positive-label findings

Sparse labels are a central cause.

| Target | Historical rows | Events | Validation events | Test events | Sparse flag |
|---|---:|---:|---:|---:|---|
| `same_year_rb_t6` | 538 | 28 | 6 | 6 | yes |
| `same_year_wr_t6` | 817 | 26 | 5 | 5 | yes |
| `same_year_rb_t12` | 538 | 54 | 10 | 11 | no, but holdout bins sparse |
| `same_year_wr_t12` | 817 | 54 | 11 | 9 | no, but holdout bins sparse |

T6 heads are clearly non-viable for release because the total historical events and holdout events are too thin. T12 has enough total events to avoid the coarse sparse-head flag, but once split into calibration bins, the lower-probability bins still often have 0-2 events.

## 5. Binning-strategy findings

Binning strategy contributes to the instability, but it is not the only cause.

5BI used 5 equal-frequency bins per head/split. That creates small bin sizes:

- Validation RB: about 21-22 rows per bin.
- Validation WR: about 30-31 rows per bin.
- Test RB: about 19-20 rows per bin.
- Test WR: about 32-33 rows per bin.

The test RB bins fall below the 20-row stability threshold, which explains the `unstable_low_row_count` flags. But reducing bins does not solve the overall release problem.

Constrained/PAVA simulated binning from the same holdout predictions:

| Bin count | Unstable constrained split-heads | Total split-heads | Main remaining failure |
|---:|---:|---:|---|
| 5 | 20 | 20 | sparse events, low row count, large gaps |
| 4 | 20 | 20 | sparse events, large gaps |
| 3 | 18 | 20 | sparse events, large gaps |
| 2 | 16 | 20 | sparse events, large gaps |

Only four constrained split-heads become stable under a 2-bin read:

- Test RB T24
- Test RB T36
- Validation RB T36
- Validation RB T48

This means fewer bins are a plausible research option, but not a release fix by themselves.

## 6. Head-level sample-size findings

The model has enough aggregate rows for internal diagnostics but not enough reliable bin-level events for player-facing probabilities.

5BI holdout rows:

- Validation: 260 RB/WR rows.
- Test: 261 RB/WR rows.
- Per head/split: 98-163 rows depending on position and split.
- Per 5-bin head/split: about 19-33 rows.

The issue is not just total rows; it is positive-event distribution inside each head/split/bin. Many lower-probability bins have 0 events even for heads whose total event counts look acceptable.

## 7. Threshold findings

All thresholds are unstable under the 5-bin audit, but for different reasons.

| Threshold | Root-cause read |
|---|---|
| T6 | Clearly non-viable for release; sparse historical and holdout positives dominate. |
| T12 | Not globally sparse, but bin-level positives are often too thin. |
| T24 | Better total support, but WR has large upper-bin calibration gaps. |
| T36 | Better total support, but WR has the worst observed large-gap failures. |
| T48 | Better total support, but high observed rates in top bins are underpredicted, especially WR and RB T48. |

Worst constrained/PAVA 5-bin gaps:

| Split | Position | Threshold | Bin | Predicted mean | Observed rate | Gap | Events | Flag |
|---|---|---|---:|---:|---:|---:|---:|---|
| Validation | WR | T36 | 5 | 0.391749 | 0.741935 | 0.350186 | 23 | large gap |
| Validation | WR | T48 | 5 | 0.521288 | 0.870968 | 0.349680 | 27 | large gap |
| Validation | WR | T24 | 5 | 0.260724 | 0.548387 | 0.287663 | 17 | large gap |
| Test | WR | T36 | 5 | 0.393677 | 0.666667 | 0.272990 | 22 | large gap |
| Validation | RB | T48 | 4 | 0.482894 | 0.714286 | 0.231392 | 15 | large gap |
| Test | RB | T48 | 4 | 0.518679 | 0.750000 | 0.231321 | 15 | large gap |

## 8. RB vs WR findings

WR behaves worse than RB on calibration gap magnitude.

Constrained/PAVA 5-bin summary:

| Position | Unstable split-heads | Total split-heads | Average max calibration gap | Minimum bin events |
|---|---:|---:|---:|---:|
| RB | 10 | 10 | 0.131975 | 0 |
| WR | 10 | 10 | 0.195768 | 0 |

RB instability is a mix of sparse early thresholds and RB T48 upper-bin underprediction. WR instability is broader: T6/T12 are sparse, while T24/T36/T48 have stronger large-gap failures.

## 9. Monotonicity vs calibration

Clamped and constrained/PAVA methods fix monotonicity but not calibration.

5BI monotonicity result:

| Method | Validation RB/WR violations | Test RB/WR violations |
|---|---:|---:|
| Raw independent baseline | 98 total adjacent violations | 96 total adjacent violations |
| Post-hoc forward clamp benchmark | 0 | 0 |
| Constrained/PAVA candidate | 0 | 0 |

Metric deltas from raw to constrained are tiny:

- Validation average Brier improves by 0.000014.
- Validation average log loss improves by 0.000047.
- Test average Brier improves by 0.000053.
- Test average log loss improves by 0.000143.

These small changes are directionally nice but not release-grade. Monotonic repair is a structural consistency fix, not a calibration model.

## 10. Clearly non-viable heads

Clearly non-viable for release:

- RB T6
- WR T6

Reason:

- Sparse historical events.
- Only 5-6 holdout events per validation/test split.
- Bin-level sparse-event failures persist even under fewer bins.

Likely non-viable for exact percentages without more data or pooling:

- RB T12
- WR T12

Reason:

- Total support is better than T6, but holdout calibration bins remain sparse.

Not release-viable yet despite stronger support:

- WR T24/T36/T48
- RB T48

Reason:

- Large upper-bin calibration gaps show underprediction in higher-probability bins.

## 11. Coarse-band theoretical eligibility

No coarse bands are release-eligible now.

Theoretical coarse-band research may be worth exploring only if all of the following are true in a future gated sprint:

- T6 heads remain abstained or excluded.
- Bands are based on pooled/hierarchical evidence rather than per-head exact percentages.
- Calibration is audited at the band level with fewer bins or grouped thresholds.
- The audit reports coverage and instability warnings alongside every band.
- Outputs remain internal-only until a separate HQ release/display gate approves them.

Even then, this would be a research direction, not a recommendation to release bands.

## 12. Historical-universe adequacy

The current 2020-2024 historical universe is too small for player-facing exact probabilities across the RB/WR threshold grid.

It is adequate for:

- internal mechanics research
- monotonicity repair testing
- rough directional holdout comparison
- identifying non-viable heads

It is not adequate for:

- player-facing exact percentages
- app-readable probability tables
- app-readable coarse-band tables
- ranking or sorting from outcome probabilities
- promoted model artifacts

## 13. Safer next research options

Recommended research options, safest first:

1. `Sprint 5BL - Calibration Bin Sensitivity and Abstention Policy`
   - Recompute stability under 2-bin, 3-bin, and grouped-threshold audits.
   - Produce no app-readable outputs.
   - Identify heads that must be permanently abstained unless more data arrives.

2. `Sprint 5BM - Threshold Grouping / Pooled Calibration Research`
   - Explore pooled RB/WR calibration by threshold family.
   - Test grouped T24/T36/T48 behavior separately from T6/T12.
   - Keep all outputs internal-only.

3. `Sprint 5BN - More Seasons / Larger Historical Universe Feasibility`
   - Determine whether additional prior seasons can be legally reconstructed with the same point-in-time feature policy.
   - Avoid source shortcuts, public ranks, projections, ADP, or market contamination.

4. `Sprint 5BO - Hierarchical Calibration Prototype`
   - Research partial pooling by position and threshold.
   - Treat results as internal-only until adversarially audited.

Do not proceed to app display, exact probabilities, coarse bands, rankings, sorting, or promoted artifacts.

## 14. Final gate label

Final gate label: `CALIBRATION_INSTABILITY_ROOT_CAUSE_INTERNAL_ONLY_CONTINUE_RESEARCH`

Meaning:

- Instability is driven by sparse positive labels, thin per-bin holdout samples, and large upper-bin gaps.
- Fewer bins help but do not clear the release gate.
- Constrained/PAVA fixes monotonicity but not calibration.
- Current 2020-2024 historical universe is too small for player-facing probabilities.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.
