# Age / Lifecycle Component Signal Test V1 Report

## Verdict

`GREEN_AGE_LIFECYCLE_SIGNAL_USEFUL_REVIEW_ONLY`

## Clear Answer

Age/lifecycle adds useful review-only context for decline-risk and breakout-window analysis, but it
does not replace PYF, role archetype, or any future benchmark. It should be interpreted as a guardrail
and formula-family design input, not as exact Model v4 accuracy or a ranking feature.

## Benchmark Scope

- Rows tested: `5518`
- Seasons: `2013-2025`
- Position coverage: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Missing age/DOB rows: `8/5518 (0.14%)`
- Duplicate keys: `0`
- Inputs: age/lifecycle sidecar, Formula Data Mart labels/PYF, review-only role/sparse flags.
- Excluded: Formula Gauntlet, formula combinations, optimized weights, ranking candidates, production model-use.

## Main Findings

- RB/WR/TE late-career and older buckets concentrate a meaningful subset of PYF false positives, but role archetype captures the broader high-volume false-positive pattern.
- Early-career lifecycle buckets capture most PYF false negatives, which is useful breakout-window context but not an automatic boost.
- Sparse-history rows remain low hit-rate even when young, so age/lifecycle must be paired with sparse-history guardrails.

## Metrics Summary

| position | rows | age_vs_finish_spearman | pyf_rank_vs_finish_spearman | older_age_share_of_pyf_false_positives | young_age_share_of_pyf_false_negatives | early_lifecycle_share_of_pyf_false_negatives | signal_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QB | 754 | 0.060 | 0.712 | 47.3% | 32.4% | 32.4% | review_only_context; does not replace PYF |
| RB | 1429 | 0.052 | 0.634 | 23.2% | 53.5% | 53.5% | review_only_context; does not replace PYF |
| TE | 1211 | -0.065 | 0.703 | 32.1% | 47.1% | 51.5% | review_only_context; does not replace PYF |
| WR | 2124 | 0.025 | 0.691 | 34.5% | 55.2% | 54.4% | review_only_context; does not replace PYF |
| ALL | 5518 |  |  | 31.3% | 48.4% | 49.0% | review_only_context; does not replace PYF |

## PYF Comparison

Age/lifecycle does not beat or replace PYF. It helps explain PYF miss slices:

| position | pyf_false_positives | older_age_share_of_pyf_false_positives | late_lifecycle_share_of_pyf_false_positives | pyf_false_negatives | young_age_share_of_pyf_false_negatives | early_lifecycle_share_of_pyf_false_negatives | role_archetype_high_volume_fp_share_reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QB | 55 | 47.3% | 49.1% | 74 | 32.4% | 32.4% | 78.2% |
| RB | 207 | 23.2% | 22.2% | 86 | 53.5% | 53.5% | 78.3% |
| TE | 81 | 32.1% | 33.3% | 68 | 47.1% | 51.5% | 98.8% |
| WR | 229 | 34.5% | 33.6% | 125 | 55.2% | 54.4% | 79.9% |
| ALL | 572 | 31.3% | 30.9% | 353 | 48.4% | 49.0% | 81.8% |

## Interpretation

- Prior-decline detection: useful as a veteran/older-player review slice, not as a direct penalty.
- Breakout-window analysis: useful as an early-career/young-player review slice, not as a direct boost.
- Role archetype comparison: role archetype remains stronger for high-volume PYF false-positive taxonomy; age/lifecycle is complementary.
- Harm risk: age/lifecycle can over-penalize older elite players and over-reward young sparse-history players if used without PYF and role context.

## Maximum Allowed Use

`REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

Also allowed:

- `REVIEW_ONLY_GUARDRAIL_CONTEXT`
- `REVIEW_ONLY_FORMULA_FAMILY_CONTEXT`

Blocked:

- production/model-use
- formula weights
- direct ranking input
- exact Model v4 replay
- Formula Gauntlet tournaments
- rankings integration

## Gates

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Formula Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- Production/model-use remains blocked.

## Recommended Next Lane

`Age / Lifecycle Master Review V1`
