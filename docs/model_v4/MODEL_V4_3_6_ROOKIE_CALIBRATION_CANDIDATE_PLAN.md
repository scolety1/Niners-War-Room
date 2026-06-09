# Model v4.3.6 Rookie Calibration Candidate Plan

## Scope

This document converts mature replay miss patterns and baseline comparisons into candidate shadow tests. It does not implement or promote formula changes.

## Baseline Read

- Current model Top 20 strict starter rate: 0.317
- Draft-capital-only Top 20 strict starter rate: 0.35
- Simple hybrid Top 20 strict starter rate: 0.367
- Current model Top 20 difference makers: 14
- Draft-capital-only Top 20 difference makers: 14
- Simple hybrid Top 20 difference makers: 15

## Candidate Tests

| ID | Candidate | Priority | Evidence Rows | Status |
|---|---|---|---:|---|
| C01 | capital_anchor_rebalance | critical | 30 | not_implemented_review_only_candidate |
| C02 | stronger_day_three_wr_skepticism | high | 5 | not_implemented_review_only_candidate |
| C03 | first_round_wr_floor_refinement | high | 6 | not_implemented_review_only_candidate |
| C04 | rb_receiving_workhorse_modifier | medium | 18 | not_implemented_review_only_candidate |
| C05 | no_premium_te_cap_refinement | medium | 8 | not_implemented_review_only_candidate |
| C06 | one_qb_qb_cap_check | medium | 5 | not_implemented_review_only_candidate |
| C07 | stricter_low_evidence_confidence_cap | critical | 39 | not_implemented_review_only_candidate |
| C08 | simple_hybrid_benchmark_guardrail | high | 33 | not_implemented_review_only_candidate |

## Recommendation

Do not tune live formulas yet. The next approved work should be a shadow-only formula experiment that includes capital anchoring and stricter confidence caps, then compares every variant against draft-capital-only and simple-hybrid baselines.

## Guardrails

- No candidate is implemented in this stage.
- No active rankings, My Team, War Board, readiness gates, or app promotion changed.
- Market, ADP, rankings, projections, mock drafts, and big boards remain excluded from private value.
- Useful model weirdness should be preserved only when it beats simple baselines.
