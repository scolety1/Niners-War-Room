# NWR Formula Family Design Plan

This plan is design-only. It does not run a tournament, tune weights, select winners, or change rankings.

## Candidate Family Scaffold

If Data Hygiene and Master HQ later clear a review-only tournament, 100 candidates could be built as:

`20 formula families x 5 predeclared weight variants = 100 candidates`

## Candidate Families

1. PYF anchor variants.
2. Multi-year weighted production variants.
3. Position-specific production variants.
4. Sparse-history guarded variants.
5. Low-games guarded variants.
6. Age/lifecycle adjusted variants.
7. Volume/opportunity variants.
8. Decline-risk penalty variants.
9. Breakout-friendly opportunity variants.
10. Robust/winsorized production variants.
11. Hybrid rank formulas.
12. First-down scoring fit variants.
13. Non-PPR receiving volume variants.
14. RB role-stability variants.
15. WR target/air-yard proxy variants.
16. TE volatility dampener variants.
17. QB rushing/passing balance variants.
18. Rookie/second-year separate model variants.
19. Market/context comparison variants if source-gated.
20. Simple review-only ML baselines only if data supports leakage-safe testing.

## Required Pre-Run Gates

- PYF baseline present and reproducible.
- Historical labels source-traced and scoring-compatible.
- Input receipts source-traced.
- Missingness policy approved.
- Sparse-history and low-games guardrails defined.
- Position-level reporting required.
- Leakage/as-of checks passed.
- Blocked inputs excluded.
- Master HQ approves tournament scope.

## Blocked Inputs For Candidate Construction

- True routes_run.
- True YPRR.
- True TPRR.
- Exact PFF Elusive Rating.
- `nwr_elusive_proxy_review_only`.
- Current/future injury, depth chart, roster, ADP, or market context as historical inputs.
- Any current-board field without historical receipts.

## PYF Anchor Policy

Every candidate must compare to PYF overall and by position. A candidate that cannot beat PYF must be treated as review evidence only, not a formula winner.
